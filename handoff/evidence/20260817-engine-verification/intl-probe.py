# -*- coding: utf-8 -*-
"""해외 출생지 지원 여부 실측.

time_correction.correct() 는 longitude/latitude 는 인자로 받지만
시간대는 _KST = ZoneInfo("Asia/Seoul") 로 고정돼 있다(21행, 90행).
-> 해외 출생 시각을 그대로 넣으면 '한국 시간'으로 해석된다.
얼마나 어긋나는지, 그리고 올바른 값은 무엇인지 비교한다.
"""
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402

CASES = [
    ("서울",       "Asia/Seoul",        126.9780,  37.5665),
    ("뉴욕",       "America/New_York",  -74.0060,  40.7128),
    ("런던",       "Europe/London",       -0.1276, 51.5074),
    ("LA",         "America/Los_Angeles", -118.2437, 34.0522),
    ("시드니",     "Australia/Sydney",   151.2093, -33.8688),
    ("도쿄",       "Asia/Tokyo",         139.6917,  35.6895),
]

Y, MO, D, H, MI = 1990, 5, 20, 14, 30

out = []
for name, tzname, lon, lat in CASES:
    # (1) 엔진 현행 동작 — 시각을 KST 로 해석
    r = engine.build(Y, MO, D, H, MI, is_male=True, longitude=lon, latitude=lat,
                     horoscope_date="2026-06-01")
    eng_ts = r.true_solar
    eng_bazi = (f"{r.myeongni.year.ganzhi} {r.myeongni.month.ganzhi} "
                f"{r.myeongni.day.ganzhi} {r.myeongni.hour.ganzhi}")

    # (2) 올바른 동작 — 그 도시의 실제 시간대로 해석했을 때의 진태양시
    local = datetime(Y, MO, D, H, MI, tzinfo=ZoneInfo(tzname))
    utc_true = local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    correct_ts = tc._apparent_solar_dt(utc_true, lon, lat,
                                       datetime(Y, MO, D, H, MI))

    # 엔진이 실제로 쓴 UTC
    utc_used = datetime(Y, MO, D, H, MI, tzinfo=ZoneInfo("Asia/Seoul")).astimezone(
        ZoneInfo("UTC")).replace(tzinfo=None)

    ts_dt = datetime.strptime(eng_ts, "%Y-%m-%d %H:%M:%S")
    gap_h = (correct_ts - ts_dt).total_seconds() / 3600.0
    out.append({
        "도시": name,
        "현지 출생시각": f"{Y}-{MO:02d}-{D:02d} {H:02d}:{MI:02d} ({tzname})",
        "엔진이 쓴 UTC": utc_used.strftime("%Y-%m-%d %H:%M"),
        "올바른 UTC": utc_true.strftime("%Y-%m-%d %H:%M"),
        "UTC 오차(시간)": round((utc_true - utc_used).total_seconds() / 3600.0, 1),
        "엔진 진태양시": eng_ts,
        "올바른 진태양시": correct_ts.strftime("%Y-%m-%d %H:%M:%S"),
        "진태양시 오차(시간)": round(gap_h, 2),
        "엔진 산출 사주": eng_bazi,
        "엔진 시지": r.myeongni.hour.zhi,
    })

Path("tmp/_intl_probe.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("ok", len(out))
