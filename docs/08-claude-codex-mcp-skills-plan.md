# 08. Claude Code / Codex / MCP / Skills Plan

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

## Codex 병행 (보류 — 1인 운영 MVP 불요)
- 도입 시: AGENTS.md 단일 소스 + CLAUDE.md @import. skills는 .agents/skills/(경로 상이 주의). PR 리뷰 @codex review, CI는 API 키.

## MCP (MVP 0개로 시작)
- kasi-calendar-mcp: 불요 — calc/kasi.py+pytest로 충분. github MCP: WebSearch로 대체. DB MCP: 고객 정보 포함이라 보류(도입 시 읽기전용+마스킹 뷰).
- 도입 기준: 외부 데이터 다건 연결 필요 시점에 MCP 스펙 보안 권고(2025-11-25: tool=임의코드 취급, 동의 MUST, token passthrough 금지) 체크리스트 적용.
