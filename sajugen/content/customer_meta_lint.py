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
        re.compile(
            r"이\s*(?:글|문서|리포트)\s*은|고객용\s*문서|수신자|한\s*분께\s*드리는"
        ),
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
]


def lint(text: str) -> list[dict]:
    """Return aggregated lint hits. Source sentences are never returned."""

    counts: Counter[str] = Counter()
    for rule, rx in _RULES:
        matches = rx.findall(text or "")
        if matches:
            counts[rule] += len(matches)
    return [
        {"type": "ai_meta", "rule": rule, "count": count}
        for rule, count in sorted(counts.items())
    ]


def is_clean(text: str) -> bool:
    return not lint(text)


def summarize(hits: list[dict]) -> dict:
    total = sum(int(h.get("count", 1)) for h in hits)
    return {
        "clean": total == 0,
        "total_count": total,
        "rules": [
            {"rule": h.get("rule"), "count": int(h.get("count", 1))}
            for h in hits
        ],
    }
