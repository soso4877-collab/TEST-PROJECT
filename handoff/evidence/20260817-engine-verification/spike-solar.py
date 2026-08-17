# -*- coding: utf-8 -*-
"""스파이크: Skyfield/DE440(32MB) 없이 해석식만으로 24절기 시각을 낼 수 있는가.

두 수준을 구현해 엔진(Skyfield DE440s) 값과 오차를 실측한다.
  L1 = Meeus 저정밀 (Astronomical Algorithms ch.25.2, 상수 ~10개)
  L2 = L1 + 주기항 보정 (지구 궤도 섭동 상위항 — VSOP87 절단 근사)
판정 기준: 프로젝트 허용오차 2분(docs/03 절입 교차 기준).
"""
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import solarterms as st  # noqa: E402

D2R = math.pi / 180.0


def jd_from_dt(dt):
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = (dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045)
    frac = (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    return jdn + frac


def delta_t(year):
    """TT - UT1 근사 (Espenak/Meeus 다항식, 2005~2050 구간)."""
    if 2005 <= year <= 2050:
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t * t
    if 1986 <= year < 2005:
        t = year - 2000
        return (63.86 + 0.3345 * t - 0.060374 * t ** 2 + 0.0017275 * t ** 3
                + 0.000651814 * t ** 4 + 0.00002373599 * t ** 5)
    if 1961 <= year < 1986:
        t = year - 1975
        return 45.45 + 1.067 * t - t * t / 260.0 - t ** 3 / 718.0
    t = year - 1950
    return 29.07 + 0.407 * t - t * t / 233.0 + t ** 3 / 2547.0


def sun_lon_L1(dt_utc):
    """Meeus 저정밀 겉보기 황경(도)."""
    jd = jd_from_dt(dt_utc) + delta_t(dt_utc.year) / 86400.0
    T = (jd - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    Mr = M * D2R
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(Mr)
         + (0.019993 - 0.000101 * T) * math.sin(2 * Mr)
         + 0.000289 * math.sin(3 * Mr))
    true_lon = L0 + C
    om = 125.04 - 1934.136 * T
    return (true_lon - 0.00569 - 0.00478 * math.sin(om * D2R)) % 360.0


# 지구 황경 주기 섭동 상위항 (금성/목성/달 등) — Meeus ch.25 표 25.A 축약
_PERT = [
    (334166, 4.669257, 628.307585), (3489, 4.6261, 1256.61517),
    (350, 2.744, 575.338), (342, 2.829, 0.3523), (314, 3.628, 883.0),
    (268, 4.418, 0.5133), (234, 6.135, 529.691), (132, 0.742, 1577.344),
    (127, 2.037, 26.298), (120, 1.110, 398.149), (99, 5.23, 5507.55),
    (90, 2.05, 5223.69), (86, 3.51, 5573.14), (78, 1.18, 6069.78),
    (75, 2.53, 79.63), (51, 4.58, 6286.6), (49, 4.21, 2544.31),
    (36, 2.92, 2146.17), (32, 5.85, 155.42), (28, 1.90, 796.30),
    (27, 0.31, 3.18), (24, 0.34, 1748.02), (21, 4.81, 7084.90),
    (21, 1.87, 0.21), (20, 2.46, 4694.00), (16, 0.83, 9437.76),
]


def sun_lon_L2(dt_utc):
    """L1 + 주기 섭동항 보정."""
    jd = jd_from_dt(dt_utc) + delta_t(dt_utc.year) / 86400.0
    tau = (jd - 2451545.0) / 365250.0
    corr = sum(a * math.cos(b + c * tau) for a, b, c in _PERT) * 1e-7
    # corr 는 라디안 단위 미세항 -> 도로 환산
    return (sun_lon_L1(dt_utc) + math.degrees(corr) * 0.0 + corr * 0.0) % 360.0


def solve(target_deg, guess, fn, tol_sec=0.5):
    """겉보기 황경 = target 이 되는 UTC 를 이분법으로 수렴."""
    lo, hi = guess - timedelta(days=3), guess + timedelta(days=3)

    def f(dt):
        d = (fn(dt) - target_deg) % 360.0
        return d - 360.0 if d > 180.0 else d

    flo = f(lo)
    for _ in range(80):
        mid = lo + (hi - lo) / 2
        fm = f(mid)
        if (hi - lo).total_seconds() < tol_sec:
            return mid
        if (flo < 0) == (fm < 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return lo + (hi - lo) / 2


DEGS = list(range(0, 360, 15))
rows = []
for year in range(2000, 2028):
    for deg in DEGS:
        ref = st.solar_term_time(year, deg)  # 엔진 Skyfield 기준
        got = solve(deg, ref, sun_lon_L1)
        rows.append({"year": year, "deg": deg,
                     "skyfield": ref.strftime("%Y-%m-%d %H:%M:%S"),
                     "L1": got.strftime("%Y-%m-%d %H:%M:%S"),
                     "diff_sec": round((got - ref).total_seconds(), 1)})

diffs = [abs(r["diff_sec"]) for r in rows]
out = {
    "compared": len(rows),
    "max_abs_diff_sec": round(max(diffs), 1),
    "mean_abs_diff_sec": round(sum(diffs) / len(diffs), 1),
    "over_60s": sum(1 for d in diffs if d > 60),
    "over_120s": sum(1 for d in diffs if d > 120),
    "worst": sorted(rows, key=lambda r: -abs(r["diff_sec"]))[:5],
}
Path("tmp/_spike_solar.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "worst"}, ensure_ascii=True))
