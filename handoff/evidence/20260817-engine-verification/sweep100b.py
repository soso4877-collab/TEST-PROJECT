# -*- coding: utf-8 -*-
"""수정판 스윕 — (1) KASI 조회 키를 '시민 입력 날짜'로 고정(엔진 출력 미사용),
(2) 진태양시 날짜 == 시민 날짜 불변식 프로브, (3) 대운수 독립 재도출 대조.

(1)(2)가 핵심: 기존 판은 조회 키를 engine.true_solar 에서 뽑아, 진태양시 '날짜'가
틀려도 오라클과 KASI 행이 함께 밀려 100% 일치가 나올 수 있었다(calc.md 가 경고한
KST 새벽 -1일 버그의 사각). 여기서는 키를 입력값에서만 만든다.
"""
import json
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
# 12 節(월건 경계) 황경
JIE = [315, 345, 15, 45, 75, 105, 135, 165, 195, 225, 255, 285]


def jdn(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def k2gz(s):
    if not s or "(" not in s:
        return None
    k = s.split("(")[0].strip()
    if len(k) != 2 or k[0] not in KGAN or k[1] not in KZHI:
        return None
    return GAN[KGAN.index(k[0])] + ZHI[KZHI.index(k[1])]


def jie_times(year):
    out = []
    for yy in (year - 1, year, year + 1):
        for deg in JIE:
            t = solarterms.solar_term_time(yy, deg)
            out.append(t)
    return sorted(set(out))


random.seed(20260816)
cases = []
while len(cases) < 100:
    cases.append(
        (
            random.randint(1920, 2020),
            random.randint(1, 12),
            random.randint(1, 28),
            random.randint(0, 23),
            random.randint(0, 59),
            random.choice([True, False]),
        )
    )

con = sqlite3.connect("data/kasi_cache.sqlite")
R = {
    "n": 0,
    "true_solar_date_eq_civil_date": 0,
    "true_solar_date_ne_civil_date": 0,
    "date_ne_samples": [],
    "day_vs_kasi_ok": 0,
    "day_vs_kasi_roll_ok": 0,
    "day_vs_kasi_ng": 0,
    "bazi_vs_oracle_ok": 0,
    "bazi_vs_oracle_ng": 0,
    "daewoon_count_floor_match": 0,
    "daewoon_count_round_match": 0,
    "daewoon_count_other": 0,
    "daewoon_start_year_match": 0,
    "daewoon_start_year_ng": 0,
    "ng": [],
}

for y, mo, d, h, mi, male in cases:
    r = engine.build(y, mo, d, h, mi, is_male=male, horoscope_date="2026-06-01")
    my = r.myeongni
    R["n"] += 1
    ts = datetime.strptime(r.true_solar, "%Y-%m-%d %H:%M:%S")

    # (2) 불변식: 진태양시 날짜 == 시민 입력 날짜
    if (ts.year, ts.month, ts.day) == (y, mo, d):
        R["true_solar_date_eq_civil_date"] += 1
    else:
        R["true_solar_date_ne_civil_date"] += 1
        if len(R["date_ne_samples"]) < 5:
            R["date_ne_samples"].append(
                {"in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}", "true_solar": r.true_solar}
            )

    # (1) KASI 조회 키 = 시민 입력 날짜 (엔진 출력 미사용)
    key = int("%04d%02d%02d" % (y, mo, d))
    row = con.execute("select iljin from lunar where sol_ymd=?", (key,)).fetchone()
    kas = k2gz(row[0]) if row else None
    rolled = ts.hour >= 23  # 자시 정책은 '시각'만 사용, 날짜 미사용
    if kas:
        if not rolled:
            if my.day.ganzhi == kas:
                R["day_vs_kasi_ok"] += 1
            else:
                R["day_vs_kasi_ng"] += 1
                R["ng"].append({"k": "day", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                                "engine": my.day.ganzhi, "kasi": kas})
        else:
            nxt = con.execute(
                "select iljin from lunar where sol_ymd>? order by sol_ymd limit 1", (key,)
            ).fetchone()
            if nxt and my.day.ganzhi == k2gz(nxt[0]):
                R["day_vs_kasi_roll_ok"] += 1
            else:
                R["day_vs_kasi_ng"] += 1
                R["ng"].append({"k": "day-roll", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                                "engine": my.day.ganzhi,
                                "kasi_next": k2gz(nxt[0]) if nxt else None})

    # 4기둥 오라클 (일주 키도 시민 날짜 기준)
    utc = datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("Asia/Seoul")).astimezone(
        ZoneInfo("UTC")
    ).replace(tzinfo=None)
    ipchun = solarterms.solar_term_time(utc.year, 315)
    myr = utc.year if utc >= ipchun else utc.year - 1
    yi = (myr - 4) % 60
    mzhi, _, _ = solarterms.month_pillar_branch(utc)
    mzi = ZHI.index(mzhi)
    di = (jdn(y, mo, d) + 49) % 60
    if rolled:
        di = (di + 1) % 60
    hb = ((ts.hour + 1) // 2) % 12
    oracle = "%s%s %s%s %s%s %s%s" % (
        GAN[yi % 10], ZHI[yi % 12],
        GAN[(WUHU[yi % 10] + ((mzi - 2) % 12)) % 10], mzhi,
        GAN[di % 10], ZHI[di % 12],
        GAN[(WUSHU[di % 10] + hb) % 10], ZHI[hb],
    )
    eng = f"{my.year.ganzhi} {my.month.ganzhi} {my.day.ganzhi} {my.hour.ganzhi}"
    if oracle == eng:
        R["bazi_vs_oracle_ok"] += 1
    else:
        R["bazi_vs_oracle_ng"] += 1
        R["ng"].append({"k": "bazi", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                        "engine": eng, "oracle": oracle})

    # (3) 대운수 독립 재도출: 3일=1년. 순행=다음 節까지, 역행=이전 節부터.
    jts = jie_times(utc.year)
    nxt_j = min((t for t in jts if t > utc), default=None)
    prv_j = max((t for t in jts if t <= utc), default=None)
    if nxt_j and prv_j:
        days = ((nxt_j - utc) if my.daewoon_forward else (utc - prv_j)).total_seconds() / 86400.0
        yrs = days / 3.0
        fl, rd = int(yrs), int(yrs + 0.5)
        if my.daewoon_count == fl:
            R["daewoon_count_floor_match"] += 1
        elif my.daewoon_count == rd:
            R["daewoon_count_round_match"] += 1
        else:
            R["daewoon_count_other"] += 1
            R["ng"].append({"k": "daewoon", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                            "engine_count": my.daewoon_count, "days": round(days, 3),
                            "yrs": round(yrs, 3), "forward": my.daewoon_forward})
    if my.daewoon:
        if my.daewoon[0].start_year == y + my.daewoon_count:
            R["daewoon_start_year_match"] += 1
        else:
            R["daewoon_start_year_ng"] += 1

Path("tmp/_sweep100b.json").write_text(
    json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(json.dumps({k: v for k, v in R.items() if k not in ("ng", "date_ne_samples")},
                 ensure_ascii=True))
print("ng_count", len(R["ng"]))
for x in R["ng"][:8]:
    print(json.dumps(x, ensure_ascii=True))
