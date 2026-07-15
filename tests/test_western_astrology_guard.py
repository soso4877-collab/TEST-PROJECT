# -*- coding: utf-8 -*-
"""서양 점성술 off-domain 가드의 차단·오탐 경계 회귀."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import llm_sections, western_astrology_lint  # noqa: E402


_PROBES = (
    "당신은 사자자리 기질이 강한 분입니다.",
    "황도 12궁으로 보면 게자리에 가까운 성향입니다.",
    "태양 별자리는 쌍둥이자리에 속합니다.",
)


@pytest.mark.parametrize("text", _PROBES)
def test_observed_leak_probes_are_blocked(text):
    """기존 safe/style을 통과했던 세 문장도 전용 룰은 모두 차단한다."""

    hits = western_astrology_lint.lint(text)

    assert hits
    assert {hit["rule"] for hit in hits} == {"western_astrology"}
    assert all(hit["severity"] == "hard" for hit in hits)


@pytest.mark.parametrize(
    "token",
    (
        *western_astrology_lint.WESTERN_ZODIAC_SIGN_NAMES,
        "별자리",
        "황도",
        "점성",
        "점성술",
    ),
)
def test_all_zodiac_names_and_domain_terms_are_blocked(token):
    """황도 12궁 12종(사수/궁수 별칭)과 상위 도메인 토큰을 빠짐없이 막는다."""

    hits = western_astrology_lint.lint(f"합성 문장에는 {token} 해석이 있습니다.")

    assert hits
    assert any(hit["token"] == token for hit in hits)


@pytest.mark.parametrize(
    "text",
    (
        "관록궁 자리에서 일의 책임을 봅니다.",
        "생활의 중심을 잡고 자리를 잡아 갑니다.",
        "사자(獅子)는 용기를 상징하는 일상 비유입니다.",
        "게는 바닷가에서 볼 수 있습니다.",
        "처녀궁은 이 가드가 막는 컴파운드가 아닙니다.",
        "물고기는 일상에서 쓰는 동물 이름입니다.",
        "자미의 주성과 보좌성을 함께 봅니다.",
        "명반의 별은 해당 궁의 영역을 보완합니다.",
        "그에게 자리를 먼저 내어 줍니다.",
    ),
)
def test_myeongni_ziwei_and_bare_words_do_not_false_positive(text):
    """명리·자미 정상어와 컴파운드 인접 경계는 오탐 없이 통과한다."""

    assert western_astrology_lint.lint(text) == []


def test_compose_system_and_closing_guide_suppress_western_astrology():
    """공용 시스템과 closing 장별 지시 양쪽에 생성 억제 계약이 실제 존재한다."""

    assert "서양 점성술은 이 상품의 근거가 아니다" in llm_sections._COMPOSE_SYSTEM
    assert "별자리·황도 12궁·점성술" in llm_sections._COMPOSE_SYSTEM
    assert "서양 별자리·황도·점성술은 끌어오지 않는다" in llm_sections._COMPOSE_GUIDE[
        "closing"
    ]
    # 삼주 시스템은 공용 시스템에서 파생되므로 동일 금지 계약을 잃지 않아야 한다.
    assert "서양 점성술은 이 상품의 근거가 아니다" in (
        llm_sections._THREE_PILLAR_COMPOSE_SYSTEM
    )
