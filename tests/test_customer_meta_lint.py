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


# ---- 2026-07-05 운영자 발견(v6 1장): 골격의 작성자 작업 예고·빈 지시 등재 양방 ----

_TASK_ANNOUNCE_FAIL = [
    "사주를 한 장으로 압축해 보겠습니다.",  # 실사고 문장 그대로
    "이제 현실에 적용해 보겠습니다.",
    "겉과 속의 짜임도 함께 보겠습니다.",
    "성격과 기질을 한데 모아 보겠습니다.",
    "일주와 부처궁을 겹쳐서 보겠습니다.",
]

_TASK_ANNOUNCE_OK = [
    "관계 영역은 일주와 부처궁을 겹쳐서 봅니다.",  # 관법 서술
    "가까운 관계의 결을 중심으로 봅니다.",
    "무리하지 않는지를 먼저 보세요.",  # 행동 권유
    "사주를 펼쳐 놓고 보면 가장 먼저 눈에 들어오는 그림이 있습니다.",  # 교체 문구
    "그 시기에는 흐름을 지켜보면 좋습니다.",
]


def test_writer_task_announcement_flags_narrator_voice():
    # 실사고(v6 1장) 문형 = FAIL — 프롬프트에만 있던 규범(llm_sections '~보겠습니다 금지')의
    # 게이트 승격. 룰 골격·LLM·관리자 수정분 모두에 적용된다.
    for text in _TASK_ANNOUNCE_FAIL:
        assert "writer_task_announcement" in _rules(text), text


def test_writer_task_announcement_passes_consult_voice():
    # 관법 서술('~으로 봅니다')·행동 권유('보세요')·교체 문구는 통과(오탐 0 앵커).
    for text in _TASK_ANNOUNCE_OK:
        assert "writer_task_announcement" not in _rules(text), text


def test_formulaic_empty_instruction_two_way():
    # 빈 지시 상투구 = FAIL / 구체 내용이 있는 지시·확인 문장은 통과.
    assert "formulaic_empty_instruction" in _rules("조건, 사람, 시기를 차례대로 확인하세요.")
    assert "formulaic_empty_instruction" in _rules("아래 항목을 순서대로 확인하면 됩니다.")
    for text in (
        "계약 조건이 실제로 갖춰졌는지 하나씩 짚은 뒤에 정하셔도 늦지 않습니다.",
        "대화가 이어지는지, 혼자만 애쓰고 있지는 않은지를 보면 답이 드러납니다.",
        "서류를 확인한 뒤 움직이는 편이 안전합니다.",
    ):
        assert "formulaic_empty_instruction" not in _rules(text), text


def test_rule_skeleton_sections_pass_customer_meta_lint():
    # 골격-게이트 동기화 앵커(근본원인 2층): 규범이 게이트에 등재될 때 룰 골격이 함께
    # 동기화됐는지를 전 섹션 실빌드로 고정 — QI-2026-07-05 유형('금지어 등재 후 골격
    # 미동기화')의 개인 리포트 재발을 구조적으로 차단한다.
    from sajugen.calc import engine
    from sajugen.content import rules

    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    sections = rules.build_all(
        saju, ref_year=2026, name="테스트", concern_category="재물",
        concern_text="합성 고민 텍스트입니다.",
    )
    for sid, text in sections.items():
        hits = lint.lint(text)
        assert hits == [], (sid, hits)
