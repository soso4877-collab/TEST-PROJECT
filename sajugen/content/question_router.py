# -*- coding: utf-8 -*-
"""질문 라우터 — 고객 고민/질문을 카테고리로 분류(Phase 5 구간1, docs/06·09).

룰 폴백 = 결정론 키워드 매칭(무키·무비용·재현성). 향후 LLM 분류(AnthropicBackend.classify)가
동일 시그니처로 이 룰을 대체/보강한다. 분류 자체는 사실 생성이 아니라 라우팅이라 가드 대상 아님.
"""

from __future__ import annotations

from enum import Enum


class QuestionCategory(str, Enum):
    LOVE = "연애"
    JOB = "직업"
    WEALTH = "재물"
    HEALTH = "건강"
    RELATION = "대인"
    TIMING = "시기"
    GENERAL = "전반"


# (카테고리, 키워드) — 리스트 순서가 우선순위(앞이 먼저 매칭). 결정론.
_KEYWORDS: list[tuple[QuestionCategory, tuple[str, ...]]] = [
    (
        QuestionCategory.LOVE,
        (
            "연애",
            "사랑",
            "애인",
            "결혼",
            "이별",
            "재회",
            "배우자",
            "궁합",
            "썸",
            "짝",
            "연인",
            "이혼",
            "남자친구",
            "여자친구",
            "전남친",
            "전여친",
            "헤어진",
            "다시 만날",
            "소개팅",
            "맞선",
        ),
    ),
    (
        QuestionCategory.JOB,
        (
            "직업",
            "취업",
            "이직",
            "진로",
            "사업",
            "승진",
            "퇴사",
            "직장",
            "커리어",
            "면접",
            "합격",
            "창업",
            "일자리",
        ),
    ),
    (
        QuestionCategory.WEALTH,
        (
            "재물",
            "재정",
            "투자",
            "빚",
            "대출",
            "수입",
            "월급",
            "부동산",
            "자산",
            "재산",
            "땅",
            "토지",
            "자식복",
            "주식",
            "재테크",
            "자금",
            "돈",
        ),
    ),
    (
        QuestionCategory.HEALTH,
        ("건강", "질병", "수술", "컨디션", "스트레스", "우울", "불면", "체력", "병원"),
    ),
    (
        QuestionCategory.RELATION,
        ("인간관계", "대인", "친구", "가족", "부모", "자식", "상사", "동료", "갈등", "관계"),
    ),
    (QuestionCategory.TIMING, ("언제", "시기", "타이밍", "이사", "개업", "택일", "적기")),
]


def classify(concern: str | None) -> QuestionCategory:
    """고민/질문 텍스트 → 카테고리. concern 없거나 매칭 0 → 전반.

    리스트 우선순위로 첫 매칭 카테고리 반환(예: '언제 결혼'은 연애가 시기보다 앞이라 연애).
    """
    if not concern or not concern.strip():
        return QuestionCategory.GENERAL
    text = concern.strip()
    for cat, kws in _KEYWORDS:
        if any(kw in text for kw in kws):
            return cat
    return QuestionCategory.GENERAL
