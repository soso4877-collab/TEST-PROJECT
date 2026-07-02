# -*- coding: utf-8 -*-
"""Customer-facing document meta/style residue lint.

This module detects editor/AI/document-structure phrasing that should not
survive into a customer PDF. Hits are intentionally aggregated by rule and do
not include source sentences or raw customer text.
"""

from __future__ import annotations

import re
from collections import Counter


_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "document_self_reference",
        re.compile(r"이\s*(?:글|문서|리포트)\s*은|고객용\s*문서|수신자|한\s*분께\s*드리는"),
    ),
    (
        "product_structure_label",
        re.compile(r"통합\s*(?:풀이|문서)|(?:개인|궁합|관계)\s*파트"),
    ),
    (
        "anti_generalized_letter_reading",
        re.compile(r"일반론이\s*아니라|실제\s*글자\s*하나하나"),
    ),
    (
        "guided_structure_walkthrough",
        re.compile(
            r"함께\s*읽습니다|차례로\s*보겠습니다|따라와\s*주세요|구조를\s*설명드리면|"
            r"(?:먼저|이어서|다음으로|각\s*파트|이\s*(?:글|문서|리포트)에서)"
            r"[^.\n!?]{0,60}살펴보겠습니다"
        ),
    ),
    (
        "formulaic_conclusion",
        re.compile(r"핵심은\s*다음과\s*같습니다|^\s*(?:종합하면|결론적으로)\s*[,，]?", re.M),
    ),
    (
        # 문서 진행/섹션 예고/다음 파트 안내 = 작성자 메타 발화(고객 풀이 내용 아님).
        # 예: "자미두수 명궁 이야기도 바로 이어집니다"·"다음 장에서는 …보겠습니다"·
        #     "이 풀이는 다음 순서로 이어집니다"·"관계 파트가 이어집니다".
        # 원칙(오탐 방지): '이어집니다'·'이야기'·'명궁' 단독은 차단하지 않는다(생활 흐름
        # "관계가 이어집니다"·"일이 이어집니다"·"흐름이 이어집니다"는 통과). 구조어(이야기/
        # 파트/장/다음/이어서/앞서 등)와 진행 앵커(이어집니다/보겠습니다/살펴보겠습니다/
        # 다룹니다)가 **함께** 쓰일 때만 FAIL 처리한다.
        "transition_section_preview",
        re.compile(
            r"이야기[^.\n!?]{0,20}이어집니다"
            r"|(?:파트|장에서는?)[^.\n!?]{0,20}(?:이어집니다|다룹니다|보겠습니다)"
            r"|(?:다음|이어서|앞서|앞에서)[^.\n!?]{0,25}(?:이어집니다|살펴보겠습니다|보겠습니다|다룹니다)"
        ),
    ),
]


def lint(text: str) -> list[dict]:
    """Return aggregated lint hits. Source sentences are never returned."""

    counts: Counter[str] = Counter()
    for rule, rx in _RULES:
        matches = rx.findall(text or "")
        if matches:
            counts[rule] += len(matches)
    return [
        {"type": "ai_meta", "rule": rule, "count": count} for rule, count in sorted(counts.items())
    ]


def is_clean(text: str) -> bool:
    return not lint(text)


def summarize(hits: list[dict]) -> dict:
    total = sum(int(h.get("count", 1)) for h in hits)
    return {
        "clean": total == 0,
        "total_count": total,
        "rules": [{"rule": h.get("rule"), "count": int(h.get("count", 1))} for h in hits],
    }
