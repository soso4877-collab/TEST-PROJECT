# [Codex 지시문] Q7 3-B — admin 모듈 추천·확정 UI (2026-07-11 운영자 승인)

> 형식: TASK_PACKET(산문판). 실행 기준 = 이 문서 + 승인 설계 `handoff/codex-q7-stage3-design.md`(A안).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review(라운드12). 커밋 = 리뷰 PASS 후 운영자.
> 3-A(라운드11 PASS·`ac5d8f2`)가 소비처(생성 분기·미확정 차단)를 이미 만들었다. 3-B는 그 `gen_params.modules`에
> 값을 넣는 운영자 입력 UI다 — 확정 즉시 생성이 아니라 저장만 하고, 생성은 기존 재시도 버튼을 재사용한다.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·sajugen 런타임 LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역 접근.
- **검색(rg/grep 등) 시 ignored 제외 글롭 필수 — 반드시 `!**/` 프리픽스 형식**:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
  (루트 기준 `!render/out/**` 형식은 하위 경로 검색에서 미적용 — QI-2026-07-11-01 2회 재발 원인).
- `sajugen/calc/`·`sajugen/input/` 무변경. 가드 완화 금지. 상태머신 전이·APPROVED 발송 차단 무변경(절대규칙 16).
- **수정 범위 한정(예상)**: `sajugen/admin.py`·`sajugen/web_templates/admin_detail.html.j2`·
  `sajugen/order_flow.py`(확정 함수)·`sajugen/modules.py`(추천 매핑 함수 추가만 — **1단계 R9-1 커버리지
  로직 비변경**)·관련 테스트. app.py·cli.py·게이트(`delivery_quality`·`verify`)·`integrated.py` 비수정.
  범위 초과 필요 시 정지·보고.
- 모순 발견 시 임의 해석 말고 정지·보고.

## 1. 상태(전제) — 2026-07-11 실측
- 브랜치 `codex/gunghap-relationship-quality`, 시작 HEAD = `3b2aa7b`(3-A 종결, origin 동기).
- 기준선(기준환경): **778 passed / 4 skipped / exit 0**. 감소 = 회귀. 샌드박스 skip 상이 가능.
- **완료(재발주 금지)**: 3-A 전체 — integrated_full 접수(시진 불명 차단)·`module_selection_state`·미확정
  생성/재시도 차단·확정 시 native 생성 분기·최종 발급 재검증·후속 차단. **미확정 주문은 NORMALIZED에서
  대기하며 감사에 `generation_blocked`가 남는다**(실경로 프로브 검증됨).
- **운영자 승인(재질의 불요)**: 추천은 표시만(자동 선택 없음) / RELATION→love 고정(1인 주문) /
  TIMING·GENERAL→추천 없음(운영자 선택 필수) / gunghap은 1인 주문 UI에서 비노출 / 확정 목록은
  `gen_params.modules`+`report_plan.sections` 저장, audit에는 모듈 ID만.
- 실측 앵커:
  - `order_flow.py:181` 근방 `module_selection_state` — 3-A가 만든 판정 함수(product·modules·confirmed·
    needs_confirmation). 3-B UI가 이 상태를 표시·갱신한다.
  - `admin.py:142-165` 상세 컨텍스트(`gen_params`·`question_category` 노출), `:283`
    `confirm_question_category` POST — Q6 확정 패턴(폼·검증·audit)의 선례.
  - `order_flow.py:573` `confirm_question_category` — 저장·audit 갱신 선례.
  - `admin_detail.html.j2:73-90` Q6 분류 패널(red 강조·드롭다운·확정 폼) — 모듈 패널의 형식 선례.
    `:54` 재시도 폼 — 확정 후 생성 트리거로 재사용(신설 금지).
  - `question_router.py:13` QuestionCategory 7종(LOVE·JOB·WEALTH·HEALTH·RELATION·TIMING·GENERAL).
  - `models/report.py:67` `ReportPlan.sections: list[str]` — 확정 목록 동기화 대상 필드(실존).

## 2. 구현
1. **추천 매핑 함수** (`modules.py`에 추가 — 레지스트리 단일 소스): 결정론
   `recommended_modules_for_category(category: str) -> tuple[str, ...]` —
   LOVE→("love",) / JOB→("job",) / WEALTH→("wealth",) / HEALTH→("health",) / RELATION→("love",) /
   TIMING·GENERAL·미지정·미등록→(). 반환은 추천일 뿐 어디서도 자동 저장하지 않는다.
2. **admin 상세 모듈 패널** (`admin.py`+템플릿): integrated_full 주문에만 표시 —
   `module_selection_state` 상태(미확정 red 강조)·Q6 현재 카테고리 기반 추천 배지·4모듈
   (love/job/wealth/health) 체크박스·확정 POST 폼. gunghap 체크박스 비노출. 기존 상품 주문 상세는 무변경.
3. **확정 POST** (`admin.py` 라우트 + `order_flow.confirm_module_selection`):
   - 검증은 레지스트리 위임 — `normalize_modules` 재사용(빈 목록·미등록·중복 = 실패). **gunghap 수신 =
     422 거부**(1인 주문 — UI 비노출과 이중 방어). 자체 보정 금지.
   - 허용 상태 = **생성 전(NORMALIZED)만**. 그 외 상태(생성 후 IN_REVIEW 등) 확정 POST = 409 거부·저장
     불변(생성물과 메타 불일치 방지 — 변경이 필요하면 주문 삭제 후 재접수, 이번 범위 밖).
   - 저장: `gen_params.modules` = 정규화 목록 + `report_plan.sections` 동기화. audit note = 모듈 ID만
     (이름·생년월일·질문 원문 비복제 — 절대규칙 17).
4. **생성 트리거 재사용**: 확정 후 생성은 기존 재시도 버튼(`/admin/orders/{id}/retry`)이 그대로 3-A
   native 분기를 탄다. 새 생성 버튼·자동 생성 금지.

## 3. 수용 기준 (양방)
- (추천 매핑) 7종 카테고리 전수 표 테스트 — RELATION→love, TIMING/GENERAL→빈 튜플. 함수는 저장 부작용 0.
- (표시) integrated_full 주문 상세에 패널·추천 배지·미확정 강조 노출. 기존 상품(integrated 등) 상세 무변경 회귀.
- (확정 저장) 정상 확정 → `gen_params.modules`+`report_plan.sections` 저장·audit 모듈 ID만 기록,
  이후 `module_selection_state.confirmed == True`·재시도가 native 생성 분기 진입(3-A 모의 패턴 재사용).
- (차단) 빈 목록·미등록·중복·gunghap 확정 → 422·저장 불변. NORMALIZED 아닌 상태 확정 → 409·저장 불변.
  추천이 존재해도 미확정이면 생성 차단 유지(자동 선택 없음 증명).
- (안전) audit·화면에 질문 원문·생년월일 전재 없음(TestClient 응답 검사). 상태머신 회귀
  (`tests/test_orders.py`·`tests/test_final_render_gate.py`) GREEN.
- 전체 pytest exit 0, **기준선 778/4 대비 감소 0** + 신규 증가분 명시. calc/input diff 0. 수정 파일 Ruff
  GREEN(기존 부채와 구분). 테스트 픽스처 PII 0.

## 4. 완료 보고 (여기서 멈춤)
실행 명령+출력(passed 수/exit code), diff 요약(파일별), 추천 표·확정/차단 양방 증거, 미검증(실브라우저 등)
명시. **커밋 없이 워킹트리 유지** → 교차리뷰 라운드12.

## 범위 밖
gunghap·2인 접수(4단계), integrated_full 후속 지원, 확정 변경/재생성 UX, 실렌더, 실브라우저 수동 검수,
LLM-on 문안, push.
