# -*- coding: utf-8 -*-
"""Skyfield 기반 24절기(節氣) 정밀 시각 — 태양 겉보기 황경이 15°의 배수가 되는 순간.

월주(月柱)·세운 경계는 12'節'(입춘·경칩·청명...)의 절입(節入) 시각을 기준으로 한다.
이분법으로 황경 = 목표각 이 되는 UTC 시각을 초 단위로 수렴.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from skyfield.api import Loader

_loader = Loader(r"C:\Users\pc\test-project\sajugen\assets\ephemeris")
_eph = _loader("de440s.bsp")
_ts = _loader.timescale()
_earth, _sun = _eph["earth"], _eph["sun"]

# 24절기 황경(°)→이름. 절입(월건) 12節은 below TwelveJie.
TERMS = {
    315: "立春",
    330: "雨水",
    345: "驚蟄",
    0: "春分",
    15: "清明",
    30: "穀雨",
    45: "立夏",
    60: "小滿",
    75: "芒種",
    90: "夏至",
    105: "小暑",
    120: "大暑",
    135: "立秋",
    150: "處暑",
    165: "白露",
    180: "秋分",
    195: "寒露",
    210: "霜降",
    225: "立冬",
    240: "小雪",
    255: "大雪",
    270: "冬至",
    285: "小寒",
    300: "大寒",
}
# 월건을 세우는 12節(절입). 立春=寅月 시작.
TWELVE_JIE = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
JIE_TO_MONTH_BRANCH = dict(zip(TWELVE_JIE, "寅卯辰巳午未申酉戌亥子丑"))


def _sun_eclon_deg(dt_utc: datetime) -> float:
    t = _ts.from_datetime(dt_utc.replace(tzinfo=timezone.utc))
    lat, lon, _ = _earth.at(t).observe(_sun).apparent().ecliptic_latlon("date")
    return lon.degrees % 360.0


def _norm(diff: float) -> float:
    """각도 차를 (-180,180]로."""
    return (diff + 180.0) % 360.0 - 180.0


def solar_term_time(year: int, target_lon: float) -> datetime:
    """해당 **그레고리력 연도(year) 안에서** 태양 황경이 target_lon(°)이 되는 UTC 시각.

    각 15° 황경은 한 해에 정확히 한 번 통과한다. 근사식의 0°/360° 경계 오류를
    피하기 위해 연중 5일 간격 거친 스캔으로 부호변화 구간을 찾은 뒤 이분법 수렴.
    """

    def f(dt: datetime) -> float:
        return _norm(_sun_eclon_deg(dt) - target_lon)

    step = timedelta(days=5)
    cur = datetime(year, 1, 1)
    end = datetime(year + 1, 1, 1)
    prev_dt, prev_v = cur, f(cur)
    bracket: tuple[datetime, datetime] | None = None
    while cur < end:
        cur += step
        v = f(cur)
        if (prev_v <= 0) != (v <= 0) and abs(prev_v - v) < 90:  # 인접 절기 통과
            bracket = (prev_dt, cur)
            break
        prev_dt, prev_v = cur, v
    if bracket is None:  # 연초/연말 경계 보정
        bracket = (datetime(year, 1, 1), datetime(year, 1, 6))

    lo, hi = bracket
    flo = f(lo)
    for _ in range(60):
        mid = lo + (hi - lo) / 2
        fmid = f(mid)
        if (flo <= 0) == (fmid <= 0):
            lo, flo = mid, fmid
        else:
            hi = mid
        if (hi - lo).total_seconds() < 1:
            break
    return lo + (hi - lo) / 2


def all_terms_utc(year: int) -> dict[str, datetime]:
    """그 해의 24절기 UTC 시각."""
    return {name: solar_term_time(year, lon) for lon, name in TERMS.items()}


def month_pillar_branch(dt_utc: datetime) -> tuple[str, str, datetime]:
    """해당 시점이 속한 월건(月支)과 직전 절입(節)·그 시각 반환."""
    y = dt_utc.year
    cands: list[tuple[datetime, int]] = []
    for yy in (y - 1, y, y + 1):
        for jl in TWELVE_JIE:
            cands.append((solar_term_time(yy, jl), jl))
    cands.sort()
    prev = [(t, jl) for t, jl in cands if t <= dt_utc.replace(tzinfo=None)][-1]
    jie_name = TERMS[prev[1]]
    return JIE_TO_MONTH_BRANCH[prev[1]], jie_name, prev[0]
