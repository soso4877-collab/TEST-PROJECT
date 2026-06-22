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
    brand: dict | None = None,
) -> str:
    # 도판 전면 제거(운영자 지시 — 목차+글만). 챕터·번호·차트 변수 미전달.
    # 본문은 빈 줄 기준 문단 분할 → 템플릿 <p> 렌더(단문 호흡 보존 + tagged 구조 개선).
    # brand = config.brand() 프로필(다계정 — 표지 표제·세로 박스 가변).
    b = brand or {}
    secs = [
        {"id": s.id, "title": s.title, "paragraphs": _split_paragraphs(s.final_text)}
        for s in report.sections
    ]
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(
        title="사주풀이 결과지",
        font_dir=_FONT_DIR,
        page_margin_css=_PAGE_MARGIN_CSS,
        brand_title=b.get("cover_title", "종합 사주 풀이"),
        brand_seal=b.get("seal", "사주명리"),
        cover_name=(f"{name} 님" if name else ""),
        cover_sub=(f"{saju.input_civil}" + ("  (생시 미상·추정)" if unknown_time else "")),
        sections=secs,
    )


_ORPHAN_TAIL_MAX = 14  # 이하 길이의 '마지막 단락'은 직전 단락에 합쳐 단독 페이지화 방지


def _split_paragraphs(text: str) -> list[str]:
    """빈 줄(연속 개행) 기준 문단 분할 — 문단 내부 단일 개행은 보존(pre-line).

    짧은 마지막 단락(예: '있습니다.')이 통째로 다음 페이지에 단독으로 떨어지는 orphan
    (블록 단위라 widows/orphans CSS로는 못 막음)을 막기 위해 직전 단락에 합친다.
    """
    if not text:
        return []
    paras = [p.strip("\n") for p in re.split(r"\n\s*\n+", text) if p.strip()]
    if len(paras) >= 2 and len(paras[-1].strip()) <= _ORPHAN_TAIL_MAX:
        paras[-2] = paras[-2].rstrip() + " " + paras[-1].strip()
        paras.pop()
    return paras


def render_pdf(
    report,
    saju,
    out_name: str = "saju_report.pdf",
    age: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
    brand: dict | None = None,
) -> str:
    os.makedirs(_OUT, exist_ok=True)
    html = render_html(report, saju, age=age, name=name, unknown_time=unknown_time, brand=brand)
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

    _apply_background(pdf_path, seal_text=(brand or {}).get("seal", "사주명리"))
    harden_pdf_ua(pdf_path, title="사주풀이 결과지", lang="ko-KR")
    return pdf_path


# 낙관 — 브랜드별 투명 PNG(assets/make_assets.build_seal)로 삽입.
# PyMuPDF insert_text 텍스트 임베드는 일부 뷰어에서 글리프 깨짐(운영자 실증
# 2026-06-12) — PDF에 텍스트를 써넣는 건 Chromium 경로만 신뢰, PyMuPDF는
# 벡터(광곽 선)·이미지(낙관·한지)만 그린다.
_GWAK = (0.42, 0.365, 0.286)  # 광곽 먹갈색(#6b5d49)
_MM = 72.0 / 25.4  # 1mm in pt
_SEAL_W_PT = 32.0  # 낙관 배치 폭(pt) — 높이는 PNG 비율 따름


def _draw_gwakgwak(page) -> None:
    """사주쌍변 광곽(匡廓) — 전통 한적 판식의 이중 테두리(굵은 외선+가는 내선).

    본문 마진(22/20mm) 바깥, 페이지 가장자리 11/13mm 인셋. 한지 위·본문 아래.
    """
    r = page.rect
    o, i = 11 * _MM, 13 * _MM
    page.draw_rect(
        fitz.Rect(o, o, r.width - o, r.height - o), color=_GWAK, width=0.9, overlay=False
    )
    page.draw_rect(
        fitz.Rect(i, i, r.width - i, r.height - i), color=_GWAK, width=0.35, overlay=False
    )


def _apply_background(pdf_path: str, seal_text: str = "사주명리") -> None:
    """전 페이지 언더레이: 낙관 PNG(브랜드 가변) + 광곽 + 한지 배경.

    PyMuPDF overlay=False 는 콘텐츠 스트림 '맨 앞'에 prepend — 나중에 넣은 것이
    가장 아래 깔린다. 낙관·광곽을 먼저, 한지 이미지를 마지막에 삽입.
    이미지(낙관·한지)는 xref 재사용으로 각 1회만 임베드. 텍스트 임베드 없음
    (PyMuPDF insert_text 글리프 깨짐 실증 — 낙관은 build_seal PNG).
    """
    if not os.path.isfile(_BG_PATH):
        return
    from .assets.make_assets import build_seal

    try:
        seal_path = build_seal(seal_text)
    except Exception:
        seal_path = None  # 낙관 생성 실패 시 배경·광곽만(기능 우선)
    doc = fitz.open(pdf_path)
    bg_xref = 0
    seal_xref = 0
    seal_rect = None
    if seal_path and os.path.isfile(seal_path):
        pix = fitz.Pixmap(seal_path)
        h_pt = _SEAL_W_PT * pix.height / pix.width
        pix = None
        r0 = doc[0].rect
        x1 = r0.width - 15.5 * _MM  # 광곽 내선(13mm) 안쪽
        y1 = r0.height - 16 * _MM
        seal_rect = fitz.Rect(x1 - _SEAL_W_PT, y1 - h_pt, x1, y1)
    for page in doc:
        if seal_rect is not None:
            seal_xref = page.insert_image(
                seal_rect, filename=seal_path, xref=seal_xref, overlay=False
            )
        _draw_gwakgwak(page)
        # 한지를 '마지막에' 삽입 = 최하층(prepend 규칙)
        bg_xref = page.insert_image(page.rect, filename=_BG_PATH, xref=bg_xref, overlay=False)
    doc.saveIncr()  # 본문 폰트 바이트 원본 보존
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
