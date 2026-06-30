# -*- coding: utf-8 -*-
"""문장 품질·시제 린터 + 자미 골격 잔재 검증(H1-mini 2026-06-15).

이슈4(신강한 신약 모순)·5(재무→재수 오타)·6(ref_year 시제)·2(자미 템플릿 잔재).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import client_tone_lint as ct  # noqa: E402
from sajugen.content import customer_meta_lint as cmeta  # noqa: E402
from sajugen.content import quality_lint as q  # noqa: E402
from sajugen.content import style_lint as style  # noqa: E402
from sajugen.content import temporal_lint as tl  # noqa: E402


# ── 이슈4: 의미 모순 ──
def test_quality_flags_singang_contradiction():
    assert q.lint("두 사람은 신강한 신약의 차이가 있어요.")
    assert q.lint("신약한 신강 구조입니다.")
    assert q.is_clean("신강한 사주라 힘이 또렷합니다.")  # 정상 미검출
    assert q.is_clean("신약한 사주라 보강이 필요합니다.")


# ── 이슈5: 재무→재수 오타 ──
def test_quality_flags_jaesu_typo():
    assert q.lint("김태수, 재수는 돈의 흐름을 읽는 사람입니다.")
    assert q.lint("재수는 재물의 창고예요.")
    # 이름 앵커
    hits = q.lint("김태수, 재수가 핵심이에요.", names=["김태수"])
    assert any(h["type"] == "name_typo" for h in hits)
    # 정상 '재수(운)'은 미검출
    assert q.is_clean("올해는 재수가 좋은 흐름이에요.")
    assert q.is_clean("재수가 트이는 시기입니다.")


def test_quality_flags_adjacent_duplicate_words():
    hits = q.lint("관계에서 반복되는 반복되는 흐름이 보입니다.")
    assert any(h["type"] == "adjacent_duplicate" for h in hits)
    assert q.is_clean("관계에서 반복되는 흐름이 보입니다.")


def test_quality_flags_customer_framing_phrases():
    hits = q.lint("이 풀이에서는 두 사람의 관계를 봅니다.")
    assert any(h["type"] == "customer_framing" for h in hits)
    assert q.lint("이 자료는 참고용입니다.")
    assert q.is_clean("이 풀이를 읽는 법")


def test_quality_flags_internal_meta_labels():
    hits = q.lint("고객 질문: 현재 썸 관계가 궁금합니다.\n상담 대상: 가현 씨, 상철 씨\n[자미두수]\n이 장에서 봅니다.")
    assert any(h["type"] == "internal_meta_label" for h in hits)


def test_customer_meta_lint_is_separate_from_internal_label_lint():
    text = "이 글은 통합 풀이입니다."
    assert cmeta.lint(text)
    assert not any(h["type"] == "internal_meta_label" for h in q.lint(text))


def test_customer_meta_lint_allows_customer_facing_explanation():
    text = "명리와 자미두수는 서로 다른 관점이라, 같은 선택도 다르게 비출 수 있습니다."
    assert cmeta.is_clean(text), cmeta.lint(text)


def test_quality_flags_relationship_raw_fact_slot_leak():
    text = (
        "두 사람 사이에서 실제로 맞물리는 부분은 다음과 같습니다.\n"
        "가현 씨 기준 상철 씨는 십성으로 비견입니다.\n"
        "일지 삼합 반합(수), 같은 방향으로 모이는 협업의 결입니다.\n"
        "자미두수로는 사람과 관계, 돈과 생활, 일의 자리를 함께 봅니다.\n"
        "명궁은 명궁, 신궁은 명궁입니다.\n"
        "시기 흐름은 다음처럼 나누어 봅니다."
    )
    hits = q.lint(text)
    assert any(h["type"] == "internal_meta_label" for h in hits)


def test_quality_flags_promo_cta_and_decorative_emoji():
    hits = q.lint("🔮 사주도령 전문 상담\n더 깊은 궁합과 시기별 흐름이 궁금하시다면 아래 링크에서 확인하세요.")
    assert any(h["type"] == "decorative_emoji" for h in hits)
    assert any(h["type"] == "promo_cta" for h in hits)
    assert q.is_clean("사주도령 궁합 풀이")  # 표지/상품명 자체는 허용


# ── 이슈6: 시제 ──
def test_temporal_flags_past_or_current_year():
    assert tl.lint("2026년이 오기 전까지 준비하세요.", 2026)  # ref=2026 → 위반
    assert tl.lint("2025년이 오기 전", 2026)  # 과거 → 위반
    assert tl.is_clean("2027년이 오기 전에 준비하세요.", 2026)  # 미래 → 정상
    assert tl.is_clean("2026년이 오기 전까지 준비하세요.", None)  # ref 없으면 검사 생략
    assert tl.is_clean("2026년 안에 흐름이 시작됩니다.", 2026)  # 올바른 표현


def test_temporal_flags_past_month_as_future_when_ref_date_known():
    hits = tl.lint("4월이 오면 자산 흐름이 열립니다.", 2026, ref_date="2026-06-25")
    assert hits
    assert tl.is_clean("7월이 오면 자산 흐름을 다시 봅니다.", 2026, ref_date="2026-06-25")


# ── 이슈2: 자미 골격 잔재(룰 경로, 무LLM) ──
def test_ziwei_skeleton_has_no_template_residue(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(saju, use_llm=False, ref_year=2026, name="김태수")
    ztext = rep.section("ziwei").final_text
    for bad in ("[핵심 궁]", "[그 밖의 궁]", "명궁(명궁)", "주성은 주성 없음", "주성 없음(공궁)"):
        assert bad not in ztext, f"자미 잔재 발견: {bad!r}"
    # 공궁(주성 없는 자리)은 자연스러운 표현으로
    assert "주성이 없는 공궁" in ztext


def test_love_consult_rule_text_quality_and_temporal_clean(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        name="김태수",
        concern="전남친과 재회 시기 언제가 좋을까요",
    )
    text = rep.section("consult").final_text
    assert q.is_clean(text), q.lint(text)
    assert tl.is_clean(text, 2026), tl.lint(text, 2026)


def test_personal_rule_positive_body_semantic_gate_clean(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(saju, use_llm=False, ref_year=2026)
    body = "\n\n".join(
        s.final_text
        for s in rep.sections
        if s.id not in {"cover", "toc", "appendix_terms", "colophon"}
    )

    assert cmeta.is_clean(body), cmeta.lint(body)
    assert not [h for h in ct.placeholder_residue_lint(body) if h.get("severity") == "hard"]
    assert style.is_clean(body), style.lint(body)
    assert q.is_clean(body), q.lint(body)
    assert tl.is_clean(body, 2026, ref_date="2026-06-01"), tl.lint(
        body, 2026, ref_date="2026-06-01"
    )
