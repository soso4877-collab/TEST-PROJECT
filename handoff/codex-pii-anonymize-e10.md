# [Codex 지시문] E10 — 실명 익명화 전수 (코드 주석·도크스트링·테스트 픽스처·문서)

> 형식: 승인된 TASK_PACKET(산문판). **웨이브2 교차리뷰 PASS 뒤 별도 세션에서 실행**(웨이브2와 동시 작업 금지 — 같은 파일 충돌).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review. 커밋 = 리뷰 PASS 후.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·LLM 호출·PDF 재생성. 한국어.
- **로직 변경 0** — 이 패킷은 문자열(이름) 치환 전용. 함수·분기·게이트·상수 구조를 바꾸지 않는다.
- 이 패킷은 예외적으로 `sajugen/input/partner.py`의 **주석 1곳** 수정을 포함한다(로직 무변경). input/ 이 diff에 잡히므로 골든 전수 재검증이 필수 동반이다(아래 §4).

## 1. 배경·상태(전제)
- 2026-07-10 운영자 확정: 코드·테스트·문서에 남은 아래 이름들 = **전부 실제 사람**(초기 고객·관계자). AGENTS 4조(PII 0) 기존 위반.
- 살아있는 실행 경로의 실명은 웨이브1(`6126d7a`)에서 이미 제거됨. 남은 것 = 주석·도크스트링·테스트 픽스처 ~250행 + 문서 8파일 ~24행.
- 시작 HEAD·기준선 = 웨이브2 리뷰 PASS 후 값으로 갱신해 착수(착수 지시문에 명시됨).

## 2. 치환 매핑 (결정론 — 전 파일 일관 적용)
| 실명 | 합성명 | 비고 |
|---|---|---|
| 김태수 / 태수 | 김민준 / 민준 | 웨이브1 _GH_SYSTEM 합성 예시와 통일 |
| 김태성 / 태성 | 이서연 / 서연 | 동일 |
| 장순조 / 순조 | 박도윤 / 도윤 | **"순조롭-"(순조롭게/순조로운)은 일반어 — 치환 금지** |
| 김동황 | 최지호 | rules.py:1764 도크스트링 |
| 장재화 | (이미 코드 제거) | 문서 잔존분만 익명 표기 |
| 가현 | 하은 | 테스트 픽스처 |
| 상철 | 준서 | 테스트 픽스처 |
- 호칭·조사 파생형("태수 씨"·"태수와 태성"·"김태수는")도 매핑대로 일괄 치환하되, 조사 받침 정합(은/는·와/과)을 깨뜨리지 않는지 치환 후 해당 assert 재확인.

## 3. 대상 (2026-07-10 실측 기준)
1. **테스트 픽스처·단언 ~250행**: `tests/test_client_tone.py`·`test_consistency.py`·`test_followup_gate.py`·`test_gate_contract.py`·`test_gunghap.py`·`test_harness.py`·`test_hsweep_contract.py`·`test_llm_usage.py`·`test_partner.py`·`test_quality_lint.py`·`test_render_verify.py`·`test_repetition.py`·`test_sdk_retry_policy.py`·`test_style_lint.py`. 이름은 입력 데이터이자 단언 문자열 — 매핑 일관 치환이면 의미 불변.
2. **코드 주석·도크스트링**: `sajugen/content/client_tone_lint.py`(266·274·286·291·296·322·355·369·382·416 등 예시), `sajugen/content/rules.py:1764`, `sajugen/input/partner.py:176`(주석 — §0 예외).
3. **문서**: `docs/00-research-ledger.md`·`docs/11-manselyeok-reference-cases.md`·`handoff/codex-ilji-tension-followup.md`·`handoff/codex-question-adaptive-q1-q7.md`·`handoff/design-question-adaptive.md`·`handoff/PROJECT_CONTEXT_AND_HARNESS_BRIEF_FOR_CHATGPT.md`·`REVIEW-FEEDBACK.md`·`sajugen/STATE.md` — 실명을 합성명 또는 "실명 N건(익명화됨)" 표기로. **이 패킷 파일 자신의 §2 매핑표도 마지막에 실명 열을 "N1~N7(파기)"로 자기 정화**(매핑 원본은 운영자 개인 보관).
4. **docs/11 만세력 골든 참조 케이스**: 이름 라벨은 치환하되 **생년월일시 데이터는 보존**(계산 골든 기준선). 실존 인물 생년월일 자체의 보관 여부는 운영자 결정 사항 — 패킷 범위 밖, 보고에 플래그만.

## 4. 수용 기준
- 전체 pytest exit 0, **기준선(착수 시점 값) 대비 passed 감소 0**(테스트 수 불변 — 치환만).
- **골든 전수**: `pytest -k golden` GREEN(입력값·계산 무변경 증명. partner.py는 주석만이지만 input/ diff라 필수).
- 잔존 스캔 (**v2 정정 2026-07-10: git grep = tracked 파일 전용.** raw `grep -r`은 gitignored
  `sajugen/render/out/**` 실고객 산출물까지 읽어 Codex 실데이터 접근 금지와 충돌 — Codex 정지 보고 실측 확인):
  `git grep -nE "김태수|김태성|장순조|김동황|장재화" -- sajugen tests docs handoff "*.md"` → 0건.
  `git grep -nE "태수|태성|가현|상철" -- sajugen tests` → 0건.
  `git grep -n "순조" -- sajugen tests | grep -v "순조롭\|순조로"` → 0건.
  ("청마"는 코드에서 이미 제거 — 문서 잔존분만 확인. "요청마다" 오탐 주의.)
- **ignored 영역 접근·수정 절대 금지**: `sajugen/render/out/`·`tmp/`·`synthetic-tmp/`·`data/`·`*.content.json` —
  실고객 산출물 포함. 열람·grep·수정 전부 금지(그 안의 실명 정리는 운영자 별도 액션, 이 패킷 범위 밖).
- 치환 전후 `git diff --stat`으로 로직 파일 변경이 문자열 행에 한정됨을 보고.

## 5. 완료 보고
실행 명령 + pytest·골든 출력 + 잔존 grep 결과 + docs/11 생년월일 보존 플래그. 커밋 없이 멈춤 → 교차리뷰.

## 범위 밖
git 이력의 실명(history rewrite = 운영자 별도 결정), 로직·게이트·상수, `harness/profiles/local/**`, 웨이브2 파일(동시 수정 금지).
