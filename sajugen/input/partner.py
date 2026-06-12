# -*- coding: utf-8 -*-
"""신청 고민 원문에서 상대방(가족 포함) 생년월일 감지 — 결정론 파서.

지원(2026-06-12 확장 — 다인 가족 케이스):
- 다중 인물: 모든 매치 반환(빌더가 전원 명식 주입).
- 음력 라벨: 날짜 앞 '음력' → is_lunar (변환은 calc 측에서 KASI 1차).
- 한글 시각: 날짜 뒤 '오후 4시 10분'/'오전 9시'/'16:10' → hour/minute.
- 관계·이름 라벨: 날짜 주변 '장남/막내/아들/딸/남편/아내…' + 2~4자 이름.
원칙: 미감지·검증 실패 = 해당 인물 생략(잘못된 명식 출력보다 안전).
매치 스팬(start, end)은 마스킹(절대규칙 17)에 재사용한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class PartnerBirthMatch:
    year: int
    month: int
    day: int
    raw: str  # 원문 표기(마스킹 치환 대상)
    start: int
    end: int
    hour: int | None = None
    minute: int = 0
    is_lunar: bool = False
    relation: str = ""  # 장남/막내/남편 등(없으면 빈 문자열)
    name: str = ""  # 감지된 이름(없으면 빈 문자열)
    time_span: tuple[int, int] | None = field(default=None, compare=False)  # 시각 마스킹용


# 전화번호·긴 숫자열 오탐 방지: 숫자/하이픈에 붙어 있는 토큰은 배제
_RX_8 = re.compile(r"(?<![\d\-])((19|20)\d{2})(\d{2})(\d{2})(?![\d\-])")
_RX_6 = re.compile(r"(?<![\d\-])(\d{2})(\d{2})(\d{2})(?![\d\-])")
_RX_KO = re.compile(r"((?:19|20)?\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일?")
_RX_SEP = re.compile(
    r"(?<![\d.\-/])((?:19|20)\d{2})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})(?![\d.\-/])"
)
# 날짜 뒤 시각: '오후 4시 10분' / '오전 9시' / '16:10'
_RX_TIME = re.compile(r"(오전|오후)?\s*(\d{1,2})\s*(?:시\s*(\d{1,2})?\s*분?|:(\d{2}))")
_RELATIONS = (
    "장남",
    "차남",
    "막내",
    "첫째",
    "둘째",
    "셋째",
    "아들",
    "딸",
    "남편",
    "아내",
    "와이프",
    "신랑",
    "어머니",
    "아버지",
    "엄마",
    "아빠",
    "남자친구",
    "여자친구",
    "남친",
    "여친",
    "그친구",
    "그 친구",
)
# 이름 후보에서 제외할 일반어(라벨 주변 빈출)
_NAME_STOP = set(
    "양력 음력 출생 출생지 서울 질문 시간 오전 오후 아들 남편 장남 막내 첫째 둘째 "
    "셋째 그리고 궁금 합니다 입니다 생일 생년 월일".split()
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


def _scan_time(text: str, end: int) -> tuple[int | None, int, tuple[int, int] | None]:
    """날짜 매치 뒤 ~20자에서 시각 감지 → (hour, minute, span)."""
    win = text[end : end + 20]
    m = _RX_TIME.search(win)
    if not m:
        return None, 0, None
    ampm, h_s, mi_s, mi_colon = m.groups()
    h = int(h_s)
    mi = int(mi_s or mi_colon or 0)
    if not ampm and ":" not in m.group(0) and "시" not in m.group(0):
        return None, 0, None
    if h > 23 or mi > 59:
        return None, 0, None
    if ampm == "오후" and h < 12:
        h += 12
    if ampm == "오전" and h == 12:
        h = 0
    return h, mi, (end + m.start(), end + m.end())


def _scan_context(text: str, start: int) -> tuple[bool, str, str]:
    """날짜 앞 같은 줄 ~30자에서 음력 여부·관계·이름 감지."""
    line_start = text.rfind("\n", 0, start) + 1
    win = text[max(line_start, start - 30) : start]
    is_lunar = "음력" in win
    relation = ""
    for r in _RELATIONS:
        if r in win:
            relation = r if r != "그 친구" else "그친구"
            # 더 구체적인 관계(장남/막내)가 일반어(아들)보다 우선
    for r in ("장남", "차남", "막내", "첫째", "둘째", "셋째", "남편", "아내"):
        if r in win:
            relation = r
            break
    name = ""
    for tok in re.findall(r"[가-힣]{2,4}", win):
        if tok in _NAME_STOP or tok in _RELATIONS or tok in ("음력", "양력"):
            continue
        if any(r in tok for r in _RELATIONS):
            continue
        name = tok  # 마지막(날짜에 가장 가까운) 후보 채택
    # 이름이 날짜 '뒤'에 오는 형식("1995년 3월 28일 오후 4시 10분 김태성")도 지원
    return is_lunar, relation, name


def _scan_name_after(text: str, end: int) -> str:
    win = text[end : end + 24]
    m = re.search(r"(?:분|시|일)?\s*([가-힣]{2,4})", win)
    if m:
        tok = m.group(1)
        if (
            tok not in _NAME_STOP
            and tok not in _RELATIONS
            and not any(r in tok for r in _RELATIONS)
        ):
            if tok not in ("오전", "오후", "음력", "양력", "출생", "태어남"):
                return tok
    return ""


def find_partner_births(
    concern: str | None,
    *,
    self_solar: date | None = None,
    ref_year: int | None = None,
) -> list[PartnerBirthMatch]:
    """고민 원문에서 상대방 생년월일 후보를 전부 찾는다(본인 생일 제외)."""
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
        hour, minute, tspan = _scan_time(concern, e)
        is_lunar, relation, name_before = _scan_context(concern, s)
        name = name_before or _scan_name_after(concern, tspan[1] if tspan else e)
        found.append(
            PartnerBirthMatch(
                y,
                mo,
                d,
                concern[s:e],
                s,
                e,
                hour=hour,
                minute=minute,
                is_lunar=is_lunar,
                relation=relation,
                name=name,
                time_span=tspan,
            )
        )

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
