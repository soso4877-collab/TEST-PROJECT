# -*- coding: utf-8 -*-
"""P3 콘텐츠 빌더 + 할루시네이션 가드 검증."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, factcheck, safe_lint  # noqa: E402
from sajugen.content.sections_schema import SECTION_SPECS  # noqa: E402

_SAJU = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")


def test_all_sections_present_and_nonempty():
    # 챕터 수는 SECTION_SPECS 계약을 따른다(주제별 챕터 재편 후 >=15).
    r = builder.build_report(_SAJU, use_llm=False)
    assert len(r.sections) == len(SECTION_SPECS) >= 15
    assert all(s.final_text.strip() for s in r.sections)
    assert any(s.id == "appendix_terms" for s in r.sections)


def test_gakron_and_new_sections_present_and_deep():
    # 주제별 챕터(흐르는 산문). 비어있지 않고 일정 분량 이상(병합으로 상향).
    r = builder.build_report(_SAJU, use_llm=False)
    by = {s.id: s for s in r.sections}
    for sid in ("love", "work", "nature", "health", "flow"):
        assert sid in by, f"{sid} 챕터 누락"
        assert len(by[sid].final_text.strip()) >= 500, (sid, len(by[sid].final_text))
    # health 는 의료 단정 금지 + 진료 안내 포함(운영자 지시 2026-06-12:
    # '전문가와 상의' 보일러플레이트 금지 → '병원 진료/확인' 자연 문구로 대체)
    ht = by["health"].final_text
    for term in ("병에 걸린", "병이 생긴", "불치", "수명이 짧", "죽는다", "사망", "단명"):
        assert term not in ht, f"health 의료 단정어: {term}"
    assert "병원" in ht
    for hedge in ("전문가와 상의", "참고용", "참고로만"):
        assert hedge not in ht, f"health 책임회피 문구 잔존: {hedge}"
    # 상품 토글: 자미단독은 명리계열 챕터(nature/flow) 제외, 자미 챕터는 유지
    rz = builder.build_report(_SAJU, use_llm=False, product="ziwei")
    zids = {s.id for s in rz.sections}
    assert "nature" not in zids and "ziwei" in zids
    assert rz.guard.clean is True


def test_rule_skeleton_passes_all_guards():
    r = builder.build_report(_SAJU, use_llm=False)
    assert r.guard.safe_lint_total == 0, "§12 위반 존재"
    assert r.guard.factcheck_total == 0, "사실일치 위반 존재"
    assert r.guard.grounding_ok is True
    assert r.guard.clean is True
    assert r.guard.fallback_sections == 0  # LLM off → 폴백 발생 없음


def test_safe_lint_catches_forbidden():
    bad = "이 사람과는 반드시 재회합니다. 올해 무조건 대박납니다. 100% 적중."
    v = safe_lint.lint(bad)
    whys = {x["why"] for x in v}
    assert "단정" in whys and "관계 단정" in whys and "재물 단정" in whys
    assert not safe_lint.is_clean(bad)


def test_factcheck_catches_hallucinated_ganzhi_and_star():
    # 이 사주(2000-01-01: 己卯 丙子 戊午 戊午, 대운 乙亥…)에 없는 간지/별
    bad = "당신은 甲寅 대운에 자미성이 빛나 큰 성취를 이룹니다."
    v = factcheck.check(bad, _SAJU)
    toks = {x["token"] for x in v}
    assert "甲寅" in toks  # 차트에 없는 간지
    # '자미'가 이 명반 명궁 주성이 아니면 잡힘(차트에 자미 주성 없을 때)
    assert factcheck.is_consistent("戊午 일주는 참고용입니다.", _SAJU)  # 실제 간지는 통과


def test_llm_fallback_when_polish_hallucinates(monkeypatch):
    # 윤문이 환각(없는 간지 삽입)하면 빌더가 룰 원문으로 폴백해야 함
    from sajugen.content import llm_polish

    monkeypatch.setattr(llm_polish, "polish", lambda rt, title: rt + " 추가로 甲寅 대운이 옵니다.")
    r = builder.build_report(_SAJU, use_llm=True)
    # 폴백 발생, 최종 텍스트엔 환각 간지 없음, 전체 여전히 clean
    assert r.guard.fallback_sections >= 1
    assert all("甲寅" not in s.final_text for s in r.sections)
    assert r.guard.factcheck_total == 0 and r.guard.clean is True
