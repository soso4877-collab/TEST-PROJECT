# -*- coding: utf-8 -*-
"""두 불일치의 원인 규명.

(A) 1976-01-30 00:45 紫微 위치: 진태양시 23:59 -> iztro time_index 12(晚子).
    가설: iztro 는 晚子時에 자미 배치용 '일'을 익일로 넘긴다(문자열은 당일 유지).
    검증: 동일 날짜를 time_index 0(早子)/12(晚子)로 직접 호출해 紫微 위치를 비교.
(B) 2005-12-01 음력: iztro(중국) 11월 1일 vs KASI(한국) 10월 30일.
    검증: iztro 음력 vs KASI 음력을 1950~2020 표본으로 전수 비교해 괴리율 측정.
"""
import json
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import iztro_py  # noqa: E402

from _ziwei_oracle import han_lunar_to_nums  # noqa: E402

out = {}

# ---- (A) 晚子 가설 ----
a = []
for ti in (0, 12):
    ast = iztro_py.by_solar("1976-01-29", ti, "男", True, "ko-KR")
    zpos = ""
    for p in ast.palaces:
        for s in p.major_stars:
            nm = s.translate_name() if hasattr(s, "translate_name") else s.name
            if nm in ("자미", "紫微"):
                zpos = p.translate_earthly_branch()
    a.append({"time_index": ti, "lunar": str(ast.lunar_date),
              "class": str(ast.five_elements_class), "ziwei_at": zpos,
              "soul": ast.get_soul_palace().translate_name()})
# 참고: 익일(1976-01-30) 早子 로 부르면 어떻게 되는지
ast = iztro_py.by_solar("1976-01-30", 0, "男", True, "ko-KR")
zpos = ""
for p in ast.palaces:
    for s in p.major_stars:
        nm = s.translate_name() if hasattr(s, "translate_name") else s.name
        if nm in ("자미", "紫微"):
            zpos = p.translate_earthly_branch()
a.append({"time_index": "0 (익일 1976-01-30)", "lunar": str(ast.lunar_date),
          "class": str(ast.five_elements_class), "ziwei_at": zpos,
          "soul": ast.get_soul_palace().translate_name()})
out["A_late_zi_probe"] = a

# ---- (B) iztro 중국음력 vs KASI 한국음력 괴리율 ----
con = sqlite3.connect("data/kasi_cache.sqlite")
d0, d1 = date(1950, 1, 1), date(2020, 12, 31)
step = 7
n = same = diff = missing = 0
samples = []
cur = d0
while cur <= d1:
    row = con.execute(
        "select lun_year,lun_month,lun_day,leap from lunar where sol_ymd=?",
        (int(cur.strftime("%Y%m%d")),),
    ).fetchone()
    if row:
        ast = iztro_py.by_solar(cur.strftime("%Y-%m-%d"), 6, "男", True, "ko-KR")
        try:
            lm, ld, leap = han_lunar_to_nums(str(ast.lunar_date))
        except Exception:
            missing += 1
            cur += timedelta(days=step)
            continue
        n += 1
        if (lm, ld, bool(leap)) == (row[1], row[2], bool(row[3])):
            same += 1
        else:
            diff += 1
            if len(samples) < 15:
                samples.append({"solar": cur.isoformat(),
                                "iztro": [lm, ld, bool(leap)],
                                "kasi": [row[1], row[2], bool(row[3])]})
    cur += timedelta(days=step)
out["B_lunar_divergence"] = {
    "range": [d0.isoformat(), d1.isoformat()], "step_days": step,
    "compared": n, "same": same, "diff": diff, "unparsed": missing,
    "diff_rate_pct": round(diff * 100.0 / n, 3) if n else None,
    "samples": samples,
}

Path("tmp/_probe3.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
print("A cases", len(a), "| B compared", n, "same", same, "diff", diff)
