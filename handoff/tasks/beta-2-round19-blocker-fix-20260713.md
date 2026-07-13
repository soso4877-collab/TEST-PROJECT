# TASK_PACKET — 라운드19 잔존 블로커 1건 수정 (삼주 wonguk 골격 meta lint 충돌)

- task_id: `beta-2-unknown-time-three-pillar-20260712` (동일 태스크의 수정 라운드 — 새 태스크 아님)
- fix_packet: `handoff/tasks/beta-2-round19-blocker-fix-20260713.md` (이 문서)
- 동결 문서(수정 금지): 원 패킷 `handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md`
  (SHA-256 `20ee5efb…04ba`), 라운드18 수정 패킷 `beta-2-round18-blockers-fix-20260713.md`,
  보류 패킷 `beta-1-hverify-module-contract-20260712.md`(SHA-256 `b981a996…5819`)
- base_commit: `084e04c95fc3d72757771b0a39d3dd7b85a2470e` + **미커밋 워킹트리(라운드19 리뷰 대상 그대로)**
- 구현자: Codex / 재검증: Claude 신선 컨텍스트 (라운드20)
- 판정 정본: `REVIEW-FEEDBACK.md` 라운드19 절 (2026-07-13, changes_requested)

## 상태(전제) — 라운드19 실측 (2026-07-13, Claude 기준환경)

- 라운드18 블로커 중 **B2(원국표 anchor)·B3(compose 중립화+SHA 핀+캡처)·B4(경계 테스트 3건) = 완결
  실측**. B1의 test_p8 갱신도 설계는 올바르다 — **이 범위는 재작업·리팩터 금지**.
- 잔존 = 단 1건: 복구된 E2E가 라운드18부터 잠복한 제품 결함을 적발했다.
  `sajugen/content/rules.py:999` wonguk 골격 "…서로 어떤 방향을 보태는지 **함께 읽습니다**"가
  `sajugen/content/customer_meta_lint.py:31` `guided_structure_walkthrough` 패턴(`함께\s*읽습니다`)에
  매치 → `customer_meta_clean=False` → `test_p8.py::test_e2e_unknown_time`에서 `gate_pass=False`.
- 기준환경 전체 pytest = **1 failed / 1031 passed / 4 skipped / exit 1** (실패는 위 1건뿐, +9, 감소 0).
  golden 28, 집중 124, Ruff 신규 0, py_compile 36, diff-check 0.
- 리뷰어 전수 프로브 실측: 삼주 골격 17개 키 × customer_meta 8룰 → **충돌 = wonguk 1건뿐**
  (`TOTAL_HIT_RULES=1`). 수정 범위는 문장 1곳으로 특정됐다.
- 근본원인 2층: 이 결함이 지금까지 안 잡힌 이유 = customer_meta 계열이 빌더 pre-render 벨트에 없고
  최종 PDF verify에서만 발화하는데, Codex 환경에서는 그 E2E가 playwright skip이라 관측 불가.
  → 문장 수정만으로는 같은 클래스가 재발한다. 비Playwright 단위 회귀가 필수 동반물이다.
- 스코프 밖 변경 2건(라운드18의 rules 문구 순화·order_flow enum 정본화)의 "운영자 추가 승인" 주장은
  플래그 상태로 유지 — 이번 라운드에서 건드리지 않고, checkpoint commit 시 운영자가 확인한다.
- manifest = `changes_requested / next_actor=codex` (validate exit 0).

## 0. 역할·금지 경계 (승인 범위)

- 이 패킷은 운영자가 승인한 잔존 블로커 1건 수정에 한정한 사안별 구현 승인이다. 그 밖의 제품 변경 금지.
- 수정 허용 파일: `sajugen/content/rules.py`(§1의 문장 1곳만), 회귀 테스트 파일 1개
  (`tests/test_unknown_time_provenance_gate.py`에 추가 권장 — 신규 파일 1개로 분리해도 무방)
  + 인계 3종(`implementation-notes.md`, `sajugen/STATE.md`, manifest는 handoff.mjs 경유).
  **`customer_meta_lint.py` 등 게이트/lint 코드 수정 금지**(완화·예외 추가 절대 금지 — 수정 대상은
  골격 문장이지 lint가 아니다). `REVIEW-FEEDBACK.md`는 리뷰어 소유 — 수정 금지.
- 상시 금지(변경 없음): Anthropic API 등 LLM 호출, 고객/실상품 PDF 재생성, hsweep, hrun,
  git commit, push, main 전진, APPROVED/발송, 고객 데이터·`harness/profiles/local/**`·`.env`·
  ignored 산출물 접근. 합성 입력만, PII 0.
  **예외: pytest 실행이 만드는 합성 테스트 PDF/HTML은 허용.**
- 검색 시 반드시 다음 글롭 적용:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만.

## 1. 수정 — rules.py:999 wonguk 골격 문장 재서술

- 대상: `sajugen/content/rules.py:999` (`_build_three_pillar_all`의 wonguk 텍스트) —
  "…세 자리는 따로 떼어 길흉을 단정하지 않고 서로 어떤 방향을 보태는지 함께 읽습니다."
- `함께 읽습니다`를 customer_meta 8룰 전부와 충돌하지 않는 표현으로 재서술한다(예: "함께 살핍니다",
  "겹쳐 살핍니다" 등 — 최종 표현은 구현자 재량이되 아래 인접 지뢰를 피할 것):
  - `보겠습니다`(writer_task_announcement — 전면 차단), `살펴보겠습니다`, `차례로 보겠습니다`,
    `차례대로/순서대로 확인`, `이야기…이어집니다`, 문두 `종합하면/결론적으로`.
  - 기존 게이트의 다른 텍스트 lint(외래어·날것 계산어·register hard·§12 안전표현·삼주 금지 패턴)와도
    비충돌이어야 한다 — 최종 판정은 아래 §2 회귀와 E2E가 한다.
- 의미 보존: "세 자리를 따로 떼어 길흉 단정하지 않는다"는 관법 서술은 유지한다. 문장 1곳 외의
  골격 텍스트 변경 금지(다른 섹션 문구를 손대면 승인 범위 밖).

## 2. 동반 회귀 — 삼주 골격 × 문서 메타 lint 비Playwright 매트릭스 (근본원인 2층)

1. **필수**: 실제 계산 결과(예: `engine.build(2000,1,15,None,None,birth_time_mode="three_pillar")`)로
   `rules.build_all(saju, ref_year=…, birth_time_mode="three_pillar")`를 만들어 **모든 키의 텍스트**에
   대해 `customer_meta_lint.lint(text) == []`를 단언하는 단위 테스트(Playwright 불필요 — Codex
   환경에서도 실행 가능). 도크스트링에 "무엇을 검증하고(골격×meta 패턴 충돌) 무엇을 검증하지
   않는지(LLM 후보·조판)"와 이번 실사고(라운드19 잔존 블로커)를 근거로 남긴다.
2. **인접 확장(같은 테스트에 포함)**: verify 전용이라 pre-render에서 골격에 적용되지 않는 텍스트
   lint 중 `client_tone_lint.loanword_lint`·`raw_calc_lint`도 같은 매트릭스로 0 단언한다(현재 E2E
   GREEN이므로 통과 예상). 만약 기존 골격에서 RED가 나면 lint를 건드리지 말고 즉시 정지·보고한다
   (게이트 완화 금지 — 스코프 확장은 운영자 결정).
3. **차단측 증명(양방)**: 수정 전 문장(`함께 읽습니다` 포함 합성 문자열)이 lint에 실제로 잡히는
   차단측 단언 1건을 같은 테스트에 둔다 — 회귀가 no-op이 아님을 증명한다.

## 3. 검증·완료 기준 (YOU MUST — 증거 없는 완료 주장 금지)

```
.\.venv\Scripts\python.exe -m pytest tests\ -q
.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
.\.venv\Scripts\python.exe -m pytest tests\test_p8.py tests\test_unknown_time_provenance_gate.py tests\test_three_pillar_calc.py -q
```
- Codex 환경 기준: 전체 exit 0 + 시작치(1004 passed / 32 skipped) 대비 기존 passed 감소 0 + 신규 증가.
  golden 28 유지. test_p8은 로컬 skip이면 그 사실을 notes에 명시(실행 증거는 Claude 라운드20
  기준환경에 위임 — skip을 통과로 보고하지 않는다).
- 변경 Python(diff+untracked 합집합) Ruff·py_compile GREEN(기존 부채 rules.py 17·verify.py 1 외
  신규 0 — rules.py 수정이 부채 구성을 바꾸면 그 사실을 수치로 보고), `git diff --check` exit 0.
- 문장 수정 후 §2-1 프로브 재실행 → `TOTAL_HIT_RULES=0` 수치를 notes에 남긴다.
- 완료 시: `implementation-notes.md`·`sajugen/STATE.md` 갱신 후 manifest를 handoff.mjs 전체 형식으로 —
  `node C:\Users\pc\.ai-harness\handoff.mjs write --replace --repo C:\Users\pc\test-project
  --task-id beta-2-unknown-time-three-pillar-20260712 --status review_requested
  --packet handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md --next-actor claude
  --next-action "라운드19 잔존 블로커 수정분 라운드20 재검증. API·PDF·commit·push 금지"`
  → `validate` exit 0. write는 notes/STATE 편집 완료 후에만 실행.

## 4. 후속 순서

1. Codex가 §1 문장 1곳 + §2 회귀만 구현하고 §3 증거와 함께 review_requested로 넘긴다.
2. Claude 라운드20 재검증(기준환경 전체 pytest — test_p8 E2E 실렌더 포함).
3. PASS 시 Codex 신선 read-only 확인 → 운영자 checkpoint commit 결정
   (이때 스코프 밖 변경 2건의 "운영자 추가 승인" 주장도 함께 확인).
4. advisory 3건·유료 replacement·hsweep·300dpi 육안은 별도 운영자 결정 전 착수 금지.
