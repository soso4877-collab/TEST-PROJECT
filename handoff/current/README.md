# handoff/current — Phase 2A 런타임 + SHA 인계 포인터

Phase 2A 하네스(`scripts/ai-harness.ps1`)의 입력·산출물이 여기에 놓인다.
동시에 Claude와 Codex의 역할 교대를 위한 SHA 인계 포인터도 이 경로를 사용한다.

두 계약은 파일 단위로 분리한다.

- 추적 가능: `.gitignore`, `README.md`, 루트 `manifest.json`(SHA 인계 포인터).
- 비추적: `task.md`, `LATEST.txt`, 실행 폴더, 로그, 실행 폴더 안 `run-manifest.json` 등 Phase 2A 런타임 산출물.
- 루트 `manifest.json`을 Phase 2A 산출물로 쓰거나, 실행 폴더의 `run-manifest.json`을 역할 교대 포인터로 쓰지 않는다.

SHA 인계 포인터의 schema·해시·경로·base ancestor 검증은
`C:\Users\pc\.ai-harness\handoff.mjs`가 담당한다. 동결 패킷은
`handoff/tasks/<task-id>.md`에 둔다.

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
- SHA 인계 manifest는 상태 포인터일 뿐이며 Q7 코드의 리뷰 PASS·커밋 승인을 대신하지 않는다.
- Phase 2A task와 SHA manifest의 task가 다르면 Claude/Codex 세션에 서로 다른 맥락이 섞일 수 있으므로 같은 실행에서 병행하지 않는다.
