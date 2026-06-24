# -*- coding: utf-8 -*-
"""공통 후처리(content.postprocess) + 렌더 후 마크다운 게이트(render.verify) 단위 검증.

개인 경로·궁합 경로가 같은 정제 함수를 쓰도록 분리한 모듈(2026-06-14 Phase 1).
회귀 핵심: (1) 한글이 한자 제거 정규식에 삭제되지 않는다(_CJK_RX U+F900 오입력 회귀),
(2) 마크다운 누출(---·**·#)이 제거/탐지된다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import postprocess as pp  # noqa: E402
from sajugen.render import verify as v  # noqa: E402


def test_strip_artifacts_drops_markdown():
    src = "본문 시작\n---\n**굵게**\n# 제목\n> 인용문\n- 목록항목\n끝 문장"
    out = pp.strip_artifacts(src)
    assert "---" not in out  # 수평선 라인 통째 드롭
    assert "**" not in out  # 굵게 마커 제거
    assert "# 제목" not in out  # 마크다운 제목 라인 드롭
    assert "굵게" in out and "본문 시작" in out and "끝 문장" in out  # 내용 보존
    assert out.startswith("본문 시작")


def test_hanja_clean_preserves_hangul():
    # 회귀: _CJK_RX 가 한글(U+AC00-D7A3)을 삭제하면 안 됨(U+8C48 오입력 사고)
    assert pp.hanja_clean("용신 화 구조 임인 일주") == "용신 화 구조 임인 일주"


def test_hanja_clean_removes_hanja():
    out = pp.hanja_clean("七殺 구조, 壬寅 일주, 火 기운")
    assert "七" not in out and "殺" not in out and "壬" not in out and "火" not in out
    assert "구조" in out and "일주" in out and "기운" in out


def test_hanja_clean_collapses_duplicate_parens():
    # 이슈3: '술(술)'·'진(진)'·'명궁(명궁)' 중복 괄호 축약
    assert pp.hanja_clean("지지 술(술)이 화의 묘고입니다.") == "지지 술이 화의 묘고입니다."
    assert pp.hanja_clean("진(진)이 수의 묘고") == "진이 수의 묘고"
    assert pp.hanja_clean("명궁(명궁)은 바탕을 봅니다.") == "명궁은 바탕을 봅니다."


def test_hanja_clean_keeps_descriptive_parens():
    # 설명 괄호(앞말≠괄호안)는 보존
    assert "묘(매우 밝음)" in pp.hanja_clean("천량 묘(매우 밝음)에 있습니다.")
    assert "함지(약함)" in pp.hanja_clean("무곡 함지(약함) 자리입니다.")


def test_paren_residue_cleanup():
    # H1.5.1: 괄호 안 중복/꼬리 쉼표 정리(한자 제거 부작용). 설명 괄호는 보존.
    assert pp.hanja_clean("창고(술, 술)에") == "창고(술)에"
    assert pp.hanja_clean("재고(진, 진)") == "재고(진)"
    assert pp.hanja_clean("용신(화, )입니다") == "용신(화)입니다"
    assert "묘(매우 밝음)" in pp.hanja_clean("천량 묘(매우 밝음) 자리")
    assert "함지(약함)" in pp.hanja_clean("무곡 함지(약함) 자리")
    assert "(목, 화)" in pp.hanja_clean("기운(목, 화) 분포")  # 일반 나열 괄호 보존


def test_punctuation_normalization():
    # H1.5: 구두점 깨짐 정규화 ('일주 기준,, 년주 기준,.' 류). 자연 구두점은 불변.
    assert pp.hanja_clean("일주 기준,, 년주 기준,.") == "일주 기준, 년주 기준."
    assert pp.hanja_clean("정리합니다, .") == "정리합니다."
    assert pp.hanja_clean("끝입니다..") == "끝입니다."
    assert (
        pp.hanja_clean("좋아요. 그리고 좋습니다.") == "좋아요. 그리고 좋습니다."
    )  # 자연 구두점 불변


def test_hanja_clean_collapses_adjacent_duplicate_korean_words():
    assert (
        pp.hanja_clean("관계에서 반복되는 반복되는 흐름이 보입니다.")
        == "관계에서 반복되는 흐름이 보입니다."
    )
    assert pp.hanja_clean("흐름 흐름 자체를 보는 문장입니다.") == "흐름 자체를 보는 문장입니다."


def test_markdown_artifacts_detects_and_clean():
    assert v.markdown_artifacts("정상 한국어 본문입니다. 문제 없음.") == []
    hits = v.markdown_artifacts("앞줄\n---\n**굵게** 줄\n# 제목 줄")
    assert any(h.strip("-") == "" for h in hits)  # --- 탐지
    assert "**" in hits  # 굵게 탐지
