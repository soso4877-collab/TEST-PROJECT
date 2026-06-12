# -*- coding: utf-8 -*-
"""주문 상태머신 + SQLite 영속 (docs/10, 절대규칙 16).

상태 전이(강제):
  RECEIVED → NORMALIZED → CALC_OK | CALC_MISMATCH(차단)
           → DRAFTED → IN_REVIEW → APPROVED → DELIVERED
규칙:
- 허용되지 않은 전이는 IllegalTransition 예외(물리 차단).
- CALC_MISMATCH/NEEDS_INFO 는 관리자 해소(→ NORMALIZED 재시도) 전 진행 불가.
- IN_REVIEW 반려 시 DRAFTED 로 회귀.
- **APPROVED 이전 최종 PDF 발급 함수 호출 불가** → issue_final_pdf 가 ApprovalRequired 예외.
- 모든 전이/발급은 audit_log 에 기록.
"""

from __future__ import annotations

import secrets
import sqlite3
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

from ..models.report import AuditEntry, UnifiedReport


class OrderState(str, Enum):
    RECEIVED = "RECEIVED"
    NORMALIZED = "NORMALIZED"
    CALC_OK = "CALC_OK"
    CALC_MISMATCH = "CALC_MISMATCH"
    NEEDS_INFO = "NEEDS_INFO"
    DRAFTED = "DRAFTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    DELIVERED = "DELIVERED"


# 허용 전이표 (이 외 전이는 전부 차단)
ALLOWED: dict[OrderState, set[OrderState]] = {
    OrderState.RECEIVED: {OrderState.NORMALIZED, OrderState.NEEDS_INFO},
    OrderState.NORMALIZED: {OrderState.CALC_OK, OrderState.CALC_MISMATCH},
    OrderState.CALC_OK: {OrderState.DRAFTED},
    OrderState.CALC_MISMATCH: {OrderState.NORMALIZED},  # 관리자 해소 후 재정규화
    OrderState.NEEDS_INFO: {OrderState.NORMALIZED},  # 추가정보 확보 후
    OrderState.DRAFTED: {OrderState.IN_REVIEW},
    OrderState.IN_REVIEW: {OrderState.APPROVED, OrderState.DRAFTED},  # 승인 | 반려
    OrderState.APPROVED: {OrderState.DELIVERED},
    OrderState.DELIVERED: set(),  # 종착
}


class IllegalTransition(Exception):
    """허용되지 않은 상태 전이."""


class ApprovalRequired(Exception):
    """APPROVED 이전 최종 PDF 발급 시도(절대규칙 16)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_order_id() -> str:
    """시간 정렬 가능한 주문 ID(ord_ 접두). 외부 ULID 의존 없이 ms+랜덤."""
    return f"ord_{int(time.time() * 1000):011x}{secrets.token_hex(4)}"


class OrderStore:
    """SQLite 기반 주문 저장소 + 상태머신 강제 + audit_log."""

    def __init__(self, db_path: str | Path = "data/orders.sqlite"):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        # 검수 UI: 생성 스레드(쓰기)와 화면 폴링(읽기) 동시 접근 시 잠금 대기
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id   TEXT PRIMARY KEY,
                state      TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id  TEXT NOT NULL,
                actor     TEXT NOT NULL,
                action    TEXT NOT NULL,
                from_state TEXT,
                to_state  TEXT,
                section   TEXT,
                note      TEXT,
                at        TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ───────────────── 생성/조회 ─────────────────

    def create(self, report: UnifiedReport, *, actor: str = "system") -> str:
        """주문 생성(상태 RECEIVED). report.order_id 가 비면 발급."""
        oid = report.order_id or new_order_id()
        report = report.model_copy(update={"order_id": oid})
        now = _now()
        self._conn.execute(
            "INSERT INTO orders (order_id, state, report_json, created_at, updated_at) "
            "VALUES (?,?,?,?,?)",
            (oid, OrderState.RECEIVED.value, report.model_dump_json(), now, now),
        )
        self._audit(oid, actor, "create", None, OrderState.RECEIVED, at=now)
        self._conn.commit()
        return oid

    def get_state(self, order_id: str) -> OrderState:
        row = self._conn.execute(
            "SELECT state FROM orders WHERE order_id=?", (order_id,)
        ).fetchone()
        if not row:
            raise KeyError(f"주문 없음: {order_id}")
        return OrderState(row["state"])

    def get_report(self, order_id: str) -> UnifiedReport:
        row = self._conn.execute(
            "SELECT report_json FROM orders WHERE order_id=?", (order_id,)
        ).fetchone()
        if not row:
            raise KeyError(f"주문 없음: {order_id}")
        return UnifiedReport.model_validate_json(row["report_json"])

    def save_report(self, order_id: str, report: UnifiedReport, *, actor: str = "admin") -> None:
        """본문 수정 등 report 갱신(상태 불변). audit 기록."""
        self._conn.execute(
            "UPDATE orders SET report_json=?, updated_at=? WHERE order_id=?",
            (report.model_dump_json(), _now(), order_id),
        )
        self._audit(order_id, actor, "save_report", None, None)
        self._conn.commit()

    def list_orders(self, state: OrderState | None = None) -> list[dict]:
        """주문 목록(최신순) — 검수 UI 목록 화면용 요약."""
        q = (
            "SELECT order_id, state, created_at, updated_at, "
            "json_extract(report_json,'$.birth.name') AS name, "
            "json_extract(report_json,'$.birth.input_date') AS input_date, "
            "json_extract(report_json,'$.safety_flags.needs_review') AS needs_review "
            "FROM orders"
        )
        args: tuple = ()
        if state is not None:
            q += " WHERE state=?"
            args = (state.value,)
        q += " ORDER BY created_at DESC, order_id DESC"
        return [dict(r) for r in self._conn.execute(q, args).fetchall()]

    def add_audit(
        self,
        order_id: str,
        *,
        action: str,
        actor: str = "system",
        section: str = "",
        note: str = "",
    ) -> None:
        """상태 전이 없는 감사 기록(생성 실패·섹션 수정 등)."""
        self.get_state(order_id)  # 존재 확인(없으면 KeyError)
        self._audit(order_id, actor, action, None, None, section=section, note=note)
        self._conn.commit()

    # ───────────────── 상태 전이 ─────────────────

    def transition(
        self, order_id: str, to_state: OrderState, *, actor: str = "admin", note: str = ""
    ) -> OrderState:
        """상태 전이(검증 + audit). 허용 외 전이는 IllegalTransition."""
        cur = self.get_state(order_id)
        if to_state not in ALLOWED.get(cur, set()):
            raise IllegalTransition(
                f"{cur.value} → {to_state.value} 불가 (허용: "
                f"{sorted(s.value for s in ALLOWED.get(cur, set()))})"
            )
        now = _now()
        self._conn.execute(
            "UPDATE orders SET state=?, updated_at=? WHERE order_id=?",
            (to_state.value, now, order_id),
        )
        self._audit(order_id, actor, "transition", cur, to_state, note=note, at=now)
        self._conn.commit()
        return to_state

    # ───────────────── 발송 게이트(절대규칙 16) ─────────────────

    def issue_final_pdf(
        self, order_id: str, render_fn: Callable[[UnifiedReport], str], *, actor: str = "admin"
    ) -> str:
        """최종 PDF 발급 — 상태가 APPROVED 일 때만. 그 외엔 ApprovalRequired 예외.

        render_fn(report) → pdf_path. 성공 시 APPROVED → DELIVERED 전이.
        """
        state = self.get_state(order_id)
        if state != OrderState.APPROVED:
            raise ApprovalRequired(
                f"APPROVED 이전 최종 PDF 발급 금지(현재 {state.value}) — 절대규칙 16"
            )
        report = self.get_report(order_id)
        pdf_path = render_fn(report)
        self._audit(order_id, actor, "issue_final_pdf", None, None, note=pdf_path)
        self.transition(order_id, OrderState.DELIVERED, actor=actor, note="final pdf issued")
        return pdf_path

    # ───────────────── audit ─────────────────

    def _audit(
        self,
        order_id: str,
        actor: str,
        action: str,
        from_state: OrderState | None,
        to_state: OrderState | None,
        *,
        section: str = "",
        note: str = "",
        at: str | None = None,
    ) -> None:
        self._conn.execute(
            "INSERT INTO audit_log (order_id, actor, action, from_state, to_state, section, note, at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                order_id,
                actor,
                action,
                from_state.value if from_state else None,
                to_state.value if to_state else None,
                section,
                note,
                at or _now(),
            ),
        )

    def audit(self, order_id: str) -> list[AuditEntry]:
        rows = self._conn.execute(
            "SELECT actor, action, from_state, to_state, section, note, at "
            "FROM audit_log WHERE order_id=? ORDER BY id",
            (order_id,),
        ).fetchall()
        return [
            AuditEntry(
                actor=r["actor"],
                action=r["action"],
                from_state=r["from_state"] or "",
                to_state=r["to_state"] or "",
                section=r["section"] or "",
                note=r["note"] or "",
                at=r["at"],
            )
            for r in rows
        ]
