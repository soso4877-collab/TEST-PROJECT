# -*- coding: utf-8 -*-
"""Report23 → Jinja2 HTML → Playwright Chromium tagged PDF.

#1 결함(통이미지) 해결: 선택·검색 가능한 텍스트 레이어 + 폰트 임베드 + 태그/아웃라인.
@page CSS + Chromium 네이티브 페이지네이션. 폰트는 번들 OFL(나눔명조 본문,
한자 폴백 Source Han Serif K)만 서브셋 임베드 — 시스템 폰트 의존 금지.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import fitz
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from ..content import unknown_time_policy
from . import charts
from . import layout

_DIR = os.path.dirname(__file__)
_OUT = os.path.join(_DIR, "out")
# 번들 폰트(SIL OFL) 디렉터리 → @font-face file:/// 절대경로. Chromium 이
# PDF 생성 시 사용 글리프만 서브셋 임베드(PDF/UA 7.1-3 개선·결정론).
_FONT_DIR = "file:///" + os.path.join(_DIR, "fonts").replace("\\", "/")
# 페이지 마진·본문폭 단일 소스(render/layout.py) — @page CSS(Jinja 주입)·pg.pdf margin·
# verify 기하 게이트가 같은 상수를 쓴다(render.md: 반드시 동기화).
_PAGE_MARGIN = {k: f"{v:g}mm" for k, v in layout.PAGE_MARGIN_MM.items()}
_BODY_MAXW_MM = layout.BODY_MAXW_MM
# 목차 단일 열 최대 행수(실측 14행/페이지, 2026-07-03). 초과 시 2단 목차로 전환(T3.5a).
_TOC_SINGLE_COL_MAX = 14
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
    "summary": (1, "전체 흐름", "내 사주의 전체 윤곽과 핵심 단서"),
    "love": (2, "영역별 흐름", "관계·일·재물에서 힘이 실리는 결"),
    "daewoon": (3, "시간의 결", "대운과 가까운 시기의 흐름"),
    "ziwei_summary": (4, "구조와 적용", "자미두수 명반과 현실 적용"),
    "appendix_terms": (5, "부록", "용어 풀이와 다음 걸음"),
}

_env = Environment(
    loader=FileSystemLoader(os.path.join(_DIR, "templates")),
    autoescape=select_autoescape(["html", "j2"]),
)


def _require_brand(brand: dict | None) -> dict:
    if not isinstance(brand, dict) or not brand:
        raise ValueError("render brand is required")
    missing = [k for k in ("cover_title", "seal", "closing_sign") if not brand.get(k)]
    if missing:
        raise ValueError(f"render brand missing keys: {', '.join(missing)}")
    return brand


# 표지(front-matter) 표시 문자열만 렌더 직전 semantic-clean 처리.
# style_lint 가 ai_signature_punctuation 으로 잡는 가운뎃점('·')·em/en dash('—'·'–')가
# page 1 표지에 남지 않게 한다. 원인: integrated/gunghap 의 input_civil=" · ".join(names)
# 과 생시 미상 고지("생시 미상·추정")가 cover_sub 로 그대로 출력돼 full-PDF semantic 이
# 실패하던 것(2026-06-30). 본문은 대상 아님 — builder/gunghap 후처리 경로가 따로 통제하고,
# 여기서는 표지 표시 문자열만 정규화한다. 날짜 하이픈('-' U+002D)은 대상이 아니라 보존된다.
_COVER_PUNCT_RX = re.compile(r"\s*[·—–]\s*")


def _clean_cover_text(text: str | None) -> str:
    if not text:
        return text or ""
    text = _COVER_PUNCT_RX.sub(", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def render_html(
    report,
    saju,
    name: str | None = None,
    unknown_time: bool = False,
    *,
    birth_time_mode: str,
    three_pillar_provenance: object | None = None,
    brand: dict | None = None,
    chapter_breaks: bool = True,
    body_font_size: str = "14.5pt",
    body_line_height: str = "1.8",
) -> str:
    if birth_time_mode is None:
        raise ValueError("birth_time_mode is required at render boundary")
    report_provenance = getattr(report, "three_pillar_provenance", None)
    birth_time_mode = unknown_time_policy.normalize_mode(
        birth_time_mode,
        unknown_time=unknown_time,
    )
    three_pillar = birth_time_mode == unknown_time_policy.THREE_PILLAR_MODE
    provenance = (
        three_pillar_provenance
        if three_pillar_provenance is not None
        else report_provenance
    )
    unknown_time_policy.assert_unknown_time_provenance_clean(
        report.sections,
        birth_time_mode=birth_time_mode,
        provenance=provenance,
        source="render_html",
    )
    # known-time 도판 정책은 그대로 유지한다. 삼주만 확정된 문서는 고객이 빠진 자리를
    # 오해하지 않도록 원국 장에 연·월·일 3열 표를 한 번 넣는다.
    # 본문은 빈 줄 기준 문단 분할 → 템플릿 <p> 렌더(단문 호흡 보존 + tagged 구조 개선).
    # brand = config.brand() 프로필(다계정 — 표지 표제·세로 박스 가변).
    brand_profile = _require_brand(brand)
    chart_anchor_index = None
    if three_pillar:
        # 정상 개인/통합 경로는 wonguk 장에 붙인다. integrated sparse 병합이 짧은
        # personal_wonguk를 앞 장에 합쳐 ID를 없앤 경우에는 첫 고객 노출 개인 장을 쓴다.
        # index를 먼저 하나만 고정해 중복 ID가 있더라도 도판은 정확히 한 번만 삽입한다.
        chart_anchor_index = next(
            (
                index
                for index, section in enumerate(report.sections)
                if str(section.id).removeprefix("personal_") == "wonguk"
            ),
            None,
        )
        if chart_anchor_index is None:
            chart_anchor_index = next(
                (
                    index
                    for index, section in enumerate(report.sections)
                    if str(section.id).startswith("personal_")
                ),
                None,
            )
        if chart_anchor_index is None:
            chart_anchor_index = next(
                (
                    index
                    for index, section in enumerate(report.sections)
                    if str(section.id) not in {"cover", "toc"}
                ),
                None,
            )

    secs = []
    for index, section in enumerate(report.sections):
        chart_svg = ""
        if index == chart_anchor_index:
            chart_svg = charts.three_pillar_table(saju.three_pillar)
        secs.append(
            {
                "id": section.id,
                "title": section.title,
                "paragraphs": _split_paragraphs(section.final_text),
                "chart_svg": chart_svg,
            }
        )
    # 목차 재넘침 방어(T3.5a): 목차 행(표지·목차 제외)이 단일 열 용량(_TOC_SINGLE_COL_MAX,
    # 실측 14행/페이지)을 넘으면 2단 목차로 전환해 1페이지 유지(행 크기 보존, 운영자 결정).
    toc_row_count = sum(1 for s in secs if s["id"] not in ("cover", "toc"))
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(
        title="사주풀이",
        font_dir=_FONT_DIR,
        page_margin_css=_PAGE_MARGIN_CSS,
        body_maxw_mm=f"{_BODY_MAXW_MM:g}",
        toc_two_col=toc_row_count > _TOC_SINGLE_COL_MAX,
        brand_title=brand_profile["cover_title"],
        brand_seal=brand_profile["seal"],
        cover_name=_clean_cover_text(f"{name} 님") if name else "",
        cover_sub=(
            _clean_cover_text(str(saju.input_civil_date))
            + "\n"
            + unknown_time_policy.THREE_PILLAR_NOTICE
            if three_pillar
            else _clean_cover_text(f"{saju.input_civil}")
        ),
        sections=secs,
        chapter_breaks=chapter_breaks,
        body_font_size=body_font_size,
        body_line_height=body_line_height,
    )


# 이하 길이의 '마지막 단락'은 직전 단락에 합쳐 단독 페이지화 방지.
# 90 = 저밀도 게이트의 장꼬리 하한(verify._CHAPTER_TAIL_MIN)과 정합(2026-07-04):
# 독립 꼬리 단락은 4줄 미만이면 widows/orphans CSS(단락 내부 전용)가 못 막아 통째로 다음
# 페이지에 떨어져 2줄(≈50자) 스필 페이지를 만든다(실측 v4: 47자·56자 페이지 → gate FAIL).
# 90 미만 마지막 단락을 직전에 병합하면 스필은 병합 단락의 내부 분할이 되어 widows:4
# (4줄≈100자+)가 보장 → 이 결함 부류가 결정론적으로 소멸(재생성 주사위 불필요).
_ORPHAN_TAIL_MAX = 90


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
    name: str | None = None,
    unknown_time: bool = False,
    *,
    birth_time_mode: str,
    three_pillar_provenance: object | None = None,
    brand: dict | None = None,
    chapter_breaks: bool = True,
    body_font_size: str = "14.5pt",
    body_line_height: str = "1.8",
    out_dir: str | Path | None = None,
) -> str:
    brand_profile = _require_brand(brand)
    seal_text = brand_profile["seal"]
    output_dir = os.fspath(out_dir) if out_dir is not None else _OUT
    if out_dir is not None and os.path.basename(out_name) != out_name:
        raise ValueError("out_name must be a filename when out_dir is set")
    os.makedirs(output_dir, exist_ok=True)
    html = render_html(
        report,
        saju,
        name=name,
        unknown_time=unknown_time,
        birth_time_mode=birth_time_mode,
        three_pillar_provenance=three_pillar_provenance,
        brand=brand_profile,
        chapter_breaks=chapter_breaks,
        body_font_size=body_font_size,
        body_line_height=body_line_height,
    )
    html_path = os.path.join(output_dir, out_name.replace(".pdf", ".html"))
    pdf_path = os.path.join(output_dir, out_name)
    staging_fd, staging_path = tempfile.mkstemp(
        prefix=f".{os.path.splitext(os.path.basename(out_name))[0]}.",
        suffix=".pdf",
        dir=output_dir,
    )
    os.close(staging_fd)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    try:
        # display_header_footer 미사용: Chromium 머리말/꼬리말은 미태깅 콘텐츠라
        # PDF/UA-1 7.1-3(콘텐츠는 태깅 또는 Artifact여야 함) 대량 위반 원인.
        with sync_playwright() as playwright:
            browser = None
            try:
                browser = playwright.chromium.launch()
                page = browser.new_page()
                page.goto("file:///" + html_path.replace("\\", "/"))
                page.emulate_media(media="print")
                # pdf()는 screenshot과 달리 웹폰트 로딩을 기다리지 않는다 — 대용량 폰트
                # (Source Han Serif 24MB)가 콜드 캐시일 때 본문 글리프가 통째로 빠지는
                # 레이스 실측(2026-06-12, text_chars 13467→606). 명시 대기 필수.
                page.evaluate("document.fonts.ready")
                page.pdf(
                    path=staging_path,
                    format="A4",
                    tagged=True,
                    outline=True,
                    print_background=True,
                    prefer_css_page_size=True,
                    margin=_PAGE_MARGIN,
                )
            finally:
                if browser is not None:
                    browser.close()

        _apply_background(staging_path, seal_text=seal_text)
        harden_pdf_ua(staging_path, title="사주풀이", lang="ko-KR")
        os.replace(staging_path, pdf_path)
    except Exception:
        if os.path.exists(staging_path):
            os.remove(staging_path)
        raise
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


def _apply_background(pdf_path: str, seal_text: str | None = None) -> None:
    """전 페이지 언더레이: 낙관 PNG(브랜드 가변) + 광곽 + 한지 배경.

    PyMuPDF overlay=False 는 콘텐츠 스트림 '맨 앞'에 prepend — 나중에 넣은 것이
    가장 아래 깔린다. 낙관·광곽을 먼저, 한지 이미지를 마지막에 삽입.
    이미지(낙관·한지)는 xref 재사용으로 각 1회만 임베드. 텍스트 임베드 없음
    (PyMuPDF insert_text 글리프 깨짐 실증 — 낙관은 build_seal PNG).
    """
    if not seal_text:
        raise ValueError("render brand seal is required")
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
