# Q7 4단계 설계안 — 2인 접수·gunghap 모듈 주문화 (2026-07-11 운영자 승인 ①~⑤)

> 작성 2026-07-11 (Claude, 실측 기반). 선행: Q7 1~3단계 완결(`d71fb35`까지, 기준선 **801 passed / 4 skipped**),
> 합성 실렌더 경계표·분량 정책 확정("무LLM 폴백 발급 N≤2, N≥3 = LLM-on 전제").
> 이 문서는 설계 승인용이다. 승인 후 TASK_PACKET으로 변환해 Codex에 발주한다.

## 목표와 불변 경계

주문 접수에서 상대(파트너) 정보를 선택 입력받아, integrated_full 주문이 **gunghap 모듈을 포함한 5모듈 조합**까지 선택·생성할 수 있게 한다. 현재 gunghap 조합은 CLI 전용이다.

불변: 계산 LLM 위임 금지 / 상태머신·APPROVED 발송 차단 무변경 / 가드 완화 금지 / 명리 최종 권위·자미 보완 / LLM 입력에 생년월일 원본 비전달(파생 계산값만) / 고객 PII 최소 저장.

## 실측한 현행 구조 (설계의 전제)

| 앵커 | 실측 |
|---|---|
| `order_flow.py:392` 근방 `create_order` | 1인 접수 — birth·gender·name을 정규화해 `gen_params` 저장. integrated_full은 시진 불명 접수 차단(3-A) |
| `order_flow.py:904`·`admin.py:173` | gunghap 거부/비노출 지점 — 정확히 2곳(1인 전제 하드 차단) |
| `_run_integrated_generation` | people을 **1인 3원소 튜플로 하드코딩** — 2인 확장 지점 |
| `integrated.build_integrated_full` | **2인+gunghap 이미 지원**(CLI 검증 완료). 단 people 튜플은 3원소 — 사람별 unknown_time 미지원 |
| `gunghap.py:940·1163` | 기존 gunghap CLI는 사람별 4원소(unknown_time) 지원 — integrated_full 튜플과 형식 상이 |
| `models/report.py` `partner_present` | 필드 실존 + 전달 경로 배선됨(3-A) — 2인 시 True로 실소비 확인 필요(팬텀 방지) |
| `store/orders.py:249 purge_identifier` | **단골(본인) 식별자만 파기** — 상대 PII는 파기 범위 밖. 주문 하드삭제(delete_order)는 전체 커버 |
| `modules.py.recommended_modules_for_category` | 카테고리만 입력 — RELATION→love 고정(3-B). 상대 유무 분기 없음 |

## 권장안 A — gen_params additive 확장 (스키마 비변경)

핵심: 상대 정보를 `gen_params["partner"]` 서브딕트(additive)로만 저장한다. `BirthInput`/`UnifiedReport` 스키마·DB 마이그레이션 0. 기존 재생성·최종 발급이 gen_params를 소비하는 구조와 정합.

1. **접수**: 웹폼에 상대 필드(선택) — 이름·생년월일시·성별·음력/윤달. 입력 시 본인과 **동일한 KASI 정규화 재사용**(경고 목록 병합). `gen_params["partner"] = {정규화된 값}`. 상대 미입력 = 기존 1인 주문과 완전 동일(키 자체 없음 — 3-A modules 패턴).
2. **상대 시진 불명 = 접수 차단**: integrated_full의 people 튜플이 unknown_time을 지원하지 않으므로(본인 차단과 동일 논리) fail-closed. 사람별 unknown_time 배선은 범위 밖(별도 단계).
3. **추천 복원**: `recommended_modules_for_category(category, partner_present=False)` — RELATION + 상대 있음 → `("gunghap",)`, 상대 없음 → `("love",)`(현행 유지). 다른 카테고리는 상대 유무 무관. 원승인 계약("상대 입력이 있으면 gunghap, 없으면 love를 추천만") 복원.
4. **admin 조건 분기**: partner 존재 주문이면 모듈 옵션에 gunghap 포함(5모듈 체크박스), `confirm_module_selection`의 gunghap 거부를 "partner 없으면 거부"로 조건화. 1인 주문 동작은 현행 그대로(회귀 고정).
5. **생성 분기 확장**: `_run_integrated_generation`이 partner 존재 시 2인 people 리스트 구성(receiver=본인 이름 명시). `build_integrated_full`은 무변경 — 이미 2인·gunghap·궁합 게이트(identity/singang/role) 지원. 최종 발급 재검증 경로도 다인 지원 확인됨(names 리스트).
6. **분량**: N=5 = 30p/10,000자(공식 상한). 무LLM 제약 승계 — gunghap 포함 조합도 N≥3이면 LLM-on 전제. 구현 후 합성 실렌더 1건(2인·N=5)으로 실증.

## 대안 비교

| 안 | 요지 | 판정 |
|---|---|---|
| **A. gen_params additive (권장)** | 상대는 gen_params 서브딕트만, 스키마 0 변경 | 최소 침습·마이그레이션 0·3-A 패턴 재사용. 위험 = 상대 PII가 정식 스키마 밖(아래 프리모템) |
| B. BirthInput/UnifiedReport 정식 partner 필드 | 모델 확장 + 마이그레이션 | 기각 — 소비처가 생성 1곳뿐인데 모델 전층 변경, E10급 PII 파장(마스킹·insight·purge 전수 재점검) |
| C. 별도 궁합 주문 상품 신설 | gunghap 상품을 주문화 | 기각 — Q7 모듈 조합 취지(한 상품에서 골라 담기)와 어긋나고 게이트·메타 이중화 |
| D. 와일드카드: 현상 유지 | gunghap 조합은 CLI 전용 지속 | 기각(이연 가능) — 운영자가 CLI로 처리 가능하므로 4단계 자체의 긴급성은 낮음. 단 주문·검수 이력이 안 남는 운영 부채 |

## 프리모템 (A안이 실패한다면)

- **상대 PII 사각**: gen_params는 purge_identifier 파기 범위 밖 — 상대 식별 정보가 주문 보존 기간 내내 남는다. 본인 생년월일도 같은 위치에 보존되므로 **보호 수준은 동일**하나, "상대는 단골 아님·동의 주체 아님"이라는 차이를 운영 정책으로 명시해야 함(승인 항목 ③). audit·admin 화면·마스킹 경로에 상대 원문이 새지 않는지 양방 테스트 필수.
- **partner_present 팬텀 재발**: 필드는 이미 있는데 접수→생성→게이트로 실제 True가 흐르는 분기 테스트가 없으면 QI-2026-07-04-01 재발 — 2인 주문에서 partner_present=True·가드 소비까지 단언.
- **관계 compose 무LLM 경로**: integrated 경유 2인 무LLM 폴백은 웨이브1 궁합 검증과 경로가 다름 — 합성 실렌더(N=5)로 실증 전에 완료 주장 금지.
- **정규화 경고 유실**: 상대 음력·한중 상이일 경고가 본인 warnings에 병합되지 않으면 관리자가 못 봄.

## 운영자 승인 대기 항목

1. **A안 채택** (B·C 기각, 사람별 시진 불명 배선은 범위 밖)
2. 상대 시진 불명 = **접수 차단** (본인과 동일 fail-closed)
3. **상대 PII 정책**: gen_params 내 본인과 동일 보호 수준으로 보존, 개별 파기는 주문 하드삭제로만(purge_identifier 확장 없음) — 이 잔여를 수용하는지
4. RELATION + 상대 있음 → gunghap 추천 복원 (없으면 love 유지)
5. 구현 = **단일 패킷**(접수·추천·admin·생성이 상호 의존적, 규모는 3-A보다 작음) + 라운드13 교차리뷰 + 합성 실렌더 N=5(2인) 1건

## 구현 분할 (승인 후)

단일 패킷 `q7-stage4-partner`: 수정 예상 = `app.py`(폼)·`order_flow.py`(접수·생성·confirm 조건)·`admin.py`+템플릿(옵션 조건)·`modules.py`(추천 시그니처)·관련 테스트. `integrated.py`·게이트·calc/input 비수정. 완료 후 합성 실렌더 N=5는 검증 세션(Claude) 몫.
