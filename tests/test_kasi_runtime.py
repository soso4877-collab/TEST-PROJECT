# -*- coding: utf-8 -*-
"""T2.3 [G-1] KASI 3원 교차 런타임 편입 (절대규칙 7 전단).

kasi.year_kasi_check → engine CrossCheck.kasi_consistent → pipeline calc_consistent →
order_flow CALC_MISMATCH 차단. 캐시 범위 밖/부재는 2원 폴백(차단 아님, kasi_out_of_range).
기지결함(KNOWN_KASI_TERM_DEFECTS)은 all_kasi_ok 에서 제외되어 차단하지 않는다.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine, kasi  # noqa: E402

_HAS_CACHE = kasi.KasiCache().exists


def test_out_of_range_falls_back_without_blocking():
    # 범위 밖(1999/2050)은 캐시 유무와 무관하게 폴백 (kasi_consistent=True, out_of_range=True)
    assert kasi.year_kasi_check(1999) == (True, True)
    assert kasi.year_kasi_check(2050) == (True, True)


@pytest.mark.skipif(not _HAS_CACHE, reason="KASI 캐시 필요(data/kasi_cache.sqlite)")
def test_unknown_mismatch_blocks(monkeypatch):
    # 미지 KASI 불일치 = 차단 대상 (kasi_consistent=False)
    monkeypatch.setattr(
        kasi, "crosscheck3_year", lambda year, **kw: {"kasi_available": True, "all_kasi_ok": False}
    )
    kasi.year_kasi_check.cache_clear()
    try:
        assert kasi.year_kasi_check(2099) == (False, False)
    finally:
        kasi.year_kasi_check.cache_clear()


@pytest.mark.skipif(not _HAS_CACHE, reason="KASI 캐시 필요")
def test_known_defect_year_not_blocked(monkeypatch):
    # 기지결함은 crosscheck3_year 가 all_kasi_ok=True 로 이미 제외 → 비차단
    monkeypatch.setattr(
        kasi,
        "crosscheck3_year",
        lambda year, **kw: {
            "kasi_available": True,
            "all_kasi_ok": True,
            "kasi_known_defects": ["立冬"],
        },
    )
    kasi.year_kasi_check.cache_clear()
    try:
        assert kasi.year_kasi_check(2098) == (True, False)
    finally:
        kasi.year_kasi_check.cache_clear()


@pytest.mark.skipif(not _HAS_CACHE, reason="KASI 캐시 필요")
def test_unknown_mismatch_propagates_to_crosscheck(monkeypatch):
    # engine.build → CrossCheck.kasi_consistent=False (pipeline calc_consistent 로 전파돼 차단)
    monkeypatch.setattr(
        kasi, "crosscheck3_year", lambda year, **kw: {"kasi_available": True, "all_kasi_ok": False}
    )
    kasi.year_kasi_check.cache_clear()
    try:
        c = engine.build(2003, 6, 15, 12, 0, is_male=True).crosscheck
        assert c.kasi_consistent is False
    finally:
        kasi.year_kasi_check.cache_clear()


@pytest.mark.skipif(not _HAS_CACHE, reason="KASI 캐시 필요")
def test_in_range_normal_and_known_defect_consistent():
    # 실캐시: 정상 연도·기지결함 연도 모두 kasi_consistent=True(오차단 0 회귀 보증)
    assert kasi.year_kasi_check(2000) == (True, False)
    assert kasi.year_kasi_check(2011) == (True, False)  # 기지결함 비차단
    c = engine.build(2000, 6, 15, 12, 0, is_male=True).crosscheck
    assert c.kasi_consistent is True and c.kasi_out_of_range is False
