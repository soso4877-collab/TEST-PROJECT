# -*- coding: utf-8 -*-
"""국내 출생지 경도를 서울 기본값으로 두면 시주/일주가 바뀌는 비율.

웹폼(app.py:59)·CLI 기본값이 서울(126.978)이라, 운영자가 출생지를 따로 넣지 않으면
전원이 서울 출생으로 계산된다. 실제 출생지 경도를 넣었을 때와 비교한다.
비교 대상: 시지(時支)와 자시 일주전환(day_offset) — 사주 4기둥 중 시주·일주에 직결.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.input import time_correction as tc  # noqa: E402

CITIES = [
    ("인천", 126.7052, 37.4563),
    ("광주", 126.8526, 35.1595),
    ("제주", 126.5312, 33.4996),
    ("대구", 128.6014, 35.8714),
    ("강릉", 128.8761, 37.7519),
    ("부산", 129.0756, 35.1796),
    ("울릉도", 130.9057, 37.4845),
]

random.seed(20260817)
N = 500
times = [(random.randint(1950, 2015), random.randint(1, 12), random.randint(1, 28),
          random.randint(0, 23), random.randint(0, 59)) for _ in range(N)]

rows = []
for name, lon, lat in CITIES:
    hour_flip = day_flip = 0
    for (y, mo, d, h, mi) in times:
        a = tc.correct(y, mo, d, h, mi)  # 서울 기본값
        b = tc.correct(y, mo, d, h, mi, longitude=lon, latitude=lat)
        if a.hour_branch != b.hour_branch:
            hour_flip += 1
        if a.day_offset != b.day_offset:
            day_flip += 1
    delta_min = round((lon - tc.SEOUL_LON) * 4.0, 1)
    rows.append({
        "도시": name,
        "경도": lon,
        "서울대비 보정차(분)": delta_min,
        "시지 바뀜": f"{hour_flip}/{N}",
        "시지 바뀜(%)": round(hour_flip * 100.0 / N, 1),
        "일주 바뀜": f"{day_flip}/{N}",
        "일주 바뀜(%)": round(day_flip * 100.0 / N, 1),
    })

Path("tmp/_domestic_lon.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok")
