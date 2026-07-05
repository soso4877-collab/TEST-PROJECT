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

from . import layout

MIN_TEXT_CHARS = 1500  # 통이미지면 ~0 → 이 기준으로 결함 차단

# 완성본 분량 벤치마크(보고 전용, 게이트 아님) — 근거: 같은 고객 H153 검증 업로드본 실측
# 17,396자·424자/쪽(2026-07-04). 하한은 그보다 낮게 잡아 질문 유형·챕터 드롭(자미단독 등)의
# 정상 변동을 허용: 공백 제거 글자수 16,000 + 쪽당 400자. verify()['volume'] 로 보고.
_VOLUME_BENCH_MIN_CHARS = 16_000
_VOLUME_BENCH_MIN_CPP = 400.0

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
_ORPHAN_SKIP = ("용어 풀이", "글을 맺으며")  # 목차 판정은 _is_toc_page 로 일원화(B-5)
# 목차 페이지 판정 단일 기준(T3.5/B-5) — 세 스캐너(_customer_body_page_items·_low_density·
# _orphan)가 같은 규칙을 쓴다. 기존엔 _customer_body_page_items 만 '<400자' 상한을 걸고
# 나머지는 '목차' 단어만 봐 이중 기준이었다. 단일화: '목차' 단어 + 상한 미만(본문이 '목차'를
# 언급하는 긴 페이지는 목차로 오분류하지 않음). _low_density(<120)·_orphan(<40)은 이미
# 그 이상 짧을 때만 이 검사에 도달하므로 상한 적용은 그 둘엔 동작 불변(순수 단일소스화, 완화 0).
# 상한 520: 2단 목차(T3.5a)는 22~24장이 1페이지에 모여 ~330~400자가 된다 — 400 고정 시 큰 목차가
# 본문으로 오분류될 수 있어 여유(해석 산문엔 '목차' 단어가 없어 본문 오제외 위험은 무시 가능).
_TOC_MAX_CHARS = 520


def _is_toc_page(text: str) -> bool:
    return "목차" in text and len(text.strip()) < _TOC_MAX_CHARS


# 두 자리 장(제10장~)은 .cnum letter-spacing 으로 "제 1 0 장"처럼 숫자 사이 공백이 추출된다
# (A-4). \d(?:\s*\d)* 로 자리 사이 공백을 허용 — 문서 후반 장 인식이 비게 되던 사각 복원.
_CHAPTER_RX = re.compile(r"제\s*\d(?:\s*\d)*\s*장")


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
        if _CHAPTER_RX.search(s) or _is_toc_page(s) or any(k in s for k in _ORPHAN_SKIP):
            continue
        # 본문 스니펫(text) 비포함 — hit 이 로그/hverify json 등 외부 표면으로 흐를 때
        # 고객 문장 노출 방지(T1.3/A-3, docs/16 QI 원칙). page/chars 메타만.
        out.append({"page": i + 1, "chars": len(s)})
    return out


# H1.5 본문/부록 구역 분리 — 용어 풀이 부록은 전문용어 허용 구역.
_APPENDIX_MARK = "본문에 나온"  # 용어 풀이(부록) 도입부 고유 문구
_LOW_DENSITY_MIN = 120  # 본문 페이지 글자수 이 미만이면 저밀도 후보(보고)
# 장꼬리(다음이 새 장) 면제 하한(A-2). 장 끝 정상 조판 꼬리는 최소 ~3줄(90자) 이상이라
# 본다. 이 미만이면 다음이 새 장이어도 '흘러넘침 결함'(하단 대부분 빈 페이지)으로 저밀도 hit
# 유지. _ORPHAN_MIN(40)~_LOW_DENSITY_MIN(120) 사이 장꼬리 사각을 41~89 로 좁힌다(완화 아님).
_CHAPTER_TAIL_MIN = 90


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
        is_toc = _is_toc_page(t)
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


# 다인(2인+) 상품 — 커플 지칭이 정상 표현인 문서(candidate 승격 비적용).
_MULTI_PERSON_PRODUCTS = {"gunghap", "relationship", "integrated_full"}


def _placeholder_residue_hits_clean(
    hits: list[dict],
    product: str | None = None,
    partner_present: bool | None = None,
) -> bool:
    # Phase 1 hard gate: definite masking/placeholder residue fails everywhere.
    # QI-2026-07-04(팬텀 파트너): product 가 dead parameter 여서 "두 분" 류 커플 지칭이
    # 1인 문서에서도 통과했다. 이제 '1인 상품 + 파트너 부재(partner_present is False)'가
    # 확인되면 candidate 도 hard 로 승격해 실패시킨다. partner_present=None(미상, 레거시
    # 호출)·다인 상품·파트너 명식 있는 개인 풀이는 기존 동작 유지(완화 0, 사각 축소만).
    if any(h.get("severity") == "hard" for h in hits):
        return False
    if partner_present is False and (product or "") not in _MULTI_PERSON_PRODUCTS:
        return not any(h.get("severity") == "candidate" for h in hits)
    return True


_CHAPTER_HEAD_RX = re.compile(r"^\s*제\s*\d(?:\s*\d)*\s*장")  # 두 자리 장 공백 추출 대응(A-4)


def _starts_new_chapter(page_text: str) -> bool:
    """페이지가 장 마스트헤드(제 N 장)로 시작하면 True.

    장마다 새 페이지로 시작하는 레이아웃(chapter_breaks=True)에서 긴 장의 끝이 다음
    장 직전에 몇 줄만 흘러넘칠 수 있다. 이 짧은 페이지는 '콘텐츠 부족'이 아니라 책에서
    흔한 정상 조판 꼬리다. 다음 페이지가 새 장이면 직전 짧은 페이지를 저밀도에서 제외.
    (짧은 '장 시작' 페이지·중간 콘텐츠 페이지·맺음 직전 말미 밀도는 계속 잡는다.)"""
    return bool(_CHAPTER_HEAD_RX.match(page_text or ""))


def _low_density_pages(pages_text: list[str]) -> list[dict]:
    """본문 글자수 <120 저밀도 페이지(보고). 표지/목차/부록/맺음/마지막·장꼬리 제외, 장 시작은 포함."""
    n = len(pages_text)
    out: list[dict] = []
    for i, t in enumerate(pages_text):
        s = t.strip()
        if i == 0 or i == n - 1:
            continue
        if len(s) >= _LOW_DENSITY_MIN:
            continue
        if _is_toc_page(s) or any(k in s for k in ("용어 풀이", _APPENDIX_MARK, "글을 맺으며")):
            continue
        if i + 1 < n and _starts_new_chapter(pages_text[i + 1]) and len(s) >= _CHAPTER_TAIL_MIN:
            # 다음이 새 장 + 꼬리가 정상 조판 분량(>= _CHAPTER_TAIL_MIN) → 면제(콘텐츠 부족 아님).
            # 하한 미만이면 다음이 새 장이어도 흘러넘침 결함으로 저밀도 hit 유지(A-2, 사각 축소).
            continue
        # 본문 스니펫(text) 비포함 — 외부 표면 노출 방지(T1.3/A-3). page/chars 메타만.
        out.append({"page": i + 1, "chars": len(s)})
    return out


# 레이아웃 기하 게이트(2026-07-02) — 텍스트/글자수 게이트가 못 잡는 시각 결함을 검출.
# 근본원인: verify 가 텍스트/카운트/시맨틱만 검사해 좌우 비대칭·넘침 같은 기하 결함이
# gate_pass=true 로 반복 통과했다. PyMuPDF 텍스트 블록 bbox 로 판정 — 픽셀 diff 는 폰트/AA
# 차이에 취약하므로 결정론적 bbox 기하를 쓴다. 검출: (a) 칼럼 쏠림(좌단 기대위치 이탈),
# (b) 콘텐츠박스 밖 넘침, (c) 인셋 상실, (d) 세로 넘침. 표지·목차·부록·짧은 페이지 스코프 제외.
_PT_PER_MM = 72.0 / 25.4
# 레이아웃 상수 단일 소스(render/layout.py) — pdf.py @page·본문폭과 동일 값 참조(T3.2/B-2).
_PAGE_LR_MARGIN_MM = layout.PAGE_MARGIN_MM["left"]  # @page left/right
_PAGE_TB_MARGIN_MM = layout.PAGE_MARGIN_MM["top"]  # @page top/bottom — 세로 넘침 검사
_BODY_MAXW_MM = layout.BODY_MAXW_MM  # .body max-width — 기대 칼럼폭·좌단 파생 기준
# 칼럼 쏠림 관용치: 좌단의 기대 위치((페이지폭-BODY_MAXW)/2) 이탈 허용. 정상 실측 이탈
# ≈0.2mm, 원 버그(좌 20mm) 이탈 ≈11mm → 5mm 로 넉넉히 분리. (종전 |좌-우| 비대칭 비교는
# 짧은 줄 래그드 페이지 과탐으로 2026-07-04 교체 — column_shift.)
_COLUMN_SHIFT_TOL_MM = 5.0
_OVERFLOW_EPS_MM = 3.0  # 콘텐츠박스 경계 넘침 허용 epsilon
# 본문 칼럼폭이 기대폭(BODY_MAXW_MM)보다 이만큼 넓으면 인셋 상실(max-width 무효) = 대칭 넓힘.
# column_shift 는 대칭 결함을 구조상 못 잡는다(좌단 정위치 유지) → 칼럼폭으로 검출.
# 실측: 정상 중앙정렬 칼럼폭 ≈147.5mm, 인셋 상실 시 콘텐츠박스 채움 ≈170mm → 관용치 10mm(임계 158mm)로 분리.
_BODY_INSET_TOL_MM = 10.0
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
    """고객 본문 페이지의 칼럼 위치·콘텐츠 넘침을 텍스트 블록 bbox 로 검사(PII-free).

    반환 hit kind: 'column_shift'|'content_overflow'|'body_inset_lost'|'vertical_overflow'
    — 본문 텍스트 미포함(page/mm 메타만)."""
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
        # 칼럼 쏠림(column_shift, 2026-07-04 교체): 종전 |좌-우|>10mm 비대칭 비교는 짧은 줄만
        # 있는 정상 페이지(우측 여백이 커지는 좌정렬 래그드)를 과탐했다(실전 오탐: 좌 31.2 정위치
        # 인데 우 41.5 로 FAIL). 원 결함(칼럼 이동, 좌 20mm)의 충실한 신호는 '좌단이 기대 위치
        # (페이지폭-BODY_MAXW)/2 에서 이탈'이다 — 좌/우 어느 쪽 이동도 잡고 래그드는 통과.
        # 원 버그(좌 20, 기대 31)=이탈 11mm 로 계속 FAIL(완화 아님 — 프록시 교정).
        expected_left_mm = (width / _PT_PER_MM - _BODY_MAXW_MM) / 2.0
        if abs(left_mm - expected_left_mm) > _COLUMN_SHIFT_TOL_MM:
            hits.append(
                {
                    "page": page,
                    "kind": "column_shift",
                    "left_mm": round(left_mm, 1),
                    "expected_left_mm": round(expected_left_mm, 1),
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
        # 본문 인셋(max-width) 상실 = 대칭 넓힘 — 좌우 여백은 그대로 대칭이라(예 20/20)
        # column_shift·content_overflow 모두 통과하던 사각. 기대 칼럼폭(BODY_MAXW_MM,
        # 중앙정렬)보다 관용치 이상 넓으면 인셋 상실로 검출(20mm 콘텐츠박스 고정이 아니라
        # (페이지폭-maxw)/2 파생과 정합 — pdf.py 와 단일 소스).
        # [불변식 주의] col_width = 최우(x1) - 최좌(x0) 는 '모든 본문 요소가 .body(max-width) 안'일
        # 때만 본문폭의 충실한 프록시다(실측 near20=0). 차트/디바이더를 .body 밖 풀블리드로 옮기면
        # min_left 가 떨어져 col_width 가 부풀어 false-fire 할 수 있다 — 그 변경 시 본문블록 격리 필요.
        col_width_mm = (x1 - x0) / _PT_PER_MM
        if col_width_mm > _BODY_MAXW_MM + _BODY_INSET_TOL_MM:
            hits.append(
                {
                    "page": page,
                    "kind": "body_inset_lost",
                    "width_mm": round(col_width_mm, 1),
                    "maxw_mm": round(_BODY_MAXW_MM, 1),
                }
            )
        # 세로(상하) 넘침 — 블록 y 가 @page 상/하 margin 밖(상단 잘림·하단 오버플로) (B-2/T3.2).
        # 기존엔 x(좌우)만 검사해 세로 방향 결함이 gate_pass=true 로 통과했다.
        height = page_rects[idx][1]
        y0 = min(b[1] for b in blocks)
        y1 = max(b[3] for b in blocks)
        content_bottom_edge_mm = height / _PT_PER_MM - _PAGE_TB_MARGIN_MM
        if (y0 / _PT_PER_MM) < _PAGE_TB_MARGIN_MM - _OVERFLOW_EPS_MM or (
            y1 / _PT_PER_MM
        ) > content_bottom_edge_mm + _OVERFLOW_EPS_MM:
            hits.append(
                {
                    "page": page,
                    "kind": "vertical_overflow",
                    "top_mm": round(y0 / _PT_PER_MM, 1),
                    "bottom_mm": round((height - y1) / _PT_PER_MM, 1),
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
    partner_present: bool | None = None,
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
    # tagged = StructTreeRoot AND MarkInfo (D-1/T3.4). 기존 OR 은 harden_pdf_ua 가 MarkInfo 를
    # 항상 넣어 StructTree 유실 시에도 True 로 항진하던 항등식이었다 — 구조트리 유실 회귀를 못
    # 잡음. StructTreeRoot 존재를 AND 로 요구(정상 Chromium PDF 는 둘 다 보유 — 실측 확인).
    tagged = ("/StructTreeRoot" in cat) and ("/MarkInfo" in cat)

    r = {
        "pages": doc.page_count,
        "text_chars": len(text),
        "text_layer_ok": len(text) >= MIN_TEXT_CHARS,
        "fonts_embedded": embedded,
        "outline_items": len(toc),
        "tagged": tagged,
    }
    # 완성본 분량 벤치마크(2026-07-04, 보고 전용 — 게이트 불변, physical_frontloaded 선례).
    # 기준 = 역대 최고본 H153 검증 업로드 실측(41p·17,396자·424자/쪽)에서 도출한 하한.
    # 목적: "완성본인지 판단이 어렵다"(운영자)를 감이 아니라 수치 미달량으로 바꾼다.
    _dense = len(text.replace(" ", "").replace("\n", ""))
    _cpp = (_dense / doc.page_count) if doc.page_count else 0.0
    r["volume"] = {
        "dense_chars": _dense,
        "chars_per_page": round(_cpp, 1),
        "benchmark_min_chars": _VOLUME_BENCH_MIN_CHARS,
        "benchmark_min_chars_per_page": _VOLUME_BENCH_MIN_CPP,
        "meets_benchmark": _dense >= _VOLUME_BENCH_MIN_CHARS and _cpp >= _VOLUME_BENCH_MIN_CPP,
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
    # P5-4(2026-07-05): 전문용어 밀도(공백 제외 1,000자당) 보고 필드 — 하드 게이트 아님
    # (첫 1회 괄호 풀이 정책과 오탐 충돌). v8 실측으로 상한 수치 확정 예정. 게이트 비악화:
    # 기존 키 제거·완화 없음, 관측 필드 추가만.
    _dense_n = max(1, len(body.replace(" ", "").replace("\n", "")))
    r["term_density_per_1k"] = round(len(_ct.term_hits(body)) * 1000.0 / _dense_n, 2)
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
        placeholder_hits, product=product, partner_present=partner_present
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
    # fake doc/블록 미지원 = 기하 검사 skip(clean 과 구분). 실 PDF 는 항상 검사됨(B-2/T3.2).
    r["layout_geometry_skipped"] = not (pages_blocks and page_rects)
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
