# -*- coding: utf-8 -*-
"""T1 후속 상담 스키마 — customers와 orders additive migration 회귀."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport  # noqa: E402
from sajugen.store.orders import OrderStore  # noqa: E402


def _report(oid: str = "") -> UnifiedReport:
    return UnifiedReport(
        order_id=oid,
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        saju={"day": {"ganzhi": "乙酉"}},
    )


def _columns(store: OrderStore, table: str) -> set[str]:
    return {r[1] for r in store._conn.execute(f"PRAGMA table_info({table})").fetchall()}


def test_migration_preserves_legacy_orders_and_is_idempotent(tmp_path):
    db = tmp_path / "orders.sqlite"
    legacy = _report("ord_legacy")
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            report_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT,
            section TEXT,
            note TEXT,
            at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO orders (order_id, state, report_json, created_at, updated_at) VALUES (?,?,?,?,?)",
        ("ord_legacy", "RECEIVED", legacy.model_dump_json(), "2026-07-07T00:00:00+00:00", "2026-07-07T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    store = OrderStore(db)
    assert {"alias", "parent_order_id", "kind"} <= _columns(store, "orders")
    assert {"alias", "name_masked", "consent_at", "purged_at", "created_at"} <= _columns(store, "customers")
    rows = store.list_orders()
    assert rows[0]["order_id"] == "ord_legacy"
    assert rows[0]["kind"] == "new"
    assert rows[0]["alias"] is None and rows[0]["parent_order_id"] is None
    store.close()

    # 같은 DB를 다시 열어도 ALTER 중복으로 crash 나지 않는다.
    again = OrderStore(db)
    assert again.get_report("ord_legacy").order_id == "ord_legacy"
    again.close()


def test_customer_linking_alias_fk_and_identifier_purge(tmp_path):
    store = OrderStore(tmp_path / "orders.sqlite")
    first = store.link_customer(name_masked="MASKED_A", consent_at="2026-07-07T00:00:00+00:00")
    second = store.link_customer(name_masked="MASKED_B", consent_at="2026-07-07T00:00:01+00:00")
    assert (first, second) == ("SD-0001", "SD-0002")

    oid = store.create(_report(), alias=first, kind="followup", parent_order_id="ord_parent")
    row = next(r for r in store.list_orders() if r["order_id"] == oid)
    assert row["alias"] == first
    assert row["kind"] == "followup"
    assert row["parent_order_id"] == "ord_parent"

    with pytest.raises(sqlite3.IntegrityError):
        store.create(_report(), alias="SD-9999", kind="followup")

    store.purge_identifier(first)
    customer = store.get_customer(first)
    assert customer["name_masked"] is None
    assert customer["purged_at"]
    assert store.get_report(oid).order_id == oid
    assert next(r for r in store.list_orders() if r["order_id"] == oid)["alias"] == first


def test_link_customer_upsert_clears_purge_marker(tmp_path):
    store = OrderStore(tmp_path / "orders.sqlite")
    alias = store.link_customer("SD-0007", name_masked="MASKED_OLD")
    store.purge_identifier(alias)
    store.link_customer(alias, name_masked="MASKED_NEW", consent_at="2026-07-07T01:00:00+00:00")
    customer = store.get_customer(alias)
    assert customer["name_masked"] == "MASKED_NEW"
    assert customer["purged_at"] is None
