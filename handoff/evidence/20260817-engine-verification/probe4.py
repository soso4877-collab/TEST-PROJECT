# -*- coding: utf-8 -*-
"""한·중 음력 괴리의 '명반 영향' 심각도 분리 측정.

3.81% 는 iztro 라벨 != KASI 라벨 비율일 뿐, 자미 명반이 바뀌는 비율이 아니다.
명반 의존성:
  命宮/身宮 = f(음력월, 시지)   -> 월이 다르면 이동, 일만 다르면 불변
  五行局    = f(命宮 간지)       -> 命宮 따라감
  紫微      = f(局數, 음력일)    -> 일이 다르면 이동 가능
따라서 (1) 월/윤달이 갈리는 날 = 명반 전체 이동(심각), (2) 일만 갈리는 날 = 紫微만 이동 가능.
1950~2020 **전일(daily) 전수**로 다시 센다.
"""
import json
import sqlite3
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import iztro_py  # noqa: E402

from _ziwei_oracle import han_lunar_to_nums, ziwei_pos  # noqa: E402

con = sqlite3.connect("data/kasi_cache.sqlite")
d0, d1 = date(1950, 1, 1), date(2020, 12, 31)

n = same = 0
month_diff = 0          # 월 또는 윤달 플래그가 갈림 -> 命宮부터 전부 이동
day_only_diff = 0       # 월 동일, 일만 갈림
ziwei_moved = Counter()  # 局數별, 일만 갈릴 때 紫微가 실제로 이동한 날 수
day_only_total = 0
runs = []               # 연속 구간(월 단위 shift 인지 확인용)
prev_diff_day = None
cur_run = None

cur = d0
while cur <= d1:
    row = con.execute(
        "select lun_month,lun_day,leap from lunar where sol_ymd=?",
        (int(cur.strftime("%Y%m%d")),),
    ).fetchone()
    if row:
        ast = iztro_py.by_solar(cur.strftime("%Y-%m-%d"), 6, "男", True, "ko-KR")
        try:
            lm, ld, leap = han_lunar_to_nums(str(ast.lunar_date))
        except Exception:
            cur += timedelta(days=1)
            continue
        n += 1
        km, kd, kleap = row[0], row[1], bool(row[2])
        if (lm, ld, bool(leap)) == (km, kd, kleap):
            same += 1
            if cur_run:
                runs.append(cur_run)
                cur_run = None
        else:
            if cur_run is None:
                cur_run = [cur.isoformat(), cur.isoformat(), 0]
            cur_run[1] = cur.isoformat()
            cur_run[2] += 1
            if (lm, bool(leap)) != (km, kleap):
                month_diff += 1
            else:
                day_only_diff += 1
                day_only_total += 1
                for ju in (2, 3, 4, 5, 6):
                    if ziwei_pos(ju, ld) != ziwei_pos(ju, kd):
                        ziwei_moved[ju] += 1
    cur += timedelta(days=1)
if cur_run:
    runs.append(cur_run)

diff = month_diff + day_only_diff
out = {
    "range": [d0.isoformat(), d1.isoformat()],
    "compared_days": n,
    "same": same,
    "diff": diff,
    "diff_rate_pct": round(diff * 100.0 / n, 3),
    "A_month_or_leap_diff": month_diff,
    "A_rate_pct": round(month_diff * 100.0 / n, 3),
    "B_day_only_diff": day_only_diff,
    "B_rate_pct": round(day_only_diff * 100.0 / n, 3),
    "B_ziwei_moved_by_ju": {str(k): ziwei_moved[k] for k in (2, 3, 4, 5, 6)},
    "B_ziwei_moved_rate_pct_by_ju": {
        str(k): (round(ziwei_moved[k] * 100.0 / day_only_total, 1) if day_only_total else None)
        for k in (2, 3, 4, 5, 6)
    },
    "runs_count": len(runs),
    "runs_longest": sorted(runs, key=lambda r: -r[2])[:5],
    "runs_len_hist": dict(Counter(r[2] for r in runs).most_common(10)),
}
Path("tmp/_probe4.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
print(json.dumps({k: v for k, v in out.items()
                  if k not in ("runs_longest", "runs_len_hist")}, ensure_ascii=True))
