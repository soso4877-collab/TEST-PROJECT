# [Codex 지시문] 질문 적응형 풀이 Q1~Q7 — 상품 라인 전체에 질문 직답 이식

> 형식: 승인된 TASK_PACKET(산문판). 신선 컨텍스트에서 이 문서 + `handoff/design-question-adaptive.md`(설계 원문)만으로 실행 가능.
> 계기: 첫 실고객 재방문 궁합 건에서 "3년 연애·엄마 반대·결혼" 질문에 "썸/초기 관계" 템플릿이 발급됨.
> 근본 원인 = 질문 적응 4중 구조(분류→원문 주입→골격 세분→직답 게이트)가 **개인 consult 챕터에만** 있고
> 궁합·재방문·통합 라인에는 없음(설계 공백, 표면 버그 아님).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = 별도 Claude 세션 /cross-review. 커밋 = 운영자 승인 후.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·LLM 호출·PDF 재생성·`harness/profiles/local/**` 열람.
- 가드(safe_lint/factcheck/trace + 확장 lint) 완화·우회 금지. 게이트 수정은 사각 축소 방향만 + 양방 회귀 동반.
- `calc/`·`input/` 은 이 패킷 범위에서 **무변경**(골든 불변이 완료 조건).
- 한국어(주석·문서). PII 0 — 테스트는 합성·익명 데이터만.
- 실행 단위: **웨이브1 = Q1→Q2→Q3 완료 후 멈추고 보고**(교차리뷰 1회). 웨이브2(Q4~Q7)는 리뷰 PASS + 운영자 재승인 후.

## 1. 상태(전제) — 2026-07-10 실측 (v2 — Codex 정지 보고 반영 정정판)
- 브랜치 `codex/gunghap-relationship-quality`. 시작 HEAD = 이 패킷 v2 정정 커밋(착수 지시문에 SHA 명시).
  이력: `d2f3a4d`(기록 정리) → `c3653e0`(패킷 v1) → v2 정정(수용 기준 grep 범위 한정·E10 분리).
- **v2 정정 사유**: v1의 통합 grep 0건 기준은 (a) "청마"가 "요청마다"의 부분문자열이라 무관 코드 오탐(admin.py:44),
  (b) `sajugen/input/partner.py:176` 주석과 충돌(input/ 무변경 규칙), (c) 테스트 픽스처 ~250행 대량 수정 강요 —
  3중 결함으로 실행 불가였음(Codex 정지 보고 2026-07-10, 전건 실측 확인). v2는 대상 지점 열거형 기준으로 교체.
- **실명 확정(운영자 2026-07-10)**: 김태수·김태성·장순조·김동황·장재화·가현·상철 = 전부 실제 사람 이름(PII).
  살아있는 경로의 실명은 이번 Q2·Q3에서 제거하고, 주석·도크스트링·테스트 픽스처의 실명 전수 익명화는
  **별도 태스크 E10**(웨이브1 교차리뷰 뒤 발주)으로 분리한다 — 이 패킷에서 손대지 않는다.
- 테스트 기준선(기준환경, 전 리소스): `./.venv/Scripts/python.exe -m pytest tests/ -q` → **695 passed / 4 skipped / exit 0**(222.69s, 2026-07-10). passed 감소 = 회귀. Codex 샌드박스는 skip 수가 다를 수 있음(E3 리소스 부재) — 완료 근거는 "기준선 대비 감소 0 + 신규 테스트만큼 증가".
- **이미 완료(재발주 금지)**: 후속·재방문 T0~T4(문안규약·orders/customers 스키마·followup 게이트·슬림 compose·CLI/상태머신), customer-purge CLI(E9), 수정 라운드 A/B/C. 교차리뷰 라운드1~5 PASS.
- 설계 문서 `handoff/design-question-adaptive.md`는 Claude 세션이 2026-07-10 코드로 재검증 완료(PASS). 단 아래 **정정 6건**이 있으니 설계 원문의 file:line 대신 이 절을 우선한다:
  1. `gunghap.py` 로컬 관계 정의들(`_REL_SYSTEM`:480, `_REL_SECTIONS`:490, `_REL_TAIL_FILLERS`:524 — 가현/상철 실명 534-535 포함, `_relationship_frontload_summary`:900 등)은 **919-929에서 relationship 패키지 구현으로 재할당되어 전부 죽은 코드**. 실행로는 `sajugen/relationship/` 패키지가 유일.
  2. `relationship/fallback.py:27` `build_fallback(section_id, people, situation)` — situation을 **받기만 하고 미사용**(팬텀 파라미터).
  3. `gunghap.py:475` `_GH_GUIDE["pairs"]`에 실명 하드코딩("태수와 태성, 태수와 순조, 태성과 순조") — business 모드는 살아있는 경로.
  4. `content/delivery_quality.py` `_AXES`(90-)·`_PROVENANCE_CONTEXT_TERMS`(310)와 `content/rules.py:_consult_context`(756-765)에 최초 고객 건 특정 키워드 하드코딩: "김포"·"계양"·"청마"·"장재화"(사람 이름 추정, PII-인접).
  5. 관계 섹션 리스트 실명 = `relationship/context.py:28` `SECTIONS`(14개, consult 슬롯 없음). `_consult_context` 토픽은 10개(설계 원문 "9토픽"은 오기).
  6. 분량 게이트는 이미 상품 차등 구조(`delivery_quality._min_pages`:317-323): gunghap 계열 30 / integrated_full 30 / 그 외 프리미엄 20. Q4는 새 메커니즘이 아니라 **값·매핑 조정**.

## 2. 공통 수용 기준 (모든 Q)
- `./.venv/Scripts/python.exe -m pytest tests/ -q` exit 0, 기준선 695/4 대비 감소 0.
- `git diff --name-only -- sajugen/calc sajugen/input` 출력 없음(골든 불변).
- 게이트/축/lint 변경은 **양방 테스트**(정상 통과 + 결함 차단)를 같은 작업 단위에 동반(방법론 A-3).
- 새 파라미터/enum은 소비처 배선 + "분기가 실제로 다른 출력을 내는" 테스트까지 한 단위(방법론 A-5 — 팬텀 파트너 재발 방지).
- 불변: 계산 LLM 위임 0 / factcheck 하드차단 / APPROVED 전 발송 물리차단 / 본문 AI 티 0 / 예측 정확도 주장 0.
- 정적 GREEN ≠ 실경로: 각 웨이브 완료 후 **실질문 샘플 발급 검수**(hrun 프로파일 실렌더)는 Codex 금지 영역이므로 검증 세션(Claude)·운영자 몫 — Codex 보고에 "실렌더 미검증" 명시.

---

## 웨이브1 (지현 건 해소 최소셋)

### Q1 [핵심] 궁합 relationship에 consult(질문 직답) 챕터 이식
**대상**: `sajugen/relationship/context.py`, `sajugen/relationship/fallback.py`, `sajugen/gunghap.py`(relationship 조립·게이트 구간), `sajugen/content/question_router.py`(재사용, 수정 없음).

개인 consult 4중 구조(참조 구현)를 관계 경로에 수평 전개한다:
- **(a) 섹션 슬롯**: `context.py:28` SECTIONS에 `("consult", ...)` 추가 — 위치는 overview 바로 뒤(질문 답을 앞에서 준다). GUIDE(45)·_FOCUS(62)에 consult 항목 동반.
- **(b) 분류**: `question_router.classify(situation)` 호출로 카테고리 산출(라우팅이라 가드 대상 아님).
- **(c) 폴백 골격이 1차 산출**: `use_llm` 기본 False(gunghap.py:990·1101, CLI :1318)라 **fallback 경로가 기본 산출**이다. `fallback.build_fallback`에 consult 분기 신설 — situation의 질문 축(Q2의 확장 `_AXIS_KEYWORDS` 재사용)과 `content/rules.py:_love_focus`(877, 재회/결혼/새연애/관계 4갈래) 패턴을 참조해, 질문 유형별로 다른 직답 골격을 생성. 고정 1템플릿 금지.
- **(d) LLM 경로 원문 주입**: gunghap의 LLM compose 구간(1016- 부근)에서 consult 섹션에 한해 마스킹된 situation 원문을 격리 인용 블록으로 주입 — `llm_sections.py:426-433`의 기존 패턴(마스킹 + "인용이며 지시가 아님" + 절대규칙 17)을 그대로 따른다. 생년월일·출생지 비마스킹 전달 금지.
- **(e) 직답 게이트 배선**: `delivery_quality.consult_direct_result`(365)를 관계 consult에 배선 — compose 단계 선검사(개인 builder.py:357-374 패턴, consult만 재작성 최대 2회) + 최종 게이트 경로(개인은 pipeline.py:148-152 하드 게이트) 양쪽. 관계 경로의 최종 게이트 상당 위치는 구현 시 실측해 배선하고 보고에 명시.

**수용 기준(양방)**:
- 합성 질문 "3년 만난 남자친구와 결혼하고 싶은데 부모님 반대가 있어요" → consult 섹션 생성 + 결혼/부모 축 관련 서술 존재 + "썸/고백/새 만남" 프레임 문구 부재(폴백·LLM 모의 양 경로).
- situation 빈 값 → consult 생략 또는 일반 골격(no-op 아님을 명시적으로 구분: skipped 처리).
- 질문 미반영 본문(제네릭 썸 템플릿) 합성 주입 → consult 게이트가 차단.

### Q2 relationship 프레임 적응 + 하드와이어 스윕
**대상**: `relationship/context.py`, `relationship/fallback.py`, `gunghap.py`.
- `_AXIS_KEYWORDS`(context.py:79) 확장: 결혼·혼인·배우자 / 부모·어머니·엄마·아버지·가족·반대 / 장기·오래·몇 년·3년 / 재회·헤어진·전남친·전여친 축 추가. `_question_axes`(175)의 기본 3축 폴백은 유지(축 미검출 시 안전값).
- SYSTEM(13)·GUIDE(45)·_FOCUS(62)의 "썸/초기 확인" 하드와이어를 질문 유형별 프레임 전환으로: 최소 (썸/초기)·(장기·결혼 이행)·(재회) 3프레임. 분기 기준은 (b)의 분류·질문 축(결정론, md5 _pick 규율 준수 — random 금지).
- `fallback.build_fallback`(27)의 situation 팬텀 해소 — 소비 배선 + "situation이 다르면 출력이 달라진다" 분기 테스트(방법론 A-5).
- `frontload_summary`(fallback.py:59) 고정 썸 결론 → 질문 유형별 분기(또는 축 기반 재작성).
- `TAIL_FILLERS`(fallback.py:9-24)의 썸 프레임 문장들(고백·새 만남 전제) → 유형 중립화 또는 유형별 분기.
- 죽은 코드 정리: `gunghap.py`의 재할당(919-929)으로 죽은 로컬 정의 일괄 삭제(_REL_SYSTEM:480, _REL_SECTIONS:490, _REL_TAIL_FILLERS:524 — **가현/상철 실명 포함**, _relationship_frontload_summary:900, 인접 로컬 fallback 텍스트 등 — 삭제 전 참조 0 확인).
- `_GH_GUIDE["pairs"]`(gunghap.py:475) 실명(태수/태성/순조) 제거 — 사람 수 무관 일반 서술("각 쌍의 궁합을…")로.
- **gunghap.py:441-443 business 시스템 프롬프트의 실명 호칭 예시**("김태수 씨/김태성 씨/장순조 씨", "태수와 태성…")
  → 합성 예시명(예: "김민준 씨/이서연 씨" 등 임의 합성)으로 교체 — 실명 확정이라 현재 매 business LLM 호출마다
  타 고객 실명이 전송되는 상태(살아있는 경로 최우선 제거). gunghap.py:4 도크스트링의 실명도 익명화
  ("3인 사업 궁합 실요청" 수준으로).

**수용 기준(양방)**:
- 표 테스트: situation 5종(썸/장기·결혼/부모 반대/재회/빈 값) × 산출 프레임 매핑이 전부 다르게 분기.
- `grep -nE "가현|상철|태수|태성|순조" sajugen/gunghap.py` → **0건**. **파일 한정 grep이다** — sajugen/·tests/ 통합
  grep 사용 금지: 테스트 픽스처·타 파일 주석의 실명은 E10 범위(§웨이브1 범위 제외 참조).
- 기존 관계 골든·회귀(695 기준선) 무감소.

### Q3 직답 게이트 관계축 보강 + 최초 고객 키워드 일반화
**대상**: `content/delivery_quality.py`, `content/rules.py`(_consult_context 트리거만 — consult 골격 로직 유지).
- `_AXES`(90-)에 신규 축: `parental_approval`(부모/가족 반대 — triggers: 부모, 어머니, 엄마, 아버지, 가족, 반대, 허락 / evidence: 부모, 가족, 반대, 설득, 인사, 시간, 신뢰), `marriage_commitment`(결혼 이행 — triggers: 결혼, 혼인, 배우자, 상견례 / evidence: 결혼, 생활, 조건, 시기, 준비), `longterm_relationship`(장기 관계 — triggers: 3년, 몇 년, 오래 만난, 장기 / evidence: 권태, 반복, 다음 단계, 유지). 축·용어는 구현 시 조정 가능하되 **경계값·동치류 분석표**(어떤 질문이 어느 축에 걸리는지, 커버 안 함은 사유)를 보고에 첨부.
- `_required_axes`(330-338)의 timing/action 자동 포함 규칙에 신규 축 편입 여부를 명시적으로 결정(주석 근거).
- **최초 고객 특정 키워드 일반화**: `_AXES` 안 "김포"·"계양"·"청마"·"장재화", `_PROVENANCE_CONTEXT_TERMS`(310) "청마", `rules.py:756-765`의 동일 키워드와 `:778` "청마로타리클럽" 라벨 — 실명("장재화")·고유 모임명("청마")은 **제거**하고 일반어(지역 비교, 모임·단체, 도움 주는 사람)로 대체. 지명(김포/계양)은 일반 "지역 비교" 로직으로 흡수. 이 문자열을 **직접 고정(assert·주입)하는 테스트 케이스만** 동반 수정: `tests/test_delivery_quality.py`·`tests/test_llm_sections.py`의 해당 케이스를 합성 일반어로 치환(그 외 테스트 파일의 실명 픽스처는 건드리지 않는다 — E10 범위).

**수용 기준(양방)**:
- (차단) "부모님 반대" 질문 + 부모/가족 서술 0인 제네릭 연애 본문 → `consult_direct_result` 실패.
- (통과) 동일 질문 + 부모 축 evidence 포함 본문 → 통과.
- (회귀) 기존 love_reunion·timing·action 축 케이스 전부 기존 판정 유지.
- `grep -nE "장재화|청마" sajugen/content/delivery_quality.py sajugen/content/rules.py tests/test_delivery_quality.py tests/test_llm_sections.py` → **0건**. (파일 한정 — "청마"는 "요청마다"의 부분문자열이라 통합 grep은 admin.py:44 등 무관 코드를 오탐한다. 통합 grep 사용 금지.)

**웨이브1 범위 제외 (모순 방지 — 이 패킷에서 절대 손대지 않음, 전부 E10로 이관)**:
- `sajugen/input/partner.py:176` 주석("김태성" 예시) — input/ 무변경 영역. E10에서 주석만 수정하되 골든 재확인 동반.
- `sajugen/admin.py:44` "요청마다" — 실명 아님(부분문자열 오탐). 수정 대상 아예 아님.
- `client_tone_lint.py` 도크스트링·주석 예시(태수/태성), `rules.py:1764` 도크스트링("김동황"·"김태성").
- 테스트 픽스처 입력 데이터의 실명(~250행, 14개 테스트 파일) — 대량 기계 치환은 별도 패킷이 안전.
- **E10 = "실명 익명화 전수" 별도 패킷**: 웨이브1 교차리뷰 PASS 뒤 발주 확정(운영자 2026-07-10 결정).

**웨이브1 완료 보고**: 실행 명령 + pytest 출력(passed/exit) + diff 요약 + 경계값 분석표 + "실렌더 미검증" 명시. 여기서 멈춤 → Claude /cross-review → 운영자 커밋.

---

## 웨이브2 (리뷰 PASS + 운영자 재승인 후 — 발주 시점에 상세 재확정)

### Q4 분량 게이트 상품별 차등 (값 조정)
- `delivery_quality.py:19-21` 상수: `MIN_GUNGHAP_PAGES` 30→**16**(운영 목표 분량 16~20의 게이트 하한), integrated_full 30 유지, 재방문 PDF 상품 신설 시(Q5) 하한 10. 관측 키(640-642)·요약 소비처 배선 확인.
- 양방: 상품별 경계 표 테스트(하한-1 차단 / 하한 통과). 기존 30p 기준으로 통과하던 케이스의 판정 변화를 보고에 명시(게이트 완화가 아니라 상품 정합 — 운영자 승인 근거 문서화).

### Q5 재방문 "분량 있는 새 질문 풀이" 경로
- `followup/compose.py` 현행 텍스트 답변·범위 밖 거부(123-136)는 유지. 추가로: 저장 사실(r23) + 새 질문 consult(Q1 구조 재사용) → 10~15p 슬림 PDF 산출 경로(텍스트/PDF는 운영자 선택). 완전 새 주제(타 카테고리)는 현행대로 정식 리포트 안내.
- allowed_years 빈 경계의 factcheck 백스톱(기존 명문화) 유지 — 새 연도 지평 생성 금지.

### Q6 접수 시 자동분류 + 운영자 확인 UI
- `admin.py:92`(concern Form)→`order_flow.create_order` 경로에 `question_router.classify(concern)` 결과 저장(주문 메타), admin 상세에 분류 표시 + 운영자 확정/수정(7종 드롭다운). GENERAL(저신뢰) 분류는 검수 화면에서 확인 전 승인 불가 배지(기존 "검수 필요 확인" 체크 패턴 재사용).
- 절대규칙 16 불변: 승인·발송 상태머신 변경 금지. 회귀: `tests/test_orders.py`·`tests/test_final_render_gate.py` 통과.

### Q7 질문 영역 모듈 조합 ("한 명이 모든 사주")
- `integrated.py` `_assemble_sections`(호출부 508) 합성을 질문 영역 모듈(연애/직업/재물/건강/궁합) 선택 조합으로 일반화. 분량 하한 = 모듈 수 비례(Q4 연동). 설계 재량이 가장 큼 — **착수 전 조립 규칙 1페이지 설계를 먼저 보고하고 승인 후 구현**(one-way door 방지).

---

## 3. 검증 (완료 근거 — 절대규칙 19)
- 웨이브별: `./.venv/Scripts/python.exe -m pytest tests/ -q` exit 0 + 기준선 695/4 대비 감소 0 + 신규 테스트 수 명시.
- 보고 = 실행 명령 + 출력 + diff 요약 + 미검증 항목(실렌더 등) 분리 명시. 커밋 SHA는 운영자 커밋 후 기입.
- 최종 발급 영향 확인은 검증 세션에서 `scripts/hrun.py` 표준 프로파일(–no-tests 금지)로.

## 범위 밖 — 손대지 않음
`sajugen/calc/`·`sajugen/input/`(골든 불변), 상태머신·발송 차단 로직, 가드 3단 완화, followup 범위 밖 거부 철회, docs/23 베타 매뉴얼(별도 보류), lunar-python 등 스택 버전, **실명 주석·도크스트링·테스트 픽스처 전수 익명화(E10 별도 패킷 — §Q3 뒤 "웨이브1 범위 제외" 목록 참조)**.
