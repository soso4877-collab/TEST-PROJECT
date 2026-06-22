# Codex 리뷰 요청 — <변경명>

## 리뷰 대상
- 브랜치: <branch>
- diff: `git diff <base>..HEAD`(또는 첨부 diffstat)
- 검증 리포트: `handoff/reports/<stamp>/summary.md` (+ `summary.json`)

## 봐줄 관점
1. 게이트 회귀: gate_pass·name_policy·identity_role·singang_role·loanword·raw_calc 가 모두 clean인가. hit count 0인가.
2. 규칙 drift: 금지어·정규식이 `client_tone_lint`/`verify` 밖에 복제되지 않았는가.
3. 안전: calc/ diff 0, PII(실명·생년월일) 비커밋, `.env`/키 비노출, 산출 PDF·임시파일 비커밋.
4. 결정성·테스트: 무LLM 경로 결정론, 신규/회귀 테스트가 의도를 고정하는가.

## 표준 리뷰 체크리스트 (Claude 구현 후 — 변경 영역에 해당하는 항목만 체크)
> 범위: 아래 "0" 조건은 Claude 작업에서 "운영자의 명시 승인 없이 실행된 작업이 0건"이라는 뜻이다(승인받아 수행한 작업은 위반이 아니며, 별도로 승인 근거·범위·결과를 기록한다). Codex 자신에게는 AGENTS.md "Codex 운영 계약" 3항의 상시 금지(승인 후에도 금지)가 그대로 적용된다.
- [ ] 권한: 이 diff는 Claude 작업분이다(Codex 직접 구현 0). Codex 수정이라면 운영자 사안별 승인 근거가 첨부됨.
- [ ] PDF 재생성: 미승인 0
  - 승인 없음: PDF 재생성 0 확인 (기본 근거: `summary.json`의 `regen_allowed=false` + 각 `pdfs[].regen`이 "skipped"로 시작. 보조: 직전 baseline 리포트가 있으면 `pdfs[].sha256` 동일 비교 — baseline 없거나 missing_pdf면 이 보조는 생략).
  - 승인 있음: 운영자 승인 근거 · 승인된 범위 · 실행 결과 확인.
  - 승인 범위를 넘은 재생성은 0이어야 함.
- [ ] LLM 호출: 미승인 0
  - 승인 없음: LLM 호출 0 확인 (근거: `final_report.md` "LLM 호출 0 확인"(항목 7) 자기보고 + diff에 LLM 호출 경로/명령 추가 없음. 주: `regen_allowed=false`는 PDF 재생성 경로 미진입 근거일 뿐 LLM 호출 0의 직접 증거는 아님).
  - 승인 있음: 운영자 승인 근거 · 승인된 provider/목적/범위 · 실행 기록 확인.
  - 미승인 호출은 0이어야 함.
- [ ] commit: 미승인 0
  - 승인 없음: 신규 commit 0 (근거: `git log --oneline <base>..HEAD`에 신규 커밋 없음 + `final_report.md` "커밋 안 함 확인"(항목 13)).
  - 승인 있음: 승인 근거 · commit hash · 검토 대상 범위 기록.
  - 미승인 commit은 0이어야 함.
- [ ] push: 미승인 0
  - 승인 없음: push 0 (근거: `final_report.md` "push 안 함 확인"(항목 14) 자기보고 + 실행 로그/운영자 확인. 한계: `git log @{u}..HEAD`는 push 여부를 증명하지 못함(이미 push된 커밋이면 비어 있음) — 보조 참고만).
  - 승인 있음: 승인 근거 · remote/ref · 실행 로그 또는 운영자 확인.
  - 미승인 push는 0이어야 함.
- [ ] 안전: `git status --short`에 `.env`·secret·실데이터·`profiles/local`·`render/out`·`reports` 추적 0, `summary.json`의 `preflight.secret_hit_count=0`.
- [ ] calc/input 변경 시 → 골든 회귀(2000-01-01 등) + p1~p5 GREEN(근거: `summary.json` pytest 섹션). 주: 이 경우 `preflight.calc_diff_empty`는 `false`가 정상(calc 변경 포함) — 골든 회귀 GREEN으로 대체 판단. calc/input 무변경이면 `calc_diff_empty=true`를 확인한다.
- [ ] content 변경 시 → 3단 가드 완화 없음, 금지어·정규식이 `client_tone_lint`/`verify` 밖에 복제 안 됨(근거: diff).
- [ ] render/** 변경 시 → `gate_pass` 구성 비악화: 키 제거·기준 하향 없음(근거: diff + `summary.md` gates 줄).
- [ ] order_flow/admin/store 변경 시 → APPROVED 차단 회귀 `tests/test_orders.py` GREEN(근거: `summary.json` pytest).

## 승인 근거 게이트
- [ ] 첨부 리포트가 `hrun.py` 기본 실행본이다(= `--no-tests` 아님). `summary.json`의 `pytest.returncode == 0`.
- [ ] `summary.json`의 `preflight.preflight_ok=true` 와 `all_gates_pass=true`(또는 `pdfs[].status=missing_pdf` 사유 명시).

> final_report.md 인용은 줄번호 없이 항목 번호+필드명으로만 고정: 항목 7="LLM 호출 0 확인", 항목 8="PDF 재생성 0 확인", 항목 13="커밋 안 함 확인", 항목 14="push 안 함 확인".

## 판정
- [ ] 머지 가능   - [ ] 수정 필요(아래)
- 코멘트:
