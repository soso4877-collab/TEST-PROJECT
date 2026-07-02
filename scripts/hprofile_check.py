# -*- coding: utf-8 -*-
"""PII-free harness profile preflight.

This tool validates profile shape for the operator without printing customer
values. It is safe to run on local profiles because it reports only field names,
counts, booleans, basenames, and short hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    profile = yaml.safe_load(raw.decode("utf-8")) or {}
    if not isinstance(profile, dict):
        raise ValueError("profile root must be a mapping")
    return profile, raw


def _birth_shape(value: Any) -> bool:
    parts = str(value or "").strip().split()
    if not parts:
        return False
    date = parts[0].split("-")
    if len(date) != 3 or not all(x.isdigit() for x in date):
        return False
    if len(parts) > 1:
        time = parts[1].split(":")
        if len(time) != 2 or not all(x.isdigit() for x in time):
            return False
    return True


def check_profile(path: str | os.PathLike[str]) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    profile, raw = _load(p)

    missing: list[str] = []
    warnings: list[str] = []
    profile_type = profile.get("type")
    if profile_type != "integrated_full":
        warnings.append("type_not_integrated_full")

    for key in ("type", "pdf", "ref_year", "receiver", "people"):
        if key not in profile:
            missing.append(key)

    people = profile.get("people") or []
    if not isinstance(people, list):
        people = []
        missing.append("people[]")

    people_count = len(people)
    people_missing: list[str] = []
    birth_shape_ok = True
    names: list[str] = []
    for idx, person in enumerate(people):
        if not isinstance(person, dict):
            people_missing.append(f"people[{idx}]")
            birth_shape_ok = False
            continue
        for key in ("name", "birth", "gender"):
            if key not in person:
                people_missing.append(f"people[{idx}].{key}")
        if "name" in person:
            names.append(str(person["name"]))
        if not _birth_shape(person.get("birth")):
            birth_shape_ok = False

    receiver = str(profile.get("receiver") or "")
    receiver_in_people = bool(receiver and receiver in names)
    if not receiver_in_people:
        warnings.append("receiver_not_in_people")

    pdf = str(profile.get("pdf") or "")
    if pdf and Path(pdf).name != Path(pdf).name.replace("\\", "/").split("/")[-1]:
        warnings.append("pdf_path_unusual")
    if pdf and not pdf.endswith(".pdf"):
        warnings.append("pdf_not_pdf")

    ok = (
        not missing
        and not people_missing
        and profile_type == "integrated_full"
        and people_count == 2
        and receiver_in_people
        and birth_shape_ok
        and bool(pdf)
    )

    return {
        "ok": ok,
        "profile_basename": p.name,
        "profile_sha12": _sha12(raw),
        "type": profile_type,
        "people_count": people_count,
        "receiver_in_people": receiver_in_people,
        "birth_shape_ok": birth_shape_ok,
        "pdf_basename": Path(pdf).name if pdf else "",
        "missing": missing,
        "people_missing": people_missing,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="PII-free integrated_full profile preflight")
    ap.add_argument("profile", help="harness profile path")
    args = ap.parse_args(argv)
    result = check_profile(args.profile)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
