# -*- coding: utf-8 -*-
"""P5 내부 도구화 E2E — pipeline · Typer CLI · FastAPI 폼."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient  # noqa: E402
from typer.testing import CliRunner  # noqa: E402

from sajugen import pipeline  # noqa: E402
from sajugen.app import app as fastapi_app  # noqa: E402
from sajugen.cli import app as cli_app  # noqa: E402
from playwright_guard import require_playwright_subprocess  # noqa: E402


def test_pipeline_e2e_gate_pass():
    require_playwright_subprocess()
    r = pipeline.generate(
        2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01", out_name="e2e_pipeline.pdf"
    )
    assert r.ok is True, r.reasons
    assert Path(r.pdf_path).exists()
    assert r.verify["gate_pass"] and r.verify["tagged"]
    assert r.guard["clean"] is True
    assert r.bazi == "己卯 丙子 戊午 戊午", r.bazi


def test_cli_gen_runs_and_passes():
    require_playwright_subprocess()
    res = CliRunner().invoke(
        cli_app,
        [
            "--birth",
            "2000-01-01 12:00",
            "--gender",
            "남",
            "--name",  # 필수화(운영자 지시 2026-06-12 — 호명 개인화)
            "홍길동",
            "--horoscope",
            "2026-06-01",
            "--out",
            "e2e_cli.pdf",
        ],
    )
    assert res.exit_code == 0, res.output
    assert "사주팔자:" in res.output and "PASS" in res.output


def test_fastapi_form_and_generate():
    require_playwright_subprocess()
    c = TestClient(fastapi_app)
    assert c.get("/").status_code == 200
    assert "사주풀이 PDF 생성" in c.get("/").text

    resp = c.post(
        "/generate",
        data={
            "birth": "2000-01-01 12:00",
            "gender": "male",
            "name": "홍길동",  # 필수화(운영자 지시 2026-06-12)
            "longitude": "126.978",
            "latitude": "37.566",
            "horoscope": "2026-06-01",
        },
    )
    assert resp.status_code == 200, resp.text[:300]
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.headers.get("X-Gate") == "PASS"
    assert resp.content[:5] == b"%PDF-"
