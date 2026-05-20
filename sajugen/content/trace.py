# -*- coding: utf-8 -*-
"""그라운딩 트레이스 — 모든 해석 섹션이 계산 소스에 연결돼 있고 내용이 비어있지 않은지."""

from __future__ import annotations

from .sections_schema import _STATIC_OK


def check(sections) -> tuple[bool, list[dict]]:
    bad: list[dict] = []
    for s in sections:
        if not s.final_text.strip():
            bad.append({"id": s.id, "why": "빈 본문"})
            continue
        if s.id in _STATIC_OK:
            continue
        if not s.source_keys:
            bad.append({"id": s.id, "why": "그라운딩 소스 없음(정적 면제 아님)"})
    return (not bad), bad
