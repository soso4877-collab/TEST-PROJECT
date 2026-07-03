# -*- coding: utf-8 -*-
"""T4.1/G-4: factcheck 연도 화이트리스트 — 허용(기준·세운·월운·대운시작·출생) 밖 'YYYY년'
언급을 하드 차단(근거 없는 미래연도 생성 방지). 양방(정상 통과 / 결함 차단) + back-compat.
자미 주성 검사는 실측상 사문(14/14 상시 배치)이라 문서화만(별도 테스트 없음)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import factcheck  # noqa: E402


def _saju():
    return engine.build(1972, 6, 30, 9, 30, is_male=False, horoscope_date="2026-06-01")


def test_year_outside_allowed_is_flagged():
    v = factcheck.check("2035년에 변화가 옵니다.", _saju())
    assert any(x["type"] == "year" and x["token"] == "2035" for x in v), v


def test_grounded_years_pass():
    saju = _saju()
    for yr in ("2026년", "2027년"):  # 기준연도·근접 세운
        assert not any(x["type"] == "year" for x in factcheck.check(f"{yr} 흐름이 열립니다.", saju))
    # 출생연도도 허용(본문이 태어난 해를 짚을 수 있음)
    assert not any(x["type"] == "year" for x in factcheck.check("1972년에 태어난 흐름은", saju))


def test_allowed_years_set_contents():
    allow = factcheck.allowed_tokens(_saju())
    assert 2026 in allow["allowed_years"]  # ref_year
    assert 1972 in allow["allowed_years"]  # 출생연도
    assert 2035 not in allow["allowed_years"]  # 미근거(1972 기준)


def test_year_check_skipped_without_allowed_years_backcompat():
    # allowed_years 미제공(구 스키마·saju 없는 재검증) → 연도 검사 skip(back-compat 유지).
    v = factcheck.check_with_allow("2099년에 일이 생깁니다.", {"ganzhi": [], "ganzhi_ko": []})
    assert not any(x["type"] == "year" for x in v)


def test_number_without_year_suffix_not_flagged():
    # '년' 접미 없는 숫자(수량·번호)는 연도 오탐 아님.
    assert not any(x["type"] == "year" for x in factcheck.check("2035명이 모였습니다.", _saju()))


def test_year_violation_is_pii_free():
    # hit 은 token(연도)·type·why·pos 만 — 본문 문장 미포함(T1.3/PII).
    v = [x for x in factcheck.check("2035년에 큰일이 납니다.", _saju()) if x["type"] == "year"]
    assert v and set(v[0]) <= {"type", "token", "why", "pos"}
    assert "큰일" not in str(v)
