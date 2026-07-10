# Q7 질문 영역 모듈 조합 설계안 — 승인 전 코드 0줄

## 목표와 불변 경계

`integrated_full._assemble_sections`의 현재 “개인 전체 + 관계 전체” 결합을, 운영자가 고른 `love | job | wealth | health | gunghap` 모듈의 결정론 조합으로 일반화한다. 계산 엔진·명리 우선권·safe_lint/factcheck/trace·APPROVED 전 발급 차단은 그대로 둔다. 모듈 선택은 계산 결과를 만들지 않고 이미 계산된 사실의 서술 범위만 정한다. 선택 목록은 정규 순서와 버전까지 저장해 같은 입력이 같은 섹션·게이트 하한을 만들게 한다.

## 권장 구조: 버전 있는 모듈 레지스트리

| 경계 | 소유 섹션/전제 | 조립 규칙 |
|---|---|---|
| `core`(항상) | `intro`, `wonguk`, `nature`, `frame`, `flow`, `ziwei`, `together` | 계산 사실과 시기·명리/자미 층위를 제공하되 영역 결론을 대신하지 않는다. |
| `love` | 기존 `love` + 해당 질문 근거 슬롯 | 연애 질문일 때만 포함한다. |
| `job` | 신규 `work_job` 제공자 | 현 `work`의 직업 문단을 재사용 가능한 제공자로 분리한다. |
| `wealth` | 신규 `work_wealth` 제공자 | 현 `work`의 재물 문단을 분리해 `job`과 독립 선택을 보장한다. |
| `health` | 기존 `health` | 건강 모듈만 선택해도 의료 단정 금지 가드를 그대로 적용한다. |
| `gunghap` | `relationship_*` 전부 | 2인 이상 입력 필수. 관계 모듈 내부 `relationship_consult` 직답 게이트를 유지한다. |
| `peak/tail`(항상) | 선택 모듈 전체를 묶는 `personal_consult`, `closing`, `appendix_terms`, `colophon` | `personal_consult`는 선택 영역마다 근거 1개 이상을 답하고, 관계 consult와 역할을 중복하지 않는다. |

최종 순서는 `core → love → job → wealth → health → gunghap → personal_consult → tail`로 고정한다.
**[정정 2026-07-10 — 1단계 패킷 v2가 우선]** 위 추상 순서는 현행 조립 순서(도입→영역→흐름→개인화 피크
consult→관계→마무리, `sections_schema.py:10` 의도된 독서 곡선)와 불일치해 폐기. 정규 순서 = 현행 순서의
필터링(재배열 없음) — `handoff/codex-q7-stage1.md` §2.3 참조. 미선택 모듈 섹션 유입, 중복 ID, 순서 역전은 조립 실패다. 현재 sparse 병합은 같은 모듈 안에서만 허용하고 모듈 경계를 넘는 병합은 금지한다.
**[정정 2026-07-10 — 1단계 패킷 v3가 우선]** 병합 경계 제한 폐기: 필터링이 병합보다 먼저라 비선택 유입은
구조적으로 불가, 현행 병합 로직 유지(하위호환). 커버리지 게이트는 병합 전 목록 기준 — `codex-q7-stage1.md` §2.3. `--module` 미지정은 하위호환을 위해 5개 전부를 선택해 현 `integrated_full`과 같은 의미를 유지한다.

## 분량·게이트 연동

선택 수 `N=1..5`에 대해 제안 하한은 `pages=min(30, 12+4N)`, `text_chars=min(10000, 1000+2000N)`이다. 따라서 1개는 16쪽/3000자(Q4 gunghap 하한과 정합), 5개는 30쪽/10000자(현 integrated_full 불변)다. 이 값은 `delivery_quality`의 단일 프로필 매핑에서 계산하고 `verify`에는 `selected_modules`와 산출 하한을 전달한다. 기존 `delivery_quality_clean` 안에 `missing_module_sections`, `unexpected_module_sections`, `module_coverage`, `module_length` 실패를 넣어 GATE_KEYS 우회 경로를 만들지 않는다. 각 모듈은 정상 통과·하한-1 차단·미선택 섹션 누출 차단을 같은 회귀에 둔다. `gunghap`은 1인 입력 차단/2인 통과, 전체 5개 기본값은 현재 섹션 집합·30쪽·10000자 회귀를 고정한다.

## CLI·관리자 계약

CLI는 `integrated gen --module love --module wealth` 반복 옵션을 추가하고, 저장 재렌더는 content.json의 `modules`와 `module_schema_version`만 따른다. 관리자는 Q6 확정 카테고리에서 추천 체크를 받되 다중 체크박스로 최종 확정한다. `GENERAL`·`TIMING`은 자동 선택하지 않고 운영자가 1개 이상 고르기 전 생성을 차단한다. `RELATION`은 상대 입력이 있으면 `gunghap`, 없으면 `love`를 추천만 한다. 확정 목록은 `report_plan.sections`와 `render_meta.gen_params.modules`에 저장하고 감사 로그에는 모듈 ID만 남긴다. 상태머신 전이는 바꾸지 않는다.

## 대안 비교와 승인 게이트

| 안 | 장점 | 위험 |
|---|---|---|
| A. 완성된 Report23 섹션 필터 | 변경량이 작고 빠르다. | 현 `work`가 직업/재물을 합쳐 독립 선택이 불가능하고, consult 문맥·미선택 영역 문장이 새어 나와 사후 필터가 영구 부채가 된다. |
| B. 모듈 레지스트리 + 제공자 분리(권장) | 경계·근거·분량·테스트가 모듈 단위로 일치하고 새 영역 추가가 가역적이다. | `work_job/work_wealth` 분리와 골든 조립 회귀가 필요해 초기 구현량이 크다. |

구현 착수 전 운영자 승인 항목은 ① B안, ② 위 분량 공식, ③ `RELATION` 추천 규칙, ④ 기본값 5개 전체다. 승인 뒤에도 1단계는 레지스트리·조립/게이트 테스트만, 2단계는 CLI/admin 배선으로 나눠 각 단계 전체 pytest와 합성 렌더를 별도 검증한다.
