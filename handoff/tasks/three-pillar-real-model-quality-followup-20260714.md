# TASK_PACKET — 삼주 실모델 품질 후속(프롬프트 억제 강화·ganzhi 조사·표지 제목 개행)

- task_id: `three-pillar-real-model-quality-followup-20260714`
- base_commit: 활성화 시점 feat HEAD (실측 — 운영자가 manifest SHA로 고정)
- 구현자: Codex
- 검증자: Claude 교차리뷰 (+ 실모델 재측정 증거는 운영자 승인 유료 재run 몫)
- 상태: `draft`(미활성 — manifest 미고정. 운영자 승인 후 `planned/next_actor=codex`로 전환)
- 근거: `docs/16` QI-2026-07-13-02 검증(2026-07-14 유료 재run)에서 실측된 실모델 거동·육안 nit

## 0. 우선순위·금지 경계

- 이 패킷은 게이트/가드 통과가 이미 확인된(gate_pass=True) 뒤의 **품질 개선**이다. 게이트·가드 완화가 아니라 생성 측 억제 강화와 문안 품질이 목표다.
- Codex 상시 금지(구현 승인 뒤에도): PDF 재생성, LLM/Anthropic API 호출, git commit, push, deploy.
- 데이터 경계: `.env`·secret·실고객 데이터·`harness/profiles/local/**`·ignored 산출물 비열람. 합성 입력만. 이름·생년월일·질문 원문 비기록.
- 검색 시 `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'` 적용. 모든 Python은 `.\.venv\Scripts\python.exe -m ...`.

## 1. 배경 (실측 — 2026-07-14 유료 재run, 합성·PII 0)

승인 유료 재run 1회(합성 9축 복합 고민 × 삼주 `integrated_full` × `[job,wealth,health]`)에서 `gate_pass=True`(사고 해소 확정). 그러나 실모델 거동에 개선 여지가 관측됐다:

- compose 9챕터 중 **4개(intro·nature·flow·consult)가 룰 폴백**. 실 Sonnet-4.6이 여전히 스스로 생성 → 가드 차단(유출 0) → 폴백:
  - `시주`(금칙 삼주 토큰): nature·consult
  - 맨몸 월표기 `7월`/`12월`(간지월·절기 형식 아님): flow·consult
  - §12/메타 표현 `운명이 정해졌`·`이 풀이는`·`이 풀이에서`: intro
- 300dpi 육안 nit(게이트 무관):
  - 표지 h1 긴 제목이 `관|계` 음절 중간에서 개행(라운드23 `.cover .sub` keep-all 적용 밖).
  - 본문 조사 오류 `정축가`/`임신가` — 받침(축=ㄱ, 신=ㄴ) 뒤라 `정축이`/`임신이`가 맞음. ganzhi 삽입 골격이 조사 헬퍼(`_josa/_J`)를 안 탐(추정).

## 2. 목표 (관측 가능한 결과)

1. 삼주 compose 프롬프트(system override·temporal_anchor)를 강화해 실모델이 `시주`·맨몸 월표기·§12 메타를 **스스로 생성하는 빈도를 낮춘다** → 폴백률↓·LLM 산문↑. (가드는 그대로. 억제는 생성 측 프롬프트 품질로.)
2. ganzhi가 주어/목적어로 삽입되는 골격 문형에서 조사를 `_josa/_J` 헬퍼로 결정론 처리해 `정축가→정축이` 류 오류 0.
3. (advisory) 표지 h1 긴 제목의 음절 중간 개행 완화(keep-all 후보) — 조판 사안, 운영자 우선순위 판단.

## 3. 루트커즈 선행 (구현 전 실측 의무)

- 폴백 4챕터(intro·nature·flow·consult) 각각에서 **어느 프롬프트 문구가 어느 금칙 생성을 유도/미억제하는지** mock/no-LLM 구조 프로브로 특정. `sajugen/content/llm_sections.py`(system override·`temporal_anchor_block`·compose user), `report_context.py`.
- 조사 오류는 어느 골격 문형(`rules.py` 삼주 nature/frame 등)이 ganzhi 뒤 하드코딩 조사를 쓰는지 grep·프로브로 특정. `_josa/_J` 소비처 배선 확인.
- factcheck/safe/style 가드는 완화·예외 추가 금지. 문제는 생성 측·문형이다.

## 4. 계약

- 프롬프트 강화는 삼주 경로 한정. known-time 4주/자미 프롬프트 바이트·골든 비악화(`_COMPOSE_SYSTEM` SHA 핀 유지).
- 조사 헬퍼 적용은 문형 치환만. 사실 슬롯(간지 값) 변경 0, factcheck 하드 차단 우회 0.
- 게이트 키(`GATE_KEYS`) 제거·완화·기준 하향 금지(비악화). 폴백 골격의 축·style 충족 비악화.

## 5. 필수 양방·경계 테스트 (합성, PII 0)

1. 삼주 compose system/user 캡처에 강화된 억제 지시가 존재하고 known-time 바이트 불변(SHA 핀).
2. 조사: ganzhi 받침 유무 표 테스트(정축이·임신이·경오는·병오년은 등 대표 간지 × 주어/목적어) — 하드코딩 `가`/`은` 재발 0. mojibake·병기(`이(가)`) 노출 0.
3. 폴백 골격이 여전히 복합/단일/무축에서 축·style 충족(비악화, 기존 `test_three_pillar_fallback_axes` 유지).
4. (표지 keep-all 시) h1 긴 제목 개행 회귀(합성 긴 제목 실렌더 또는 HTML 층).

## 6. 검증·완료 기준

- 전체 `pytest tests\ -q` exit 0(기준선 비감소 + 신규). 골든 유지. 변경 Python Ruff·py_compile·diff-check GREEN.
- **실모델 증거 분리(Codex LLM 금지)**: Codex는 no-LLM/mock 층으로 "억제 지시 존재·조사 결정론·known 비악화"를 증명. 실모델 폴백률 감소(예: 4챕터→N)와 조사 육안 개선은 **운영자 승인 유료 재run(운영자/Claude 환경)** 몫이며 CODE_PASS에 미포함.
- 완료 시 `implementation-notes.md`·`STATE.md`·`docs/16` 갱신. commit/push는 운영자 승인 전 금지.

## 7. 예상 수정 범위

- 생성 억제: `sajugen/content/llm_sections.py`(삼주 system override·temporal_anchor 강화), 필요 시 `report_context.py`.
- 조사: `sajugen/content/rules.py`(삼주 골격 문형 → `_josa/_J` 헬퍼 배선). calc/input 무변경.
- (표지) `sajugen/render/report.html.j2` 또는 관련 CSS(h1 keep-all) — advisory.
- 테스트: 관련 기존 + 억제/조사/keep-all 신규.
- 금지/불변: `render/verify.py` 게이트 완화, factcheck/safe/style 가드 완화, known-time 4주/자미·골든, `harness/profiles/local/**`.

## 8. 후속 순서

1. (운영자) 승인 → manifest 고정, `planned/next_actor=codex`.
2. Codex 루트커즈(§3) → 구현(§2·§4) → 양방 테스트(§5) → 증거 보고(§6, no-LLM/mock 층).
3. Claude 교차리뷰(diff 전량 + 기준환경 pytest + 게이트 비악화).
4. PASS 뒤 운영자 승인 유료 재run으로 폴백률 감소·조사 개선 재측정. 통과 시 표준 게이트→검수 Z=0 뒤에만 발송.
