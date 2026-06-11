# -*- coding: utf-8 -*-
"""LLM 윤문(옵션) — Instructor+pydantic으로 '표현만' 다듬음. 사실 슬롯 불변.

- ANTHROPIC_API_KEY 없거나 instructor/anthropic 미가용 → 룰 원문 그대로 반환(무비용·무위험).
- LLM은 사실(干支·별·궁·수치) 추가/변경 금지. 결과는 호출측에서 다시 가드 검증.
"""

from __future__ import annotations

import os

_SYSTEM = (
    "너는 한국어 사주 상담 결과지의 '윤문' 담당이다. 입력 문장의 "
    "사실(간지·오행·십성·별·궁·수치·시기)은 절대 바꾸거나 추가하지 마라. "
    "표현만 따뜻하고 읽기 쉽게 다듬어라. 단정·공포·보장 표현 금지(경향·참고 어조). "
    "새 간지나 별 이름을 만들지 마라. 길이는 원문의 ±30% 이내."
)


def available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        import instructor  # noqa: F401

        return True
    except Exception:
        return False


def polish(rule_text: str, title: str) -> str:
    """가용 시 윤문 텍스트, 아니면 rule_text 그대로(폴백)."""
    if not available():
        return rule_text
    try:
        import anthropic
        import instructor
        from pydantic import BaseModel

        class Polished(BaseModel):
            text: str

        client = instructor.from_anthropic(anthropic.Anthropic())
        res = client.messages.create(
            model="claude-haiku-4-5-20251001",  # 윤문=단순작업 → 저비용 모델
            # 긴 섹션은 instructor 도구JSON 래핑으로 1200 초과→절단→폴백되던 이슈가 있어 상향
            max_tokens=2000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"[섹션:{title}]\n원문:\n{rule_text}"}],
            response_model=Polished,
        )
        return res.text.strip() or rule_text
    except Exception:
        return rule_text  # 어떤 실패든 안전 폴백
