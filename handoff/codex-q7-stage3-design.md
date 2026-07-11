# Q7 3단계 설계안 — 주문 플로우 모듈 편입 + admin 추천·확정 UI (2026-07-11 운영자 승인 ①~④, ⑤는 별도)

> 작성 2026-07-11 (Claude, 실측 기반). 선행: 1단계(레지스트리·조립·게이트, `065c987`)·2단계(CLI `--module`, `ff002ee`) 종결, 기준선 758 passed / 4 skipped.
> 이 문서는 설계 승인용이다. 승인 후 TASK_PACKET으로 변환해 Codex에 발주한다.

## 목표와 불변 경계

운영자가 admin에서 Q6 질문 분류를 참고해 모듈을 확정하면, **주문 생성이 그 선택을 실제로 소비**해 부분 조합 리포트를 만든다. 2단계까지의 모듈 기능은 CLI 전용이라 주문·검수 흐름과 분리돼 있다 — 3단계가 이 간극을 잇는다.

불변: 계산 LLM 위임 금지 / APPROVED 전 발송 차단·상태머신 전이 무변경 / 가드 완화 금지 / 모듈 선택은 서술 범위만 정함(계산 불변) / 소비처 없는 파라미터 금지(A-5).

## 실측한 현행 구조 (설계의 전제)

| 앵커 | 실측 |
|---|---|
| `app.py:53 /generate` | 웹폼 접수 = **1인** birth·name·concern·product(기본 "integrated"). 상대 입력 없음 |
| `order_flow.py:192 run_order` | 접수 → `gen_params` 저장(재생성이 그대로 소비) + Q6 자동분류 저장 |
| `pipeline.py:46 generate` | 1인 주문 생성 경로. `builder.build_report` 호출 — **1단계가 확장한 그 빌더**지만 `work_modules`/`include_section_ids`는 미전달(항상 전체) |
| `delivery_quality.py:29` | 모듈 게이트(N 하한·missing/unexpected)는 `_INTEGRATED_FULL_PRODUCTS = {"integrated_full"}` 전용 |
| `integrated.build_integrated_full` | **1인 + gunghap 제외 조합 이미 지원**(1단계). content.json 모듈 메타 영속·복원·재렌더 완비 |
| `question_router.py:13` | Q6 7종: LOVE·JOB·WEALTH·HEALTH·RELATION·TIMING·GENERAL. admin 확정 POST(`admin.py:283`)·GENERAL 미확정 승인 409 기존 배선 |

## 권장안 A — 1인 주문의 integrated_full 편입 (gunghap·2인 접수는 4단계 이연)

핵심: 새 생성 코드를 만들지 않고, **이미 완성된 `build_integrated_full`(1인·부분 조합)을 주문 생성 경로에 연결**한다. 1단계 게이트·메타·재렌더가 전부 그대로 소비된다(팬텀 0).

1. **접수**: product 선택지에 `integrated_full` 추가. 접수 시 modules는 받지 않는다(고객이 아니라 운영자가 정함 — 빈 상태로 IN_REVIEW 전 단계 대기).
2. **자동 추천 (Q6 연동, 표시만·자동 선택 없음)**: LOVE→love, JOB→job, WEALTH→wealth, HEALTH→health, **RELATION→love**(1인 주문이므로 — 승인된 "상대 없으면 love" 규칙), TIMING·GENERAL→추천 없음. 결정론 매핑 함수는 `modules.py`에 둔다(레지스트리 단일 소스).
3. **admin 확정 UI**: 주문 상세에 모듈 체크박스(**4모듈** — gunghap은 1인 주문에서 미표시) + 추천 배지 + 확정 POST. 확정 목록은 `render_meta.gen_params.modules`(생성 소비용)와 `report_plan.sections`(요약 관측용)에 저장, audit엔 모듈 ID만(질문 원문 비복제 — 절대규칙 17 정합).
4. **생성 차단 (fail-closed)**: `integrated_full` 주문은 모듈 미확정 시 생성·재시도를 차단한다(Q6 GENERAL 미확정 승인 409 패턴 재사용 — `question_category_state` 상당의 `module_selection_state`).
5. **생성 소비**: 백그라운드 생성/재시도가 `product == "integrated_full"`이면 `pipeline.generate` 대신 `build_integrated_full(1인, modules=확정값, render=True)` 분기. content.json 영속 포함(재렌더 무과금 유지). 최종 발급(final_render) 경로도 동일 spec·게이트 재사용 — 발급 시점 게이트 no-op 금지(B-1 선례).
6. **게이트**: 기존 1단계 그대로 — N=1..4 하한(16/20/24/28쪽), missing/unexpected, R9-1 소유권 교차검증. 신규 게이트 없음.
7. **기존 상품 무변경**: `integrated`(1인 Report23 23장)는 그대로 병행 판매. 이중 레짐 아님 — 서로 다른 상품이 서로 다른 게이트 프로필을 갖는 기존 구조(gunghap/followup과 동일 패턴).

## 대안 비교

| 안 | 요지 | 판정 |
|---|---|---|
| **A. 1인 integrated_full 편입 (권장)** | 완성된 빌더를 주문 경로에 연결. 게이트·메타 재사용 | 변경 최소·팬텀 0. 위험 = 생성 경로 2갈래 분기(양방 테스트 필수) |
| B. 기존 integrated(Report23)에 모듈 적용 | `pipeline.generate`에 include_section_ids 전달 | 기각 — Report23은 모듈 게이트 비대상 상품이라 하한·커버리지 재설계 필요, 23장 구조와 12+4N 공식 불일치(이중 레짐) |
| C. 2인 접수 확장까지 한 번에 | 상대 입력 폼 + gunghap 주문화 포함 | 기각(이연) — BirthInput 스키마 2인화·PII 지평 확대·발급 전 경로 전면 확장 = 1스텝=1기능 위반. **4단계**로 분리 |
| D. 와일드카드: 고객 셀프서비스 모듈 선택 | 접수 폼에서 고객이 직접 체크 | 기각 — "운영자 확정" 승인 계약과 충돌, 검수 전 고객 선택은 상품 정책 변경(가격·표시광고 검토 필요) |

## 프리모템 (A안이 실패한다면)

- **생성 분기 사각**: integrated_full 분기가 재시도·최종 발급 중 한 곳만 배선되면 팬텀 파트너(QI-2026-07-04-01)류 재발 → 접수·생성·재시도·최종 발급 4지점 분기 테스트를 수용 기준에 명시.
- **시진 불명 주문**: `build_integrated_full`의 unknown_time 경로(절대규칙 8 — 자미 생성 금지 강등)가 1인 주문화에서 실제 작동하는지 미실측 → 구현 전 프로브 필수(착수 점검 항목).
- **후속(Q5) 상호작용**: 부분 조합 주문(예: love만)의 후속 질문이 없는 영역(job 등)을 물으면 근거 장이 없다 → followup compose의 카테고리 근거 장 선택이 저장 섹션 부재 시 fail-closed인지 확인, 아니면 차단 규칙 추가.
- **분량 상한**: 1인 4모듈(28쪽 하한)이 실제 조판에서 안정 달성되는지 미검증 → 승인 시 합성 실렌더 1회(N=1과 N=4)를 검증 단계에 포함.

## 착수 점검 실측 결과 (2026-07-11 — 프리모템 항목 확정, 3-A 범위에 반영)

1. **계산 입력 미배선 확정**: `integrated.py:593` `engine.build(y,mo,da,hh,mi,is_male,horoscope_date=하드코딩)` —
   longitude·latitude·policy(yajasi)·unknown_time을 받지 않는다. 주문화 시 진태양시 보정 누락 = 정확도 결함.
   → **3-A에 계산 입력 배선 포함**(기본값=현행 동일로 CLI 하위호환 보존). unknown_time은 배선하지 않고
   **integrated_full 접수 시점 차단**(절대규칙 8의 명리 단독 강등 지원은 후속 단계).
2. **followup 근거 장 부재 = 조용한 skip**: `followup/compose.py:149-156` — 저장본에 카테고리 근거 장이 없으면
   조용히 건너뛴다. 부분 조합 저장본(예: love만)에 job 후속이 오면 근거 없는 조립 위험.
   → **3-A에서 integrated_full 부모 주문의 후속 생성을 fail-closed 차단**(지원은 별도 단계).

## 운영자 승인 대기 항목

1. **A안 채택** (B·C·D 기각, 2인·gunghap 주문화 = 4단계 이연)
2. 접수 폼 product 선택지에 `integrated_full` 노출 (대안: 폼 비노출, 운영자가 admin에서 상품 전환 — 노출을 권장)
3. 모듈 미확정 시 생성 차단 정책 (409 패턴 재사용)
4. RELATION→love 고정 추천 (1인 한정이므로)
5. 가격·상품명·판매 페이지 표기 (이 문서 범위 밖 — 운영자 별도)

## 구현 분할 (승인 후 발주 단위)

- **3-A**: 접수 product 확장 + 생성/재시도/최종 발급의 integrated_full 분기 + 미확정 차단 (order_flow·app·store 경계) — 4지점 양방 테스트 동반.
- **3-B**: admin 추천·확정 UI (admin.py·템플릿) + 추천 매핑 함수(modules.py) + 저장·audit.
- 각 단계 착수 전 실측 앵커 재검(특히 unknown_time·final_render 경로), 완료 시 전체 pytest·교차리뷰 라운드 별도.
- Codex 패킷 0절에 "검색 시 ignored 제외 글롭 필수" 포함(라운드10 재발 방지).
