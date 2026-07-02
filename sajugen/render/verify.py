# -*- coding: utf-8 -*-
"""렌더 산출 PDF 게이트 — 보고서 #1 결함(통이미지) 재발 차단.

PyMuPDF: 텍스트레이어 글자수 + 폰트 임베드 + 아웃라인 + 태그(StructTree/MarkInfo).
veraPDF: Java 설치 시 PDF/UA-1 검증, 미설치 시 PyMuPDF 게이트로 대체 + 안내.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections import Counter

import fitz

MIN_TEXT_CHARS = 1500  # 통이미지면 ~0 → 이 기준으로 결함 차단

# 렌더 후 마크다운 누출 탐지(궁합 PDF '---'·'**' 본문 인쇄 실사고 2026-06-14).
# 한국어 본문에는 등장하지 않는 강한 신호만 검사 → 오탐 0(부록 한자 병기 등은 무관).
_MD_HR_RX = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", re.M)  # 수평선 라인('---')
_MD_HEADING_RX = re.compile(r"^\s*#{1,6}\s", re.M)  # 마크다운 제목('# …')
_MD_FENCE = "```"


def markdown_artifacts(text: str) -> list[str]:
    """본문에 누출된 마크다운 흔적(수평선/굵게/제목/코드펜스). 빈 리스트면 정상."""
    hits: list[str] = []
    hits += [m.group(0).strip() for m in _MD_HR_RX.finditer(text)]
    if "**" in text:
        hits.append("**")
    hits += [m.group(0).strip() or "#" for m in _MD_HEADING_RX.finditer(text)]
    if _MD_FENCE in text:
        hits.append(_MD_FENCE)
    return hits


# orphan(widow) page 검출 — 섹션 말미 짧은 문장이 단독 페이지로 넘어간 경우('있습니다.' p25).
_ORPHAN_MIN = 40  # 본문 페이지 최소 글자수(이하 & 예외 아니면 orphan 후보)
_ORPHAN_SKIP = ("목차", "용어 풀이", "글을 맺으며")
_CHAPTER_RX = re.compile(r"제\s*\d+\s*장")


def _orphan_pages(pages_text: list[str]) -> list[dict]:
    """본문이 비정상적으로 짧은 단독 페이지 검출. 표지/마지막/목차/부록/맺음/장구분 제외."""
    n = len(pages_text)
    out: list[dict] = []
    for i, t in enumerate(pages_text):
        s = t.strip()
        if i == 0 or i == n - 1:  # 표지·마지막(맺음/판권) 제외
            continue
        if len(s) >= _ORPHAN_MIN:
            continue
        if _CHAPTER_RX.search(s) or any(k in s for k in _ORPHAN_SKIP):
            continue
        out.append({"page": i + 1, "chars": len(s), "text": s[:30]})
    return out


# H1.5 본문/부록 구역 분리 — 용어 풀이 부록은 전문용어 허용 구역.
_APPENDIX_MARK = "본문에 나온"  # 용어 풀이(부록) 도입부 고유 문구
_LOW_DENSITY_MIN = 120  # 본문 페이지 글자수 이 미만이면 저밀도 후보(보고)


def _split_body_appendix(pages_text: list[str]) -> tuple[str, str]:
    """(본문구역 텍스트, 부록구역 텍스트). 용어 풀이 부록 이전/이후로 분리(없으면 전부 본문)."""
    idx = next((i for i, t in enumerate(pages_text) if _APPENDIX_MARK in t), None)
    if idx is None:
        return "".join(pages_text), ""
    return "".join(pages_text[:idx]), "".join(pages_text[idx:])


# H1.5.3 이름/일간 게이트용 — 고객 본문 챕터 페이지만 스캔(표지·목차·용어풀이 부록 제외).
# 중요: '오행/십성/명식/사주팔자' 같은 단어가 있다는 이유로 페이지를 제외하지 않는다
# (본문 산문에 정상 등장 → 제외하면 lint 무력화). 명식표/근거표는 챕터에 임베드되어
# 별도 표 페이지가 없으므로 표 마커 제외는 적용 대상 없음(구조적 마커 조합만 허용 정책).
def _customer_body_pages(pages_text: list[str]) -> tuple[str, str]:
    """(고객 본문 산문 텍스트, 제외 영역 텍스트=표지·목차·부록). 페이지 단위 분리."""
    body_items = _customer_body_page_items(pages_text)
    body_pages = {page for page, _ in body_items}
    body, allowed = [], []
    for i, t in enumerate(pages_text, start=1):
        (body if i in body_pages else allowed).append(t)
    return "".join(body), "".join(allowed)


def _customer_body_page_items(pages_text: list[str]) -> list[tuple[int, str]]:
    """고객 본문 산문 페이지 목록. 표지·목차·용어풀이 부록은 제외."""
    app_idx = next((i for i, t in enumerate(pages_text) if _APPENDIX_MARK in t), len(pages_text))
    body: list[tuple[int, str]] = []
    for i, t in enumerate(pages_text):
        is_cover = i == 0
        is_toc = "목차" in t and len(t.strip()) < 400
        is_appendix = i >= app_idx
        if not (is_cover or is_toc or is_appendix):
            body.append((i + 1, t))
    return body


def _paged_lint_hits(
    page_items: list[tuple[int, str]],
    lint_func,
    *,
    limit: int = 50,
) -> list[dict]:
    """Run an aggregated lint per page and add page without leaking source text."""

    out: list[dict] = []
    for page, page_text in page_items:
        for hit in lint_func(page_text):
            safe = {
                k: v
                for k, v in hit.items()
                if k
                in {"type", "rule", "count", "severity", "allowed", "role", "expected", "actual"}
            }
            safe["page"] = page
            out.append(safe)
    return out[:limit]


_STYLE_RULES = {
    "규칙 누설": "instruction_meta_leak",
    "호칭 선언": "address_meta_declaration",
    "em dash": "ai_signature_punctuation",
    "가운뎃점": "ai_signature_punctuation",
    "기호 난발": "symbol_overuse",
    "과한 비유": "poetic_overreach",
    "시기·나이 가정어": "uncertain_timing_wording",
    "AI틱 반복 표현": "ai_like_repetition",
    "반복 남발": "excessive_repetition",
}


def _style_rule_id(why: str) -> str:
    for marker, rule in _STYLE_RULES.items():
        if marker in why:
            return rule
    return "style_lint"


def _semantic_style_hits(page_items: list[tuple[int, str]]) -> list[dict]:
    """style_lint hits grouped by rule/page. Raw matched text is not returned."""

    from ..content import style_lint

    counts: Counter[tuple[int, str]] = Counter()
    for page, page_text in page_items:
        for hit in style_lint.lint(page_text):
            counts[(page, _style_rule_id(str(hit.get("why", ""))))] += 1
    return [
        {"type": "semantic_style", "rule": rule, "page": page, "count": count}
        for (page, rule), count in sorted(counts.items())
    ][:50]


def _placeholder_residue_hits_clean(hits: list[dict], product: str | None = None) -> bool:
    # Phase 1 hard gate: definite masking/placeholder residue fails everywhere.
    # Candidate hits such as "두 분께" are exposed for product-aware follow-up without
    # failing relationship/gunghap documents by default.
    return not any(h.get("severity") == "hard" for h in hits)


def _low_density_pages(pages_text: list[str]) -> list[dict]:
    """본문 글자수 <120 저밀도 페이지(보고). 표지/목차/부록/맺음/마지막 제외, 장 시작은 포함."""
    n = len(pages_text)
    out: list[dict] = []
    for i, t in enumerate(pages_text):
        s = t.strip()
        if i == 0 or i == n - 1:
            continue
        if len(s) >= _LOW_DENSITY_MIN:
            continue
        if any(k in s for k in ("목차", "용어 풀이", _APPENDIX_MARK, "글을 맺으며")):
            continue
        out.append({"page": i + 1, "chars": len(s), "text": s[:40]})
    return out


# 레이아웃 기하 게이트(2026-07-02) — 텍스트/글자수 게이트가 못 잡는 시각 결함을 검출.
# 근본원인: verify 가 텍스트/카운트/시맨틱만 검사해 좌우 비대칭·넘침 같은 기하 결함이
# gate_pass=true 로 반복 통과했다. PyMuPDF 텍스트 블록 bbox 로 판정 — 픽셀 diff 는 폰트/AA
# 차이에 취약하므로 결정론적 bbox 기하를 쓴다. 검출: (a) 좌우 여백 비대칭(칼럼 쏠림),
# (b) 콘텐츠박스 밖 넘침. 표지·목차·부록·짧은/장식 페이지는 스코프 제외(오탐 방지).
_PT_PER_MM = 72.0 / 25.4
_PAGE_LR_MARGIN_MM = 20.0  # @page left/right (pdf._PAGE_MARGIN 과 동기 — 변경 시 함께 갱신)
_MARGIN_ASYMMETRY_MM = (
    10.0  # 좌우 여백 차 관용치(= 칼럼중심 5mm 오프셋). 중앙정렬≈0=통과, 쏠림 버그(≈22mm)=탐지
)
_OVERFLOW_EPS_MM = 3.0  # 콘텐츠박스 경계 넘침 허용 epsilon
_GEOM_MIN_BLOCKS = 6  # 본문형 페이지 최소 텍스트 블록(표지/짧은/장식 페이지 오탐 제외)


def _capture_page_geometry(doc) -> tuple[list, list]:
    """페이지별 텍스트 블록 bbox·페이지 폭을 doc.close() 전에 캡처.

    블록/rect 미지원 문서(테스트 fake doc)면 빈 리스트를 돌려 기하 게이트를 skip 한다
    (실 렌더 PDF 는 항상 지원 → 기하 검사 적용)."""
    try:
        blocks: list[list[tuple]] = []
        rects: list[tuple] = []
        for i in range(doc.page_count):
            pg = doc.load_page(i)
            bl = [
                b[:4]
                for b in pg.get_text("blocks")
                if len(b) > 6 and b[6] == 0 and (b[4] or "").strip()
            ]
            blocks.append(bl)
            rects.append((pg.rect.width, pg.rect.height))
        return blocks, rects
    except (TypeError, AttributeError):
        return [], []


def _layout_geometry_hits(
    pages_text: list[str],
    pages_blocks: list,
    page_rects: list,
) -> list[dict]:
    """고객 본문 페이지의 좌우 여백 대칭·콘텐츠 넘침을 텍스트 블록 bbox 로 검사(PII-free).

    반환 hit = {page, kind: 'margin_asymmetry'|'content_overflow', left_mm, right_mm} — 본문 텍스트 미포함."""
    if not pages_blocks or not page_rects:
        return []
    body_pages = {p for p, _ in _customer_body_page_items(pages_text)}
    hits: list[dict] = []
    for page in sorted(body_pages):
        idx = page - 1
        if idx >= len(pages_blocks) or idx >= len(page_rects):
            continue
        blocks = pages_blocks[idx]
        if len(blocks) < _GEOM_MIN_BLOCKS:
            continue  # 장식/짧은 페이지 제외
        width = page_rects[idx][0]
        x0 = min(b[0] for b in blocks)  # 최좌(칼럼 좌단 — 좌정렬이라 신뢰도 높음)
        x1 = max(b[2] for b in blocks)  # 최우(가장 넓은 줄)
        left_mm = x0 / _PT_PER_MM
        right_mm = (width - x1) / _PT_PER_MM
        content_left_mm = _PAGE_LR_MARGIN_MM
        content_right_edge_mm = width / _PT_PER_MM - _PAGE_LR_MARGIN_MM
        if abs(left_mm - right_mm) > _MARGIN_ASYMMETRY_MM:
            hits.append(
                {
                    "page": page,
                    "kind": "margin_asymmetry",
                    "left_mm": round(left_mm, 1),
                    "right_mm": round(right_mm, 1),
                }
            )
        if (
            left_mm < content_left_mm - _OVERFLOW_EPS_MM
            or (x1 / _PT_PER_MM) > content_right_edge_mm + _OVERFLOW_EPS_MM
        ):
            hits.append(
                {
                    "page": page,
                    "kind": "content_overflow",
                    "left_mm": round(left_mm, 1),
                    "right_mm": round(right_mm, 1),
                }
            )
    return hits


# 포터블 toolchain (시스템 미오염, 무관리자)
_TOOLS = os.path.join(os.path.dirname(__file__), "..", "tools")
_JAVA = os.path.abspath(os.path.join(_TOOLS, "jdk-21.0.11+10-jre", "bin", "java.exe"))
_VERA_BASE = os.path.abspath(os.path.join(_TOOLS, "verapdf"))


def _verapdf_ua1(pdf_path: str) -> dict:
    """포터블 veraPDF로 PDF/UA-1 검증 → {compliant, failed_clauses, available}."""
    if not (os.path.isfile(_JAVA) and os.path.isdir(_VERA_BASE)):
        if shutil.which("verapdf"):  # 시스템 설치 폴백
            base = None
        else:
            return {"available": False, "note": "veraPDF 미설치 — sajugen/tools 포터블 설치 필요"}
    cp = f"{_VERA_BASE}{os.sep}etc;{_VERA_BASE}{os.sep}bin{os.sep}*"
    try:
        out = subprocess.run(
            [
                _JAVA,
                "-classpath",
                cp,
                "-XX:+IgnoreUnrecognizedVMOptions",
                "--add-exports=java.base/sun.security.pkcs=ALL-UNNAMED",
                "org.verapdf.apps.GreenfieldCliWrapper",
                "-f",
                "ua1",
                "--format",
                "mrr",
                pdf_path,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",  # veraPDF MRR XML = UTF-8 (Windows cp949 디코드 오류 차단)
            errors="replace",  # 잔여 바이트 방어 — 측정값이라 손실 무해
            timeout=180,
        )
        xml = out.stdout
        compliant = 'isCompliant="true"' in xml
        clauses = sorted(
            set(re.findall(r'clause="([^"]+)" testNumber="(\d+)" status="failed"', xml))
        )
        return {
            "available": True,
            "compliant": compliant,
            "failed_clauses": [f"{c}-{t}" for c, t in clauses],
        }
    except Exception as e:
        return {"available": False, "note": f"verapdf 실행 오류:{type(e).__name__}"}


def verify(
    pdf_path: str,
    ref_year: int | None = None,
    names: list[str] | None = None,
    name_full: list[str] | None = None,
    identity: tuple | None = None,
    singang: list[dict] | None = None,
    product: str | None = None,
    premium: bool = False,
    concern: str | None = None,
    expected_context_terms: list[str] | None = None,
    ref_date: str | None = None,
    role_perspective: list[dict] | None = None,
    honorific: list[dict] | None = None,
) -> dict:
    """렌더 PDF 게이트. name_full(전체 이름 리스트)·identity((expected_gans, expected_terms,
    subject_specs))·singang([{full,given,honor,singang}]) 가 주어지면 H1.5.3/3.2 이름 호칭·일간
    role·신강약 group/role 게이트를 본문에 추가 적용한다.
    미전달이면 해당 게이트는 skip(clean True 기본 — 기존 호출·테스트 back-compat)."""
    doc = fitz.open(pdf_path)
    pages_text = [doc.load_page(i).get_text() for i in range(doc.page_count)]
    # 레이아웃 기하 게이트용 — 텍스트 블록 bbox·페이지 폭을 close 전에 캡처(2026-07-02).
    pages_blocks, page_rects = _capture_page_geometry(doc)
    text = "".join(pages_text).strip()
    fonts = []
    for i in range(min(doc.page_count, 3)):
        fonts += doc.load_page(i).get_fonts(full=True)
    embedded = any(f[3] for f in fonts)  # f[3]=embedded fontname
    toc = doc.get_toc()
    cat = doc.xref_object(doc.pdf_catalog())
    tagged = ("/StructTreeRoot" in cat) or ("/MarkInfo" in cat)

    r = {
        "pages": doc.page_count,
        "text_chars": len(text),
        "text_layer_ok": len(text) >= MIN_TEXT_CHARS,
        "fonts_embedded": embedded,
        "outline_items": len(toc),
        "tagged": tagged,
        # 풀이 재설계(2026-06-12)로 본문 간지 표기 = 한글 전용 — 한자/한글 모두 인정
        "contains_known_ganzhi": any(t in text for t in ("己卯", "戊午", "기묘", "무오")),
    }
    md_hits = markdown_artifacts(text)
    r["markdown_hits"] = md_hits[:20]
    r["markdown_clean"] = not md_hits
    # 교차챕터 대운 일관성(자기완결 게이트): 최종 PDF에서 '현재 대운'으로 서술된 간지가
    # 2종 이상이면 모순 → 빌드 실패(정미/병오 혼서 실사고 2026-06-14). 기대값 없이 구조만 검사.
    from ..content import consistency  # 지연 임포트(render→content 단방향, 순환 없음)

    framed = sorted(consistency.current_framed(text))
    r["daewoon_current"] = framed
    r["daewoon_consistent"] = len(framed) <= 1
    # orphan(widow) 페이지 검출(이슈1)
    r["orphan_pages"] = _orphan_pages(pages_text)
    r["no_orphan"] = not r["orphan_pages"]
    doc.close()

    # 문장 품질·시제 스캔(이슈4·5·6) — 최종 PDF 고객 본문 기준 known-bad 검출
    from ..content import quality_lint, temporal_lint

    cust_body, allowed_region = _customer_body_pages(pages_text)
    qh = quality_lint.lint(cust_body, names)
    th = temporal_lint.lint(cust_body, ref_year, ref_date=ref_date)
    r["quality_hits"] = qh[:20]
    r["quality_clean"] = not qh
    r["temporal_hits"] = th[:20]
    r["temporal_clean"] = not th

    # 고객 본문 톤(H1.5) — 본문구역만 검사(용어풀이 부록은 허용 → allowed_section_hits 보고).
    from ..content import client_tone_lint as _ct

    body, appendix = _split_body_appendix(pages_text)
    loan = _ct.loanword_lint(body)
    head = _ct.raw_calc_headwords(body)
    r["loanword_hits"] = loan[:30]
    r["loanword_clean"] = not loan  # 게이트
    r["raw_calc_phrase_hits"] = _ct.raw_calc_lint(body)[:30]  # 표제형+카운트(보고)
    r["raw_calc_head_clean"] = not head  # 표제형은 게이트
    r["client_tone_hits"] = _ct.term_hits(body)[:50]  # 전문용어 밀도(보고만)
    r["punctuation_hits"] = re.findall(r",\s*,|,\s*\.|\.\s*\.", body)[
        :30
    ]  # 보고(postprocess 후 0 기대)
    r["low_density_pages"] = _low_density_pages(pages_text)  # 보고만
    r["allowed_section_hits"] = [
        h["match"] for h in (_ct.loanword_lint(appendix) + _ct.raw_calc_lint(appendix))
    ][:30]

    # 이름 호칭 정책 + 일간 role(H1.5.3) — 고객 본문 챕터 페이지만 게이트(표지·목차·부록 제외).
    body_page_items = _customer_body_page_items(pages_text)
    from ..content import customer_meta_lint

    semantic_style_hits = _semantic_style_hits(body_page_items)
    ai_meta_hits = _paged_lint_hits(body_page_items, customer_meta_lint.lint)
    placeholder_hits = _paged_lint_hits(body_page_items, _ct.placeholder_residue_lint)
    r["semantic_style_hits"] = semantic_style_hits
    r["semantic_style_hits_count"] = sum(int(h.get("count", 1)) for h in semantic_style_hits)
    r["style_clean"] = not semantic_style_hits
    r["ai_meta_hits"] = ai_meta_hits
    r["ai_meta_hits_count"] = sum(int(h.get("count", 1)) for h in ai_meta_hits)
    r["customer_meta_clean"] = not ai_meta_hits
    r["placeholder_residue_hits"] = placeholder_hits
    r["placeholder_residue_hits_count"] = sum(int(h.get("count", 1)) for h in placeholder_hits)
    r["placeholder_residue_clean"] = _placeholder_residue_hits_clean(
        placeholder_hits, product=product
    )
    r["role_perspective_hits"] = []
    r["role_perspective_hits_count"] = 0
    role_hits = _paged_lint_hits(
        body_page_items,
        lambda page_text: _ct.role_perspective_lint(page_text, role_perspective or []),
    )
    honorific_hits = _paged_lint_hits(
        body_page_items,
        lambda page_text: _ct.honorific_consistency_lint(
            page_text, honorific or role_perspective or []
        ),
    )
    r["role_perspective_hits"] = role_hits
    r["role_perspective_hits_count"] = sum(int(h.get("count", 1)) for h in role_hits)
    r["role_perspective_clean"] = not role_hits
    r["honorific_consistency_hits"] = honorific_hits
    r["honorific_consistency_hits_count"] = sum(int(h.get("count", 1)) for h in honorific_hits)
    r["honorific_consistency_clean"] = not honorific_hits
    r["name_policy_clean"] = True
    r["identity_role_clean"] = True
    r["name_policy_hits"] = []
    r["name_policy_allowed_hits"] = []
    r["identity_role_hits"] = []
    if name_full:
        nph = _ct.name_policy_lint(cust_body, name_full)
        r["name_policy_hits"] = nph[:30]
        r["name_policy_clean"] = not nph  # 게이트
        # 제외 영역(표지·목차·부록)의 전체 이름은 허용 — 보고만(가운뎃점 나열 등)
        r["name_policy_allowed_hits"] = [f for f in name_full if f and f in allowed_region][:30]
    if identity:
        irh = _ct.identity_role_lint(cust_body, identity[0], identity[1], identity[2])
        r["identity_role_hits"] = irh[:30]
        r["identity_role_clean"] = not irh  # 게이트
    # 신강약 group/role(H1.5.3.2) — 본문만, spec 있을 때만 게이트
    r["singang_role_clean"] = True
    r["singang_role_hits"] = []
    if singang:
        srh = _ct.singang_role_lint(cust_body, singang)
        r["singang_role_hits"] = srh[:30]
        r["singang_role_clean"] = not srh  # 게이트

    from ..content import delivery_quality

    dq = delivery_quality.analyze(
        text,
        pages=r["pages"],
        low_density_pages=r["low_density_pages"],
        product=product,
        premium=premium,
        concern=concern,
        expected_context_terms=expected_context_terms,
        # integrated_full·궁합 계열은 고객 질문 필수 → concern 부재 시 조용히 통과 금지(P1).
        context_required=delivery_quality.context_required_for(product),
        # 물리 페이지 기준 초반 답변 보조지표(P5, 보고용 warning) — 표지/목차가 물리 p1~p3을
        # 차지해 초반 답변이 없을 때를 드러낸다(게이트 미변경).
        page_texts=pages_text,
    )
    r["delivery_quality"] = dq
    r["delivery_quality_clean"] = dq["clean"]
    r["delivery_missing_axes"] = dq["missing_axes"]
    r["delivery_repetition_hits"] = dq["repetition_hits"][:20]
    r["delivery_guarantee_hits"] = dq["guarantee_hits"][:20]

    # 레이아웃 기하 게이트(2026-07-02) — 좌우 여백 비대칭·콘텐츠 넘침(텍스트 게이트가 못 잡는 시각 결함).
    geom_hits = _layout_geometry_hits(pages_text, pages_blocks, page_rects)
    r["layout_geometry_hits"] = geom_hits[:20]
    r["layout_geometry_hits_count"] = len(geom_hits)
    r["layout_geometry_clean"] = not geom_hits

    # PDF/UA-1 검증 활성화(포터블 veraPDF). 결과는 '측정·보고'.
    va = _verapdf_ua1(pdf_path)
    r["verapdf"] = va
    r["verapdf_compliant"] = va.get("compliant") if va.get("available") else None

    # 하드 게이트(빌드 차단 기준): 검증된 구조 요건. veraPDF PDF/UA-1 완전 준수는
    # 별도 추적(Chromium 엔진 한계로 7.1-3 잔존 — WeasyPrint pdf/ua-1 경로 필요).
    r["gate_pass"] = bool(
        r["text_layer_ok"]
        and r["fonts_embedded"]
        and r["tagged"]
        and r["markdown_clean"]
        and r["daewoon_consistent"]
        and r["quality_clean"]
        and r["temporal_clean"]
        and r["no_orphan"]
        and r["loanword_clean"]  # 외래어 hard-ban(고객 본문)
        and r["raw_calc_head_clean"]  # 표제형 계산표현(오행 분포·십성축·신강약)
        and r["customer_meta_clean"]  # AI/meta/document self-reference residue
        and r["placeholder_residue_clean"]  # placeholder/masking residue
        and r["style_clean"]  # compose 외 경로까지 style_lint 보편 적용
        and r["role_perspective_clean"]  # integrated_full receiver perspective
        and r["honorific_consistency_clean"]  # integrated_full honorific consistency
        and r["name_policy_clean"]  # 전체 이름 반복(H1.5.3, name_full 전달 시)
        and r["identity_role_clean"]  # 일간 role 오서술(H1.5.3, identity 전달 시)
        and r["singang_role_clean"]  # 신강약 group/role(H1.5.3.2, singang 전달 시)
        and r["delivery_quality_clean"]
        and r["layout_geometry_clean"]  # 레이아웃 기하(좌우 여백·넘침) — 시각 결함 반복 차단
    )
    return r
