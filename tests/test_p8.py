# -*- coding: utf-8 -*-
"""P8 MVP 릴리스 게이트 — 3개 입력 아키타입(평일/윤달/시진불명) 풀사이클 E2E.

각 케이스를 pipeline.generate(use_llm=False=룰 백엔드=무비용·결정론)로 통과시키고
렌더 게이트(text_layer/fonts/tagged)와 입력 아키타입별 불변식을 검증한다.
윤달 케이스는 실 KASI 캐시(data/kasi_cache.sqlite)가 있을 때만 실행(없으면 skip).
"""

import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import pipeline  # noqa: E402
from sajugen.calc import kasi  # noqa: E402
from sajugen.input import normalize as norm  # noqa: E402


def _assert_gate(r):
    # 통이미지 결함 차단: 텍스트레이어·폰트 임베드·태그 + 명리↔자미 교차 일치(절대규칙 7)
    assert r.verify["gate_pass"], r.verify
    assert r.verify["text_layer_ok"] and r.verify["fonts_embedded"] and r.verify["tagged"]
    assert r.calc_consistent, r.crosscheck_warnings
    assert r.ok, r.reasons


def test_e2e_solar_weekday():
    # 평일: 평범한 양력 생년월일시 → 풀사이클 게이트 통과
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
    # 시진불명: unknown_time=True → 게이트 통과 + 시주 추정 고지(절대규칙 8) 본문 반영
    r = pipeline.generate(
        1995,
        7,
        7,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
        name="박미상",
        unknown_time=True,
        out_name="e2e_p8_unknown.pdf",
    )
    _assert_gate(r)
    doc = fitz.open(r.pdf_path)
    text = "".join(doc.load_page(i).get_text() for i in range(doc.page_count))
    doc.close()
    assert "추정" in text, "시진 불명 고지(추정) 누락"
