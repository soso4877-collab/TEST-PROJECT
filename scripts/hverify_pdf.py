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


def _parse_birth(s: str) -> tuple[int, int, int, int, int]:
    d, t = (s.strip().split() + ["12:00"])[:2]
    y, mo, da = (int(x) for x in d.split("-"))
    hh, mi = (int(x) for x in t.split(":"))
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


def _build_specs(profile: dict) -> dict:
    """프로파일 type → verify 인자(결정론 spec). 기존 헬퍼만 재사용."""
    t = profile["type"]
    ref = int(profile.get("ref_year", 2026))
    if t == "personal":
        from sajugen.calc import engine
        from sajugen.content import builder

        y, mo, da, hh, mi = _parse_birth(profile["birth"])
        saju = engine.build(
            y,
            mo,
            da,
            hh,
            mi,
            is_male=_is_male(profile.get("gender", "남")),
            horoscope_date=str(profile.get("horoscope") or f"{ref}-06-01"),
        )
        name = profile["name"]
        return {
            "ref_year": ref,
            "names": [name],
            "name_full": None,
            "identity": builder.personal_identity_spec(saju, name),
            "singang": None,
        }
    if t == "gunghap":
        from sajugen import gunghap as g

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
        return {
            "ref_year": ref,
            "names": names,
            "name_full": names,
            "identity": g._identity_spec(people),
            "singang": g._singang_specs(people),
        }
    raise ValueError(f"알 수 없는 profile type: {t}")


def verify_profile(profile: dict, pdf_override: str | None = None) -> dict:
    """프로파일 1건 검증. 재생성하지 않는다. PDF 없으면 status=missing_pdf."""
    from sajugen.content import client_tone_lint as ct
    from sajugen.render import verify as V

    pdf = pdf_override or profile.get("pdf")
    pdf_abs = str((ROOT / pdf).resolve()) if pdf and not os.path.isabs(pdf) else pdf
    out: dict = {"type": profile.get("type"), "pdf": pdf}
    if not pdf_abs or not os.path.isfile(pdf_abs):
        out["status"] = "missing_pdf"  # 재생성하지 않고 스킵/실패 보고
        out["gate_pass"] = False
        return out
    specs = _build_specs(profile)
    v = V.verify(
        pdf_abs,
        ref_year=specs["ref_year"],
        names=specs["names"],
        name_full=specs["name_full"],
        identity=specs["identity"],
        singang=specs["singang"],
        product=profile.get("product"),
        premium=bool(profile.get("premium", False)),
        concern=profile.get("concern"),
        expected_context_terms=profile.get("expected_context_terms"),
        ref_date=profile.get("ref_date"),
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
        "name_policy_clean",
        "identity_role_clean",
        "singang_role_clean",
        "delivery_quality_clean",
        "daewoon_current",
    ):
        out[k] = v.get(k)
    for k in (
        "loanword_hits",
        "raw_calc_phrase_hits",
        "punctuation_hits",
        "name_policy_hits",
        "identity_role_hits",
        "singang_role_hits",
        "orphan_pages",
        "low_density_pages",
        "delivery_missing_axes",
        "delivery_repetition_hits",
        "delivery_guarantee_hits",
        "name_policy_allowed_hits",
    ):
        val = v.get(k) or []
        out[k + "_count"] = len(val)
        out[k] = val[:20]
    out["delivery_quality"] = v.get("delivery_quality")
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
