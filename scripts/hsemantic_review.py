# -*- coding: utf-8 -*-
"""PII-safe semantic/style review summary.

This tool never grants release approval. Even a zero-hit result remains
REVIEW_REQUIRED because operator full-text reading is mandatory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _total(hits: list[dict]) -> int:
    return sum(int(h.get("count", 1)) for h in hits)


def _status(*hit_groups: list[dict], ran: bool = True) -> str:
    if not ran:
        return "NOT_RUN"
    return "FAILED" if any(_total(group) for group in hit_groups) else "REVIEW_REQUIRED"


def _style_rule_id(why: str) -> str:
    from sajugen.render import verify as render_verify

    return render_verify._style_rule_id(why)


def _style_hits_for_text(text: str, page: int | None = None) -> list[dict]:
    from collections import Counter

    from sajugen.content import style_lint

    counts: Counter[str] = Counter()
    for hit in style_lint.lint(text or ""):
        counts[_style_rule_id(str(hit.get("why", "")))] += 1
    out = [
        {"type": "semantic_style", "rule": rule, "count": count}
        for rule, count in sorted(counts.items())
    ]
    if page is not None:
        for item in out:
            item["page"] = page
    return out


def _with_page(hits: list[dict], page: int | None) -> list[dict]:
    if page is None:
        return hits
    out = []
    for hit in hits:
        item = dict(hit)
        item["page"] = page
        out.append(item)
    return out


def review_text(text: str, *, page: int | None = None) -> dict:
    from sajugen.content import client_tone_lint, customer_meta_lint

    semantic_style_hits = _style_hits_for_text(text, page=page)
    ai_meta_hits = _with_page(customer_meta_lint.lint(text), page)
    placeholder_residue_hits = _with_page(client_tone_lint.placeholder_residue_lint(text), page)
    role_perspective_hits: list[dict] = []
    honorific_consistency_hits: list[dict] = []
    return {
        "semantic_review_status": _status(
            semantic_style_hits,
            ai_meta_hits,
            [
                h
                for h in placeholder_residue_hits
                if h.get("severity") == "hard"
            ],
            role_perspective_hits,
            honorific_consistency_hits,
        ),
        "operator_full_text_reading_required": True,
        "release_allowed": False,
        "semantic_style_hits": semantic_style_hits,
        "ai_meta_hits": ai_meta_hits,
        "placeholder_residue_hits": placeholder_residue_hits,
        "role_perspective_hits": role_perspective_hits,
        "honorific_consistency_hits": honorific_consistency_hits,
    }


def review_verify_result(data: dict) -> dict:
    semantic_style_hits = data.get("semantic_style_hits") or []
    ai_meta_hits = data.get("ai_meta_hits") or []
    placeholder_residue_hits = data.get("placeholder_residue_hits") or []
    role_perspective_hits = data.get("role_perspective_hits") or []
    honorific_consistency_hits = data.get("honorific_consistency_hits") or []
    return {
        "semantic_review_status": _status(
            semantic_style_hits,
            ai_meta_hits,
            [
                h
                for h in placeholder_residue_hits
                if h.get("severity") == "hard"
            ],
            role_perspective_hits,
            honorific_consistency_hits,
        ),
        "operator_full_text_reading_required": True,
        "release_allowed": False,
        "semantic_style_hits": semantic_style_hits,
        "ai_meta_hits": ai_meta_hits,
        "placeholder_residue_hits": placeholder_residue_hits,
        "role_perspective_hits": role_perspective_hits,
        "honorific_consistency_hits": honorific_consistency_hits,
    }


def review_pdf(path: str | Path) -> dict:
    import fitz

    doc = fitz.open(str(path))
    merged = {
        "semantic_style_hits": [],
        "ai_meta_hits": [],
        "placeholder_residue_hits": [],
        "role_perspective_hits": [],
        "honorific_consistency_hits": [],
    }
    for idx in range(doc.page_count):
        result = review_text(doc.load_page(idx).get_text(), page=idx + 1)
        for key in merged:
            merged[key].extend(result[key])
    doc.close()
    return review_verify_result(merged)


def not_run() -> dict:
    return {
        "semantic_review_status": "NOT_RUN",
        "operator_full_text_reading_required": True,
        "release_allowed": False,
        "semantic_style_hits": [],
        "ai_meta_hits": [],
        "placeholder_residue_hits": [],
        "role_perspective_hits": [],
        "honorific_consistency_hits": [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="PII-safe semantic/style review summary")
    ap.add_argument("--pdf", default=None)
    ap.add_argument("--text", default=None)
    ap.add_argument("--verify-json", default=None)
    args = ap.parse_args(argv)

    if args.verify_json:
        data = json.loads(Path(args.verify_json).read_text(encoding="utf-8"))
        result = review_verify_result(data)
    elif args.text:
        result = review_text(Path(args.text).read_text(encoding="utf-8"))
    elif args.pdf:
        result = review_pdf(args.pdf)
    else:
        result = not_run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["semantic_review_status"] == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
