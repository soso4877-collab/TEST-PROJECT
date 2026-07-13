# -*- coding: utf-8 -*-
"""P8 MVP 릴리스 게이트 — 3개 입력 아키타입(평일/윤달/시진불명) 풀사이클 E2E.

각 케이스를 pipeline.generate(use_llm=False=룰 백엔드=무비용·결정론)로 통과시키고
렌더 게이트(text_layer/fonts/tagged)와 입력 아키타입별 불변식을 검증한다.
윤달 케이스는 실 KASI 캐시(data/kasi_cache.sqlite)가 있을 때만 실행(없으면 skip).
"""

import re
import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sajugen import pipeline  # noqa: E402
from sajugen.calc import kasi  # noqa: E402
from sajugen.content import unknown_time_policy  # noqa: E402
from sajugen.input import normalize as norm  # noqa: E402
from playwright_guard import require_playwright_subprocess  # noqa: E402


def _assert_gate(r):
    # 통이미지 결함 차단: 텍스트레이어·폰트 임베드·태그 + 명리↔자미 교차 일치(절대규칙 7)
    assert r.verify["gate_pass"], r.verify
    assert r.verify["text_layer_ok"] and r.verify["fonts_embedded"] and r.verify["tagged"]
    assert r.calc_consistent, r.crosscheck_warnings
    assert r.ok, r.reasons


def test_e2e_solar_weekday():
    # 평일: 평범한 양력 생년월일시 → 풀사이클 게이트 통과
    require_playwright_subprocess()
    r = pipeline.generate(
        1988,
        3,
        15,
        10,
        30,
        is_male=True,
        horoscope_date="2026-06-01",
        name="김평일",
        out_name="e2e_p8_solar.pdf",
    )
    _assert_gate(r)


def _real_cache():
    c = kasi.KasiCache()
    return c if c.exists else None


def test_e2e_lunar_leap():
    # 윤달: 2012 윤3월1일 → 양력 2012-04-21 (KASI 한국기준, 한·중 상이일). 캐시 없으면 skip.
    require_playwright_subprocess()
    c = _real_cache()
    if c is None:
        pytest.skip("실 KASI 캐시 미구축")
    nd = norm.normalize_date(2012, 3, 1, is_lunar=True, is_leap=True, cache=c)
    assert (nd.year, nd.month, nd.day) == (2012, 4, 21), nd
    # 한·중 상이일 경고가 surface 되는지(검수자 인지용)
    assert any("한·중 음력 상이일" in w for w in nd.warnings), nd.warnings
    r = pipeline.generate(
        nd.year,
        nd.month,
        nd.day,
        9,
        0,
        is_male=False,
        horoscope_date="2026-06-01",
        name="이윤달",
        out_name="e2e_p8_leap.pdf",
    )
    _assert_gate(r)


def test_e2e_unknown_time():
    # 레거시 호출자는 12:00+unknown_time=True를 계속 보낼 수 있지만, 결과는 정오
    # 추정이 아니라 신고 날짜 기준 삼주로 정규화돼야 한다. 비절입 날짜를 사용해
    # 렌더 계약만 검증하고, 절입 차단은 calc 전용 테스트에서 별도로 고정한다.
    require_playwright_subprocess()
    r = pipeline.generate(
        2000,
        1,
        15,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
        name="합성미상",
        unknown_time=True,
        out_name="e2e_p8_unknown.pdf",
    )
    _assert_gate(r)
    doc = fitz.open(r.pdf_path)
    text = "".join(doc.load_page(i).get_text() for i in range(doc.page_count))
    doc.close()
    # 한국어는 음절 사이에서도 줄이 바뀔 수 있어 "해석\n은"을 "해석 은"으로 만드는
    # 공백 보존 정규화로는 원문을 복원할 수 없다. 추출문과 대조 상수를 모두 무공백화해
    # 조판 위치와 무관하게 동일 고객 문구를 판정한다(라운드21 E2E 잠복 결함 회귀).
    normalized_text = re.sub(r"\s+", "", text)
    normalized_notice = re.sub(r"\s+", "", unknown_time_policy.THREE_PILLAR_NOTICE)
    assert normalized_text.count(normalized_notice) == 1
    assert "年柱" in normalized_text and "月柱" in normalized_text and "日柱" in normalized_text

    # 금지 토큰도 무공백화하면 개행으로 쪼개진 누출을 숨길 수 없다. 어절 경계가 합쳐져
    # 과탐할 가능성은 fail-closed로 수용하며, RED이면 조판 오탐인지 실제 누출인지 조사한다.
    for forbidden in (
        "時柱",
        "12:00",
        "정오",
        "추정",
        "진태양시",
        "시주",
        "사주팔자",
        "자미두수",
        "두 체계를 함께 읽으며",
    ):
        normalized_forbidden = re.sub(r"\s+", "", forbidden)
        assert normalized_forbidden not in normalized_text, (
            f"삼주 PDF에 금지 토큰 잔존: {forbidden}"
        )
