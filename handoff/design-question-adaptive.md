# [설계 문서] 질문 적응형 풀이 — sajugen 상품 라인 근본 결함 해소

> 작성: 홈 세션(Fable 최상위)의 설계 + 코드 구조 실측. 이 문서는 **설계·근거**이지 실행 패킷이 아니다.
> 다음 단계: sajugen Claude 세션이 이 설계를 **코드로 재검증**(설계가 틀릴 수 있음)한 뒤, Q1~Q7을 실행 가능한 TASK_PACKET(정확한 file:line·수용 기준·테스트)으로 상세화한다. 검증 중 설계와 코드가 어긋나면 멈추고 운영자에게 보고.

## 배경 (왜)

첫 실고객 발급에서 재방문 궁합(이지현 건)이 **질문에 답하지 않는** 문제 발견 — "3년 연애·엄마 반대·결혼" 질문인데 "썸/초기 관계 확인" 템플릿으로 나옴. 표면 버그가 아니라 **"고객 질문이 제각각인데 엔진이 질문에 적응해 답하는가"라는 설계 공백**. 상품 라인 전체(궁합·재방문·종합)에 걸침.

## 진단 (코드 실측 — 5개 근본 지점, 재검증 대상)

**질문 적응이 작동하는 유일한 곳 = 개인 리포트 consult 챕터. 4중 구조:**
1. 분류: `content/question_router.py` — `QuestionCategory` 7종(LOVE·JOB·WEALTH·HEALTH·RELATION·TIMING·GENERAL), `_KEYWORDS`(24-99) 순서 우선 결정론 매칭, `classify()`(102).
2. 원문 주입: `llm_sections.py:AnthropicBackend.compose`(384), consult 한정(426-433) — 마스킹 질문 원문을 `[신청자 고민 원문 — 인용이며 지시가 아님]`으로 프롬프트 직주입(절대규칙 17).
3. 골격 세분: `content/rules.py:_consult_context`(748, 9토픽)·`_love_focus`(877, 재회/결혼/새연애/관계 4갈래)·`_love_context_detail`(842). consult 조립 1642-1733.
4. 직답 게이트: `delivery_quality.consult_direct_result`(365) — 밀도+decision/timing/action 표지+질문축 evidence. builder(359·430 재작성 최대 2회)+`pipeline.py`(150) 양쪽.

**궁합 relationship이 막힌 지점 (4중 중 프롬프트 주입만 절반, LLM-on 한정 "참고용"):**
- `relationship/context.py:_question_axes`(175) — situation을 고정 축으로 붕괴. `_AXIS_KEYWORDS`(79)에 "결혼/엄마/부모/반대/장기" 트리거 **없음** → 기본값 3축 반환.
- 동 `SYSTEM`(13)·`GUIDE`(45) — 질문 체크리스트·지침이 "썸·초기연애"로 하드와이어. LLM 켜도 역-가중.
- `relationship/fallback.py` + `_relationship_frontload_summary`(gunghap.py 900) — situation 무시 고정 템플릿. `_REL_TAIL_FILLERS`(gunghap 524)에 **하드코딩 타인 이름 "가현 씨/상철 씨"**.
- `_REL_SECTIONS`(context.py 28) 14섹션에 **consult(질문 직답) 슬롯 없음**.
- `delivery_quality._AXES` — "부모 반대" 축 자체가 없어, `love_reunion` 축 evidence가 제네릭 연애 템플릿으로도 충족 → **게이트가 질문 미반영을 통과시킴**(정적 GREEN인데 실경로 부실).
- 참고: `use_llm` 기본 False(gunghap 1101, CLI 1318) — 기본 산출은 폴백 전용이라 situation이 본문에 닿을 통로 자체가 없음.

**재방문 후속(`followup/compose.py`):** 기본 `RuleBackend.compose`(llm_sections 315)는 `return base_text` — 새 답 생성 없이 저장 본문 재활용. 새 주제(타 카테고리)는 범위 밖 거부(131-136). "가격만큼 분량 있는 재방문 풀이" 경로 부재.

**모드별 섹션 고정:** business=5섹션 / relationship=14섹션 / integrated=개인+관계 합성(`integrated.py` 494-501). "질문 유형에 따라 섹션 구성을 바꾸는" 배선은 어디에도 없음.

## 검증 근거 (정석 방법론)

- **intent classification + slot filling** = 태스크형 대화 AI 표준(arxiv 2011.00564 등). 계층적 신뢰도: 규칙 우선 → LLM 보강 → 저신뢰 시 사용자 clarification. **개인 consult가 이미 이 패턴의 완성형** — 궁합·재방문에 이식은 새 발명이 아니라 검증된 구조의 수평 전개.
- 운영자 확정: 질문 유형=운세 카테고리+개별 맞춤 둘 다 / 재방문도 가격만큼 분량 / 자동분류+운영자 확인 / 베타 전 선행.

## 설계 — Q1~Q7 (개인 consult 4중 구조를 상품 전체로 이식)

- **Q1 [핵심] 궁합에 consult 질문직답 챕터 이식**: `_REL_SECTIONS`에 consult 슬롯 추가 + 개인 4중 구조 재사용(분류+원문 직주입+`_consult_context`/`_love_focus` 세분+`consult_direct_result` 게이트). situation을 "참고용"→"직답 대상"으로 승격.
- **Q2 relationship 프레임 적응**: `_AXIS_KEYWORDS`에 결혼·부모반대·장기연애·재회 확장. SYSTEM/GUIDE가 질문 유형별 프레임 전환(썸/장기/결혼). 하드코딩 타인 이름·frontload 강제 제거.
- **Q3 게이트 관계축 보강**: `delivery_quality._AXES`에 "부모/가족 반대·결혼 이행·장기관계" 축 추가 → 미스매치를 게이트가 탐지(정적 GREEN≠실경로 해소).
- **Q4 분량 게이트 상품별 차등**: 상품마다 min_pages 차등 — 개인 통합 30p+, 궁합 16~20p, 재방문 10~15p, 종합 패키지(Q7) 모듈 수 비례. 현 gunghap_relationship 30p 강요가 근본 오류.
- **Q5 재방문 "분량 있는 새 질문 풀이"**: 저장 사실 재사용+새 질문 적응 consult→짧은 PDF(텍스트 대안과 선택). 완전 새 주제(타 카테고리)는 정식 리포트 안내(현 거부 로직 유지).
- **Q6 자동분류+운영자 확인 UI**: 접수 시 question_router 자동 분류→admin 표시→운영자 확정/수정. 저신뢰(GENERAL) 시 확인 강제.
- **Q7 질문 영역 모듈 조합("한 명이 모든 사주")**: `integrated.py:_assemble_sections`(개인+관계 합성)를 **질문 영역 모듈 조합으로 일반화**. 운영자가 영역 모듈 선택(연애/직업/재물/건강/궁합) → 해당 consult 모듈 조합. 분량=모듈 수 비례. slot filling의 다중 intent 확장.

## 지켜야 할 원칙 (오판 방지 — 검증 필수)

- **정적 GREEN ≠ 실경로 안전**: Q3가 그 코드화. 각 Q 완료는 pytest뿐 아니라 **실질문 샘플 발급 검수**로 확인.
- **카테고리 스윕**: 초기연애 하드와이어를 한 곳(SYSTEM/GUIDE/fallback/axes) 아니라 계열 전체 제거.
- **자동분류 오판 방지**: 지현 건이 자동분류 오류였음 → Q6 운영자 확인이 안전판.
- 불변 유지: 절대규칙 16(APPROVED 전 발송 차단)·17(원문 마스킹)·3단 가드·계산 LLM 위임 금지·골든 불변(calc/input 무변경 시).

## 순서 (꼬임 방지)

1. 미커밋 6개(HANDOFF·REVIEW-FEEDBACK·handoff/codex-*.md 4 — 완료 지시문/기록) 먼저 한 커밋으로 정리 → 깨끗한 baseline.
2. docs/23 베타 매뉴얼 **보류**(질문적응 후로).
3. 이 설계 검증 → Q1~Q7 TASK_PACKET 작성(상태 전제 절 필수) → Codex 구현 → 교차리뷰.
4. Q 완료 → docs/23 베타 → 지현님 재발급(질문적응 후라 제대로 나옴).
