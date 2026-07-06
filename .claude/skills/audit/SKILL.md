---
name: audit
description: sajugen 월 감사 표준 지시문. 회의적 재검증(문서가 보장하는 규칙이 코드 프로브로 증명되는가) + 문서-코드 대조 + docs/16 포스트모템 리뷰(직전 달 QI 재발방지가 코드/테스트로 닫혔는지 전수) + mutation testing(verify.py·temporal_lint.py). 매달 1회 또는 대형 변경 후 사용.
user-invocable: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(./.venv/Scripts/python.exe *)
  - Bash(git log *)
  - Bash(git diff *)
  - Bash(git rev-parse *)
---

# /audit — 월 감사 (회의적 재검증)

**근거**: 2026-07-03 전수 감사에서 문서-코드 불일치 6건 적발(day_offset 미배선·KASI 교차
미구현·절입 ±2분 플래그 문서만 등 — 문서가 보장한 규칙을 코드가 안 하고 있었다). 문서는
강제력이 없다. 이 감사는 **문서가 보장하는 것을 코드 프로브로 증명**하고, 지난 사고의 재발방지가
실제로 닫혔는지 전수 확인한다. 무비난 포스트모템(Google SRE) — 사람이 아니라 시스템의 구멍을 본다.

## 1. 회의적 재검증 (문서 보장 ↔ 코드 프로브)
문서(절대규칙·docs/03 결정표·docs/20 게이트 레지스트리)가 "보장한다"고 쓴 규칙마다, 그것이
실제 코드 경로에서 작동함을 **재현 프로브**로 증명한다. 증명 못 하면 "미검증"으로 분리 보고.
- 정책 enum/플래그(자시·윤달·사화표·GATE_KEYS)가 **소비처까지 배선**됐는가 → 분기 프로브.
  (day_offset·verify spec·product 3연속 팬텀 사례 — 만들었으나 안 쓰던 것.)
- 계산 골든이 독립 오라클로 대조되는가(속성 재도출) — `pytest -k golden` 실측.
- 정적 스캐너 게이트 GREEN 확인: `./.venv/Scripts/python.exe scripts/deadparam_scan.py`(dead-param 0),
  `pytest tests/test_gate_registry.py tests/test_skeleton_lint_matrix.py`(커버리지·골격 동기화).

## 2. 문서-코드 대조
- docs/20 GATE_KEYS 레지스트리 == live `verify.GATE_KEYS`(test_gate_registry 가 강제하나 육안 재확인).
- .claude/rules/00-immutable.md 의 각 절대규칙이 코드/테스트로 강제되는 지점을 1개씩 지목
  (강제 지점이 없는 규칙 = 문서만의 규칙 = 리스크).
- STATE.md 의 "완료" 주장이 커밋 SHA + 테스트 출력으로 뒷받침되는가(증거 없는 완료 색출).

## 3. 포스트모템 리뷰 (docs/16 전수)
직전 달 QI 항목마다 "재발방지 액션"이 **코드/테스트로 닫혔는지** 확인한다. 리뷰되지 않은
포스트모템은 없는 것과 같다(Google SRE). 각 QI 에 대해:
- 재발방지가 테스트로 고정됐는가(어느 테스트?) — 없으면 "열린 사고"로 표시.
- 같은 클래스의 인접 결함이 남았는가(/adjacent 병행).
- 추적 대기 항목(예: QI-2026-07-06-01 age 팬텀 체인 제거)이 진행됐는가.

## 4. Mutation testing (감지 시스템의 실효성)
게이트/가드가 **실제로 결함을 잡는지**를 코드에 변이를 주입해 확인한다(테스트가 통과만 하고
아무것도 안 잡는 no-op 색출). 대상 = 감지 핵심: `sajugen/render/verify.py`·
`sajugen/content/temporal_lint.py`.
- 도구 미설치 시 온디맨드: `./.venv/Scripts/python.exe -m pip install cosmic-ray`(또는 mutmut).
- 실행 후 **생존 변이(survived mutants)** = 그 변이를 잡는 테스트가 없다는 뜻 → 양방 테스트 보강.
- 비용/시간이 크면 함수 단위로 좁혀 실행(변경이 있었던 함수 우선).

## 산출
- `handoff/reports/audit-<YYYY-MM>/` 에 (a) 문서-코드 불일치 목록, (b) 열린 포스트모템,
  (c) 생존 변이, (d) 인접 사각을 기록. 각 항목에 후속 액션 + 담당(사람/에이전트) 지정.
- 새로 발견한 사고는 docs/16 에 QI 로 등재(증상/영향/원인 2층/재발방지).
- PII 0(합성 프로브만) — 실고객 데이터·본문 전문 비인용.

## 규율
- 실측 우선("아마" 금지). 확인 못 한 것은 "미검증"으로 정직하게 분리.
- 감사는 코드를 고치지 않는다(발견·기록·후속 지정). 수정은 별도 작업 단위(양방 테스트 동반).
