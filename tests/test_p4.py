# -*- coding: utf-8 -*-
"""P4 렌더 파이프라인 — 통이미지 결함 해결(텍스트레이어·폰트·태그) 종단 검증."""

import sys
import hashlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sajugen.calc import engine  # noqa: E402
from sajugen import config as cfg  # noqa: E402
from sajugen.content import builder  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402
from sajugen.render import verify as render_verify  # noqa: E402
from playwright_guard import require_playwright_subprocess  # noqa: E402


@pytest.fixture(scope="module")
def rendered_pdf():
    require_playwright_subprocess()
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    report = builder.build_report(saju, use_llm=False)
    pdf = render_pdf.render_pdf(
        report,
        saju,
        "test_saju_report.pdf",
        brand=cfg.brand("sajudoryeong"),
    )
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


def test_positive_render_fixture_uses_sajudoryeong_html_boundary():
    brand = cfg.brand("sajudoryeong")
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    report = builder.build_report(saju, use_llm=False)

    html = render_pdf.render_html(report, saju, name="홍길동", brand=brand)

    assert brand["seal"] == "사주도령"
    assert "사주도령" in html
    assert "서담선생" not in html
    assert "사주명리" not in html


def test_sajudoryeong_assets_do_not_share_legacy_seal_cache_if_present():
    from sajugen.render.assets import make_assets

    sajudoryeong = Path(make_assets.seal_png_path("사주도령"))
    seodam = Path(make_assets.seal_png_path("서담선생"))
    neutral_svg = Path(render_pdf._DIR, "assets", "hanji.svg")

    assert sajudoryeong != seodam
    assert "서담선생" not in sajudoryeong.name
    assert "사주도령" not in seodam.name
    if sajudoryeong.is_file() and seodam.is_file():
        assert hashlib.sha256(sajudoryeong.read_bytes()).hexdigest() != hashlib.sha256(
            seodam.read_bytes()
        ).hexdigest()
    if neutral_svg.is_file():
        svg = neutral_svg.read_text(encoding="utf-8")
        assert "서담선생" not in svg
        assert "사주도령" not in svg
        assert "사주명리" not in svg


def test_print_css_has_no_legacy_brand_content_or_image_swap():
    template = Path(render_pdf._DIR, "templates", "report.html.j2").read_text(encoding="utf-8")

    assert "서담선생" not in template
    assert "사주명리" not in template
    if "@media print" in template:
        print_css = template.split("@media print", 1)[1]
        assert "서담선생" not in print_css
        assert "사주명리" not in print_css
        assert "background-image" not in print_css


def test_render_requires_explicit_brand():
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    report = builder.build_report(saju, use_llm=False)
    with pytest.raises(ValueError, match="brand"):
        render_pdf.render_html(report, saju, name="홍길동")


def _fake_report():
    from types import SimpleNamespace

    section = SimpleNamespace(id="a", title="합성", source_keys=["m"], final_text="본문입니다.")
    return SimpleNamespace(sections=[section]), SimpleNamespace(input_civil="합성")


class _FakePage:
    def goto(self, url):
        self.url = url

    def emulate_media(self, media):
        self.media = media

    def evaluate(self, script):
        self.script = script

    def pdf(self, *, path, **kwargs):
        Path(path).write_bytes(b"%PDF-1.7\nsynthetic staging\n")


class _FakeBrowser:
    def __init__(self):
        self.closed = False

    def new_page(self):
        return _FakePage()

    def close(self):
        self.closed = True


class _FakeChromium:
    def __init__(self, browser):
        self._browser = browser

    def launch(self):
        return self._browser


class _FakePlaywrightContext:
    def __init__(self, browser):
        self.chromium = _FakeChromium(browser)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_render_pdf_keeps_brand_profile_separate_from_browser(tmp_path, monkeypatch):
    report, saju = _fake_report()
    fake_browser = _FakeBrowser()
    seen = {}

    monkeypatch.setattr(render_pdf, "_OUT", str(tmp_path))
    monkeypatch.setattr(render_pdf, "sync_playwright", lambda: _FakePlaywrightContext(fake_browser))
    monkeypatch.setattr(
        render_pdf,
        "_apply_background",
        lambda pdf_path, *, seal_text: seen.setdefault("seal_text", seal_text),
    )
    monkeypatch.setattr(render_pdf, "harden_pdf_ua", lambda *args, **kwargs: None)

    path = render_pdf.render_pdf(report, saju, "brand_contract.pdf", brand=cfg.brand("sajudoryeong"))

    assert seen["seal_text"] == "사주도령"
    assert Path(path).is_file()
    assert Path(path).name == "brand_contract.pdf"
    assert fake_browser.closed is True


def test_render_pdf_does_not_publish_partial_pdf_when_postprocess_fails(tmp_path, monkeypatch):
    report, saju = _fake_report()
    target = tmp_path / "partial.pdf"
    target.write_bytes(b"existing-target")

    monkeypatch.setattr(render_pdf, "_OUT", str(tmp_path))
    monkeypatch.setattr(render_pdf, "sync_playwright", lambda: _FakePlaywrightContext(_FakeBrowser()))

    def fail_background(pdf_path, *, seal_text):
        raise RuntimeError("postprocess failed")

    monkeypatch.setattr(render_pdf, "_apply_background", fail_background)
    monkeypatch.setattr(render_pdf, "harden_pdf_ua", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="postprocess failed"):
        render_pdf.render_pdf(report, saju, target.name, brand=cfg.brand("sajudoryeong"))

    assert target.read_bytes() == b"existing-target"
    leftovers = [p.name for p in tmp_path.iterdir() if p.suffix == ".pdf" and p.name != target.name]
    assert leftovers == []


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
