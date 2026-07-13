# -*- coding: utf-8 -*-
"""P2 통합 엔진 — P1 보정 → 명리(흐름) + 자미두수(구조) → 교차·통합 결과 객체.

보고서 §8: 명리=흐름, 자미두수=구조. 두 체계 일치/상이/충돌을 '표면화'하되
단정하지 않는다(해석 문안은 P3에서 가드 통과 후 생성).
"""

from __future__ import annotations

from pydantic import BaseModel

from ..input import time_correction as tc
from ..input.birth_time import BirthTimeMode, normalize_birth_time_mode
from . import kasi
from . import myeongni as mod_my
from . import solarterms
from . import three_pillar as mod_three
from . import ziwei as mod_zw


class CrossCheck(BaseModel):
    bazi_consistent: bool  # 명리 사주팔자 == 자미 chinese_date
    bazi_myeongni: str
    bazi_ziwei: str
    month_branch_ok: bool  # lunar ↔ Skyfield 월지
    hour_branch_conflict: bool  # P1 자시정책 ↔ lunar-python 시지
    year_branch_ok: bool = True  # 입춘 기준 연지 lunar ↔ Skyfield (T2.4/F-2)
    near_term_boundary: bool = False  # 절입(월건/입춘) ±2분 knife-edge 출생 — 관리자 확인(T2.2)
    kasi_consistent: bool = True  # KASI 3원 교차 일치(미지 불일치=False → 차단, T2.3)
    kasi_out_of_range: bool = False  # KASI 캐시 범위 밖/부재 = 2원 폴백(차단 아님, 사실 기록)
    warnings: list[str]


class SajuResult(BaseModel):
    input_civil: str
    true_solar: str
    eot_minutes: float
    longitude: float
    zasi_policy: str
    ref_year: int | None = None  # 풀이 기준 연도(horoscope_date 연도) — '올해' 서술의 닻
    myeongni: mod_my.Myeongni
    ziwei: mod_zw.Ziwei
    crosscheck: CrossCheck

    @property
    def birth_time_mode(self) -> BirthTimeMode:
        """알려진 시각 결과도 동일한 공개 모드 인터페이스를 제공한다.

        Pydantic 저장 필드로 추가하지 않아 기존 known-time 직렬화 계약은 바꾸지 않는다.
        """

        return BirthTimeMode.KNOWN


class ThreePillarSajuResult(BaseModel):
    """생시 미상용 명시적 대체 결과.

    알려진 시각용 `.myeongni`를 제공하지 않는다. 소비자는 `birth_time_mode`를 확인한 뒤
    `.three_pillar`를 사용해야 하며, 자미두수는 계산하지 않았음을 `None`으로 명시한다.
    """

    birth_time_mode: BirthTimeMode = BirthTimeMode.THREE_PILLAR
    input_civil_date: str
    ref_year: int | None = None
    three_pillar: mod_three.ThreePillarMyeongni
    ziwei: None = None
    crosscheck: mod_three.ThreePillarCrossCheck
    provenance: mod_three.ThreePillarProvenance


def build(
    year: int,
    month: int,
    day: int,
    hour: int | None,
    minute: int | None,
    *,
    is_male: bool,
    longitude: float = tc.SEOUL_LON,
    latitude: float = tc.SEOUL_LAT,
    policy: tc.ZasiPolicy = tc.ZasiPolicy.JST_2300,
    horoscope_date: str | None = None,
    birth_time_mode: BirthTimeMode | str | None = None,
    unknown_time: bool | None = None,
) -> SajuResult | ThreePillarSajuResult:
    mode = normalize_birth_time_mode(
        birth_time_mode,
        unknown_time=unknown_time,
        hour=hour,
    )
    ref_year = None
    if horoscope_date:
        try:
            ref_year = int(str(horoscope_date)[:4])
        except Exception:
            ref_year = None

    if mode is BirthTimeMode.THREE_PILLAR:
        result = mod_three.build(
            year,
            month,
            day,
            ref_year=ref_year,
        )
        return ThreePillarSajuResult(
            input_civil_date=result.input_civil_date,
            ref_year=result.ref_year,
            three_pillar=result.three_pillar,
            ziwei=None,
            crosscheck=result.crosscheck,
            provenance=result.provenance,
        )

    if hour is None or minute is None:
        raise ValueError("birth_time_mode=known 에는 hour/minute 가 필요합니다")
    ct = tc.correct(
        year, month, day, hour, minute, longitude=longitude, latitude=latitude, policy=policy
    )
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
    if not my.year_branch_crosscheck_ok:
        warnings.append(
            f"연지 lunar({my.year_branch_lunar})↔Skyfield({my.year_branch_skyfield}) 불일치 — 입춘 경계"
        )
    if my.hour_branch_conflict:
        warnings.append(
            f"시지 P1정책({my.hour_branch_p1_policy})↔lunar({my.hour.zhi}) 불일치 — 자시 학설 차이(정책 선택 사항)"
        )

    # 절입 ±2분 knife-edge 출생 = 관리자 확인 플래그(T2.2/G-2, 절대규칙 7 후단). 월주/연주
    # 경계에 근접하면 두 엔진이 합의해도 절입 시각 미세차로 결과가 흔들릴 수 있어 재확인 대상.
    near_term = solarterms.minutes_to_nearest_jie(ct.utc) <= solarterms.NEAR_TERM_TOL_MIN
    if near_term:
        warnings.append("절입 ±2분 근접 출생 — 월주/연주 경계 관리자 확인 필요")

    # KASI 3원 교차 런타임 편입(T2.3/G-1, 절대규칙7 전단). 캐시 범위 내 미지 불일치면
    # calc_consistent=False → 주문 차단. 범위 밖/부재는 2원 폴백(차단 아님, 사실만 기록).
    kasi_consistent, kasi_oor = kasi.year_kasi_check(year)
    if not kasi_consistent:
        warnings.append("KASI 3원 교차 미지 불일치 — 절입 시각 재확인(주문 차단)")
    elif kasi_oor:
        warnings.append("KASI 절기 캐시 범위 밖(2원 검증) — kasi_out_of_range")

    return SajuResult(
        input_civil=ct.civil_local.strftime("%Y-%m-%d %H:%M"),
        true_solar=ct.true_solar.strftime("%Y-%m-%d %H:%M:%S"),
        eot_minutes=ct.eot_minutes,
        longitude=ct.longitude,
        zasi_policy=ct.policy.value,
        ref_year=ref_year,
        myeongni=my,
        ziwei=zw,
        crosscheck=CrossCheck(
            bazi_consistent=consistent,
            bazi_myeongni=bazi_my,
            bazi_ziwei=bazi_zw,
            month_branch_ok=my.month_branch_crosscheck_ok,
            year_branch_ok=my.year_branch_crosscheck_ok,
            hour_branch_conflict=my.hour_branch_conflict,
            near_term_boundary=near_term,
            kasi_consistent=kasi_consistent,
            kasi_out_of_range=kasi_oor,
            warnings=warnings,
        ),
    )
