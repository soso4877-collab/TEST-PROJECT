# TASK_PACKET — 라운드18 블로커 4건 수정 (생시 미상 삼주 전환 후속)

- task_id: `beta-2-unknown-time-three-pillar-20260712` (동일 태스크의 수정 라운드 — 새 태스크 아님)
- fix_packet: `handoff/tasks/beta-2-round18-blockers-fix-20260713.md` (이 문서)
- 원 패킷(동결): `handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md`
  SHA-256 `20ee5efb728456c8dd6c379da00a466d8885360802b73c5c8345400f307a04ba` — 수정 금지
- base_commit: `084e04c95fc3d72757771b0a39d3dd7b85a2470e` + **미커밋 워킹트리(라운드18 리뷰 대상 그대로)**
- 구현자: Codex / 재검증: Claude 신선 컨텍스트
- 판정 정본: `REVIEW-FEEDBACK.md` 라운드18 절 (2026-07-13, changes_requested)

## 상태(전제) — 라운드18 실측 (2026-07-13, Claude 기준환경)

- 기존 구현(수정 41 + 신규 8파일)은 **광범위하게 GREEN으로 실측 완료** — 계산 12/12 축약·digest
  순서불변·경계 0/11/13, 주문/레거시 fail-closed, 22키 게이트 양방, known 비악화, 문서-코드 정합,
  golden 28, 신규/집중 176 passed, Ruff 신규 위반 0, py_compile 35 exit 0, diff-check exit 0.
  **이 범위는 재작업·리팩터 금지**(승인 범위 밖 변경 0 원칙).
- 미해결 = 아래 블로커 4건뿐. 기준환경 전체 pytest는
  **1 failed / 1022 passed / 4 skipped / exit 1** (실패 = `tests/test_p8.py::test_e2e_unknown_time`).
  Codex 환경(995/32)에서는 이 테스트가 playwright skip 32건 안에 있어 관측되지 않았다.
- manifest = `changes_requested / next_actor=codex` (validate exit 0). 라운드18 advisory 3건
  (ziwei_fact 궁 목록 6개 부재, engine 표면 minute 조용 무시, 야자시 관찰)은 **이번 스코프 밖 — 수정 금지**.

## 0. 역할·금지 경계 (승인 범위)

- 이 패킷은 운영자가 승인한 블로커 1~4 수정에 한정한 사안별 구현 승인이다. 그 밖의 제품 변경 금지.
- 수정 허용 파일: `tests/test_p8.py`, `sajugen/render/pdf.py`, `sajugen/content/llm_sections.py`,
  `tests/test_three_pillar_calc.py`, `tests/test_unknown_time_order_contract.py`,
  `tests/test_unknown_time_provenance_gate.py`(또는 동급 신규 테스트 파일 1개),
  `sajugen/integrated.py`(B2에 필요한 최소 범위만) + 인계 3종(`implementation-notes.md`,
  `sajugen/STATE.md`, manifest는 handoff.mjs 경유). **REVIEW-FEEDBACK.md는 리뷰어 소유 — 수정 금지.**
- 동결 패킷 2개 수정 금지: 원 패킷(위 SHA) / `handoff/tasks/beta-1-hverify-module-contract-20260712.md`
  (SHA-256 `b981a99642ed47ca9c78c85733af5d114fd9e872acbb65efd905570754a05819`).
- 상시 금지(변경 없음): Anthropic API 등 LLM 호출, 고객/실상품 PDF 재생성, hsweep, hrun,
  git commit, push, main 전진, 배포, APPROVED/발송. 고객 데이터·`harness/profiles/local/**`·`.env`·
  ignored 산출물 접근 금지. 합성 입력만 사용, PII 0.
  **예외: pytest 실행이 만드는 합성 테스트 PDF/HTML은 허용**(B1의 E2E 렌더 포함).
- 검색 시 반드시 다음 글롭 적용:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만 (bare python/pytest 금지).
- 가드/게이트 완화 금지 — 모든 수정은 사각 축소 방향 + (정상 통과 + 결함 차단) 양방 테스트 동반.

## 1. 블로커 B1 — test_p8 구계약 테스트 갱신 (기준환경 exit 1의 직접 원인)

- 대상: `tests/test_p8.py:78-103` `test_e2e_unknown_time`.
- 결함: (a) 1995-07-07은 소서 절입일이라 새 `NEEDS_INFO_TIME_BOUNDARY`에 접수 차단되고,
  (b) `assert "추정" in text`는 구 고지 계약이라 날짜를 바꿔도 새 계약(`추정` 문구 금지)과 충돌한다.
- 수정:
  1. 날짜를 비절입일로 교체 — 권장 `2000-01-15`(기존 테스트에서 통과 실증된 날짜). 다른 날짜를 쓰면
     절입 비포함을 계산으로 확인하고 근거를 도크스트링에 남긴다.
  2. 레거시 호환 호출 형태(`12, 0` + `unknown_time=True`)는 유지해 legacy→three_pillar 정규화의
     E2E 실증을 겸하게 한다(정오 인자가 무시되고 삼주로 계산됨을 겸증).
  3. 단언을 새 계약으로 교체: 추출 텍스트에 (i) 정확 고지 문자열
     `출생시각이 확인되지 않아 연·월·일 세 기둥을 기준으로 풀이했습니다. 시간에 따라 달라지는 세부 해석은 제외했습니다.`
     포함, (ii) `추정`·`진태양시`·`사주팔자`·`時柱` 부재, (iii) 기존 자미 섹션 부재 단언 2건 유지.
  4. 도크스트링에 검증/비검증 범위 명시(구계약 단언을 왜 교체했는지 1줄 포함).
- Codex 환경에서 이 테스트가 playwright 미설치로 skip되면: 수정만 하고 "로컬 skip — 실행 증거는
  Claude 재검증(기준환경)에 위임"을 implementation-notes에 명시한다. skip을 통과로 보고하지 않는다.

## 2. 블로커 B2 — integrated_full 삼주 원국표 팬텀 배선 수정

- 결함: 표 삽입 조건이 `sajugen/render/pdf.py:128` `section.id == "wonguk"` 하나인데,
  integrated 조립 섹션 ID는 `sajugen/integrated.py:117,256`(`_copy_section(prefix="personal")`)로
  `personal_wonguk`이 된다 → 조건 영구 False. `_render_integrated`의 `fake_saju.three_pillar`(integrated.py:501),
  content.json의 `three_pillar_chart` 영속·`_three_pillar_from_chart_data` 복원이 전부 미소비.
- 수정:
  1. `render/pdf.py:128` 조건을 raw ID 기준으로 확장 — 권장:
     `section.id.removeprefix("personal_") == "wonguk"` (relationship_ 프리픽스는 대상 아님 — 삼주는
     상대 입력 자체가 접수 차단이므로 확장하지 않는다).
  2. known-time 경로 비악화: known에서는 어떤 섹션에도 chart_svg가 들어가지 않음(도판 전면 제거
     정책 유지)을 단언하는 테스트를 함께 둔다.
- 양방 테스트(신규):
  1. integrated 조립 형태(섹션 ID `personal_wonguk` 포함)의 삼주 report를 `render_html`(또는
     `_render_integrated` 경유 render 캡처)로 렌더 → `charts.three_pillar_table` 산출이 HTML에 존재 +
     정확 고지 1회 + `時柱` 0.
  2. `render_integrated_from_content` 복원 경로 — `three_pillar_chart` 라운드트립이 실제 chart 렌더로
     소비됨(무과금 재렌더에서도 표 유지).
  3. known integrated HTML에 chart_svg 0(비악화측).
- API·실 PDF 없이 render_html 문자열 검증 또는 render 함수 캡처(monkeypatch)로 구성한다.

## 3. 블로커 B3 — 삼주 compose 상충 시스템 지시 제거 + override 배선 캡처 테스트

- 결함: `sajugen/content/llm_sections.py` `_COMPOSE_SYSTEM`의 자미·궁 긍정 지시
  (46행 "사주·자미두수 상담가" 페르소나, 108행 "사실 토큰(간지·연도·신살·궁 이름)을 챕터당 충분히 호명",
  154-157행 "자미두수 궁 이야기를 ... 같은 호흡 안에서 겹쳐")가 삼주 compose에도 그대로 전달되고
  `_THREE_PILLAR_SYSTEM_OVERRIDE`(252행)가 뒤에서 금지한다 — 쓰라고 했다가 금지하는 상충 구조로
  재시도·룰 폴백을 유도할 수 있다. 또한 override 분기(`_compose_system_blocks`)를 단언하는 테스트가
  0건이라 분기가 사라져도 어떤 테스트도 RED가 되지 않는다.
- 수정:
  1. 삼주 모드의 시스템 표면에서 자미·궁 긍정 지시가 **아예 전달되지 않게** 재구성한다. 권장:
     `_COMPOSE_SYSTEM`을 공통부와 known 전용부(자미 페르소나·궁 호명·자미 겹쳐 읽기 라인)로 분해해
     모드별로 조립하거나, 삼주 전용 시스템 상수를 둔다. "뒤에서 금지" 패치 유지가 아니라 상충 원천 제거.
  2. **known 경로 비악화 하드 제약**: known compose의 시스템 블록 최종 문자열은 현재와
     **바이트 동일**해야 한다(분해-재조립 결과 대조). cache_control 블록 구성(마지막 context 블록에만
     ephemeral 5m)도 불변.
  3. override 블록은 유지하되(이중 방어), 삼주 시스템에 남는 지시와 모순되지 않게 문구를 정리한다.
- 양방 테스트(신규):
  1. `_compose_system_blocks(three_pillar context)` 캡처 → override 블록 존재 + 시스템 전체 문자열에
     "궁 이름"·"자미두수 상담가"·"궁 이야기" 류 긍정 지시 부재 + 마지막 블록만 cache_control.
  2. `_compose_system_blocks(known context)` 캡처 → 현재 `_COMPOSE_SYSTEM`과 바이트 동일 + override 부재.
  3. AnthropicBackend.compose 테스트 더블 캡처로 삼주 guide가 `_THREE_PILLAR_COMPOSE_GUIDE`에서
     오는지, user payload(base_text·근거)에 시주·자미·후보 원시 값이 없는지 단언(패킷 §6.8 완결).
- LLM 실호출 금지 — 전부 캡처/더블로 검증한다.

## 4. 블로커 B4 — 필수 경계 테스트 3건 추가 (테스트만, 제품 코드 무변경)

1. **비입춘 월 절입 경계**: `tests/test_three_pillar_calc.py`에 추가 —
   `1995-07-07`(소서) three_pillar 접수/계산 시 `NeedsInfoTimeBoundary`(code 검증 + 날짜 비노출),
   전날 `1995-07-06`·다음날 `1995-07-08` 통과. 기존 입춘 케이스(2000-02-04/05)는 그대로 둔다.
2. **three_pillar + 시각 동시 입력 접수 차단**: `order_flow.create_order(birth="2000-01-01 09:30",
   birth_time_mode="three_pillar", ...)` → `ValueError("must not include a birth time")` + 주문 0
   (DB `list_orders() == []`). 대칭으로 `birth_time_mode="known"` + 날짜-only → 차단(기존 매치 문자열)
   케이스가 이미 있으면 중복 금지, 없으면 함께 고정.
3. **레거시 known 주문 오분류 방지**: `render_meta.gen_params`에 `birth_time_mode` 키가 없고
   `hour/minute`(및/또는 `birth.birth_time`)이 존재하는 저장본 →
   `store.orders.report_birth_time_mode()`가 `KNOWN` 반환 + `final_birth_time_contract_error()`가
   `None`(최종 발급 통과). 반대편(레거시 `unknown_time=True`+정오 잔재 차단)은 기존 테스트가 있으므로
   중복 작성 금지 — 존재 확인만 도크스트링에 인용.
- calc/input 제품 코드는 이번에 변경하지 않는다(변경 시 골든 전수 조건이 다시 붙는다 — 스코프 밖).

## 5. 검증·완료 기준 (YOU MUST — 증거 없는 완료 주장 금지)

```
.\.venv\Scripts\python.exe -m pytest tests\ -q
.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
.\.venv\Scripts\python.exe -m pytest tests\test_p8.py tests\test_three_pillar_calc.py tests\test_unknown_time_order_contract.py tests\test_unknown_time_provenance_gate.py tests\test_llm_sections.py -q
```
- Codex 환경 기준: 전체 exit 0 + 시작치(995 passed / 32 skipped) 대비 **기존 passed 감소 0 + 신규 증가**.
  golden 28 유지. test_p8이 로컬 skip이면 그 사실을 명시(§1) — 기준환경 확정치는 Claude 재검증 몫.
- 변경 Python 전부(tracked diff + untracked 합집합) Ruff·py_compile GREEN, `git diff --check` exit 0.
  기존 부채(rules.py 17·verify.py 1) 외 신규 위반 0.
- 게이트 키 22종·기존 게이트 구성 비악화(제거·완화·기준 하향 0). B2·B3의 known 비악화 단언 필수.
- 완료 시: `implementation-notes.md`·`sajugen/STATE.md` 갱신(수정 파일 목록·실측 수치·미검증 명시) 후
  manifest를 handoff.mjs 전체 형식으로 기록 —
  `node C:\Users\pc\.ai-harness\handoff.mjs write --replace --repo C:\Users\pc\test-project
  --task-id beta-2-unknown-time-three-pillar-20260712 --status review_requested
  --packet handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md --next-actor claude
  --next-action "라운드18 블로커 수정분 재검증(diff 전량+기준환경 pytest). API·PDF·commit·push 금지"`
  → `validate` exit 0 확인. write는 notes/STATE 편집을 전부 마친 뒤에만 실행한다.

## 6. 후속 순서

1. Codex가 이 패킷의 블로커 1~4만 수정하고 §5 증거와 함께 review_requested로 넘긴다.
2. Claude 신선 컨텍스트가 라운드19 재검증(기준환경 전체 pytest 실측 포함)한다.
3. PASS 시 Codex 신선 read-only 검증 → 운영자 checkpoint commit 결정(원 패킷 §9 순서 유지).
4. advisory 3건·유료 replacement·hsweep·300dpi 육안은 별도 운영자 결정 전 착수 금지.
