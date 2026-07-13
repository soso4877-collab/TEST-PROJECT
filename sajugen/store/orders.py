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

from ..content import unknown_time_policy
from ..input.birth_time import BirthTimeMode, normalize_birth_time_mode
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


class BirthTimeProvenanceRequired(RuntimeError):
    """생시 미상 주문의 삼주 provenance가 없거나 계약과 다를 때 최종 발급 차단."""


def report_birth_time_mode(report: UnifiedReport) -> BirthTimeMode:
    """신규 enum을 우선하고 레거시 ``unknown_time``을 호환 읽기한다.

    새 주문의 정본은 ``render_meta.gen_params.birth_time_mode``다. 후속 PDF는
    ``render_meta.followup.birth_time_mode``를 사용한다. 두 키가 없는 과거 주문은
    저장된 birth_time과 legacy boolean으로만 분류하며, unknown이면 provenance
    검증에서 최종 발급이 차단된다.
    """

    meta = dict(report.render_meta or {})
    params = dict(meta.get("gen_params") or {})
    followup = dict(meta.get("followup") or {})
    explicit = params.get("birth_time_mode", followup.get("birth_time_mode"))
    has_stored_clock = "hour" in params and "minute" in params
    legacy_unknown_flag = bool(params.get("unknown_time") or followup.get("unknown_time"))
    # 레거시 주문은 gen_params의 시각 필드와 unknown_time이 실제 정본이었다. 초기
    # 저장본에서 BirthInput.birth_time이 비어 있어도 clock+unknown_time=False면 known으로
    # 복원하고, unknown_time=True면 정오 값이 남아 있어도 three_pillar로 분류한다.
    legacy_unknown = legacy_unknown_flag or (
        explicit is None and not has_stored_clock and report.birth.birth_time is None
    )
    # 알려진 시각 문자열의 실제 값은 최종 발급 모드 판정에 필요하지 않다. 존재 여부만
    # normalize 계약의 hour 힌트로 전달해 PII를 새 변수·로그에 복제하지 않는다.
    hour_hint = 0 if has_stored_clock or report.birth.birth_time is not None else None
    return normalize_birth_time_mode(
        explicit,
        unknown_time=True if legacy_unknown else None,
        hour=hour_hint,
    )


def three_pillar_provenance_error(provenance: object) -> str | None:
    """공용 pure validator를 재사용하고 PII-free 고정 오류 코드만 반환한다."""

    if provenance is None:
        return "provenance_missing"
    hits = unknown_time_policy.provenance_contract_lint(
        provenance,
        birth_time_mode=BirthTimeMode.THREE_PILLAR.value,
        source="order_store",
    )
    if not hits:
        return None
    rule = str(hits[0].get("rule") or "provenance")
    return {
        "schema_version": "schema_version_invalid",
        "candidate_count": "candidate_count_invalid",
        "candidate_digest": "candidate_digest_invalid",
        "stable_fact_ids": "stable_fact_ids_invalid",
        "stable_fact_ids_duplicate": "stable_fact_ids_invalid",
        "suppressed_fact_ids": "suppressed_fact_ids_invalid",
        "suppressed_fact_ids_duplicate": "suppressed_fact_ids_invalid",
        "fact_id_overlap": "fact_id_overlap",
    }.get(rule, "provenance_invalid")


def final_birth_time_contract_error(report: UnifiedReport) -> str | None:
    """최종 발급 직전 출생시각·provenance 계약의 위반 코드를 반환한다.

    알려진 시각 경로는 기존 동작을 유지한다. 삼주 경로는 정오 추정 잔재나 provenance
    결손을 하나라도 발견하면 fail-closed한다.
    """

    try:
        mode = report_birth_time_mode(report)
    except (TypeError, ValueError):
        return "birth_time_mode_invalid"
    if mode is BirthTimeMode.KNOWN:
        return None

    meta = dict(report.render_meta or {})
    params = dict(meta.get("gen_params") or {})
    if report.birth.birth_time is not None:
        return "three_pillar_birth_time_present"
    if "hour" in params or "minute" in params:
        return "three_pillar_clock_fields_present"
    return three_pillar_provenance_error(meta.get("three_pillar_provenance"))


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
        # 후속 상담용 customers.alias 참조 무결성. 기존 NULL alias 주문은 영향 없다.
        self._conn.execute("PRAGMA foreign_keys=ON")
        # WAL: 쓰기 중에도 읽기 허용(생성 스레드 쓰기 + 화면 폴링 읽기 동시성 개선).
        # synchronous=NORMAL: WAL 과 함께 안전(전원 손실 외 내구성 유지) — 내부 도구에 적정(T5.5/C-4).
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                alias       TEXT PRIMARY KEY,
                name_masked TEXT,
                consent_at  TEXT,
                purged_at   TEXT,
                created_at  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                order_id   TEXT PRIMARY KEY,
                state      TEXT NOT NULL,
                report_json TEXT NOT NULL,
                alias      TEXT REFERENCES customers(alias),
                parent_order_id TEXT,
                kind       TEXT DEFAULT 'new',
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
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(orders)")}
        for name, ddl in (
            ("alias", "TEXT REFERENCES customers(alias)"),
            ("parent_order_id", "TEXT"),
            ("kind", "TEXT DEFAULT 'new'"),
        ):
            if name not in cols:
                self._conn.execute(f"ALTER TABLE orders ADD COLUMN {name} {ddl}")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ───────────────── 생성/조회 ─────────────────

    def create(
        self,
        report: UnifiedReport,
        *,
        actor: str = "system",
        alias: str | None = None,
        parent_order_id: str | None = None,
        kind: str = "new",
    ) -> str:
        """주문 생성(상태 RECEIVED). report.order_id 가 비면 발급."""
        oid = report.order_id or new_order_id()
        report = report.model_copy(update={"order_id": oid})
        now = _now()
        self._conn.execute(
            "INSERT INTO orders "
            "(order_id, state, report_json, alias, parent_order_id, kind, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                oid,
                OrderState.RECEIVED.value,
                report.model_dump_json(),
                alias,
                parent_order_id,
                kind or "new",
                now,
                now,
            ),
        )
        self._audit(oid, actor, "create", None, OrderState.RECEIVED, at=now)
        self._conn.commit()
        return oid

    def _next_customer_alias(self) -> str:
        """현재 customers 테이블 상태만으로 다음 단골번호를 결정한다. PII를 채번에 쓰지 않는다."""
        rows = self._conn.execute("SELECT alias FROM customers WHERE alias GLOB 'SD-[0-9]*'").fetchall()
        nums: list[int] = []
        for row in rows:
            tail = str(row["alias"])[3:]
            if tail.isdigit():
                nums.append(int(tail))
        return f"SD-{(max(nums) + 1) if nums else 1:04d}"

    def link_customer(
        self,
        alias: str | None = None,
        *,
        name_masked: str | None = None,
        consent_at: str | None = None,
    ) -> str:
        """단골 별칭을 생성/갱신한다. 식별자는 마스킹본만 받고, 원문 PII는 저장하지 않는다."""
        alias = (alias or "").strip() or self._next_customer_alias()
        now = _now()
        self._conn.execute(
            """
            INSERT INTO customers (alias, name_masked, consent_at, purged_at, created_at)
            VALUES (?, ?, ?, NULL, ?)
            ON CONFLICT(alias) DO UPDATE SET
                name_masked=excluded.name_masked,
                consent_at=COALESCE(excluded.consent_at, customers.consent_at),
                purged_at=CASE
                    WHEN excluded.name_masked IS NOT NULL THEN NULL
                    ELSE customers.purged_at
                END
            """,
            (alias, name_masked, consent_at or now, now),
        )
        self._conn.commit()
        return alias

    def get_customer(self, alias: str) -> dict:
        """단골 메타 조회. 이름 원문은 없고 name_masked 만 반환된다."""
        row = self._conn.execute("SELECT * FROM customers WHERE alias=?", (alias,)).fetchone()
        if not row:
            raise KeyError(f"단골 없음: {alias}")
        return dict(row)

    def find_customers(
        self, *, alias: str | None = None, name_masked: str | None = None
    ) -> list[dict]:
        """단골 검색. 최근 주문 메타를 함께 반환하되, 이름은 마스킹 저장값만 노출한다."""
        q = (
            "SELECT c.alias, c.name_masked, c.consent_at, c.purged_at, c.created_at, "
            "o.order_id AS latest_order_id, o.kind AS latest_kind, o.created_at AS latest_order_created_at "
            "FROM customers c "
            "LEFT JOIN orders o ON o.order_id = ("
            "  SELECT oo.order_id FROM orders oo WHERE oo.alias=c.alias "
            "  ORDER BY oo.created_at DESC, oo.order_id DESC LIMIT 1"
            ")"
        )
        where: list[str] = []
        args: list[str] = []
        if alias:
            where.append("c.alias=?")
            args.append(alias)
        if name_masked:
            where.append("c.name_masked LIKE ?")
            args.append(f"%{name_masked}%")
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY c.created_at DESC, c.alias DESC"
        return [dict(r) for r in self._conn.execute(q, tuple(args)).fetchall()]

    def latest_order_for_alias(self, alias: str) -> str:
        """단골 별칭의 최신 주문 ID. 후속 답변의 부모 주문 선택에 사용한다."""
        row = self._conn.execute(
            "SELECT order_id FROM orders WHERE alias=? ORDER BY created_at DESC, order_id DESC LIMIT 1",
            (alias,),
        ).fetchone()
        if not row:
            raise KeyError(f"단골 주문 없음: {alias}")
        return str(row["order_id"])

    def purge_identifier(self, alias: str) -> None:
        """단골 식별자만 파기한다. alias 와 기존 주문/report_json 은 보존한다."""
        now = _now()
        cur = self._conn.execute(
            "UPDATE customers SET name_masked=NULL, purged_at=? WHERE alias=?",
            (now, alias),
        )
        if cur.rowcount == 0:
            raise KeyError(f"단골 없음: {alias}")
        self._conn.commit()

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
            "alias, parent_order_id, COALESCE(kind, 'new') AS kind, "
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

    def delete(self, order_id: str, *, actor: str = "admin", reason: str = "") -> None:
        """주문 하드 삭제 — PII(생년월일·출생지·고민 원문) 복구불가 파기.
        개인정보보호법 제21조(보유기간 경과·목적 달성 시 지체 없이 파기) 이행 경로.
        파기 전 audit_log에 'delete'를 기록하되, audit에는 PII를 남기지 않는다
        (order_id·actor·사유·시각만 — reason에 개인정보 기재 금지). audit_log는 별도
        테이블이라 orders 행 삭제 후에도 파기 추적 기록은 보존된다."""
        cur = self.get_state(order_id)  # 존재 확인(없으면 KeyError)
        # docstring 권고를 코드로 강제(T1.3/E-2): reason 에 생년월일이 섞여도 audit 에 남지 않게 마스킹.
        from ..content import masking

        self._audit(
            order_id, actor, "delete", cur, None, note=masking.mask_birth_in_text(reason, None)
        )
        self._conn.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
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
        contract_error = final_birth_time_contract_error(report)
        if contract_error:
            # 고객 입력·본문은 오류에 넣지 않는다. 레거시 정오 추정 주문도 새 삼주
            # provenance 없이 조용히 재발급되지 않도록 render_fn 호출 전에 차단한다.
            raise BirthTimeProvenanceRequired(
                f"생시 미상 주문 최종 발급 차단({contract_error}) — 새 삼주 정책으로 재생성 필요"
            )
        pdf_path = render_fn(report)
        self._audit(order_id, actor, "issue_final_pdf", None, None, note=pdf_path)
        self.transition(order_id, OrderState.DELIVERED, actor=actor, note="final pdf issued")
        return pdf_path

    def issue_final_text(self, order_id: str, *, actor: str = "admin") -> str:
        """후속 텍스트 발급 — APPROVED 일 때만. 승인 전에는 ApprovalRequired 예외."""
        state = self.get_state(order_id)
        if state != OrderState.APPROVED:
            raise ApprovalRequired(
                f"APPROVED 이전 최종 텍스트 발급 금지(현재 {state.value}) — 절대규칙 16"
            )
        report = self.get_report(order_id)
        contract_error = final_birth_time_contract_error(report)
        if contract_error:
            raise BirthTimeProvenanceRequired(
                f"생시 미상 주문 최종 발급 차단({contract_error}) — 새 삼주 정책으로 재생성 필요"
            )
        text = str(report.derived_interpretation.get("followup_answer") or "").strip()
        if not text:
            for q in report.customer_questions:
                if q.answer_text.strip():
                    text = q.answer_text.strip()
                    break
        if not text:
            raise KeyError(f"후속 답변 없음: {order_id}")
        self._audit(order_id, actor, "issue_final_text", None, None, note=f"{len(text)}자")
        self.transition(order_id, OrderState.DELIVERED, actor=actor, note="final text issued")
        return text

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
