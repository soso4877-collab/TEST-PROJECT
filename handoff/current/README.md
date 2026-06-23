# handoff/current — AI 하네스 런타임 작업 공간

Phase 2A 하네스(`scripts/ai-harness.ps1`)의 입력·산출물이 여기에 놓인다.
이 디렉터리에서 git에 추적되는 것은 `.gitignore`와 이 `README.md` 뿐이다.
나머지(작업 task, 실행 폴더, 로그, manifest, LATEST.txt)는 전부 gitignore 대상이다.

## 사용법
1. 템플릿 복사: `handoff/templates/ai_task.md` → `handoff/current/task.md` 작성
   (PII·secret 금지 — 생년월일·출생시간·실고객·API 키 넣지 말 것).
2. 하네스 실행:
   ```
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\ai-harness.ps1 -Stage Plan -Task handoff/current/task.md
   ```
   - 먼저 `-DryRun`을 붙여 실호출 없이 점검할 수 있다(런타임 산출물 미생성, 콘솔에 `DRYRUN=1`).
3. 결과 확인: `handoff/current/LATEST.txt`가 가리키는 실행 폴더 안의 `plan-verdict.json`을 본다.
   (`LATEST.txt`는 폴더 생성 직후 기록되므로 "최신 **시도** 실행"을 가리킨다 — 성공/실패와 무관.)
   - `PLAN_VERDICT = APPROVE`(종료코드 0) 또는 `BLOCK`(종료코드 2).
4. APPROVE면 계획을 사람이 검토 후 **별도 구현 단계**로 넘어간다(이 하네스는 구현하지 않는다).

## 산출물 (실행 폴더 `<runId>/` 안)
- `task.checked.md` — 고신뢰 secret 검사를 통과한 task(주의: PII는 자동 제거하지 않음 — 운영자가 PII를 넣지 않아야 함)
- `claude-response.json` — Claude 전체 JSON envelope
- `claude-plan.json` — envelope에서 추출한 structured_output(계획)
- `codex-plan-review.json` — Codex 리뷰 결과(PLAN_VERDICT)
- `plan-verdict.json` — 최종 판정
- `run-manifest.json` — 실행 메타(해시·버전·종료코드)
- `*-stdout.log` / `*-stderr.log` — Claude·Codex 실행 로그

## 경계
- 이 하네스는 **계획만** 다룬다. 구현·git commit/push·PDF 재생성·hrun 실행·sajugen 런타임 LLM 호출을 하지 않는다.
- PLAN_VERDICT(구현 전)와 DIFF_VERDICT(구현 후, 기존 `scripts/hrun.py` 경로)는 혼용하지 않는다.
