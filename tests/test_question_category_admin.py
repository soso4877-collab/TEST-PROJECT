# -*- coding: utf-8 -*-
"""Q6 질문 자동분류·운영자 확정·승인 전제조건 회귀."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from sajugen.app import app  # noqa: E402
from sajugen.content.question_router import QuestionCategory  # noqa: E402
from sajugen.content.sections_schema import GuardReport, Report23, Section  # noqa: E402
from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport  # noqa: E402
from sajugen.store.orders import OrderState, OrderStore  # noqa: E402


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "orders.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(path))
    return path


@pytest.fixture
def client(db_path) -> TestClient:
    return TestClient(app)


def _report(*, concern: str, category: str, confirmed: bool = False) -> UnifiedReport:
    report23 = Report23(
        sections=[
            Section(
                id="consult",
                title="합성 질문 답변",
                source_keys=["report_json"],
                rule_text="합성 검수 본문입니다.",
                final_text="합성 검수 본문입니다.",
            )
        ],
        guard=GuardReport(
            safe_lint_total=0,
            factcheck_total=0,
            grounding_ok=True,
            polished_sections=0,
            fallback_sections=1,
            clean=True,
        ),
        concern_category=category,
    )
    return UnifiedReport(
        order_id="",
        birth=BirthInput(
            name="",
            gender="M",
            input_date="2000-01-01",
            birth_time="12:00",
            concern_text=concern,
        ),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        content=report23.model_dump(),
        render_meta={
            "question_category": {
                "value": category,
                "confirmed": confirmed,
                "source": "admin" if confirmed else "auto",
            }
        },
    )


def _seed_in_review(
    db_path: Path,
    *,
    concern: str,
    category: str,
    confirmed: bool = False,
) -> str:
    store = OrderStore(db_path)
    try:
        order_id = store.create(
            _report(concern=concern, category=category, confirmed=confirmed)
        )
        for state in (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
            OrderState.IN_REVIEW,
        ):
            store.transition(order_id, state, actor="system")
        return order_id
    finally:
        store.close()


def test_general_question_requires_category_confirmation_then_allows_approval(
    client, db_path
):
    order_id = _seed_in_review(
        db_path,
        concern="앞으로 무엇을 먼저 살펴야 할까요?",
        category="전반",
    )

    detail = client.get(f"/admin/orders/{order_id}")
    assert detail.status_code == 200
    assert "현재 카테고리: <b>전반</b>" in detail.text
    assert "전반 분류는 저신뢰" in detail.text
    for category in QuestionCategory:
        assert f'value="{category.value}"' in detail.text

    blocked = client.post(f"/admin/orders/{order_id}/approve")
    assert blocked.status_code == 409
    assert "카테고리를 먼저 확정" in blocked.text
    store = OrderStore(db_path)
    try:
        assert store.get_state(order_id) == OrderState.IN_REVIEW
    finally:
        store.close()

    confirmed = client.post(
        f"/admin/orders/{order_id}/question-category",
        data={"category": "직업"},
    )
    assert confirmed.status_code == 200

    store = OrderStore(db_path)
    try:
        report = store.get_report(order_id)
        report23 = Report23.model_validate(report.content)
        assert report23.concern_category == "직업"
        assert report.render_meta["question_category"] == {
            "value": "직업",
            "confirmed": True,
            "source": "admin",
        }
        audits = [entry for entry in store.audit(order_id) if entry.action == "confirm_question_category"]
        assert audits and audits[-1].section == "concern_category"
        assert audits[-1].note == "직업"
    finally:
        store.close()

    approved = client.post(f"/admin/orders/{order_id}/approve")
    assert approved.status_code == 200
    store = OrderStore(db_path)
    try:
        assert store.get_state(order_id) == OrderState.APPROVED
    finally:
        store.close()


@pytest.mark.parametrize(
    ("concern", "category"),
    [
        ("", "전반"),
        ("이직 준비 순서가 궁금합니다.", "직업"),
    ],
)
def test_empty_or_non_general_question_keeps_existing_approval_flow(
    client,
    db_path,
    concern,
    category,
):
    order_id = _seed_in_review(db_path, concern=concern, category=category)

    detail = client.get(f"/admin/orders/{order_id}")
    assert detail.status_code == 200
    if not concern:
        assert "질문 없음" in detail.text

    approved = client.post(f"/admin/orders/{order_id}/approve")
    assert approved.status_code == 200
    store = OrderStore(db_path)
    try:
        assert store.get_state(order_id) == OrderState.APPROVED
    finally:
        store.close()


def test_text_followup_general_category_can_be_confirmed_without_report23(client, db_path):
    report = UnifiedReport(
        order_id="",
        birth=BirthInput(
            name="",
            gender="M",
            input_date="2000-01-01",
            concern_text="이직 준비 순서가 궁금합니다.",
        ),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        content={},
        render_meta={
            "followup": {
                "parent_order_id": "ord_parent",
                "category": "전반",
                "masked_question": "앞으로 무엇을 먼저 살펴야 할까요?",
            }
        },
    )
    store = OrderStore(db_path)
    try:
        order_id = store.create(report, kind="followup", parent_order_id="ord_parent")
        for state in (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
            OrderState.IN_REVIEW,
        ):
            store.transition(order_id, state, actor="system")
    finally:
        store.close()

    assert client.post(f"/admin/orders/{order_id}/approve").status_code == 409
    confirmed = client.post(
        f"/admin/orders/{order_id}/question-category",
        data={"category": "직업"},
    )
    assert confirmed.status_code == 200

    store = OrderStore(db_path)
    try:
        saved = store.get_report(order_id)
        assert saved.content == {}
        assert saved.render_meta["followup"]["category"] == "직업"
        assert saved.render_meta["followup"]["category_confirmed"] is True
    finally:
        store.close()

    assert client.post(f"/admin/orders/{order_id}/approve").status_code == 200
