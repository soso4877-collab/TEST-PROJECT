# -*- coding: utf-8 -*-
"""입력 정규화 — 음력/양력 + 윤달 입력을 양력(그레고리력) 날짜로 통일.

명리·자미 계산 엔진은 모두 양력 시각 기준으로 동작한다(time_correction → engine).
따라서 입력이 음력이면 여기서 먼저 양력으로 변환해 넘긴다.

음력 변환 1차 기준 = KASI 캐시(절대규칙 3). 한·중 음력 상이일이 존재하고
lunar-python 음력은 중국 기준이므로, 한국 사용자의 음력 생일은 KASI 값이 권위.
- KASI 캐시에 있으면 KASI 채택(source='kasi').
- 캐시 부재/범위 밖이면 lunar-python(중국 기준)로 폴백하고 경고(source='lunar_python_cn').
- 입력 음력 날짜가 어느 쪽에도 없으면 ValueError(존재하지 않는 음력일).

시각(hh:mm)은 달력 무관(시민 시각)이라 변환하지 않고 그대로 둔다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from lunar_python import Lunar

from ..calc import kasi


@dataclass
class NormalizedDate:
    """정규화 결과 — 항상 양력 (year/month/day) + 출처/경고."""

    year: int
    month: int
    day: int
    source: str  # 'solar' | 'kasi' | 'lunar_python_cn'
    input_kind: str  # 'solar' | 'lunar'
    warnings: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def solar(self) -> date:
        return date(self.year, self.month, self.day)


def normalize_date(
    year: int,
    month: int,
    day: int,
    *,
    is_lunar: bool = False,
    is_leap: bool = False,
    cache: kasi.KasiCache | None = None,
) -> NormalizedDate:
    """음력/양력 입력을 양력 NormalizedDate로 변환."""
    if not is_lunar:
        return NormalizedDate(year, month, day, source="solar", input_kind="solar")

    cache = cache or kasi.KasiCache()

    # 1차: KASI 캐시(한국 공식)
    if cache.exists:
        hit = cache.solar_of_lunar(year, month, day, is_leap)
        if hit:
            nd = NormalizedDate(
                hit["year"],
                hit["month"],
                hit["day"],
                source="kasi",
                input_kind="lunar",
                note=f"음력 {year}-{'윤' if is_leap else ''}{month}-{day} → 양력(KASI 기준)",
            )
            # 한·중 차이 여부 참고 표기(중국기준과 다르면 안내, 차단 아님)
            cn = _lunar_python_solar(year, month, day, is_leap)
            ksolar = (hit["year"], hit["month"], hit["day"])
            if cn is None:
                # 중국 달력엔 이 음력 라벨 자체가 없음(예: 2012 윤3월은 중국=윤4월) → 명백한 한·중 상이
                nd.warnings.append(
                    "한·중 음력 상이일: 중국기준(lunar-python)에 해당 음력 라벨 없음 → KASI 채택"
                )
            elif cn != ksolar:
                nd.warnings.append(
                    f"한·중 음력 상이일: 중국기준(lunar-python) {cn[0]}-{cn[1]:02d}-{cn[2]:02d} "
                    f"≠ KASI {ksolar[0]}-{ksolar[1]:02d}-{ksolar[2]:02d} → KASI 채택"
                )
            return nd

    # 폴백: lunar-python(중국 기준)
    cn = _lunar_python_solar(year, month, day, is_leap)
    if cn is None:
        raise ValueError(f"존재하지 않는 음력일: {year}-{'윤' if is_leap else ''}{month}-{day}")
    rng_note = "KASI 캐시 미구축" if not cache.exists else "KASI 캐시 범위 밖/미수록"
    return NormalizedDate(
        cn[0],
        cn[1],
        cn[2],
        source="lunar_python_cn",
        input_kind="lunar",
        warnings=[f"{rng_note} → lunar-python(중국 기준) 폴백 — 한·중 상이일이면 부정확 가능"],
        note=f"음력 {year}-{'윤' if is_leap else ''}{month}-{day} → 양력(중국기준 폴백)",
    )


def _lunar_python_solar(
    year: int, month: int, day: int, is_leap: bool
) -> tuple[int, int, int] | None:
    """lunar-python(중국 기준) 음력→양력. 유효하지 않으면 None."""
    try:
        lunar = Lunar.fromYmd(year, -month if is_leap else month, day)
        s = lunar.getSolar()
        return (s.getYear(), s.getMonth(), s.getDay())
    except Exception:
        return None
