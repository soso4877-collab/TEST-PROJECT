# -*- coding: utf-8 -*-
"""P1 보정 레이어 검증: 표준시 역사·DST(zoneinfo), 진태양시, Skyfield↔lunar-python 절기 교차."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import crosscheck  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402


def test_standard_time_history_matches_zoneinfo_authority():
    # 한국 표준시 역사·서머타임은 zoneinfo(Asia/Seoul)가 권위 — 손코딩 가정 대신
    # 우리 파이프라인의 UTC가 독립적인 zoneinfo 변환과 정확히 일치하는지 검증.
    from datetime import datetime
    from zoneinfo import ZoneInfo

    for y, mo, d, h, mi in [
        (1955, 6, 1, 12, 0),
        (1959, 7, 1, 9, 0),
        (1953, 3, 1, 8, 0),
        (1990, 5, 20, 14, 30),
    ]:
        r = tc.correct(y, mo, d, h, mi)
        exp = (
            datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("Asia/Seoul"))
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )
        assert r.utc == exp, (y, r.utc, exp)


def test_dst_1988_summer_utc_plus_10():
    # 1988 서머타임(+1h) → 표준 UTC+9 위 +1 = UTC+10 → 12:00 → 02:00 UTC
    r = tc.correct(1988, 8, 1, 12, 0)
    assert r.utc.hour == 2, r.utc


def test_modern_kst_utc_plus_9():
    r = tc.correct(1990, 5, 20, 14, 30)
    assert r.utc.hour == 5 and r.utc.minute == 30, r.utc


def test_true_solar_time_seoul_offset_reasonable():
    # 서울(126.978E)은 135E 표준 대비 ~ -32분 + 균시차(수 분) → 대략 -40~-20분
    r = tc.correct(1990, 5, 20, 14, 30)
    assert -40 < r.eot_minutes < -20, r.eot_minutes
    assert r.true_solar < r.civil_local


def test_hour_branch_known():
    # 진태양시 약 13:58 → 未시(13:00~15:00)
    r = tc.correct(1990, 5, 20, 14, 30)
    assert r.hour_branch == "未", (r.hour_branch, r.true_solar)


def test_solarterms_skyfield_vs_lunar_python_1990():
    res = crosscheck.crosscheck_year(1990, tolerance_min=5.0)
    assert res["all_ok"], (res["max_diff_min"], [r for r in res["rows"] if not r.get("ok", True)])
    assert res["max_diff_min"] <= 5.0, res["max_diff_min"]


def test_solarterms_robust_other_year_2026():
    res = crosscheck.crosscheck_year(2026, tolerance_min=5.0)
    assert res["all_ok"], res["max_diff_min"]
