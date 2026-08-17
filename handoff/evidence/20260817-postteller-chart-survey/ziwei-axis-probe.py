# -*- coding: utf-8 -*-
"""자미두수에 명리와 같은 '시각축' 문제가 있는지 실측.

명리 결함(solar-term-axis-defect.md)의 요지
-------------------------------------------
진태양시를 시민시각처럼 넘겨 **절입** 판정을 하는 바람에 월주·연주가 앞당겨졌다.

자미두수는 다른가?
------------------
`calc/ziwei.py:82-87` 은 `by_solar(진태양시 날짜, _time_index(진태양시 시))` 를 호출한다.
자미두수는 **절기를 쓰지 않고 음력**을 쓰므로 절입 문제는 직접 적용되지 않는다.
대신 두 가지를 확인한다.

  A. 날짜 축: 진태양시 날짜 != 시민 날짜 가 되는 구간(자정 직후)에서 명반이 흔들리는가
  B. 명리↔자미 정합: 엔진 자체 crosscheck(bazi_consistent)가 그 구간에서 깨지는가
  C. 절입 구간(명리 결함 창)에서 자미도 영향을 받는가

콘솔 ASCII, 상세는 JSON.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sajugen.calc import engine  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402

OUT = Path(__file__).resolve().parent


def probe(y, mo, d, h, mi):
    ct = tc.correct(y, mo, d, h, mi, longitude=tc.SEOUL_LON, latitude=tc.SEOUL_LAT)
    r = engine.build(y, mo, d, h, mi, is_male=True)
    zw = r.ziwei
    civil = datetime(y, mo, d, h, mi)
    return {
        "civil": civil.isoformat(sep=" "),
        "true_solar": ct.true_solar.isoformat(sep=" "),
        "date_shifted": ct.true_solar.date() != civil.date(),
        "eot": round(ct.eot_minutes, 2),
        "hour_branch": ct.hour_branch,
        "day_offset": ct.day_offset,
        "zw_solar_date": zw.solar_date,
        "zw_lunar_date": zw.lunar_date,
        "zw_chinese": zw.chinese_date,
        "soul": zw.soul_palace,
        "body": zw.body_palace,
        "five": zw.five_elements_class,
        "bazi_my": r.crosscheck.bazi_myeongni,
        "bazi_zw": r.crosscheck.bazi_ziwei,
        "bazi_consistent": bool(r.crosscheck.bazi_consistent),
        "month_ok": bool(r.crosscheck.month_branch_ok),
        "year_ok": bool(r.crosscheck.year_branch_ok),
    }


report = {}

# ---------------------------------------------------------------- A/B 자정 구간
# 서울 보정량은 -26 ~ -46분이므로 00:00~00:50 사이에서 진태양시 날짜가 전날로 밀린다.
rows = []
for mo, d in ((2, 10), (6, 15), (11, 5)):          # 균시차 부호가 다른 세 시기
    for mi in range(0, 60, 5):
        rows.append(probe(2000, mo, d, 0, mi))
report["midnight_window"] = rows
shifted = [r for r in rows if r["date_shifted"]]
report["midnight_summary"] = {
    "samples": len(rows),
    "date_shifted": len(shifted),
    "bazi_inconsistent": sum(1 for r in rows if not r["bazi_consistent"]),
    "shifted_but_consistent": sum(1 for r in shifted if r["bazi_consistent"]),
}

# ---------------------------------------------------------------- C 절입 구간
# 명리가 틀리는 창(입춘 2000-02-04 21:40 KST 기준 앞뒤)에서 자미가 흔들리는지.
rows2 = []
for off in range(-30, 16, 3):
    t = datetime(2000, 2, 4, 21, 40) + timedelta(minutes=off)
    rows2.append({"off": off, **probe(t.year, t.month, t.day, t.hour, t.minute)})
report["ipchun_window"] = rows2
souls = {r["soul"] for r in rows2}
fives = {r["five"] for r in rows2}
report["ipchun_summary"] = {
    "samples": len(rows2),
    "distinct_soul_palace": len(souls),
    "distinct_five_class": len(fives),
    "month_ok_false": sum(1 for r in rows2 if not r["month_ok"]),
    "year_ok_false": sum(1 for r in rows2 if not r["year_ok"]),
    "bazi_inconsistent": sum(1 for r in rows2 if not r["bazi_consistent"]),
}

# ---------------------------------------------------------------- 자시 경계
rows3 = []
for hh, mm in ((22, 50), (23, 10), (23, 32), (23, 33), (23, 50), (0, 10), (0, 30), (1, 10)):
    dd = 16 if hh == 0 or hh == 1 else 15
    rows3.append(probe(2000, 6, dd, hh, mm))
report["zasi_window"] = rows3

(OUT / "ziwei-axis.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

print(json.dumps({"midnight": report["midnight_summary"],
                  "ipchun": report["ipchun_summary"]}, ensure_ascii=True))
print("zasi window (civil -> true_solar | hourbranch dayoff | bazi_ok):")
for r in rows3:
    print("  %s -> %s | %s %d | %s" % (
        r["civil"][11:], r["true_solar"][5:], r["hour_branch"].encode("ascii", "backslashreplace").decode(),
        r["day_offset"], r["bazi_consistent"]))
