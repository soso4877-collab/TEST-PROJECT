# AGENTS.md — sajugen 협업 역할 분리 + 불변 제약

> 이 문서는 **컨텍스트 제공용**이다. 실제 강제는 코드(`scripts/hpreflight.py`·`scripts/hrun.py`의 검사와 exit code, `sajugen/render/verify.py` 게이트, pytest)와 git hook이 한다. 문서는 강제력이 없다.

## 프로젝트 한 줄
운영자 1인 내부 도구. 생년월일시·고민 → 진태양시 → 명리+자미 **결정론 계산** → 룰+부분 LLM 산문(챕터별 근거 슬롯) → 3단+가드 → tagged PDF → 관리자 검수 후 수동 발송. 상세: `CLAUDE.md`, `.claude/rules/00-immutable.md`, `sajugen/STATE.md`.

## 역할 분리
- **Cursor (사람+IDE)**: 탐색·편집·diff 검토. 변경 전 `.cursor/rules/*` 컨텍스트 확인.
- **Claude Code**: 승인 범위 안에서 구현·검증. 매 작업 단위로 plan→승인→구현→`hrun` 검증→보고. 커밋/푸시/PDF 재생성/LLM 호출은 명시 승인 시에만.
- **Codex (리뷰어)**: 기본 = 리뷰어. 권한·금지·동반 의무는 아래 `## Codex 운영 계약` 참조.

## Phase 0 containment — handoff source of truth
- 고객 납품·품질 사고 대응은 역할을 분리한다: Claude는 Plan Architect와 Semantic Reviewer, Codex는 승인된 TASK_PACKET 구현자, Codex Verifier는 별도 세션 검증자다. Claude가 직접 코딩·PDF 생성·테스트 수정을 하지 않는다.
- 구현의 source of truth는 `handoff/templates/task_packet.json` 형식의 TASK_PACKET이다. 구현 보고와 검증 보고는 분리하고, 세션 전환은 `handoff/templates/context_snapshot.md` 형식을 따른다.
- 납품 후보는 표준 게이트 파이프라인에서만 만든다. 손편집 HTML/PDF는 최종 납품 기준선으로 쓰지 않고, 실제 PDF는 render_verify·금칙 텍스트 스캔·300dpi 시각 점검·운영자 전문 검수 전 발송 금지다.
- 컨텍스트가 길어지면 대화 전문이 아니라 파일 경로, SHA, 결정사항, 실패 rule만 인계한다. 최신본 판단은 파일명이 아니라 SHA를 기준으로 한다.
- 고객 실데이터, PDF, PNG, summary는 gitignore 영역에만 둔다. 문서와 템플릿에는 고객 이름, 생년월일, 질문 원문, 본문 전문을 넣지 않고 `DOC_A`, `CUSTOMER_1` 같은 익명 ID만 쓴다.
- 세부 운영 순서는 `docs/17-agent-tooling-runbook.md`, 품질 사고 기록은 `docs/16-quality-incident-ledger.md`, PDF 수동 검수는 `handoff/templates/pdf_review_report.md`를 따른다.

## Codex 운영 계약 (권한 경계 — 강제는 코드·게이트·git hook, 이 절은 경계 정의)
1. 기본 역할 = 리뷰어. Codex는 diff와 `handoff/reports/<stamp>/summary.md`(+ `summary.json`)를 받아 게이트·회귀·안전(PII/secrets) 관점으로 읽고 판정만 한다.
2. 구현(파일 수정) 권한 없음 — 코드를 고치려면 운영자의 사안별 명시 승인이 매번 필요(포괄 승인 불가).
3. Codex 전용 상시 금지(Claude의 승인 범위 권한과는 별개이며, 구현 승인을 받은 뒤에도 금지): PDF 재생성, LLM(Anthropic API 포함) 호출, git commit, push, 배포(deploy).
4. 데이터 경계 — 두 가지를 분리한다:
   - (a) 접근(열람) 금지: `.env`·secret 값, 실고객 데이터, `harness/profiles/local/**` 파일을 직접 열지 않는다. 실데이터 관련 확인은 PII가 제거된 `summary.{json,md}`만 보고 판단한다.
   - (b) 인용 금지: 리뷰·리포트에 PII(실명·생년월일·출생시간)를 인용·전재하지 않는다.
5. (구현 승인 시) `calc/`·`input/` 변경 → 같은 작업 단위에 골든·회귀 테스트 동반(절대규칙 20, calc.md).
6. (구현 승인 시) `content/` 변경 → 3단 가드(safe_lint/factcheck/trace) 완화·우회 금지(절대규칙 12, content.md).
7. (구현 승인 시) `sajugen/render/**`(특히 `render/verify.py`) 변경 → 기존 `gate_pass` 구성 비악화(게이트 키 제거·완화·기준 하향 금지, render.md).
8. (구현 승인 시) 주문/검수 경로(`order_flow.py`·`store/orders.py`·`admin.py`·`app.py`) 변경 → APPROVED 전 발송 차단 회귀(`tests/test_orders.py`) 통과 필수(절대규칙 16).
9. 승인 근거 리포트: 최종 승인 근거는 "전체 tests 실행본 리포트"만 인정한다 = `scripts/hrun.py`를 `--no-tests` 없이(기본 실행) 돌려 만든 `summary.json`의 `pytest.returncode == 0`(passed 수 포함). `--no-tests`로 만든 리포트는 pytest 미실행이므로 최종 승인 근거로 사용 금지.
10. 리포트 산출물: `scripts/hrun.py`(no-regen)·`hsummary` 실행 시 `handoff/reports/<stamp>/summary.{json,md}`가 생성되며, 이 파일이 리뷰의 필수 첨부 근거물(게이트 근거)이다. diff·`git status`·`git log`·`final_report.md` 등 다른 증거와 함께 종합 판정한다(이 리포트가 유일 근거는 아니다).

## 불변 제약 (요약 — 원문 `.claude/rules/00-immutable.md`)
- 계산은 LLM 위임 금지. `sajugen/calc/`·`input/` 수정은 테스트+골든 회귀 동반.
- 가드(safe_lint/factcheck/trace + client_tone_lint name/identity/singang/loanword/raw_calc) 우회·완화 금지.
- APPROVED 전 발송 금지. 예측 정확도 주장 금지. 본문에 AI/도구 산출 고지 금지.
- 한국어(주석·커밋·문서). 산출 PDF·`.env`·`data/`·임시 `_*` 비커밋.

## 검증 진입점 (단일 명령)
```
./.venv/Scripts/python.exe scripts/hrun.py --profile harness/profiles/local/personal_h153.yml --profile harness/profiles/local/gunghap_h153.yml
```
- 기본: preflight(git/calc/secrets) + pytest + PDF 읽기 전용 검증 + `handoff/reports/<stamp>/` 리포트. **재생성·LLM·커밋 안 함.**
- PDF 재생성/LLM은 3중 잠금: `--regen --allow-llm` + env `SAJUGEN_HARNESS_ALLOW_REGEN=1` 전부 충족 시에만.
- 실데이터 프로파일은 `harness/profiles/local/`(gitignore)에만. 커밋되는 프로파일은 `*.example.yml`·`fixtures/*`(가짜값).
