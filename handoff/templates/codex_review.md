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

## 판정
- [ ] 머지 가능   - [ ] 수정 필요(아래)
- 코멘트:
