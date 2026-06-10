# 05. NLG / PDF Generation

> 최초 작성: 2026-06-10

## 규칙 기반 섹션 (기존 27섹션 — content/rules.py, 변경 최소)
cover, summary, howto, keywords, wonguk, ohaeng, ilgan, sipseong, strength, character, geukguk, shinsal, love, job, wealth, health, daewoon, thisyear, seun, monthly, ziwei_summary, ziwei_palaces, cross, advice, caution, questions, appendix_terms, closing, next (+상품 토글 integrated/myeongni/ziwei).
- 입력: Unified JSON. 검증: safe_lint + factcheck + trace (기존 3단 가드).
- 시진 불명: 자미 계열 섹션 생략(명리 단독 강등) — docs/03 §1.

## LLM 사용 섹션 (신규 4구간 — content/llm_sections.py)

| 구간 | 모델 | 입력 | 검증 | 폴백 |
|---|---|---|---|---|
| 질문 분류 | Haiku+Instructor | 고민 텍스트만 | enum 강제 | domain=etc |
| 명리×자미 통합 관점 | Sonnet | 양 엔진 파생 JSON(사실 슬롯 고정) | 가드 재검증 | 룰 cross 섹션 |
| 신청 질문 답변 | Sonnet | 질문+evidence_slots(슬롯 외 사실 금지) | 가드+관리자 필수 검수 | 룰 기본 문안+NEEDS_REVIEW |
| 마지막 조언 | Sonnet | 전 섹션 요약 슬롯 | 가드 재검증 | 룰 closing |
| (검수자) 재윤문 | Haiku (기존 llm_polish) | 선택 섹션 룰 원문 | 기존 가드 | 룰 원문 |

- 통합 관점 프롬프트에 docs/03 §5 규칙 내장: 명리 우선, 상충=층위 재서술, "모순" 단어 금지, 정확도 주장 금지.
- 프롬프트는 prompts/ 디렉토리에 버전 파일(YYYYMMDD-vN)로 관리, Unified JSON의 report_plan.template_version과 함께 audit_log에 기록.

## 반복 표현 검출 (content/repetition.py, 신규)
- 문장 단위 3~5 n-gram 중복률 측정. 임계치(초안: 동일 4-gram 3회 이상) 초과 시 관리자 화면 하이라이트.
- 자동 차단은 아님(하이라이트만) — 룰 골격 특성상 일부 반복은 정상.

## PDF (기존 유지)
- Jinja2 + Playwright Chromium tagged + veraPDF 측정(7.1-3 비악화 게이트). 폰트 Pretendard+Source Han Serif K(OFL) 임베드.
- 변경: 말미 고지 슬롯 추가 — "자동 분석 도구로 산출하고 운영자가 직접 검수·감수한 자료"(감수 명시형, 2026-06-10 확정) + 윤달 출생 시 산입 기준 고지.
