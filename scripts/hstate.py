# -*- coding: utf-8 -*-
"""Minimal RUN_STATE schema helper for handoff/review tooling."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "current_stage",
    "input_sha",
    "output_sha",
    "api_calls",
    "pdf_rendered",
    "retry_blocked",
    "final_status",
)


def default_state(**overrides: Any) -> dict:
    state = {
        "current_stage": "NOT_RUN",
        "input_sha": None,
        "output_sha": None,
        "api_calls": 0,
        "pdf_rendered": False,
        "retry_blocked": False,
        "final_status": "NOT_RUN",
    }
    state.update(overrides)
    return state


def validate_run_state(state: dict | None) -> dict:
    state = state or {}
    missing = [field for field in REQUIRED_FIELDS if field not in state]
    invalid: list[str] = []
    if "api_calls" in state and not isinstance(state.get("api_calls"), int):
        invalid.append("api_calls")
    for field in ("pdf_rendered", "retry_blocked"):
        if field in state and not isinstance(state.get(field), bool):
            invalid.append(field)
    return {"valid": not missing and not invalid, "missing": missing, "invalid": invalid}


def sha12_payload(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:12]


def build_run_state(
    *,
    current_stage: str,
    input_payload: Any,
    output_payload: Any,
    api_calls: int = 0,
    pdf_rendered: bool = False,
    retry_blocked: bool = False,
    final_status: str,
) -> dict:
    state = default_state(
        current_stage=current_stage,
        input_sha=sha12_payload(input_payload),
        output_sha=sha12_payload(output_payload),
        api_calls=api_calls,
        pdf_rendered=pdf_rendered,
        retry_blocked=retry_blocked,
        final_status=final_status,
    )
    result = validate_run_state(state)
    if not result["valid"]:
        raise ValueError(f"invalid RUN_STATE: {result}")
    return state


def load_state(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_state(path: str | Path, state: dict) -> dict:
    result = validate_run_state(state)
    if not result["valid"]:
        raise ValueError(f"invalid RUN_STATE: {result}")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state
