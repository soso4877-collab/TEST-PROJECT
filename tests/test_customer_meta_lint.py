# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import customer_meta_lint as lint  # noqa: E402


def _rules(text: str) -> set[str]:
    return {hit["rule"] for hit in lint.lint(text)}


def test_document_self_reference_and_integrated_reading_hit():
    hits = lint.lint("이 글은 통합 풀이입니다.")
    assert {"document_self_reference", "product_structure_label"} <= {hit["rule"] for hit in hits}
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


_TRANSITION_FAIL = [
    "자미두수 명궁 이야기도 바로 이어집니다.",
    "자미두수 명궁 이야기가 바로 이어집니다.",
    "명궁 이야기도 이어집니다.",
    "이어서 자미두수 명궁을 보겠습니다.",
    "다음 장에서는 관계의 흐름을 보겠습니다.",
    "다음으로 명궁을 살펴보겠습니다.",
    "이 풀이는 다음 순서로 이어집니다.",
    "앞서 본 내용을 이어서 보겠습니다.",
    "관계 파트가 이어집니다.",
    "다음 파트에서는 두 사람의 흐름을 다룹니다.",
]

_TRANSITION_OK = [
    "관계가 오래 이어지려면 확인의 속도를 맞춰야 합니다.",
    "일이 이어집니다.",
    "흐름이 이어집니다.",
    "2027년까지 이 흐름이 이어질 수 있습니다.",
    "명궁은 삶의 중심이 어디에 놓이는지를 보여 줍니다.",
    "자미두수에서는 명궁이 사람의 기본 결을 보여 줍니다.",
    "이야기를 나누는 방식이 관계에 영향을 줍니다.",
]


def test_transition_section_preview_flags_document_progression():
    # 문서 진행/섹션 예고/다음 파트 안내 = FAIL(작성자 메타 발화).
    for text in _TRANSITION_FAIL:
        assert "transition_section_preview" in _rules(text), text


def test_transition_section_preview_does_not_flag_life_flow():
    # 생활 흐름의 '이어집니다'·'이야기'·'명궁' 단독은 통과(오탐 0).
    for text in _TRANSITION_OK:
        assert "transition_section_preview" not in _rules(text), text


def test_transition_section_preview_is_pii_free():
    hits = lint.lint("자미두수 명궁 이야기도 바로 이어집니다.")
    assert any(h["rule"] == "transition_section_preview" for h in hits)
    assert all("match" not in h for h in hits)
    assert "명궁 이야기" not in str(hits)


def test_summarize_has_counts_only():
    summary = lint.summarize(lint.lint("이 문서는 고객용 문서입니다."))
    assert summary["clean"] is False
    assert summary["total_count"] >= 1
    assert "이 문서는" not in str(summary)
