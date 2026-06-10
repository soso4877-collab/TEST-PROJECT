# 06. LLM Usage Policy

> 최초 작성: 2026-06-10. 이 문서는 강제 정책이다 — 위반 구조는 코드 리뷰에서 반려.

## 허용 (이 4구간 + 검수자 재윤문만)
1. 고객 고민/질문 분류 (Haiku, enum 강제)
2. 명리×자미 통합 관점 문단 (Sonnet)
3. 신청 질문 답변 (Sonnet, 관리자 필수 검수)
4. 마지막 조언 (Sonnet)
5. (검수자 버튼) 섹션 재윤문 (Haiku, 기존 llm_polish)

## 금지 (절대)
- LLM에게 계산 위임: 양음력 변환, 절기/월주, 일주/시주, 대운/세운/월운, 십성/오행/합충, 격국/용신, 자미 명궁/성요/사화/대한 — 전부 deterministic 엔진 전용.
- 전체 PDF 원샷 LLM 생성.
- Claude/ChatGPT 웹 UI 헤드리스 자동화로 고객 주문 처리 (약관·계정·장애·개인정보 리스크). 런타임 LLM은 Anthropic 공식 API만.
- 슬롯 외 사실 생성: 프롬프트에 주어진 evidence_slots/사실 슬롯에 없는 간지·별·수치·사건 언급 금지(factcheck 하드 차단).
- 검수 없는 LLM 출력 발송.

## 모델·비용
- 분류/재윤문 = claude-haiku-4-5 (저비용), 통합/답변/조언 = claude-sonnet-4-6 (품질).
- 무키(ANTHROPIC_API_KEY 부재) 시 전 구간 룰 폴백 = 비용 0 (기존 llm_polish 패턴 유지).
- 호출 로그(모델·토큰·섹션) audit_log 집계 — 건당 비용 가시화.

## 출력 계약 (contract)
- 모든 LLM 출력은 safe_lint + factcheck 재검증 통과 전 사용 불가. 실패 시 룰 폴백 + needs_review 플래그.
- Instructor + pydantic 스키마 강제. 자유 텍스트 직접 수용 금지.
- 프롬프트 버전 관리: prompts/ 파일 + audit_log 기록. 프롬프트 변경 시 골든 케이스 6종 가드 clean 재확인 후 반영.
