# [Codex 지시문] Q7 3-A — 주문 플로우 integrated_full 편입(생성 소비·차단) (2026-07-11 운영자 승인)

> 형식: TASK_PACKET(산문판). 실행 기준 = 이 문서 + 승인 설계 `handoff/codex-q7-stage3-design.md`(A안 + 착수 점검 정정 2건).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review(라운드11). 커밋 = 리뷰 PASS 후 운영자.
> admin 추천·확정 UI는 3-B(별도 패킷)다. 3-A는 소비처(생성·차단)를 먼저 만들어 팬텀 메타를 구조적으로 막는다.

## 0. 역할·금지 (기존 + 신규 1건)
- Codex 상시 금지: git commit·push·deploy·sajugen 런타임 LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역
  (`render/out/`·`tmp/`·`synthetic-tmp/`·`data/`·`*.content.json`) 접근.
- **검색(rg/grep 등) 시 ignored 영역 제외 글롭 필수**(예: `--glob '!render/out/**' --glob '!tmp/**' --glob '!synthetic-tmp/**' --glob '!data/**'`) —
  라운드10 절차 이탈 재발 방지. 광역 검색 전 제외 패턴을 먼저 확인한다.
- `sajugen/calc/`·`sajugen/input/` 무변경(골든 불변). 가드 완화 금지. **상태머신 전이·APPROVED 발송 차단 무변경**(절대규칙 16).
- **수정 범위 한정(예상)**: `sajugen/integrated.py`(계산 입력 파라미터)·`sajugen/app.py`(접수 product)·
  `sajugen/order_flow.py`(분기·차단)·`sajugen/cli.py`(gen-followup 차단 배선 시)·관련 테스트. admin·템플릿·
  `modules.py`·게이트(`delivery_quality`·`verify`)는 비수정. 범위 초과 필요 시 정지·보고.
- 모순 발견 시 임의 해석 말고 정지·보고(선례: Q7 1단계 3회 정지 — 전부 타당했음).

## 1. 상태(전제) — 2026-07-11 실측
- 브랜치 `codex/gunghap-relationship-quality`, 시작 HEAD = `1401dbf`(Q7 1·2단계 종결, origin 동기).
- 기준선(기준환경): **758 passed / 4 skipped / exit 0**. 감소 = 회귀. 샌드박스 skip 상이 가능.
- **완료(재발주 금지)**: 1단계 레지스트리·조립·게이트·R9-1(`065c987`), 2단계 CLI `--module`(`ff002ee`).
  `build_integrated_full`은 1인+부분 조합(gunghap 제외)·content.json 모듈 메타 영속·복원을 이미 지원한다.
- **운영자 승인(2026-07-11, 재질의 불요)**: 설계 A안(1인 한정, gunghap·2인 접수는 4단계) / 접수 폼 product에
  integrated_full 노출 / 모듈 미확정 시 생성 차단(409 패턴) / RELATION→love 고정 추천(3-B 소관).
- 실측 앵커:
  - `integrated.py:593` — `engine.build(y,mo,da,hh,mi,is_male, horoscope_date=f"{ref_year}-06-01")`:
    longitude·latitude·policy 미전달(서울·JST_2300 기본), unknown_time 미지원. **이 갭이 3-A의 1번 작업**.
  - `app.py:53 /generate` — 1인 접수 폼, `product: str = Form("integrated")`.
  - `order_flow.py:192 run_order`(접수·gen_params 저장)·`:283` 근방(백그라운드 생성/재시도 — `pipeline.generate` 호출)·
    `:694` 근방(최종 발급 final_render 게이트)·`:141 question_category_state`(차단 상태 패턴 선례).
  - `followup/compose.py:149-156` — 저장본에 카테고리 근거 장 부재 시 조용히 skip(부분 조합 후속 위험 확정).
  - `delivery_quality.py:29` `_INTEGRATED_FULL_PRODUCTS = {"integrated_full"}` — 주문 product 문자열을 이와
    정확히 일치시키면 기존 모듈 게이트·N 하한이 자동 적용된다(게이트 신설 불필요).

## 2. 구현
1. **계산 입력 배선** (`integrated.py`): `build_integrated_full`에 `longitude`·`latitude`·`policy`(자시 정책)·
   명시적 horoscope 기준 파라미터를 추가하고 `engine.build`에 전달한다. **모든 신규 파라미터의 기본값은
   현행 동작과 동일**(서울 좌표·JST_2300·`f"{ref_year}-06-01"`) — 기존 CLI·테스트 출력 바이트 불변을 회귀로
   고정한다. unknown_time 파라미터는 만들지 않는다(소비처 없는 파라미터 금지 — 접수 차단으로 대신함).
2. **접수 확장** (`app.py`·`order_flow.run_order`): product 선택지에 `integrated_full` 추가(문자열은
   `_INTEGRATED_FULL_PRODUCTS`와 정확히 일치). integrated_full 접수에서 **시진 불명(birth에 시각 없음) →
   ValueError로 주문 미생성**(fail-closed — 자미 강등 미지원 상태에서 조용한 진행 금지). modules는 접수 시
   받지 않는다(빈 상태로 저장, 3-B가 확정 UI 담당).
3. **모듈 미확정 차단** (`order_flow.py`): `module_selection_state(report)` 상당의 결정론 판정 —
   integrated_full 주문이 `gen_params.modules` 미확정(부재/빈 목록)이면 백그라운드 생성·재시도를 차단한다
   (주문 상태 불변, 원인 메시지에 PII 없음). 기존 Q6 GENERAL 미확정 승인 409 패턴을 참조하되 이번 차단
   지점은 승인 아닌 **생성**이다.
4. **생성·재시도 분기** (`order_flow.py`): product==integrated_full이면 `pipeline.generate` 대신
   `build_integrated_full`을 호출한다 — gen_params를 전부 소비: 1인 people 튜플(name·생년월일시·성별),
   `modules`(확정값), longitude·latitude·yajasi→policy, horoscope, use_llm, brand, concern→situation,
   ref_date=생성 당일(T5.3 규약). content.json 영속이 함께 일어나는지 확인하고 없으면 배선한다(무과금 재렌더 유지).
5. **최종 발급 분기** (`order_flow.py:694` 근방): integrated_full 주문의 final_render가 동일 spec·게이트
   (identity·singang·role·모듈 커버리지)를 재사용하는지 확인·배선한다. 발급 시점 게이트 no-op 금지(B-1 선례).
6. **후속 차단**: parent 주문 product==integrated_full이면 `gen-followup`(텍스트·`--pdf` 모두)을 fail-closed
   거부한다(원인: 부분 조합 저장본의 근거 장 부재 시 조용한 skip — 지원은 별도 단계). 기존 개인 상품 후속
   경로는 무변경.

## 3. 수용 기준 (양방)
- (CLI 하위호환) 신규 계산 입력 파라미터 기본값에서 기존 CLI gen·기존 테스트 출력 불변(기존 30건 GREEN 유지)
  + longitude 등 명시 전달 시 `engine.build` kwargs 도달(캡처 단언).
- (접수) integrated_full 정상 접수 → 주문 생성·modules 빈 상태·Q6 자동분류 저장. **시진 불명 + integrated_full →
  주문 미생성**(기존 integrated 상품의 시진 불명 접수는 무변경 회귀).
- (차단) modules 미확정 integrated_full 주문의 생성·재시도 → 차단(상태 불변). 확정값 합성 주입 후 →
  `build_integrated_full`에 modules·longitude·situation 도달(모의 캡처).
- (분기 전수) 생성·재시도·최종 발급 3지점 모두 integrated_full 분기 테스트 + 기존 integrated(Report23) 주문
  경로 무변경 회귀(팬텀 파트너 QI-2026-07-04-01 재발 방지).
- (후속) integrated_full 부모 → gen-followup 거부. 기존 부모 → 기존 동작 회귀.
- (게이트 자동 적용) 생성 결과 verify에 product="integrated_full"·selected_modules 전달 →
  `module_coverage.skipped == False` 관측 단언.
- 상태머신: `tests/test_orders.py`·`tests/test_final_render_gate.py` GREEN(절대규칙 16 회귀).
- 전체 pytest exit 0, **기준선 758/4 대비 감소 0** + 신규 증가분 명시. calc/input diff 0. 수정 파일 Ruff GREEN
  (기존 부채와 신규 위반 구분 보고).
- 테스트 픽스처 PII 0(익명 ID·합성 생일만).

## 4. 완료 보고 (여기서 멈춤)
실행 명령+출력(passed 수/exit code), diff 요약(파일별), 3지점 분기·차단·하위호환 증거, 미검증(실렌더 등) 명시.
**커밋 없이 워킹트리 유지** → 교차리뷰 라운드11.

## 범위 밖
admin 추천·확정 UI(3-B), gunghap 모듈·2인 접수(4단계), 시진 불명 명리 단독 강등, integrated_full 후속 지원,
실렌더, LLM-on 문안, push.
