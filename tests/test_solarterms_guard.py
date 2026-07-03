# -*- coding: utf-8 -*-
"""T5.6/F-4: solarterms de440s 범위 가드 — 천체력 범위(실측 1850~2149) 밖은 모호한
Skyfield EphemerisRangeError 대신 명확한 ValueError. 범위 내는 정상 계산(골든 무영향)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import solarterms as S  # noqa: E402


def test_in_range_years_compute():
    for y in (1850, 2000, 2027, 2149):  # 실측 가능 경계 포함
        assert S.solar_term_time(y, 315) is not None


def test_out_of_range_raises_clear_valueerror():
    for y in (1849, 2150, 1700, 2200):
        with pytest.raises(ValueError, match="범위"):
            S.solar_term_time(y, 315)
