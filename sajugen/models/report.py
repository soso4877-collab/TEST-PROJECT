# -*- coding: utf-8 -*-
"""Unified JSON 스키마 (docs/04) — 주문 1건의 전체 산출을 담는 직렬화 모델.

순수 스키마 레이어: calc/content 에 의존하지 않는다(역방향 의존 금지).
saju/ziwei 는 기존 pydantic 모델의 model_dump() 를 dict 로 담아 JSON round-trip 보장.
모든 모델 pydantic, model_dump_json ↔ model_validate_json 왕복 일치(테스트 필수).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# LLM 허용 섹션 고정(절대규칙 15). 그 외 섹션은 룰 NLG 전용.
LLM_ALLOWED_SECTIONS = ["integration", "question_answers", "final_advice"]

Domain = Literal["wealth", "love", "job", "health", "timing", "etc"]
AnswerStatus = Literal["draft", "approved", "needs_review"]


class Birthplace(BaseModel):
    label: str = "서울"
    lon: float = 126.978
    lat: float = 37.566
    tz: str = "Asia/Seoul"


class BirthInput(BaseModel):
    name: str = ""  # 호명 슬롯 전용
    gender: Literal["M", "F"]
    input_calendar: Literal["solar", "lunar"] = "solar"
    input_date: str  # 입력 그대로(YYYY-MM-DD)
    is_leap_month: bool = False  # lunar 일 때만 유효
    birth_time: str | None = None  # 'HH:MM' 또는 None=시진 불명
    birthplace: Birthplace = Field(default_factory=Birthplace)
    concern_text: str = ""  # 발송 후 마스킹 대상


class CalendarVerification(BaseModel):
    solar_date: str  # 확정 양력일(KASI 1차 기준)
    sources: dict = Field(default_factory=dict)  # {kasi, lunar_python, klc}
    iljin: dict = Field(default_factory=dict)  # {kasi, lunar_python}
    term_minutes_diff: float | None = None  # 절입 Skyfield↔KASI 분차
    match: bool = True
    mismatch_fields: list[str] = Field(default_factory=list)
    near_term_boundary: bool = False  # 절입 ±2분 플래그


class CustomerQuestion(BaseModel):
    raw: str
    domain: Domain = "etc"
    evidence_slots: list[str] = Field(default_factory=list)
    answer_text: str = ""
    answer_status: AnswerStatus = "draft"


class SafetyFlags(BaseModel):
    safe_lint_total: int = 0
    factcheck_total: int = 0
    grounding_ok: bool = True
    needs_review: bool = False


class ReportPlan(BaseModel):
    product: str = "integrated"  # integrated|myeongni|ziwei
    sections: list[str] = Field(default_factory=list)
    template_version: str = ""
    tone: str = "consult"


class AuditEntry(BaseModel):
    actor: Literal["engine", "llm", "admin", "system"]
    action: str
    section: str = ""
    from_state: str = ""
    to_state: str = ""
    note: str = ""
    at: str = ""  # ISO8601 UTC


class UnifiedReport(BaseModel):
    """주문 1건의 통합 산출(최상위). order_id 는 store 가 발급."""

    order_id: str
    birth: BirthInput
    calendar_verification: CalendarVerification
    saju: dict = Field(default_factory=dict)  # 기존 Myeongni.model_dump()
    ziwei: dict | None = None  # 시진 불명 시 None
    derived_interpretation: dict = Field(default_factory=dict)  # 섹션별 사실 슬롯
    customer_questions: list[CustomerQuestion] = Field(default_factory=list)
    llm_allowed_sections: list[str] = Field(default_factory=lambda: list(LLM_ALLOWED_SECTIONS))
    safety_flags: SafetyFlags = Field(default_factory=SafetyFlags)
    report_plan: ReportPlan = Field(default_factory=ReportPlan)
    audit_log: list[AuditEntry] = Field(default_factory=list)
    # 검수 UI 연결(2026-06-13, additive — 기본값 있어 기존 직렬화 왕복 유지):
    content: dict = Field(default_factory=dict)  # Report23.model_dump() — 섹션 본문·가드
    render_meta: dict = Field(default_factory=dict)  # 생성 파라미터·드래프트 경로 등(재렌더용)
