# -*- coding: utf-8 -*-
"""문장 품질·시제 린터 + 자미 골격 잔재 검증(H1-mini 2026-06-15).

이슈4(신강한 신약 모순)·5(재무→재수 오타)·6(ref_year 시제)·2(자미 템플릿 잔재).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import quality_lint as q  # noqa: E402
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


# ── 이슈6: 시제 ──
def test_temporal_flags_past_or_current_year():
    assert tl.lint("2026년이 오기 전까지 준비하세요.", 2026)  # ref=2026 → 위반
    assert tl.lint("2025년이 오기 전", 2026)  # 과거 → 위반
    assert tl.is_clean("2027년이 오기 전에 준비하세요.", 2026)  # 미래 → 정상
    assert tl.is_clean("2026년이 오기 전까지 준비하세요.", None)  # ref 없으면 검사 생략
    assert tl.is_clean("2026년 안에 흐름이 시작됩니다.", 2026)  # 올바른 표현


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
