# TASK_PACKET — 표지 고지 음절 중간 개행 수정 (.cover .sub word-break keep-all, advisory 후속 소작업)

- task_id: `cover-sub-keepall-20260713` (신규 태스크 — beta-2는 `763ed73`으로 종결됨)
- packet: `handoff/tasks/cover-sub-keepall-20260713.md` (이 문서)
- base_commit: `763ed735b59ff5dc97ff8632158ba3dca03a3edb` (= main, 클린 워킹트리에서 시작)
- 구현자: Codex / 재검증: Claude 신선 컨텍스트
- 발주 근거: REVIEW-FEEDBACK 라운드21 advisory + 라운드22 운영자 checkpoint 확인 ③ — 운영자 발주 2026-07-13

## 상태(전제) — 발주 시점 실측 (2026-07-13, Claude 기준환경)

- beta-2 종결 완료: checkpoint 3커밋(`2cad29c` feat / `02b3c48` docs / `763ed73` handoff done) 커밋·push,
  main = `763ed73` fast-forward 완료. manifest = done(archive `handoff/archive/beta-2-…json` 보존).
- 기준환경 전체 pytest = **1036 passed / 4 skipped / exit 0**. golden 28. test_p8 실렌더 3/3 PASSED.
  Ruff 부채 = rules.py 17 + verify.py 1 (신규 0). **이 기준선 비악화가 완료 조건.**
- 결함 실측(라운드21 리뷰): 표지 고지가 음절 중간 개행("…세부 해석"|"은 제외했습니다") —
  PyMuPDF 추출 "해석\n은". 라운드21은 테스트를 무공백 정규화로 우회(fail-closed)했고 조판 자체는
  advisory로 이월. 고객 계약 위반은 아니며 조판 품질 사안.
- 원인 실측(이 발주 시점): 고지는 `{{ cover_sub }}` → `.cover .sub`(report.html.j2:120, CSS 59-60)로
  렌더되는데, **`.cover .sub`에만 `word-break:keep-all`이 없다** — `.toc-name`(76-77)·
  `h2.ctitle`(90-92)·`.body`(101-102)는 이미 `keep-all` 적용. 한국어 기본 개행 규칙(UAX #14)은
  음절 사이 임의 개행을 허용하므로 keep-all 부재 셀렉터가 표지에 남은 마지막 사각.
- 영향 범위: `cover_sub`는 전 상품 공용(생년월일 줄 + 고지들, `white-space:pre-line`) —
  이 수정은 삼주뿐 아니라 **전 상품 표지**에 적용된다. 비악화 근거는 §3의 E2E 3건 + gate 단언.

## 0. 역할·금지 경계 (승인 범위)

- 이 패킷은 표지 조판 1건(CSS 1셀렉터 + 회귀 1단언) 수정에 한정한 사안별 구현 승인이다.
- 수정 허용 파일: `sajugen/render/templates/report.html.j2`(§1의 `.cover .sub` 선언만) +
  `tests/test_p8.py`(§2의 단언 추가만) + 인계 3종(`implementation-notes.md`, `sajugen/STATE.md`,
  manifest는 handoff.mjs 경유).
- **금지: `verify.py`·게이트·lint·고지 문안(불변규칙 8 고정 문구)·`@page`/여백·다른 셀렉터·
  다른 테스트 수정.** 렌더 레이어 규칙(render.md) 적용 — gate_pass 구성 비악화.
- `REVIEW-FEEDBACK.md`는 리뷰어 소유 — 수정 금지.
- 상시 금지(변경 없음): LLM/API 호출, 고객/실상품 PDF 재생성, hsweep, hrun, git commit, push,
  main 전진, APPROVED/발송, 고객 데이터·`.env`·ignored 산출물 접근. 합성 입력만, PII 0.
  예외: pytest가 만드는 합성 테스트 PDF/HTML은 허용.
- 검색 글롭 필수: `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만.

## 1. 수정 — `.cover .sub`에 keep-all 3종 부여

- `report.html.j2:59-60`의 `.cover .sub` 선언에 `word-break:keep-all;overflow-wrap:normal;
  line-break:strict`를 추가한다(`.toc-name`·`h2.ctitle`과 동일 3종 패턴으로 정합).
- 기존 속성(`white-space:pre-line`·`line-height:1.95` 등) 유지. 셀렉터 신설·구조 변경 불필요.
- 다른 변경 금지.

## 2. 회귀 — 표지 개행이 어절 경계에서만 일어남을 E2E로 고정

- `tests/test_p8.py::test_e2e_unknown_time`에 단언 1개 추가: **공백 보존 정규화**
  (`" ".join(text.split())`) 기준으로도 고지 상수(공백 포함 원문)가 정확 1회 존재.
  - 근거: keep-all 적용 후 모든 개행은 공백 위치에서만 일어나므로 공백 보존 정규화로 원문이
    복원된다. 음절 중간 개행이 재발하면 가짜 공백이 끼어 불일치 → 이 단언이 라운드21 실사고의
    정확한 역방향이라 (수정 전 RED / 수정 후 GREEN) 양방 증거가 자연 성립한다.
  - 기존 무공백(`re.sub(r"\s+", "", …)`) 단언·금지 토큰 스캔은 **그대로 유지**(금지 토큰 은닉
    방지 층 — 대체 아님, 층 추가). 고지 상수는 기존 test_p8이 쓰는 정본 소스 그대로 사용.
- 도크스트링에 명시: (a) 검증 = 표지 고지 개행이 어절 경계에서만 일어남(keep-all 배선),
  (b) 비검증 = 표지 외 페이지 조판·시각 품질(운영자 육안 몫).
- Codex 환경에서 E2E가 skip이면 skip으로 정직 보고(실렌더 판정은 Claude 재검증 라운드 몫).

## 3. 검증·완료 기준 (YOU MUST)

```
.\.venv\Scripts\python.exe -m pytest tests\ -q
.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
.\.venv\Scripts\python.exe -m pytest tests\test_p8.py -q
```
- 전체 exit 0 + 시작 실측치 대비 기존 passed 감소 0(Codex 환경 skip 수는 환경 의존 — 시작치를
  notes에 기록하고 그 기준으로 보고). golden 28 유지. 기준환경 기대 = 1036+α passed / 4 skipped.
- E2E 3건(gate_pass 단언 포함)이 전 상품 표지 변경의 비악화 근거다 — layout_geometry 포함
  게이트 키가 하나라도 악화되면 즉시 중지·보고(우회 금지).
- 변경 Python Ruff·py_compile GREEN(신규 위반 0), `git diff --check` exit 0.
- 완료 시: notes·STATE 갱신 후 manifest를 handoff.mjs 전체 형식으로 —
  `node C:\Users\pc\.ai-harness\handoff.mjs write --replace --repo C:\Users\pc\test-project
  --task-id cover-sub-keepall-20260713 --status review_requested
  --packet handoff/tasks/cover-sub-keepall-20260713.md --next-actor claude
  --next-action "표지 keep-all 수정분 신선 재검증(실렌더 포함). API·PDF·commit·push 금지"`
  → `validate` exit 0. write는 notes/STATE 편집 완료 후에만. write가 GIT_COMMAND_FAILED면
  수동 편집 금지·"기준환경 위임" 보고 후 종료. (--replace는 task_id 전환에 필수 — 구 beta-2
  manifest는 archive에 보존돼 있어 유실 없음.)

## 4. 후속 순서

1. Codex가 §1+§2만 구현하고 §3 증거와 함께 review_requested로 넘긴다.
2. Claude 신선 재검증 — 전체 GREEN + 실렌더에서 표지 추출 실측(공백 보존 정규화 일치 확인).
3. PASS 시 운영자 checkpoint commit. 커밋 전 권장: 표지 1쪽 육안 확인(줄바꿈 위치의 시각 품질 —
   keep-all은 어절 경계 개행만 보장하며 좌우 균형은 별개 사안).
