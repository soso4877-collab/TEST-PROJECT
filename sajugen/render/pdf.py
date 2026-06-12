# -*- coding: utf-8 -*-
"""Report23 → Jinja2 HTML → Playwright Chromium tagged PDF.

#1 결함(통이미지) 해결: 선택·검색 가능한 텍스트 레이어 + 폰트 임베드 + 태그/아웃라인.
@page CSS + Chromium 네이티브 페이지네이션. 폰트는 번들 OFL(나눔명조 본문,
한자 폴백 Source Han Serif K)만 서브셋 임베드 — 시스템 폰트 의존 금지.
"""

from __future__ import annotations

import os
import re

import fitz
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from . import charts

_DIR = os.path.dirname(__file__)
_OUT = os.path.join(_DIR, "out")
# 번들 폰트(SIL OFL) 디렉터리 → @font-face file:/// 절대경로. Chromium 이
# PDF 생성 시 사용 글리프만 서브셋 임베드(PDF/UA 7.1-3 개선·결정론).
_FONT_DIR = "file:///" + os.path.join(_DIR, "fonts").replace("\\", "/")
# 페이지 마진 단일 소스 — @page CSS(Jinja 주입)와 pg.pdf margin이 같은 상수를 쓴다
# (render.md: 둘은 반드시 동기화).
_PAGE_MARGIN = {"top": "22mm", "bottom": "22mm", "left": "20mm", "right": "20mm"}
# 한지 배경(낙관 합성, assets/make_assets.py 산출). CSS 캔버스 배경은 Chromium
# print에서 마진 영역·마지막 페이지가 칠해지지 않는 것을 실측(2026-06-12)
# → PyMuPDF 언더레이(전 페이지·XObject 1회 임베드)로 풀블리드 적용.
_BG_PATH = os.path.join(_DIR, "assets", "hanji_bg.jpg")
_PAGE_MARGIN_CSS = (
    f"{_PAGE_MARGIN['top']} {_PAGE_MARGIN['right']} {_PAGE_MARGIN['bottom']} {_PAGE_MARGIN['left']}"
)
# 본문 내 산출 방식 고지(자동 분석 도구·AI 언급)는 넣지 않는다
# (절대규칙 18 개정, 2026-06-12 운영자 지시). colophon = 맺음 서명 슬롯.
# 챕터 마스트헤드(페이지 시작) — 5챕터. id → (번호, 제목, 설명).
# .chapter 가 page-break-before 를 가지므로 강제 디바이더는 이 5곳만.
_CHAPTERS = {
    "summary": (1, "큰 그림", "내 사주의 전체 윤곽과 핵심 단서"),
    "love": (2, "영역별 흐름", "관계·일·재물에서 힘이 실리는 결"),
    "daewoon": (3, "시간의 결", "대운과 가까운 시기의 흐름"),
    "ziwei_summary": (4, "구조와 적용", "자미두수 명반과 현실 적용"),
    "appendix_terms": (5, "부록", "용어 풀이와 다음 걸음"),
}

_env = Environment(
    loader=FileSystemLoader(os.path.join(_DIR, "templates")),
    autoescape=select_autoescape(["html", "j2"]),
)


def render_html(
    report,
    saju,
    age: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
) -> str:
    # 도판 전면 제거(운영자 지시 — 목차+글만). 챕터·번호·차트 변수 미전달.
    # 본문은 빈 줄 기준 문단 분할 → 템플릿 <p> 렌더(단문 호흡 보존 + tagged 구조 개선).
    secs = [
        {"id": s.id, "title": s.title, "paragraphs": _split_paragraphs(s.final_text)}
        for s in report.sections
    ]
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(
        title="사주풀이 결과지",
        font_dir=_FONT_DIR,
        page_margin_css=_PAGE_MARGIN_CSS,
        cover_name=(f"{name} 님" if name else ""),
        cover_sub=(f"{saju.input_civil}" + ("  (생시 미상·추정)" if unknown_time else "")),
        sections=secs,
    )


def _split_paragraphs(text: str) -> list[str]:
    """빈 줄(연속 개행) 기준 문단 분할 — 문단 내부 단일 개행은 보존(pre-line)."""
    if not text:
        return []
    return [p.strip("\n") for p in re.split(r"\n\s*\n+", text) if p.strip()]


def render_pdf(
    report,
    saju,
    out_name: str = "saju_report.pdf",
    age: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
) -> str:
    os.makedirs(_OUT, exist_ok=True)
    html = render_html(report, saju, age=age, name=name, unknown_time=unknown_time)
    html_path = os.path.join(_OUT, out_name.replace(".pdf", ".html"))
    pdf_path = os.path.join(_OUT, out_name)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # display_header_footer 미사용: Chromium 머리말/꼬리말은 미태깅 콘텐츠라
    # PDF/UA-1 7.1-3(콘텐츠는 태깅 또는 Artifact여야 함) 대량 위반 원인.
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto("file:///" + html_path.replace("\\", "/"))
        pg.emulate_media(media="print")
        # pdf()는 screenshot과 달리 웹폰트 로딩을 기다리지 않는다 — 대용량 폰트
        # (Source Han Serif 24MB)가 콜드 캐시일 때 본문 글리프가 통째로 빠지는
        # 레이스 실측(2026-06-12, text_chars 13467→606). 명시 대기 필수.
        pg.evaluate("document.fonts.ready")
        pg.pdf(
            path=pdf_path,
            format="A4",
            tagged=True,
            outline=True,
            print_background=True,
            prefer_css_page_size=True,
            margin=_PAGE_MARGIN,
        )
        b.close()

    _apply_background(pdf_path)
    harden_pdf_ua(pdf_path, title="사주풀이 결과지", lang="ko-KR")
    return pdf_path


def _apply_background(pdf_path: str) -> None:
    """전 페이지 한지 배경 언더레이 — 텍스트 레이어·태그 트리 비파괴.

    overlay=False 로 기존 콘텐츠 아래에 깔고, xref 재사용으로 이미지 1회만 임베드.
    (배경 이미지는 비태깅 콘텐츠지만 veraPDF 7.1-3은 이미 잔존 clause — 목록 비악화.)
    """
    if not os.path.isfile(_BG_PATH):
        return
    doc = fitz.open(pdf_path)
    xref = 0
    for page in doc:
        xref = page.insert_image(page.rect, filename=_BG_PATH, xref=xref, overlay=False)
    doc.saveIncr()
    doc.close()


def harden_pdf_ua(pdf_path: str, *, title: str, lang: str = "ko-KR") -> None:
    """PDF/UA-1 7.1 메타데이터 보정 — XMP 스트림(pdfuaid:part=1)+제목+언어+
    DisplayDocTitle. (구조 태깅은 Chromium tagged 출력 사용; 메타데이터 결손만 보강)
    """
    doc = fitz.open(pdf_path)
    doc.set_metadata(
        {"title": title, "author": "사주풀이 생성기", "subject": "명리·자미두수 종합 풀이"}
    )
    xmp = f"""<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:pdfuaid="http://www.aiim.org/pdfua/ns/id/" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">{title}</rdf:li></rdf:Alt></dc:title>
   <dc:language><rdf:Bag><rdf:li>{lang}</rdf:li></rdf:Bag></dc:language>
   <pdfuaid:part>1</pdfuaid:part>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""
    doc.set_xml_metadata(xmp)  # Catalog /Metadata 스트림 생성 → 7.1-8 충족
    cat = doc.pdf_catalog()
    doc.xref_set_key(cat, "Lang", f"({lang})")
    doc.xref_set_key(cat, "ViewerPreferences", "<</DisplayDocTitle true>>")
    doc.xref_set_key(cat, "MarkInfo", "<</Marked true>>")
    doc.saveIncr()
    doc.close()
