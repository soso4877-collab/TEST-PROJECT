# -*- coding: utf-8 -*-
"""신청 고민 원문에서 상대방 생년월일 감지 — 결정론 파서.

샘플 유형: "그친구는 990118 양력인데", "19990118", "99년 1월 18일", "1999.1.18".
원칙: 미감지·검증 실패 = 기능 생략(잘못된 상대 사주 출력보다 안전).
매치 스팬(start, end)은 마스킹(절대규칙 17)에 재사용한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PartnerBirthMatch:
    year: int
    month: int
    day: int
    raw: str  # 원문 표기(마스킹 치환 대상)
    start: int
    end: int


# 전화번호·긴 숫자열 오탐 방지: 숫자/하이픈에 붙어 있는 토큰은 배제
_RX_8 = re.compile(r"(?<![\d\-])((19|20)\d{2})(\d{2})(\d{2})(?![\d\-])")
_RX_6 = re.compile(r"(?<![\d\-])(\d{2})(\d{2})(\d{2})(?![\d\-])")
_RX_KO = re.compile(r"((?:19|20)?\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일?")
_RX_SEP = re.compile(
    r"(?<![\d.\-/])((?:19|20)\d{2})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})(?![\d.\-/])"
)


def _century(yy: int, ref_year: int) -> int:
    """두 자리 연도 → 세기 추론: 2000+yy가 기준연도를 넘으면 1900+yy (99→1999)."""
    y = 2000 + yy
    return y if y <= ref_year else 1900 + yy


def _valid(y: int, mo: int, d: int, ref_year: int) -> bool:
    if not (1900 <= y <= ref_year and 1 <= mo <= 12 and 1 <= d <= 31):
        return False
    try:
        date(y, mo, d)
        return True
    except ValueError:
        return False


def find_partner_births(
    concern: str | None,
    *,
    self_solar: date | None = None,
    ref_year: int | None = None,
) -> list[PartnerBirthMatch]:
    """고민 원문에서 상대방 생년월일 후보를 전부 찾는다(본인 생일 제외).

    ref_year: 두 자리 연도 세기 추론 기준(테스트 결정론 위해 주입 가능, 기본=올해).
    """
    if not concern or not concern.strip():
        return []
    ry = ref_year or date.today().year
    found: list[PartnerBirthMatch] = []
    spans: list[tuple[int, int]] = []

    def _add(y: int, mo: int, d: int, m: re.Match) -> None:
        if not _valid(y, mo, d, ry):
            return
        if self_solar and date(y, mo, d) == self_solar:
            return  # 본인 생일 재언급 오탐 방지
        s, e = m.span()
        if any(s < pe and ps < e for ps, pe in spans):
            return  # 겹침(같은 표기 이중 매치) 방지
        spans.append((s, e))
        found.append(PartnerBirthMatch(y, mo, d, concern[s:e], s, e))

    for m in _RX_8.finditer(concern):
        _add(int(m.group(1)), int(m.group(3)), int(m.group(4)), m)
    for m in _RX_SEP.finditer(concern):
        _add(int(m.group(1)), int(m.group(2)), int(m.group(3)), m)
    for m in _RX_KO.finditer(concern):
        ys = m.group(1)
        y = int(ys) if len(ys) == 4 else _century(int(ys), ry)
        _add(y, int(m.group(2)), int(m.group(3)), m)
    for m in _RX_6.finditer(concern):
        _add(_century(int(m.group(1)), ry), int(m.group(2)), int(m.group(3)), m)

    found.sort(key=lambda x: x.start)
    return found
