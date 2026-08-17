# -*- coding: utf-8 -*-
"""起紫微訣 꼬리 구간 표적 측정 — 음력 28·29·30일 + 윤달을 강제 포함.

앞선 랜덤 표본은 randint(1,28) 이라 음력 29·30일이 한 번도 나오지 않았다.
여기서는 KASI 캐시에서 lun_day in (28,29,30) 인 양력 날짜를 직접 뽑고,
각 날짜마다 12개 시지를 훑어 命宮(→五行局)을 골고루 흔든다.
목표: (局數 x 음력일) 조합 커버리지를 넓혀 起紫微訣의 差 최대 구간까지 밟는다.
"""
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from _ziwei_oracle import (  # noqa: E402
    GAN, KZHI, five_class, han_lunar_to_nums, soul_body, ziwei_pos,
)
from sajugen.calc import engine  # noqa: E402

con = sqlite3.connect("data/kasi_cache.sqlite")


def pick(lun_day, k, leap=0):
    rows = con.execute(
        "select sol_ymd,lun_month,lun_day,leap from lunar "
        "where lun_day=? and leap=? and sol_ymd between 19300101 and 20201231 "
        "order by sol_ymd",
        (lun_day, leap),
    ).fetchall()
    if not rows:
        return []
    step = max(1, len(rows) // k)
    return rows[::step][:k]


dates = []
for ld, k in ((28, 5), (29, 6), (30, 6)):
    dates += pick(ld, k)
for ld in (28, 29, 30):
    dates += pick(ld, 1, leap=1)

HOURS = list(range(0, 24, 2))  # 12 시지 블록 (분 45 -> 진태양시가 해당 시각대 중앙 부근)

R = {
    "cases": 0,
    "soul_ok": 0, "soul_ng": 0,
    "body_ok": 0, "body_ng": 0,
    "class_ok": 0, "class_ng": 0,
    "ziwei_ok": 0, "ziwei_ng": 0,
    "lunar_day_vs_kasi_ok": 0, "lunar_day_vs_kasi_ng": 0,
    "ng": [],
}
cover = defaultdict(set)   # 局數 -> {음력일}
diff_hist = defaultdict(int)  # 起紫微訣 差 값 분포
leap_seen = 0

for sol, klm, kld, kleap in dates:
    s = str(sol)
    y, mo, d = int(s[:4]), int(s[4:6]), int(s[6:])
    for h in HOURS:
        try:
            r = engine.build(y, mo, d, h, 45, is_male=(h % 4 == 0),
                             horoscope_date="2026-06-01")
        except Exception as exc:  # noqa: BLE001
            R["ng"].append({"k": "build", "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:45",
                            "err": type(exc).__name__})
            continue
        zw = r.ziwei
        R["cases"] += 1
        ts = datetime.strptime(r.true_solar, "%Y-%m-%d %H:%M:%S")
        hb = ((ts.hour + 1) // 2) % 12
        lm, ld, leap = han_lunar_to_nums(zw.lunar_date)
        if leap:
            leap_seen += 1

        # iztro 음력일 vs KASI 음력일 (한중 음력 차이는 최대 1일 — 그 이상이면 이상)
        if abs(ld - kld) <= 1:
            R["lunar_day_vs_kasi_ok"] += 1
        else:
            R["lunar_day_vs_kasi_ng"] += 1
            R["ng"].append({"k": "lunar", "in": f"{y}-{mo:02d}-{d:02d}",
                            "iztro": zw.lunar_date, "kasi_day": kld})

        eff_m = lm + 1 if (leap and ld >= 16) else lm
        s_i, b_i = soul_body(eff_m, hb)
        ygan = GAN.index(r.myeongni.year.ganzhi[0])
        _gz, ju, junum = five_class(ygan, s_i)
        zpos = ziwei_pos(junum, ld)

        cover[junum].add(ld)
        n = -(-ld // junum)
        diff_hist[junum * n - ld] += 1

        eng_soul = next((p.branch for p in zw.palaces if p.is_soul), "")
        eng_body = next((p.branch for p in zw.palaces if p.is_body), "")
        eng_zwp = next((p.branch for p in zw.palaces
                        for st in p.major_stars if st.name == "자미"), "")

        for key, e, o in (("soul", eng_soul, KZHI[s_i]),
                          ("body", eng_body, KZHI[b_i]),
                          ("class", zw.five_elements_class, ju),
                          ("ziwei", eng_zwp, KZHI[zpos])):
            if e == o:
                R[key + "_ok"] += 1
            else:
                R[key + "_ng"] += 1
                R["ng"].append({"k": key, "in": f"{y}-{mo:02d}-{d:02d} {h:02d}:45",
                                "lunar": f"{'윤' if leap else ''}{lm}/{ld}",
                                "ju": ju, "engine": e, "oracle": o})

R["dates_used"] = len(dates)
R["leap_cases"] = leap_seen
R["coverage_ju_x_day"] = {str(k): sorted(v) for k, v in sorted(cover.items())}
R["ziwei_diff_hist"] = {str(k): v for k, v in sorted(diff_hist.items())}
Path("tmp/_ziwei_tail.json").write_text(
    json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in R.items()
                  if k not in ("ng", "coverage_ju_x_day")}, ensure_ascii=True))
print("ng_count", len(R["ng"]))
for x in R["ng"][:10]:
    print(json.dumps(x, ensure_ascii=False))
