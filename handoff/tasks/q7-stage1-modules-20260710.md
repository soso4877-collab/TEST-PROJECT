# Q7 1단계 모듈 레지스트리·조립/게이트 — SHA 인계 패킷

- task_id: `q7-stage1-modules-20260710`
- status: `review_requested`
- base_commit: `0b3134fe7ef508dde6f4d45952a132016a687fc8`
- branch: `codex/gunghap-relationship-quality`
- upstream: `origin/codex/gunghap-relationship-quality` 대비 ahead 20 / behind 0
- 승인 지시문: `handoff/codex-q7-stage1.md` v3
- 승인 지시문 SHA-256: `bcc5fff81e552e028c3deb360da719fb94ea48d31ab51f676f6e04193dab7614`
- 다음 작업자: `claude`

## 프로젝트 성격과 불변 경계

이 저장소는 운영자 1인이 사용하는 `sajugen` 상담 상품 엔진이다. 생년월일시와 질문을 입력으로 받아 결정론 명리·자미 계산, 룰과 부분 LLM 산문, 다층 품질 게이트, tagged PDF, 관리자 검수 순으로 처리하고 `APPROVED` 뒤 사람이 수동 발송한다.

- 계산의 LLM 위임 금지. 명리가 최종 권위이고 자미는 보완이다.
- 고객 PII를 코드·로그·채팅·커밋·테스트에 남기지 않는다.
- 자동 발송 및 `APPROVED` 우회 금지.
- 유파 정책은 `docs/03-engine-validation-plan.md`가 SSOT다.
- Q7 1단계는 레지스트리·조립·게이트·메타·테스트만 다룬다. CLI `--module`과 admin UI는 2단계이므로 범위 밖이다.
- Codex는 PDF 재생성, LLM 호출, commit, push, deploy를 하지 않는다.

근거: `AGENTS.md`, `CLAUDE.md`, `sajugen/STATE.md`, `handoff/codex-q7-stage1.md`.

## 실측한 현재 상태

Q7 v3 범위의 구현 후보가 미커밋 워킹트리에 존재한다. 이번 SHA 인계 적용은 아래 제품 코드와 테스트를 수정하지 않았다.

| 파일 | 상태 | SHA-256 |
|---|---|---|
| `sajugen/content/builder.py` | modified | `7c18376ce68d851d56ef3fde073b9d73c6e1471442a1cda37fcdfe1546445d1c` |
| `sajugen/content/delivery_quality.py` | modified | `99a2661987cb5c7d82240de46254ad9aed48e966021bb12e2deeaaf3df905948` |
| `sajugen/content/rules.py` | modified | `87d76f77bd812f1642818934553dea6b85a9555922cf25bc0fcdab87d3186b09` |
| `sajugen/integrated.py` | modified | `b1573f514c74eaf12b940313cf0e0695ab7bb59afe77fd1a7b597c6a6a915d4d` |
| `sajugen/render/verify.py` | modified | `a2218e71e5be1e4a2b622129f8b80e7212abaf981c72d0d9be2810b555c516be` |
| `tests/test_integrated_content_meta.py` | modified | `9b75d2d63c62ece7b29517f014409d93558d79a00ec2b361b7c23b008c39ff07` |
| `tests/test_integrated_product.py` | modified | `d671838a0af44273937c4db22bf711f2a7ec8d0ac74b1d2f4d7f6f6c99917b0f` |
| `sajugen/modules.py` | untracked | `49cb546a1a7fd2b5177bb031a05c4d5f5a5eaac8ee6745107047d57bf56468bb` |
| `tests/test_integrated_modules.py` | untracked | `f6898a9b1a92edbb2e290d8b9a0957fa758a2ec50f990642e90b20663a18ece4` |

제품 tracked diff는 7파일 `+304/-43`이며 신규 파일은 `sajugen/modules.py`와 `tests/test_integrated_modules.py`다. `sajugen/calc/**`, `sajugen/input/**`, CLI, admin, order/state-machine 경로 diff는 0이다.

## Q7 v3 수용기준 대조

- 모듈 레지스트리와 schema version, 기본 5모듈 정규화가 구현되어 있다.
- job/wealth 제공자가 분리되며 기본 결합 순서와 본문 바이트를 보존하는 회귀가 있다.
- 현행 섹션 순서를 먼저 필터링하고 기존 sparse 병합을 유지한다. 커버리지는 병합 전 ID로 판정한다.
- N=1..5 페이지·문자 하한, missing/unexpected 차단, gunghap 1인 차단/2인 통과, content 메타 저장·복원 테스트가 있다.
- CLI `--module`, admin 추천 UI, Q6 자동 추천은 수정하지 않았다.

## 실행한 검증

```text
.\.venv\Scripts\python.exe -m pytest tests\test_integrated_modules.py tests\test_integrated_content_meta.py tests\test_integrated_product.py -q
43 passed / exit 0

.\.venv\Scripts\python.exe -m pytest tests\test_integrated_modules.py -q
17 passed / exit 0

.\.venv\Scripts\python.exe -m pytest tests\ -q
718 passed / 31 skipped / exit 0

.\.venv\Scripts\python.exe -m ruff check sajugen/modules.py tests/test_integrated_modules.py
All checks passed / exit 0

git diff --check
exit 0 (LF→CRLF 안내만)

.\.venv\Scripts\python.exe -m pytest tests\test_ai_harness_contract.py -q
25 passed / exit 0

git check-ignore --no-index handoff/current/RUN_EXAMPLE/plan-verdict.json
exit 0 (Phase 2A 런타임 ignored)

git check-ignore --no-index handoff/current/manifest.json
exit 1 (루트 SHA manifest 추적 가능)

node C:\Users\pc\.ai-harness\relay-context.mjs --repo C:\Users\pc\test-project --format claude
exit 0 / SessionStart structured JSON에 verified task_id·status·SHA·next_actor·next_action 출력
```

마지막 확정 기준환경은 Q7 전 `728 passed / 4 skipped`다. Q7 신규 수집 17건을 더하면 기준환경 예상은 `745 passed / 4 skipped`지만, 이는 아직 기준환경에서 재실행하지 않았으므로 **확정 불가**다. 현재 샌드박스의 `718+31=749`와 기준환경 예상 `745+4=749`는 총 수집 수가 일치한다.

전체 `ruff check .`는 exit 1, 기존 부채 29건이다. Q7 신규 두 파일은 GREEN이며 감사 시점 기준 Q7 추가 라인에서 새 Ruff 위반은 확인되지 않았다. 전체 Ruff GREEN을 이 태스크의 완료 근거로 주장하지 않는다.

## 판정과 다음 행동

현재 판정은 `review_requested`다. 구현 후보와 샌드박스 회귀는 GREEN이지만 다음이 없어 `verified`·`done`이 아니다.

1. 신선 Claude 세션이 승인 지시문 v3와 전체 diff를 라운드9로 교차리뷰한다.
2. 기준환경에서 전체 pytest를 재실행해 `745 passed / 4 skipped / exit 0`과 감소 0을 확정한다.
3. 5모듈 완전 동일성, N 경계표, missing/unexpected, 1인/2인 gunghap, job/wealth 양방을 독립 확인한다.
4. 구조화 `module_sections` 맵이 잘못된 소유권을 주장하는 경우(예: love에 `personal_health` 배정) 현재 missing/unexpected가 이를 탐지하지 못하는 사각을 보완할지 판정한다.
5. `REVIEW-FEEDBACK.md`의 현재 내용은 Q7 이전 라운드 기록이다. Q7 라운드9 결과가 생기기 전에는 PASS로 해석하지 않는다.
6. 라운드9 PASS 뒤에만 사용자가 checkpoint commit 여부를 결정한다. Q7 2단계는 별도 승인·패킷으로 시작한다.

## 확인하지 못한 것

- 기준환경 4-skip 전체 테스트와 Q7 라운드9: 미실행.
- 실제 PDF 렌더·조판·수동 육안 검수: 미실행.
- LLM-on 문안: 미실행.
- 실제 새 `codex exec` 프로세스의 hook 주입: 외부 AI 서비스로 프로젝트 메타가 전송될 위험 때문에 보안 검토에서 차단되어 확정 불가. 로컬 relay 구조화 출력까지만 검증했다.
- `module_sections` 자체의 소유권 위조·손상 차단: 현재 회귀에 없으며 라운드9 판정 필요.
- 메타가 없던 레거시 bundle은 대표 커버리지 맵으로 복원하므로 실제 손상 bundle의 누락까지 증명하지는 못한다.
- ignored 산출물, 실고객 데이터, `.env`, secret, `harness/profiles/local/**`: 비열람.
