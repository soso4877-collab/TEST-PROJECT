# -*- coding: utf-8 -*-
"""T4.5/E-1: /generate 구형경로 PII 제거 — 다운로드 파일명에 생년월일 미포함 +
X-Saju-Bazi(사주팔자) 응답 헤더 제거. 비-PII 헤더(X-Gate/X-Pages)는 유지."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from sajugen import app as app_mod  # noqa: E402
from sajugen.pipeline import GenResult  # noqa: E402
from sajugen.store.orders import OrderState, OrderStore  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    # generate 를 대체 — out_name(app.py 가 정한 파일명)을 그대로 pdf_path 로 반영해
    # FileResponse 다운로드 파일명이 app.py 의 out_name 규칙을 타게 한다(Playwright 무실행).
    def _fake_generate(*_a, out_name="saju.pdf", **_k):
        p = tmp_path / out_name
        p.write_bytes(b"%PDF-1.7 fake")
        return GenResult(
            pdf_path=str(p),
            ok=True,
            reasons=[],
            verify={"gate_pass": True, "pages": 10, "text_chars": 2000, "tagged": True},
            guard={"clean": True},
            bazi="庚午 辛巳 庚午 癸未",
        )

    monkeypatch.setattr(app_mod, "generate", _fake_generate)
    return TestClient(app_mod.app)


_FORM = {"birth": "1990-05-20 14:30", "name": "홍길동", "gender": "male", "brand": "seodam"}


def test_generate_form_exposes_integrated_full_product(client):
    r = client.get("/")
    assert r.status_code == 200
    assert '<option value="integrated_full">' in r.text
    for field in (
        "partner_name",
        "partner_birth",
        "partner_lunar",
        "partner_leap",
        "partner_gender",
    ):
        assert f'name="{field}"' in r.text


def test_generate_integrated_full_creates_waiting_order(client, tmp_path, monkeypatch):
    db = tmp_path / "integrated-full-app.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(db))
    r = client.post(
        "/generate",
        data={
            "birth": "2000-01-01 12:00",
            "name": "DOC_A",
            "gender": "male",
            "product": "integrated_full",
            "concern": "이직 준비 순서가 궁금합니다.",
            "brand": "default",
        },
        follow_redirects=False,
    )

    assert r.status_code == 303
    order_id = r.headers["location"].rstrip("/").split("/")[-1]
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
        assert store.get_state(order_id) == OrderState.NORMALIZED
        assert report.render_meta["gen_params"]["modules"] == []
        assert "partner" not in report.render_meta["gen_params"]
        assert report.render_meta["question_category"]["value"] == "직업"
        blocked = [entry for entry in store.audit(order_id) if entry.action == "generation_blocked"]
        assert len(blocked) == 1
    finally:
        store.close()


def test_generate_integrated_full_unknown_time_returns_422_without_order(
    client, tmp_path, monkeypatch
):
    db = tmp_path / "integrated-full-unknown-app.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(db))
    r = client.post(
        "/generate",
        data={
            "birth": "2000-01-01",
            "name": "DOC_A",
            "gender": "male",
            "product": "integrated_full",
            "brand": "default",
        },
        follow_redirects=False,
    )

    assert r.status_code == 422
    store = OrderStore(db)
    try:
        assert store.list_orders() == []
    finally:
        store.close()


def test_generate_integrated_full_partner_creates_waiting_two_person_order(
    client, tmp_path, monkeypatch
):
    db = tmp_path / "integrated-full-partner-app.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(db))

    response = client.post(
        "/generate",
        data={
            "birth": "2000-01-01 12:00",
            "name": "DOC_A",
            "gender": "male",
            "partner_name": "DOC_B",
            "partner_birth": "2001-02-02 13:30",
            "partner_gender": "female",
            "product": "integrated_full",
            "brand": "default",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    order_id = response.headers["location"].rstrip("/").split("/")[-1]
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
        assert store.get_state(order_id) == OrderState.NORMALIZED
        assert report.render_meta["gen_params"]["partner"] == {
            "name": "DOC_B",
            "year": 2001,
            "month": 2,
            "day": 2,
            "hour": 13,
            "minute": 30,
            "is_male": False,
            "is_leap": False,
        }
        blocked = [
            entry
            for entry in store.audit(order_id)
            if entry.action == "generation_blocked"
        ]
        assert blocked and blocked[-1].note == "integrated_full modules unconfirmed"
    finally:
        store.close()


def test_generate_rejects_unknown_partner_time_without_echoing_birth(
    client, tmp_path, monkeypatch
):
    db = tmp_path / "integrated-full-partner-unknown-app.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(db))
    partner_birth = "2001-02-02"

    response = client.post(
        "/generate",
        data={
            "birth": "2000-01-01 12:00",
            "name": "DOC_A",
            "partner_name": "DOC_B",
            "partner_birth": partner_birth,
            "partner_gender": "female",
            "product": "integrated_full",
            "brand": "default",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert partner_birth not in response.text
    store = OrderStore(db)
    try:
        assert store.list_orders() == []
    finally:
        store.close()


def test_generate_rejects_partner_for_legacy_product_before_pdf(client, monkeypatch):
    def forbidden_generate(*args, **kwargs):
        raise AssertionError("legacy product must reject partner before generation")

    monkeypatch.setattr(app_mod, "generate", forbidden_generate)

    response = client.post(
        "/generate",
        data={
            **_FORM,
            "partner_name": "DOC_B",
            "partner_birth": "2001-02-02 13:30",
            "partner_gender": "female",
        },
    )

    assert response.status_code == 422
    assert "only supported for integrated_full" in response.text


def test_generate_filename_has_no_birthdate(client):
    r = client.post("/generate", data=_FORM)
    assert r.status_code == 200
    cd = r.headers.get("content-disposition", "")
    # 생년월일 파생 문자열(YYYYMMDD·연도·시각) 미포함
    assert "19900520" not in cd and "1990" not in cd and "1430" not in cd, cd
    assert re.search(r"saju_[0-9a-f]{12}\.pdf", cd), cd  # 비-DOB 무작위 파일명


def test_generate_removes_bazi_header_keeps_nonpii(client):
    r = client.post("/generate", data=_FORM)
    assert r.status_code == 200
    assert "X-Saju-Bazi" not in r.headers  # 사주팔자 헤더 제거
    assert r.headers.get("X-Gate") == "PASS"  # 비-PII 헤더는 유지
    assert r.headers.get("X-Pages") == "10"
