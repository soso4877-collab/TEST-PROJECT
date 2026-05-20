# -*- coding: utf-8 -*-
"""P2 통합 엔진 — P1 보정 → 명리(흐름) + 자미두수(구조) → 교차·통합 결과 객체.

보고서 §8: 명리=흐름, 자미두수=구조. 두 체계 일치/상이/충돌을 '표면화'하되
단정하지 않는다(해석 문안은 P3에서 가드 통과 후 생성).
"""

from __future__ import annotations

from pydantic import BaseModel

from ..input import time_correction as tc
from . import myeongni as mod_my
from . import ziwei as mod_zw


class CrossCheck(BaseModel):
    bazi_consistent: bool  # 명리 사주팔자 == 자미 chinese_date
    bazi_myeongni: str
    bazi_ziwei: str
    month_branch_ok: bool  # lunar ↔ Skyfield 월지
    hour_branch_conflict: bool  # P1 자시정책 ↔ lunar-python 시지
    warnings: list[str]


class SajuResult(BaseModel):
    input_civil: str
    true_solar: str
    eot_minutes: float
    longitude: float
    zasi_policy: str
    myeongni: mod_my.Myeongni
    ziwei: mod_zw.Ziwei
    crosscheck: CrossCheck


def build(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    *,
    is_male: bool,
    longitude: float = tc.SEOUL_LON,
    latitude: float = tc.SEOUL_LAT,
    policy: tc.ZasiPolicy = tc.ZasiPolicy.JST_2300,
    horoscope_date: str | None = None,
) -> SajuResult:
    ct = tc.correct(
        year, month, day, hour, minute, longitude=longitude, latitude=latitude, policy=policy
    )
    ref_year = None
    if horoscope_date:
        try:
            ref_year = int(str(horoscope_date)[:4])
        except Exception:
            ref_year = None
    my = mod_my.build(ct, is_male=is_male, ref_year=ref_year)
    zw = mod_zw.build(ct, is_male=is_male, horoscope_date=horoscope_date)

    bazi_my = f"{my.year.ganzhi} {my.month.ganzhi} {my.day.ganzhi} {my.hour.ganzhi}"
    bazi_zw = zw.chinese_date.strip()
    consistent = bazi_my == bazi_zw

    warnings: list[str] = []
    if not consistent:
        warnings.append(
            f"명리({bazi_my}) ↔ 자미({bazi_zw}) 사주팔자 불일치 — 입력/시지 정책 재확인"
        )
    if not my.month_branch_crosscheck_ok:
        warnings.append(
            f"월지 lunar({my.month_branch_lunar})↔Skyfield({my.month_branch_skyfield}) 불일치"
        )
    if my.hour_branch_conflict:
        warnings.append(
            f"시지 P1정책({my.hour_branch_p1_policy})↔lunar({my.hour.zhi}) 불일치 — 자시 학설 차이(정책 선택 사항)"
        )

    return SajuResult(
        input_civil=ct.civil_local.strftime("%Y-%m-%d %H:%M"),
        true_solar=ct.true_solar.strftime("%Y-%m-%d %H:%M:%S"),
        eot_minutes=ct.eot_minutes,
        longitude=ct.longitude,
        zasi_policy=ct.policy.value,
        myeongni=my,
        ziwei=zw,
        crosscheck=CrossCheck(
            bazi_consistent=consistent,
            bazi_myeongni=bazi_my,
            bazi_ziwei=bazi_zw,
            month_branch_ok=my.month_branch_crosscheck_ok,
            hour_branch_conflict=my.hour_branch_conflict,
            warnings=warnings,
        ),
    )
