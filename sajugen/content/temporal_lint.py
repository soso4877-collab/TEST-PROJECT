# -*- coding: utf-8 -*-
"""시제 린터 — ref_year 기준, 이미 시작했거나 지난 해를 '아직 오지 않은' 미래로 서술하는
오류를 검출(H1-mini 2026-06-15).

예: ref_year=2026 에서 '2026년이 오기 전까지'는 틀림(이미 그 해 안). 위반 시 룰 골격 폴백.
연도 ≤ ref_year 인 경우만 잡아 미래 연도('2027년이 오기 전')는 정상 통과(보수적).
"""

from __future__ import annotations

from datetime import date
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


def _parse_ref_date(ref_date: str | date | None) -> date | None:
    if isinstance(ref_date, date):
        return ref_date
    if not ref_date:
        return None
    try:
        return date.fromisoformat(str(ref_date)[:10])
    except Exception:
        return None


def lint(text: str, ref_year: int | None, ref_date: str | date | None = None) -> list[dict]:
    """위반 목록(빈 리스트면 통과). ref_year 미지정 시 검사 생략."""
    if not ref_year:
        return []
    out: list[dict] = []
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
    return out


def is_clean(text: str, ref_year: int | None, ref_date: str | date | None = None) -> bool:
    return not lint(text, ref_year, ref_date=ref_date)
