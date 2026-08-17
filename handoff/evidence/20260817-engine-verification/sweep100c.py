# -*- coding: utf-8 -*-
"""최종판 — 엔진 출력을 일절 참조하지 않는 독립 오라클.

진태양시를 NOAA 해석식으로 자체 계산(Skyfield 미사용)해 날짜·시각을 직접 도출한다.
따라서 '진태양시 날짜'가 틀렸다면 오라클과 KASI 가 함께 밀리는 순환이 성립하지 않는다.
대운수·起運연도도 절입까지의 일수에서 재도출한다(3일=1년, 1일=4개월).
"""
import json
import math
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine, solarterms  # noqa: E402

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
KGAN = "갑을병정무기경신임계"
KZHI = "자축인묘진사오미신유술해"
WUHU = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}
WUSHU = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
JIE = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]
LON = 126.9784


def eot_min(u):
    jd = u.toordinal() + 1721424.5 + (u.hour * 3600 + u.minute * 60 + u.second) / 86400.0
    t = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
    M = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    eps = 23.0 + (26.0 + ((21.448 - t * (46.815 + t * (0.00059 - t * 0.001813)))) / 60.0) / 60.0
    om = 125.04 - 1934.136 * t
    y = math.tan(math.radians((eps + 0.00256 * math.cos(math.radians(om))) / 2)) ** 2
    Lr, Mr = math.radians(L0), math.radians(M)
    E = (y * math.sin(2 * Lr) - 2 * e * math.sin(Mr) + 4 * e * y * math.sin(Mr) * math.cos(2 * Lr)
         - 0.5 * y * y * math.sin(4 * Lr) - 1.25 * e * e * math.sin(2 * Mr))
    return math.degrees(E) * 4.0


def jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def k2gz(s):
    if not s or "(" not in s:
        return None
    k = s.split("(")[0].strip()
    return GAN[KGAN.index(k[0])] + ZHI[KZHI.index(k[1])] if len(k) == 2 else None


def add_months(dt, months):
    m = dt.month - 1 + int(months)
    y = dt.year + m // 12
    m = m % 12 + 1
    d = min(dt.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return dt.replace(year=y, month=m, day=d)


random.seed(20260816)
cases = [(random.randint(1920, 2020), random.randint(1, 12), random.randint(1, 28),
          random.randint(0, 23), random.randint(0, 59), random.choice([True, False]))
         for _ in range(100)]

con = sqlite3.connect("data/kasi_cache.sqlite")
R = {"n": 0, "true_solar_match_sec_max": 0.0, "bazi_ok": 0, "bazi_ng": 0,
     "day_vs_kasi_ok": 0, "day_vs_kasi_ng": 0, "roll_cases": 0,
     "dw_floor": 0, "dw_round": 0, "dw_other": 0,
     "dw_start_year_ok": 0, "dw_start_year_ng": 0, "ng": []}

jcache = {}
for y, mo, d, h, mi, male in cases:
    r = engine.build(y, mo, d, h, mi, is_male=male, horoscope_date="2026-06-01")
    my = r.myeongni
    R["n"] += 1

    loc = datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("Asia/Seoul"))
    utc = loc.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    off = loc.utcoffset().total_seconds() / 3600.0
    # 독립 진태양시 (NOAA) — 엔진 출력 미참조
    corr = (LON - off * 15.0) * 4.0 + eot_min(utc)
    tso = datetime(y, mo, d, h, mi) + timedelta(minutes=corr)
    eng_ts = datetime.strptime(r.true_solar, "%Y-%m-%d %H:%M:%S")
    R["true_solar_match_sec_max"] = max(
        R["true_solar_match_sec_max"], abs((tso - eng_ts).total_seconds()))

    rolled = tso.hour >= 23
    if rolled:
        R["roll_cases"] += 1
    # 일주 = 독립 진태양시 날짜의 60갑자 (+ 자시정책 익일)
    di = (jdn(tso.year, tso.month, tso.day) + 49) % 60
    if rolled:
        di = (di + 1) % 60
    dgz = GAN[di % 10] + ZHI[di % 12]

    # KASI 대조: 위 di 가 가리키는 '실제 달력일'의 일진과 비교
    eff = tso.date() + timedelta(days=1 if rolled else 0)
    row = con.execute("select iljin from lunar where sol_ymd=?",
                      (int(eff.strftime("%Y%m%d")),)).fetchone()
    kas = k2gz(row[0]) if row else None
    if kas:
        if my.day.ganzhi == kas:
            R["day_vs_kasi_ok"] += 1
        else:
            R["day_vs_kasi_ng"] += 1
            R["ng"].append({"k": "day", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                            "engine": my.day.ganzhi, "kasi": kas,
                            "eff_date": str(eff), "rolled": rolled})

    ipchun = solarterms.solar_term_time(utc.year, 315)
    myr = utc.year if utc >= ipchun else utc.year - 1
    yi = (myr - 4) % 60
    mzhi, _, _ = solarterms.month_pillar_branch(utc)
    mzi = ZHI.index(mzhi)
    hb = ((tso.hour + 1) // 2) % 12
    oracle = "%s%s %s%s %s %s%s" % (
        GAN[yi % 10], ZHI[yi % 12],
        GAN[(WUHU[yi % 10] + ((mzi - 2) % 12)) % 10], mzhi, dgz,
        GAN[(WUSHU[di % 10] + hb) % 10], ZHI[hb])
    eng = f"{my.year.ganzhi} {my.month.ganzhi} {my.day.ganzhi} {my.hour.ganzhi}"
    if oracle == eng:
        R["bazi_ok"] += 1
    else:
        R["bazi_ng"] += 1
        R["ng"].append({"k": "bazi", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                        "engine": eng, "oracle": oracle})

    # 대운수 / 起運 연도
    if utc.year not in jcache:
        jcache[utc.year] = sorted({solarterms.solar_term_time(yy, dg)
                                   for yy in (utc.year - 1, utc.year, utc.year + 1)
                                   for dg in JIE})
    jts = jcache[utc.year]
    nxt_j = min((t for t in jts if t > utc), default=None)
    prv_j = max((t for t in jts if t <= utc), default=None)
    if nxt_j and prv_j:
        days = ((nxt_j - utc) if my.daewoon_forward else (utc - prv_j)).total_seconds() / 86400.0
        yrs = days / 3.0
        fl, rd = int(yrs), int(yrs + 0.5)
        if my.daewoon_count == fl:
            R["dw_floor"] += 1
        elif my.daewoon_count == rd:
            R["dw_round"] += 1
        else:
            R["dw_other"] += 1
            R["ng"].append({"k": "dw", "in": f"{y}-{mo:02d}-{d:02d}",
                            "engine": my.daewoon_count, "days": round(days, 3),
                            "yrs": round(yrs, 3), "fwd": my.daewoon_forward})
        # 起運 시점 = 출생 + days*4 개월 -> 그 연도
        qi = add_months(datetime(y, mo, d), days * 4)
        if my.daewoon and abs(my.daewoon[0].start_year - qi.year) <= 1:
            R["dw_start_year_ok"] += 1
        elif my.daewoon:
            R["dw_start_year_ng"] += 1
            R["ng"].append({"k": "dw_year", "in": f"{y}-{mo:02d}-{d:02d}",
                            "engine": my.daewoon[0].start_year, "oracle": qi.year})

R["true_solar_match_sec_max"] = round(R["true_solar_match_sec_max"], 1)
Path("tmp/_sweep100c.json").write_text(json.dumps(R, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
print(json.dumps({k: v for k, v in R.items() if k != "ng"}, ensure_ascii=True))
print("ng_count", len(R["ng"]))
for x in R["ng"][:10]:
    print(json.dumps(x, ensure_ascii=True))
