# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import client_tone_lint, customer_meta_lint, postprocess  # noqa: E402


def test_replace_generic_address_preserves_particles():
    honorific = "합성갑 님"
    text = "당신은 기준을 세우고, 당신의 속도를 봅니다. 고객님께 필요한 말도 남깁니다."

    out = postprocess.replace_generic_address(text, honorific)

    assert "합성갑 님은" in out
    assert "합성갑 님의" in out
    assert "합성갑 님께" in out
    assert client_tone_lint.placeholder_residue_clean(out), out


def test_strip_document_self_reference_preserves_sentence_body():
    text = (
        "이 글은 합성갑 님의 생활 기준을 정리합니다.\n"
        "이 문서는 고객용 문서로서 한 분께 드리는 수신자에게 필요한 기준입니다.\n"
        "이 리포트는 관계의 속도를 봅니다."
    )

    out = postprocess.strip_document_self_reference(text)

    assert "합성갑 님의 생활 기준을 정리합니다." in out
    assert "필요한 기준입니다." in out
    assert "관계의 속도를 봅니다." in out
    assert customer_meta_lint.is_clean(out), out


def test_style_residue_sanitize_combined_section_is_gate_clean():
    text = "이 글은 당신은 관계 기준을 확인하고, 고객님께 필요한 속도를 정리합니다."

    out = postprocess.strip_document_self_reference(text)
    out = postprocess.replace_generic_address(out, "합성갑 님")

    assert client_tone_lint.placeholder_residue_clean(out), out
    assert customer_meta_lint.is_clean(out), out


def test_strip_document_self_reference_does_not_overdelete_normal_words():
    text = "이 글자는 그대로 남습니다. 문서화 과정은 생활 기록을 정리하는 방법입니다."

    out = postprocess.strip_document_self_reference(text)

    assert "이 글자는 그대로 남습니다." in out
    assert "문서화 과정은 생활 기록을 정리하는 방법입니다." in out


def test_strip_formulaic_conclusion_preserves_body():
    text = (
        "종합하면, 합성갑 님은 속도를 조절해야 합니다.\n"
        "결론적으로 합성갑 님은 기준을 세워야 합니다.\n"
        "핵심은 다음과 같습니다. 합성갑 님은 관계의 순서를 확인해야 합니다."
    )

    out = postprocess.strip_formulaic_conclusion(text)

    assert "종합하면" not in out
    assert "결론적으로" not in out
    assert "핵심은 다음과 같습니다" not in out
    assert "합성갑 님은 속도를 조절해야 합니다." in out
    assert "합성갑 님은 기준을 세워야 합니다." in out
    assert "합성갑 님은 관계의 순서를 확인해야 합니다." in out
    assert customer_meta_lint.is_clean(out), out


def test_strip_formulaic_conclusion_keeps_normal_words():
    text = "두 내용을 종합해서 봅니다. 관계의 핵심 기준은 속도입니다."

    out = postprocess.strip_formulaic_conclusion(text)

    assert "종합해서 봅니다." in out
    assert "핵심 기준은 속도입니다." in out


def test_strip_formulaic_conclusion_consumes_trailing_josa_and_punct():
    # 선행 조사(은/는)·문장부호가 함께 제거돼야 함(과소삭제 패치 회귀).
    cases = [
        ("결론적으로는 합성갑 님은 기준을 세웁니다.", "합성갑 님은 기준을 세웁니다."),
        ("종합하면은 합성갑 님은 속도를 조절합니다.", "합성갑 님은 속도를 조절합니다."),
        ("핵심은 다음과 같습니다! 합성갑 님은 기준을 세웁니다.", "합성갑 님은 기준을 세웁니다."),
    ]
    for text, expected in cases:
        out = postprocess.strip_formulaic_conclusion(text)
        assert out == expected, (text, out)
        # 선행 잔재(조사/부호) 0
        assert not out.startswith(("는", "은", "!", "?", ",", ".", ":")), out
        assert customer_meta_lint.is_clean(out), out
