# -*- coding: utf-8 -*-
"""Report23 → Jinja2 HTML → Playwright Chromium tagged PDF.

#1 결함(통이미지) 해결: 선택·검색 가능한 텍스트 레이어 + 폰트 임베드 + 태그/아웃라인.
Paged.js 대신 견고한 @page CSS + Chromium 네이티브 페이지네이션 + Playwright
header/footer(러닝헤더·페이지번호). 한글 폰트는 시스템(Malgun Gothic) 서브셋 임베드.
"""

from __future__ import annotations

import os

import fitz
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from . import charts

_DIR = os.path.dirname(__file__)
_OUT = os.path.join(_DIR, "out")
# 번들 폰트(SIL OFL) 디렉터리 → @font-face file:/// 절대경로. Chromium 이
# PDF 생성 시 사용 글리프만 서브셋 임베드(PDF/UA 7.1-3 개선·결정론).
_FONT_DIR = "file:///" + os.path.join(_DIR, "fonts").replace("\\", "/")
_DISCLAIMER = (
    "본 풀이는 명리학·자미두수 전통 해석 체계에 기반한 참고용 상담 자료이며, "
    "의료·법률·투자 등 중요한 결정은 전문가와 상의하시기 바랍니다."
)
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
    secs = []
    for s in report.sections:
        secs.append(
            {
                "id": s.id,
                "title": s.title,
                "final_text": s.final_text,
                "source_keys": s.source_keys,
                "chapter": _CHAPTERS.get(s.id),
            }
        )
    tmpl = _env.get_template("report.html.j2")
    return tmpl.render(
        title="사주풀이 결과지",
        font_dir=_FONT_DIR,
        cover_sub=(
            (f"{name}님\n" if name else "")
            + f"입력 {saju.input_civil}"
            + ("(생시 미상·추정)" if unknown_time else "")
            + f"\n진태양시 {saju.true_solar}\n"
            + f"경도보정 {saju.eot_minutes}분 · 자시정책 {saju.zasi_policy}"
        ),
        sections=secs,
        ohaeng_svg=charts.ohaeng_bar(saju.myeongni.elements),
        daewoon_svg=charts.daewoon_timeline(saju.myeongni.daewoon, current_age=age),
        manse_svg=charts.manse_table(saju.myeongni),
        sipseong_svg=charts.sipseong_card(saju.myeongni),
        ziwei_svg=charts.ziwei_chart(saju.ziwei),
        disclaimer=_DISCLAIMER,
    )


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
        pg.pdf(
            path=pdf_path,
            format="A4",
            tagged=True,
            outline=True,
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "16mm", "bottom": "16mm", "left": "15mm", "right": "15mm"},
        )
        b.close()

    harden_pdf_ua(pdf_path, title="사주풀이 결과지", lang="ko-KR")
    return pdf_path


def harden_pdf_ua(pdf_path: str, *, title: str, lang: str = "ko-KR") -> None:
    """PDF/UA-1 7.1 메타데이터 보정 — XMP 스트림(pdfuaid:part=1)+제목+언어+
    DisplayDocTitle. (구조 태깅은 Chromium tagged 출력 사용; 메타데이터 결손만 보강)
    """
    doc = fitz.open(pdf_path)
    doc.set_metadata(
        {"title": title, "author": "사주풀이 생성기", "subject": "명리·자미두수 참고 상담 자료"}
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
