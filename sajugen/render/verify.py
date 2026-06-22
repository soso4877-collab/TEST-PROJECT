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
    app_idx = next((i for i, t in enumerate(pages_text) if _APPENDIX_MARK in t), len(pages_text))
    body, allowed = [], []
    for i, t in enumerate(pages_text):
        is_cover = i == 0
        is_toc = "목차" in t and len(t.strip()) < 400
        is_appendix = i >= app_idx
        (allowed if (is_cover or is_toc or is_appendix) else body).append(t)
    return "".join(body), "".join(allowed)


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
) -> dict:
    """렌더 PDF 게이트. name_full(전체 이름 리스트)·identity((expected_gans, expected_terms,
    subject_specs))·singang([{full,given,honor,singang}]) 가 주어지면 H1.5.3/3.2 이름 호칭·일간
    role·신강약 group/role 게이트를 본문에 추가 적용한다.
    미전달이면 해당 게이트는 skip(clean True 기본 — 기존 호출·테스트 back-compat)."""
    doc = fitz.open(pdf_path)
    pages_text = [doc.load_page(i).get_text() for i in range(doc.page_count)]
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

    # 문장 품질·시제 스캔(이슈4·5·6) — 최종 PDF 본문 기준 known-bad 검출
    from ..content import quality_lint, temporal_lint

    qh = quality_lint.lint(text, names)
    th = temporal_lint.lint(text, ref_year)
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
    cust_body, allowed_region = _customer_body_pages(pages_text)
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
        and r["name_policy_clean"]  # 전체 이름 반복(H1.5.3, name_full 전달 시)
        and r["identity_role_clean"]  # 일간 role 오서술(H1.5.3, identity 전달 시)
        and r["singang_role_clean"]  # 신강약 group/role(H1.5.3.2, singang 전달 시)
    )
    return r
