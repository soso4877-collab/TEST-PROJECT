# 06. LLM Usage Policy

> 최초 작성: 2026-06-10. 개정: 2026-06-11(절대규칙15·17 운영자 승인 — LLM 챕터 작성 확대·고민 원문 전달).
> 이 문서는 강제 정책이다 — 위반 구조는 코드 리뷰에서 반려.

## 허용 (챕터 단위 '근거 슬롯 기반 작성' + 분류 + 재윤문)
- 고객 고민/질문 분류 (Haiku, enum 강제)
- 해석 챕터 LLM 작성 (Sonnet): intro·wonguk·nature·frame·love·work·health·flow·ziwei·together·consult·closing.
  각 챕터는 결정론 룰 골격 + 검증된 계산 사실 슬롯(rules.<chapter>_facts: 간지·오행·십성·신살·궁·세운 연도 등)만을
  근거로 작성. 12개 챕터는 서로의 LLM 산문을 전달받지 않으며, PII 없는 결정론 ReportContext만 공유한다.
- 신청 질문 답변 (consult, Sonnet, 관리자 필수 검수) — 고객 고민 원문을 마스킹·격리 블록으로 전달해 개인화(절대규칙17 개정).
- (검수자 버튼) 섹션 재윤문 (Haiku, 기존 llm_polish)
- 경계(핵심): 챕터별 개별 근거 슬롯 기반 작성만 허용 — 전체 PDF 원샷 freeform 생성은 금지. 근거 밖 사실은 factcheck 하드 차단.

## 금지 (절대)
- LLM에게 계산 위임: 양음력 변환, 절기/월주, 일주/시주, 대운/세운/월운, 십성/오행/합충, 격국/용신, 자미 명궁/성요/사화/대한 — 전부 deterministic 엔진 전용.
- 전체 PDF 원샷 LLM 생성.
- Claude/ChatGPT 웹 UI 헤드리스 자동화로 고객 주문 처리 (약관·계정·장애·개인정보 리스크). 런타임 LLM은 Anthropic 공식 API만.
- 슬롯 외 사실 생성: 프롬프트에 주어진 evidence_slots/사실 슬롯에 없는 간지·별·수치·사건 언급 금지(factcheck 하드 차단).
- 검수 없는 LLM 출력 발송.

## 모델·비용
- 분류/검수자 재윤문 = claude-haiku-4-5 (저비용), 12챕터 compose = claude-sonnet-4-6 (품질).
- 현재 개인 상품 자동 생성 경로에서 Haiku 윤문 전용 챕터는 0개다. 본문 비용의 중심은 Sonnet 12개 compose이며, 모델 전환은 합성 A/B와 비용 승인을 분리한다.
- 무키(ANTHROPIC_API_KEY 부재) 시 전 구간 룰 폴백 = 비용 0 (기존 llm_polish 패턴 유지).
- 5분 explicit prompt caching은 정적 시스템 규칙+동일 PDF ReportContext prefix에만 적용한다. 캐시는 비용 최적화이며 가드나 사실 경계를 바꾸지 않는다.
- 호출 로그는 PII 없이 role·model·section·attempt·일반 입력·cache 생성/읽기·출력·thinking·stop_reason을 집계한다. 기존 calls/input/output 합계 소비자는 하위호환한다.

## 출력 계약 (contract)
- 모든 LLM 출력은 safe_lint + factcheck 재검증 통과 전 사용 불가. 실패 시 룰 폴백 + needs_review 플래그.
- 질문 분류는 Instructor+pydantic enum을 강제한다. 챕터 compose는 plain text이지만 safe_lint+factcheck+trace와 확장 lint를 모두 통과한 경우에만 수용한다.
- 프롬프트 정책 정본은 `docs/14-tone-spec.md`, 런타임 구현은 `llm_sections.py`다. 프롬프트 변경 시 합성 양방 회귀와 전체 가드 clean을 확인한다.
