# -*- coding: utf-8 -*-
"""LLM 백엔드 추상화 — Phase 5 부분 LLM 4구간의 provider-agnostic 레이어.

백엔드 2종(절대규칙14·docs/06):
- RuleBackend(기본·무키): 모든 메서드가 결정론 룰 산출/원문 패스스루. 무비용·항상 가드 통과.
- AnthropicBackend(ANTHROPIC_API_KEY 있을 때만): instructor+pydantic. 분류=Haiku, 윤문=기존 llm_polish.
  ※ 자체호스팅 로컬(Ollama/vLLM) 백엔드는 범위 제외(하드웨어 필요·운영자 의도=API 키).

계약 불변: 백엔드는 '텍스트만' 생성한다. 사실 슬롯 외 생성 금지·가드(safe_lint/factcheck/trace)
재검증·APPROVED 전 발송 금지는 호출측(builder/store)이 책임진다(절대규칙12·13·16). 어떤 백엔드든
실패 시 룰 폴백.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from . import llm_polish
from .question_router import QuestionCategory
from .question_router import classify as _rule_classify

_CLASSIFY_SYSTEM = (
    "너는 한국어 사주 상담 신청 문장을 한 개의 카테고리로 분류한다. "
    "카테고리: 연애/직업/재물/건강/대인/시기/전반. "
    "애매하거나 해당 없음은 '전반'. 분류만 하고 다른 말은 하지 마라."
)


@runtime_checkable
class LLMBackend(Protocol):
    name: str

    def available(self) -> bool: ...

    def classify(self, concern: str | None) -> QuestionCategory: ...

    def polish(self, rule_text: str, title: str) -> str: ...


class RuleBackend:
    """무LLM 폴백 — 결정론. 무키 기본값."""

    name = "rule"

    def available(self) -> bool:
        return True

    def classify(self, concern: str | None) -> QuestionCategory:
        return _rule_classify(concern)

    def polish(self, rule_text: str, title: str) -> str:
        return rule_text  # 윤문 없음 = 룰 원문 그대로(항상 가드 통과)


class AnthropicBackend:
    """Anthropic 공식 API — 키 있을 때만. 실패는 전부 룰 폴백."""

    name = "anthropic"

    def available(self) -> bool:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return False
        try:
            import anthropic  # noqa: F401
            import instructor  # noqa: F401

            return True
        except Exception:
            return False

    def classify(self, concern: str | None) -> QuestionCategory:
        if not concern or not concern.strip():
            return QuestionCategory.GENERAL
        if not self.available():
            return _rule_classify(concern)
        try:
            import anthropic
            import instructor
            from pydantic import BaseModel

            class _Cat(BaseModel):
                category: QuestionCategory

            client = instructor.from_anthropic(anthropic.Anthropic())
            res = client.messages.create(
                model="claude-haiku-4-5-20251001",  # 분류=저비용
                max_tokens=20,
                system=_CLASSIFY_SYSTEM,
                messages=[{"role": "user", "content": concern.strip()}],
                response_model=_Cat,
            )
            return res.category
        except Exception:
            return _rule_classify(concern)  # 어떤 실패든 룰 폴백

    def polish(self, rule_text: str, title: str) -> str:
        # 구간5 재윤문 — 기존 검증된 구현 재사용(무키/실패 시 원문 폴백 내장)
        return llm_polish.polish(rule_text, title)


def get_backend() -> LLMBackend:
    """ANTHROPIC_API_KEY 있으면 Anthropic, 없으면 Rule. (config 강제 override 여지 — 차후)"""
    ab = AnthropicBackend()
    return ab if ab.available() else RuleBackend()
