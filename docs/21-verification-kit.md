# 21. 다층 검증 키트 (vkit) — 이식 규격

> 범용 "운영자보다 먼저 버그를 잡는" 검증 시스템을 타 프로젝트에 이식하는 규격. 이 규격 자체는
> Phase 5 설계 논쟁 프로토콜을 1회 통과해 확정됐다(handoff/kit/design-debate-vkit-distribution.md
> — sg-design-critic 적대 비평 반영). 배포 = **복사-적응 + 출처 스탬프 벤더링**(안 B 공유패키지·
> 안 C 생성기 기각: 하드게이트 결정론·무의존 불변 위반). 하이브리드(D-4): 전역 /vkit 스킬(스캐폴딩)
> + 저장소 정본 handoff/kit/(복사 원본).

## 5개 층 (L0~L4)
| 층 | 이름 | 내용 | sajugen 구현(참조 정본) |
|---|---|---|---|
| **L0** | 스펙 + 재현 실패 테스트 선행 | RED-first: 결함/요구를 재현하는 실패 테스트를 먼저 쓰고 GREEN 으로 닫는다. 말미 종단 검증 필수(테스트 통과 ≠ 동작 확인). | Phase 1 RED 실측, /verify |
| **L1** | 결정론 하드 게이트 | GATE_KEYS SSOT 상수 + gate_pass=all(키) 순수 · 요약↔원천 정합 계약(수동 목록 복제 금지) · 골격×lint 매트릭스(도메인별). LLM 판정 편입 금지. | verify.GATE_KEYS, test_gate_contract, test_gate_registry, test_skeleton_lint_matrix |
| **L2** | 이질 렌즈 스윕(advisory) | 발굴(이질 렌즈)→반박≤1→루브릭 judge(렌즈≠judge 모델·순서 스왑)→사람. 백엔드 주입, PII fail-closed, 비용 상한, 게이트 무접촉. | scripts/hsweep.py, harness/prompts/sweep/ |
| **L3** | 구조 검사 | dead-param 정적 스캐너(stdlib AST) · 프록시 레지스트리(물리/프록시 분류) · 커버리지 매트릭스 · property(hypothesis 무크래시·결정론). | deadparam_scan.py, docs/20, test_lint_properties |
| **L4** | 사람 육안 | 자동이 못 재는 미감·물리 배치. 다이어트 체크리스트 **≤7항목**(경고 다이어트). | handoff/templates/pdf_review_report.md |

## 배포 메커니즘 (확정 = 복사-적응 + 스탬프 벤더링)
- 정본은 `handoff/kit/`(이 저장소). 채택처는 파일을 **복사**하되 `handoff/kit/manifest.json`에
  upstream 저장소·SHA·복사일을 스탬프한다.
- **비차단 drift-check**(권고): 채택처 CI 가 상류 정본과 diff 나면 **경고만**(하드게이트 결정론은
  건드리지 않는다). 전파는 사람이 판단해 재복사.
- 안 B(pip 패키지) 금지 이유: 외부 패키지 버전이 결정론 하드게이트를 인질로 잡는다(Phase 2 에서
  ruff 대신 stdlib 자작을 택한 바로 그 불변). 안 C(생성기) 금지 이유: 생성기 자체가 게이트로
  검증되지 않는 미검증 메타코드 + 껍데기 게이트(no-op) 양산.

## 측정된 이식 경계 (critic 지적 — "그대로 복사"의 실제 범위)
"도메인 무관 = 그대로 복사"는 sajugen 리터럴 때문에 부분적으로만 참이다. 채택 전 아래를 치환한다.
| 아티팩트 | 이식 등급 | 치환/적응 필요 |
|---|---|---|
| handoff/templates/design_debate.md | 거의 그대로 | 트리거 체크리스트의 도메인 문자열(GATE_KEYS·발송 상태머신)을 채택 도메인으로 |
| .claude/skills/{done,adjacent,audit} | 거의 그대로 | /audit 의 mutation 대상 파일 경로, /done 의 venv python 경로 |
| scripts/deadparam_scan.py | 적응 | `_EXCLUDE_SUBPATHS`(sajugen 경로 리터럴)·기본 `paths`·`ROOT` 가정 치환 |
| L1 게이트 계약 테스트(test_gate_contract/registry) | 패턴만 | GATE_KEYS 집합·`>=20` floor 는 도메인 키 수로 재도출(하드코딩 금지) |
| 골격×lint 매트릭스 | 재작성 | 도메인 골격 빌더·lint 모듈 import 는 전면 도메인 특화 |
| L2 hsweep 렌즈 프롬프트 | 재작성 | 렌즈 5종(육안 결함 부류)은 도메인별로 새로 정의 |
| **L2 PII 마스킹 룰** | **재정의 필수** | sajugen=생년월일·이름·출생지 / crypto=지갑주소·API키·시크릿. 복사 시 **탐지 no-op** |

## 채택 안전장치 (critic 이 드러낸 4대 no-op·착시 차단 — 채택 체크리스트)
1. [ ] **no-op 자가검증**: 이식한 게이트가 채택처 CI 에 **실제 배선**됐고, 각 게이트에 "결함 주입→
   차단" **양방 회귀**가 존재한다(없으면 "이식했으나 안 도는" 팬텀 파라미터의 메타 재현).
2. [ ] **PII 형상 재정의**: L2/마스킹 PII 룰을 채택 도메인 형상으로 재정의하고, 도메인 PII 를 주입한
   합성 입력이 실제로 차단됨을 테스트("탐지 존재=보호됨" 착시 금지).
3. [ ] **이질성 검증**: L2 생성 세션 실모델 ≠ 비평/judge 모델을 채택처 config 로 확인(단일 모델이면
   이질 렌즈가 자기토론=다수결로 조용히 퇴화).
4. [ ] **도메인 리터럴 치환**: 위 경계표의 sajugen 경로·매직넘버를 전부 치환(미치환 시 오탐 또는 미탐).

## /vkit 스캐폴딩 (하이브리드 D-4)
- 정본 = 이 저장소 `handoff/kit/`. 전역 스킬 `/vkit`(스캐폴딩)은 채택처에 kit 을 복사 + manifest 스탬프
  + 위 4 안전장치 체크리스트를 채택처에 찍고 **no-op 자가검증 골격**을 생성한다.
- 현재 `/vkit`은 이 저장소 `.claude/skills/vkit/`에 정의(추적·테스트 가능). 크로스 프로젝트로 쓰려면
  운영자가 `~/.claude/skills/vkit/`로 승격(전역화 = 시스템 변경이라 운영자 조치).

## crypto-signal 드라이런 (이식 검증 — 비파괴, 계획만)
crypto-signal(암호화폐 신호 서비스)에 vkit 을 적용하면:
- L1 GATE_KEYS: sajugen 의 "발송 차단 기준"(텍스트레이어·게이트 20키) 대신 신호 발행 게이트
  (백테스트 통과·데이터 신선도·거래소 응답 정합 등)로 **재정의**. `>=20` floor 는 그 키 수로 재도출.
- L2 렌즈: "직답 만족도·명리-자미 통합감" 대신 도메인 결함(신호 근거 설명 부실·과최적화 티·리스크
  고지 누락)으로 렌즈 **재작성**.
- **L2 PII: 생년월일 마스킹 룰 폐기 → 지갑주소·API키·시크릿·거래소 계정 마스킹으로 재정의**(형상 불일치
  가 최대 위험 — critic 치명 리스크 ②). 미재정의 시 crypto PII 를 구조적으로 못 봐 "보호됨" 착시.
- L3 deadparam_scan: 경로 리터럴을 crypto-signal 트리로 치환하면 stdlib 라 그대로 동작.
- 실제 crypto-signal 저장소는 이 세션에서 수정하지 않는다(별개 repo — 운영자 승인 후 vkit 스캐폴딩).
