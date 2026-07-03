# -*- coding: utf-8 -*-
"""고민 원문 결정론 마스킹 — 절대규칙 17(a): LLM 전달 전 생년월일·출생시각 치환.

consult 챕터 인용 블록 전용. 본인 생년월일(다양한 표기)·상대 생년월일(파서 스팬)·
시각(HH:MM)을 토큰으로 치환한다. audit·로그에도 마스킹본만 기록(절대규칙 17d).
"""

from __future__ import annotations

import re
from datetime import datetime

_MASK = "[생년월일 비공개]"
_MASK_T = "[출생시각 비공개]"


def mask_birth_in_text(text: str, self_civil: str | None) -> str:
    """임의 텍스트에서 본인 생년월일시 표기와 8자리 생일형 숫자를 결정론 치환.

    LLM 전송 전 방어겹(절대규칙 17) — 룰 텍스트에도 적용 가능. self_civil
    ("1989-01-02 07:40" 류)에서 파생한 표기 변형 전부를 [비공개] 토큰으로 바꾼다."""
    if not text:
        return text
    # 본인 생년월일 — input_civil 에서 파생한 표기 변형 전부
    if self_civil:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})[ T]?(\d{2}):(\d{2})?", self_civil)
        if m:
            y, mo, d, hh, mi = m.groups()
            dt = datetime(int(y), int(mo), int(d))
            variants = [
                f"{y}-{mo}-{d}",
                f"{y}.{mo}.{d}",
                f"{y}/{mo}/{d}",
                f"{y}{mo}{d}",
                f"{y[2:]}{mo}{d}",
                f"{y}년 {int(mo)}월 {int(d)}일",
                f"{y[2:]}년 {int(mo)}월 {int(d)}일",
                f"{int(mo)}월 {int(d)}일",
            ]
            _ = dt  # 유효성 확인용
            for v in variants:
                text = text.replace(v, _MASK)
            if hh and mi:
                text = text.replace(f"{hh}:{mi}", _MASK_T)
                text = text.replace(f"{int(hh)}시 {int(mi)}분", _MASK_T)
    # 남은 8자리 생년월일형 숫자 보수적 치환(연도 19/20 시작 8자리만)
    text = re.sub(r"(?<![\d\-])(19|20)\d{6}(?![\d\-])", _MASK, text)
    return text


def mask_concern(
    concern: str,
    *,
    self_civil: str | None = None,
    partner_spans: list[tuple[int, int]] | None = None,
) -> str:
    """고민 원문 → 마스킹본. partner_spans = input.partner 매치 스팬(우선 치환)."""
    if not concern:
        return ""
    text = concern
    # 1) 상대 생년월일(파서가 찾은 스팬) — 뒤에서부터 치환해 오프셋 보존
    for s, e in sorted(partner_spans or [], reverse=True):
        text = text[:s] + _MASK + text[e:]
    # 2) 본인 생년월일 변형 + 3) 8자리 숫자 (공용 헬퍼)
    return mask_birth_in_text(text, self_civil)
