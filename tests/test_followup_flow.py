# -*- coding: utf-8 -*-
"""T4 후속 답변 CLI/상태머신 배선 회귀."""

import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import order_flow  # noqa: E402
from sajugen.cli import app as cli_app  # noqa: E402
from sajugen.content.sections_schema import GuardReport, Report23, Section  # noqa: E402
from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport  # noqa: E402
from sajugen.store.orders import ApprovalRequired, OrderState, OrderStore  # noqa: E402

_ANSWER = (
    "결론부터 말하면, 이 질문은 올해 하반기 안에서 조건을 좁혀 확인하는 방식이 맞습니다. "
    "먼저 맡을 역할과 돈의 조건을 나누어 보세요. 확인 순서는 세 가지입니다. "
    "첫째, 현재 자리에서 남길 수 있는 조건을 확인합니다. 둘째, 옮길 자리의 계약 조건과 "
    "실제 업무 범위를 문서로 확인합니다. 셋째, 답이 늦어지면 바로 결정하지 말고 다음 확인 "
    "시점을 잡습니다. 질문하신 이직 문제는 직업과 재물 조건이 함께 움직이는 고민이라, "
    "속도보다 확인 순서가 중요합니다. 결과를 보장하려는 말이 아니라 저장된 흐름 안에서 "
    "선택 기준을 좁혀 드리는 답변입니다. "
) * 2


class _Backend:
    name = "fake"

    def available(self):
        return True

    def classify(self, concern):
        raise AssertionError("classify 직접 호출 금지")

    def polish(self, rule_text, title):
        return rule_text

    def compose(self, **kwargs):
        return _ANSWER


def _section(sid: str, text: str) -> Section:
    return Section(id=sid, title=sid, source_keys=["report_json"], rule_text=text, final_text=text)


def _parent_report() -> UnifiedReport:
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
        concern_category="직업",
        allow_tokens={
            "ganzhi": [],
            "ganzhi_ko": ["정미"],
            "ziwei_majors_in_chart": [],
            "allowed_years": [2026],
        },
    )
    return UnifiedReport(
        order_id="",
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        content=r23.model_dump(),
    )


def _seed_parent(db: Path) -> tuple[str, str]:
    store = OrderStore(db)
    try:
        alias = store.link_customer("SD-0001", name_masked="MASKED_A")
        parent = store.create(_parent_report(), alias=alias, kind="new")
        return alias, parent
    finally:
        store.close()


def test_run_followup_creates_in_review_order_and_text_issue_is_approval_gated(tmp_path):
    db = tmp_path / "orders.sqlite"
    alias, parent = _seed_parent(db)
    result = order_flow.run_followup(
        alias=alias,
        question="이직을 준비해도 될까요?",
        db_path=str(db),
        backend=_Backend(),
        today="2026-07-07",
    )
    assert result["ok"] is True, result
    oid = result["order_id"]
    store = OrderStore(db)
    try:
        assert store.get_state(oid) == OrderState.IN_REVIEW
        row = next(r for r in store.list_orders() if r["order_id"] == oid)
        assert row["alias"] == alias and row["parent_order_id"] == parent
        assert row["kind"] == "followup"
        with pytest.raises(ApprovalRequired):
            store.issue_final_text(oid)
        store.transition(oid, OrderState.APPROVED, actor="admin")
        assert store.issue_final_text(oid, actor="admin") == _ANSWER.strip()
        assert store.get_state(oid) == OrderState.DELIVERED
    finally:
        store.close()


def test_run_followup_gate_failure_creates_no_order(tmp_path):
    db = tmp_path / "orders.sqlite"
    alias, _parent = _seed_parent(db)
    result = order_flow.run_followup(
        alias=alias,
        question="2099년에 이직해도 될까요?",
        db_path=str(db),
        backend=_Backend(),
        today="2026-07-07",
    )
    assert result["ok"] is False
    store = OrderStore(db)
    try:
        rows = store.list_orders()
        assert len(rows) == 1
        assert rows[0]["kind"] == "new"
    finally:
        store.close()


def test_customer_find_cli_outputs_alias_and_latest_order(tmp_path):
    db = tmp_path / "orders.sqlite"
    alias, parent = _seed_parent(db)
    result = CliRunner().invoke(cli_app, ["customer-find", "--alias", alias, "--db", str(db)])
    assert result.exit_code == 0, result.output
    assert alias in result.output and parent in result.output
    assert "MASKED_A" in result.output


def test_gen_followup_cli_reports_failure(monkeypatch, tmp_path):
    def fake_run_followup(**kwargs):
        return {"ok": False, "reason": "범위 밖 연도", "failures": [{"rule": "year"}]}

    monkeypatch.setattr(order_flow, "run_followup", fake_run_followup)
    result = CliRunner().invoke(
        cli_app,
        ["gen-followup", "--alias", "SD-0001", "--question", "2029년은요", "--db", str(tmp_path / "x.sqlite")],
    )
    assert result.exit_code == 1
    assert "게이트: FAIL" in result.output and "year" in result.output
