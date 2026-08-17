# -*- coding: utf-8 -*-
"""절입 경계에서 우리 엔진 내부의 축 불일치 창(window)이 얼마나 넓은지 실측.

배경
----
`myeongni.build` 는 **진태양시를 시민시각인 것처럼** lunar-python 에 넘겨 4기둥을 뽑는다
(144-147행). 그런데 절입 교차검증은 **절대 UTC** 로 한다(193-194행 월지, 201행 입춘 연지).
축이 다르므로 절입 근처에서 두 판정이 갈린다 → `month_branch_crosscheck_ok=False`.

이 갈림 폭이 곧
  (a) 포스텔러 등 '경도차만' 쓰는 서비스와 결과가 달라지는 구간
  (b) 우리 엔진이 스스로 CALC_MISMATCH 를 낼 구간
이다. 절대규칙 7 의 '절입 ±2분' 이 이 폭을 덮는지 확인한다.

콘솔은 ASCII 만 출력(cp949 크래시 방지). 상세는 JSON.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sajugen.calc import engine  # noqa: E402
from sajugen.calc import solarterms  # noqa: E402

OUT = Path(__file__).resolve().parent

# 12절(節) 황경. 월주를 바꾸는 것은 節 뿐이다.
JIE = list(solarterms.TWELVE_JIE)


def flags(y, mo, d, h, mi):
    r = engine.build(y, mo, d, h, mi, is_male=True)
    m = r.myeongni
    return {
        "month_ok": bool(m.month_branch_crosscheck_ok),
        "year_ok": bool(m.year_branch_crosscheck_ok),
        "near": bool(r.crosscheck.near_term_boundary),
        "eot": round(r.eot_minutes, 2),
    }


def window_at(term_utc_naive):
    """절입 시각 주변에서 month_ok(또는 year_ok)가 False 인 시민시각 분 구간 폭을 잰다."""
    # 절입 UTC -> KST 시민시각(엔진 입력축)
    kst = term_utc_naive + timedelta(hours=9)
    bad = []
    for off in range(-40, 41):          # 절입 전후 40분
        t = kst + timedelta(minutes=off)
        f = flags(t.year, t.month, t.day, t.hour, t.minute)
        if not (f["month_ok"] and f["year_ok"]):
            bad.append((off, f))
    if not bad:
        return {"width_min": 0, "lo": None, "hi": None, "near_covered": None, "eot": None}
    offs = [o for o, _ in bad]
    near_all = all(f["near"] for _, f in bad)
    return {
        "width_min": len(bad),
        "lo": min(offs),
        "hi": max(offs),
        "near_covered": near_all,          # 기존 ±2분 플래그가 이 구간을 전부 덮는가
        "eot": bad[0][1]["eot"],
    }


rows = []
for year in (1990, 2000, 2010):
    for lon in JIE:
        t = solarterms.solar_term_time(year, lon)
        name = solarterms.TERMS[lon]
        w = window_at(t.replace(tzinfo=None))
        rows.append({"year": year, "term": name, "lon": lon,
                     "term_utc": t.replace(tzinfo=None).isoformat(), **w})

widths = [r["width_min"] for r in rows]
covered = [r for r in rows if r["width_min"] and r["near_covered"]]
uncovered = [r for r in rows if r["width_min"] and not r["near_covered"]]

summary = {
    "samples": len(rows),
    "width_min_max": max(widths),
    "width_min_mean": round(sum(widths) / len(widths), 2),
    "width_min_min": min(widths),
    "terms_with_window": sum(1 for w in widths if w),
    "fully_covered_by_pm2min_flag": len(covered),
    "NOT_covered_by_pm2min_flag": len(uncovered),
}

(OUT / "eot-window.json").write_text(
    json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1),
    encoding="utf-8")

print(json.dumps(summary, ensure_ascii=True))
print("worst cases (width, lo..hi, eot):")
for r in sorted(rows, key=lambda x: -x["width_min"])[:8]:
    print("  %d %-8s width=%2d  %+3d..%+3d  eot=%s" % (
        r["year"], r["lon"], r["width_min"], r["lo"] or 0, r["hi"] or 0, r["eot"]))
