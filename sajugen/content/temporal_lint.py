# -*- coding: utf-8 -*-
"""시제 린터 — ref_year 기준, 이미 시작했거나 지난 해를 '아직 오지 않은' 미래로 서술하는
오류와 월운 표기·절기 경계 시제 오류를 검출(H1-mini 2026-06-15).

예: ref_year=2026 에서 '2026년이 오기 전까지'는 틀림(이미 그 해 안). 위반 시 룰 골격 폴백.
연도 ≤ ref_year 인 경우만 잡아 미래 연도('2027년이 오기 전')는 정상 통과(보수적).
"""

from __future__ import annotations

from datetime import date, timedelta
import re

_BEFORE = re.compile(r"(\d{4})\s*년이?\s*오기\s*전")  # 'YYYY년이 오기 전' / 'YYYY년 오기 전'
_UNTIL = re.compile(r"(\d{4})\s*년\s*전까지(?!\s*지)")  # 'YYYY년 전까지'(앞에 '오기' 없는 형태)
_MONTH_FUTURE = re.compile(
    r"(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월(?:이|은|에는|부터)?\s*"
    r"(?:다가오|오면|오게|오고|열리|시작되|들어오)"
)
# 지난 달을 '앞으로의 행동 시기'로 제시하는 형태(QI-2026-07-04-02) — 실사고: 7월 4일 생성
# 풀이가 "4월 안에 준비를 시작해 두라", "5월 이후부터 열어두고 보시길"을 권함. 기존
# _MONTH_FUTURE 는 도착동사(다가오/오면/열리) 전용이라 이 행동 권유 프레임을 놓쳤다(사각 인접).
# 회고 서술("4월에는 힘드셨을")은 행동 문맥이 없어 통과(양방 테스트로 고정).
_MONTH_DEADLINE = re.compile(  # 'N월 안에/까지/내로 ~(행동)' — 이미 지난 마감
    # 간격에 \n 허용(문장 경계 .!? 만 차단) — PDF 추출 텍스트는 시각적 줄바꿈이 문장 중간에
    # 끼므로 \n 배제 시 실검출 누락(실측: v3 '4월 안에 …\n준비를' 미탐).
    r"(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월\s*(?:안에|까지|내로|전까지)"
    r"[^.!?]{0,40}?(?:준비|시작|마련|정리|계획|움직|잡|열|보|권|해\s*두|해두|끝내|마치)"
)
_MONTH_ANCHOR = re.compile(  # 'N월 이후/부터 ~(권유)' — 과거 달을 기점으로 권유
    r"(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월\s*(?:이후|부터|이후부터)"
    r"[^.!?]{0,40}?(?:권합|권해|보시|살피|열어|시작|준비|잡|움직|계획)"
)
_MONTH_TOKEN = re.compile(r"(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월")
_GANJI_MONTH_BARE = re.compile(r"(?<![가-힣])([갑을병정무기경신임계][자축인묘진사오미신유술해]월)(?!\s*\()")
_GANJI_MONTH_RANGE = re.compile(
    r"([갑을병정무기경신임계][자축인묘진사오미신유술해]월)"
    r"\([^)]*?양력\s*(\d{1,2})/(\d{1,2})\s*~\s*(\d{1,2})/(\d{1,2})[^)]*\)"
)
_CURRENT_MONTH_WORD = re.compile(r"지금\s*이\s*달|이번\s*달|현재\s*달|지금의?\s*월운|현재의?\s*월운")
_NEXT_MONTH_WORD = re.compile(r"다음\s*달|다음\s*월운")


def _parse_ref_date(ref_date: str | date | None) -> date | None:
    if isinstance(ref_date, date):
        return ref_date
    if not ref_date:
        return None
    try:
        return date.fromisoformat(str(ref_date)[:10])
    except Exception:
        return None


def _month_token_allowed(text: str, match: re.Match) -> bool:
    """실제 날짜와 허용된 음력 보조 표기는 통과시키고, 월 라벨 단독 표기만 잡는다."""
    try:
        mo = int(match.group(2))
    except ValueError:
        return True
    if not 1 <= mo <= 12:
        return True
    tail = text[match.end() :]
    head = text[max(0, match.start() - 4) : match.start()]
    if re.match(r"\s*\d{1,2}\s*일", tail):
        return True
    if "음력" in head and re.match(r"\s*무렵", tail):
        return True
    return False


def _sentence_window(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("!", 0, start), text.rfind("?", 0, start), text.rfind("\n", 0, start))
    right_candidates = [p for p in (text.find(".", end), text.find("!", end), text.find("?", end), text.find("\n", end)) if p != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 : right]


def _interval_contains(ref: date, sm: int, sd: int, em: int, ed: int) -> bool:
    """연도 없는 절기 구간(M/D~M/D)을 기준일 주변 3개년에 맞춰 본다."""
    for yy in (ref.year - 1, ref.year, ref.year + 1):
        try:
            start = date(yy, sm, sd)
            end = date(yy + 1 if (em, ed) < (sm, sd) else yy, em, ed)
        except ValueError:
            continue
        if start <= ref < end:
            return True
    return False


def _next_month_start(ref: date) -> date:
    if ref.month == 12:
        return date(ref.year + 1, 1, 1)
    return date(ref.year, ref.month + 1, 1)


def _next_next_month_start(ref: date) -> date:
    nxt = _next_month_start(ref)
    return _next_month_start(nxt)


def _interval_starts_next_month(ref: date, sm: int, sd: int, em: int, ed: int) -> bool:
    """'다음 달'은 해당 간지월 절기 구간이 다음 양력월 안에서 시작할 때만 허용한다."""
    nxt = _next_month_start(ref)
    end_next = _next_next_month_start(ref)
    for yy in (ref.year - 1, ref.year, ref.year + 1):
        try:
            start = date(yy, sm, sd)
            _ = date(yy + 1 if (em, ed) < (sm, sd) else yy, em, ed)
        except ValueError:
            continue
        if nxt <= start < end_next:
            return True
    return False


def lint(text: str, ref_year: int | None, ref_date: str | date | None = None) -> list[dict]:
    """위반 목록(빈 리스트면 통과). ref_year 미지정 시 연도 시제 검사만 생략."""
    out: list[dict] = []
    if ref_year:
        for rx in (_BEFORE, _UNTIL):
            for m in rx.finditer(text):
                y = int(m.group(1))
                if y <= ref_year:
                    out.append(
                        {
                            "type": "temporal",
                            "match": m.group(0),
                            "why": f"{y}년은 기준연도 {ref_year} 이하 — 이미 시작/지난 해를 미래로 서술",
                        }
                    )
    for m in _MONTH_TOKEN.finditer(text):
        if _month_token_allowed(text, m):
            continue
        out.append(
            {
                "type": "month_notation",
                "match": m.group(0),
                "why": "맨몸 n월 표기는 양력·음력·절기월 오독 위험 — 간지월(절기명 - 양력 M/D~M/D) 또는 음력 n월 무렵으로 표기",
            }
        )
    for m in _GANJI_MONTH_BARE.finditer(text):
        out.append(
            {
                "type": "month_notation",
                "match": m.group(1),
                "why": "간지월은 절기명과 양력 구간을 함께 표기해야 함",
            }
        )
    rd = _parse_ref_date(ref_date)
    if rd:
        for rx, label in (
            (_MONTH_FUTURE, "지난 월을 미래로 서술"),
            (_MONTH_DEADLINE, "지난 월을 행동 마감으로 제시"),
            (_MONTH_ANCHOR, "지난 월을 권유 기점으로 제시"),
        ):
            for m in rx.finditer(text):
                y = int(m.group(1)) if m.group(1) else rd.year
                mo = int(m.group(2))
                if not 1 <= mo <= 12:
                    continue
                if (y, mo) < (rd.year, rd.month):
                    out.append(
                        {
                            "type": "temporal",
                            "match": m.group(0),
                            "why": f"{y}년 {mo}월은 기준일 {rd.isoformat()} 이전 — {label}",
                        }
                    )
        for m in _GANJI_MONTH_RANGE.finditer(text):
            sm, sd, em, ed = (int(m.group(i)) for i in range(2, 6))
            window = _sentence_window(text, m.start(), m.end())
            if _CURRENT_MONTH_WORD.search(window) and not _interval_contains(rd, sm, sd, em, ed):
                out.append(
                    {
                        "type": "relative_month_boundary",
                        "match": window.strip(),
                        "why": f"기준일 {rd.isoformat()} 이 {m.group(1)} 절기 구간 밖인데 현재 월운으로 서술",
                    }
                )
            if _NEXT_MONTH_WORD.search(window) and not _interval_starts_next_month(rd, sm, sd, em, ed):
                out.append(
                    {
                        "type": "relative_month_boundary",
                        "match": window.strip(),
                        "why": f"기준일 {rd.isoformat()} 의 다음 양력월에 시작하는 간지월이 아닌데 다음 달로 서술",
                    }
                )
    return out


def is_clean(text: str, ref_year: int | None, ref_date: str | date | None = None) -> bool:
    return not lint(text, ref_year, ref_date=ref_date)
