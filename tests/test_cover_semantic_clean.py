# -*- coding: utf-8 -*-
"""표지(front-matter) semantic-clean 회귀.

배경: integrated/gunghap 의 input_civil=" · ".join(names) 과 생시 미상 고지
("생시 미상·추정")가 page 1 표지(cover_sub)로 그대로 출력돼, hrun 본문-스코프
게이트는 PASS 였지만 full-PDF semantic(hsemantic_review)이 page 1 의
ai_signature_punctuation('·')을 잡아 FAILED 가 났다(2026-06-30, customer Tier2 retry2).

수정: render/pdf.py 가 표지 표시 문자열만 렌더 직전 정규화('·'·em/en dash → ', ').
본문은 대상 아님. 여기서는 표지 HTML 에 '·'·'—'·'–' 가 남지 않고 style_lint clean 임을 고정한다.
style_lint.py / verify.py / hsemantic_review 는 완화하지 않는다(게이트가 잡을 문자를
표지에서 없앤다).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import config as cfg  # noqa: E402
from sajugen.content import style_lint  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402

_SUB_RX = re.compile(r'<div class="sub">(.*?)</div>', re.S)
_NAME_RX = re.compile(r'<div class="cover-name">(.*?)</div>', re.S)
_AI_PUNCT = ("·", "—", "–")


def _report():
    secs = [
        SimpleNamespace(
            id="summary",
            title="큰 그림",
            source_keys=["m"],
            final_text="합성 본문 문단입니다. " * 20,
        ),
    ]
    return SimpleNamespace(sections=secs)


def _brand():
    return dict(cfg.brand("seodam"))


def _render(input_civil: str, *, name: str = "", unknown_time: bool = False) -> str:
    return render_pdf.render_html(
        _report(),
        SimpleNamespace(input_civil=input_civil),
        name=name,
        unknown_time=unknown_time,
        brand=_brand(),
    )


def _sub_text(html: str) -> str:
    m = _SUB_RX.search(html)
    assert m, "cover sub not found"
    return m.group(1)


def _name_text(html: str) -> str:
    m = _NAME_RX.search(html)
    assert m, "cover-name not found"
    return m.group(1)


def test_helper_normalizes_ai_signature_punctuation():
    # 헬퍼 단위: '·'·em/en dash → ', ', 날짜 하이픈은 보존.
    assert render_pdf._clean_cover_text("DOC_A · DOC_B") == "DOC_A, DOC_B"
    assert render_pdf._clean_cover_text("DOC_A — DOC_B") == "DOC_A, DOC_B"
    assert render_pdf._clean_cover_text("DOC_A – DOC_B") == "DOC_A, DOC_B"
    assert render_pdf._clean_cover_text("생시 미상·추정") == "생시 미상, 추정"
    # 날짜 하이픈(U+002D)은 ai_signature 아님 → 보존
    assert render_pdf._clean_cover_text("1990-05-20") == "1990-05-20"
    assert render_pdf._clean_cover_text("") == ""
    assert render_pdf._clean_cover_text(None) == ""


def test_cover_sub_join_path_is_semantic_clean():
    # integrated/gunghap 의 ' · '.join 경로를 그대로 재현.
    sub = _sub_text(_render(" · ".join(["DOC_A", "DOC_B"])))
    for ch in _AI_PUNCT:
        assert ch not in sub, (ch, sub)
    assert "DOC_A, DOC_B" in sub
    assert style_lint.is_clean(sub), style_lint.lint(sub)


def test_cover_sub_three_person_join_is_semantic_clean():
    sub = _sub_text(_render(" · ".join(["DOC_A", "DOC_B", "DOC_C"])))
    for ch in _AI_PUNCT:
        assert ch not in sub, (ch, sub)
    assert "DOC_A, DOC_B, DOC_C" in sub
    assert style_lint.is_clean(sub), style_lint.lint(sub)


def test_cover_unknown_time_suffix_is_semantic_clean():
    # 생시 미상 suffix("생시 미상·추정") 안의 '·'도 제거돼야 함.
    sub = _sub_text(_render("DOC_A", unknown_time=True))
    for ch in _AI_PUNCT:
        assert ch not in sub, (ch, sub)
    assert "생시 미상, 추정" in sub
    assert style_lint.is_clean(sub), style_lint.lint(sub)


def test_cover_name_with_separator_is_semantic_clean():
    # 방어적: 이름 영역에도 ai_signature 문자가 남지 않게.
    name = _name_text(_render("DOC_A", name="DOC·NAME"))
    for ch in _AI_PUNCT:
        assert ch not in name, (ch, name)
    assert style_lint.is_clean(name), style_lint.lint(name)
