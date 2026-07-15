# TASK_PACKET — 서양 점성술(별자리) off-domain 하드 가드 + 억제

- task_id: `offdomain-zodiac-guard-20260715`
- base_commit: 활성화 시점 feat HEAD (운영자가 manifest SHA로 고정)
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰
- 상태: `planned`(활성 시 manifest가 `packet_path`+SHA로 고정, `next_actor=codex`)
- 근거: 4모듈 LLM-on 유료 확인(2026-07-15)에서 closing이 서양 별자리 생성 + 유출 위험 프로브 실측

## 0. 역할·금지 경계 (YOU MUST)

- Codex 상시 금지(구현 승인 뒤에도): PDF 재생성, LLM/Anthropic API 호출, git commit, push, deploy.
- 데이터 경계: `.env`·secret·실고객 데이터·`harness/profiles/local/**`·ignored 산출물 비열람. 합성 입력만·PII 0.
- 검색은 ignored 제외 글롭 필수: `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`.
- 모든 실행은 `.\.venv\Scripts\python.exe -m ...`. 계산(`sajugen/calc/**`·`input/**`) 무변경.

## 1. 배경 (실측 — 2026-07-15, 합성·PII 0)

- 4모듈 LLM-on 유료 확인 1회에서 **closing 챕터가 서양 점성술을 생성**: 쌍둥이자리/게자리/사자자리 + 양력 날짜 구간(황도 12궁). `gate_pass=True`였으나 그 인스턴스는 룰 폴백으로 처리됨(guard-fail safe=1).
- **전용 가드 부재 실측**: `sajugen/content/`에 별자리·황도·점성 관련 차단 문구 **0**(grep). factcheck 미검(fact=0). 그 인스턴스는 safe_lint가 **우연히** 잡았을 뿐 별자리 전용 룰이 아니다.
- **유출 위험 프로브(확정)**: 결과 보장·단정이 없는 '깨끗한' 별자리 문장 3종 —
  "당신은 사자자리 기질이 강한 분입니다." / "황도 12궁으로 보면 게자리에 가까운 성향입니다." /
  "태양 별자리는 쌍둥이자리에 속합니다." — 전부 **safe=0·style=0 = 전 가드 통과(유출)**.
- 결론: 서양 점성술 off-domain 서술은 현재 **신뢰할 수 있는 차단이 없어 변형 문구가 고객 PDF에 유출될 수 있다.** 이 상품은 명리(권위)+자미(12궁 영역) 전용이며 서양 점성술은 도메인 밖이다.

## 2. 목표 (관측 가능한 결과)

1. **전용 하드 가드**(1차·핵심): 서양 점성술 off-domain 토큰을 **fail-closed로 차단**하는 룰을 추가하고, 기존 3단 가드처럼 compose 가드 체인 + 최종 발급 게이트까지 배선한다. 어떤 문구 변형이든(보장·단정 여부와 무관) 별자리 서술이 **유출 0**이 되게 한다.
2. **프롬프트 억제**(2차): `_COMPOSE_SYSTEM`/closing compose guide에 서양 점성술 금지를 명시해 실 모델의 생성 빈도·폴백률을 낮춘다.

## 3. 루트커즈 선행 (구현 전 실측 의무)

- 유료 run에서 걸린 인스턴스가 **어느 safe_lint 패턴에 우연히** 매치됐는지 특정(전용 아님 확인). §1 프로브 3종을 재현해 현재 가드 통과를 RED 기준선으로 고정.
- 차단 대상 토큰 집합을 확정: **황도 12궁명 12종**(양자리·황소자리·쌍둥이자리·게자리·사자자리·처녀자리·천칭자리·전갈자리·사수자리/궁수자리·염소자리·물병자리·물고기자리) + `별자리`·`황도`·`점성`(술). 자미두수 문안이 `별자리`를 쓰지 않음을 실 골격으로 확인(쓰면 그 표현은 예외 처리).
- factcheck/safe/style 기존 룰은 완화·예외 추가 금지. 문제는 **미커버(신규 차단 필요)**다.

## 4. 계약

- 가드는 **사각 축소 방향만**(완화 0). 별자리 sign name 컴파운드 + 황도/점성만 매치하고, **명리/자미 정상어 오탐 0**:
  `관록궁 자리`·`자리를 잡다`(bare `자리`), `사자(獅子)`·`게`·`처녀`·`물고기` 등 단독 일상어, `주성`·`별`(자미 星)은 **차단 금지**. 컴파운드 sign name(`사자자리` 등)과 bare word를 구분한다.
- 가드 추가는 (정상 통과 + 별자리 차단) **양방 회귀 동반**(작업 규율 3). 게이트 키 추가 시 `GATE_KEYS`·docs/20 등록.
- 프롬프트 강화는 생성 측만. known-time/삼주 프롬프트 바이트 핀(`_COMPOSE_SYSTEM` SHA)이 있으면 갱신하고 그 근거를 notes에 남긴다.

## 5. 필수 양방·경계 테스트 (합성, PII 0)

1. **차단**: §1 프로브 3종 + 12궁명 각각 + `황도`·`점성술` → 신규 가드 hit(유출 0). 실제 compose 가드 체인·최종 게이트 경유(fake-doc 전용 아님).
2. **오탐 0(경계 인접)**: `관록궁 자리`·`자리를 잡다`·`사자(獅子)`·`게`·`처녀궁`·`물고기(오행 아님 일상)`·자미 `주성`/`별` → 가드 clean.
3. **프롬프트**: closing/compose system 캡처에 서양 점성술 금지 지시 존재. known 바이트 핀 비악화.
4. 기준선 비악화: 기존 게이트 구성·golden·delivery 판정 불변.

## 6. 검증·완료 기준

- 전체 `pytest tests\ -q` exit 0(기준선 **1071/4** 비감소 + 신규). golden 28. 변경 Python Ruff·py_compile·diff-check GREEN. calc/input diff 0.
- 실모델 폴백률 감소(closing 별자리 미생성)는 운영자 승인 유료 재run 몫이며 CODE_PASS에 미포함. **CODE_PASS의 핵심은 "별자리 유출 0"의 결정론 가드 실증**이다.
- 완료 시 `implementation-notes.md`·`STATE.md`·`docs/16`(QI: off-domain 미커버 2층) 갱신. commit/push는 운영자 승인 전 금지.

## 7. 예상 수정 범위

- 가드: `sajugen/content/`의 신규 또는 확장 lint(off-domain 서양 점성술) + `builder.py`·`gunghap.py`·`integrated.py` compose 가드 체인 배선 + `render/verify.py` 최종 게이트(게이트 키 추가 시 비악화).
- 프롬프트: `sajugen/content/llm_sections.py`(`_COMPOSE_SYSTEM`/closing guide).
- 문서: `docs/16` QI + (게이트 키 추가 시) `docs/20`.
- 테스트: 신규 양방·경계.
- 금지/불변: calc/input, factcheck/safe/style 기존 룰 완화, known-time 4주/자미·golden.

## 8. 후속 순서

1. (운영자) 승인 → manifest 고정, `planned/next_actor=codex`.
2. Codex 루트커즈(§3) → 구현(§2·§4) → 양방 테스트(§5) → 증거 보고(§6, no-LLM/mock 층).
3. Claude 교차리뷰(diff 전량 + 기준환경 pytest + 게이트 비악화 + 유출 0 실증).
4. PASS 뒤 운영자 승인 유료 재run으로 억제 효과(별자리 미생성) 재측정.
