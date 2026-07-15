# -*- coding: utf-8 -*-
"""하네스 PDF 검증 — 읽기 전용(재생성 안 함). 기존 게이트를 호출만 한다(규칙 drift 금지).

판정 로직은 sajugen.render.verify.verify 와 sajugen.content.client_tone_lint 가 소유한다.
이 스크립트는 (1) 프로파일 type 으로 결정론 spec 생성(기존 헬퍼 재사용),
(2) verify 호출, (3) 파일 메타(SHA256/page/size/mtime) + 외래어 원시 substring 보조 스캔
(금지어 목록도 client_tone_lint.LOANWORDS 재사용)만 더한다. PDF 없으면 missing_pdf.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import hprofile_check  # noqa: E402


def _parse_birth(s: str) -> tuple[int, int, int, int | None, int | None]:
    parts = s.strip().split()
    d = parts[0]
    y, mo, da = (int(x) for x in d.split("-"))
    if len(parts) < 2:
        # 날짜-only 프로파일을 정오 출생으로 위장하지 않는다. personal 경로는 삼주로
        # 계산하고, 관계 프로파일은 person_facts의 known-time 계약에서 fail-closed한다.
        hh, mi = None, None
    else:
        hh, mi = (int(x) for x in parts[1].split(":"))
    return y, mo, da, hh, mi


def _is_male(g) -> bool:
    return str(g).strip().lower() not in ("여", "여자", "f", "female", "0")


def _file_meta(pdf: str) -> dict:
    import fitz

    st = os.stat(pdf)
    h = hashlib.sha256()
    with open(pdf, "rb") as f:
        for b in iter(lambda: f.read(8192), b""):
            h.update(b)
    doc = fitz.open(pdf)
    pages = doc.page_count
    doc.close()
    return {
        "sha256": h.hexdigest(),
        "pages": pages,
        "size": st.st_size,
        "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
    }


def _safe_hits(hits: list[dict] | None) -> list[dict]:
    """Forward count/rule metadata only; never forward raw matched text."""
    out: list[dict] = []
    for h in (hits or [])[:20]:
        if not isinstance(h, dict):
            continue
        item = {}
        for key in (
            "type",
            "kind",
            "rule",
            "page",
            "chars",
            "term",
            "token",
            "count",
            "allowed",
            "severity",
            "role",
            "expected",
            "actual",
        ):
            if key in h:
                item[key] = h[key]
        if item:
            out.append(item)
    return out


def _build_specs(profile: dict) -> dict:
    """프로파일 type → verify 인자(결정론 spec). 기존 헬퍼만 재사용."""
    t = profile["type"]
    ref = int(profile.get("ref_year", 2026))
    if t == "personal":
        from sajugen.calc import engine
        from sajugen.content import builder
        from sajugen.input.birth_time import normalize_birth_time_mode

        y, mo, da, hh, mi = _parse_birth(profile["birth"])
        birth_time_mode = normalize_birth_time_mode(
            profile.get("birth_time_mode"),
            unknown_time=True if hh is None else None,
            hour=hh,
        )
        saju = engine.build(
            y,
            mo,
            da,
            hh,
            mi,
            is_male=_is_male(profile.get("gender", "남")),
            horoscope_date=str(profile.get("horoscope") or f"{ref}-06-01"),
            birth_time_mode=birth_time_mode,
        )
        name = profile["name"]
        return {
            "ref_year": ref,
            "names": [name],
            "name_full": None,
            "identity": builder.personal_identity_spec(saju, name),
            "singang": None,
            "product": profile.get("product"),
            "premium": bool(profile.get("premium", False)),
            "role_perspective": None,
            "honorific": None,
        }
    if t in ("gunghap", "integrated", "integrated_full"):
        from sajugen import gunghap as g
        from sajugen.content import client_tone_lint

        people = [
            g.person_facts(
                p["name"],
                _parse_birth(p["birth"]),
                ref_year=ref,
                is_male=_is_male(p.get("gender", "남")),
            )
            for p in profile["people"]
        ]
        names = [p["name"] for p in people]
        product = profile.get("product")
        if not product and t == "integrated_full":
            product = "integrated_full"
        elif not product and t == "integrated":
            product = "integrated"
        receiver = profile.get("receiver") or (names[0] if names else None)
        role_specs = (
            client_tone_lint.role_perspective_specs(names, receiver=receiver)
            if t in ("integrated", "integrated_full")
            else None
        )
        return {
            "ref_year": ref,
            "names": names,
            "name_full": names,
            "identity": g._identity_spec(people),
            "singang": g._singang_specs(people),
            "product": product,
            "premium": bool(profile.get("premium", product == "integrated_full")),
            "role_perspective": role_specs,
            "honorific": role_specs,
        }
    raise ValueError(f"알 수 없는 profile type: {t}")


def verify_profile(profile: dict, pdf_override: str | None = None) -> dict:
    """프로파일 1건 검증. 재생성하지 않는다. PDF 없으면 status=missing_pdf."""
    pdf = pdf_override or profile.get("pdf")
    pdf_abs = str((ROOT / pdf).resolve()) if pdf and not os.path.isabs(pdf) else pdf
    out: dict = {"type": profile.get("type"), "pdf": pdf}

    # ``modules`` 명시 프로파일은 저장 주문에서 온 모듈/커버리지/스키마 원자를 모두
    # 갖춰야 한다. PDF 존재 여부보다 먼저 닫아 증거 누락이 missing_pdf나 레거시 5모듈
    # 보정으로 가려지지 않게 한다.
    module_contract = hprofile_check.module_contract(profile)
    if module_contract["explicit"]:
        out["selected_modules"] = module_contract["selected_modules"]
        out["module_schema_version"] = module_contract["module_schema_version"]
    if not module_contract["ok"]:
        out["status"] = "invalid_module_contract"
        out["gate_pass"] = False
        out["module_contract_errors"] = module_contract["errors"]
        return out

    if not pdf_abs or not os.path.isfile(pdf_abs):
        out["status"] = "missing_pdf"  # 재생성하지 않고 스킵/실패 보고
        out["gate_pass"] = False
        return out


    from sajugen.content import client_tone_lint as ct
    from sajugen.render import verify as V

    specs = _build_specs(profile)
    v = V.verify(
        pdf_abs,
        ref_year=specs["ref_year"],
        names=specs["names"],
        name_full=specs["name_full"],
        identity=specs["identity"],
        singang=specs["singang"],
        product=profile.get("product") or specs.get("product"),
        premium=bool(specs.get("premium", profile.get("premium", False))),
        concern=profile.get("concern"),
        expected_context_terms=profile.get("expected_context_terms"),
        ref_date=profile.get("ref_date"),
        role_perspective=specs.get("role_perspective"),
        honorific=specs.get("honorific"),
        # QI-2026-07-04: 프로파일이 파트너 유무를 선언하면 커플 지칭 승격 판정에 사용
        # (미선언 None = 기존 동작 — 잘못된 hard fail 방지 위해 운영자가 명시할 때만).
        partner_present=profile.get("partner_present"),
        # Q7 모듈 계약은 세 원자를 함께 넘긴다. explicit=False 레거시는 모두 None이라
        # 제품 정본이 기존 5모듈/30쪽 계약을 복원한다.
        selected_modules=module_contract["selected_modules"],
        module_sections=module_contract["module_sections"],
        premerge_section_ids=module_contract["premerge_section_ids"],
        # 생시 미상 삼주 PDF는 프로파일의 PII-free 출처 계약을 최종 verify까지 전달한다.
        # 두 필드가 빠진 레거시 unknown 프로파일은 새 게이트의 승인 근거로 쓸 수 없다.
        birth_time_mode=profile.get("birth_time_mode"),
        three_pillar_provenance=profile.get("three_pillar_provenance"),
    )
    out["status"] = "verified"
    out["meta"] = _file_meta(pdf_abs)
    # 게이트/힌트는 verify 결과를 그대로 옮긴다(복제 아님).
    for k in (
        "gate_pass",
        "markdown_clean",
        "daewoon_consistent",
        "quality_clean",
        "temporal_clean",
        "no_orphan",
        "loanword_clean",
        "raw_calc_head_clean",
        "client_register_clean",
        "unknown_time_provenance_clean",
        "customer_meta_clean",
        "placeholder_residue_clean",
        "style_clean",
        "western_astrology_clean",
        "name_policy_clean",
        "identity_role_clean",
        "singang_role_clean",
        "delivery_quality_clean",
        "register_hard_hits_count",
        "register_warning_hits_count",
        "unknown_time_provenance_hits_count",
        "western_astrology_hits_count",
        "delivery_external_domain_advice_hits_count",
        "role_perspective_clean",
        "honorific_consistency_clean",
        "daewoon_current",
    ):
        out[k] = v.get(k)
    for k in (
        "loanword_hits",
        "register_hits",
        "raw_calc_phrase_hits",
        "punctuation_hits",
        "name_policy_hits",
        "identity_role_hits",
        "singang_role_hits",
        "orphan_pages",
        "low_density_pages",
        "quality_hits",
        "temporal_hits",
        "delivery_missing_axes",
        "delivery_repetition_hits",
        "delivery_guarantee_hits",
        "name_policy_allowed_hits",
        "honorific_consistency_hits",
    ):
        val = v.get(k) or []
        out[k + "_count"] = v.get(k + "_count", len(val))
        out[k] = val[:20]
    for k in (
        "semantic_style_hits",
        "ai_meta_hits",
        "placeholder_residue_hits",
        "role_perspective_hits",
        "unknown_time_provenance_hits",
        "western_astrology_hits",
    ):
        val = _safe_hits(v.get(k) or [])
        out[k + "_count"] = len(v.get(k) or [])
        out[k] = val
    # delivery_quality 통째 forward 금지(T1.3/B-3): failures/warnings 내부에 본문 조각
    # (guarantee match·repetition term·저밀도 스니펫)이 중첩돼 --json stdout/summary.json 으로
    # 샐 수 있다. hsummary._delivery_finding 과 동일한 rule/메타 화이트리스트만 내보낸다.
    _dq = v.get("delivery_quality") or {}

    def _safe_finding(f: dict) -> dict:
        o = {"rule": f.get("rule")}
        for kk in ("value", "minimum", "axes"):
            if kk in f:
                o[kk] = f[kk]
        if "pages" in f:
            o["pages_count"] = len(f.get("pages") or [])
        return o

    out["delivery_quality"] = {
        "clean": _dq.get("clean"),
        "premium": _dq.get("premium"),
        "product": _dq.get("product"),
        "pages": _dq.get("pages"),
        "text_chars": _dq.get("text_chars"),
        "minimum_pages": _dq.get("minimum_pages"),
        "minimum_text_chars": _dq.get("minimum_text_chars"),
        "selected_modules": _dq.get("selected_modules"),
        "module_schema_version": _dq.get("module_schema_version"),
        "required_axes": _dq.get("required_axes"),
        "missing_axes": _dq.get("missing_axes"),
        "failures": [_safe_finding(f) for f in (_dq.get("failures") or [])],
        "warnings": [_safe_finding(w) for w in (_dq.get("warnings") or [])],
    }
    # summary가 본문이나 섹션 원문 없이도 적용된 모듈 하한을 직접 관측하도록 PII-free
    # 정수/enum 네 값만 최상위로 올린다.
    out["selected_modules"] = v.get("selected_modules")
    out["module_schema_version"] = v.get("module_schema_version")
    out["minimum_pages"] = _dq.get("minimum_pages")
    out["minimum_text_chars"] = _dq.get("minimum_text_chars")

    # 제품 verify 응답이 프로파일 원자와 다른 스키마/선택을 되돌리면 gate_pass가 참이어도
    # 하네스 증거로 사용할 수 없다. 조용한 재정규화 대신 명시적 계약 오류로 닫는다.
    if module_contract["explicit"]:
        mismatch_errors: list[str] = []
        if out["module_schema_version"] != module_contract["module_schema_version"]:
            mismatch_errors.append("verify_module_schema_version_mismatch")
        if out["selected_modules"] != module_contract["selected_modules"]:
            mismatch_errors.append("verify_selected_modules_mismatch")
        if mismatch_errors:
            out["gate_pass"] = False
            out["module_contract_errors"] = mismatch_errors
    # 보조: 외래어 원시 substring(목록은 client_tone_lint.LOANWORDS 재사용 — 정규식 복붙 아님)
    import fitz

    doc = fitz.open(pdf_abs)
    body, _ = V._split_body_appendix([doc.load_page(i).get_text() for i in range(doc.page_count)])
    doc.close()
    out["loanword_substring_count"] = sum(1 for w in ct.LOANWORDS if w in body)
    return out


def load_profile(path: str) -> dict:
    import yaml

    p = path if os.path.isabs(path) else str(ROOT / path)
    return yaml.safe_load(Path(p).read_text(encoding="utf-8")) or {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="sajugen 하네스 PDF 검증(읽기 전용)")
    ap.add_argument("profile", help="프로파일 YAML 경로")
    ap.add_argument("--pdf", default=None, help="PDF 경로 override")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = verify_profile(load_profile(a.profile), pdf_override=a.pdf)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"type={r.get('type')} status={r.get('status')} gate_pass={r.get('gate_pass')}")
    return 0 if r.get("gate_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
