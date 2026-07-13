# -*- coding: utf-8 -*-
"""출생시각 입력의 단일 정규화 계약.

`unknown_time`은 과거 주문과 호출자를 위한 호환 입력일 뿐이다. 내부 계산은 항상
`BirthTimeMode` 하나로 분기해, 생시 미상 입력이 정오 출생으로 조용히 변환되는 일을
막는다.
"""

from __future__ import annotations

from enum import Enum


class BirthTimeMode(str, Enum):
    """출생시각의 출처 상태."""

    KNOWN = "known"
    THREE_PILLAR = "three_pillar"


def normalize_birth_time_mode(
    mode: BirthTimeMode | str | None = None,
    *,
    unknown_time: bool | None = None,
    hour: int | None = None,
) -> BirthTimeMode:
    """신규 enum과 레거시 boolean을 하나의 모드로 정규화한다.

    명시적인 `mode`가 우선하되, 서로 모순되는 레거시 입력은 조용히 덮지 않고
    `ValueError`로 차단한다. 모드가 생략되면 기존 호출은 시각 유무로 판단한다.
    """

    normalized = BirthTimeMode(mode) if mode is not None else None

    if unknown_time is True:
        if normalized is BirthTimeMode.KNOWN:
            raise ValueError("birth_time_mode=known 과 unknown_time=True 는 함께 쓸 수 없습니다")
        return BirthTimeMode.THREE_PILLAR

    if unknown_time is False and normalized is BirthTimeMode.THREE_PILLAR:
        raise ValueError(
            "birth_time_mode=three_pillar 과 unknown_time=False 는 함께 쓸 수 없습니다"
        )

    if normalized is not None:
        return normalized
    return BirthTimeMode.THREE_PILLAR if hour is None else BirthTimeMode.KNOWN
