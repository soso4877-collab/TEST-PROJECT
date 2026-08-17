# -*- coding: utf-8 -*-
"""포스텔러 대조용 경계 케이스 생성 + **우리 엔진 답을 먼저 확정**.

순환 참조 방지(sweep100 -> sweep100c 에서 겪은 것과 같은 함정):
포스텔러 화면을 보고 나서 우리 값을 맞춰보는 순서가 되면 대조가 아니라 확인이 된다.
그래서 이 스크립트는 **브라우저를 열기 전에** 우리 답을 JSON 으로 동결한다.

경계는 추측하지 않고 **엔진에 이분 탐색**을 걸어 기둥이 실제로 바뀌는 시민시각(분)을 찾는다.
콘솔 출력은 ASCII 만(cp949 크래시 방지, QI-2026-06-24-06). 한자·한글은 파일로만 나간다.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sajugen.calc import engine  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402

OUT = Path(__file__).resolve().parent
ULLEUNG_LON, ULLEUNG_LAT = 130.9057, 37.4845  # 울릉도(국내 최동단 유인도)
NY_LON, NY_LAT = -74.006, 40.713


def pillars(y, mo, d, h, mi, *, male=True, lon=tc.SEOUL_LON, lat=tc.SEOUL_LAT,
            policy=tc.ZasiPolicy.JST_2300):
    """엔진 산출에서 대조에 쓸 값만 뽑는다."""
    r = engine.build(y, mo, d, h, mi, is_male=male, longitude=lon, latitude=lat, policy=policy)
    m = r.myeongni

    def gz(p):
        dd = p.model_dump()
        return f"{dd.get('gan', '')}{dd.get('zhi', '')}"

    return {
        "saju": " ".join(gz(p) for p in (m.year, m.month, m.day, m.hour)),
        "year": gz(m.year), "month": gz(m.month), "day": gz(m.day), "hour": gz(m.hour),
        "day_master": m.day_master,
        "daewoon_count": m.daewoon_count,
        "daewoon_forward": m.daewoon_forward,
        "singang": m.singang,
        "singang_score": m.singang_score,
        "gongmang": m.gongmang,
        "geukguk": m.geukguk,
        "yongshin_eokbu": m.yongshin_eokbu,
        "true_solar": r.true_solar,
        "eot_minutes": round(r.eot_minutes, 2),
    }


def find_flip(base_dt, key, *, lo_min=-180, hi_min=180, **kw):
    """base_dt 주변에서 `key` 기둥이 바뀌는 시민시각 경계를 분 단위 이분 탐색으로 찾는다.

    반환: (마지막으로 이전 값인 시각, 처음으로 새 값인 시각). 구간 내 변화가 없으면 None.
    """
    def val(off):
        t = base_dt + timedelta(minutes=off)
        return pillars(t.year, t.month, t.day, t.hour, t.minute, **kw)[key]

    a, b = lo_min, hi_min
    va, vb = val(a), val(b)
    if va == vb:
        return None
    while b - a > 1:
        mid = (a + b) // 2
        if val(mid) == va:
            a = mid
        else:
            b = mid
    return base_dt + timedelta(minutes=a), base_dt + timedelta(minutes=b)


cases = []


def add(cid, label, why, dt, *, male=True, lon=tc.SEOUL_LON, lat=tc.SEOUL_LAT,
        city="서울", policy=tc.ZasiPolicy.JST_2300, extra=None):
    row = {
        "id": cid,
        "label": label,
        "why": why,
        "input": {
            "date": dt.strftime("%Y/%m/%d"),
            "time": dt.strftime("%H:%M"),
            "gender": "남자" if male else "여자",
            "city": city,
            "calendar": "양력",
        },
        "ours": pillars(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                        male=male, lon=lon, lat=lat, policy=policy),
    }
    if extra:
        row["input"].update(extra)
    cases.append(row)
    return row


# ---------------------------------------------------------------- P1 자시 경계
# 포스텔러 12간지표는 자시를 23:30~01:30 으로 고지한다. 우리 엔진의 실제 일주 전환
# 시각을 이분 탐색으로 찾아 그 직전/직후를 넣는다(표와 엔진이 일치하는지 자체가 관측 대상).
flip = find_flip(datetime(2000, 6, 15, 23, 30), "day", lo_min=-90, hi_min=90)
if flip:
    before, after = flip
    add("A1", "자시 경계 직전", "일주 전환 직전 1분 — 조자시설이면 여기서 아직 당일", before)
    add("A2", "자시 경계 직후", "일주 전환 직후 1분 — 조자시설이면 여기서 익일로 전환", after)

# ---------------------------------------------------------------- P2 절입(월주)
flip = find_flip(datetime(2000, 6, 5, 12, 0), "month", lo_min=-2880, hi_min=2880)
if flip:
    before, after = flip
    add("B1", "절입(망종) 직전", "월주 전환 직전 1분 — 절기 시각 정밀도 대조", before)
    add("B2", "절입(망종) 직후", "월주 전환 직후 1분", after)

# ---------------------------------------------------------------- P3 입춘(연주)
flip = find_flip(datetime(2000, 2, 4, 12, 0), "year", lo_min=-2880, hi_min=2880)
if flip:
    before, after = flip
    add("C1", "입춘 연경계 직전", "연주 전환 직전 1분 — 연 기준이 입춘인지 대조", before)
    add("C2", "입춘 연경계 직후", "연주 전환 직후 1분", after)

# ---------------------------------------------------------------- P4 대운 방향
# 양남음녀 순행 / 음남양녀 역행. 같은 날 성별만 바꿔 방향과 대운수를 본다.
add("D1", "대운 방향 양년 남", "양년(庚辰) 남 = 순행 기대", datetime(2000, 9, 9, 10, 20), male=True)
add("D2", "대운 방향 양년 여", "양년 여 = 역행 기대(같은 생일, 성별만 다름)",
    datetime(2000, 9, 9, 10, 20), male=False)

# ---------------------------------------------------------------- P5 국내 경도
# 같은 시민시각에 서울/울릉도. 경도차 약 3.9도 = 약 15.7분 → 시지가 갈리는 구간을 고른다.
seoul_flip = find_flip(datetime(2000, 3, 10, 9, 30), "hour", lo_min=-60, hi_min=60)
if seoul_flip:
    _, just_after = seoul_flip
    edge = just_after - timedelta(minutes=8)  # 서울은 이전 시지, 울릉도는 다음 시지가 되는 지점
    add("E1", "국내 경도 서울", "서울 좌표 기준 시지", edge, city="서울")
    add("E2", "국내 경도 울릉도", "동일 시민시각·울릉도 좌표 — 시지가 갈리는지",
        edge, city="울릉도", lon=ULLEUNG_LON, lat=ULLEUNG_LAT)

# ---------------------------------------------------------------- P6 해외
# 현행 엔진은 tz 하드코딩이라 이 값이 틀린다(패킷 2-1). '우리(현행)' 값으로 기록해 둔다.
add("F1", "해외 뉴욕", "패킷 2-3 대조 케이스 — 현행 엔진은 11시간 오차가 나는 자리",
    datetime(1990, 5, 20, 14, 30), city="뉴욕", lon=NY_LON, lat=NY_LAT)

# ---------------------------------------------------------------- 저장
payload = {
    "generated_for": "postteller-chart-survey",
    "engine_head": "444420d",
    "note": "우리 엔진 답은 브라우저 조회 전에 동결했다(순환 참조 방지).",
    "zasi_policy": "JST_2300",
    "cases": cases,
}
(OUT / "cases.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

print("cases=%d" % len(cases))
for c in cases:
    print("  %-3s %s %s %-6s -> %s" % (
        c["id"], c["input"]["date"], c["input"]["time"],
        "M" if c["input"]["gender"] == "남자" else "F",
        c["ours"]["saju"].encode("ascii", "backslashreplace").decode()))
