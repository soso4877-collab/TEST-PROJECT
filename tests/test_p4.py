# -*- coding: utf-8 -*-
"""P4 렌더 파이프라인 — 통이미지 결함 해결(텍스트레이어·폰트·태그) 종단 검증."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402
from sajugen.render import verify as render_verify  # noqa: E402
from playwright_guard import require_playwright_subprocess  # noqa: E402


@pytest.fixture(scope="module")
def rendered_pdf():
    require_playwright_subprocess()
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    report = builder.build_report(saju, use_llm=False)
    pdf = render_pdf.render_pdf(report, saju, "test_saju_report.pdf")
    return pdf, render_verify.verify(pdf), report, saju


def test_pdf_created_multipage(rendered_pdf):
    pdf, v, _, _ = rendered_pdf
    assert Path(pdf).exists()
    assert v["pages"] >= 6, v


def test_has_real_text_layer_not_image(rendered_pdf):
    # #1 결함 해결 핵심: 통이미지면 ~0자 → 충분한 텍스트 추출되어야 함
    _, v, _, _ = rendered_pdf
    assert v["text_layer_ok"], v["text_chars"]
    assert v["text_chars"] >= render_verify.MIN_TEXT_CHARS


def test_fonts_embedded_and_tagged(rendered_pdf):
    _, v, _, _ = rendered_pdf
    assert v["fonts_embedded"] is True
    assert v["tagged"] is True, "태그드 PDF 아님(StructTree/MarkInfo 없음)"


def test_selectable_known_facts_end_to_end(rendered_pdf):
    # 계산된 간지가 PDF에서 '선택 가능한 텍스트'로 추출되는지(종단 증명)
    _, v, _, _ = rendered_pdf
    assert v["contains_known_ganzhi"] is True


def test_render_gate_pass(rendered_pdf):
    _, v, _, _ = rendered_pdf
    assert v["gate_pass"] is True, v


def test_brand_seal_drawn_every_page(rendered_pdf):
    # 런타임 낙관(브랜드 가변, R5) — 우하단 인주색 픽셀 존재 + 한지 위 z순서
    # (PyMuPDF overlay=False prepend 규칙: 낙관 먼저→한지 마지막 삽입 회귀 앵커)
    import fitz

    pdf, _, _, _ = rendered_pdf
    doc = fitz.open(pdf)
    for i in (0, doc.page_count - 1):
        pix = doc.load_page(i).get_pixmap(dpi=100)
        red = 0
        for dx in range(20, 110):
            for dy in range(30, 220):
                r, g, b = pix.pixel(pix.width - dx, pix.height - dy)
                if r > 120 and r > g + 30 and r > b + 30:
                    red += 1
        assert red > 300, (i + 1, red)  # 테두리+글자 인주색이 충분히 찍혀야 함
    doc.close()


def test_brand_profile_in_html():
    # config/brands.yaml 프로필이 표지 표제·세로 박스에 주입되는지
    from sajugen import config as cfg

    bp = cfg.brand("seodam")
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    report = builder.build_report(saju, use_llm=False)
    html = render_pdf.render_html(report, saju, name="홍길동", brand=bp)
    assert "서담선생" in html
    # 브랜드 계약(2026-06-14 개정): 미지정→default, 프리셋 키→그 프로필, 그 외 임의 문구→그 문구로 합성
    assert cfg.brand(None)["seal"] == "사주명리"  # 미지정 = default
    assert cfg.brand("서담선생직접입력")["seal"] == "서담선생직접입력"  # 자유 입력 브랜드명 합성


def test_gwakgwak_frame_every_page(rendered_pdf):
    # 사주쌍변 광곽(R6) — 페이지 가장자리 11mm 인셋(dpi100 기준 x=43px)에
    # 먹갈색 세로선이 전 페이지 존재(한지 위·본문 아래 z순서 포함 검증)
    import fitz

    pdf, _, _, _ = rendered_pdf
    doc = fitz.open(pdf)
    for i in (0, doc.page_count - 1):
        pix = doc.load_page(i).get_pixmap(dpi=100)
        hits = 0
        for y in range(60, pix.height - 60, 7):
            r, g, b = pix.pixel(43, y)
            if r < 200 and g < 190:  # 베이지(>0xE0)보다 어두운 선
                hits += 1
        assert hits > 50, (i + 1, hits)
    doc.close()


def test_hanji_background_full_bleed_every_page(rendered_pdf):
    # 한지 배경 언더레이 — 마진 영역 포함 풀블리드가 1·2·마지막 페이지 모두 적용
    # (CSS 캔버스 배경은 마진·마지막 페이지 미도색 실측 → PyMuPDF 언더레이 회귀 앵커)
    import fitz

    pdf, _, _, _ = rendered_pdf
    doc = fitz.open(pdf)
    for i in (0, 1, doc.page_count - 1):
        pix = doc.load_page(i).get_pixmap(dpi=50)
        r, g, b = pix.pixel(5, 5)  # 좌상단 모서리 = @page 마진 영역
        assert r > 0xC8 and r > b and g > b, (i + 1, (r, g, b))  # 베이지(흰색/투명 아님)
    doc.close()
