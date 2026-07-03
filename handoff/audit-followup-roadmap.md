# sajugen 감사 후속 수정 — 구현 세션용 실행 지시문 (전체 로드맵 분할형)

> 이 문서는 2026-07-03 전수 감사(기준: tmp/audit_brief.md)의 산출물이다.
> 감사 세션은 조사만 수행했고(수정·커밋·push·재생성 0건), 이 지시문이 구현의 source of truth 다.
> 발견 항목의 상세 근거(파일:라인·실측·출처 URL)는 이 문서 하단 [부록 A~C]에 있다 — 각 태스크의
> ID(P0-1, A-1, B-2 …)로 참조한다. 작업 전 해당 ID 의 부록 항목을 반드시 읽어라.

## 0. 세션 운영 프로토콜 (모든 구현 세션 공통)

1. 한 세션 = 한 Phase. 이 문서의 Phase 1~5 중 STATE.md 가 가리키는 다음 Phase 하나만 수행한다.
   Phase 를 넘나들지 마라. 컨텍스트가 부족해지면 중단하고 STATE.md 에 진행 지점을 남긴 뒤 종료한다.
2. 시작 절차: (a) sajugen/STATE.md -> (b) CLAUDE.md -> (c) .claude/rules/00-immutable.md ->
   (d) 이 문서의 담당 Phase 절 + 해당 부록 항목 정독 -> (e) 착수 전 전체 테스트 1회 GREEN 확인:
   ./.venv/Scripts/python.exe -m pytest tests/ -q  (감사 시점 기준선 = 438 passed / 3 skipped / exit 0)
3. 완료 절차(각 Phase): 전체 pytest GREEN -> STATE.md 활성 워크플로우 블록 갱신(수행 태스크 ID·실측
   결과·다음 Phase 명시) -> 한국어 Conventional Commit(논리 1변경=1커밋, 태스크 ID 를 본문에 기재).
   push 는 운영자 지시 시만. 고객 PDF 재생성/발송 금지(운영자 명시 승인 필요).
4. 보고 규율: 검증하지 않은 것을 "완료/해결"이라 쓰지 마라. 각 태스크의 "검증" 항목을 실측한 값으로만
   보고한다. 실패하면 실패로 보고하고 원인 조사를 남긴다.

### 0-1. 불변 가드 (위반 시 그 자리에서 중단)

- 계산은 LLM 위임 금지. 게이트/가드/차단룰의 완화 금지 — 이 지시문의 게이트 수정은 전부 "사각 축소"
  방향이며, 기존에 잡던 것을 놓치게 되는 변경은 반려 대상이다. 각 게이트 수정은 (정상 케이스 통과 +
  결함 케이스 차단) 양방 회귀 테스트를 같은 커밋에 동반한다.
- calc/, input/ 수정은 같은 커밋에 테스트+골든 회귀 동반(절대규칙 20). 골든 22건 전수 GREEN 필수.
- 고객 PII(이름/생년월일/질문 원문/본문)를 채팅·로그·커밋·테스트 픽스처에 넣지 마라. 진단은
  page/char/coord/rule/bool 메타만. 예시는 DOC_A, CUSTOMER_1 익명 ID.
- 터미널 출력 ASCII 평문(이모지/장식기호 금지). Bash 로 PowerShell/cmd 실행 금지. 테스트는
  ./.venv/Scripts/python.exe -m pytest 만(bare pytest 금지).
- APPROVED 전 발송 금지. .env 값 출력 금지.

### 0-2. 운영자 기결정 사항 (2026-07-03 확정 — 재질문 금지)

- 자시 정책 = JST_2300 구현 완성 (문서 유지, 코드를 문서에 맞춘다): 진태양시 23:00~24:00 출생은
  일주를 익일로 전환한다. 야자시설로의 문서 개정안은 기각됨.
- 지시문 범위 = 전체 로드맵(Phase 1~5) 분할 수행.

---
## Phase 1 — PII/유출 봉쇄 (저위험·무회귀, 최우선)

### T1.1 [A-1] gitignore 보강 + PII 임시파일 처리
- .gitignore 에 tmp/, synthetic-tmp/, *.content.json 3줄 추가.
- 추가 후 git check-ignore tmp synthetic-tmp exit 0 확인.
- tmp/repro_c2.content.json, tmp/before_customer2.pdf, tmp/diag_customer2.pdf, tmp/diag_customer2.html,
  synthetic-tmp/integrated_full.content.json 은 고객 파생물 — 삭제 전 운영자에게 목록을 보여주고 확인
  (재compose 비용 방지용 저장본일 수 있음). 확인받으면 삭제, 아니면 sajugen/render/out/ 으로 이동.
- 검증: git status 에서 tmp/·synthetic-tmp/ 미표시.

### T1.2 [P0-2] 표지 polish 경로의 생년월일 원본 API 전송 차단
- 원인 체인: rules.py:899(표지에 input_civil 원문) -> cover 가 _STATIC_OK/_COMPOSE_SECTIONS 어디에도
  없음 -> builder.py:275-280 polish 분기 -> llm_polish.py:53 원문 그대로 API 전송.
- 수정: builder 의 polish 분기에서 cover 제외(표지는 정형 메타라 윤문 이득 0 — 룰 텍스트 그대로 사용).
  _STATIC_OK 에 "cover" 추가가 가장 단순하나, 추가 시 builder.py:368·402 등 _STATIC_OK 소비처의
  부작용(한자정리 skip 등)을 먼저 확인하고 안전한 쪽(분기 조건에 cover 명시 제외)을 택하라.
- 벨트: llm_polish.polish 입력에 masking 결정론 치환(입력 생년월일시 문자열 정확 치환) 추가.
- 검증(같은 커밋): 모의 백엔드로 polish 호출을 캡처해 생년월일 패턴(YYYY-MM-DD, HH:MM) 0건 단언 테스트.

### T1.3 [A-3+B-3] verify hit 본문 스니펫 제거 + raw 표면 정제
- verify.py:57 _orphan_pages 의 "text": s[:30], verify.py:193 _low_density_pages 의 "text": s[:40]
  필드 제거(필요 시 글자수만). 소비처(테스트 포함) 동반 갱신.
- scripts/hverify_pdf.py:232 delivery_quality 통째 forward -> _safe_hits 화이트리스트 정제로 교체.
- order_flow.py:217 어드민 리뷰 dict 의 "verify": r.verify -> rule/page/count/bool digest 로 교체
  (integrated.py:243 _pii_free_verify_digest 재사용/이동).
- [E-2] order_flow.py:175-181 audit note 의 예외 문자열 — 기록 전 masking 헬퍼 통과 일원화.
  orders.py delete reason 도 동일 헬퍼 적용.
- 검증: hverify_pdf --json 출력 전수에서 한글 본문 문장 0건 + 관련 테스트 GREEN.

Phase 1 완료 기준: 상기 검증 전부 실측 + 전체 pytest GREEN + STATE 갱신 + 커밋(push 안 함).

---
## Phase 2 — 계산 정확도 (calc/ — 골든 회귀 동반 필수)

### T2.1 [P0-1] 자시 정책 JST_2300 구현 완성 (운영자 기결정 — 0-2 절)
- 확정 실측: 1999-06-11 23:50 서울 -> day_offset=1 인데 엔진 일주=당일. 정책 enum 이 일주에 무효.
- 수정 3곳 동시(부분 수정 금지 — 명리<->자미 교차검증 축이 함께 움직여야 함):
  - calc/myeongni.py:140-147 — EightChar 생성 시 ct.day_offset 반영(익일 날짜로 Solar 생성 또는
    setSect(1)). 어느 방식이든 시지(hour_branch)·월주·연주가 안 흔들리는지 골든으로 증명.
  - calc/partner.py:121 — 동일 적용.
  - calc/ziwei.py — iztro 는 晚子時=당일 고정이므로, 23시대에 명리 일주가 익일이 되면
    engine.py:90-97 bazi_consistent(chinese_date 대조)가 깨진다. 자미 명반 자체는 자미 관례(당일) 유지
    (docs/03: 자미는 명반 구조 한정)하되, 교차검증 비교자를 "정책 반영 후 기대값" 기준으로 정정.
    이 결정(자미 명반은 당일 유지 + 교차 비교자만 정정)이 docs/03 결정표와 일관하는지 서술을
    docs/03 에 1줄 보강하고 STATE 에 기록.
- 골든(같은 커밋): 진태양시 기준 22:59/23:01/23:59/00:01 4케이스 + lunar-python 이슈 #32 케이스
  (1999-06-11 23:31 -> 익일 일주) 앵커 + 기존 골든 22건·전 테스트 GREEN. YAJASI_SPLIT 과 JST_2300 이
  서로 다른 일주를 내는 정책 분기 테스트 1건(현재 공백).
- 영향 보고: 수정 후 "결과가 달라지는 입력 구간"(시민시각 약 23:32~00:32)을 STATE 에 명시.
  기존 발송물 재검토 여부는 운영자 판단 사항으로 보고만.

### T2.2 [G-2] 절입 ±2분 관리자 확인 플래그 (절대규칙 7 후단 구현)
- solarterms 절입시각과 진태양시 차가 ±2분 이내면 GenResult 에 near_term_boundary 플래그 ->
  order_flow 에서 needs_review=True + 관리자 화면 표시. insight.py 의 미충전 필드도 이걸로 충전.
- 검증: 입춘 ±1분 합성 2케이스 발화 + 평시 케이스 미발화.

### T2.3 [G-1] KASI 3원 교차 런타임 편입 (절대규칙 7 전단 구현)
- kasi.crosscheck3_year 를 engine.build 또는 pipeline 에서 호출해 calc_consistent 판정에 편입.
  캐시 범위(절기 2000~2027) 밖 연도는 2원 + "kasi_out_of_range" 기록(차단 아님 — 규칙 7 의 분류 원칙,
  KNOWN_KASI_TERM_DEFECTS 기지결함 처리 로직 재사용).
- 검증: 캐시 조작 합성 케이스 CALC_MISMATCH 전이 + 기지결함 케이스 비차단 + 전 골든 GREEN.

### T2.4 [F-1] iztro-py 0.3.4->0.3.5 업그레이드 + [F-2] 연주 경계 교차
- 0.3.5 는 대한(大限/童限) 궁 배정 버그 수정본. 업그레이드 후 tests/test_ziwei_parity.py 전수 재검
  (스택 버전 변경 = 골든 전수 재검증 규칙). ziwei.py:121 try/except pass 를 warning 기록으로.
- myeongni 교차검증에 연간지(입춘 기준) 항목 추가(현재 월지만 — myeongni.py:183-187).
- 검증: parity 100건 구조 불일치 0 유지 + 연주 경계 골든(2000-02-04/05) 통과.

### T2.5 [G-3] 시진불명 시 자미 생성 금지 배선 (절대규칙 8)
- 먼저 실측: unknown_time 주문에서 자미 섹션이 실제 렌더되는지 E2E 확인(감사에서 ziwei 계층 무가드
  확정, builder 드롭 여부 미검증). 렌더된다면: unknown_time 시 ziwei 산출 억제 + builder 섹션 드롭
  + 명리 단독 강등 고지 유지. test_p8 시진불명 케이스에 자미 부재 단언 추가.

Phase 2 완료 기준: 골든 22건+신규 앵커 전수 GREEN, 전체 pytest GREEN, docs/03·STATE 갱신, 커밋.

---
## Phase 3 — 게이트 실효성 (완화 0 — 전 태스크에 정상/결함 양방 테스트)

### T3.1 [A-2+A-4] 저밀도 장꼬리 사각 축소 (두 건 동시 설계)
- A-4 먼저: verify.py:42·165 의 제\s*\d+\s*장 을 제\s*\d(?:\s*\d)*\s*장 으로(letter-spacing 추출 공백
  대응 — DOC_A 실측: 두 자리 장이 "제 1 0 장"으로 추출됨). DOC_A 로 1~17장 전부 매칭 True 실측.
- A-2: verify.py:190 장꼬리 면제에 글자수 하한 도입 — 꼬리가 그 하한 미만이면 저밀도 hit 유지.
  하한값은 DOC_A 실측 분포로 캘리브레이션(p16=50자는 잡히고, 정상 꼬리 150자+ 는 면제되는 값 —
  120(_LOW_DENSITY_MIN)과의 관계를 명시적으로 설계). _ORPHAN_MIN=40 과의 3중 사각(41~119자)이
  소멸함을 표로 증명하는 테스트 작성.
- 근본 보완(같은 Phase, 별 커밋): 50자급 스필은 게이트가 아니라 조판이 원인 — integrated/_LAYOUT_VARIANTS
  재시도에 "짧은 꼬리 발생 시 행간 미세조정 변형" 추가 검토(하한 13.8pt 불변, 열화 발급 금지 유지).
- 검증: 50자 꼬리 합성 케이스 FAIL + 정상 꼬리(150자+) PASS + DOC_A 재검증 결과 보고.

### T3.2 [B-2] 기하 게이트 보강 + 실렌더 회귀
- verify.py:233-280 — (1) 세로 넘침 검사 추가(블록 y 좌표 vs @page 상하 margin+eps), (2) 기대 좌단을
  20mm 고정이 아니라 "(페이지폭 - maxw)/2" 파생으로 계산(pdf.py 와 공유 상수로 단일소스화 —
  현재 .body max-width 148mm 인셋 미반영으로 좌 14mm 밀림까지 미탐), (3) fake doc skip 시
  layout_geometry_skipped=True 를 결과에 표기.
- 실렌더 결함주입 회귀 1건 이상: 좌쏠림 CSS 주입 렌더 -> FAIL, 정상 렌더 -> PASS
  (현재 기하 게이트를 실 PDF 로 검증하는 테스트 0건 — test_integrated_product 의 _FakeDoc 은 전부 no-op).
- 검증: DOC_A gate clean 유지(false fail 0) + 주입 케이스 차단.

### T3.3 [B-1+G-5] 최종 발급 게이트 완전화
- order_flow.py:318-322 final_render_fn 이 Report23/주문 데이터에서 names/name_full/identity/singang/
  role_perspective/honorific 을 복원해 verify 에 완전 전달(현재 5종 게이트 no-op).
- verify 에 safe_lint(§12)·factcheck(allow_tokens=Report23 영속본) 재실행 편입 — 최종 비우회 게이트에
  안전·사실 검증 부재 해소.
- admin approve: needs_review=True 주문은 확인 파라미터 없이는 409(1클릭 컨펌 폼).
- [E-3] DELIVERED 전이는 final PDF verify 통과 기록이 있을 때만 허용(store 레벨).
- 검증: 위반 주입 E2E 에서 발급 차단 + 기존 test_admin_ui 12건 GREEN(의도 강화로 인한 수정은 명시).

### T3.4 [D-1] tagged 게이트 항진 해소
- verify.py:362 OR -> StructTreeRoot AND(+ 트리 비어있지 않음). pdf.py:304 harden 이 MarkInfo 를 항상
  넣어 현재 게이트가 무의미.
- 검증: StructTree 제거 합성 PDF FAIL + 정상본 PASS + veraPDF 비악화.

### T3.5 [B-4+B-5] 목차 재넘침 방어 + 스코프 통일
- report.html.j2 목차: 행수 기반 동적 축소(장 >18 시 폰트/패딩 단계 축소) 또는 2단 목차 —
  장 22개 합성 케이스로 1페이지 유지 증명.
- verify 의 목차 판정 이중 기준(_customer_body_page_items <400자 vs _low_density "목차" 포함) 단일
  헬퍼로 통일. [B-8] 죽은 필드 contains_known_ganzhi 는 게이트 편입 또는 제거 결정.

Phase 3 완료 기준: 전 태스크 양방 테스트 + DOC_A 재검증 clean + 전체 pytest GREEN + STATE/장부 갱신.

---
## Phase 4 — 가드 커버리지/문안 (검수 동반)

### T4.1 [G-4] factcheck 연도 화이트리스트 + 주성 오탐
- 허용 연도 집합(ref_year·세운·대운 시작연도 파생) 밖 연도 언급 하드 차단. "자미" 주성 매칭에
  문맥 경계(자미두수/자미성 구분) 요구. 오탐/미탐 양방 케이스.
### T4.2 [G-7] safe_lint _OUTCOME 확장 (승진/창업/합격류) — C1 완화 원칙(부사 단독 허용)은 불변.
### T4.3 [G-6] masking 보강 — 출생지 입력값 문자열 결정론 치환 + 시각 표현("오전 7시"/"7시반") 패턴 확장.
### T4.4 [G-8] 윤달 15일 분할법 고지 자동 삽입 + 회귀(절대규칙 5. 먼저 현 경로에 고지가 정말 없는지 E2E 확인).
### T4.5 [E-1] /generate 구형 경로 — 운영자에게 제거 vs 주문 경로 통합 질문 후 처리. 최소한 파일명
  DOB 제거(saju_<ts>.pdf)와 X-Saju-Bazi 헤더 제거는 즉시.

Phase 4 완료 기준: 가드 변경 후 골든 문안 6케이스 clean 재확인(docs/06 계약) + 전체 pytest GREEN.

---
## Phase 5 — 운영/관측/유지보수 (저위험 일괄)

- T5.1 [E-4] conftest.py autouse fixture 로 ANTHROPIC_API_KEY 기본 삭제(실호출 테스트만 명시 opt-in 마커).
- T5.2 [E-5] hsummary 화이트리스트에 regen_stderr_tail 추가(마스킹 통과 후).
- T5.3 [B-6+B-7] content.json 스키마에 ref_date/premium/layout_variant/모델 메타 추가(하위호환 기본값).
- T5.4 [C-1] classify max_tokens 20->256 + instructor mode=Mode.TOOLS 명시 + 폴백 카운트 로깅.
- T5.5 [C-2] requirements 핀: fastapi>=0.136 / starlette==1.0.0 명문화. [C-4] SQLite WAL+synchronous=NORMAL.
- T5.6 [F-4] solarterms 폴백(1/1~1/6 하드코딩) 경보화 + de440s 범위(1849~2150) 가드.
- T5.7 [D-2] 7.1-3 귀속 판별 측정: 언더레이 적용 전 staging PDF veraPDF 비교(측정만, 아키텍처 변경 없음).
- T5.8 [G-10] 미커밋 3파일(brand fail-closed) 커밋 방침 운영자 확인 후 처리(내용은 양성 — 부록 참조).
- T5.9 테스트 공백 보충: 미성년/입춘 ±2분/자미단독 강등 케이스 + 통합 실렌더 E2E 정기 실행 방안.
- T5.10 [C-3] SDK 정리(무효 max_retries 인자 제거)·마이너 업그레이드는 선택 — 모델 변경(sonnet-5)은
  톤 A/B 없이 금지.

---
(부록 A~D 상세 근거는 운영자 감사 원문에 보존 — 각 태스크 착수 시 해당 ID 근거를 원문에서 재확인.
 핵심: 감사 기준선 438 passed / 3 skipped, DOC_A=customer2 통합본 55p 실측. HEAD=d0aa483.)

### 부록 C 요약 — 착수 시 먼저 실측으로 해소할 미검증 항목
- G-3 자미 시진불명: ziwei 무가드 확정, builder/rules 섹션 드롭 우회 여부 미소진 — E2E 실측 필요.
- G-8 윤달 고지: grep 중간확신, ziwei note 전문 미소진.
- D-2 veraPDF 7.1-3 원인 귀속(Chromium vs PyMuPDF 언더레이): 가설 — staging PDF 판별 측정 필요.
- B-3 잔여/name_policy hit 고객명 포함 여지: 정밀 추적 미완.
- B-1 범위: integrated_full 이 order_flow 최종발급을 타는지 미확정.
- G-5 실착취성: 구조 공백 확정, live 재현 미실시.
