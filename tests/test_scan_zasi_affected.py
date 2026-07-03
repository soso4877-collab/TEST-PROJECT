# -*- coding: utf-8 -*-
"""T2.1 자시 영향 스캔 도구 회귀 — 진태양시 23~24시(day_offset=1) 주문만 식별, PII 미출력."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import scan_zasi_affected  # noqa: E402

from sajugen import order_flow  # noqa: E402


def test_scan_flags_only_zasi_affected(tmp_path):
    db = str(tmp_path / "orders.sqlite")
    # 진태양시 23:11(day_offset=1, 영향) vs 14:01(day_offset=0, 무영향)
    oid_aff, _ = order_flow.create_order(
        birth="1990-05-20 23:40", name="가나", brand="seodam", db_path=db
    )
    oid_ok, _ = order_flow.create_order(
        birth="1990-05-20 14:30", name="다라", brand="seodam", db_path=db
    )

    res = scan_zasi_affected.scan(db)
    ids = {r["order_id"] for r in res}
    assert oid_aff in ids  # 자시 영향 주문 식별
    assert oid_ok not in ids  # 무영향 주문 제외


def test_scan_output_is_pii_free(tmp_path):
    db = str(tmp_path / "orders.sqlite")
    order_flow.create_order(birth="1990-05-20 23:50", name="홍길동", brand="seodam", db_path=db)
    res = scan_zasi_affected.scan(db)
    # 필드 화이트리스트: order_id/state/day_offset/error 만
    assert all(set(r) <= {"order_id", "state", "day_offset", "error"} for r in res)
    # 이름·생년월일 미노출
    assert "홍길동" not in str(res) and "1990" not in str(res) and "23:50" not in str(res)
    assert res and res[0]["day_offset"] == 1
