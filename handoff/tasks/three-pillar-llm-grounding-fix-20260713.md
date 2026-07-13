# TASK_PACKET — 삼주(three_pillar) 실LLM 콘텐츠 근거화·축 커버리지·오류경로 usage 영속

- task_id: `three-pillar-llm-grounding-fix-20260713`
- base_commit: `d318894ae9df5617d5ef21200d2439395ef87716` (HEAD 실측 — 활성화 시 운영자가 manifest SHA로 고정)
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰 (+ 실모델 재run 증거는 운영자/Claude 환경 몫)
- 상태: `draft`(미활성 — manifest 미고정. 운영자 승인 후 `planned/next_actor=codex`로 전환)
- 근거 사고: `docs/16` QI-2026-07-13-02 (첫 실LLM-on 삼주 유료 run 게이트 실패)

## 0. 우선순위·금지 경계

- 이 패킷은 QI-2026-07-13-02의 구현 후속이다. 게이트/가드 완화가 아니라 **생성(LLM) 측 근거화**와 **관측 갭 보강**이 목표다.
- Codex 상시 금지(구현 승인 뒤에도): PDF 재생성, LLM/Anthropic API 호출, git commit, push, deploy.
- 데이터 경계: `.env`·secret·실고객 데이터·`harness/profiles/local/**`·ignored 산출물을 읽거나 수정하지 않는다. 합성 입력만 사용한다.
- 이름·생년월일·질문 원문·본문 전문을 코드·로그·테스트·문서·채팅에 넣지 않는다. 익명 ID(`DOC_A`)·메타만.
- 검색 시 `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`를 적용한다.
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만 사용한다.

## 1. 배경 (PII 0 — 실측 증거)

첫 실LLM-on 생시 미상 삼주 `integrated_full` 주문(익명 `DOC_1F3817DC9C`, 모듈 `[job,wealth,health]`)이 유료 파이프라인 1회에서 게이트 실패로 `NORMALIZED` 정지(PDF 미생성)했다. 관측된 사실:

- 하드 게이트: `gate_pass=False`, `failed_clean_flags=[delivery_quality_clean, style_clean]`, `delivery_failures=[missing_question_axes]`(+`low_density` 절단).
- `classify` LLM = `InstructorRetryException`으로 룰 폴백(질문 분류 저하).
- `flow`·`consult`·`closing` 챕터 LLM 출력이 가드에 거부돼 룰 폴백:
  - factcheck가 삼주 금칙 토큰 `시주`(시주는 삼주에서 금지), 근거 없는 월주 간지(`정미월`·`경술` 등)를 차단.
  - consult는 `질문 직답 미달(question_topic)`.
- `delivery_quality.missing_question_axes`는 **고민 원문 기반**(`_required_axes(concern)`, 모듈 독립)이라, 룰 폴백 본문이 고민의 topic 축(직업/경제/건강 + 월별·이사·취미)을 못 채워 실패.
- 게이트는 정상 fail-closed(유출 0). 문제는 **삼주 LLM 경로가 허용 출처 밖 토큰을 생성**해 폴백을 유발하고, 폴백 본문이 축·style을 못 채운 것.

배선·계산은 정상 실측(무과금 dry-run): 절입 경계 차단 없음, KASI 음력 교차 정상(중국기준≠KASI→KASI 채택), 정오 미저장, three_pillar create→모듈확정→run_generation 전 구간 실행.

## 2. 목표 (관측 가능한 결과)

1. 삼주 `integrated_full` LLM 챕터가 허용 출처(`three_pillar`/`time_invariant`/`calendar_flow`) 밖 토큰(시주·미승격 월주 간지 등)을 **구조적으로 생성하지 않도록** 프롬프트·fact allowlist·compose slot을 정합시킨다(가드 완화 아님 — 생성 억제).
2. LLM 출력이 거부돼 폴백이 발생하더라도, 룰 폴백 골격이 고민 topic 축과 `style_clean`을 충족하는 **최소 보장**을 갖는다.
3. `run_generation` 오류 경로에서도 `llm_usage`(호출·토큰, PII 0)를 audit 또는 render_meta에 영속해 실패 run 비용을 관측할 수 있게 한다.
4. `classify`의 `InstructorRetryException` 원인을 규명해 (구조화 출력 스키마/instructor 설정 결함이면) 수정하거나, (일시 API면) 근거와 함께 분리 보고한다.

## 3. 루트커즈 선행 (구현 전 실측 의무)

- 삼주 콘텐츠 경로에서 **어느 프롬프트/슬롯이 금칙 토큰을 유도하는지**를 mock/no-LLM 구조 프로브로 재현한다(실 API 금지). 소비처:
  `sajugen/content/llm_sections.py`(compose 시스템 프롬프트·슬롯), `sajugen/content/rules.py`(삼주 골격), `sajugen/content/report_context.py`(ReportContext·fact allowlist), `sajugen/content/unknown_time_policy.py`(허용 출처·provenance).
- factcheck/safe/style 가드(`sajugen/content/factcheck.py`, `delivery_quality.py`, style lint)는 **완화·예외 추가 금지**. 문제는 생성 측이다.
- `delivery_quality._required_axes`/`_axis_evidence_hits`가 요구하는 축을 룰 폴백 골격이 어떻게 충족/미충족하는지 실측으로 확정한다.

## 4. 계약

- 프롬프트·슬롯·allowlist 수정은 삼주(`three_pillar`) 경로에 한정하고 known-time 4주/자미 문맥·골든은 **바이트/골든 비악화**한다.
- 폴백 골격 보강은 factcheck 하드 차단(사실 슬롯 밖 사실 생성 금지, 절대규칙 13)과 §12 안전표현을 우회하지 않는다.
- 관측 영속은 PII 0(호출 수·토큰 수·고정 ID만). 생년월일·질문 원문·후보 원시값을 영속하지 않는다.
- 게이트 키(`GATE_KEYS`) 제거·완화·기준 하향 금지(비악화).

## 5. 필수 양방·경계 테스트 (합성, PII 0)

1. 삼주 LLM 슬롯/프롬프트 입력에 시주·미승격 월주 간지·자미·후보 원시값이 **구조적으로 부재**(mock 캡처로 증명) + known-time 경로는 4주/자미 문맥 유지.
2. 삼주 챕터 mock LLM 출력에 금칙 토큰 주입 시 factcheck 차단 유지(차단측), 허용 출처만 쓴 정상 출력은 통과(통과측).
3. 룰 폴백 골격이 다축 고민(직업+경제+건강+월별+이사+취미 계열 합성 concern)에서 `_required_axes` 전 축 evidence 충족 + `style_clean` 통과(폴백 단독 gate 통과 최소 보장).
4. `run_generation` 오류 경로에서 `llm_usage`가 audit/render_meta에 영속됨(생성 강제 실패 주입 → usage 필드 존재 단언). 성공 경로 usage 영속 비악화.
5. (classify 규명이 스키마 결함으로 판명 시) 구조화 출력 파싱 회귀 양방.
6. 경계 인접: 축 트리거 term 경계(고민에 축 term 1개만/없음), 폴백/정상 혼합 챕터, 금칙 토큰 부분 일치(`사주`의 정상 용법 vs `사주팔자`/`시주` 금칙) 오탐 0.

## 6. 검증·완료 기준

- 전체: `.\.venv\Scripts\python.exe -m pytest tests\ -q` exit 0. 기준선 = **Claude 기준환경 1036 passed / 4 skipped**(passed 감소=회귀) + 신규 테스트 증가.
- 골든: `-k golden` = 기존 28 passed 유지. calc/input 변경이 없어야 정상(있으면 골든 전수 재검증 동반).
- 변경 Python 전부 Ruff·py_compile GREEN, `git diff --check` exit 0.
- **실모델 증거 분리(Codex LLM 금지)**: Codex는 no-LLM/mock 층 회귀로 "금칙 토큰 구조적 억제 + 폴백 축 충족 + usage 영속"을 증명한다. 실LLM-on 삼주 `integrated_full` × 실복합 고민의 `gate_pass=True` 재측정은 **운영자 승인 유료 재run(운영자/Claude 환경)** 몫이며 이 CODE_PASS에 포함하지 않는다.
- 완료 시 `implementation-notes.md`·`sajugen/STATE.md` 갱신, manifest를 `review_requested/next_actor=claude`로 기록. commit/push는 운영자 별도 승인 전 금지.

## 7. 예상 수정 범위

- 생성/근거: `sajugen/content/llm_sections.py`, `sajugen/content/rules.py`, `sajugen/content/report_context.py`, `sajugen/content/unknown_time_policy.py`
- 관측: `sajugen/order_flow.py`(run_generation 오류 경로 usage 영속)
- (classify 결함 시) 질문 분류 구조화 출력 경로
- 테스트: 관련 기존 + 삼주 근거화/폴백/usage 신규
- 문서: `docs/16-quality-incident-ledger.md`(QI-2026-07-13-02 재발방지 액션 추적)
- **금지/불변**: `sajugen/render/verify.py` 게이트 완화, factcheck/safe/style 가드 완화, known-time 4주/자미 문맥·골든, `harness/profiles/local/**`, 실고객 DB.

## 8. 후속 순서

1. (운영자) 이 패킷 승인 → manifest `packet_path`+SHA 고정, `planned/next_actor=codex`.
2. Codex 루트커즈(§3) 실측 → 구현(§2·§4) → 양방 테스트(§5) → 증거 보고(§6, no-LLM/mock 층).
3. Claude 신선 컨텍스트 교차리뷰(diff 전량 + 기준환경 pytest + 게이트 비악화).
4. PASS 뒤 **운영자 승인 유료 재run 1회**로 실모델 gate_pass 재측정(신규 order `DOC_1F3817DC9C`는 NORMALIZED+모듈확정 상태 = create 없이 `run_generation` 재호출 = 여전히 1건). 통과 시 표준 게이트→hrun→hsweep(과금 선보고)→300dpi 육안→운영자 전문 검수 Z=0 뒤에만 APPROVED/수동 발송.
