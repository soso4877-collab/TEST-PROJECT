# -*- coding: utf-8 -*-
"""Opt-in integrated_full synthetic render e2e.

This test creates HTML/PDF through Playwright only when the operator explicitly
sets SAJUGEN_INTEGRATED_RENDER_E2E=1. Unit tests in test_integrated_product.py
cover mocked contracts; this file is the real pagination gate for integrated_full.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import hsemantic_review  # noqa: E402
from sajugen import integrated  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.environ.get("SAJUGEN_INTEGRATED_RENDER_E2E") != "1",
    reason="integrated_full render e2e requires explicit operator approval.",
)

FORBIDDEN_OUT_PARTS = ("sajugen/render/out", "render/out")


def _assert_tmp_only(path: str | Path, tmp_path: Path) -> Path:
    actual = Path(path).resolve()
    root = tmp_path.resolve()
    assert actual.is_relative_to(root)
    normalized = actual.as_posix()
    assert not any(part in normalized for part in FORBIDDEN_OUT_PARTS)
    return actual


def test_integrated_full_synthetic_render_gate_passes(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out_dir = tmp_path / "integrated_full"
    out_name = "integrated_full_synthetic.pdf"

    result = integrated.build_integrated_full(
        [
            ("합성갑", (1990, 1, 1, 10, 0), True),
            ("합성을", (1991, 2, 2, 11, 0), False),
        ],
        receiver_name="합성갑",
        situation="",
        ref_year=2026,
        out_name=out_name,
        brand="sajudoryeong",
        use_llm=False,
        render=True,
        out_dir=out_dir,
    )

    pdf_path = _assert_tmp_only(result["pdf_path"], tmp_path)
    html_path = _assert_tmp_only(out_dir / out_name.replace(".pdf", ".html"), tmp_path)
    assert pdf_path.exists()
    assert html_path.exists()

    verify = result["verify"]
    assert verify["gate_pass"] is True, verify
    assert verify["delivery_quality_clean"] is True, verify.get("delivery_quality")
    assert verify["style_clean"] is True, verify.get("semantic_style_hits")
    assert verify["customer_meta_clean"] is True, verify.get("ai_meta_hits")
    assert verify["placeholder_residue_clean"] is True, verify.get("placeholder_residue_hits")
    assert verify["role_perspective_clean"] is True, verify.get("role_perspective_hits")
    assert verify["honorific_consistency_clean"] is True, verify.get("honorific_consistency_hits")

    review = hsemantic_review.review_verify_result(verify)
    assert review["semantic_review_status"] == "REVIEW_REQUIRED"
    assert review["release_allowed"] is False
    assert "READY" not in str(review)
    assert "APPROVED" not in str(review)
