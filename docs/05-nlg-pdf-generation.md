# 05. NLG / PDF Generation

> 최초 작성: 2026-06-10

## 규칙 기반 섹션 (기존 27섹션 — content/rules.py, 변경 최소)
cover, summary, howto, keywords, wonguk, ohaeng, ilgan, sipseong, strength, character, geukguk, shinsal, love, job, wealth, health, daewoon, thisyear, seun, monthly, ziwei_summary, ziwei_palaces, cross, advice, caution, questions, appendix_terms, closing, next (+상품 토글 integrated/myeongni/ziwei).
- 입력: Unified JSON. 검증: safe_lint + factcheck + trace (기존 3단 가드).
- 시진 불명: 자미 계열 섹션 생략(명리 단독 강등) — docs/03 §1.

## LLM 사용 섹션 (현재 16챕터 조립 — content/builder.py·llm_sections.py)

| 역할 | 모델 | 입력 | 검증 | 폴백 |
|---|---|---|---|---|
| 질문 분류 | Haiku+Instructor | 고민 텍스트만 | enum 강제 | domain=etc |
| 개인 풀이 12챕터 | Sonnet | 챕터별 룰 골격+검증 사실 슬롯+PII 없는 공통 ReportContext | 3단 가드+챕터별 확장 lint | 해당 챕터 룰 골격 |
| 신청 질문 답변(12챕터 중 consult) | Sonnet | nature+flow+consult 근거와 마스킹·격리된 질문 | 가드+관리자 필수 검수 | consult 룰 골격 |
| (검수자) 재윤문 | Haiku (기존 llm_polish) | 선택 섹션 룰 원문 | 기존 가드 | 룰 원문 |

- Sonnet compose 대상은 intro·wonguk·nature·frame·love·work·health·flow·ziwei·together·consult·closing이다.
- cover·toc·appendix_terms·colophon은 정적이다. 현재 개인 상품의 자동 Haiku 윤문 전용 챕터는 0개이며, Haiku polish는 검수자 재윤문 경로로 남는다.
- 각 Sonnet 호출은 다른 챕터의 LLM 산문을 받지 않는다. 대신 선택 모듈·질문 카테고리·챕터 소유 주제·승인 용어 풀이 ID를 담은 결정론적 ReportContext를 공통으로 받아 목소리와 범위를 맞춘다.
- 통합 관점 프롬프트에 docs/03 §5 규칙을 내장한다: 명리 우선, 상충=층위 재서술, "모순" 단어 금지, 정확도 주장 금지.
- 프롬프트 정본은 `docs/14-tone-spec.md`, 런타임 구현은 `sajugen/content/llm_sections.py`다. 계약 테스트가 문서 rule ID와 코드 lint를 양방 대조한다.

## 반복 표현 검출 (content/repetition.py, 신규)
- 문장 단위 3~5 n-gram 중복률 측정. 임계치(초안: 동일 4-gram 3회 이상) 초과 시 관리자 화면 하이라이트.
- 자동 차단은 아님(하이라이트만) — 룰 골격 특성상 일부 반복은 정상.

## PDF (기존 유지)
- Jinja2 + Playwright Chromium tagged + veraPDF 측정(7.1-3 비악화 게이트). 폰트 Pretendard+Source Han Serif K(OFL) 임베드.
- 말미에는 브랜드 서명 슬롯만 둔다. 고객 PDF 본문에는 도구·AI·프로그램 산출 고지를 넣지 않는다(절대규칙18). 윤달 출생 시에는 산입 기준을 자동 고지한다.
