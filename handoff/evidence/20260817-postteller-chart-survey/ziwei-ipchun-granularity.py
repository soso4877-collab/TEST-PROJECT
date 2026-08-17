# -*- coding: utf-8 -*-
"""자미(iztro)의 입춘 판정 정확도 — 시진(2시간) 단위 해상도 문제 확인.

`calc/ziwei.py:83-84` 는 iztro 에 **날짜 + time_index(시진)** 만 넘긴다. 분은 안 넘어간다.
자미두수의 五行局·사화는 **연간**에서 나오고, 연간은 입춘으로 갈린다.
따라서 입춘이 시진 한가운데 떨어지면 iztro 는 그 시진 전체를 한쪽으로 몰아버린다.

여러 해의 입춘에 대해 iztro 연간이 실제로 몇 시에 뒤집히는지 재고, 정답과의 오차를 낸다.
콘솔 ASCII.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sajugen.calc import engine  # noqa: E402
from sajugen.calc import solarterms  # noqa: E402

OUT = Path(__file__).resolve().parent


def year_stems(t: datetime):
    """그 시민시각의 명리 연주 / 자미 연주."""
    r = engine.build(t.year, t.month, t.day, t.hour, t.minute, is_male=True)
    my = r.crosscheck.bazi_myeongni.split()[0]
    zw = r.ziwei.chinese_date.split()[0]
    return my, zw


def find_flip(kst_term: datetime, getter):
    """입춘 전후 ±150분에서 연주가 바뀌는 시민시각(분)을 이분 탐색."""
    lo, hi = -150, 150
    vlo = getter(kst_term + timedelta(minutes=lo))
    vhi = getter(kst_term + timedelta(minutes=hi))
    if vlo == vhi:
        return None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if getter(kst_term + timedelta(minutes=mid)) == vlo:
            lo = mid
        else:
            hi = mid
    return kst_term + timedelta(minutes=hi)


rows = []
for y in (1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020):
    utc = solarterms.solar_term_time(y, 315).replace(tzinfo=None)
    kst = utc + timedelta(hours=9)
    f_my = find_flip(kst, lambda t: year_stems(t)[0])
    f_zw = find_flip(kst, lambda t: year_stems(t)[1])
    rows.append({
        "year": y,
        "ipchun_kst": kst.isoformat(sep=" "),
        "myeongni_flip": f_my.isoformat(sep=" ") if f_my else None,
        "ziwei_flip": f_zw.isoformat(sep=" ") if f_zw else None,
        "myeongni_err_min": round((f_my - kst).total_seconds() / 60, 1) if f_my else None,
        "ziwei_err_min": round((f_zw - kst).total_seconds() / 60, 1) if f_zw else None,
    })

me = [abs(r["myeongni_err_min"]) for r in rows if r["myeongni_err_min"] is not None]
ze = [abs(r["ziwei_err_min"]) for r in rows if r["ziwei_err_min"] is not None]
summary = {
    "years": len(rows),
    "myeongni_abs_err_max": max(me) if me else None,
    "myeongni_abs_err_mean": round(sum(me) / len(me), 1) if me else None,
    "ziwei_abs_err_max": max(ze) if ze else None,
    "ziwei_abs_err_mean": round(sum(ze) / len(ze), 1) if ze else None,
}

(OUT / "ziwei-ipchun-granularity.json").write_text(
    json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1),
    encoding="utf-8")

print(json.dumps(summary, ensure_ascii=True))
print("year  ipchun_kst           myeongni_err  ziwei_err")
for r in rows:
    print("  %d  %s   %+8s   %+8s" % (
        r["year"], r["ipchun_kst"], r["myeongni_err_min"], r["ziwei_err_min"]))
