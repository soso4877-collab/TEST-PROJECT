# TASK_PACKET — 라운드21 잔존 블로커 1건 수정 (test_p8 무공백 정규화 — 테스트 전용)

- task_id: `beta-2-unknown-time-three-pillar-20260712` (동일 태스크의 수정 라운드 — 새 태스크 아님)
- fix_packet: `handoff/tasks/beta-2-round21-blocker-fix-20260713.md` (이 문서)
- 동결 문서(수정 금지): 원 패킷(`20ee5efb…04ba`), 라운드18(`65b98207…54a0`)·라운드19(`0912acf9…b752`)·
  라운드20 v2(`04d5ee5f…d59d`) 수정 패킷, 보류 패킷(`b981a996…5819`)
- base_commit: `084e04c95fc3d72757771b0a39d3dd7b85a2470e` + **미커밋 워킹트리(라운드21 리뷰 대상 그대로)**
- 구현자: Codex / 재검증: Claude 신선 컨텍스트 (라운드22)
- 판정 정본: `REVIEW-FEEDBACK.md` 라운드21 절 (2026-07-13, changes_requested)

## 상태(전제) — 라운드21 실측 (2026-07-13, Claude 기준환경)

- 라운드20 블로커 3건(style·quality·delivery)은 **제품 수준 전부 해소 실측** — E2E 동일 입력 verify
  `gate_pass=True`, delivery failures 0, final_text 14섹션 lint 0, PDF 표지 고지 외 가운뎃점 0.
  **이 범위 재작업·리팩터 금지.**
- 잔존 = 단 1건, 테스트 전용: `tests/test_p8.py::test_e2e_unknown_time`이 게이트 통과 후 처음
  실행된 101-115행에서 실패(`assert 0 == 1`). 원인: 표지 고지가 음절 중간 줄바꿈("해석"|"은")으로
  개행 → PyMuPDF 추출 "해석\n은" → `" ".join(text.split())` 정규화가 단어 내부 개행을
  "해석 은"으로 만들어 고지 상수(바이트 동일·65자)와 불일치.
- 제품 정상 실측: **무공백 기준 고지 정확 1회 + 금지 토큰 9종 전부 0**(리뷰어 프로브).
  HTML 층 고지 1회 테스트 GREEN. 계약 위반 없음 — 카운트 방법만 조판 현실과 불일치.
- 기준환경 전체 pytest = **1 failed / 1035 passed / 4 skipped / exit 1**. golden 28,
  Ruff 부채 rules.py 17 + verify.py 1(신규 0), py_compile 38 exit 0, diff-check 0.
- manifest = `changes_requested / next_actor=codex` (validate exit 0).

## 0. 역할·금지 경계 (승인 범위)

- 이 패킷은 잔존 블로커 1건(테스트 1파일) 수정에 한정한 사안별 구현 승인이다.
- 수정 허용 파일: `tests/test_p8.py`(§1의 101-115행 판정 방식만) + 인계 3종
  (`implementation-notes.md`, `sajugen/STATE.md`, manifest는 handoff.mjs 경유).
- **제품 코드·게이트·lint·고지 문안·다른 테스트 수정 금지.** 특히 표지 조판(word-break 등)
  변경 금지 — 음절 중간 개행의 조판 품질 여부는 운영자 육안 검수 시 별도 판단(advisory).
- `REVIEW-FEEDBACK.md`는 리뷰어 소유 — 수정 금지.
- 상시 금지(변경 없음): LLM/API 호출, 고객/실상품 PDF 재생성, hsweep, hrun, git commit, push,
  main 전진, APPROVED/발송, 고객 데이터·`.env`·ignored 산출물 접근. 합성 입력만, PII 0.
  예외: pytest가 만드는 합성 테스트 PDF/HTML은 허용.
- 검색 글롭 필수: `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만.

## 1. 수정 — test_p8.py 101-115행 판정을 무공백 기준으로

- 추출 텍스트와 대조 상수 양쪽에서 공백을 전부 제거(`re.sub(r"\s+", "", …)`)한 뒤 판정한다:
  1. 고지 카운트(102행): 무공백 고지 상수의 `count == 1`.
  2. 양성 단언(103행): `年柱`·`月柱`·`日柱` — 2자 한자 토큰도 음절 중간 개행에 같은 방식으로
     취약(사각 인접)하므로 무공백 텍스트 기준으로.
  3. 금지 스캔(104-115행): 무공백 텍스트 기준(개행으로 쪼개진 금지 토큰이 숨지 못함 — 차단측
     강화). 단 `12:00`처럼 공백이 없는 토큰은 그대로, `두 체계를 함께 읽으며`처럼 공백 포함
     토큰은 상수도 무공백화해 대조한다.
- 주석/도크스트링에 명시할 것: (a) 왜 무공백인가(한국어 음절 중간 개행은 공백 보존 정규화로
  복원 불가 — 라운드21 실사고), (b) 금지 스캔의 무공백화는 어절 경계 결합으로 과탐(fail-closed)
  가능성이 있으며 RED 시 레이아웃 유발 오탐인지 실제 누출인지 조사 후 처리한다는 것.
- 판정 로직 외 테스트 구조(생성 인자·gate 단언·다른 E2E) 변경 금지.

## 2. 검증·완료 기준 (YOU MUST)

```
.\.venv\Scripts\python.exe -m pytest tests\ -q
.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
.\.venv\Scripts\python.exe -m pytest tests\test_p8.py -q
```
- Codex 환경 기준: 전체 exit 0 + 시작치(1008 passed / 32 skipped) 대비 기존 passed 감소 0.
  golden 28 유지. test_p8 E2E는 로컬 skip이면 skip으로 정직 보고(실렌더 판정은 Claude 라운드22).
- 변경 Python Ruff·py_compile GREEN(신규 위반 0), `git diff --check` exit 0.
- 완료 시: notes·STATE 갱신 후 manifest를 handoff.mjs 전체 형식으로 —
  `node C:\Users\pc\.ai-harness\handoff.mjs write --replace --repo C:\Users\pc\test-project
  --task-id beta-2-unknown-time-three-pillar-20260712 --status review_requested
  --packet handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md --next-actor claude
  --next-action "라운드21 잔존 1건(test_p8 무공백 정규화) 수정분 라운드22 재검증. API·PDF·commit·push 금지"`
  → `validate` exit 0. write는 notes/STATE 편집 완료 후에만. write가 GIT_COMMAND_FAILED면
  수동 편집 금지·"기준환경 위임" 보고 후 종료.

## 3. 후속 순서

1. Codex가 §1만 구현하고 §2 증거와 함께 review_requested로 넘긴다.
2. Claude 라운드22 재검증(전체 GREEN + E2E 실렌더 최종 확인 기대).
3. PASS 시 Codex 신선 read-only 확인 → 운영자 checkpoint commit
   (스코프 밖 2건 플래그 + 삼주 delivery 하한 12쪽/3,500자 + 표지 개행 조판 advisory 함께 확인).
