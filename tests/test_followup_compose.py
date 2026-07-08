# -*- coding: utf-8 -*-
"""T3 후속 답변 슬림 컴포저 — 저장 사실 재사용과 시제 2기준 회귀."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content.sections_schema import GuardReport, Report23, Section  # noqa: E402
from sajugen.followup import compose as followup_compose  # noqa: E402
from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport  # noqa: E402

_ANSWER = (
    "결론부터 말하면, 이 질문은 올해 하반기 안에서 조건을 좁혀 확인하는 방식이 맞습니다. "
    "지금 바로 결정을 밀어붙이기보다 먼저 맡을 역할과 돈의 조건을 나누어 보세요. "
    "실행 순서는 세 가지입니다. 첫째, 지금 직장에서 남길 수 있는 조건을 확인합니다. "
    "둘째, 옮길 자리의 계약 조건과 실제 업무 범위를 문서로 확인합니다. 셋째, 답이 늦어지면 "
    "바로 결정하지 말고 다음 확인 시점을 잡습니다. 질문하신 이직 문제는 직업과 재물 조건이 "
    "함께 움직이는 고민이라, 속도보다 확인 순서가 중요합니다. 결과를 보장하려는 말이 아니라 "
    "저장된 흐름 안에서 선택 기준을 좁혀 드리는 답변입니다. "
) * 2


class _Backend:
    name = "fake"

    def __init__(self, answer: str = _ANSWER):
        self.answer = answer
        self.calls = []

    def available(self) -> bool:
        return True

    def classify(self, concern):
        raise AssertionError("compose.classify 직접 호출 금지")

    def polish(self, rule_text, title):
        return rule_text

    def compose(self, **kwargs):
        self.calls.append(kwargs)
        return self.answer


def _section(sid: str, text: str) -> Section:
    return Section(id=sid, title=sid, source_keys=["report_json"], rule_text=text, final_text=text)


def _report(*, allowed_years=None, concern_category="직업") -> UnifiedReport:
    year_tokens = [2026] if allowed_years is None else allowed_years
    r23 = Report23(
        sections=[
            _section("nature", "저장된 기질 본문입니다."),
            _section("flow", "저장된 시간 흐름 본문입니다. 지금은 정미 대운을 지나는 시기입니다."),
            _section("consult", _ANSWER),
        ],
        guard=GuardReport(
            safe_lint_total=0,
            factcheck_total=0,
            grounding_ok=True,
            polished_sections=0,
            fallback_sections=0,
            clean=True,
        ),
        concern_category=concern_category,
        allow_tokens={
            "ganzhi": [],
            "ganzhi_ko": ["정미"],
            "ziwei_majors_in_chart": [],
            "allowed_years": year_tokens,
        },
    )
    return UnifiedReport(
        order_id="ord_followup",
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        content=r23.model_dump(),
        render_meta={"gen_params": {"horoscope": "2025-06-01"}},
    )


def test_compose_uses_stored_sections_masks_question_and_current_ref_date(monkeypatch):
    # live saju 재계산을 호출하지 않는지 방어한다.
    monkeypatch.setattr("sajugen.calc.engine.build", lambda *a, **k: (_ for _ in ()).throw(AssertionError("live calc 금지")))
    backend = _Backend()
    result = followup_compose.compose(
        _report(allowed_years=[1990, 2026]),
        "1990년 5월 20일 이직을 지금 준비해도 될까요?",
        backend=backend,
        today="2026-07-07",
    )
    assert result["ok"] is True, result
    assert "[생년월일 비공개]" in result["masked_question"]
    assert "1990년 5월 20일" not in result["masked_question"]
    call = backend.calls[0]
    assert call["section_id"] == "consult"
    assert "저장된 기질 본문" in call["base_text"] and "저장된 시간 흐름" in call["base_text"]
    assert call["ref_year"] == 2026 and call["ref_date"] == "2026-07-07"


def test_out_of_scope_year_rejects_before_backend_call():
    backend = _Backend()
    result = followup_compose.compose(
        _report(allowed_years=[2026]),
        "2029년에 이직해도 될까요?",
        backend=backend,
        today="2026-07-07",
    )
    assert result["ok"] is False
    assert "범위 밖 연도" in result["reason"]
    assert backend.calls == []


def test_empty_allowed_years_boundary_uses_factcheck_backstop():
    # 구 저장본처럼 allowed_years 가 비면 질문의 절대연도 사전 거부는 판정할 근거가 없다.
    # 대신 답변 후보가 저장 allow_tokens 밖 간지를 꺼내면 factcheck 가 fail-closed 로 막는다.
    backend = _Backend("2099년 경오년에는 조건을 다시 보세요. " + _ANSWER)
    result = followup_compose.compose(
        _report(allowed_years=[]),
        "내년에 이직해도 될까요?",
        backend=backend,
        today="2026-07-07",
    )
    assert backend.calls, "allowed_years 빈 경계에서는 사전 out_of_scope 거부가 아니다"
    assert result["ok"] is False
    assert any(f["source"] == "factcheck" and f["rule"] == "ganzhi_ko" for f in result["failures"])


def test_relative_next_year_question_is_backstopped_after_generation():
    # "내년"은 질문에 YYYY가 없으므로 현행 사전 범위밖 정규식 대상이 아니다.
    # 답변 후보가 저장 지평 밖 절대연도를 발화하면 factcheck allowed_years 가 차단한다.
    backend = _Backend("2027년에 바로 움직이면 됩니다. " + _ANSWER)
    result = followup_compose.compose(
        _report(allowed_years=[2026]),
        "내년에 이직해도 될까요?",
        backend=backend,
        today="2026-07-07",
    )
    assert backend.calls, "상대연도 질문은 사전 out_of_scope 거부가 아니다"
    assert result["ok"] is False
    assert any(f["source"] == "factcheck" and f["rule"] == "year" for f in result["failures"])


def test_out_of_scope_topic_rejects_before_backend_call():
    backend = _Backend()
    result = followup_compose.compose(
        _report(concern_category="직업"),
        "연애는 언제 좋아질까요?",
        backend=backend,
        today="2026-07-07",
    )
    assert result["ok"] is False
    assert "범위 밖 주제" in result["reason"]
    assert backend.calls == []


def test_generated_answer_must_pass_allow_tokens_and_month_notation():
    bad_year = _Backend("2099년에 결정하면 됩니다. " + _ANSWER)
    result = followup_compose.compose(
        _report(allowed_years=[2026]),
        "이직을 준비해도 될까요?",
        backend=bad_year,
        today="2026-07-07",
    )
    assert result["ok"] is False
    assert any(f["rule"] == "year" for f in result["failures"])

    bad_month = _Backend("9월 이후부터 움직이면 됩니다. " + _ANSWER)
    result2 = followup_compose.compose(
        _report(allowed_years=[2026]),
        "이직을 준비해도 될까요?",
        backend=bad_month,
        today="2026-07-07",
    )
    assert result2["ok"] is False
    assert any(f["rule"] == "month_notation" for f in result2["failures"])


def test_current_year_anchor_is_today_not_original_report_year():
    backend = _Backend()
    result = followup_compose.compose(
        _report(allowed_years=[2026]),
        "이직을 준비해도 될까요?",
        backend=backend,
        today="2026-07-07",
    )
    assert result["ok"] is True
    assert backend.calls[0]["ref_year"] == 2026
    assert backend.calls[0]["ref_date"] == "2026-07-07"
