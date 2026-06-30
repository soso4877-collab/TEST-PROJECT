# -*- coding: utf-8 -*-
"""하네스 요약 리포트 — preflight+pytest+per-PDF 결과를 summary.json + summary.md 로.

기본 PII redaction: 파일명·SHA256·page·verify 필드·hits(개수+문구)·git/calc/secrets 상태·
tests PASS 수만 기록. 실제 이름/생년월일/출생시간은 넣지 않는다(--include-pii 미구현, OFF 고정).
리포트는 report_dir(기본 handoff/reports, .gitignore) 아래 <stamp>/ 에 쓴다.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# PDF 검증 결과에서 리포트에 노출할 키(이름/생년월일 등 PII는 _build_specs 입력일 뿐 결과에 없음)
_PDF_GATE = [
    "gate_pass",
    "markdown_clean",
    "daewoon_consistent",
    "quality_clean",
    "temporal_clean",
    "no_orphan",
    "loanword_clean",
    "raw_calc_head_clean",
    "customer_meta_clean",
    "placeholder_residue_clean",
    "style_clean",
    "role_perspective_clean",
    "honorific_consistency_clean",
    "name_policy_clean",
    "identity_role_clean",
    "singang_role_clean",
    "delivery_quality_clean",
]
_PDF_COUNT = [
    "quality_hits_count",
    "temporal_hits_count",
    "loanword_hits_count",
    "raw_calc_phrase_hits_count",
    "punctuation_hits_count",
    "semantic_style_hits_count",
    "ai_meta_hits_count",
    "placeholder_residue_hits_count",
    "role_perspective_hits_count",
    "honorific_consistency_hits_count",
    "name_policy_hits_count",
    "identity_role_hits_count",
    "singang_role_hits_count",
    "orphan_pages_count",
    "delivery_missing_axes_count",
    "delivery_repetition_hits_count",
    "delivery_guarantee_hits_count",
    "loanword_substring_count",
]
_SEMANTIC_GATE_DEFAULTS = {
    "customer_meta_clean": None,
    "placeholder_residue_clean": None,
    "style_clean": None,
    "role_perspective_clean": None,
    "honorific_consistency_clean": None,
}
_SEMANTIC_COUNT_DEFAULTS = {
    "semantic_style_hits_count": 0,
    "ai_meta_hits_count": 0,
    "placeholder_residue_hits_count": 0,
    "role_perspective_hits_count": 0,
    "honorific_consistency_hits_count": 0,
}
_SEMANTIC_HIT_FIELDS = (
    "semantic_style_hits",
    "ai_meta_hits",
    "placeholder_residue_hits",
    "role_perspective_hits",
    "honorific_consistency_hits",
)


def build_summary(preflight: dict, pytest_result: dict, pdf_results: list[dict]) -> dict:
    return {
        "preflight": {
            "branch": preflight.get("branch"),
            "preflight_ok": preflight.get("preflight_ok"),
            "calc_diff_empty": preflight.get("calc_diff_empty"),
            "env_tracked": preflight.get("env_tracked"),
            "render_out_tracked": preflight.get("render_out_tracked"),
            "local_profiles_ignored": preflight.get("local_profiles_ignored"),
            "reports_ignored": preflight.get("reports_ignored"),
            "secret_hit_count": preflight.get("secret_hit_count"),
            "status_short_count": preflight.get("status_short_count"),
        },
        "pytest": pytest_result,
        "pdfs": [_redact_pdf(p) for p in pdf_results],
        "all_gates_pass": all(p.get("gate_pass") for p in pdf_results) if pdf_results else None,
    }


def _redact_pdf(p: dict) -> dict:
    out = {
        "type": p.get("type"),
        "pdf": _redacted_pdf_name(p.get("pdf")),
        "status": p.get("status"),
        "regen": p.get("regen", "skipped(미승인)"),
    }
    if p.get("meta"):
        out["sha256"] = p["meta"].get("sha256")
        out["pages"] = p["meta"].get("pages")
        out["size"] = p["meta"].get("size")
    for k in _PDF_GATE:
        if k in p:
            out[k] = p[k]
    for k, default in _SEMANTIC_GATE_DEFAULTS.items():
        out.setdefault(k, default)
    for k in _PDF_COUNT:
        if k in p:
            out[k] = p[k]
    for k, default in _SEMANTIC_COUNT_DEFAULTS.items():
        out.setdefault(k, default)
    for k in (
        "quality_hits",
        "temporal_hits",
        "name_policy_hits",
        "identity_role_hits",
        "singang_role_hits",
        "loanword_hits",
        "orphan_pages",
        "low_density_pages",
    ):
        if p.get(k):
            out[k] = _summarize_hits(p[k])
    for k in _SEMANTIC_HIT_FIELDS:
        out[k] = _summarize_hits(p.get(k) or [])
    if "semantic_review_status" in p:
        out["semantic_review_status"] = p.get("semantic_review_status")
    else:
        out["semantic_review_status"] = None
    if p.get("delivery_quality"):
        out["delivery_quality"] = _summarize_delivery_quality(p["delivery_quality"])
    out["daewoon_current"] = p.get("daewoon_current")
    return out


def _redacted_pdf_name(path: str | None) -> str | None:
    if not path:
        return None
    suffix = Path(path).suffix or ".pdf"
    return f"[redacted]{suffix}"


def _summarize_hits(hits: list[dict]) -> list[dict]:
    out: list[dict] = []
    for h in hits[:20]:
        item = {}
        for key in (
            "type",
            "kind",
            "rule",
            "page",
            "chars",
            "term",
            "count",
            "allowed",
            "severity",
            "role",
            "expected",
            "actual",
        ):
            if key in h:
                item[key] = h[key]
        if not item and isinstance(h, dict):
            item["type"] = "hit"
        out.append(item)
    return out


def _summarize_delivery_quality(dq: dict) -> dict:
    return {
        "clean": dq.get("clean"),
        "premium": dq.get("premium"),
        "product": dq.get("product"),
        "pages": dq.get("pages"),
        "text_chars": dq.get("text_chars"),
        "required_axes": dq.get("required_axes"),
        "missing_axes": dq.get("missing_axes"),
        "failures": dq.get("failure_messages") or [_delivery_finding(f) for f in dq.get("failures", [])],
        "warnings": dq.get("warning_messages") or [_delivery_finding(w) for w in dq.get("warnings", [])],
    }


def _delivery_finding(finding: dict) -> dict:
    out = {"rule": finding.get("rule")}
    for key in ("value", "minimum", "axes"):
        if key in finding:
            out[key] = finding[key]
    if "pages" in finding:
        out["pages_count"] = len(finding.get("pages") or [])
    return {k: v for k, v in out.items() if v is not None}


def _sha12_payload(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:12]


def _archive_summary(summary: dict, out_dir: Path) -> dict:
    archived = json.loads(json.dumps(summary, ensure_ascii=False, default=str))
    run_state = archived.pop("run_state", None)
    if run_state:
        report = dict(archived.get("report") or {})
        report["run_state"] = {
            "path": str(out_dir / "RUN_STATE.json"),
            "sha12": _sha12_payload(run_state),
        }
        archived["report"] = report
    return archived


def _md(summary: dict) -> str:
    pf = summary["preflight"]
    L = ["# sajugen 하네스 검증 리포트", "", "## preflight"]
    L += [
        f"- branch: {pf['branch']}",
        f"- preflight_ok: {pf['preflight_ok']}",
        f"- calc_diff_empty: {pf['calc_diff_empty']}",
        f"- env_tracked: {pf['env_tracked']} / render_out_tracked: {pf['render_out_tracked']}",
        f"- local_profiles_ignored: {pf['local_profiles_ignored']} / reports_ignored: {pf['reports_ignored']}",
        f"- secret_hit_count: {pf['secret_hit_count']} (값 미출력)",
        f"- status_short_count: {pf['status_short_count']}",
    ]
    pt = summary["pytest"]
    L += [
        "",
        "## pytest",
        f"- passed: {pt.get('passed')} / returncode: {pt.get('returncode')} / skipped(regen): {pt.get('skipped')}",
    ]
    L += ["", "## PDF 검증", f"- all_gates_pass: {summary['all_gates_pass']}"]
    for p in summary["pdfs"]:
        L += [f"### {p['type']} — {p['pdf']} ({p['status']})"]
        if p["status"] != "verified":
            L.append(f"- (검증 안 됨: {p['status']}) — 재생성하지 않음")
            continue
        L.append(f"- sha256: {p.get('sha256')} / pages: {p.get('pages')} / size: {p.get('size')}")
        L.append("- gates: " + ", ".join(f"{k}={p.get(k)}" for k in _PDF_GATE if k in p))
        L.append("- hit counts: " + ", ".join(f"{k}={p.get(k)}" for k in _PDF_COUNT if k in p))
        if p.get("delivery_quality"):
            dq = p["delivery_quality"]
            L.append(f"- delivery failures: {dq.get('failures')}")
            L.append(f"- delivery warnings: {dq.get('warnings')}")
        if p.get("quality_hits"):
            L.append(f"- quality_hits: {p.get('quality_hits')}")
        if p.get("temporal_hits"):
            L.append(f"- temporal_hits: {p.get('temporal_hits')}")
        if p.get("low_density_pages"):
            L.append(f"- low_density_pages: {p.get('low_density_pages')}")
        if p.get("orphan_pages"):
            L.append(f"- orphan_pages: {p.get('orphan_pages')}")
        L.append(f"- daewoon_current: {p.get('daewoon_current')}")
    L += ["", "> PII(실명·생년월일·출생시간) 미포함. PDF/LLM 재생성·커밋은 하네스 밖(승인 게이팅)."]
    return "\n".join(L)


def write_report(
    summary: dict, report_dir: str = "handoff/reports", stamp: str | None = None
) -> dict:
    stamp = stamp or time.strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / report_dir / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    j = out_dir / "summary.json"
    m = out_dir / "summary.md"
    archived = _archive_summary(summary, out_dir)
    j.write_text(json.dumps(archived, ensure_ascii=False, indent=2), encoding="utf-8")
    m.write_text(_md(archived), encoding="utf-8")
    return {"json": str(j), "md": str(m), "dir": str(out_dir)}
