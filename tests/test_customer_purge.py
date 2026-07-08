# -*- coding: utf-8 -*-
"""customer-purge CLI — E9 식별자 차등 파기 실행 경로 회귀."""

import sys
from pathlib import Path

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.cli import app as cli_app  # noqa: E402
from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport  # noqa: E402
from sajugen.store.orders import OrderStore  # noqa: E402


def _report() -> UnifiedReport:
    return UnifiedReport(
        order_id="",
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        saju={"day": {"ganzhi": "乙酉"}},
        content={"sections": []},
    )


def _seed(db: Path) -> tuple[str, str]:
    store = OrderStore(db)
    try:
        alias = store.link_customer("SD-0007", name_masked="MASKED_CUSTOMER")
        order_id = store.create(_report(), alias=alias, kind="new")
        return alias, order_id
    finally:
        store.close()


def _customer(db: Path, alias: str) -> dict:
    store = OrderStore(db)
    try:
        return store.get_customer(alias)
    finally:
        store.close()


def _orders(db: Path) -> list[dict]:
    store = OrderStore(db)
    try:
        return store.list_orders()
    finally:
        store.close()


def test_customer_purge_yes_removes_identifier_only_and_preserves_report(tmp_path):
    db = tmp_path / "orders.sqlite"
    alias, order_id = _seed(db)

    result = CliRunner().invoke(cli_app, ["customer-purge", "--alias", alias, "--yes", "--db", str(db)])

    assert result.exit_code == 0, result.output
    assert "식별자 파기 완료" in result.output
    assert alias in result.output
    assert "MASKED_CUSTOMER" not in result.output

    customer = _customer(db, alias)
    assert customer["name_masked"] is None
    assert customer["purged_at"]

    rows = _orders(db)
    assert len(rows) == 1
    assert rows[0]["order_id"] == order_id
    assert rows[0]["alias"] == alias

    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
    finally:
        store.close()
    assert report.saju["day"]["ganzhi"] == "乙酉"


def test_customer_purge_prompts_without_yes(tmp_path):
    db = tmp_path / "orders.sqlite"
    alias, _order_id = _seed(db)

    result = CliRunner().invoke(
        cli_app,
        ["customer-purge", "--alias", alias, "--db", str(db)],
        input="y\n",
    )

    assert result.exit_code == 0, result.output
    assert "식별자만 파기할까요" in result.output
    assert _customer(db, alias)["name_masked"] is None


def test_customer_purge_missing_alias_exits_one(tmp_path):
    db = tmp_path / "orders.sqlite"
    _seed(db)

    result = CliRunner().invoke(
        cli_app,
        ["customer-purge", "--alias", "SD-9999", "--yes", "--db", str(db)],
    )

    assert result.exit_code == 1
    assert "단골 없음" in result.output
    assert _orders(db)
