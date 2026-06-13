# -*- coding: utf-8 -*-
"""Phase 4 주문 상태머신 + Unified JSON round-trip (docs/04·10, 절대규칙 16)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.models.report import (  # noqa: E402
    BirthInput,
    CalendarVerification,
    CustomerQuestion,
    UnifiedReport,
)
from sajugen.store.orders import (  # noqa: E402
    ApprovalRequired,
    IllegalTransition,
    OrderState,
    OrderStore,
)


def _report(oid: str = "") -> UnifiedReport:
    return UnifiedReport(
        order_id=oid,
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        saju={"day": {"ganzhi": "乙酉"}},
        customer_questions=[CustomerQuestion(raw="올해 이직 어떤가요?", domain="job")],
    )


@pytest.fixture
def store(tmp_path) -> OrderStore:
    return OrderStore(tmp_path / "orders.sqlite")


# ─────────────────── Unified JSON round-trip ───────────────────


def test_unified_report_roundtrip():
    r = _report("ord_x")
    again = UnifiedReport.model_validate_json(r.model_dump_json())
    assert again == r
    assert again.llm_allowed_sections == ["integration", "question_answers", "final_advice"]


# ─────────────────── 생성/조회 ───────────────────


def test_create_sets_received_and_audit(store):
    oid = store.create(_report())
    assert oid.startswith("ord_")
    assert store.get_state(oid) == OrderState.RECEIVED
    aud = store.audit(oid)
    assert aud[0].action == "create" and aud[0].to_state == "RECEIVED"
    assert store.get_report(oid).order_id == oid  # order_id 발급 반영


# ─────────────────── 정상 경로 ───────────────────


def test_happy_path_to_delivered(store):
    oid = store.create(_report())
    for to in [
        OrderState.NORMALIZED,
        OrderState.CALC_OK,
        OrderState.DRAFTED,
        OrderState.IN_REVIEW,
        OrderState.APPROVED,
    ]:
        store.transition(oid, to)
    # 발송 게이트로만 DELIVERED 진입
    called = {}
    pdf = store.issue_final_pdf(oid, lambda rep: called.setdefault("path", "out/final.pdf"))
    assert pdf == "out/final.pdf" and called["path"] == "out/final.pdf"
    assert store.get_state(oid) == OrderState.DELIVERED


# ─────────────────── 차단 전이 ───────────────────


def test_illegal_transition_blocked(store):
    oid = store.create(_report())
    with pytest.raises(IllegalTransition):
        store.transition(oid, OrderState.APPROVED)  # RECEIVED→APPROVED 불가


def test_calc_mismatch_blocks_progress(store):
    oid = store.create(_report())
    store.transition(oid, OrderState.NORMALIZED)
    store.transition(oid, OrderState.CALC_MISMATCH)
    # 불일치 상태에서 본문 진행 불가
    with pytest.raises(IllegalTransition):
        store.transition(oid, OrderState.DRAFTED)
    # 관리자 해소 → 재정규화만 허용
    store.transition(oid, OrderState.NORMALIZED)
    assert store.get_state(oid) == OrderState.NORMALIZED


def test_review_reject_returns_to_drafted(store):
    oid = store.create(_report())
    for to in [OrderState.NORMALIZED, OrderState.CALC_OK, OrderState.DRAFTED, OrderState.IN_REVIEW]:
        store.transition(oid, to)
    store.transition(oid, OrderState.DRAFTED, note="반려: 호명 오기")  # 반려 회귀
    assert store.get_state(oid) == OrderState.DRAFTED


# ─────────────────── 발송 게이트(절대규칙 16) ───────────────────


def test_final_pdf_blocked_before_approved(store):
    oid = store.create(_report())
    store.transition(oid, OrderState.NORMALIZED)
    store.transition(oid, OrderState.CALC_OK)
    store.transition(oid, OrderState.DRAFTED)
    store.transition(oid, OrderState.IN_REVIEW)
    # IN_REVIEW(승인 전)에서 발급 금지
    rendered = {"n": 0}
    with pytest.raises(ApprovalRequired):
        store.issue_final_pdf(oid, lambda rep: rendered.__setitem__("n", rendered["n"] + 1) or "x")
    assert rendered["n"] == 0  # render_fn 호출조차 안 됨
    assert store.get_state(oid) == OrderState.IN_REVIEW


# ─────────────────── audit_log 완전성 ───────────────────


def test_audit_log_records_all(store):
    oid = store.create(_report())
    store.transition(oid, OrderState.NORMALIZED)
    store.transition(oid, OrderState.CALC_OK)
    actions = [a.action for a in store.audit(oid)]
    assert actions == ["create", "transition", "transition"]
    trans = [(a.from_state, a.to_state) for a in store.audit(oid) if a.action == "transition"]
    assert trans == [("RECEIVED", "NORMALIZED"), ("NORMALIZED", "CALC_OK")]


# ─────────────────── 하드 삭제(개인정보 파기, 제21조) ───────────────────


def test_delete_destroys_pii_and_keeps_audit(store):
    oid = store.create(_report())
    # 파기 전: 조회·목록에 존재
    assert store.get_report(oid).order_id == oid
    assert any(r["order_id"] == oid for r in store.list_orders())

    store.delete(oid, actor="admin", reason="발송 완료 파기")

    # PII(report) 복구불가 파기: 조회 불가
    with pytest.raises(KeyError):
        store.get_report(oid)
    with pytest.raises(KeyError):
        store.get_state(oid)
    assert all(r["order_id"] != oid for r in store.list_orders())

    # 파기 추적 기록은 audit_log에 보존(별도 테이블) — 마지막 액션이 delete
    aud = store.audit(oid)
    assert aud and aud[-1].action == "delete"
    assert aud[-1].from_state == "RECEIVED" and aud[-1].to_state == ""
    assert aud[-1].note == "발송 완료 파기"


def test_delete_unknown_order_raises(store):
    with pytest.raises(KeyError):
        store.delete("ord_does_not_exist")
