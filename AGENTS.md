# AGENTS.md — sajugen 공유 진실원 (모든 에이전트 공통: Codex·Claude·Cursor)

> 이 문서는 **컨텍스트 제공용**이다. 실제 강제는 코드(`scripts/hpreflight.py`·`scripts/hrun.py`의 검사와 exit code, `sajugen/render/verify.py` 게이트, pytest)와 git hook이 한다. 문서는 강제력이 없다 — 그래서 아래 "Programmatic checks"를 반드시 실행해 증거로 말한다.
> Claude Code 는 `CLAUDE.md` 첫 줄의 `@AGENTS.md` import 로 이 문서를 함께 로드한다. 여기 있는 내용은 CLAUDE.md 에 중복 기재하지 않는다(단일 소스).

## 프로젝트 성격 (절대 망각 금지 — 모든 신규 작업은 착수 전 이 6개조와의 정합부터 확인)
운영자 1인 내부 도구. 생년월일시·고민 -> 진태양시 -> 명리+자미 **결정론 계산** -> 룰+부분 LLM 산문(챕터별 근거 슬롯) -> 다단 가드 -> tagged PDF -> 관리자 검수 후 수동 발송.
1. **정확도 = 상품의 생명.** 계산은 결정론 엔진 전용(같은 입력=같은 출력). 계산의 LLM 위임은 어떤 예외도 없다.
2. **명리가 최종 권위**(총평·시기·길흉). 자미두수는 12궁 영역 서술·기질 묘사 보완 한정. 상충 시 명리 우선, "모순" 아닌 층위 차이로 재서술.
3. **사람 상담가의 글.** 예측 정확도 주장 전면 금지("적중" 등), 본문에 AI/도구/자동화 티 일절 금지, 반복 패턴·기호 난발 금지.
4. **고객 PII 0.** 이름·생년월일·질문 원문·본문 전문은 코드·로그·채팅·커밋·테스트 픽스처 어디에도 없다. 익명 ID(`DOC_A`, `CUSTOMER_1`)와 메타(page/char/rule/bool)만.
5. **APPROVED 후 수동 발송.** 자동 발송 없음. 상태머신이 물리 차단하며 우회 코드 작성 금지.
6. **유파 정책은 `docs/03` 결정표가 SSOT.** 자시/윤달/연경계/사화표는 config·enum 으로만 분기, 코드 하드코딩 금지. 정책 변경은 운영자 승인 + 골든 재검증.

## 이 세팅이 이런 모양인 이유 (규칙 <-> 실제 사고·결정 — 규칙을 "불필요한 관례"로 오판해 걷어내지 말 것)
| 세팅 | 존재 이유 (근거) |
|---|---|
| 다층 게이트(기하·저밀도·시맨틱·safe/fact 벨트) | gate_pass=true 인데 육안 불합격이 반복된 실사고 (docs/16 QI-2026-07-02-01/02) |
| PII digest·마스킹·익명 ID 규율 | verify_result raw 출력으로 고객명 노출 실수 + 표지 polish 로 생년월일 API 전송 결함 (2026-07-03 감사 P0-2) |
| 3원 교차(KASI)·골든 22건·자시 경계 앵커 | KASI 원본결함 3건 + 자시 정책 미배선으로 일주 오류(2026-07-03 감사 P0-1 — "문서가 보장한다"를 코드가 안 하고 있었음) |
| 손편집 HTML/PDF 금지·표준 게이트 파이프라인 전용 | 손편집 우회로 AI-meta·placeholder 잔재 위험 (QI-2026-06-26-01) |
| 오류 시 도구·공식자료 우선 조사(runbook docs/17) | 같은 명령 반복으로 지연·신뢰 하락 (QI-2026-06-24-07) |
| 터미널 ASCII 평문·PS 스크립트 ASCII-only | cp949/xterm 한글 깨짐·파서 크래시 (QI-2026-06-24-06) |
| compose 결과 content.json 영속(무과금 재렌더) | 레이아웃 수정마다 재compose 과금 낭비 (QI-2026-07-02-02) |
| "검증 없는 완료 보고 금지"(증거 규율) | 사용자 2회 교정 이력 + 감사에서 문서-코드 불일치 6건 적발 |

## 작업 규율 — YOU MUST (요약. 상세·실증 사례는 `.claude/rules/10-methodology.md`)
1. **실측 우선**: 결함/완료 주장은 재현 프로브·측정치·테스트 출력으로만. "아마 ~일 것" 금지. 확인 못 한 것은 "미검증"으로 분리 명시.
2. **증거 있는 완료 보고**: 완료 주장 = 실행 명령 + 출력(passed 수/exit code) + 커밋 SHA. 증거 없으면 미완료로 간주한다.
3. **양방 테스트**: 게이트/가드/차단룰 수정은 (정상 통과 + 결함 차단) 양방 회귀를 같은 커밋에 동반. 결함 케이스는 합성 주입, PII 0.
4. **사각 인접 탐색**: 결함을 고치면 그 규칙의 경계값·이웃 조건(자릿수/임계 ±1/스코프 제외)에 같은 결함이 남는지 탐색한다.
5. **문서-코드 정합**: 정책 enum/플래그를 만들면 소비처까지 배선하고 분기 테스트를 둔다. 문서가 보장하는 규칙은 코드 프로브로 증명된 것만 유효.
6. **근본원인 2층**: 표면 결함과 함께 "왜 지금까지 못 잡았나"(감지 시스템의 구멍)를 고치고, 사고는 `docs/16` 장부에 기록한다.
7. **오류 시 조사 우선**: 같은 명령 반복 금지. 공식 문서/이슈 트래커 1차 자료 조사 후 결론(`docs/17` 순서). 스택 버전 변경은 골든 전수 재검증 동반.

## Programmatic checks — 코드 변경 후 반드시 전부 실행 (YOU MUST)
```
./.venv/Scripts/python.exe -m pytest tests/ -q
```
- 통과 기준: exit code 0. (기준선 2026-07-04: 512 passed / 4 skipped. passed 감소 = 회귀.)
- `calc/`·`input/` 변경 시 골든(test_golden_sweep 22건) 포함 전체 GREEN 없이는 커밋 금지.
- PDF 산출 검증(재생성·LLM·커밋 없음):
```
./.venv/Scripts/python.exe scripts/hrun.py --profile harness/profiles/local/personal_h153.yml --profile harness/profiles/local/gunghap_h153.yml
```
- 통과 기준: `handoff/reports/<stamp>/summary.json` 의 `pytest.returncode == 0` + `gate_pass` 비악화. `--no-tests` 리포트는 완료 근거로 사용 금지.
- PDF 재생성/LLM 은 3중 잠금: `--regen --allow-llm` + env `SAJUGEN_HARNESS_ALLOW_REGEN=1` 전부 충족 + 운영자 명시 승인 시에만.
- bare `pytest`·`python` 금지(전역 파이썬 오염) — 항상 `./.venv/Scripts/python.exe`.

## 역할 분리
- **Cursor (사람+IDE)**: 탐색·편집·diff 검토. 변경 전 `.cursor/rules/*` 컨텍스트 확인.
- **Claude Code = 설계자·최종 리뷰어**: 상태 실측 → 승인용 TASK_PACKET 작성 → Codex 구현 결과를 신선 컨텍스트에서 독립 검증한다. 운영자가 Claude 구현을 별도로 승인한 경우만 예외다.
- **Codex = 구현자·자체 검증자**: 승인된 TASK_PACKET의 허용 파일만 수정하고 Programmatic checks와 증거 보고를 수행한다. Claude가 직접 구현한 태스크에서는 별도 지시가 있을 때 read-only 리뷰어가 된다.
- 기본 사이클은 `Claude 설계 → Codex 구현 → Claude 교차리뷰 → 사용자 checkpoint` 한 번이다. Claude PASS 뒤 Codex를 다시 확인자로 보내지 않는다. 예외는 Claude 직접 구현·미해결 의견 충돌·릴리스급 별도 감사·운영자 명시 지시뿐이다.
- Playwright 실렌더처럼 환경 종속 검증은 패킷이 지정한 증거 소유자만 실행한다. 다른 환경의 예정된 skip은 코드 실패가 아니며 동일 tree SHA·수집 총수·skip 사유로 분리 증거를 합성한다.

## Phase 0 containment — handoff source of truth
- 고객 납품·품질 사고 대응은 역할을 분리한다: Claude는 Plan Architect와 Semantic Reviewer, Codex는 승인된 TASK_PACKET 구현자다. Claude가 직접 구현한 예외 태스크만 신선 Codex 세션이 검증한다.
- 구현의 source of truth는 `handoff/templates/task_packet.json` 형식의 TASK_PACKET(또는 승인된 로드맵 문서, 예: `handoff/audit-followup-roadmap.md`)이다. 구현 보고와 검증 보고는 분리하고, 세션 전환은 `handoff/templates/context_snapshot.md` 형식을 따른다.
- 실제 활성 지시문은 `handoff/current/manifest.json`의 `packet_path`와 SHA 하나뿐이다. `next_action` 자유문장으로 다른 미고정 task packet을 지시하지 않는다.
- 납품 후보는 표준 게이트 파이프라인에서만 만든다. 손편집 HTML/PDF는 최종 납품 기준선으로 쓰지 않고, 실제 PDF는 render_verify·금칙 텍스트 스캔·300dpi 시각 점검·운영자 전문 검수 전 발송 금지다.
- 컨텍스트가 길어지면 대화 전문이 아니라 파일 경로, SHA, 결정사항, 실패 rule만 인계한다. 최신본 판단은 파일명이 아니라 SHA 기준.
- 고객 실데이터, PDF, PNG, summary는 gitignore 영역에만 둔다(`tmp/`·`synthetic-tmp/`·`*.content.json` 포함 — 2026-07-03 감사 A-1).
- 세부 운영 순서는 `docs/17-agent-tooling-runbook.md`, 품질 사고 기록은 `docs/16-quality-incident-ledger.md`, PDF 수동 검수는 `handoff/templates/pdf_review_report.md`.

## Codex 운영 계약 (권한 경계 — 강제는 코드·게이트·git hook, 이 절은 경계 정의)
1. manifest `next_actor=codex`이고 승인된 TASK_PACKET이 구현을 지시하면 Codex가 구현자다. Claude 구현분 검증이나 운영자 명시 read-only 태스크에서는 판정만 한다.
2. 수정 권한은 TASK_PACKET의 허용 파일·수용 기준으로 한정한다. 요구사항을 충족하려면 허용 파일 밖 수정이 필요하거나 실행 능력과 완료 조건이 모순되면 우회하지 않고 `BLOCKED_CONTRACT`로 정지한다.
3. Codex 전용 상시 금지(구현 승인을 받은 뒤에도 금지): PDF 재생성, LLM(Anthropic API 포함) 호출, git commit, push, 배포(deploy).
4. 데이터 경계: (a) 접근 금지 — `.env`·secret 값, 실고객 데이터, `harness/profiles/local/**` 비열람. 실데이터 확인은 PII 제거된 `summary.{json,md}`만. (b) 인용 금지 — 리뷰·리포트에 PII(실명·생년월일·출생시간) 인용·전재 금지.
5. (구현 승인 시) `calc/`·`input/` 변경 -> 같은 작업 단위에 골든·회귀 테스트 동반(절대규칙 20, calc.md).
6. (구현 승인 시) `content/` 변경 -> 3단 가드(safe_lint/factcheck/trace) 완화·우회 금지(절대규칙 12, content.md).
7. (구현 승인 시) `sajugen/render/**`(특히 `render/verify.py`) 변경 -> 기존 `gate_pass` 구성 비악화(게이트 키 제거·완화·기준 하향 금지, render.md) + 양방 테스트(작업 규율 3).
8. (구현 승인 시) 주문/검수 경로(`order_flow.py`·`store/orders.py`·`admin.py`·`app.py`) 변경 -> APPROVED 전 발송 차단 회귀(`tests/test_orders.py`·`tests/test_final_render_gate.py`) 통과 필수(절대규칙 16).
9. 승인 근거 리포트: 해당 환경에서 실행 가능한 전체 tests를 직접 실행한다. `scripts/hrun.py` 증거가 필요한 태스크는 `--no-tests` 없이 만든 `summary.json`의 `pytest.returncode == 0`을 요구하되, 패킷에 지정된 다른 환경의 실렌더 증거를 Codex가 억지로 재현하지 않는다.
10. 판정은 `CODE_PASS`·`EVIDENCE_SPLIT_PASS`·`CHANGES_REQUESTED`·`BLOCKED_ENV`·`BLOCKED_CONTRACT`로 구분한다. 리포트는 diff·`git status`·`git log`·동일 tree SHA와 함께 종합하며, 환경별 raw passed 수만 직접 비교하지 않는다.

## 불변 제약 (요약 — 원문 `.claude/rules/00-immutable.md`)
- 계산은 LLM 위임 금지. `sajugen/calc/`·`input/` 수정은 테스트+골든 회귀 동반.
- 가드(safe_lint/factcheck/trace + 확장 lint 군) 우회·완화 금지.
- APPROVED 전 발송 금지. 예측 정확도 주장 금지. 본문에 AI/도구 산출 고지 금지.
- 한국어(주석·커밋·문서). 산출 PDF·`.env`·`data/`·`tmp/`·`*.content.json` 비커밋.
