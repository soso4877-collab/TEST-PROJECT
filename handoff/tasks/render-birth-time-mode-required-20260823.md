# TASK_PACKET — 렌더 경계에서 `birth_time_mode` 를 필수 인자로, report 스니핑(getattr) 제거 (render-birth-time-mode-required-20260823)

- **task_id**: `render-birth-time-mode-required-20260823`
- **owner**: **Codex 구현자** / **next_reviewer**: Claude Code 교차리뷰(read-only)
- **base_commit**: `a8840de` (tree clean)
- **근거**: `REVIEW-FEEDBACK.md` 2026-08-23 birth_time_mode 리뷰 소견 ① — `render/pdf.py:98` 같은 계열 getattr 잔존. 조용한 기본값 계열 3번째
  (N-1 `ym_time_dependent` → `birth_time_mode` 5곳 → 렌더 경계). 방법론 B-2·A-5.
- **rev**: 1

## 0. 역할·금지
Codex 상시 금지(PDF 재생성·LLM 호출·git commit·push·배포) 유지. **`render/**` 변경이므로 `gate_pass` 구성 비악화 + 양방 테스트**(AGENTS 계약 7,
`.claude/rules/render.md`). 검증용 실렌더(Playwright subprocess)는 샌드박스에서 skip 될 수 있다 — 환경차 규칙대로 분리 보고.
ignored 글롭 필수(`!**/render/out/**` `!**/tmp/**` `!**/synthetic-tmp/**` `!**/data/**`). 저장소 루트의 `_h153*.py` 류 **untracked 스크립트는 범위 밖**(`git ls-files` 로 추적 여부 확인 후 추적분만).

## 1. Goal (관측 가능한 결과 하나)
**`render_html`/`render_pdf` 는 호출자가 넘긴 `birth_time_mode` 만을 모드 권위로 쓴다.** report 객체에서 모드를 추론(getattr)하지 않고,
모드 미전달·`None` 은 소리 내어 실패한다. 산출 HTML/PDF 는 교정 전과 동일(비악화).

## 2. Background — 실측 (2026-08-23, read-only)

### 2-1. 결함 문장
```
render/pdf.py:98   report_mode = birth_time_mode or getattr(report, "birth_time_mode", None)
render/pdf.py:100  if report_mode is None and (three_pillar_provenance is not None or report_provenance): report_mode = THREE_PILLAR
render/pdf.py:104  birth_time_mode = normalize_mode(report_mode, unknown_time=unknown_time)     # None → known
```
### 2-2. 왜 "report 직접 접근"이 답이 아닌가
렌더 경계는 **의도적으로 duck-typed** 다. 제품 경로가 `SimpleNamespace` 리포트를 넘긴다:
| 호출자 | report 객체 | 모드 전달 |
|---|---|---|
| `pipeline.py:131` | `Report23` | `birth_time_mode=mode` ✔ |
| `order_flow.py:202` (follow-up) | `Report23` | `render_context.get("birth_time_mode")` ✔(항상 구성) |
| `order_flow.py:1594` (최종 발급) | `Report23` | ✔ |
| `order_flow.py:1524→integrated._render_integrated→:510` | `SimpleNamespace(sections=r23.sections)` | `_render_integrated` 가 정규화해 `:522` 전달 ✔ |
| `integrated.py:597/775` (저장 재렌더·빌드) | `SimpleNamespace(..., birth_time_mode=…)` | `:630`/`:777` ✔ (단 `:630` 은 구 파일이면 `None` 전달 가능 → `_render_integrated:496` 이 `report.birth_time_mode`("known" 폴백)로 복구) |
| **`gunghap.py:1116`** | `SimpleNamespace(sections=sections)` | **미전달** — 관계 리포트는 known 전용인데 모드를 안 넘기고 report 에도 없어 getattr→None→known 으로 통과 |
| `scripts/dump_reading.py:55` | `Report23` | 미전달(**`age=` 라는 존재하지 않는 kwarg 도 넘김** — 이미 깨진 스크립트, §3-4) |
따라서 권위는 **인자**여야 하고, report 스니핑과 None 폴백이 제거 대상이다.

### 2-3. 100-103행의 "provenance 가 있으면 three_pillar 로 복원" 추론
모드 미전달 사고를 막는 안전장치였다. 모드가 필수가 되면 도달 불가. `render/verify.py:589-594` 의 동형 추론(텍스트 고지 기반)은 **게이트**라
이 패킷 범위 밖이며 무수정.

## 3. 변경 설계
1. `render_html(report, saju, name=None, unknown_time=False, *, birth_time_mode: str, three_pillar_provenance=None, brand=None, …)`:
   - `birth_time_mode` 키워드 **필수**. `None` 이 들어오면 `ValueError("birth_time_mode is required at render boundary")` — `normalize_mode(None)`
     의 known 폴백에 태우지 않는다.
   - `report_mode = …getattr…`(98) 과 추론 블록(100-103) 제거. `birth_time_mode = normalize_mode(birth_time_mode, unknown_time=unknown_time)` 유지.
   - `report_provenance = getattr(report, "three_pillar_provenance", None)`(99) 와 provenance 선택(109-113)은 **데이터 폴백**이라 유지.
   - `assert_unknown_time_provenance_clean` 호출·도판 정책·이하 전부 무수정.
2. `render_pdf(...)`: 같은 키워드 필수 + 그대로 전달(이미 전달 중).
3. 호출자: `gunghap.py:1116` 에 `birth_time_mode="known"` 명시(관계 리포트 = known 전용, 주석 1줄). `integrated.py:510` 은 `_render_integrated` 가 이미
   정규화값을 넘기므로 무수정. `pipeline`·`order_flow` 무수정(이미 전달).
4. `scripts/dump_reading.py:55`: `age=` 제거 + `birth_time_mode=saju.birth_time_mode.value` 전달(깨진 스크립트 복구는 부수; 실행은 LLM 필요라 금지,
   `py_compile` 만).
5. 테스트 호출 18곳(8파일)에 `birth_time_mode="known"` 추가 — **단언 무수정**. fake `render_pdf` 2곳(`test_integrated_product:528`,
   `test_unknown_time_provenance_gate:666`)은 kwargs 통과형이라 무수정 예상.

### 하지 않을 것
`render/verify.py` 무수정 / `@page`·폰트·레이아웃·태그 무수정 / `calc/**`·`content/**`·`store/**` 무수정 / `normalize_mode` 레거시 규칙 무수정.

## 4. 파일 경계
**allowed_files**
```
sajugen/render/pdf.py(render_html·render_pdf 시그니처+98~103행) · sajugen/gunghap.py(1116행 호출만) · scripts/dump_reading.py(55행)
tests/test_render_birth_time_mode_required.py(신설)
tests/test_consistency.py · tests/test_cover_semantic_clean.py · tests/test_harness.py · tests/test_p4.py
tests/test_relationship_quality_contracts.py · tests/test_render_gate_e2e.py · tests/test_render_verify.py
tests/test_unknown_time_provenance_gate.py  (전부 호출 kwarg 추가만, 단언 무수정)
implementation-notes.md · sajugen/STATE.md
```
그 외 forbidden(특히 `render/verify.py`·`render/layout.py`·`content/**`·`calc/**`·`integrated.py`·`order_flow.py`·`pipeline.py`·manifest).

## 5. 수용 기준 — 양방
**(가) 비악화**
1. 전체 GREEN, 기존 단언 수정 0. `test_render_verify`·`test_render_gate_e2e`(환경 skip 가능)·`test_unknown_time_provenance_gate`·`test_p4` GREEN.
2. **HTML 동치**: known 정본 `Report23` 1건 + three_pillar 정본 1건에 대해 교정 전후 `render_html` 출력이 **바이트 동일**(신규 테스트에서
   교정 전 HTML 을 픽스처로 박지 말고, `git stash` 없이 증명하려면 교정 전 커밋의 함수를 `git show a8840de:sajugen/render/pdf.py` 로 임시 모듈 로드해 대조 —
   임시 파일은 scratch 에만, 커밋 금지). 대조가 환경상 불가하면 사유와 함께 **미검증**으로 분리.
3. `gate_pass` 키 구성 변화 0(`render/verify.py` 무수정이므로 자동).
**(나) 차단**
4. `render_html(report, saju)` 모드 kwarg 없음 → `TypeError`. **교정 전 RED**(현재는 known 으로 통과).
5. `render_html(report, saju, birth_time_mode=None)` → `ValueError`. 교정 전 RED.
6. 모드 없는 `SimpleNamespace(sections=…)` + provenance 만 전달 → 교정 전엔 three_pillar 로 **추론**됐음을 먼저 보이고(RED 근거), 교정 후엔
   모드 미전달로 `TypeError`(추론 경로 제거 실증).
7. three_pillar 모드 + provenance 정상 → `assert_unknown_time_provenance_clean` 이 여전히 호출됨(삼주 고지 누락 섹션 주입 시 차단) — 안전장치
   유지 실증.

## 6. 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m pytest tests/test_render_birth_time_mode_required.py tests/test_render_verify.py tests/test_unknown_time_provenance_gate.py tests/test_p4.py tests/test_consistency.py -q
./.venv/Scripts/python.exe -m ruff check <변경 파일>
./.venv/Scripts/python.exe -m py_compile scripts/dump_reading.py
```
- 기준선(2026-08-23) = **1299 passed / 14 skipped / exit 0**, 수집 1313. 구현환경 Playwright skip +28.

## 7. 정지 조건
기존 단언 수정 필요 / allowed 밖 수정 필요 / HTML 동치 실패(출력이 바뀜) / `gate_pass` 키 변화 → 정지 보고.

## 8. 산출물
`CODEX_IMPLEMENTATION_REPORT`(notes 최상단): 명령·출력, RED 3종(4·5·6), HTML 동치 결과, 호출자 표, 미검증 분리. 커밋 금지.
