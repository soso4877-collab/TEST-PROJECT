# AGENTS.md — sajugen 협업 역할 분리 + 불변 제약

> 이 문서는 **컨텍스트 제공용**이다. 실제 강제는 코드(`scripts/hpreflight.py`·`scripts/hrun.py`의 검사와 exit code, `sajugen/render/verify.py` 게이트, pytest)와 git hook이 한다. 문서는 강제력이 없다.

## 프로젝트 한 줄
운영자 1인 내부 도구. 생년월일시·고민 → 진태양시 → 명리+자미 **결정론 계산** → 룰+부분 LLM 산문(챕터별 근거 슬롯) → 3단+가드 → tagged PDF → 관리자 검수 후 수동 발송. 상세: `CLAUDE.md`, `.claude/rules/00-immutable.md`, `sajugen/STATE.md`.

## 역할 분리
- **Cursor (사람+IDE)**: 탐색·편집·diff 검토. 변경 전 `.cursor/rules/*` 컨텍스트 확인.
- **Claude Code**: 승인 범위 안에서 구현·검증. 매 작업 단위로 plan→승인→구현→`hrun` 검증→보고. 커밋/푸시/PDF 재생성/LLM 호출은 명시 승인 시에만.
- **Codex (리뷰어)**: diff + `handoff/reports/<stamp>/summary.md`를 받아 게이트·회귀·안전(PII/secrets) 관점 리뷰. 리포트 파일로 공유(GPT 웹 붙여넣기 대체).

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
