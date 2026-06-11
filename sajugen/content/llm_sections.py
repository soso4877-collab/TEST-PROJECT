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

# 구간2·3·4 본문 생성(compose) 공통 시스템 — 근거 본문의 사실 범위 밖 생성 절대 금지.
# (절대규칙13: 사실 슬롯 외 새 사실 생성 금지 / 절대규칙11·§12: 단정·보장·예측정확도 주장 금지)
_COMPOSE_SYSTEM = (
    "너는 한국어 사주 상담 결과지의 한 섹션 본문을 쓰는 작가다. "
    "반드시 아래 '근거 본문'에 이미 담긴 사실(간지·오행·십성·별 이름·궁·수치·시기)만 사용하고, "
    "거기에 없는 새 간지·별 이름·숫자·연도·시기를 절대 만들지 마라. "
    "단정·공포·보장·운명론·적중 주장 금지(경향·참고·~할 수 있습니다 어조). "
    "의료·법률·투자·합격·재회 등은 단정하지 말고 '점검'이나 '전문가 상의' 틀로 적어라. "
    "근거 본문과 같은 사실 범위 안에서, 더 자연스럽고 따뜻하게, 상담하듯 풀어 써라. "
    "근거 본문에 없는 정보를 끌어오지 말고, 분량은 근거 본문의 0.8~1.6배."
)

# 섹션별 역할 안내(구간2=cross, 구간3=consult, 구간4=advice·closing)
_COMPOSE_GUIDE = {
    "cross": (
        "명리와 자미두수를 교차로 본 '통합 관점'을 설명한다. 명리는 시간의 흐름을, "
        "자미두수는 인생의 구조를 보는 역할 분담으로, 두 체계가 같은 출생 정보에서 "
        "어긋나지 않는다는 점이 풀이 토대의 안정성을 뜻함을 차분히 전한다. "
        "두 체계가 다른 부분은 '틀림'이 아니라 보는 층위가 다른 것으로 서술한다."
    ),
    "consult": (
        "신청자가 묻고 싶어 한 영역(아래 '신청 영역')을 중심으로, 이 결과지를 어떻게 "
        "읽으면 좋을지 안내한다. 결과를 단정하거나 보장하지 말고, 타고난 경향과 시기 "
        "흐름을 참고로 읽는 자료임을 분명히 한다. 신청자가 적은 원문 문장은 모른다고 "
        "전제하고, 영역 이름만으로 일반적인 읽기 방향을 안내한다."
    ),
    "advice": (
        "현실에 적용할 조언을 정리한다. 강점은 살리고 약한 축은 작은 습관으로 채우는 "
        "방향과, 상황→행동 형태의 점검 틀을 제안하되, 보장이 아니라 실행을 돕는 틀임을 "
        "밝힌다. 한 번에 많이 바꾸기보다 한두 가지를 꾸준히 점검하는 방식을 권한다."
    ),
    "closing": (
        "결과지를 마무리하는 따뜻한 격려를 전한다. 타고난 기운은 방향을 보는 참고이지 "
        "정해진 결말이 아니며, 선택과 노력·환경에 따라 길이 달라질 수 있음을 분명히 한다."
    ),
}


@runtime_checkable
class LLMBackend(Protocol):
    name: str

    def available(self) -> bool: ...

    def classify(self, concern: str | None) -> QuestionCategory: ...

    def polish(self, rule_text: str, title: str) -> str: ...

    def compose(self, *, section_id: str, title: str, category: str, base_text: str) -> str: ...


class RuleBackend:
    """무LLM 폴백 — 결정론. 무키 기본값."""

    name = "rule"

    def available(self) -> bool:
        return True

    def classify(self, concern: str | None) -> QuestionCategory:
        return _rule_classify(concern)

    def polish(self, rule_text: str, title: str) -> str:
        return rule_text  # 윤문 없음 = 룰 원문 그대로(항상 가드 통과)

    def compose(self, *, section_id: str, title: str, category: str, base_text: str) -> str:
        return base_text  # 본문 생성 없음 = 룰 골격 그대로(항상 가드 통과)


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

    def compose(self, *, section_id: str, title: str, category: str, base_text: str) -> str:
        # 구간2·3·4 본문 생성 — Sonnet 4.6(통합·답변·조언). 근거 본문의 사실만 사용.
        # 호출측(builder)이 결과를 3단 가드 재검증하고, 실패/무변경이면 룰 골격 폴백.
        if not self.available():
            return base_text
        guide = _COMPOSE_GUIDE.get(section_id)
        if not guide:
            return base_text  # 정의된 구간이 아니면 손대지 않음
        try:
            import anthropic
            import instructor
            from pydantic import BaseModel

            class _Body(BaseModel):
                text: str

            user = f"[섹션 역할]\n{guide}\n"
            if section_id == "consult":
                user += f"\n[신청 영역]\n{category}\n"
            user += f"\n[근거 본문(이 사실만 사용, 새 사실 추가 금지)]\n{base_text}"

            client = instructor.from_anthropic(anthropic.Anthropic())
            res = client.messages.create(
                model="claude-sonnet-4-6",  # 통합·답변·조언 = 본문 품질 모델
                max_tokens=2000,  # 룰 골격(~0.4~1.4k자)의 1.6배 + JSON 래핑 여유
                system=_COMPOSE_SYSTEM,
                messages=[{"role": "user", "content": user}],
                response_model=_Body,
            )
            return (res.text or "").strip() or base_text
        except Exception:
            return base_text  # 어떤 실패든 룰 골격 폴백


def get_backend() -> LLMBackend:
    """ANTHROPIC_API_KEY 있으면 Anthropic, 없으면 Rule. (config 강제 override 여지 — 차후)"""
    ab = AnthropicBackend()
    return ab if ab.available() else RuleBackend()
