# -*- coding: utf-8 -*-
"""렌더 검증 — orphan(widow) 페이지 검출 + 짧은 마지막 단락 병합(이슈1, H1-mini)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.render import pdf as render_pdf  # noqa: E402
from sajugen.render import verify as v  # noqa: E402


def test_orphan_detector_flags_short_standalone_page():
    pages = [
        "표지",  # p1 표지(제외)
        "제 1 장 본문 " + "가" * 200,  # 정상 장
        "있습니다.",  # p3 orphan(짧은 단독 본문)
        "본문이 충분히 긴 페이지입니다. " * 20,  # 정상
        "글을 맺으며 감사합니다.",  # 마지막(제외)
    ]
    orphans = v._orphan_pages(pages)
    assert [o["page"] for o in orphans] == [3], orphans


def test_orphan_detector_excludes_chapter_and_appendix():
    pages = [
        "표지",
        "제 3 장",  # 장 구분(짧아도 제외)
        "용어 풀이",  # 부록(제외)
        "마지막",
    ]
    assert v._orphan_pages(pages) == []


def test_split_paragraphs_merges_short_tail():
    # '있습니다.' 같은 짧은 마지막 단락은 직전 단락에 합쳐 단독 페이지화 방지
    text = "앞 단락은 충분히 깁니다. 흐름을 이어 갑니다.\n\n있습니다."
    paras = render_pdf._split_paragraphs(text)
    assert len(paras) == 1
    assert paras[0].endswith("있습니다.")
    # 긴 마지막 단락은 그대로 분리 유지
    text2 = "첫 단락입니다.\n\n두 번째 단락은 충분히 길어서 합쳐지지 않습니다."
    assert len(render_pdf._split_paragraphs(text2)) == 2
