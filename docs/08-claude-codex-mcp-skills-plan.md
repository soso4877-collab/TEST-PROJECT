# 08. Claude Code / Codex / MCP / Skills Plan

## 2026-06-24 update: tool-first workflow

Decision: keep MCP MVP at zero for sajugen product work. Use installed Codex/GitHub Skills and repo-native harnesses before adding a new MCP server.

Why:

- Codex already exposes Skills, GitHub integration, shell, web search, AGENTS.md, and MCP as separate tool surfaces. For this repo, GitHub PR/CI/review work is covered by the installed GitHub Skills and connector.
- MCP tools are external-system calls that a model may invoke automatically. The MCP tool spec also treats annotations as untrusted unless they come from trusted servers, and structured outputs still need client validation. That is too broad for customer birth data, PDFs, `.env`, and `data/` until a specific read-only use case is proven.
- The recurring failures were not caused by missing MCP. They were process gaps: missing hrun evidence in the AI plan, sandbox/network confusion, Playwright probe noise, pytest hang diagnosis, and quality incidents not being consulted first.

Use order:

1. Repo docs and gates: `AGENTS.md`, `CLAUDE.md`, `.claude/rules/00-immutable.md`, `docs/14-tone-spec.md`, `docs/16-quality-incident-ledger.md`, `docs/17-agent-tooling-runbook.md`.
2. Installed Skills: GitHub Skills for PR/CI/review, local Codex Skills for reusable workflows.
3. Repo tools: `scripts/hrun.py`, `scripts/ai-harness.ps1`, targeted pytest, PDF verify.
4. External MCP only if it passes the checklist in `docs/17-agent-tooling-runbook.md`.

Deferred improvement: create a personal `sajugen-workflow` Codex Skill only after this workflow repeats again. The Skill should point to `docs/17-agent-tooling-runbook.md` and avoid duplicating full project rules.

> 최초 작성: 2026-06-10. 공식자료 확인: docs/00 §A. 원칙: AI 도구 = 개발·검증 전용, 제품 런타임은 공식 API 호출만.

## 기존 자산 (설치 완료, 유지)
- .claude/agents 6종: sg-planner/sg-calc-architect/sg-accuracy-verifier/sg-content-guard(opus급), sg-render-runner/sg-extractor(sonnet).
- test-project/.claude/settings.json: SessionStart+PreCompact 훅(STATE.md 자동주입).

## 추가 구성 (Phase 진행 중 점진 도입)

| 항목 | 시점 | 내용 |
|---|---|---|
| CLAUDE.md (test-project 루트) | Phase 8 | 테스트 명령, 경계 규칙(계산 수정 시 골든 스냅샷 필수, LLM 계산 금지), @AGENTS.md import |
| .claude/rules/calc.md | Phase 1~ | paths: sajugen/calc/** — "계산 변경은 테스트 동반 + 3원 교차 재확인" |
| .claude/skills/saju-engine-audit | Phase 1 후 | KASI 3원 교차+골든 회귀 일괄 실행 절차 |
| .claude/skills/safety-expression-check | Phase 7 | safe_lint+반복(n-gram) 검사 절차 |
| permissions.deny 보강 | Phase 4 | 주문 DB(data/orders.sqlite)·고객 PDF 출력 경로 보호 |
| PostToolUse hook | 선택 | calc/·content/ 편집 후 해당 pytest 자동 실행, 실패 시 block(exit 2) |

## 개발용 모델 라우팅 (2026-06-10 적용, 공식: code.claude.com/docs/en/model-config + /en/advisor)

| 용도 | 모델 | 설정 위치 |
|---|---|---|
| 플랜 모드(설계·추론) | Fable 5 | ~/.claude/settings.json: model="opusplan" + env ANTHROPIC_DEFAULT_OPUS_MODEL="claude-fable-5" |
| 실행(메인 루프) | Opus 4.8 | env ANTHROPIC_DEFAULT_SONNET_MODEL="claude-opus-4-8" (opusplan 비플랜 단계) |
| 중요 결정 시점 자문 | Fable 5 | advisorModel="fable" — 접근 확정 전·오류 반복·완료 선언 전 Claude가 자동 호출(advisor tool, 실험적) |
| sg-planner/calc-architect/accuracy-verifier/content-guard | claude-opus-4-8 풀네임 핀 | .claude/agents frontmatter |
| sg-render-runner/sg-extractor | claude-sonnet-4-6 풀네임 핀 | .claude/agents frontmatter |
| 제품 런타임 LLM | 변경 없음 (docs/06: Haiku 윤문/Sonnet 질문답변) | content/llm_polish.py 등 |

운영 규칙: **이 프로젝트 서브에이전트 모델 하한선 = Sonnet 4.6.** Haiku는 읽기 전용 탐색·분류 한정(공식 카탈로그 "simple tasks" 용도 — 검증 해석·골든 스냅샷 갱신은 범위 초과).
전역 ~/.claude/settings.json은 git 밖이므로 스냅샷 사본을 docs/global-claude-settings.snapshot.json 으로 추적(변경 시마다 갱신 — defaultMode=plan, opusplan 라우팅, advisor 포함).
주의: (a) opusplan 플랜 단계는 200K 컨텍스트 고정(공식 명시). (b) 전역 env로 인해 `opus` 별칭=Fable 5, `sonnet` 별칭=Opus 4.8로 해석됨 — 별칭 대신 풀네임으로 핀할 것. (c) Fable 5는 보안·생물 분류기 플래그 시 Opus 4.8 자동 폴백. (d) advisor는 실험적 기능 — 동작 변경 가능.

## Codex 병행 (보류 — 1인 운영 MVP 불요)
- 도입 시: AGENTS.md 단일 소스 + CLAUDE.md @import. skills는 .agents/skills/(경로 상이 주의). PR 리뷰 @codex review, CI는 API 키.

## MCP (MVP 0개로 시작)
- kasi-calendar-mcp: 불요 — calc/kasi.py+pytest로 충분. github MCP: WebSearch로 대체. DB MCP: 고객 정보 포함이라 보류(도입 시 읽기전용+마스킹 뷰).
- 도입 기준: 외부 데이터 다건 연결 필요 시점에 MCP 스펙 보안 권고(2025-11-25: tool=임의코드 취급, 동의 MUST, token passthrough 금지) 체크리스트 적용.
