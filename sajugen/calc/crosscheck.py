# -*- coding: utf-8 -*-
"""3원 교차검증: lunar-python(节气) ↔ Skyfield(천문) [↔ KASI(키 시)].

분 단위 불일치 시 플래그. KASI는 키 확보 시 결합(미보유 시 2원 = lunar↔Skyfield).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from lunar_python import Solar

from . import solarterms

_KST = ZoneInfo("Asia/Seoul")
# lunar-python 절기 시각은 **고정 UTC+8**(中 동경120° 표준)로 산출됨.
# Asia/Shanghai를 쓰면 중국 서머타임(1986–91)이 잘못 적용되므로 고정 오프셋 사용.
_CHINA = timezone(timedelta(hours=8))

# Skyfield 황경(°) → lunar-python JieQi 키(중문)
_LON_TO_LUNAR = {
    315: "立春",
    345: "驚蟄",
    15: "清明",
    45: "立夏",
    75: "芒種",
    105: "小暑",
    135: "立秋",
    165: "白露",
    195: "寒露",
    225: "立冬",
    255: "大雪",
    285: "小寒",
    330: "雨水",
    0: "春分",
    30: "穀雨",
    60: "小滿",
    90: "夏至",
    120: "大暑",
    150: "處暑",
    180: "秋分",
    210: "霜降",
    240: "小雪",
    270: "冬至",
    300: "大寒",
}


def crosscheck_year(year: int, tolerance_min: float = 5.0) -> dict:
    """그 해 절기: Skyfield vs lunar-python 분 단위 차이와 불일치 플래그."""
    # 인접 연도 절기까지 모아 이름별 후보군 구성(연 경계 매칭 안전)
    cand: dict[str, list[datetime]] = {}
    for yy in (year - 1, year, year + 1):
        tbl = Solar.fromYmd(yy, 6, 1).getLunar().getJieQiTable()
        for key, s in tbl.items():
            # lunar-python 절기는 중국표준시(UTC+8) → UTC(naive)로 정규화
            d = (
                datetime(
                    s.getYear(),
                    s.getMonth(),
                    s.getDay(),
                    s.getHour(),
                    s.getMinute(),
                    s.getSecond(),
                    tzinfo=_CHINA,
                )
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )
            cand.setdefault(key, []).append(d)
    rows = []
    max_diff = 0.0
    for lon, lname in _LON_TO_LUNAR.items():
        sky_utc = solarterms.solar_term_time(year, lon)  # UTC naive
        opts = cand.get(lname) or []
        if not opts:
            rows.append({"term": lname, "status": "lunar_missing"})
            continue
        # 같은 이름 후보 중 Skyfield(UTC)에 가장 가까운 것(연 경계 자동 정합)
        lun_utc = min(opts, key=lambda d: abs((d - sky_utc).total_seconds()))
        diff = abs((sky_utc - lun_utc).total_seconds()) / 60.0
        max_diff = max(max_diff, diff)
        sky_kst = sky_utc.replace(tzinfo=timezone.utc).astimezone(_KST)
        lun_kst = lun_utc.replace(tzinfo=timezone.utc).astimezone(_KST)
        rows.append(
            {
                "term": lname,
                "skyfield_kst": sky_kst.strftime("%Y-%m-%d %H:%M:%S"),
                "lunar_kst": lun_kst.strftime("%Y-%m-%d %H:%M:%S"),
                "diff_min": round(diff, 2),
                "ok": diff <= tolerance_min,
            }
        )
    return {
        "year": year,
        "max_diff_min": round(max_diff, 2),
        "all_ok": all(r.get("ok", False) for r in rows if "diff_min" in r),
        "rows": rows,
    }
