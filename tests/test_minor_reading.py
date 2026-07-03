# -*- coding: utf-8 -*-
"""T5.9: 미성년(만 19세 미만) 연령 적합 분기 회귀 — love 섹션이 연애/배우자 단정 대신
성장·친구 등 연령에 맞춘 서술로 치환되는지(A5 분기). 입춘 ±2분·자미단독 강등은 각각
test_near_term_boundary·test_p8/test_p3 에서 기존 커버(중복 미신설)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder  # noqa: E402


def _love(birth_year: int):
    saju = engine.build(birth_year, 6, 15, 10, 0, is_male=False, horoscope_date="2026-06-01")
    rep = builder.build_report(
        saju, use_llm=False, ref_year=2026, name="가나", product="integrated"
    )
    love = next((s.final_text for s in rep.sections if s.id == "love"), "")
    return love, rep.guard.clean


def test_minor_love_section_is_age_appropriate():
    minor_love, minor_clean = _love(2015)  # ref_year 2026 기준 만 11세
    adult_love, adult_clean = _love(1990)  # 만 36세
    assert "미성년" in minor_love, minor_love[:80]  # 연령 적합 분기 발동
    assert "미성년" not in adult_love  # 성인은 일반 연애/배우자 서술
    assert minor_clean is True and adult_clean is True  # 양쪽 가드 clean
