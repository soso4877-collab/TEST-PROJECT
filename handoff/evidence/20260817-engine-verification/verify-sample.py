# -*- coding: utf-8 -*-
"""엔진 정확도 표본 측정 — 랜덤 6 + 경계 프로브 4. 렌더/LLM 미호출(engine.build 만).

재현성: random.seed(20260816) 고정. 결과는 stdout JSON 으로만 남기고 저장/커밋 없음.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402

random.seed(20260816)

# 랜덤 6건: 1940~2015, 시지 블록 중앙 시각(23~01시 회피 — 자시정책 교란 배제)
MID_HOURS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
rand_cases = []
while len(rand_cases) < 6:
    y = random.randint(1940, 2015)
    mo = random.randint(1, 12)
    d = random.randint(1, 28)
    h = random.choice(MID_HOURS)
    mi = random.choice([5, 15, 25, 35, 45, 55])
    male = random.choice([True, False])
    rand_cases.append(("R%d" % (len(rand_cases) + 1), y, mo, d, h, mi, male))

# 경계 프로브 4건 (정확도 표본과 분리 집계)
probe_cases = [
    ("B1-입춘경계", 1994, 2, 4, 10, 0, True),
    ("B2-자시정책", 2001, 7, 15, 23, 30, False),
    ("B3-KST0830", 1957, 5, 20, 9, 0, True),
    ("B4-서머타임", 1988, 8, 15, 14, 0, False),
]

out = []
for tag, y, mo, d, h, mi, male in rand_cases + probe_cases:
    r = engine.build(y, mo, d, h, mi, is_male=male, horoscope_date="2026-06-01")
    my, zw, cc = r.myeongni, r.ziwei, r.crosscheck
    out.append(
        {
            "tag": tag,
            "input": f"{y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d} KST {'남' if male else '여'}",
            "true_solar": r.true_solar,
            "eot_min": round(r.eot_minutes, 2),
            "zasi": r.zasi_policy,
            "bazi": f"{my.year.ganzhi} {my.month.ganzhi} {my.day.ganzhi} {my.hour.ganzhi}",
            "day_master": my.day_master,
            "daewoon_count": my.daewoon_count,
            "daewoon_forward": my.daewoon_forward,
            "daewoon0": my.daewoon[0].ganzhi if my.daewoon else "",
            "daewoon0_year": my.daewoon[0].start_year if my.daewoon else 0,
            "ziwei_lunar": zw.lunar_date,
            "ziwei_chinese": zw.chinese_date,
            "ziwei_soul": zw.soul_palace,
            "ziwei_body": zw.body_palace,
            "ziwei_class": zw.five_elements_class,
            "ziwei_ziwei_palace": next(
                (
                    p.branch
                    for p in zw.palaces
                    for s in p.major_stars
                    if s.name in ("자미", "紫微")
                ),
                "",
            ),
            "soul_branch": next((p.branch for p in zw.palaces if p.is_soul), ""),
            "cross": {
                "bazi_consistent": cc.bazi_consistent,
                "month_ok": cc.month_branch_ok,
                "year_ok": cc.year_branch_ok,
                "hour_conflict": cc.hour_branch_conflict,
                "near_term": cc.near_term_boundary,
                "kasi_consistent": cc.kasi_consistent,
                "kasi_oor": cc.kasi_out_of_range,
            },
            "warnings": cc.warnings,
        }
    )

# cp949 콘솔 인코딩 이슈(QI-2026-06-24-06) 회피 — UTF-8 파일로만 산출
Path(__file__).with_name("_verify_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
)
print("OK cases=%d" % len(out))
