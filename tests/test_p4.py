# -*- coding: utf-8 -*-
"""P4 렌더 파이프라인 — 통이미지 결함 해결(텍스트레이어·폰트·태그) 종단 검증."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402
from sajugen.render import verify as render_verify  # noqa: E402

_SAJU = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
_REPORT = builder.build_report(_SAJU, use_llm=False)
_PDF = render_pdf.render_pdf(_REPORT, _SAJU, "test_saju_report.pdf")
_V = render_verify.verify(_PDF)


def test_pdf_created_multipage():
    assert Path(_PDF).exists()
    assert _V["pages"] >= 6, _V


def test_has_real_text_layer_not_image():
    # #1 결함 해결 핵심: 통이미지면 ~0자 → 충분한 텍스트 추출되어야 함
    assert _V["text_layer_ok"], _V["text_chars"]
    assert _V["text_chars"] >= render_verify.MIN_TEXT_CHARS


def test_fonts_embedded_and_tagged():
    assert _V["fonts_embedded"] is True
    assert _V["tagged"] is True, "태그드 PDF 아님(StructTree/MarkInfo 없음)"


def test_selectable_known_facts_end_to_end():
    # 계산된 간지가 PDF에서 '선택 가능한 텍스트'로 추출되는지(종단 증명)
    assert _V["contains_known_ganzhi"] is True


def test_render_gate_pass():
    assert _V["gate_pass"] is True, _V
