# 구현 상태 기록 — 2026-07-10 질문 적응형 풀이

## 라운드17 교차리뷰 — 2026-07-12 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. `일정/일정한` 오탐 소수정(제품 2파일, +32/-1) — 승인 범위 밖 변경 0.
  정본 = `REVIEW-FEEDBACK.md` 라운드17 절.
- 기준환경 확정: **949 passed / 4 skipped / exit 0**(941+8, 감소 0) — 새 기준선. golden 28, 집중 70,
  변경 2파일 Ruff/py_compile/diff-check GREEN. 경계 프로브 14건 전부 기대 일치.
- 비블로커: 인접 `일정하다/일정해서` 잔존 오탐(승인 스코프 밖, fail-closed). 절차 이탈 1건(broad rg →
  render/out 매치, 자진 보고) — 재발 방지 = 이후 패킷 0절에 ignored 제외 글롭 문구 필수.
- 다음: 운영자 checkpoint commit 결정 → (별도 과금 승인 시) Phase C replacement 1회.
- **종결(2026-07-12)**: 제품 checkpoint commit = `e6145fc`(fix, 2파일 +32/-1). **라운드17 PASS**,
  새 기준선 **949 passed / 4 skipped**. `일정하다/일정해서`는 실제 관측 시에만 확장하는 비블로커.
  beta-1-schedule-boundary done + archive 동결. API·PDF·비용·hsweep K/Z·육안 Z=0 미검증.
  다음 = 운영자의 Phase C replacement 1회 과금 승인 결정.

---

## 라운드16 advisory `일정/일정한` 오탐 소수정 — 2026-07-12 (Codex)

- 상태: **구현·자체 검증 완료 / Claude 신선 컨텍스트 교차리뷰 요청**.
- 제품 변경: `sajugen/content/delivery_quality.py` 일정 fact 정규식 1곳을 `일정(?!한|하게|하지)`로 경계화하고,
  `tests/test_register_advice_gate.py`에 수용 기준 명사형 차단 4건·인접 명사형 차단 1건·형용사 활용형 허용 3건을 추가했다.
- 기존 “외부 도메인 + 사실/절차” 계약과 고정 토큰 `일정`, 다른 차단 패턴, 게이트 키는 바꾸지 않았다.
  제품 diff = 2파일, 32+/1-. 정책 문서·다른 게이트 수정 0.
- 실측: 수정 전 차단 5=True/허용 예정 3=True → 수정 후 차단 5=True/허용 3=False. 신규 8 passed,
  관련 집중 70 passed, 전체 **921 passed / 32 skipped / exit 0**(동일 환경 913/32+8), golden 28.
  변경 Python Ruff GREEN, py_compile exit 0, `git diff --check` exit 0.
- 금지 준수: API·PDF·hsweep·유료 재생성·hrun·commit·push·main 전진 없음.
- 절차 기록: 초기 broad `rg`가 비대상 `sajugen/render/out/**`까지 1회 매치했다. 출력 내용을 인용·전재·수정하거나
  PII 확인을 위해 재열람하지 않았고, 이후 탐색 범위를 제품 코드·테스트로 제한했다.
- 인계 정본: `handoff/tasks/beta-1-schedule-boundary-20260712.md`. 다음 = Claude가 diff+검증을 독립 재실행해
  PASS면 운영자 checkpoint commit 결정. replacement는 여전히 별도 과금 승인 전 실행 금지.

---

## 라운드16 교차리뷰 — 2026-07-12 (검증 세션, 리뷰어 Claude)

- 판정: **PASS(CODE_PASS)**. 패킷 `beta-1-register-harness-20260712` A~D 전 항목 diff 근거 확인.
  정본 = `REVIEW-FEEDBACK.md` 라운드16 절.
- 기준환경 확정: **941 passed / 4 skipped / exit 0**(831+110, 감소 0) — 새 기준선. golden 28.
  Ruff 신규 0(HEAD 부채 19건 동일 구성 대조 실측), py_compile 43파일·diff-check GREEN, calc/input diff 0.
- advisory 1건(비블로커): `일정` 외부사실 패턴이 형용사 `일정한`에 오탐(프로브 실측). 골격 무저촉,
  영향은 LLM 후보 룰 폴백(fail-closed). 다음 라운드에서 오탐 축소 방향 개선 후보.
- 리뷰어 수정 = 허용 4파일만(REVIEW-FEEDBACK·STATE·이 파일·manifest는 handoff 도구). read-only 56파일
  SHA-256 시작/종료 스냅샷 전수 일치.
- 다음: 운영자 checkpoint commit 결정 → (별도 과금 승인 시) replacement 주문 1회 → 게이트/hsweep/육안 Z.
- **종결(2026-07-12)**: checkpoint commit = `5b0a88f`. beta-1-register-harness **CODE_PASS 태스크 종결**
  (manifest done + `handoff/archive/beta-1-register-harness-20260712.json` 동결). 실제 API·PDF·prompt cache
  비용·hsweep K/Z·육안 Z=0은 여전히 미검증. 다음 = 유료 재생성 전 라운드16 advisory `일정/일정한` 오탐
  소수정 여부 결정 → 이후 운영자 별도 과금 승인 시에만 Phase C replacement 1회.

---

## 베타 1호 Z>0 개선 구현 후보 — 2026-07-12 (Codex)

### 현재 상태

- 브랜치 `codex/gunghap-relationship-quality`, 시작·현재 HEAD `5ebd3b6`, upstream 대비 ahead 0 / behind 0.
- 베타 1호 육안 Z>0를 계기로 문체 register·외부 실무조언·어려운 용어·hsweep 판정 구조·LLM 비용 관측을 함께
  보완했다. 워킹트리는 미커밋이며 현재 판정은 **CODE_PASS / Claude 교차리뷰 요청**이다.
- 세션 시작 때 이미 수정돼 있던 `docs/16-quality-incident-ledger.md`와 `docs/23-beta-operation.md`의 Claude Phase A
  기록은 보존했다. 그 기록을 구현 계약과 hsweep v2 사실에 맞춰 확장했으며 되돌리지 않았다.

### 완료한 구현

1. `docs/14-tone-spec.md`를 문체 register·외부 도메인 조언·첫 등장 쉬운 풀이의 기계 판독 SSOT로 확장했다.
2. register 하드 게이트를 cover·toc·본문·appendix 전역에 연결하고, 외부 사실/절차 조언을 독립 실패 원인으로
   연결했다. builder 최초 후보·재시도·룰 폴백, 개인·궁합·관계·followup·최종 PDF가 같은 판정을 사용한다.
   최종 섹션을 다시 집계해 룰 골격 위반도 `GuardReport.clean=False`가 되도록 pre-render false-PASS를 닫았다.
3. consult의 의미 없는 action 표지를 제거하고 `work_career` 축을 추가했다. 7개 질문 카테고리와 followup 골격,
   질문 미러링 허용/후속 조언 차단을 양방 테스트로 고정했다.
4. PII 없는 `ReportContext`를 추가했다. 12개 Sonnet 장은 같은 결정론 context/cache prefix를 공유하되 현재 장
   ID는 호출별 user 블록으로 받는다. 상품별 비활성 용어 소유 장은 활성 장으로 결정론 재배정한다.
5. Anthropic explicit cache를 fail-closed로 배선했다. 첫 호출에서 cache usage가 관측된 경우에만 나머지 호출을
   3병렬로 실행한다. 모델은 Sonnet 4.6을 유지하고 role/model/section/attempt/cache/thinking/stop usage를 PII 없이
   run 단위로 격리·주문 메타에 저장한다.
6. hsweep를 비파괴 schema v2로 개편했다. raw→rank(advisory)→judge 전수→운영자 review를 분리하고 K/Z를
   운영자 판정으로만 계산한다. PII manifest·정밀 마스킹·partial/stage/usage·v1 migration·canonical review와
   gitignored atomic temp를 추가했다.
7. 게이트 레지스트리·하네스 요약/검증·운영 문서를 새 키와 지표에 맞춰 동기화했다.

### 수정 파일 전체 목록

- 기존 Claude 기록에서 시작: `docs/16-quality-incident-ledger.md`, `docs/23-beta-operation.md`.
- 문서: `docs/01-product-context.md`, `docs/02-architecture.md`, `docs/05-nlg-pdf-generation.md`,
  `docs/06-llm-usage-policy.md`, `docs/07-safety-and-compliance.md`, `docs/09-roadmap.md`,
  `docs/14-tone-spec.md`, `docs/16-quality-incident-ledger.md`, `docs/20-gate-coverage.md`,
  `docs/23-beta-operation.md`.
- 하네스 프롬프트: `harness/prompts/sweep/lens_direct_answer.md`,
  `harness/prompts/sweep/lens_narrator_tone.md`.
- 제품 코드: `sajugen/cli.py`, `sajugen/content/builder.py`, `sajugen/content/client_tone_lint.py`,
  `sajugen/content/delivery_quality.py`, `sajugen/content/llm_polish.py`, `sajugen/content/llm_sections.py`,
  `sajugen/content/llm_usage.py`, `sajugen/content/rules.py`, `sajugen/content/sections_schema.py`,
  `sajugen/followup/answer_gate.py`, `sajugen/gunghap.py`, `sajugen/integrated.py`, `sajugen/order_flow.py`,
  `sajugen/pipeline.py`,
  `sajugen/relationship/context.py`, `sajugen/relationship/delivery_gate.py`, `sajugen/render/pdf.py`,
  `sajugen/render/verify.py`.
- 하네스 코드: `scripts/hrun.py`, `scripts/hsummary.py`, `scripts/hsweep.py`, `scripts/hverify_pdf.py`.
- 기존 테스트 수정: `tests/test_chapter_fallback_observability.py`, `tests/test_consistency.py`,
  `tests/test_consult_gate.py`, `tests/test_delivery_quality.py`, `tests/test_followup_gate.py`,
  `tests/test_gate_contract.py`, `tests/test_harness.py`, `tests/test_hsweep_contract.py`,
  `tests/test_integrated_order_flow.py`, `tests/test_integrated_product.py`, `tests/test_llm_sections.py`,
  `tests/test_llm_usage.py`, `tests/test_myeongni_ziwei_weave.py`, `tests/test_pii_masking.py`,
  `tests/test_postprocess.py`, `tests/test_skeleton_lint_matrix.py`, `tests/test_verify_gate_meta.py`.
- 신규 파일: `sajugen/content/report_context.py`, `tests/test_register_advice_gate.py`,
  `tests/test_report_context.py`, `tests/test_tone_spec_contract.py`.
- 인계 기록: `sajugen/STATE.md`, `implementation-notes.md`,
  `handoff/tasks/beta-1-register-harness-20260712.md`, `handoff/current/manifest.json`.
- 계산·입력 SSOT인 `sajugen/calc/**`, `sajugen/input/**`은 변경하지 않았다.

### 검증 증거

- `./.venv/Scripts/python.exe -m pytest tests/ -q` → **913 passed / 32 skipped / exit 0**(116.48s).
  Codex 환경 기존 803/32 대비 passed 감소 0, 신규 검증 +110.
- `./.venv/Scripts/python.exe -m pytest tests/ -q -k golden` → **28 passed / exit 0**.
- register/context/tone/hsweep/PII 핵심 합성 → **123 passed**.
- 독립 리뷰: register/context/골격 68 passed·최종 PASS, hsweep canonical/temp 보안 57 passed·최종 PASS,
  usage run 격리/cache fail-closed 47 passed·최종 PASS.
- 변경 Python 중 기존 Ruff 부채 파일 3개를 제외한 검사 → `All checks passed!`.
- 전체 변경 Python `py_compile` exit 0, `git diff --check` exit 0, calc/input diff 0.
- 변경 파일 전체 Ruff는 기존 HEAD 부채 19건 때문에 exit 1: `rules.py` F841 1+F541 16,
  `render/pdf.py` F401 1, `render/verify.py` F841 1. 이번 변경의 신규 위반으로 판정된 항목은 0.

### 확인하지 못한 것과 남은 위험

- 실제 Anthropic API를 호출하지 않았으므로 prompt cache hit, 실제 호출 수·비용 절감, Sonnet 문안 품질은
  **확정 불가**다. 모델을 낮추거나 바꾸지 않았다.
- 고객·ignored 산출물과 local profile을 열지 않았고 PDF를 재생성하지 않았다. 새 replacement PDF의 조판,
  표준 게이트, hsweep K/Z, 운영자 육안 Z=0은 미검증이다.
- 정규식은 등재한 register·외부 조언 조합만 막는다. 폐쇄 목록 밖 의미 결함은 hsweep와 육안 Z가 계속 맡는다.
- Claude 기준환경 예상은 총 수집 수 산술상 941 passed / 4 skipped지만 직접 실행 전에는 확정값이 아니다.
- commit·push·APPROVED·발송은 하지 않았다.

### 다음 행동

1. Claude 신선 컨텍스트가 `handoff/tasks/beta-1-register-harness-20260712.md`를 기준으로 diff 전량과 기준환경
   전체 pytest를 교차리뷰한다.
2. PASS 뒤 운영자가 checkpoint commit 여부를 결정한다.
   이때 미추적 필수 파일 5개(packet·`report_context.py`·신규 테스트 3개)를 경로로 명시해 함께 추가한다.
   `git commit -am`만 사용하면 import/계약 파일이 빠지므로 금지한다.
3. 별도 과금 승인 후에만 기존 로컬 접수 절차로 replacement 주문을 1회 생성한다.
4. 새 PDF에서 표준 게이트→hsweep→운영자 전문 육안 검수를 실행하고 Z=0일 때만 승인·수동 발송한다.

---

## 베타 트랙 세션 인계 — 2026-07-12 (Claude)

- 완료: docs/23 확정(N=3 무료·재발급 1인 선행) / A-2 정리(389파일 repo 밖, QI-2026-07-11-01 종결) / 베타 1호 접수·4모듈 확정·LLM 생성(gate_pass=True·36p·DRAFTED) / hsweep 파일럿 1호(N=29·M=0·K=0·$0.41).
- 대기 지점: **운영자 육안 검수 + Z 값 보고**(익명 문서 `DOC_BETA_1`). 인계 정본 = `handoff/tasks/beta-1-issuance-20260712.md`.
- 새 세션은 "이어받아"로 시작 — manifest가 이 패킷을 가리킨다.

---

## 감사 A-1 라운드15 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. 테스트 전용(test_render_verify.py +91, 제품 diff 0) — M1 차단측(text_layer 임계 양방)·M3 이중화(verify 경유 delivery 전용). 정본 = `REVIEW-FEEDBACK.md` 라운드15 절.
- 기준환경 확정: **831 passed / 4 skipped / exit 0**(829+2, 감소 0) — 새 기준선. 변이 재검 직접 재실행으로 M1·M3 격추 실증(원복 완료). **감사 2026-07 생존 변이 0, 코드 후속 종결.**
- 커밋 완료(2026-07-11 운영자 지시): `3f36b39` test(A-1) / docs(기록·manifest). manifest = done + archive. feat push + main ff 전진·push. 감사 코드 후속 종결.
- 다음: 베타 트랙 — docs/23 초안 작성.

---

## Q7 given 가드 라운드14 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. v2 패킷(정지→정정 경유) 그대로 — given_name 출력 동등성 술어, 접수 전 차단, 경계표 차단 5·통과 4 고정. 정본 = `REVIEW-FEEDBACK.md` 라운드14 절.
- 기준환경 확정: **829 passed / 4 skipped / exit 0**(820+9, 감소 0) — 새 기준선. 골든 28, Ruff GREEN, 프로브 실측.
- **Q7 전체 완결** — 알려진 잔여 0. 선택 항목만: LLM-on 정상 쌍 N=5 실측·main 전진·육안 검수.
- 커밋 완료(2026-07-11 운영자 지시): `5519899` feat / docs(기록·manifest). manifest = done + archive. feat push + **main ff 전진·push — Q7 프로젝트 종결.**

---

## Q7 4단계 라운드13 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. 2인 접수·gunghap 주문화(접수 additive·추천 분기·admin/confirm 조건화·생성 2인 분기·partner_present 실소비) 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드13 절.
- 기준환경 확정: **820 passed / 4 skipped / exit 0**(801+19, 감소 0) — 새 기준선. 골든 28, Ruff GREEN, 프로브·합성 실렌더 N=5(2인) 실측.
- 실렌더 N=5: 35p로 분량 하한(30p) 통과 — 관계 조립 실작동. 발견 R13-1(비블로커·기존 경로): 무LLM 관계 문안 수신자 '씨' 호칭 → role 게이트 차단. LLM-on 해소 여부 미검증.
- 커밋 완료(2026-07-11 운영자 지시): `c8cd1cc` feat(4단계 10파일) / docs(기록·manifest). manifest = done + archive. push 완료.
- R13-1 처리: (a)안 실측 완료(2026-07-11) — LLM-on N=5도 GATE FAIL(동일 호칭 룰 17회 + identity_role + 저밀도 1쪽). ~~문안 수정 발주 필요로 확정~~ **[정정 2026-07-11]** 위반 문형 추출로 재판정: 프로브 합성 쌍의 given 동일("합성")이 원인인 입력 엣지. given 상이 쌍(김민준/이서연) 무LLM N=5 = **gate_pass True·35p·전 게이트 clean** → 수정 발주 불필요, 2인 N=5 상품 정상. 잔여 = 동명 given 커플 접수 차단 추가 여부만 결정 대기.

---

## Q7 3-B 라운드12 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. admin 모듈 추천·확정 UI(추천 표시 전용·NORMALIZED 한정 확정·정규화 위임·audit 모듈 ID만) 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드12 절.
- 기준환경 확정: **801 passed / 4 skipped / exit 0**(778+23, 감소 0) — 새 기준선. 골든 28, Ruff GREEN, 실경로 프로브 3종 실측.
- 절차 이탈 0 — QI-2026-07-11-01 재발 방지(`!**/` 글롭) 첫 적용 라운드에서 유효 확인.
- **Q7 3단계 완결.** 커밋 완료(2026-07-11 운영자 지시): `8098f84` feat(3-B 7파일) / docs(기록·manifest). manifest = done + archive. push 완료.
- 합성 실렌더 실측 완료(2026-07-11): 무LLM N=1 21p PASS / N=2 22p PASS / N=3 23p FAIL(-1p) / N=4 24p FAIL(-4p) → 룰 전용 분량 모듈당 +1p vs 공식 +4p. LLM-on N=4 = 34p **PASS**(과금 승인분, calls 18).
- 분량 정책 확정(운영자): 공식 유지 + 알려진 제약 "무LLM 폴백 발급은 N≤2만"(N≥3 = LLM-on 전제). 산출 PDF는 render/out 비커밋.
- 다음: 4단계(gunghap·2인 접수) 별도 설계. LLM-on 문안 육안 검수는 운영자 영역 잔존.

---

## Q7 3-A 라운드11 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. 주문 플로우 integrated_full 편입(계산 입력 배선·접수/시진불명 차단·미확정 차단·3지점 분기·후속 차단) 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드11 절.
- 기준환경 확정: **778 passed / 4 skipped / exit 0**(758+20, 감소 0) — 새 기준선. 골든 28, Ruff 8파일 GREEN, 실경로 프로브 P1~P3 차단 실측.
- 절차 이탈 2회차(비블로커): 원인 = 패킷 글롭 예시가 루트 기준으로 불충분 → 이후 패킷 `!**/...` 형식 고정. docs/16 기록 권고.
- 커밋 완료(2026-07-11 운영자 지시, 분리안 2커밋): `ac5d8f2` feat(3-A 8파일) / docs(기록·manifest·QI). manifest = done + archive. push 완료. 절차 이탈 2회 = docs/16 QI-2026-07-11-01 기록.
- 다음: 3-B(admin 추천·확정 UI) 발주 → 라운드12.

---

## Q7 2단계 라운드10 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. CLI `--module` 배선(2파일) 수용기준 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드10 절.
- 기준환경 확정: 전체 pytest **758 passed / 4 skipped / exit 0**(753+5, 감소 0) — 새 기준선. 골든 28, Ruff 2파일 GREEN, 실 프로세스 차단 3종 exit 1 실측.
- 절차 이탈 1건(비블로커): Codex 광역 rg가 ignored render/out/** 일부를 검색 결과에 포함(수정·전재 없음, 자진 보고). 재발 방지 권고 기록, docs/16 여부 운영자 결정 대기.
- 커밋 완료(2026-07-11 운영자 지시, 분리안 2커밋): `ff002ee` feat(CLI 2파일) / docs(기록·manifest). manifest = done + archive. push 완료. Q7 1·2단계 종결.
- 다음: 3단계(admin·주문 플로우 편입)는 별도 설계·승인. 이후 Codex 패킷에 ignored 제외 글롭 필수 문구 포함.

---

## Q7 1단계 라운드9 재검 — 2026-07-10 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. R9-1 종결, Q7 1단계 미해결 0. 정본 = `REVIEW-FEEDBACK.md` 최상단 "라운드9 재검" 절.
- 기준환경 확정: 전체 pytest **753 passed / 4 skipped / exit 0**(745+8, 감소 0) — 새 기준선. 골든 28. 허용 밖 동결 7파일 SHA 불변 실측, 수정 2파일 Ruff GREEN.
- 프로브: 라운드9 동일 스크립트 재실행으로 P1·P3·P4·P5 전부 차단 전환 확인 + 통과측 G1~G4 오탐 0.
- 이 세션 수정 = 상태·리뷰 4파일만. 제품 코드 비접촉, commit/push/PDF/sajugen LLM 호출 없음.
- 커밋 완료(2026-07-10 운영자 지시, 분리안 3커밋): `065c987` feat(제품 9파일) / `fbdb296` chore(handoff 공존 3파일) / docs(기록·manifest). manifest = done + archive 동결.
- 다음: Q7 2단계(CLI/admin)는 별도 승인·패킷 발주. push는 지시 대기.

---

## Q7 1단계 교차리뷰 라운드9 — 2026-07-10 (검증 세션, 리뷰어 Claude)

- 판정: **changes_requested**. v3 수용기준 전 항목 GREEN이나 R9-1(module_sections 소유권 교차검증 사각) 1건 보완 필요. 정본 = `REVIEW-FEEDBACK.md` 라운드9 절.
- 기준환경 확정: 전체 pytest **745 passed / 4 skipped / exit 0**(728+17, 감소 0), 골든 28, 동결 SHA 10건 MATCH, Ruff 신규 위반 0.
- 이 세션 수정 파일 = 상태·리뷰 4개만(`REVIEW-FEEDBACK.md`·`sajugen/STATE.md`·`implementation-notes.md`·`handoff/current/manifest.json`). Q7 제품 코드·테스트 9개는 SHA 동결 그대로 비수정. commit/push/PDF 재생성/sajugen 런타임 LLM 호출 없음.
- 다음: Codex가 R9-1만 수정(예상 범위 `sajugen/modules.py`+`tests/test_integrated_modules.py`, 양방 회귀 동반) → 라운드9 재검 → PASS 후 사용자 checkpoint commit 결정.

---

## Q7 1단계 구현 후보 검증·SHA 인계 — 2026-07-10

### 현재 상태

- 브랜치 `codex/gunghap-relationship-quality`, HEAD `0b3134fe7ef508dde6f4d45952a132016a687fc8`, upstream 대비 ahead 20 / behind 0.
- 승인 source of truth는 `handoff/codex-q7-stage1.md` v3다. v2 이후 sparse 병합의 현행 유지와 병합 전 커버리지 판정까지 정정된 커밋이 HEAD에 포함돼 있다.
- Q7 1단계 제품 구현 후보는 미커밋 상태다: tracked modified 7개 + 신규 2개. 이전 최상단의 “Q7 코드 미착수” 기록은 과거 정지 시점의 이력이며 현재 상태가 아니다.
- 상태 판정은 `review_requested`다. 라운드9와 기준환경 4-skip 전체 검증 전에는 `verified`·`done`이 아니다.

### 실측한 구현 범위

- `sajugen/modules.py`: schema v1 레지스트리, 5모듈 정규화, 섹션 소유권, 병합 전 커버리지, N별 하한 계산.
- `sajugen/content/rules.py`·`builder.py`: job/wealth 제공자 분리와 선택 밖 개인 장 생성 제외.
- `sajugen/integrated.py`: 현행 순서 필터링 후 sparse 병합, 병합 전 ID/모듈 맵 보존, 선택 메타 저장·복원.
- `sajugen/content/delivery_quality.py`·`render/verify.py`: 모듈 하한과 missing/unexpected fail-closed 게이트 배선.
- 관련 테스트 3파일: 5모듈 완전 동일성, N=1..5 경계, missing/unexpected, gunghap 1인/2인, job/wealth 분리, 메타 재렌더 회귀.
- `sajugen/calc/**`, `sajugen/input/**`, CLI, admin, order/state-machine 변경은 0이다. Q7 2단계는 미착수다.

### 검증 증거

- Q7 대상 3파일: `43 passed`, exit 0.
- 신규 모듈 테스트 단독: `17 passed`, exit 0.
- 전체: `.\.venv\Scripts\python.exe -m pytest tests\ -q` → `718 passed / 31 skipped`, exit 0. Q7 전 기준환경 `728/4` + 신규 17의 예상 `745/4`는 총 수집 수 749로 산술 일치하지만 기준환경 재실행 전이라 확정 불가다.
- 신규 두 파일 Ruff: `All checks passed!`, exit 0. 전체 `ruff check .`는 기존 부채 29건으로 exit 1이므로 전체 Ruff GREEN은 주장하지 않는다.
- `git diff --check` → exit 0(LF→CRLF 안내만). calc/input/CLI/admin/order 경로 diff 0.
- Phase2A 공존 계약 테스트: `tests/test_ai_harness_contract.py` → `25 passed`, exit 0. `git check-ignore --no-index`로 실행 산출물은 ignored(exit 0), 루트 manifest는 추적 가능(exit 1)을 확인했다.
- 로컬 SessionStart relay: `relay-context.mjs --format claude` → exit 0, verified task/status/SHA/next actor/action의 structured JSON 출력. 실제 새 `codex exec` 실주입은 외부 전송 보안 검토에서 차단돼 확정 불가다.

### 이번 SHA 인계 적용과 기존 Q7 변경의 구분

- 이 세션은 위 Q7 제품 코드·테스트 9개의 내용을 수정하지 않았다. 인계 패킷에 적용 전 SHA-256을 동결했다.
- 이번 세션 변경은 `handoff/current/.gitignore`, `handoff/current/README.md`, `tests/test_ai_harness_contract.py`, `handoff/tasks/q7-stage1-modules-20260710.md`, `implementation-notes.md`, `sajugen/STATE.md`, `handoff/current/manifest.json`과 AI-Brain의 sajugen 포인터 정합화다.
- 기존 Phase2A 런타임은 유지한다. 실행 폴더·task/LATEST/log/run-manifest는 계속 ignored이고 루트 `manifest.json`만 SHA 역할 교대 포인터로 추적 가능하다.
- commit, push, PR, deploy, PDF 재생성, LLM 호출은 실행하지 않았다.

### 미완 지점과 다음 행동

1. 신선 Claude 세션이 `handoff/tasks/q7-stage1-modules-20260710.md`와 v3 지시문을 기준으로 라운드9 교차리뷰한다.
2. 기준환경 전체 pytest 예상 `745 passed / 4 skipped`를 직접 확정한다.
3. `module_sections`에 잘못된 모듈↔섹션 소유권을 합성 주입하면 현재 게이트가 탐지하지 못하는 사각을 라운드9에서 판정한다.
4. PASS 뒤 사용자가 Q7 checkpoint commit 여부를 결정한다. 그 전에는 Q7 2단계·실렌더를 시작하지 않는다.
5. 현재 `REVIEW-FEEDBACK.md`는 Q7 이전 이력이며 Q7 라운드9 PASS 근거가 아니다.

---

## Q7 1단계 착수 점검 정지 — 2026-07-10

### 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 시작 HEAD: `7fa5d57` (`Q7 1단계 TASK_PACKET 발주 — 모듈 레지스트리·조립·게이트`). 현재 HEAD: `3be5d96` (`Q7 1단계 착수 점검 정지 기록`).
- 현재 원격 대비: ahead 18. 세션 시작 워킹트리는 깨끗했고 구현 파일 수정·push·deploy는 없다. 상태 기록 중 외부에서 패킷 v2 커밋 `c4443a1`과 상태 기록 커밋 `3be5d96`을 생성했으며, Codex는 commit을 실행하지 않았다.
- Q7 1단계 코드는 미착수다. 레지스트리·work 제공자·조립·게이트·테스트 변경은 모두 0줄이다.

### 이번 세션에서 완료한 태스크

- `handoff/codex-q7-stage1.md`와 승인 설계 `handoff/codex-q7-design.md`를 읽고 1단계 범위와 금지 경계를 대조했다.
- `sajugen/integrated.py`, `sajugen/content/rules.py`, `sajugen/content/delivery_quality.py`, `sajugen/render/verify.py`와 기존 integrated 테스트를 읽어 현행 조립·게이트 소비 경로를 실측했다.
- 합성 2인·무LLM·무렌더 프로브로 현행 섹션 ID 순서를 확인했다: `personal_intro → personal_nature → personal_work → personal_flow → personal_ziwei → personal_consult → integrated_full_depth → relationship_overview`.
- 패킷의 고정 순서(`core → love → job → wealth → health → gunghap → personal_consult → tail`)를 적용하면 `flow/ziwei`와 `personal_consult` 위치가 바뀌어, 동시에 요구된 “modules 미지정/5모듈 전체 = 현행 섹션 ID 리스트·본문 동일”을 만족할 수 없음을 확인했다.
- 결과물이 달라지는 플랜 모순이므로 임의 구현하지 않고 정지 보고했다. 상태 기록 중 패킷 v2가 현행 순서 필터링 방식으로 모순을 해소했지만, 이번 종료 세션에서는 구현을 재개하지 않았다.

### 이번 세션 수정 파일과 기존 잔존 파일 구분

- 이번 Codex 세션 수정 파일: `implementation-notes.md` 1개(현재 상태 기록만). 내용은 외부 프로세스가 `3be5d96`으로 커밋했으며 Codex는 커밋하지 않았다.
- 외부 동시 변경: `handoff/codex-q7-stage1.md`가 `c4443a1`에서 v2로 정정됐다. 설계의 추상 고정 순서를 폐기하고 “현행 순서에서 미선택 모듈만 필터링”하도록 변경해 하위호환 모순을 해소했으며, Codex가 수정하지 않았다.
- 기존 잔존 문서: `handoff/codex-q7-design.md`는 HEAD에 이미 있던 승인 설계이며 수정하지 않았다.
- 구현 후보인 `sajugen/integrated.py`, `sajugen/content/rules.py`, `sajugen/content/delivery_quality.py`, `sajugen/render/verify.py`, 관련 테스트는 수정하지 않았다.
- `sajugen/calc/`, `sajugen/input/`, CLI, admin, 상태머신·발송 차단은 모두 무변경이다.

### 검증·미검증

- 읽기 전용 `git status -sb`와 `git diff --name-only`로 구현 코드 diff 0을 확인했다. 외부 두 커밋 반영 뒤 워킹트리는 깨끗했으며, 이 최종 정합 보정으로 `implementation-notes.md`만 다시 미커밋 상태다.
- 합성 무렌더 조립 프로브는 exit 0이었다. LLM 호출·PDF 재생성·실렌더·ignored 영역 접근은 하지 않았다.
- 코드 변경이 없어 전체 pytest·린트는 실행하지 않았다. Q7 신규 회귀와 기준환경 `728 passed / 4 skipped` 비교도 미실행이다.

### 미완 지점과 다음 스텝

1. 다음 구현 세션은 외부에서 정정된 `handoff/codex-q7-stage1.md` v2 전체를 다시 읽고, 현행 순서 필터링 규칙을 source of truth로 확정한다.
2. 레지스트리·work 제공자·부분 조합 조립·모듈 게이트·content 메타 배선을 구현한다.
3. 5모듈 완전 동일성, N=1~5 분량 경계, missing/unexpected, gunghap 1인 차단/2인 통과, job/wealth 분리 양방 테스트를 추가한다.
4. 대상 테스트와 전체 pytest, Ruff, `git diff --check`, calc/input diff 0을 검증하고 교차리뷰 라운드9에 넘긴다.

### 세션 종료

Codex Q7 1단계 착수 점검·모순 정지 보고·상태 기록 역할을 종료한다. 다음 세션은 정정된 v2 패킷을 기준으로 새 구현 세션에서 재개한다.

---

- E10 인접 탐색: 패킷에 열거되지 않은 `tests/test_relationship_quality_contracts.py` 1줄에서도 대상 이름 잔존을 확인해 tracked 수용 기준에 따라 동일 치환했다.

## 웨이브2 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 현재 HEAD: `fea0e7a` (`Q7 설계 4항목·Q4 문자 하한 운영자 승인 기록`)
- 구현 커밋: `fec5321` (`R6-1 + Q4~Q6 + Q7 설계`)
- 교차리뷰 라운드7 PASS 기록: `a568170`
- 원격 대비: ahead 11. 상태 기록 직전 워킹트리는 깨끗했으며, 이 문서만 현재 세션에서 수정한다.
- 완료 태스크: R6-1, Q4, Q5, Q6 구현. Q7은 승인된 1페이지 설계까지만 완료하고 코드 구현은 하지 않았다.
- 운영자 승인 완료: Q4 문자 하한(gunghap 3000자·followup 2000자), Q7 B안·분량 공식·RELATION 추천·기본 5모듈 전체.

## 웨이브2 완료 내용

- R6-1: `_PROVENANCE_CONTEXT_TERMS=()` 기본 비활성 상태는 유지하면서 합성 용어 monkeypatch로 `unbacked_context_terms` 차단 분기를 고정했다.
- Q4: gunghap 하한을 16쪽/3000자로 분리하고 followup 10쪽/2000자 상품을 추가했다. integrated_full 30쪽/10000자와 premium 10000자는 유지했다.
- Q4: 15쪽·2999자 차단, 16쪽·3000자 통과, 기존 30쪽 하한에서 막히던 18쪽 gunghap 통과를 양방 회귀로 고정했다.
- Q5: `gen-followup --pdf` opt-in 경로를 추가했다. 저장 Report23과 질문 카테고리별 `love/work/health` 근거 장을 재사용하고 새 consult만 조립한다.
- Q5: 연도·주제 범위 밖 질문, 10~15쪽 범위 위반, 저장 일간 부재를 주문 생성 전에 차단한다. 최종 발급도 저장 `bazi` 기반 identity 스펙과 동일 render_verify/delivery_quality를 사용하며 새 계산은 0회다.
- Q5: `--pdf`가 없는 기존 텍스트 주문의 반환·저장 경로는 유지했다.
- Q6: 접수 concern을 7종 QuestionCategory로 자동분류해 주문 메타에 저장하고 관리자 상세에 표시했다.
- Q6: 운영자 확정 POST가 Report23/후속 메타와 audit_log를 갱신한다. concern 있음+GENERAL+미확정 주문은 승인 409, 빈 질문·비GENERAL 주문은 기존 승인 흐름을 유지한다.
- Q6: APPROVED/DELIVERED 상태머신 전이 규칙은 변경하지 않았다.
- Q7: `handoff/codex-q7-design.md`에 모듈 레지스트리 B안, 조립 경계, 분량 공식, 게이트, CLI/admin 계약과 2안 비교를 작성했다. `sajugen/integrated.py` 변경은 0줄이다.

## 웨이브2 구현 파일 전체 목록

- `sajugen/content/delivery_quality.py`: R6-1 주입점 주석, 상품별 페이지·문자 하한, followup 질문 필수 게이트.
- `sajugen/followup/compose.py`: PDF용 저장 섹션 조립, 카테고리별 근거 장 선택, consult 직답·부모 가드 차단.
- `sajugen/order_flow.py`: 후속 PDF 표준 렌더/검증, 저장 일간 identity 복원, 분류 상태·운영자 확정·GENERAL 승인 전제조건.
- `sajugen/cli.py`: `gen-followup --pdf` opt-in 인터페이스.
- `sajugen/admin.py`: 질문 분류 상세 컨텍스트, 확정 POST, 승인 전제조건.
- `sajugen/web_templates/admin_detail.html.j2`: 7종 분류 표시·확정 드롭다운·차단 안내.
- `tests/test_delivery_quality.py`: R6-1 차단 회귀와 Q4 상품별 경계표.
- `tests/test_followup_pdf.py`: PDF 통과/범위 밖/페이지 초과/일간 부재/텍스트 회귀/CLI 배선.
- `tests/test_orders.py`: 접수 자동분류 저장 회귀.
- `tests/test_question_category_admin.py`: GENERAL 차단·운영자 확정·빈 질문/비GENERAL/텍스트 후속 양방 회귀.
- `handoff/codex-q7-design.md`: Q7 승인 전 설계 1페이지.
- `implementation-notes.md`: 현재 웨이브2 상태 기록(이번 사용자 요청으로 추가).

## 기존 잔존 파일과 분리

- `REVIEW-FEEDBACK.md`와 `sajugen/STATE.md`는 구현 파일이 아니라 별도 커밋 `a568170`·`fea0e7a`의 교차리뷰/운영자 승인 기록이다.
- `handoff/codex-question-adaptive-wave2.md`는 시작 HEAD `985031a`에 이미 있던 승인 TASK_PACKET이며 이번 구현 파일이 아니다.
- 웨이브1 Q1~Q3 코드는 커밋 `6126d7a`에 이미 존재했으며 웨이브2에서 재구현하지 않았다.
- `handoff/codex-pii-anonymize-e10.md`와 E10 실명 익명화 대상은 별도 패킷으로 유지했고 웨이브2에서 수정하지 않았다.
- `sajugen/calc/`, `sajugen/input/`, `sajugen/integrated.py`, 상태머신 허용 전이표는 무변경이다.

## 검증 증거

- Codex 샌드박스: `./.venv/Scripts/python.exe -m pytest tests/ -q` -> `701 passed, 31 skipped`, exit 0. 수정 전 688/31 대비 신규 13건 증가, passed 감소 0.
- 기준환경 교차리뷰: 같은 전체 명령 -> `728 passed, 4 skipped`, exit 0. 기준선 715/4 대비 신규 13건 증가, passed 감소 0.
- 기준환경 골든: `pytest -k golden` -> `28 passed`.
- 변경 Python 파일 Ruff -> `All checks passed!`; `py_compile` -> exit 0.
- `git diff --check` -> exit 0(LF→CRLF 안내만).
- `git diff --name-only -- sajugen/calc sajugen/input sajugen/integrated.py` -> 출력 없음.

## 확인하지 못한 것

- 후속 `--pdf`의 실제 10~15쪽 실렌더·조판·다운로드 동선은 미검증이다. 테스트에서는 렌더 엔진을 모의했다.
- 실제 LLM 호출과 LLM-on 문안은 미검증이다.
- Codex는 금지사항에 따라 `harness/profiles/local/**`를 열지 않았고 표준 hrun을 실행하지 않았다.
- 실제 브라우저 수동 UI 검수는 미실행이며 FastAPI TestClient 회귀만 통과했다.

## 남은 위험

- 실제 저장 섹션 길이에 따라 후속 PDF가 15쪽을 넘으면 fail-closed로 차단된다. 운영상 10~15쪽 안에 안정적으로 들어오는지는 승인된 합성 실렌더가 필요하다.
- 저장 `bazi`가 없는 레거시 부모 주문은 identity 게이트를 비활성화하지 않고 후속 PDF를 차단한다. 레거시 처리 정책은 별도 결정이 필요하다.
- admin `action_error` 문구 범용화로 최종 발급 실패 시 “APPROVED 상태 잔류” 안내가 사라진 비블로커가 라운드7에 기록돼 있다.
- Q7 설계는 승인됐지만 구현은 E10 완료 뒤 별도 TASK_PACKET으로 1단계(레지스트리·조립/게이트)와 2단계(CLI/admin)로 나눠야 한다.

## 다음 스텝

1. E10 익명화 패킷을 기준선 `728 passed / 4 skipped`, HEAD `fea0e7a`에서 별도 실행한다.
2. E10 교차리뷰·커밋 뒤 Q7 1단계 구현 패킷을 발주한다.
3. 운영자 승인 시 후속 `--pdf` 합성 실렌더로 실제 페이지 수·조판·게이트를 확인한다.
4. push는 별도 지시 전까지 하지 않는다.

## 웨이브2 세션 종료

Codex 웨이브2 구현·상태 기록 역할을 종료한다. 현재 세션은 `implementation-notes.md`만 미커밋으로 남기고 다음 작업자에게 인계한다.

---

## 웨이브1 기록

## 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 시작·현재 HEAD: `3a30667` (`Q1~Q3 TASK_PACKET v2`)
- 원격 대비: ahead 3. 이번 세션에서 commit·push·deploy 없음.
- 완료 태스크: Q1 관계 consult 이식, Q2 질문별 풀이 분기·실행 경로 PII 제거, Q3 관계 질문축 직답 게이트 강화·고유 키워드 일반화.
- Q4~Q7은 미착수. 패킷 지시대로 웨이브1에서 중단.

## 완료 내용

- Q1: relationship 섹션을 `overview -> consult -> intent` 순서로 조립한다. 빈 질문은 consult를 생략하고 `skipped=True`로 구분한다.
- Q1: 질문 분류를 context·폴백·LLM 작성 방향이 실제 소비한다. consult 원문은 생년월일·시각·출생지 마스킹 뒤 격리 인용한다.
- Q1: consult 후보는 compose 단계에서 검사하고 최대 2회 재작성한다. 모든 후처리 뒤 최종 직답 하드 게이트를 다시 적용한다.
- Q2: 초기 관계·장기/결혼·가족 조율·재회·일반 관계의 5개 결정론 분기를 추가했다. situation에 따라 폴백과 앞부분 요약이 실제로 달라진다.
- Q2: `gunghap.py`에서 재할당으로 죽어 있던 로컬 relationship 구현을 삭제했다. 살아있는 business 시스템 프롬프트·가이드·도크스트링의 타 고객 PII도 합성 예시 또는 일반 서술로 교체했다.
- Q3: 부모 동의·결혼 이행·장기 관계 축을 추가했다. consult는 감지된 질문축 중 하나가 아니라 각 축의 직접 근거를 모두 포함해야 통과한다.
- Q3: 지역 비교·모임/단체·도움을 주는 사람을 일반 트리거로 바꾸고 고객별 고유 키워드 상수를 제거했다.

## 이번 구현 파일

- `sajugen/relationship/context.py`: consult 슬롯, 질문 분류·축·5개 풀이 기준.
- `sajugen/relationship/fallback.py`: 질문별 consult 골격, 겹침축 보강, 앞부분 요약·중립 필러.
- `sajugen/gunghap.py`: 죽은 코드 삭제, PII 제거, 마스킹 인용, LLM 재작성, 최종 consult 게이트.
- `sajugen/content/delivery_quality.py`: 신규 3축과 축별 전수 evidence 판정.
- `sajugen/content/rules.py`: 지역·모임·조력자 일반화.
- `tests/test_question_adaptive_relationship.py`: Q1~Q2 통합·양방·겹침축 신규 회귀.
- `tests/test_delivery_quality.py`: Q3 차단/통과·동치류·기존 축 회귀.
- `tests/test_gunghap.py`: 빈 질문 consult 생략에 맞춘 이웃 회귀.
- `tests/test_llm_sections.py`: 일반화한 합성 맥락 회귀.
- `implementation-notes.md`: 이번 상태 기록.

## 기존 잔존 파일 구분

- 세션 시작 시 워킹트리는 깨끗했다. 위 구현 파일 외 기존 미커밋·미추적 파일은 없었다.
- HEAD에 이미 있던 패킷·설계·리뷰 기록은 이번 세션에서 수정하지 않았다.
- `sajugen/calc/`·`sajugen/input/`은 무변경이다.
- 기존 테스트 픽스처·주석·도크스트링의 PII 전수 익명화는 E10 별도 패킷 범위라 이번 세션에서 건드리지 않았다.

## 검증 증거

- `./.venv/Scripts/python.exe -m pytest tests/ -q` -> `688 passed, 31 skipped`, exit 0.
- 이 샌드박스 직전 기준 `668 passed, 31 skipped` 대비 신규 테스트 20개만 증가, passed 감소 0.
- 기준환경 기준선 `695 passed, 4 skipped`에 대한 예상값은 `715 passed, 4 skipped`; 기준환경 직접 실행은 미완료.
- 관계·질문 적응 관련 대상 테스트 -> 71 passed, exit 0.
- 최초 전체 실행에서 3건 실패를 확인한 뒤 각각 다른 원인으로 수정; 실패 3건 단독 재검증 -> 3 passed, 최종 전체 GREEN.
- Q2 파일 한정 PII 스윕 -> 0건.
- Q3 파일 한정 고객 고유 키워드 스윕 -> 0건.
- `git diff --name-only -- sajugen/calc sajugen/input` -> 출력 없음.
- `git diff --check` -> exit 0. 기존 LF/CRLF 경고만 있음.
- 변경 파일 Ruff 검사(`rules.py` 제외) -> `All checks passed!`.
- 전체 Ruff는 `rules.py`의 이번 diff 밖 기존 오류 17건 때문에 미통과.

## 확인하지 못한 것

- 실렌더 미검증.
- 실제 LLM 호출 미검증. 테스트는 모의 Anthropic 모듈만 사용했다.
- PDF 재생성·`harness/profiles/local/**` 열람·표준 hrun 미실행.
- 기준환경의 `715 passed / 4 skipped` 기대값 미검증.

## 남은 위험

- 실제 LLM 문안과 PDF 조판에서 질문 직답성과 분량이 유지되는지는 신선 컨텍스트 교차리뷰와 합성 실렌더로 확인해야 한다.
- 장기 관계 축은 승인 동치류인 `3년`, `몇 년`, `오래 만난`, `장기`, `오랜 연애`만 자동 분류한다. 다른 숫자 연도 단독 표현은 현재 범위 밖이다.
- 저장소 이력과 기존 테스트 픽스처의 PII 전수 익명화는 E10에서 별도 처리해야 한다.

## 다음 스텝

1. Claude 신선 컨텍스트 `/cross-review`에서 diff와 기준환경 전체 pytest를 검증한다.
2. 합성 실질문으로 표준 실렌더를 실행해 consult 위치·문안·게이트·조판을 확인한다.
3. 교차리뷰 PASS 후 운영자가 웨이브1을 커밋한다.
4. 이후 E10 익명화 패킷을 별도 발주하고, Q4~Q7은 재승인 전 착수하지 않는다.

## 세션 종료

Codex 구현 세션 역할을 종료한다. 워킹트리는 커밋하지 않은 상태로 교차리뷰에 인계한다.
