# -*- coding: utf-8 -*-
"""콘텐츠 빌더 — SajuResult → 23섹션 룰 골격 → (옵션)LLM 윤문 → 가드 → Report23.

가드: §12 안전 린트 + 사실일치 린트 + 그라운딩. 윤문이 가드 실패 시 룰 원문 폴백.
"""

from __future__ import annotations

from . import factcheck, llm_polish, llm_sections, question_router, rules, safe_lint, trace
from .sections_schema import SECTION_SPECS, GuardReport, Report23, Section

# 3단 상품 토글 — 제외할 섹션 집합. integrated=전부, myeongni=명리만,
# ziwei=자미만. 개요·각론·정적·부록 섹션은 공통 유지(v1: 혼합 섹션 보존).
_PRODUCT_DROP = {
    "integrated": set(),
    "myeongni": {"ziwei_summary", "ziwei_palaces", "cross"},
    "ziwei": {
        "wonguk",
        "ohaeng",
        "ilgan",
        "sipseong",
        "strength",
        "character",
        "daewoon",
        "thisyear",
        "monthly",
        "cross",
    },
}


def build_report(
    saju,
    *,
    use_llm: bool = False,
    ref_year: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
    product: str = "integrated",
    concern: str | None = None,
) -> Report23:
    # Phase5 구간1: 고민 분류. use_llm+키면 LLM 분류, 아니면 결정론 룰(무키·재현성).
    if concern and use_llm:
        category = llm_sections.get_backend().classify(concern)
    else:
        category = question_router.classify(concern)

    skeletons = rules.build_all(
        saju,
        ref_year=ref_year,
        name=name,
        unknown_time=unknown_time,
        concern_category=category.value,
    )
    drop = _PRODUCT_DROP.get(product, set())
    sections: list[Section] = []
    safe_total = fact_total = polished_n = fallback_n = 0

    for sid, title, src in SECTION_SPECS:
        if sid in drop:
            continue
        rule_text = skeletons[sid].strip()

        # 룰 골격 자체 가드(설계상 통과해야 함; 위반 시 버그로 표면화)
        sv = safe_lint.lint(rule_text)
        fv = factcheck.check(rule_text, saju)
        rule_violations = sv + fv

        final = rule_text
        polished = False
        applied_violations = list(rule_violations)

        if use_llm and not rule_violations:
            cand = llm_polish.polish(rule_text, title)
            if cand and cand != rule_text:
                csv = safe_lint.lint(cand)
                cfv = factcheck.check(cand, saju)
                if not csv and not cfv:
                    final, polished = cand, True
                    polished_n += 1
                else:
                    fallback_n += 1  # 윤문이 가드 실패 → 룰 원문 유지

        safe_total += len(safe_lint.lint(final))
        fact_total += len(factcheck.check(final, saju))
        sections.append(
            Section(
                id=sid,
                title=title,
                source_keys=src,
                rule_text=rule_text,
                final_text=final,
                polished=polished,
                guard_violations=applied_violations if not polished else [],
            )
        )

    grounding_ok, _bad = trace.check(sections)
    clean = safe_total == 0 and fact_total == 0 and grounding_ok
    return Report23(
        sections=sections,
        concern_category=category.value,
        guard=GuardReport(
            safe_lint_total=safe_total,
            factcheck_total=fact_total,
            grounding_ok=grounding_ok,
            polished_sections=polished_n,
            fallback_sections=fallback_n,
            clean=clean,
        ),
    )
