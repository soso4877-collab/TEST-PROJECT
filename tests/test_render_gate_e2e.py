# -*- coding: utf-8 -*-
"""Tier1 synthetic render-only e2e authoring.

These tests intentionally require an explicit environment opt-in because they
create PDF/HTML files through Playwright.  They are authored here for a later
Tier1 approval run and must not be executed during authoring.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import hsemantic_review  # noqa: E402
import hsummary  # noqa: E402
from sajugen import config as cfg  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402
from sajugen.render import verify as render_verify  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("SAJUGEN_TIER1_RENDER_E2E") != "1",
    reason="Tier1 render e2e requires explicit operator approval.",
)

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "synthetic_render"
FORBIDDEN_OUT_PARTS = ("sajugen/render/out", "render/out")


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _report_from_fixture(data: dict) -> SimpleNamespace:
    sections = []
    for item in data["sections"]:
        text = "\n\n".join([item["text"]] * int(item.get("repeat", 1)))
        sections.append(
            SimpleNamespace(
                id=item["id"],
                title=item["title"],
                source_keys=["synthetic"],
                final_text=text,
            )
        )
    return SimpleNamespace(sections=sections)


def _assert_tmp_only(path: str | Path, tmp_path: Path) -> Path:
    actual = Path(path).resolve()
    root = tmp_path.resolve()
    assert actual.is_relative_to(root)
    normalized = actual.as_posix()
    assert not any(part in normalized for part in FORBIDDEN_OUT_PARTS)
    return actual


def _render_and_verify(data: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out_dir = tmp_path / data["doc_id"]
    assert out_dir.is_relative_to(tmp_path)
    report = _report_from_fixture(data)
    saju = SimpleNamespace(input_civil=data["input_civil"])
    pdf_path = render_pdf.render_pdf(
        report,
        saju,
        data["out_name"],
        out_dir=out_dir,
        name="",
        brand=cfg.brand("seodam"),
    )
    pdf_file = _assert_tmp_only(pdf_path, tmp_path)
    html_file = _assert_tmp_only(out_dir / data["out_name"].replace(".pdf", ".html"), tmp_path)
    assert pdf_file.exists()
    assert html_file.exists()
    result = render_verify.verify(str(pdf_file))
    result["semantic_review"] = hsemantic_review.review_verify_result(result)
    result["tier1_summary"] = {
        "api_calls": 0,
        "llm_calls": 0,
        "customer_data_accessed": False,
        "pdf_path": "[redacted].pdf",
    }
    result["hsummary"] = hsummary.build_summary(
        {"branch": "tier1-synthetic", "preflight_ok": True},
        {"returncode": 0, "passed": None, "skipped": None},
        [dict(result, type="tier1_synthetic", pdf=str(pdf_file), status="verified")],
    )
    return result


def test_tier1_injected_render_gate_blocks_semantic_residue(tmp_path, monkeypatch):
    result = _render_and_verify(_load_fixture("injected.json"), tmp_path, monkeypatch)

    assert result["gate_pass"] is False
    assert result["customer_meta_clean"] is False
    assert result["placeholder_residue_clean"] is False
    assert result["style_clean"] is False
    assert result["semantic_review"]["semantic_review_status"] == "FAILED"
    assert "READY" not in str(result["semantic_review"])
    assert "APPROVED" not in str(result["semantic_review"])
    assert result["tier1_summary"]["api_calls"] == 0
    assert result["tier1_summary"]["llm_calls"] == 0
    assert result["tier1_summary"]["customer_data_accessed"] is False


def test_tier1_clean_render_gate_passes_with_review_required(tmp_path, monkeypatch):
    result = _render_and_verify(_load_fixture("clean.json"), tmp_path, monkeypatch)

    assert result["gate_pass"] is True, result
    assert result["semantic_review"]["semantic_review_status"] == "REVIEW_REQUIRED"
    assert result["semantic_review"]["release_allowed"] is False
    assert "READY" not in str(result["semantic_review"])
    assert "APPROVED" not in str(result["semantic_review"])
    assert result["tier1_summary"]["api_calls"] == 0
    assert result["tier1_summary"]["llm_calls"] == 0
    assert result["tier1_summary"]["customer_data_accessed"] is False
