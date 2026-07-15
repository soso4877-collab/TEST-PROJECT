# -*- coding: utf-8 -*-
"""후속 답변 문자열 게이트.

텍스트 답변에는 PDF 레이아웃·태그·밀도 게이트를 적용할 대상이 없다. 이 모듈은 기존
콘텐츠 안전 린트 중 문자열에 직접 적용 가능한 것만 개별 호출해, 후속 답변 발급 전에
같은 안전 벨트를 통과했는지 확인한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sajugen.content import (
    client_tone_lint,
    consistency,
    customer_meta_lint,
    delivery_quality,
    factcheck,
    quality_lint,
    safe_lint,
    style_lint,
    temporal_lint,
    trace,
    western_astrology_lint,
)
from sajugen.content.sections_schema import Section
from sajugen.render import verify


@dataclass(frozen=True)
class AnswerGateError(RuntimeError):
    """후속 답변 게이트 실패."""

    failures: list[dict]

    def __str__(self) -> str:
        rules = ", ".join(sorted({str(f.get("rule", "?")) for f in self.failures})[:6])
        return f"followup answer gate failed: {rules or 'unknown'}"


def _specs(specs: dict | None) -> dict:
    return specs or {}


def _norm(source: str, hit: Any, default_rule: str) -> dict:
    """PII 원문을 보고하지 않도록 rule/type 중심으로 정규화한다."""
    if isinstance(hit, dict):
        rule = hit.get("rule") or hit.get("type") or default_rule
        item = {"source": source, "rule": rule}
        for key in ("severity", "kind", "count", "expected", "actual", "got"):
            if key in hit:
                item[key] = hit[key]
        return item
    return {"source": source, "rule": default_rule}


def _add_hits(failures: list[dict], source: str, hits: list, default_rule: str) -> None:
    failures.extend(_norm(source, h, default_rule) for h in (hits or []))


def _trace_failures(answer: str) -> list[dict]:
    section = Section(
        id="followup_answer",
        title="후속 답변",
        source_keys=["report_json"],
        rule_text=answer,
        final_text=answer,
    )
    ok, bad = trace.check([section])
    return [] if ok else [{"source": "trace", "rule": b.get("why", "trace")} for b in bad]


def _consult_failures(answer: str, concern: str | None, skipped: list[dict]) -> list[dict]:
    result = delivery_quality.consult_direct_result(answer, concern)
    if result.get("skipped"):
        skipped.append({"check": "consult_direct_result", "reason": "concern 없음"})
    if result.get("ok", True):
        return []
    return [
        {
            "source": "delivery_quality.consult_direct_result",
            "rule": "consult_direct",
            "missing": list(result.get("missing", [])),
        }
    ]


def _conditional_lints(answer: str, specs: dict, skipped: list[dict]) -> list[dict]:
    failures: list[dict] = []

    identity = specs.get("identity")
    if identity:
        _add_hits(
            failures,
            "identity_role_lint",
            client_tone_lint.identity_role_lint(
                answer,
                identity.get("expected_gans", ()),
                identity.get("expected_terms", ()),
                identity.get("subject_specs", ()),
            ),
            "identity_role",
        )
    else:
        skipped.append({"check": "identity_role_lint", "reason": "identity specs 없음"})

    singang = specs.get("singang")
    if singang:
        _add_hits(
            failures,
            "singang_role_lint",
            client_tone_lint.singang_role_lint(answer, singang),
            "singang_role",
        )
    else:
        skipped.append({"check": "singang_role_lint", "reason": "singang specs 없음"})

    full_names = specs.get("name_full")
    if full_names:
        _add_hits(
            failures,
            "name_policy_lint",
            client_tone_lint.name_policy_lint(answer, full_names),
            "name_policy",
        )
    else:
        skipped.append({"check": "name_policy_lint", "reason": "name_full specs 없음"})

    honorific = specs.get("honorific")
    if honorific:
        _add_hits(
            failures,
            "honorific_consistency_lint",
            client_tone_lint.honorific_consistency_lint(answer, honorific),
            "honorific_consistency",
        )
    else:
        skipped.append({"check": "honorific_consistency_lint", "reason": "honorific specs 없음"})

    perspective = specs.get("role_perspective")
    if perspective:
        _add_hits(
            failures,
            "role_perspective_lint",
            client_tone_lint.role_perspective_lint(answer, perspective),
            "role_perspective",
        )
    else:
        skipped.append({"check": "role_perspective_lint", "reason": "role perspective specs 없음"})

    if "대운" in answer:
        expected = specs.get("daewoon_current")
        if expected:
            section = type("_Sec", (), {"id": "followup_answer", "final_text": answer})()
            ok, bad = consistency.check([section], expected_ko=expected)
            if not ok:
                _add_hits(failures, "daewoon_consistent", bad, "daewoon_consistent")
        else:
            skipped.append({"check": "daewoon_consistent", "reason": "현재 대운 specs 없음"})

    return failures


def check(
    answer: str,
    *,
    concern: str | None,
    allow_tokens: dict | None,
    ref_year: int | None,
    ref_date: str | None,
    specs: dict | None = None,
) -> dict:
    """후속 답변 게이트 결과. `failures`가 비어 있으면 통과, `skipped`는 미적용 사유다."""
    text = answer or ""
    spec = _specs(specs)
    skipped: list[dict] = []
    failures: list[dict] = []

    _add_hits(failures, "safe_lint", safe_lint.lint(text), "safe")
    _add_hits(failures, "factcheck", factcheck.check_with_allow(text, allow_tokens or {}), "factcheck")
    failures.extend(_trace_failures(text))
    _add_hits(failures, "temporal_lint", temporal_lint.lint(text, ref_year, ref_date=ref_date), "temporal")
    _add_hits(failures, "loanword_lint", client_tone_lint.loanword_lint(text), "loanword")
    _add_hits(failures, "raw_calc_lint", client_tone_lint.raw_calc_lint(text), "raw_calc")
    _add_hits(
        failures,
        "register_lint",
        [hit for hit in client_tone_lint.register_lint(text) if hit.get("severity") == "hard"],
        "client_register",
    )
    _add_hits(
        failures,
        "external_domain_advice_lint",
        delivery_quality.external_domain_advice_lint(text),
        "external_domain_advice",
    )
    _add_hits(
        failures,
        "western_astrology_lint",
        western_astrology_lint.lint(text),
        "western_astrology",
    )
    _add_hits(failures, "customer_meta_lint", customer_meta_lint.lint(text), "customer_meta")
    _add_hits(failures, "placeholder_residue_lint", client_tone_lint.placeholder_residue_lint(text), "placeholder_residue")
    _add_hits(failures, "style_lint", style_lint.lint(text), "style")
    _add_hits(failures, "quality_lint", quality_lint.lint(text, spec.get("names")), "quality")
    _add_hits(failures, "guarantee_lint", delivery_quality.guarantee_lint(text), "guarantee")
    failures.extend(_consult_failures(text, concern, skipped))
    _add_hits(failures, "markdown_artifacts", verify.markdown_artifacts(text), "markdown_artifact")
    failures.extend(_conditional_lints(text, spec, skipped))

    return {"ok": not failures, "failures": failures, "skipped": skipped}


def assert_clean(
    answer: str,
    *,
    concern: str | None,
    allow_tokens: dict | None,
    ref_year: int | None,
    ref_date: str | None,
    specs: dict | None = None,
) -> None:
    """게이트 실패 시 AnswerGateError. 후속 답변 발급 전 이 함수가 성공해야 한다."""
    result = check(
        answer,
        concern=concern,
        allow_tokens=allow_tokens,
        ref_year=ref_year,
        ref_date=ref_date,
        specs=specs,
    )
    if result["failures"]:
        raise AnswerGateError(result["failures"])
