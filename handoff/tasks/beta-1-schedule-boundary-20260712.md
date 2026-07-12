# TASK_PACKET — 라운드16 `일정/일정한` 오탐 소수정 교차리뷰

- task_id: `beta-1-schedule-boundary-20260712`
- base_commit: `1b46b47a606dc51924c05dabcca537d5dbb10a72`
- 구현자: Codex
- 다음 작업자: Claude 신선 컨텍스트
- 상태: `review_requested`
- 판정 범위: 라운드16 advisory였던 `일정` 명사형과 `일정하다` 활용형 경계만 CODE_PASS 검토한다.

## 0. 리뷰 권한·금지 경계

- 제품 코드와 테스트는 read-only로 검토한다. 수정이 필요하면 `REVIEW-FEEDBACK.md`에 미해결 항목만 기록하고
  제품 파일을 직접 고치지 않는다.
- API·PDF·hsweep·유료 재생성·commit·push·main 전진을 실행하지 않는다.
- `.env`, secrets, 고객/ignored 산출물, `harness/profiles/local/**`를 열지 않는다.
- 리뷰 기록이 필요하면 `REVIEW-FEEDBACK.md`, `implementation-notes.md`, `sajugen/STATE.md`,
  `handoff/current/manifest.json`만 수정한다.

## 1. 승인 범위와 구현

사용자 승인 범위는 external-domain 사실 패턴의 `일정/일정한` 오탐 1건뿐이다.

1. `sajugen/content/delivery_quality.py`
   - `_EXTERNAL_FACT_PATTERNS`의 일정 패턴만 `일정`에서 `일정(?!한|하게|하지)`로 경계화했다.
   - 명사와 조사형(`일정`, `일정을`, `일정은`, `일정하고`)은 계속 검출한다.
   - `일정하다` 활용형(`일정한`, `일정하게`, `일정하지`)만 제외한다.
   - 다른 domain/fact/procedure 패턴, finding 구조, 호출부, 게이트 키는 변경하지 않았다.
2. `tests/test_register_advice_gate.py`
   - 수용 기준 차단측 4건, 인접 명사형 차단 1건, 허용측 3건의 public
     `external_domain_advice_lint()` 양방 회귀를 추가했다.
   - `접수 일정`과 `일정을 확인하세요`는 기존 계약인 “외부 도메인 + 사실/절차”를 유지하도록 각각
     `시험 접수 일정`, `시험 일정을 확인하세요` 문맥에서 검사한다. 단독 문장 차단으로 계약을 확장하지 않았다.

제품 diff는 위 2파일, `32 insertions / 1 deletion`뿐이다. 정책 문서·다른 게이트 수정은 필요하지 않았고 하지 않았다.

## 2. 수용 기준

- 차단 유지: 시험 일정, 시험 접수 일정, 채용 일정, 시험 일정을 확인하세요.
- 인접 차단 유지: 명사+접속 조사인 `채용 일정하고 장소를 확인하세요`.
- 정상 허용: 일정한 속도, 일정하게 유지하다, 일정하지 않은 흐름.
- 차단측 finding의 `advice_terms`에 고정 토큰 `일정`이 실제 포함된다.
- 기존 external-domain 차단 매트릭스(마감·점수·요건·자격·연령·비용·규정·접수·제출·준비·발급·행정·절차)가
  모두 통과한다.
- 수정 파일은 linter 구현과 해당 양방 테스트뿐이며, 나머지는 인계 기록이다.

## 3. 구현자 실측 증거

```text
# 수정 전 public linter 프로브
차단측 5건=True / 허용 예정 3건=True(오탐 재현)

.\.venv\Scripts\python.exe -m pytest tests\test_register_advice_gate.py -q \
  -k "schedule_noun_forms or schedule_adjective_forms"
→ 8 passed / exit 0

# 수정 후 public linter 프로브
차단측 5건=True / 허용측 3건=False

.\.venv\Scripts\python.exe -m pytest \
  tests\test_register_advice_gate.py tests\test_tone_spec_contract.py \
  tests\test_skeleton_lint_matrix.py -q
→ 70 passed / exit 0

.\.venv\Scripts\python.exe -m pytest tests\ -q
→ 921 passed / 32 skipped / exit 0
  (동일 Codex 환경 라운드16 913/32 + 신규 8, 감소 0)

.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
→ 28 passed / exit 0

.\.venv\Scripts\python.exe -m ruff check \
  sajugen\content\delivery_quality.py tests\test_register_advice_gate.py
→ All checks passed / exit 0

.\.venv\Scripts\python.exe -m py_compile \
  sajugen\content\delivery_quality.py tests\test_register_advice_gate.py
→ exit 0

git diff --check
→ exit 0
```

## 4. Claude 교차리뷰 순서

1. HEAD가 `1b46b47`인지, 제품 diff가 위 2파일뿐인지 확인한다.
2. 정규식 경계가 명사형 차단을 유지하면서 세 활용형만 허용하는지 직접 프로브한다.
3. 신규 양방 테스트가 다른 규칙에 기대어 거짓 통과하지 않는지 `advice_terms` assertion까지 검토한다.
4. 집중 3파일, 전체 pytest, golden, 변경 Python Ruff·py_compile, `git diff --check`를 직접 실행한다.
5. 기준환경의 라운드16 기준선은 941/4였으므로 신규 8건을 더한 산술 예상은 949/4다. 직접 실행 전 확정하지 않는다.
6. PASS면 `verified/next_actor=user/checkpoint commit 결정`, 수정 필요면
   `changes_requested/next_actor=codex/REVIEW-FEEDBACK 미해결만 수정`으로 manifest를 갱신한다.

## 5. 미검증·남은 경계

- API·PDF·hsweep·유료 재생성·hrun은 사용자 금지에 따라 실행하지 않았다.
- 새 replacement 문안·prompt cache·비용·조판·게이트·hsweep K/Z·육안 Z는 이 태스크 판정 범위 밖이며 미검증이다.
- bare `접수 일정`·bare `일정을 확인하세요`는 외부 도메인 표지가 없으므로 기존 계약대로 단독 차단하지 않는다.
  이를 바꾸려면 문서·룰 계약 확장이 필요하며 이번 패치에는 포함하지 않는다.
- 절차 이탈 1건: 초기 broad `rg`가 비대상 `sajugen/render/out/**`까지 매치해 출력 조각이 도구 결과에 포함됐다.
  해당 내용을 인용·전재·수정하지 않았고 PII 여부 확인을 위한 재열람도 하지 않았다. 이후 모든 탐색을 제품 코드·테스트로 제한했다.
