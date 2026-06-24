# -*- coding: utf-8 -*-
"""문장 품질 린터 — LLM 산문의 의미 모순·알려진 오타를 보수적으로 검출(H1-mini 2026-06-15).

safe_lint(§12 안전)·style_lint(AI틱)·factcheck(사실)가 못 잡는 '말이 안 되는 문장'을
잡는다: (1) 신강/신약 모순, (2) '재무'를 '재수'로 쓴 오타(돈 맥락), (3) 이름 뒤 재수.
위반 시 builder/gunghap 가드에서 룰 골격 폴백(재작성). 과탐 방지를 위해 known bad 중심 —
'재수가 좋다'(운) 같은 정상 표현은 검출하지 않는다.
"""

from __future__ import annotations

import re

# 1) 의미 모순쌍 — 신강과 신약은 동시 성립 불가
_CONTRADICTIONS = [
    re.compile(r"신강한\s*신약"),
    re.compile(r"신약한\s*신강"),
]
# 2) 재무→재수 오타: '재수'가 돈/재물 맥락에 붙은 경우만(운세의 '재수가 좋다'는 미검출)
_TYPO = [
    re.compile(r"재수(?:는|가|를|의)?\s*(?:돈|재물|재정|자금|흐름)"),
]
_ADJACENT_HANGUL_DUP_RX = re.compile(
    r"(?<![\uac00-\ud7a3])(?P<word>[\uac00-\ud7a3]{2,8})(?:\s+(?P=word))+(?![\uac00-\ud7a3])"
)


def lint(text: str, names: list[str] | None = None) -> list[dict]:
    """위반 목록(빈 리스트면 통과). names = 사람 이름(이름 뒤 재수 오타 앵커용, 선택)."""
    out: list[dict] = []
    for rx in _CONTRADICTIONS:
        for m in rx.finditer(text):
            out.append({"type": "contradiction", "match": m.group(0), "why": "신강/신약 모순"})
    for rx in _TYPO:
        for m in rx.finditer(text):
            out.append({"type": "typo", "match": m.group(0), "why": "재무→재수 오타 의심(돈 맥락)"})
    for m in _ADJACENT_HANGUL_DUP_RX.finditer(text):
        out.append({"type": "adjacent_duplicate", "match": m.group(0), "why": "인접 단어 반복"})
    for nm in names or []:
        if not nm:
            continue
        for m in re.finditer(re.escape(nm) + r"\s*,?\s*재수", text):
            out.append(
                {"type": "name_typo", "match": m.group(0), "why": f"{nm} 뒤 재수(재무 오타 의심)"}
            )
    return out


def is_clean(text: str, names: list[str] | None = None) -> bool:
    return not lint(text, names)
