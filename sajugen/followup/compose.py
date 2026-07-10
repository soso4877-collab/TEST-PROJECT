# -*- coding: utf-8 -*-
"""후속 답변 슬림 컴포저.

새 계산은 하지 않는다. 기존 주문의 `report_json`에 저장된 Report23 본문과 allow_tokens 만
읽어, 새 질문을 마스킹 인용으로 격리한 뒤 답변 후보를 만들고 answer_gate 로 재검증한다.
"""

from __future__ import annotations

from datetime import date
import re
from typing import Any

from sajugen.content import delivery_quality, llm_sections, masking, question_router
from sajugen.content.sections_schema import Report23, Section
from sajugen.followup import answer_gate
from sajugen.models.report import UnifiedReport

_YEAR_RX = re.compile(r"(?:19|20)\d{2}(?=\s*년)")

# 표지·목차 2쪽 + 본문 8개 장을 기본 골격으로 삼는다. 각 장은 저장 Report23에서만
# 복사하고 consult만 새 답변으로 교체하므로 새 계산이나 근거 생성은 일어나지 않는다.
_FOLLOWUP_CATEGORY_SECTION = {
    "연애": "love",
    "직업": "work",
    "재물": "work",
    "건강": "health",
}


def _followup_pdf_section_ids(category: str) -> tuple[str, ...]:
    category_section = _FOLLOWUP_CATEGORY_SECTION.get(category, "wonguk")
    return (
        "cover",
        "toc",
        "intro",
        "nature",
        category_section,
        "flow",
        "ziwei",
        "together",
        "consult",
        "closing",
    )


def _load_report(report_json: UnifiedReport | dict | str) -> UnifiedReport:
    if isinstance(report_json, UnifiedReport):
        return report_json
    if isinstance(report_json, str):
        return UnifiedReport.model_validate_json(report_json)
    return UnifiedReport.model_validate(report_json)


def _report23(report: UnifiedReport) -> Report23:
    if not report.content:
        raise ValueError("저장된 content.sections 없음")
    return Report23.model_validate(report.content)


def _section_text(r23: Report23, sid: str) -> str:
    try:
        return r23.section(sid).final_text.strip()
    except StopIteration:
        return ""


def _base_text(r23: Report23) -> str:
    parts = [_section_text(r23, sid) for sid in ("nature", "flow", "consult")]
    text = "\n\n".join(p for p in parts if p)
    if not text:
        raise ValueError("재사용할 저장 본문 없음")
    return text


def _self_civil(report: UnifiedReport) -> str | None:
    solar = (report.calendar_verification.solar_date or report.birth.input_date or "").strip()
    if not solar:
        return None
    if report.birth.birth_time:
        return f"{solar} {report.birth.birth_time}"
    return solar


def _allowed_years(allow_tokens: dict) -> set[int]:
    years: set[int] = set()
    for y in allow_tokens.get("allowed_years", ()):
        try:
            years.add(int(y))
        except (TypeError, ValueError):
            continue
    return years


def _question_years(question: str) -> set[int]:
    return {int(m.group(0)) for m in _YEAR_RX.finditer(question or "")}


def _category_value(cat: Any) -> str:
    return getattr(cat, "value", str(cat or "전반"))


def _today(today: date | str | None) -> date:
    if isinstance(today, date):
        return today
    if today:
        return date.fromisoformat(str(today)[:10])
    return date.today()


def _reject(
    reason: str,
    *,
    category: str | None = None,
    failures: list[dict] | None = None,
) -> dict:
    return {
        "ok": False,
        "answer": "",
        "reason": reason,
        "category": category or "",
        "failures": failures or [],
        "skipped": [],
    }


def _compose_pdf_report(
    source: Report23,
    *,
    answer: str,
    category: str,
    polished: bool,
) -> Report23:
    """저장 섹션을 슬림 골격으로 복사하고 consult만 새 답변으로 교체한다."""
    by_id = {section.id: section for section in source.sections}
    previous_consult = by_id.get("consult")
    consult = Section(
        id="consult",
        title=(previous_consult.title if previous_consult else "새로 질문하신 내용에 대하여"),
        source_keys=(
            list(previous_consult.source_keys) if previous_consult else ["report_json", "input"]
        ),
        rule_text=answer,
        final_text=answer,
        polished=polished,
        guard_violations=[],
    )

    sections: list[Section] = []
    for section_id in _followup_pdf_section_ids(category):
        if section_id == "consult":
            sections.append(consult)
            continue
        stored = by_id.get(section_id)
        if stored is not None:
            sections.append(stored.model_copy(deep=True))

    polished_sections = sum(1 for section in sections if section.polished)
    guard = source.guard.model_copy(
        update={
            "polished_sections": polished_sections,
            "fallback_sections": len(sections) - polished_sections,
            "clean": True,
        }
    )
    return Report23(
        sections=sections,
        guard=guard,
        concern_category=category,
        allow_tokens=dict(source.allow_tokens or {}),
        partner_present=source.partner_present,
    )


def compose(
    report_json: UnifiedReport | dict | str,
    new_question: str,
    *,
    backend: llm_sections.LLMBackend | None = None,
    today: date | str | None = None,
    specs: dict | None = None,
    pdf: bool = False,
) -> dict:
    """저장 리포트와 새 질문으로 후속 답변 후보를 만든다.

    반환 dict:
    - ok=True: answer 가 T2 게이트를 통과했다.
    - ok=False: reason/failures 를 보고하고 발급하지 않는다.
    """
    question = (new_question or "").strip()
    if not question:
        return _reject("질문 없음")

    report = _load_report(report_json)
    r23 = _report23(report)
    allow_tokens = dict(r23.allow_tokens or {})
    allowed_years = _allowed_years(allow_tokens)
    asked_years = _question_years(question)
    # allowed_years 가 비어 있는 구 저장본은 질문의 절대연도 사전 판정 근거가 없다.
    # 여기서 새 연도 지평을 만들지 않고, 저장 allow_tokens 밖 간지·사실 토큰은
    # answer_gate 의 factcheck 백스톱이 차단하도록 경계를 고정한다.
    out_of_scope = sorted(y for y in asked_years if allowed_years and y not in allowed_years)
    category = _category_value(question_router.classify(question))
    if out_of_scope:
        return _reject(
            "범위 밖 연도입니다. 신규/재방문 정식 리포트가 필요합니다.",
            category=category,
        )

    stored_category = (r23.concern_category or "").strip()
    if stored_category and stored_category != "전반" and category not in {stored_category, "전반"}:
        return _reject(
            "범위 밖 주제입니다. 신규/재방문 정식 리포트가 필요합니다.",
            category=category,
        )

    now = _today(today)
    masked_question = masking.mask_concern(question, self_civil=_self_civil(report))
    composer = backend or llm_sections.RuleBackend()
    answer = composer.compose(
        section_id="consult",
        title="후속 답변",
        category=category,
        base_text=_base_text(r23),
        quoted_concern=masked_question,
        ref_year=now.year,
        ref_date=now.isoformat(),
    )
    gate = answer_gate.check(
        answer,
        concern=question,
        allow_tokens=allow_tokens,
        ref_year=now.year,
        ref_date=now.isoformat(),
        specs=specs,
    )
    if gate["failures"]:
        return {
            "ok": False,
            "answer": "",
            "reason": "후속 답변 게이트 실패",
            "category": category,
            "masked_question": masked_question,
            "failures": gate["failures"],
            "skipped": gate["skipped"],
        }
    result = {
        "ok": True,
        "answer": answer,
        "reason": "",
        "category": category,
        "masked_question": masked_question,
        "failures": [],
        "skipped": gate["skipped"],
    }
    if not pdf:
        return result

    # 텍스트 답변의 기존 T2 게이트에 더해 PDF 경로만 Q1 consult 직답 게이트를 적용한다.
    # 기본 텍스트 경로의 반환 스키마와 판정은 위에서 그대로 종료되어 변하지 않는다.
    consult_direct = delivery_quality.consult_direct_result(answer, question)
    if not consult_direct["ok"]:
        return _reject(
            "후속 PDF consult 직답 게이트 실패",
            category=category,
            failures=[
                {
                    "source": "delivery_quality",
                    "rule": "consult_direct",
                    "missing": list(consult_direct.get("missing", [])),
                }
            ],
        )
    if not r23.guard.clean:
        return _reject(
            "저장 리포트 가드 미통과",
            category=category,
            failures=[{"source": "report23", "rule": "parent_guard"}],
        )

    result.update(
        {
            "pdf_report": _compose_pdf_report(
                r23,
                answer=answer,
                category=category,
                polished=getattr(composer, "name", "rule") != "rule",
            ),
            "ref_year": now.year,
            "ref_date": now.isoformat(),
            "consult_direct": consult_direct,
        }
    )
    return result
