# 04. Unified JSON Schema

> 최초 작성: 2026-06-10. pydantic 모델: sajugen/models/report.py (Phase 4)

## 최상위 구조

| 키 | 타입 | 설명 |
|---|---|---|
| order_id | str | ord_ 접두 ULID |
| birth | BirthInput | 고객 입력 원본+정규화 |
| calendar_verification | CalendarVerification | 3원 교차 결과 |
| saju | SajuChart | 기존 Myeongni 직렬화 |
| ziwei | ZiweiChart \| None | 시진 불명 시 None |
| derived_interpretation | dict | 섹션별 사실 슬롯(factcheck allowed_tokens, trace 소스) |
| customer_questions | list[CustomerQuestion] | 고민/질문 + 분류 + 근거 슬롯 |
| llm_allowed_sections | list[str] | ["integration","question_answers","final_advice"] 고정 |
| safety_flags | SafetyFlags | safe_lint/factcheck/needs_review |
| report_plan | ReportPlan | product, sections, template_version, tone |
| audit_log | list[AuditEntry] | actor(engine/llm/admin), action, section, at |

## BirthInput

| 필드 | 타입 | 비고 |
|---|---|---|
| name | str | 호명 슬롯 전용 |
| gender | "M"/"F" | |
| input_calendar | "solar"/"lunar" | |
| input_date | date | 입력 그대로 |
| is_leap_month | bool | lunar일 때만 |
| birth_time | time \| None | None=시진 불명 |
| birthplace | {label, lon, lat, tz} | 기본 서울, tz=Asia/Seoul(MVP) |
| concern_text | str | 고민/질문 원문(발송 후 마스킹 대상) |

## CalendarVerification

| 필드 | 설명 |
|---|---|
| solar_date | 확정 양력일 (KASI 1차 기준) |
| sources.{kasi, lunar_python, klc} | 각 소스 변환 결과 |
| iljin.{kasi, lunar_python} | 일진 간지 대조 |
| term_minutes_diff | 해당 월 절입 Skyfield↔KASI 차이(분) |
| match / mismatch_fields | 전체 일치 여부 |
| near_term_boundary | 절입 ±2분 플래그 |

## CustomerQuestion

| 필드 | 설명 |
|---|---|
| raw | 질문 원문 |
| domain | enum: wealth/love/job/health/timing/etc |
| evidence_slots | 계산 근거 키 목록(예: daewoon, seun_2026, 관록궁) |
| answer_text / answer_status | draft/approved, 폴백 시 needs_review |

## 원칙
- LLM 입력에는 birth 원본(생년월일·출생지) 대신 saju/ziwei/derived 파생값만 전달. name은 호명 슬롯만.
- 모든 모델 pydantic, round-trip 테스트 필수.
