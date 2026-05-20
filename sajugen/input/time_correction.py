# -*- coding: utf-8 -*-
"""P1 보정 레이어: 시민시각 → UTC(한국 표준시 역사·DST) → 진태양시 → 시지/일주경계.

- 한국 표준시 역사(1908 UTC+8:30 / 1912 +9 / 1954 +8:30 / 1961 +9)와 서머타임
  (1948–51, 1955–60, 1987–88)은 IANA tz DB `Asia/Seoul`(zoneinfo)이 권위 있게 인코딩하므로
  손코딩하지 않고 zoneinfo로 시민시각→UTC 변환(검증 가능·유지보수됨).
- 진태양시(眞太陽時)는 출생지 경도에서의 '태양 시각각(hour angle)'을 Skyfield로 직접 계산
  → 균시차(EoT)+경도차가 자동 반영됨(별도 근사식 불필요).
- 단정 금지(메모리 feedback-verify-no-overclaim): 자시/야자시는 정책을 '선택'으로 노출.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from skyfield.api import Loader, wgs84

_KST = ZoneInfo("Asia/Seoul")
_EPHEM_DIR = r"C:\Users\pc\test-project\sajugen\assets\ephemeris"
_loader = Loader(_EPHEM_DIR)
_eph = _loader("de440s.bsp")
_ts = _loader.timescale()
_earth, _sun = _eph["earth"], _eph["sun"]

SEOUL_LON = 126.9780
SEOUL_LAT = 37.5665

_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"  # 자축인묘진사오미신유술해


class ZasiPolicy(enum.Enum):
    """일주(日柱) 전환·자시 처리 정책. 학설이 갈리므로 단정하지 않고 선택."""

    JST_2300 = "zasi_2300"  # 23:00(진태양시)부터 子시이며 일주도 다음날로 전환(조자시설)
    YAJASI_SPLIT = (
        "yajasi"  # 23:00~24:00=야자시(일주는 当日, 시지 子) / 00:00~01:00=조자시(다음날, 子)
    )


@dataclass(frozen=True)
class CorrectedTime:
    civil_local: datetime  # 입력(시민 시각, naive 가정 → Asia/Seoul 부여)
    utc: datetime  # zoneinfo 변환(표준시 역사·DST 자동 반영)
    true_solar: datetime  # 진태양시(출생지 경도 기준 태양 시각각)
    eot_minutes: float  # 균시차+경도차 합산 보정량(분, 시민시각 대비)
    hour_branch: str  # 시지(時支)
    day_offset: int  # 일주 기준 날짜 보정(0=당일, +1=다음날)
    policy: ZasiPolicy
    longitude: float


def _apparent_solar_dt(utc_dt: datetime, lon: float, lat: float) -> datetime:
    """출생지에서의 진태양시(태양 hour angle + 12h)를 datetime으로 환원."""
    t = _ts.from_datetime(utc_dt.replace(tzinfo=ZoneInfo("UTC")))
    observer = _earth + wgs84.latlon(lat, lon)
    ha, dec, _ = observer.at(t).observe(_sun).apparent().hadec()
    # 진태양시(시) = 태양 시각각 + 12 (mod 24)
    ast_hours = (ha.hours + 12.0) % 24.0
    # UTC 날짜를 기준으로 진태양시 시:분:초를 입힌 datetime 구성
    base = utc_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(hours=ast_hours)


def correct(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    *,
    longitude: float = SEOUL_LON,
    latitude: float = SEOUL_LAT,
    policy: ZasiPolicy = ZasiPolicy.JST_2300,
) -> CorrectedTime:
    civil = datetime(year, month, day, hour, minute, tzinfo=_KST)
    utc = civil.astimezone(ZoneInfo("UTC"))

    true_solar = _apparent_solar_dt(utc.replace(tzinfo=None), longitude, latitude)
    # 시민시각 대비 총 보정량(분): 진태양시 - 시민시각(동일 '벽시계' 비교 위해 KST 분해)
    civil_naive = civil.replace(tzinfo=None)
    eot_minutes = round((true_solar - civil_naive).total_seconds() / 60.0, 2)

    h = true_solar.hour + true_solar.minute / 60.0
    # 시지: 23:00~01:00=子, 01~03=丑, ... (2시간 단위, 子 중심 23시 시작)
    idx = int(((h + 1) % 24) // 2)  # 23→0(子),1→1(丑)...
    hour_branch = _BRANCHES[idx]

    day_offset = 0
    if policy is ZasiPolicy.JST_2300:
        if true_solar.hour >= 23:
            day_offset = 1  # 23시 이후 子시 → 일주 다음날
    elif policy is ZasiPolicy.YAJASI_SPLIT:
        if 0 <= true_solar.hour < 1:
            day_offset = 1  # 조자시(00~01)만 다음날, 야자시(23~24)는 당일

    return CorrectedTime(
        civil_local=civil_naive,
        utc=utc.replace(tzinfo=None),
        true_solar=true_solar,
        eot_minutes=eot_minutes,
        hour_branch=hour_branch,
        day_offset=day_offset,
        policy=policy,
        longitude=longitude,
    )
