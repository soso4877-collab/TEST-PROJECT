# -*- coding: utf-8 -*-
"""KASI 캐시 전수 감사 — 음양력 55,152일 + 절기 672행 무결성 검증.

"오류가 있어서는 안 된다"는 요구에 맞춘 최강 검증: 표본이 아닌 전 데이터에 대해
(1) 수학적 불변식(외부 의존 0) + (2) 독립 엔진(lunar-python) 전수 대조.

검증 항목:
  A. 율리우스적일(solJd) 연속성 — 인접일 차이 정확히 +1 (날짜 누락/중복/오기 탐지)
  B. 일진 60갑자 연속성 — 매일 간지가 60주기에서 +1 (내부 불변식)
  C. KASI 일진 ↔ lunar-python 일진 전수 일치 — 干支는 달력 무관 연속값 → 100% 일치 필수
  D. KASI 음력(년/월/일/윤달) ↔ lunar-python 전수 대조 — 차이=한·중 상이일(KASI 채택, 예상)
     ※ lunar-python은 중국 기준(절대규칙 3). 차이는 오류가 아니라 한·중 달력 차이이며 KASI가 권위.
       대표 검증: 2012년 KASI=윤3월(한국)·lunar-python=윤4월(중국), 일진은 동일 → 날짜무결성 보존.
       하드오류 집계에서 제외하고 한·중 상이일 카탈로그(data/kasi_kr_cn_divergence.json)로 기록.
  E. 절기: KASI ↔ Skyfield ↔ lunar-python 3원(2000~2027) — 기지 KASI 결함만 허용

실행: ./.venv/Scripts/python.exe -m scripts.verify_kasi_cache
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lunar_python import Solar  # noqa: E402

from sajugen.calc import kasi  # noqa: E402

# 60갑자 — 천간/지지
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"
_JIAZI = [_GAN[i % 10] + _ZHI[i % 12] for i in range(60)]
_JIAZI_IDX = {g: i for i, g in enumerate(_JIAZI)}


def _hanja(kasi_ganzhi: str) -> str:
    """'병인(丙寅)' → '丙寅'."""
    s = kasi_ganzhi
    if "(" in s and ")" in s:
        return s[s.index("(") + 1 : s.index(")")]
    return s.strip()


def main() -> int:
    cache_path = kasi.DEFAULT_CACHE
    if not cache_path.exists():
        print("캐시 없음 — scripts.kasi_dump 먼저 실행")
        return 1
    conn = sqlite3.connect(f"file:{cache_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT sol_ymd, lun_year, lun_month, lun_day, leap, secha, iljin, sol_jd "
        "FROM lunar ORDER BY sol_ymd"
    ).fetchall()
    n = len(rows)
    print(f"[대상] 음양력 {n}일 ({rows[0]['sol_ymd']}~{rows[-1]['sol_ymd']})")

    errA = []  # solJd 연속성
    errB = []  # 일진 60갑자 연속성
    errC = []  # KASI 일진 vs lunar-python
    divD = []  # 음력 라벨 한·중 상이일(오류 아님 — KASI 채택, Phase 2 카탈로그)

    prev = None
    for r in rows:
        ymd = r["sol_ymd"]
        y, m, d = ymd // 10000, (ymd // 100) % 100, ymd % 100
        ilj = _hanja(r["iljin"])

        # A. solJd 연속성
        if prev is not None:
            # 실제 달력상 인접일인지(월말→다음달 1일 포함) date 차이로 판정
            gap = (date(y, m, d) - prev["date"]).days
            if gap == 1 and r["sol_jd"] - prev["jd"] != 1:
                errA.append((ymd, "solJd 비연속", prev["jd"], r["sol_jd"]))
            # B. 일진 60갑자 연속성(인접일 한정)
            if gap == 1 and ilj in _JIAZI_IDX and prev["ilj_idx"] is not None:
                if (prev["ilj_idx"] + 1) % 60 != _JIAZI_IDX[ilj]:
                    errB.append((ymd, prev["ilj"], ilj))

        # C. KASI 일진 ↔ lunar-python 일진
        lunar = Solar.fromYmd(y, m, d).getLunar()
        lp_ilj = lunar.getDayInGanZhi()
        if ilj != lp_ilj:
            errC.append((ymd, ilj, lp_ilj))

        # D. 음력 년/월/일/윤달 대조 — KASI(한국)≠lunar-python(중국)은 한·중 상이(오류 아님)
        lp_month_raw = lunar.getMonth()  # 음수=윤달
        lp_leap = 1 if lp_month_raw < 0 else 0
        lp_month = abs(lp_month_raw)
        lp_day = lunar.getDay()
        lp_year = lunar.getYear()
        if (r["lun_year"], r["lun_month"], r["lun_day"], r["leap"]) != (
            lp_year,
            lp_month,
            lp_day,
            lp_leap,
        ):
            divD.append(
                {
                    "sol": ymd,
                    "kasi": f"{r['lun_year']}-{'윤' if r['leap'] else ''}{r['lun_month']}-{r['lun_day']}",
                    "lunar_python_cn": f"{lp_year}-{'윤' if lp_leap else ''}{lp_month}-{lp_day}",
                }
            )

        prev = {
            "date": date(y, m, d),
            "jd": r["sol_jd"],
            "ilj": ilj,
            "ilj_idx": _JIAZI_IDX.get(ilj),
        }

    def show(name, errs, limit=10):
        status = "OK (0건)" if not errs else f"실패 {len(errs)}건"
        print(f"\n[{name}] {status}")
        for e in errs[:limit]:
            print("   ", e)
        if len(errs) > limit:
            print(f"    ... 외 {len(errs) - limit}건")

    print("\n" + "=" * 60)
    show("A. 율리우스적일(solJd) 연속성", errA)
    show("B. 일진 60갑자 연속성", errB)
    show("C. KASI 일진 ↔ lunar-python (100% 일치 필수)", errC)

    # D. 한·중 상이일 카탈로그(오류 아님). 연도별 집계 + 파일 기록.
    import json

    by_year: dict[int, int] = {}
    for x in divD:
        yy = x["sol"] // 10000
        by_year[yy] = by_year.get(yy, 0) + 1
    print(
        f"\n[D. KASI(한국) ↔ lunar-python(중국) 음력 라벨 상이] {len(divD)}일 / {len(by_year)}개년"
    )
    print(
        "    => 오류 아님. 절대규칙 3 한·중 상이(KASI 권위). 대표: 2012 KASI 윤3월 vs 중국 윤4월."
    )
    for e in divD[:6]:
        print("   ", e)
    print("    영향 연도:", sorted(by_year))
    catalog = Path(__file__).resolve().parents[1] / "data" / "kasi_kr_cn_divergence.json"
    catalog.write_text(
        json.dumps(
            {
                "_note": "KASI(한국 공식) vs lunar-python(중국 기준) 음력 라벨 상이일. KASI 채택(절대규칙3). 오류 아님.",
                "total_days": len(divD),
                "years": sorted(by_year),
                "days": divD,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"    카탈로그 기록: {catalog} ({len(divD)}일)")

    # E. 절기 3원
    print("\n" + "=" * 60)
    rcache = kasi.KasiCache()
    eng_fail = []
    kasi_unknown = []
    known = 0
    for yy in range(2000, 2028):
        res = kasi.crosscheck3_year(yy, cache=rcache)
        if not res["all_ok"]:
            eng_fail.append((yy, res["max_diff_min"]))
        if res.get("kasi_unknown_mismatches"):
            kasi_unknown.append((yy, res["kasi_unknown_mismatches"]))
        known += len(res.get("kasi_known_defects", []))
    print("[E. 절기 3원 2000~2027]")
    print(f"    2원(계산엔진) 불일치: {eng_fail if eng_fail else '없음'}")
    print(f"    KASI 미지 불일치: {kasi_unknown if kasi_unknown else '없음'}")
    print(f"    KASI 기지결함(문서화): {known}건")

    # 종합 판정 — 하드오류는 A·B·C(날짜 무결성) + E(계산엔진/미지 KASI)만. D는 한·중 상이(예상).
    hard_errors = len(errA) + len(errB) + len(errC) + len(eng_fail) + len(kasi_unknown)
    print("\n" + "=" * 60)
    print(f"[종합] 하드오류(절대 0이어야 함): {hard_errors}건")
    print(f"       한·중 음력 상이일(예상·카탈로그, 오류 아님): {len(divD)}건")
    print("       => " + ("무결성 검증 통과" if hard_errors == 0 else "오류 발견 — 수정 필요"))
    conn.close()
    return 0 if hard_errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
