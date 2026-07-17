# TASK_PACKET — 재시도 피드백 형식교정형 전환 (temporal 폴백 비용중립 감소)

- task_id: `temporal-retry-format-feedback-20260717`
- base_commit: 활성화 시점 HEAD `0c93f98`(운영자가 manifest SHA로 고정)
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰
- 상태: `planned`(활성 시 manifest가 `packet_path`+SHA로 고정, `next_actor=codex`)
- 로드맵: `말투 개편 단계형 로드맵` Stage 1 항목 **1a**(최우선·비용중립·최저위험)

## 0. 역할·금지 경계 (YOU MUST)

- Codex 상시 금지(구현 승인 뒤에도): PDF 재생성, LLM/Anthropic API 호출, git commit, push, deploy.
- 데이터 경계: `.env`·secret·실고객 데이터·`harness/profiles/local/**`·ignored 산출물 비열람. 합성 입력만·PII 0.
- 검색은 ignored 제외 글롭 필수: `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`.
- 모든 실행은 `.\.venv\Scripts\python.exe -m ...`. 계산(`sajugen/calc/**`·`input/**`) 무변경.

## 1. 배경 (실측 — 코드 대조 확인, 2026-07-17)

개인 리포트(integrated_full) 실 LLM-on 생성인데도 여러 챕터(intro·love·flow·consult 등)가 룰 골격으로
폴백되어 산출물이 템플릿틱("AI틱")하게 읽힌다. 폴백 최대 유발원은 **temporal 맨몸월/bare 간지월**이다.

- 실 Sonnet이 시간 흐름 챕터에서 "신사월", "7월" 같은 표기를 종종 생성 → `temporal_lint`가 정확히 차단 →
  가드 실패 → 재시도 → (재시도도 실패하면) 룰 골격 폴백.
- **핵심 결함**: 재시도 피드백이 **오되먹임**이다. `builder.py:159-163` `_retry_feedback_labels`의 known-time
  분기가 위반 dict에서 raw `match`("신사월")만 뽑아 `_fb`로 넘기고, `llm_sections.py:681-685`가 이를
  `"직전 초안이 다음 표현 때문에 반려됐다: {feedback}. 이 단어·표현과 그 변형을 쓰지 말고 다시 써라"`로 감싼다.
  즉 모델에게 **"신사월을 쓰지 마라"**고 지시한다.
- 그러나 모델은 그 간지월을 **반드시 말하되 형식만** "신사월(입하 - 양력 5/5~6/5)"로 써야 한다. 그 정답
  형식 문자열은 이미 (a) 골격 `_worun_label`(`rules.py:349-364`)이 결정론 생성하고, (b) `temporal_lint`가
  반환하는 위반 dict의 `why` 필드가 "간지월(절기명 - 양력 M/D~M/D) 또는 음력 n월 무렵으로 표기"라는 정답
  형식을 담고 있다(`temporal_lint.py:140,148`).
- 피드백을 "토큰 회피"에서 "형식 교정"으로 재프레이밍하면 재시도 성공률↑ → 폴백↓. **호출 수 불변 =
  비용중립**(피드백은 재시도(attempt≥2) 프롬프트 내부값이라 첫 호출 캐시 prefix 무변경).

## 2. 목표 (관측 가능한 결과)

재시도 피드백을 **위반 타입별 두 모드**로 분기한다:
1. **형식교정형** — temporal 계열 위반(`type` ∈ `{month_notation, temporal, relative_month_boundary}`)은
   raw 토큰 대신 그 위반의 `why`(정답 형식 내장)를 전달하고, 프롬프트에 "이 표현을 올바른 형식으로 **고쳐**
   다시 써라"로 주입한다.
2. **토큰회피형(현행 유지)** — 그 외 위반(safe_lint 단정, factcheck 근거밖 간지, style, 등)은 기존대로 raw
   match를 "이 단어·표현을 **쓰지 말고** 다시 써라"로 주입한다.

결과: 맨몸월/간지월 재시도가 정답 형식으로 교정돼 temporal clean 통과 → 폴백 회피. 진짜 금칙 토큰은 여전히
회피형으로 차단(완화 0).

## 3. 스코프 경계 (반드시 지킬 것)

- **known-time 분기만** 수정한다. `_retry_feedback_labels`의 `three_pillar=True` 분기(삼주)는 **불변** —
  삼주가 raw 토큰을 되먹이지 않는 보호(고정 라벨만)를 유지한다. 다만 반환 타입 변경(§4)에 맞춰 삼주도 새
  반환 형태로 감싼다(값·의미 동일: 모든 라벨은 "회피/일반" 버킷, `why` 누출 0).
- `temporal_lint.py`·`factcheck.py`·`safe_lint.py`·`style_lint.py` **로직 무변경**(가드 완화 0). 이 패킷은
  가드가 반환하는 기존 `why`/`type`을 **소비만** 한다.
- `render/verify.py` GATE_KEYS·게이트 로직 무관·무변경. calc/input 무변경.
- 피드백은 재시도 경로 전용(첫 호출 프롬프트·캐시 prefix 불변) — 비용중립 유지.

## 4. 접근 (설계 — 구현 세부는 Codex 재량, 계약은 아래)

- `builder.py:146-173` `_retry_feedback_labels` 반환 타입을 `set[str]` → **`tuple[set[str], set[str]]` =
  (avoid, fix)**로 변경.
  - known-time: 위반 `type`이 `{month_notation, temporal, relative_month_boundary}`이고 `why`가 있으면 그
    `why`를 **fix**에, 그 외는 raw `match`/`token`/`rule`을 **avoid**에.
  - three_pillar: 기존 고정 라벨을 **avoid**에(fix는 빈 set), raw 토큰·`why` 누출 0.
- `builder.py` 재시도 루프(`~570-639`): `_fb_pool` 단일 set → **두 누적자**(avoid/fix). 실패 라운드 누적
  (`~635`)도 동일 분기. 각각 `sorted[:8]`/`sorted[:6]`로 join → `_compose_one`에 전달.
- `builder.py:425-449` `_compose_one` 시그니처에 `feedback_fix: str | None = None` 추가, `compose_kwargs`에
  기존 파라미터와 동일 패턴(`accepts_kwargs or "feedback_fix" in compose_params` 가드)으로 전달.
- `llm_sections.py` `compose(...)` 시그니처에 `feedback_fix: str | None = None` 추가. `681-685` 기존
  `feedback`(회피) 블록은 유지하고, 그 뒤에 `feedback_fix` 블록 신설:
  `"\n[재작성 사유 — 형식 교정. 다음 지적대로 표현을 올바른 형식으로 고쳐 다시 써라]\n{feedback_fix}\n"`.
  두 블록은 공존 가능(한 라운드에 회피+교정 동시).

## 5. 필수 양방·비-no-op 테스트 (합성, PII 0)

1. **형식교정 프롬프트(비-no-op)**: `test_temporal_month.py`의 기존
   `test_compose_prompt_carries_month_anchor_and_feedback`(69행) 패턴 확장 — `feedback_fix`에 month_notation
   `why`를 넣고 compose 프롬프트를 만들면 "형식 교정 … 고쳐 다시 써라" 블록에 정답 형식 토큰
   (예: `간지월(절기명 - 양력`)이 나타나고, **"쓰지 말고" 회피 블록에는 안 나타남**을 단언.
2. **`_retry_feedback_labels` 분기(양방)**:
   - month_notation 위반 dict(`{"type":"month_notation","match":"신사월","why":"…간지월(절기명…"}`) → `why`가
     **fix**에, `"신사월"`은 **avoid에 없음**(비-no-op: "신사월 쓰지 마"가 아님을 증명).
   - safe/style 위반(`type` 없음, `{"match":"반드시 …됩니다"}`) → **avoid**에, fix에 없음(회귀: 회피형 유지).
   - factcheck 근거밖 간지(`{"token":"경술"}`) → **avoid**(여전히 "쓰지 마").
   - three_pillar=True → 고정 라벨만 avoid, raw 토큰·`why` 누출 0(삼주 보호 회귀).
3. 기준선 비악화: 전체 `pytest tests\ -q` exit 0·**1110 passed / 4 skipped 비감소**+신규, golden 28.

## 6. 검증·완료 기준

- 전체 `.\.venv\Scripts\python.exe -m pytest tests\ -q` exit 0(기준선 **1110/4** 비감소). golden 28.
  변경 Python Ruff `All checks passed!`·py_compile·`git diff --check` exit 0. calc/input diff 0.
- 실모델 폴백률 감소(맨몸월/간지월 재시도 교정 통과)는 **운영자 승인 유료 재run 몫이며 CODE_PASS에 미포함**.
  CODE_PASS의 핵심 = "형식교정 피드백이 정답 형식을 전달하고 회피형과 정확히 분기됨"의 결정론 실증.
- 완료 시 `implementation-notes.md`·`STATE.md` 갱신. commit/push는 운영자 승인 전 금지.

## 7. 예상 수정 범위

- `sajugen/content/builder.py`(`_retry_feedback_labels`·재시도 루프 두 누적자·`_compose_one` +feedback_fix).
- `sajugen/content/llm_sections.py`(`compose` +feedback_fix + 형식교정 주입 블록).
- 테스트: `tests/test_temporal_month.py` 확장 + (권장) `_retry_feedback_labels` 단위 신규.
- 금지/불변: `temporal_lint.py`·factcheck/safe/style 로직, calc/input, verify GATE_KEYS, golden, known-time
  4주/자미 계산, three_pillar 피드백 보호.

## 8. 후속 순서

1. (운영자) 승인 → 패킷 commit + manifest 고정(`planned/next_actor=codex`).
2. Codex 구현(§2·§4) → 양방 테스트(§5) → 증거 보고(§6, no-LLM/mock 층).
3. Claude 교차리뷰(diff 전량 + 기준환경 pytest 1110/4 비악화 + 분기 정확성 실증 + 가드/게이트 비악화).
4. PASS 뒤 로드맵 다음 항목(S0 자미 정본 승인 → 1e/1d → 1c → 1b), Stage 1 완료 시 운영자 승인 유료 재측정.
