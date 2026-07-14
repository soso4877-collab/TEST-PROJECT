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
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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


def module_contract(profile: dict[str, Any]) -> dict[str, Any]:
    """프로파일의 integrated_full 모듈 증거를 PII 없이 검증한다.

    ``modules``가 없는 프로파일은 선택 기능 이전의 레거시 계약이므로 세 verify 인자를
    모두 ``None``으로 유지한다. 반대로 ``modules``를 명시한 프로파일은 저장 주문에서
    가져온 두 커버리지 증거와 현재 스키마 버전을 함께 갖춰야 한다. 이 경계에서 누락을
    레거시 5모듈 값으로 보정하면 잘못된 30쪽 하한이 적용되므로 오류 코드로 닫는다.
    """
    from sajugen import modules as integrated_modules

    explicit = "modules" in profile
    if not explicit:
        return {
            "ok": True,
            "explicit": False,
            "selected_modules": None,
            "module_sections": None,
            "premerge_section_ids": None,
            "module_schema_version": None,
            "errors": [],
        }

    errors: list[str] = []
    selected_modules: list[str] | None = None
    raw_modules = profile.get("modules")
    if not isinstance(raw_modules, list):
        errors.append("modules_not_list")
    else:
        try:
            selected_modules = list(integrated_modules.normalize_modules(raw_modules))
        except (TypeError, ValueError):
            errors.append("modules_invalid")

    if profile.get("type") != "integrated_full":
        errors.append("modules_unsupported_profile_type")

    module_sections: dict[str, list[str]] | None = None
    raw_sections = profile.get("module_sections")
    if "module_sections" not in profile:
        errors.append("module_sections_missing")
    elif not isinstance(raw_sections, dict):
        errors.append("module_sections_invalid")
    else:
        section_shape_ok = True
        normalized_sections: dict[str, list[str]] = {}
        for module_id, section_ids in raw_sections.items():
            if not isinstance(module_id, str) or not module_id.strip():
                section_shape_ok = False
                continue
            if not isinstance(section_ids, list) or not all(
                isinstance(section_id, str) and bool(section_id.strip())
                for section_id in section_ids
            ):
                section_shape_ok = False
                continue
            normalized_sections[module_id.strip()] = [section_id.strip() for section_id in section_ids]
        if not section_shape_ok:
            errors.append("module_sections_invalid")
        elif not any(normalized_sections.values()):
            errors.append("module_sections_empty")
        else:
            module_sections = normalized_sections

    premerge_section_ids: list[str] | None = None
    raw_premerge = profile.get("premerge_section_ids")
    if "premerge_section_ids" not in profile:
        errors.append("premerge_section_ids_missing")
    elif not isinstance(raw_premerge, list) or not all(
        isinstance(section_id, str) and bool(section_id.strip()) for section_id in raw_premerge
    ):
        errors.append("premerge_section_ids_invalid")
    elif not raw_premerge:
        errors.append("premerge_section_ids_empty")
    else:
        premerge_section_ids = [section_id.strip() for section_id in raw_premerge]

    schema_version = profile.get("module_schema_version")
    if "module_schema_version" not in profile:
        errors.append("module_schema_version_missing")
    elif type(schema_version) is not int or schema_version != integrated_modules.MODULE_SCHEMA_VERSION:
        errors.append("module_schema_version_mismatch")

    return {
        "ok": not errors,
        "explicit": True,
        "selected_modules": selected_modules,
        "module_sections": module_sections,
        "premerge_section_ids": premerge_section_ids,
        "module_schema_version": schema_version if type(schema_version) is int else None,
        "errors": list(dict.fromkeys(errors)),
    }


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

    modules = module_contract(profile)

    ok = (
        not missing
        and not people_missing
        and profile_type == "integrated_full"
        and people_count == 2
        and receiver_in_people
        and birth_shape_ok
        and bool(pdf)
        and modules["ok"]
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
        "module_contract_explicit": modules["explicit"],
        "selected_modules": modules["selected_modules"],
        "module_schema_version": modules["module_schema_version"],
        "module_sections_count": sum(
            len(section_ids) for section_ids in (modules["module_sections"] or {}).values()
        ),
        "premerge_section_ids_count": len(modules["premerge_section_ids"] or []),
        "module_contract_errors": modules["errors"],
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
