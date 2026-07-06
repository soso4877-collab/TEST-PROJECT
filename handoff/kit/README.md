# handoff/kit — 다층 검증 키트 (vkit) 정본

이 디렉터리는 "운영자보다 먼저 버그를 잡는" 다층 검증 시스템의 **이식용 정본**이다. 규격 전문은
`docs/21-verification-kit.md`. 배포 = 복사-적응 + 출처 스탬프 벤더링(Phase 5 논쟁으로 확정 —
handoff/kit/design-debate-vkit-distribution.md).

## 채택 절차 (요약 — 상세는 docs/21)
1. `manifest.template.json`을 채택처 `handoff/kit/manifest.json`으로 복사하고 upstream 저장소·SHA·
   복사일을 스탬프한다(drift-check 근거).
2. docs/21 "측정된 이식 경계표"를 보고 각 아티팩트를 복사(거의 그대로) 또는 적응/재작성한다.
3. docs/21 "채택 안전장치 4대" 체크리스트를 **전부** 통과해야 이식 완료다:
   - no-op 자가검증(게이트 CI 배선 + 결함주입→차단 양방 회귀 존재)
   - PII 형상 재정의(도메인 PII 주입이 실제 차단됨을 테스트)
   - 이질성 검증(생성 모델 ≠ 비평/judge 모델)
   - 도메인 리터럴 치환(경로·매직넘버)
4. `/vkit` 스킬이 위를 스캐폴딩한다(전역화는 운영자가 ~/.claude/skills/vkit/로 승격).

## 정본 아티팩트 경로 (이 저장소 기준 — 복사 원본)
- L1: `sajugen/render/verify.py`(GATE_KEYS 패턴)·`tests/test_gate_contract.py`·`tests/test_gate_registry.py`·`docs/20-gate-coverage.md`
- L2: `scripts/hsweep.py`·`harness/prompts/sweep/lens_*.md`
- L3: `scripts/deadparam_scan.py`·`tests/test_deadparam_scan.py`·`tests/test_lint_properties.py`
- 프로토콜/스킬: `handoff/templates/design_debate.md`·`.claude/agents/sg-design-critic.md`·`.claude/skills/{audit,adjacent,done}/`
- L4: `handoff/templates/pdf_review_report.md`(≤7항목 다이어트 체크리스트 패턴)

## 불변 (채택처에서도 유지)
- 하드게이트는 결정론·무의존(외부 패키지 의존 금지 — 그래서 pip 배포가 아니라 복사-벤더링).
- L2 LLM 판정은 advisory 전용(게이트 AND 체인 편입 금지). API 호출은 운영자 승인 후.
- 이식은 "복사했다"가 아니라 "no-op 자가검증 4대 통과"로 완료된다(팬텀 메타 재현 차단).
