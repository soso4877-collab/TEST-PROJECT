# -*- coding: utf-8 -*-
"""시제 린터 — ref_year 기준, 이미 시작했거나 지난 해를 '아직 오지 않은' 미래로 서술하는
오류를 검출(H1-mini 2026-06-15).

예: ref_year=2026 에서 '2026년이 오기 전까지'는 틀림(이미 그 해 안). 위반 시 룰 골격 폴백.
연도 ≤ ref_year 인 경우만 잡아 미래 연도('2027년이 오기 전')는 정상 통과(보수적).
"""

from __future__ import annotations

import re

_BEFORE = re.compile(r"(\d{4})\s*년이?\s*오기\s*전")  # 'YYYY년이 오기 전' / 'YYYY년 오기 전'
_UNTIL = re.compile(r"(\d{4})\s*년\s*전까지(?!\s*지)")  # 'YYYY년 전까지'(앞에 '오기' 없는 형태)


def lint(text: str, ref_year: int | None) -> list[dict]:
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
    return out


def is_clean(text: str, ref_year: int | None) -> bool:
    return not lint(text, ref_year)
