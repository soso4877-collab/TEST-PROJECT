# -*- coding: utf-8 -*-
"""T2.4 [F-1] iztro-py 0.3.5 대한(大限/童限) 궁 배정 회귀 앵커.

0.3.4 는 출생 이전/유아기 나이의 대한 조회에서 궁 배정 오류가 있었고 0.3.5 가 수정본.
ziwei.build 의 horoscope(대한/유년) 경로 값을 고정해 이후 스택 변경 회귀를 잡는다.
(decadal/yearly 는 iztro raw 키 형식 — 구조 동등성은 test_ziwei_parity 가 커버.)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402


def test_decadal_infant_range():
    # 유아기(출생 직후, 2001) 대한 — 0.3.5 궁배정 수정 반영값
    s = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2001-06-01")
    assert s.ziwei.decadal == "bingHeavenlyyinEarthly"  # 丙寅
    assert s.ziwei.yearly == "xinHeavenlysiEarthly"  # 辛巳


def test_decadal_adult_range():
    s = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    assert s.ziwei.decadal == "wuHeavenlychenEarthly"  # 戊辰
    assert s.ziwei.yearly == "bingHeavenlywuEarthly"  # 丙午
