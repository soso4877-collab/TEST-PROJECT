# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import customer_meta_lint as lint  # noqa: E402


def _rules(text: str) -> set[str]:
    return {hit["rule"] for hit in lint.lint(text)}


def test_document_self_reference_and_integrated_reading_hit():
    hits = lint.lint("이 글은 통합 풀이입니다.")
    assert {"document_self_reference", "product_structure_label"} <= {
        hit["rule"] for hit in hits
    }
    assert all("match" not in hit for hit in hits)


def test_anti_generalized_letter_reading_hit():
    rules = _rules("일반론이 아니라 실제 글자 하나하나를 기준으로 봅니다.")
    assert "anti_generalized_letter_reading" in rules


def test_structure_walkthrough_hit():
    rules = _rules("먼저 큰 흐름을 보고, 이어서 관계의 결을 살펴보겠습니다.")
    assert "guided_structure_walkthrough" in rules


def test_normal_customer_copy_is_clean():
    text = (
        "이 시기에는 말보다 행동의 속도를 낮추는 편이 좋습니다. "
        "상대의 반응을 살피되, 답이 늦다는 이유만으로 결론을 서두르지 마세요. "
        "글로 마음을 정리해 보는 정도는 도움이 됩니다."
    )
    assert lint.is_clean(text), lint.lint(text)


def test_summarize_has_counts_only():
    summary = lint.summarize(lint.lint("이 문서는 고객용 문서입니다."))
    assert summary["clean"] is False
    assert summary["total_count"] >= 1
    assert "이 문서는" not in str(summary)
