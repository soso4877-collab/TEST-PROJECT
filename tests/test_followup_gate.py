# -*- coding: utf-8 -*-
"""T2 후속 답변 게이트 서브셋 양방 회귀."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.followup import answer_gate  # noqa: E402

_CONCERN = "요즘 돈 문제와 매매 계약 시기가 크게 고민입니다."
_ALLOW = {
    "ganzhi": [],
    "ganzhi_ko": ["정미", "병오"],
    "ziwei_majors_in_chart": [],
    "allowed_years": [2026, 2027],
}
_DIRECT = (
    "결론부터 말하면, 이 고민은 2026년 하반기부터 2027년 상반기 사이에 조건을 좁혀 "
    "확인하는 쪽이 맞습니다. 돈과 계약이 함께 걸린 자리라서 먼저 할 일은 셋입니다. "
    "첫째, 확정된 금액과 말로만 들은 조건을 나누어 적으세요. 둘째, 계약 전 확인할 서류와 "
    "일정을 한 번 더 맞추세요. 셋째, 상대가 답을 미루면 바로 결정하지 말고 다음 확인 "
    "시점을 잡으세요. 지금 당장 결론을 밀어붙이기보다 기준을 정하고 작은 실행으로 반응을 "
    "보는 편이 안전합니다. 이 흐름은 결과를 보장하려는 말이 아니라, 질문하신 매매와 돈 "
    "문제를 다룰 때 놓치기 쉬운 확인 순서입니다. "
) * 2


def _rules(text: str, **over) -> set[str]:
    result = answer_gate.check(
        text,
        concern=over.get("concern", _CONCERN),
        allow_tokens=over.get("allow_tokens", _ALLOW),
        ref_year=over.get("ref_year", 2026),
        ref_date=over.get("ref_date", "2026-07-07"),
        specs=over.get("specs"),
    )
    return {f["rule"] for f in result["failures"]}


def test_clean_answer_passes_and_reports_skipped_specs():
    result = answer_gate.check(
        _DIRECT,
        concern=_CONCERN,
        allow_tokens=_ALLOW,
        ref_year=2026,
        ref_date="2026-07-07",
        specs=None,
    )
    assert result["ok"] is True
    assert result["failures"] == []
    skipped = {s["check"] for s in result["skipped"]}
    assert "identity_role_lint" in skipped
    assert "name_policy_lint" in skipped


@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("반드시 결혼합니다.", "safe"),
        ("2099년에 일이 생깁니다.", "year"),
        ("", "빈 본문"),
        ("9월 이후부터 준비하세요.", "month_notation"),
        ("시간의 리듬을 타면 좋습니다.", "loanword"),
        ("오행 분포를 보면 목 2, 화 2입니다.", "raw_calc_head"),
        ("이 글은 통합 풀이입니다.", "document_self_reference"),
        ("고객님, 기준을 잡으세요.", "generic_customer_address"),
        ("시간의 결을 따라 걷는 중입니다.", "style"),
        ("명궁은 명궁, 신궁은 명궁입니다.", "internal_meta_label"),
        ("무조건 성공합니다.", "guarantee"),
        ("짧은 안내입니다.", "consult_direct"),
        ("# 제목\n본문입니다.", "markdown_artifact"),
    ],
)
def test_each_text_lint_blocks_injected_defect(text, rule):
    assert rule in _rules(text), (rule, _rules(text))


def test_conditional_lints_run_when_specs_exist():
    specs = {
        "name_full": ["김민준"],
        "identity": {
            "expected_gans": ["임"],
            "expected_terms": ["임수"],
            "subject_specs": [(["민준 씨"], "임수")],
        },
        "singang": [{"full": "김민준", "given": "민준", "honor": "민준 씨", "singang": "신약"}],
        "honorific": [
            {
                "role": "receiver",
                "aliases": ["김민준", "민준", "민준 씨", "민준 님"],
                "expected_honorific": "님",
            }
        ],
        "role_perspective": [
            {
                "role": "receiver",
                "aliases": ["김민준", "민준", "민준 씨", "민준 님"],
                "expected_honorific": "님",
            }
        ],
        "daewoon_current": "정미",
    }
    text = (
        "김민준은 일간은 병화입니다. 민준 씨는 신강이고, 민준 님도 같은 흐름입니다. "
        "지금 병오 대운 초입에 들어서는 자리입니다. "
    ) + _DIRECT
    result = answer_gate.check(
        text,
        concern=_CONCERN,
        allow_tokens=_ALLOW,
        ref_year=2026,
        ref_date="2026-07-07",
        specs=specs,
    )
    rules = {f["rule"] for f in result["failures"]}
    assert {
        "name_policy",
        "identity_role",
        "singang_role",
        "mixed_honorific",
        "receiver_third_person_honorific",
        "daewoon_consistent",
    } <= rules


def test_assert_clean_raises_on_failure():
    with pytest.raises(answer_gate.AnswerGateError):
        answer_gate.assert_clean(
            "2099년에 반드시 성공합니다.",
            concern=_CONCERN,
            allow_tokens=_ALLOW,
            ref_year=2026,
            ref_date="2026-07-07",
        )


def test_drop_pdf_layout_gate_is_not_called(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("PDF delivery_quality.analyze 호출 금지")

    monkeypatch.setattr("sajugen.content.delivery_quality.analyze", boom)
    result = answer_gate.check(
        _DIRECT,
        concern=_CONCERN,
        allow_tokens=_ALLOW,
        ref_year=2026,
        ref_date="2026-07-07",
    )
    assert result["failures"] == []
