# TASK_PACKET — `birth_time_mode` getattr 기본값 5곳을 명시 전달/직접 접근으로 (birth-time-mode-direct-access-20260823)

- **task_id**: `birth-time-mode-direct-access-20260823`
- **owner**: **Codex 구현자** / **next_reviewer**: Claude Code 교차리뷰(read-only)
- **base_commit**: `ca36e9f` (tree clean)
- **근거**: `REVIEW-FEEDBACK.md` 2026-08-22 N-1 리뷰 §2-1 — 패킷이 "fail-loud"라 했던 `builder.py:120` 이 실제로는 **fail-open**
  (`order_flow.py:188-190` follow-up 렌더가 `birth_time_mode` 없는 `SimpleNamespace` 를 넘김). 방법론 A-5(파라미터=소비처 배선까지 한 단위)·
  B-2(조용한 기본값 금지). N-1(`ym_time_dependent`)과 같은 계열의 두 번째 사례.
- **rev**: 2 (2026-08-23 — rev1 Codex `BLOCKED_CONTRACT`: `tests/test_three_pillar_orchestration.py:98`·`tests/test_unknown_time_order_contract.py:726`
  이 `personal_identity_spec` 을 **키워드를 못 받는 람다**(`lambda *_args: None` / `lambda _saju, _name: …`)로 monkeypatch 하고 있어 §3-1 키워드
  배선 시 `unexpected keyword argument` 가 확정적. 설계자 누락. rev2 = 이 두 파일을 allowed 에 추가(람다 시그니처를 `*args, **kwargs`
  수용형으로 바꾸는 **픽스처만**, 반환값·단언 무수정). 나머지 동일.)

## 0. 역할·금지
Codex 상시 금지(PDF 재생성·LLM 호출·git commit·push·배포) 유지. 검색 시 ignored 글롭 필수
(`--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`).
**주문/검수 경로(`order_flow.py`) 변경이므로 `tests/test_orders.py`·`tests/test_final_render_gate.py` 통과 필수**(AGENTS.md 계약 8).

## 1. Goal (관측 가능한 결과 하나)
**`birth_time_mode` 를 "있으면 쓰고 없으면 known" 으로 추론하는 경로가 제품 코드에 남지 않는다.** 모드는 호출자가 명시 전달하거나
정본 객체(`SajuResult.birth_time_mode` property / `ThreePillarSajuResult.birth_time_mode` / `Report23.birth_time_mode`)에서 **직접 접근**
하며, 모드 없는 객체는 소리 내어 실패한다.

## 2. Background — 실측 (2026-08-23, read-only)

### 2-1. 기본값 사이트 5곳
```
content/builder.py:120    if getattr(saju, "birth_time_mode", None) == "three_pillar"   (personal_identity_spec)
content/builder.py:208    birth_time_mode or getattr(saju, "birth_time_mode", None)      (build 본체)
integrated.py:497         birth_time_mode or getattr(report, "birth_time_mode", None)    (_render_integrated)
content/factcheck.py:68   getattr(saju, "birth_time_mode", None) == "three_pillar"      (allowed_tokens)
content/rules.py:1241     … or getattr(saju, "birth_time_mode", None) == "three_pillar"  (build_all 래퍼)
```
정본 객체는 **항상 모드를 갖는다**: `calc/engine.py:46` `SajuResult.birth_time_mode` property(KNOWN), `:62` `ThreePillarSajuResult` 필드,
`content/sections_schema.py:83` `Report23.birth_time_mode="known"`. 따라서 기본값은 정본 경로에선 사문이고 **합성 객체에서만** 발동한다.

### 2-2. 필드 없는 호출자
| 호출자 | 객체 | 성격 |
|---|---|---|
| `order_flow.py:188-190` `_render_followup_pdf` | `SimpleNamespace(myeongni=SimpleNamespace(day_master=…))` | **제품 경로**. 같은 함수가 `:199`·`:213` 에서 `render_context.get("birth_time_mode")` 를 이미 들고 있다 — 즉 모드를 알면서 `personal_identity_spec` 에만 안 넘긴다 |
| `tests/test_final_render_gate.py:87`, `tests/test_delivery_quality.py:726` | `engine.build` 를 `SimpleNamespace(myeongni=…)` 로 대체 | 테스트 합성. 호출자(`order_flow.py:1576`)가 모드를 명시 전달하면 픽스처 수정 불요 |
| `tests/test_integrated_modules.py:755`, `tests/test_integrated_order_flow.py:586` | `_render_integrated(SimpleNamespace(sections=[]), …)` 모드 kwarg 없음 | 테스트 합성. 직접 접근으로 바꾸면 **RED** → 픽스처에 `birth_time_mode="known"` 명시 추가 |
| `scripts/hverify_pdf.py:121` | 실제 `SajuResult` | 정본 객체. 명시 전달로 통일 |
| `tests/test_three_pillar_orchestration.py:98`, `tests/test_unknown_time_order_contract.py:726` (rev2) | `personal_identity_spec` 자체를 키워드 불수용 람다로 대체 | 테스트 합성. 람다를 `lambda *a, **k: …` 로 — 반환값 동일 |

### 2-3. 영향 평가
follow-up 은 저장된 `day_master` 만 쓰고 일간은 시각 불변이라 **현재 출력 영향 0**. 이 패킷은 계약 정리(조용한 기본값 제거)이지 결과
교정이 아니다 — 따라서 골든·문안 변동 0 이 수용 기준이다.

## 3. 변경 설계
1. `personal_identity_spec(saju, name, *, birth_time_mode)` — 키워드 **필수**. `unknown_time_policy.normalize_mode(birth_time_mode)` 로
   정규화 후 three_pillar 면 `saju.three_pillar`, 아니면 `saju.myeongni` 직접 접근(getattr 제거). 모드 미전달은 `TypeError`(파이썬 기본).
2. 호출자 5곳 명시 전달: `builder.py:363`(지역 `birth_time_mode`), `pipeline.py:119`(`mode`), `order_flow.py:1576`(`:1384` 의 `birth_time_mode.value`),
   `order_flow.py:188`(**`store/orders.report_birth_time_mode` 와 같은 정본 규칙** — `render_context["birth_time_mode"]` 를 읽되 키 부재는
   `store/orders.py:71-72` 가 문서화한 레거시 규칙으로만 해석. 규칙을 복제하지 말고 기존 헬퍼 재사용 또는 `render_context` 에 키를 넣는
   생산자 쪽 배선을 확인 — 어느 쪽이든 "없으면 known" 을 `_render_followup_pdf` 안에 새로 쓰지 않는다), `scripts/hverify_pdf.py:121`.
3. `builder.py:208` → `birth_time_mode or saju.birth_time_mode` / `integrated.py:497` → `birth_time_mode or report.birth_time_mode` /
   `factcheck.py:68` → `saju.birth_time_mode` / `rules.py:1241` → `saju.birth_time_mode` (전부 `normalize_mode` 경유, `== "three_pillar"` 문자열
   비교는 `unknown_time_policy.is_three_pillar_mode` 재사용).
4. 테스트 픽스처: `test_integrated_modules.py:755`·`test_integrated_order_flow.py:586` 의 `SimpleNamespace(sections=[])` 에 `birth_time_mode="known"`
   추가. `test_final_render_gate.py:87`·`test_delivery_quality.py:726` 은 호출자가 명시 전달하므로 **무수정이 목표** — 수정이 필요해지면 이유 보고.

### 하지 않을 것
- `calc/**`·`render/**`·`store/**` 무수정(`report_birth_time_mode` 는 **호출만**). `docs/**` 무수정.
- `normalize_mode` 의 "None → known" 레거시 규칙 자체는 건드리지 않는다(콘텐츠 API 역사적 기본, `unknown_time_policy.py:54-58` 주석).
  이 패킷이 없애는 것은 **객체 속성 부재를 None 으로 바꿔 그 규칙에 태우는 getattr** 이다.
- 시그니처에 타입 힌트로 `SajuResult` import 추가 금지(`content`→`calc` 순환 위험, N-1 패킷과 동일 사유).

## 4. 파일 경계
**allowed_files**
```
sajugen/content/builder.py · sajugen/content/factcheck.py · sajugen/content/rules.py(1241행 부근만)
sajugen/integrated.py(497행 부근만) · sajugen/pipeline.py(119행만) · sajugen/order_flow.py(188-190, 1576행만)
scripts/hverify_pdf.py(121행만)
tests/test_birth_time_mode_direct_access.py(신설) · tests/test_integrated_modules.py · tests/test_integrated_order_flow.py
tests/test_final_render_gate.py · tests/test_delivery_quality.py(픽스처만, 단언 무수정)
tests/test_three_pillar_orchestration.py(98행 람다만) · tests/test_unknown_time_order_contract.py(726행 람다만)   ← rev2 추가
implementation-notes.md · sajugen/STATE.md
```
그 외 전부 forbidden(특히 `sajugen/calc/**`·`render/**`·`store/**`·`docs/**`·manifest). 경계 밖 필요 시 `BLOCKED_CONTRACT`.

## 5. 수용 기준 — 양방 (작업 규율 3)
**(가) 정상 통과 — 거동 불변**
1. 전체 GREEN, 기존 단언 수정 0. `tests/test_orders.py`·`tests/test_final_render_gate.py`·`tests/test_unknown_time_order_contract.py`·
   `tests/test_three_pillar_orchestration.py` 개별 GREEN(주문 경로·삼주 계약).
2. known/three_pillar 정본 객체로 `personal_identity_spec`·`allowed_tokens`·`build_all` 출력이 교정 전과 **동일**(신규 테스트에서 교정 전
   값을 픽스처로 박지 말고, 두 모드의 실제 `engine.build` 결과로 속성 동치 단언).
**(나) 결함 차단**
3. `personal_identity_spec(fake, None)` 모드 kwarg 없이 → `TypeError`.
4. `personal_identity_spec(SimpleNamespace(myeongni=…), None, birth_time_mode="three_pillar")` → `AttributeError`(three_pillar 부재, fail-loud).
5. `_render_integrated(SimpleNamespace(sections=[]), …)` 모드 kwarg·속성 모두 없음 → `AttributeError`. **교정 전 RED 실증 의무**: 3·4·5 를
   교정 전 코드에서 먼저 돌려 "통과해 버림"(RED) 출력을 보고에 첨부.
6. `allowed_tokens(SimpleNamespace(myeongni=…))` 모드 속성 없음 → `AttributeError`(교정 전엔 known 으로 조용히 통과 — RED).

## 6. 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m pytest tests/test_orders.py tests/test_final_render_gate.py tests/test_unknown_time_order_contract.py tests/test_three_pillar_orchestration.py tests/test_birth_time_mode_direct_access.py -q
./.venv/Scripts/python.exe -m ruff check <변경 파일 전부>
```
- 기준선(2026-08-23) = **1293 passed / 14 skipped / exit 0**, 수집 1307(격자 10 skip 포함). 구현환경은 Playwright skip 28 추가.
- 통과 기준: exit 0, 기존 passed 감소 0, 신규만큼 증가.

## 7. 정지 조건
기존 단언을 고쳐야 통과 / allowed 밖 수정 필요 / `_render_followup_pdf` 에 "없으면 known" 을 새로 써야만 통과 / 골든·문안 출력 변동 → 정지 보고.

## 8. 산출물
`CODEX_IMPLEMENTATION_REPORT`(notes 최상단): 명령·출력, RED 3종, 호출자 배선표(5곳), 미검증 분리. 커밋 금지.
