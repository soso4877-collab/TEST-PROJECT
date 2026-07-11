# -*- coding: utf-8 -*-
"""Q7 3-B 관리자 모듈 추천·확정 UI와 저장 차단의 양방 회귀."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sajugen.app import app
from sajugen.models.report import (
    BirthInput,
    CalendarVerification,
    ReportPlan,
    UnifiedReport,
)
from sajugen import order_flow
from sajugen.store.orders import OrderState, OrderStore


# 테스트 응답과 감사 로그에 복제되면 안 되는 합성 비밀 토큰이다. 실제 고객 정보나
# 자연어 질문을 쓰지 않고도 새 UI가 gen_params 원문을 펼치지 않는지 확인할 수 있다.
_PRIVATE_TOKENS = (
    "PRIVATE_NAME_TOKEN",
    "PRIVATE_BIRTH_TOKEN",
    "PRIVATE_QUESTION_TOKEN",
)


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "orders.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(path))
    return path


@pytest.fixture
def client(db_path) -> TestClient:
    return TestClient(app)


def _report(*, product: str = "integrated_full", category: str = "직업") -> UnifiedReport:
    """계산·본문·PII 없이 관리자 메타 경계만 검증하는 최소 주문을 만든다."""

    gen_params = {
        "product": product,
        "brand": "default",
        "use_llm": False,
        "name": _PRIVATE_TOKENS[0],
        "birth": _PRIVATE_TOKENS[1],
        "concern": _PRIVATE_TOKENS[2],
    }
    if product == "integrated_full":
        gen_params["modules"] = []
    return UnifiedReport(
        order_id="",
        birth=BirthInput(
            name="",
            gender="M",
            input_date="",
            concern_text="",
        ),
        calendar_verification=CalendarVerification(solar_date=""),
        report_plan=ReportPlan(
            product=product,
            sections=[] if product == "integrated_full" else ["legacy_section"],
        ),
        render_meta={
            "question_category": {
                "value": category,
                "confirmed": False,
                "source": "auto",
            },
            "gen_params": gen_params,
        },
    )


def _seed_order(
    db_path: Path,
    *,
    product: str = "integrated_full",
    category: str = "직업",
    state: OrderState = OrderState.NORMALIZED,
) -> str:
    """허용 상태와 인접 차단 상태를 같은 합성 주문 형상으로 준비한다."""

    paths = {
        OrderState.RECEIVED: (),
        OrderState.NORMALIZED: (OrderState.NORMALIZED,),
        OrderState.CALC_OK: (OrderState.NORMALIZED, OrderState.CALC_OK),
        OrderState.DRAFTED: (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
        ),
        OrderState.IN_REVIEW: (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
            OrderState.IN_REVIEW,
        ),
        OrderState.APPROVED: (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
            OrderState.IN_REVIEW,
            OrderState.APPROVED,
        ),
    }
    store = OrderStore(db_path)
    try:
        order_id = store.create(_report(product=product, category=category))
        for next_state in paths[state]:
            store.transition(order_id, next_state, actor="system")
        return order_id
    finally:
        store.close()


def _stored_snapshot(db_path: Path, order_id: str) -> dict:
    store = OrderStore(db_path)
    try:
        return store.get_report(order_id).model_dump()
    finally:
        store.close()


def _module_audits(db_path: Path, order_id: str):
    store = OrderStore(db_path)
    try:
        return [
            entry
            for entry in store.audit(order_id)
            if entry.action == "confirm_module_selection"
        ]
    finally:
        store.close()


def test_integrated_full_detail_shows_recommendation_without_auto_selection(
    client,
    db_path,
):
    order_id = _seed_order(db_path, category="직업")
    before = _stored_snapshot(db_path, order_id)

    response = client.get(f"/admin/orders/{order_id}")

    assert response.status_code == 200
    assert "<h3>모듈 추천·확정</h3>" in response.text
    assert "현재 상태:\n  <b>미확정</b>" in response.text
    assert "질문 카테고리 추천: job" in response.text
    assert 'value="job">' in response.text
    assert 'value="job" checked' not in response.text
    assert 'job <span class="tag">추천</span>' in response.text
    for module_id in ("love", "job", "wealth", "health"):
        assert f'name="modules" value="{module_id}"' in response.text
    assert 'name="modules" value="gunghap"' not in response.text
    assert f'action="/admin/orders/{order_id}/retry"' not in response.text
    for token in _PRIVATE_TOKENS:
        assert token not in response.text
    assert _stored_snapshot(db_path, order_id) == before


def test_existing_recommendation_does_not_unblock_unconfirmed_generation(db_path):
    order_id = _seed_order(db_path, category="직업")
    calls = {"count": 0}

    def forbidden_generate(*args, **kwargs):
        calls["count"] += 1
        raise AssertionError("표시용 추천은 생성 입력이 될 수 없습니다")

    order_flow.run_generation(
        order_id,
        generate_fn=forbidden_generate,
        db_path=str(db_path),
    )

    store = OrderStore(db_path)
    try:
        report = store.get_report(order_id)
        assert store.get_state(order_id) == OrderState.NORMALIZED
        assert report.render_meta["question_category"]["value"] == "직업"
        assert report.render_meta["gen_params"]["modules"] == []
        assert order_flow.module_selection_state(report)["needs_confirmation"] is True
        blocked = [
            entry
            for entry in store.audit(order_id)
            if entry.action == "generation_blocked"
        ]
        assert blocked and blocked[-1].note == "integrated_full modules unconfirmed"
    finally:
        store.close()
    assert calls["count"] == 0


def test_existing_product_detail_has_no_module_selection_panel(client, db_path):
    order_id = _seed_order(db_path, product="integrated")
    before = _stored_snapshot(db_path, order_id)

    response = client.get(f"/admin/orders/{order_id}")

    assert response.status_code == 200
    assert "모듈 추천·확정" not in response.text
    assert f"/admin/orders/{order_id}/module-selection" not in response.text
    assert _stored_snapshot(db_path, order_id) == before


def test_module_selection_post_normalizes_and_saves_without_generation(client, db_path):
    order_id = _seed_order(db_path, category="재물")

    response = client.post(
        f"/admin/orders/{order_id}/module-selection",
        data={"modules": ["wealth", "love"]},
    )

    assert response.status_code == 200
    store = OrderStore(db_path)
    try:
        report = store.get_report(order_id)
        assert store.get_state(order_id) == OrderState.NORMALIZED
        assert report.render_meta["gen_params"]["modules"] == ["love", "wealth"]
        assert report.report_plan.sections == ["love", "wealth"]
        assert order_flow.module_selection_state(report) == {
            "product": "integrated_full",
            "modules": ["love", "wealth"],
            "confirmed": True,
            "needs_confirmation": False,
        }
    finally:
        store.close()

    audits = _module_audits(db_path, order_id)
    assert len(audits) == 1
    assert audits[0].section == "modules"
    assert audits[0].note == "love,wealth"
    assert 'value="love" checked' in response.text
    assert 'value="wealth" checked' in response.text
    assert f'action="/admin/orders/{order_id}/retry"' in response.text
    for token in _PRIVATE_TOKENS:
        assert token not in response.text
        assert token not in audits[0].note


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"modules": "unknown"},
        {"modules": ["love", "love"]},
        {"modules": ["love", "gunghap"]},
    ],
    ids=("empty", "unknown", "duplicate", "gunghap"),
)
def test_module_selection_post_rejects_invalid_values_without_saving(
    client,
    db_path,
    payload,
):
    order_id = _seed_order(db_path)
    before = _stored_snapshot(db_path, order_id)

    response = client.post(
        f"/admin/orders/{order_id}/module-selection",
        data=payload,
    )

    assert response.status_code == 422
    assert _stored_snapshot(db_path, order_id) == before
    assert _module_audits(db_path, order_id) == []


@pytest.mark.parametrize(
    "state",
    [
        OrderState.RECEIVED,
        OrderState.CALC_OK,
        OrderState.IN_REVIEW,
        OrderState.APPROVED,
    ],
)
def test_module_selection_post_rejects_every_non_normalized_phase_without_saving(
    client,
    db_path,
    state,
):
    order_id = _seed_order(db_path, state=state)
    before = _stored_snapshot(db_path, order_id)

    response = client.post(
        f"/admin/orders/{order_id}/module-selection",
        data={"modules": "love"},
    )

    assert response.status_code == 409
    assert _stored_snapshot(db_path, order_id) == before
    assert _module_audits(db_path, order_id) == []


def test_non_normalized_state_rejection_precedes_payload_validation(client, db_path):
    order_id = _seed_order(db_path, state=OrderState.IN_REVIEW)
    before = _stored_snapshot(db_path, order_id)

    response = client.post(
        f"/admin/orders/{order_id}/module-selection",
        data={"modules": ["love", "gunghap"]},
    )

    assert response.status_code == 409
    assert _stored_snapshot(db_path, order_id) == before
    assert _module_audits(db_path, order_id) == []


def test_module_selection_post_rejects_existing_product_without_saving(client, db_path):
    order_id = _seed_order(db_path, product="integrated")
    before = _stored_snapshot(db_path, order_id)

    response = client.post(
        f"/admin/orders/{order_id}/module-selection",
        data={"modules": "love"},
    )

    assert response.status_code == 422
    assert _stored_snapshot(db_path, order_id) == before
    assert _module_audits(db_path, order_id) == []
