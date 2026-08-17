# -*- coding: utf-8 -*-
"""엔진 Skyfield 절기 시각 vs KASI 원본 절기(2000~2027, 672행) 전수 대조.

이름 매핑 없이 '가장 가까운 엔진 절기'로 매칭해 분 단위 차이를 측정한다
(프로젝트의 crosscheck 래퍼를 쓰지 않는 독립 경로).
"""
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import solarterms as st  # noqa: E402

DEGS = list(range(0, 360, 15))

con = sqlite3.connect("data/kasi_cache.sqlite")
rows = con.execute(
    "select year,term,locdate,kst_min,raw_name from solarterm order by year,locdate"
).fetchall()

# 연도별 엔진 절기 시각(KST) 캐시
eng = {}
for y in sorted({r[0] for r in rows}):
    pts = []
    for d in DEGS:
        for yy in (y - 1, y, y + 1):
            t = st.solar_term_time(yy, d) + timedelta(hours=9)
            if t.year == y:
                pts.append(t)
    eng[y] = sorted(set(pts))

diffs = []
for year, term, locdate, kst_min, raw in rows:
    s = str(locdate)
    kt = datetime(int(s[:4]), int(s[4:6]), int(s[6:])) + timedelta(minutes=int(kst_min))
    best = min(eng[year], key=lambda t: abs((t - kt).total_seconds()))
    diffs.append(
        {
            "year": year,
            "term": term,
            "kasi": kt.strftime("%Y-%m-%d %H:%M"),
            "engine": best.strftime("%Y-%m-%d %H:%M:%S"),
            "diff_min": round((best - kt).total_seconds() / 60.0, 2),
        }
    )

within2 = [d for d in diffs if abs(d["diff_min"]) <= 2.0]
over2 = [d for d in diffs if abs(d["diff_min"]) > 2.0]
out = {
    "rows": len(diffs),
    "within_2min": len(within2),
    "over_2min": len(over2),
    "max_abs_diff_min_within": round(max((abs(d["diff_min"]) for d in within2), default=0), 2),
    "over_2min_detail": over2,
}
Path("tmp/_terms_vs_kasi.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(json.dumps({k: v for k, v in out.items() if k != "over_2min_detail"}, ensure_ascii=True))
for d in over2:
    print("OVER", d["year"], d["kasi"], "->", d["engine"], d["diff_min"])
