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


def verify(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    text = "".join(doc.load_page(i).get_text() for i in range(doc.page_count))
    text = text.strip()
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
    doc.close()

    # PDF/UA-1 검증 활성화(포터블 veraPDF). 결과는 '측정·보고'.
    va = _verapdf_ua1(pdf_path)
    r["verapdf"] = va
    r["verapdf_compliant"] = va.get("compliant") if va.get("available") else None

    # 하드 게이트(빌드 차단 기준): 검증된 구조 요건. veraPDF PDF/UA-1 완전 준수는
    # 별도 추적(Chromium 엔진 한계로 7.1-3 잔존 — WeasyPrint pdf/ua-1 경로 필요).
    r["gate_pass"] = bool(r["text_layer_ok"] and r["fonts_embedded"] and r["tagged"])
    return r
