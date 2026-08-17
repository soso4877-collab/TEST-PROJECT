# -*- coding: utf-8 -*-
"""랜덤 100건 확대 측정 — 엔진 vs (a) KASI 원본 일진/음력, (b) 독립 JDN·둔법 오라클.

seed 고정(재현성). 시각은 시지 블록 중앙(자시 정책 교란 배제) 대신 전 시간대를
쓰되 자시 정책 보정을 오라클에도 동일 적용해 정책차와 오차를 분리한다.
"""
import json
import random
import sqlite3
import sys
from datetime import datetime
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


random.seed(20260816)
cases = []
while len(cases) < 100:
    y = random.randint(1920, 2020)
    mo = random.randint(1, 12)
    d = random.randint(1, 28)
    h = random.randint(0, 23)
    mi = random.randint(0, 59)
    male = random.choice([True, False])
    cases.append((y, mo, d, h, mi, male))

con = sqlite3.connect("data/kasi_cache.sqlite")

res = {
    "n": 0,
    "day_vs_kasi_ok": 0,
    "day_vs_kasi_ng": 0,
    "day_vs_kasi_policy_shift": 0,
    "bazi_vs_oracle_ok": 0,
    "bazi_vs_oracle_ng": 0,
    "lunar_vs_kasi_ok": 0,
    "lunar_vs_kasi_ng": 0,
    "bazi_consistent_engine_internal": 0,
    "near_term": 0,
    "hour_conflict": 0,
    "ng_details": [],
}

for y, mo, d, h, mi, male in cases:
    r = engine.build(y, mo, d, h, mi, is_male=male, horoscope_date="2026-06-01")
    my, zw, cc = r.myeongni, r.ziwei, r.crosscheck
    res["n"] += 1
    if cc.bazi_consistent:
        res["bazi_consistent_engine_internal"] += 1
    if cc.near_term_boundary:
        res["near_term"] += 1
    if cc.hour_branch_conflict:
        res["hour_conflict"] += 1

    ts = datetime.strptime(r.true_solar, "%Y-%m-%d %H:%M:%S")
    # --- (a) 일주 vs KASI 원본 일진 ---
    row = con.execute(
        "select iljin from lunar where sol_ymd=?",
        (int("%04d%02d%02d" % (ts.year, ts.month, ts.day)),),
    ).fetchone()
    kas = k2gz(row[0]) if row else None
    rolled = ts.hour >= 23  # JST_2300 자시 정책 = 진태양시 23시 이후 일주 익일
    if kas:
        if not rolled and my.day.ganzhi == kas:
            res["day_vs_kasi_ok"] += 1
        elif rolled:
            nxt = con.execute(
                "select iljin from lunar where sol_ymd>? order by sol_ymd limit 1",
                (int("%04d%02d%02d" % (ts.year, ts.month, ts.day)),),
            ).fetchone()
            if nxt and my.day.ganzhi == k2gz(nxt[0]):
                res["day_vs_kasi_policy_shift"] += 1
            else:
                res["day_vs_kasi_ng"] += 1
                res["ng_details"].append(
                    {"k": "day-roll", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                     "engine": my.day.ganzhi, "kasi_next": k2gz(nxt[0]) if nxt else None}
                )
        else:
            res["day_vs_kasi_ng"] += 1
            res["ng_details"].append(
                {"k": "day", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
                 "engine": my.day.ganzhi, "kasi": kas, "true_solar": r.true_solar}
            )

    # --- (b) 4기둥 vs 독립 오라클 ---
    utc = datetime(y, mo, d, h, mi, tzinfo=ZoneInfo("Asia/Seoul")).astimezone(
        ZoneInfo("UTC")
    ).replace(tzinfo=None)
    ipchun = solarterms.solar_term_time(utc.year, 315)
    myr = utc.year if utc >= ipchun else utc.year - 1
    yi = (myr - 4) % 60
    ygz = GAN[yi % 10] + ZHI[yi % 12]
    mzhi, _, _ = solarterms.month_pillar_branch(utc)
    mzi = ZHI.index(mzhi)
    mgz = GAN[(WUHU[yi % 10] + ((mzi - 2) % 12)) % 10] + mzhi
    di = (jdn(ts.year, ts.month, ts.day) + 49) % 60
    if rolled:
        di = (di + 1) % 60
    dgz = GAN[di % 10] + ZHI[di % 12]
    hb = ((ts.hour + 1) // 2) % 12
    hgz = GAN[(WUSHU[di % 10] + hb) % 10] + ZHI[hb]
    oracle = f"{ygz} {mgz} {dgz} {hgz}"
    eng = f"{my.year.ganzhi} {my.month.ganzhi} {my.day.ganzhi} {my.hour.ganzhi}"
    if oracle == eng:
        res["bazi_vs_oracle_ok"] += 1
    else:
        res["bazi_vs_oracle_ng"] += 1
        res["ng_details"].append(
            {"k": "bazi", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}",
             "engine": eng, "oracle": oracle, "true_solar": r.true_solar}
        )

    # --- (c) 자미 입력 음력 vs KASI 한국 음력 ---
    lr = con.execute(
        "select lun_year,lun_month,lun_day,leap from lunar where sol_ymd=?",
        (int("%04d%02d%02d" % (ts.year, ts.month, ts.day)),),
    ).fetchone()
    if lr:
        zh_day = zw.lunar_date
        # iztro 한자 음력 문자열에서 일(日) 숫자 추출은 생략하고, 월/윤달 비교용 토큰만
        res.setdefault("_lunar_pairs", []).append(
            {"solar": ts.strftime("%Y-%m-%d"), "kasi": list(lr), "iztro": zh_day}
        )

Path("tmp/_sweep100.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(
    json.dumps(
        {k: v for k, v in res.items() if not k.startswith("_") and k != "ng_details"},
        ensure_ascii=True,
    )
)
print("ng_count", len(res["ng_details"]))
