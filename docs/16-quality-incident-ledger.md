# 16. 품질 사고 장부와 재발 방지 규칙

## 2026-07-06 파일럿 계측(대기): 발송 전 이질 렌즈 스윕(Phase 4, hsweep) — 인프라 완료, 실측 미실행

- 목적: 육안급 결함을 발송 전에 선제 적발(운영자 신규 발견 Z=0 이 목표 지표). 인프라(scripts/hsweep.py + harness/prompts/sweep/lens_*.md 5종 + tests/test_hsweep_contract.py 12건)는 완료·전부 API 0 검증. advisory 전용(게이트/발송 무접촉, 구조적으로 verify/order 모듈 비import).
- **실측 미실행(2중 게이트)**: (a) 실 API 스윕은 운영자 명시 승인 + 3중 잠금(--approve --allow-llm + env) 필요, (b) 실 발송 후보 PDF 부재(customer3 v9 미생성 — 고객 PII 입력 필요; h153 은 룰 전용 픽스처지 납품물 아님).
- **파일럿 계측 지표(실행 시 이 절에 기록)**: 다음 발송물에서 후보 N → 반박 생존 M → 운영자 확정 진결함 K, 운영자 육안 신규 발견(스윕 미탐) Z. 목표 Z=0, 정밀도 K/M ≥ 0.7. 미달 시 렌즈/루브릭 1회 조정 후 재측.
- 비용: 회당 ~$1.2-1.5 예상, 상한 $3 코드 강제(초과 시 중단·부분 리포트). 첫 승인 지출 후보 = 기존 렌더 PDF(예: customer2) 합성 드라이런(실모델 동작·실비용 대 상한 검증) — 실 파일럿 계측과 별개.
- **합성 드라이런 실측(2026-07-06, customer2_integrated_full.pdf, 운영자 승인 지출)**: 인프라 전 단계 실 API 검증 성공. 후보 N=30(렌즈 5종) → 반박 생존 M=0 → 확정 K=0. **비용 $0.617**(상한 $3의 21%, 추정 $1.2-1.5보다 낮음 — 비용 모델 보수적 확정). calls=6(렌즈 5+반박 1; judge는 생존 0이라 미발화). partial=False. **PII 0 실측**: 전송 전 프리플라이트로 잔존 이름·dashed 날짜·한글 생년월일 전부 0 확인(self_civils 정밀 마스킹 추가로 한글 형식 생일 갭 선제 차단), 리포트에도 dashed 0. advisory 구조 확인(gate_pass 부재). 리포트 gitignored.
  - 관측/교훈: (a) customer2 는 이미 전 게이트+운영자 검수 통과한 정제 납품물이라 M=0(정제 문서에 오경보 0)은 타당하나 (b) judge 경로(Opus·순서 스왑)가 실데이터로 미발화 + 정밀도 K/M 산출 불가(M=0). **실 파일럿 계측은 검수 전 신선 발송물이 필요**(judge 발화 + K/M 측정). (c) 반박이 30→0으로 강함 — 신선 문서에서 과반박(진결함 유실) 여부를 Z(운영자 육대 신규 발견)로 검증해야 함.
  - **발견·선제수정**: mask_for_api 가 self_civil 미수용이라 한글 형식 생년월일("YYYY년 M월 D일")을 못 막던 갭 발견(customer2 엔 없었으나 타 리포트 유출 위험) → self_civils 정밀 마스킹 추가(시기 참조 오마스킹 없이 특정 인물 생일만). 양방 테스트 동반.
- PII 방어 범위(residual 명시): 전송 페이로드는 이름(공급값)·날짜/시각/8자리 마스킹 + 전송 전 벨트로 fail-closed. rationale 은 모델 free-text 라 parse 시점에 name/date 스크럽하나, 그 외 PII 클래스(지명·직장·관계 세부)는 프롬프트 지시 + 벨트로 축소할 뿐 완전 제거 보장 아님("PII 0" 아니라 "name/date belt + 인용 금지 프롬프트"). 리포트는 gitignored·운영자 전용이라 잔여 위험 낮음. 더 강한 보장이 필요하면 rationale 자체를 구조화(자유텍스트 제거)하는 후속.

## 2026-07-06 추가: QI-2026-07-06-01 age 팬텀 파라미터 체인(도판 제거 잔여) — dead-param 스캐너(Phase 2)가 적발, 2026-07-06 제거 완료

- 증상(Phase 2 dead-param 스캔 실측): `age` 가 order_flow(관메타 `meta.get("age")`)→pipeline→render_pdf(`age=age` 포워딩)→render_html 로 4단계 흐르는데 어느 렌더 함수도 소비하지 않는다. 도판(일러스트) 전면 제거(운영자 지시) 후 남은 잔여 인자 — 기능 영향은 없으나 팬텀 파라미터 클래스(QI-2026-07-04-01 계열: "받기만 하고 안 쓰는" 인자).
- 영향: 현재 무해(미소비라 산출 불변). 위험은 미래 — 이런 죽은 배선이 방치되면 "존재하지 않는 값이 흐르는" 착시로 실결함(팬텀 파트너류)의 온상이 된다.
- 조치(Phase 2): dead-param 스캐너(scripts/deadparam_scan.py)+하드 게이트가 이 클래스를 자동 적발하도록 상시화. `age` 는 체인 전체 제거가 주문경로(order_flow) 리팩터라 반나절 범위 밖 → tests/deadparam_allowlist.txt 에 참 사유로 등재하고 별도 세션 제거로 추적(이 항목). page_texts(내 frontload 제거 잔여)·geukguk(day_master)는 같은 스캔에서 즉시 제거(소비처 배선까지 한 단위).
- 재발 방지: 파라미터 신설 시 소비처 배선까지가 한 단위(방법론 A-5). 스캐너 게이트가 미소비 인자를 커밋 시점에 차단(allowlist 는 참 사유 필수).
- 제거 완료(2026-07-06): age 4단계 체인 전체 제거. 사전 매핑으로 소비처가 order_flow:385(최종 발급 render) **단 하나**(render_meta["age"] 는 dict 라 무마이그레이션·다른 READ 0)임을 실측 → 원자적 제거: render_html/render_pdf 시그니처·forward + pipeline age 계산·kwarg + order_flow age 계산·render_meta 저장·kwarg + test_final_render_gate 픽스처 키 + allowlist 항목. 전 render_pdf/render_html 호출부 positional-arg 점검(오배치 0). 순수 dead-code 제거라 산출 불변(골든 불요) — 발급 경로 회귀(test_orders·test_final_render_gate) GREEN 으로 APPROVED-전-발송 상태머신 불변 확인. 전체 pytest 643 passed(제거 전과 동일, 테스트 수 불변). deadparam 스캔 미해결 0.

## 2026-07-05 추가: QI-2026-07-05-03 consult 골격 폴백 false-PASS — 질문 답변 챕터 붕괴가 게이트·발송 리포트 모두에서 안 보임

- 증상(운영자 실격 판정 v7 + 조사 B 실측): 질문에 정면으로 답하는 유일한 챕터(consult)가 가장 얇은 generic 골격으로 폴백(985→388자, -61%). 그런데 (a) delivery 게이트는 intro 초반 1800자만 검사해 gate PASS, (b) 발송 리포트에는 "전 챕터 LLM 재작성"으로 오기재됐다(GuardReport 가 폴백 카운트만 보고, 어느 챕터인지 미배선).
- 영향: 유료 풀이의 핵심 가치(질문 답변)가 무너진 채 발송 직전까지 통과. 총 분량은 배경 챕터 증가로 비슷해 보여 육안 감지도 늦음(재분배 착시). 운영자 지적의 "질문 답변 소극화·다운그레이드"의 실체.
- 원인(2층):
  - (감지) frontload 게이트가 intro 전용 — consult 자체의 밀도·직답성 검사가 0. 챕터별 polished 플래그는 존재하나 CLI·hrun·발송 리포트 어디에도 소비처가 없었다(P0-1 day_offset 류 "존재하나 미배선" 재발).
  - (구조) 골격 consult(generic-else)가 388자 유보 체크리스트라, 폴백이 곧 품질 붕괴가 되는 구조. 보장 금지 프롬프트가 문맥 무관 금지("반드시/확실히 쓰지 마라")로 완곡어법을 유도해 폴백률을 올린 것도 배경(P3 에서 정밀화).
- 재발 방지(구현·검증 완료, 7c94afa·7b154fc·02e7c1d·a896515):
  - P0 관측: GuardReport 에 polished/fallback_section_ids + cli "chapters:" 줄 + hrun summary regen_fallback_chapters — "전 챕터 LLM" 오보가 구조적으로 불가능.
  - P1 골격: consult·스냅샷을 [방향 단정→근거(궁 실명)→시기→첫 행동] 구조 830~930자로 재작성 — 폴백돼도 직답 품질 유지.
  - P2 게이트: consult_direct_result(밀도 하한 450 + 결론/시기/행동/질문축) — compose 선검사 + pipeline 하드 게이트 2단. consult 한정 2차 재시도(+1콜).
  - P3 정밀화: 결과어 결합만 금지, 행동·시기 단정 허용(절대규칙 12 사각 축소, safe_lint §12 전례) — 소극화 원인 제거.
- 실측: 양방 테스트 신규 14건(P0 5+P1 4+P2 5), v7형 388자 유보 문안 FAIL·직답 골격 PASS 재현. 전체 pytest 591 passed / 4 skipped / exit 0.
- 교훈: "카운트만 보고 무엇인지 안 보이는 관측"은 관측이 아니다. 파생 요약(발송 리포트)의 주장(전 챕터 LLM)은 원천 필드(polished 플래그)로 증명 가능해야 한다.

## 2026-07-05 추가: QI-2026-07-05-02 개인 리포트 1장 문서 내레이터 말투 — 골격이 고객 표면에 그대로 노출 (gate PASS·육안 불합격 유형)

- 증상(운영자 발견, v6 발송 직전): 1장에 "사주를 한 장으로 압축해 보겠습니다"(작성자 작업 예고 = AI 인상), "조건, 사람, 시기를 차례대로 확인하세요"(무엇을 어떻게 볼지 없는 빈 지시). 전 게이트 PASS 상태로 발송 준비까지 통과 — 감지선은 운영자 육안뿐이었다.
- 원인(2층):
  - (생성) 두 문구 모두 LLM 이 아니라 결정론 골격(rules.py 924·1556) 원문. 1장 요약은 _COMPOSE_SECTIONS 미포함(rule-only)이라 골격이 곧 고객 표면. 동종 작업 예고형('~보겠습니다')이 골격에 총 9곳, 빈 지시 2곳, '읽는 방향' 문서 진행 예고 1곳.
  - (감지) '~보겠습니다 금지' 규범이 llm_sections 프롬프트(LLM 지시)에만 존재 — 골격은 적용 대상이 아니고 lint 강제도 없었다. customer_meta_lint 는 연결부 예고형('다음/이어서/장에서 …보겠습니다')만 등재, 단독 작업 선언형은 사각. QI-2026-07-05-01(감지 강화 때 business 골격 미동기화)과 동일 패턴의 개인판 — **규범을 만들면 골격·lint·프롬프트 3면 동기화까지가 한 단위.**
- 재발 방지(구현·검증 완료, 0c91f03):
  - 생성: rules.py 9+2+1곳 상담가 화법 교체(작업 예고 → 관법 서술 '~으로 봅니다'/직접 내용 진입, 빈 지시 → 구체 확인 항목, 요약 도입 = "사주를 펼쳐 놓고 보면 가장 먼저 눈에 들어오는 그림이 있습니다").
  - 감지: customer_meta_lint 에 writer_task_announcement('보겠습니다' 전면 — 관법 '봅니다'·권유 '보세요' 통과)·formulaic_empty_instruction('차례대로/순서대로 확인') 등재. 프롬프트 규범의 게이트 승격(완화 0).
  - 구조 앵커: 전 섹션 실빌드 → customer_meta_lint 0 테스트(test_rule_skeleton_sections_pass_customer_meta_lint) — 이후 금지어 등재 시 골격 미동기화가 즉시 RED.
- 실측: v7 재생성(운영자 승인, 동일 입력) 39p·게이트 PASS·지적 문구 0·신규 룰 포함 벨트 0. 신규 usage 관측 첫 실전: 17호출·입력 102,757·출력 26,904 토큰(약 $0.7). 전체 pytest 566 passed / 4 skipped / exit 0.
- 후속: v6 발송 보류(폐기 예정), v7 은 전 챕터 LLM 재작성본이라 운영자 전문 육안 검수 후 발송(REVIEW_REQUIRED).

## 2026-07-05 추가: QI-2026-07-05-01 business 궁합 골격 미동기화 — 감지(금지어)만 강화되고 생성 골격이 안 따라감 + regen 실패가 "done" 으로 표기

- 증상: h153 픽스처 재생성(운영자 승인 regen)에서 gunghap(3인 business 모드) 빌드가 하드 게이트 실패. hverify 실측 quality internal_meta_label 8건('십성으로' 6·'같은 방향으로 모이는 협업의 결' 2) + semantic ai_signature_punctuation 4건(장 제목의 em dash, 4개 페이지). 동일 PDF 계열이 06-25 리포트까지는 gate PASS — 그 후 게이트 강화기에 잠복.
- 영향: business 궁합 경로는 compose 폴백이 발생하면 현행 게이트를 통과하는 PDF 를 만들 수 없는 상태였다(판매 시 빌드 실패로 fail-closed — 고객 유출은 없음). 부가로 hrun summary 가 재생성 실패(rc!=0)를 `regen: "done"` 으로 표기해 실패가 가려졌다(관측 갭).
- 원인(2층):
  - (생성) `_pair_slot` 골격 문구('십성으로'·'같은 방향으로 모이는 협업의 결')가 relationship 작업 때 quality_lint internal_meta_label 금지어로 등재됐는데, 순화 치환은 relationship 모드(relationship/context.py)에만 배선 — business 모드는 이 슬롯이 폴백 본문으로 원문 그대로 나간다. `_GH_SECTIONS` 장 제목 4개의 em dash 도 시맨틱 벨트(ai_signature_punctuation, 제목 포함 페이지 텍스트 검사) 사각. **금지어를 등재하면 그 문구를 쓰는 생성 골격 전 경로의 동기화까지가 한 단위**(A-5 '배선까지 한 단위'의 감지-생성 대칭형).
  - (감지/관측) hrun 이 regen rc!=0 이어도 res["regen"]="done" — retry_reasons 에만 pdf_regen_failed 가 남고 문서별 표기는 성공처럼 보였다. regen_returncode 는 summary 화이트리스트에서 드롭(E-5 유형 재발).
- 재발 방지(구현·검증 완료):
  - `_pair_slot` 문구 고객 문장화('관계 역할로 보면'·'관계의 결', em dash 제거) + `_GH_SECTIONS` 제목 em dash 제거. 게이트는 불변(완화 0).
  - hrun: regen rc!=0 이면 `regen: "failed"` 로 표기(fail-closed 관측).
  - 양방 테스트 4건: 골격 출력 internal_meta_label 0 / 구 골격 문구는 여전히 차단(가드 불변 앵커) / 제목 시그니처 부호 0 / regen 실패 "failed" 표기.
- 실측: 골격 수정 후 룰 전용 빌드(API 0) gate_pass=True 선확인 → LLM 재생성 1회로 성공. h153 픽스처 교체 완료: personal 37p·gunghap 17p 모두 gate PASS(리포트 handoff/reports/20260705-031710·20260705-033305). 전체 pytest 553 passed / 4 skipped / exit 0.
- 비용 주의: 1차 재생성은 compose(LLM 지출) 후 최종 게이트에서 파기 — 게이트가 옳게 막았지만 차단 시점이 비용 발생 이후라 실패 1회분이 낭비된다. 재시도 전 API 0 룰 전용 프로브로 통과를 선확인하는 순서가 비용 방어의 표준.
- 연결 커밋: d7dc63c(골격+제목+양방 3건)·88fb6a1(hrun ref_date 전달+failed 표기+양방 3건)·e9efc7a(integrated CLI ref_date).

- 증상(운영자 발견): 2026-07-04 생성 풀이(CUSTOMER 시기재물)가 "4월 안에 재물 준비를 하나라도 시작해 두라", "5월 이후부터 더 열어두고 보시길 권합니다" — 이미 지난 달을 앞으로의 행동 시기로 제시. gate_pass=True 로 통과했었음(false-pass).
- 영향: 유료 풀이의 시기 답변 신뢰 붕괴(고객이 즉시 알아챌 오류). 연도 닻(2026-06-12 "지금은 2025년" 사고의 4중 방어)은 연 단위만 커버 — 월 단위 재판.
- 원인(2층):
  - (생성) compose [기준 시점] 블록이 연도만 주입 — LLM 이 '지금이 몇 월'을 모른 채 연중 아무 달이나 시기로 제안. ref_date 는 verify 까지만 배선되고 builder/compose 에는 미전달.
  - (감지) temporal_lint 월 검사가 도착동사(다가오/오면/열리) 전용 — "N월 안에 ~하라"(마감)·"N월 이후부터 ~보시길"(기점 권유) 프레임 미커버(사각 인접). 간격 패턴이 \n 배제라 PDF 추출 줄바꿈에서도 누락.
- 재발 방지(구현·검증 완료, 같은 날 후속 3건 포함):
  - 생성: [기준 시점]에 '오늘은 Y년 M월 D일, M월 이전 달을 행동 시기로 제시 금지' 주입(builder/pipeline ref_date 배선) + 재작성 피드백(위반 표현을 재작성 프롬프트에 전달 — 사유 없는 재시도의 동일 단어 재발 구조 해소).
  - 감지: _MONTH_DEADLINE/_MONTH_ANCHOR 신설(+\n 허용 간격). 재현 증명: 결함본(v3)에서 지적 2문장이 정확히 2건 검출, 수정본(v6) 0건. 양방 테스트 7건(미래 달 권유·회고 서술·다음 해 이른 달은 통과).
  - 후속 실측 결함 2건 동시 수정: (a) 장 말미 <90자 독립 꼬리 단락의 스필 페이지(widows CSS 는 단락 내부 전용) → _ORPHAN_TAIL_MAX 14→90(게이트 하한 정합)으로 부류 소멸. (b) intro 윤문이 골격의 '신청 질문부터 먼저 답하면' 직답 문단을 확률적으로 유실 → intro 가이드 직답 유지 지시 + 챕터 단위 frontload 선검사(유실 시 골격 폴백).
  - 2026-07-05 운영자 지시 개정(위 (b) 폐기): 운영자 v8 육안에서 1장 도입의 직답 문단(concern_snapshot)이 "처음부터 답을 흐린다"고 실격 판정 — 성향 슬롯만으로 만든 결정론 템플릿이라 어떤 문안으로도 뭉툭. intro 직답 유지 가드·frontload 게이트(char/physical)를 전부 폐기하고 1장 직답 문단(골격+_love_snapshot_text)을 제거했다. 신청 질문 직답은 고객 원문을 보고 쓰는 consult 장 + 전용 게이트(consult_direct_result + pipeline 하드 게이트 + 2차 재시도)가 전담 — docs/13 원 설계('답변은 후반 감정 피크에 배치')로의 회귀다. 커밋 9eec8d8.
- 실측: v6 = gate PASS·월 시제 0·저밀도 0·직답 유지·커플어 0. 전체 pytest 539 passed / 4 skipped. 생성 반복 비용 실측 ~$3(v1~v6) — 각 실패가 실결함 1개씩을 노출·박멸(기하 오탐·저밀도 재과금·월 시제·스필·직답 유실).
- 연결 커밋: b3cc880(월 시제+피드백)·3ceaae8(꼬리 병합)·e195dfd(직답 가드), 테스트 test_temporal_month·test_frontload_guard.
- 후속 완료(2026-07-05, 사각 인접 2건 — 백로그 소화):
  - 관계 경로 ref_date 배선(151ef23): 이 사고의 수정이 개인 경로(builder/pipeline)만 커버 — 궁합 compose 프롬프트에는 연도 닻조차 없었고 verify ref_date 는 3곳 하드코딩("{ref_year}-06-13"). [기준 시점] 닻을 llm_sections.temporal_anchor_block 으로 단일소스화해 gunghap._compose(프롬프트+temporal_lint)·build_gunghap·build_integrated_full(개인 장 build_report 포함)·재렌더(content.json 영속 소비)·CLI --ref-date 에 배선. 미지정 시 연중 6-13 기본(하위호환). 양방 6건(지난 달 권유 폴백/미래 달 통과 등). 운영 수칙: 실주문은 ref_date=생성 당일(docs/19 §11, ac371f6).
  - '또렷해지는' 변형형 선치환(3e8407e): 개별 활용형 나열 대신 어간 캐치올('또렷'→'분명', '또렷이'만 특례) — 가드(style_lint 또렷[가-힣]*) 불변, 양방 2건. v6 폴백 원인 소멸.
  - 전체 pytest 547 passed / 4 skipped / exit 0. main 37bbe12→ac371f6→9a486b3 전진.
- 남은 수동 검수: v6 육안 검수 후 발송.

## 2026-07-04 추가: QI-2026-07-04-01 팬텀 파트너 — 개인 풀이에 존재하지 않는 상대의 궁합 서술 혼입

- 증상: 궁합이 없는 개인(1인) 풀이에 궁합·관계 문구가 혼입(운영자 CUSTOMER_3 1회성 풀이에서 발견). 합성 재현 실측: 고민 원문의 사건 날짜("2020년 3월 5일에 이사")가 상대방 생일로 둔갑, 원문 동사 조각("이사한")이 이름으로 오인되어 "이사한님"(2020년생)의 명식·십성 관계 서술이 consult 에 통째로 주입됨.
- 영향: 개인 상품의 신뢰 사고(내 풀이가 아닌 내용). 본인 생일 재언급·이력 날짜·맨 6자리 숫자가 전부 오탐면.
- 원인(2층):
  - (유입) builder.py 가 `find_partner_births(concern)` 호출 시 본인 생일 제외 가드 인자(self_solar/ref_year)를 미전달 — **가드도 데이터도 있었는데 배선만 누락**. 또한 파서가 인물 문맥 없는 날짜(사건·이력)도 전부 상대 생일로 채택.
  - (감지) 커플 지칭("두 분/두 사람")을 잡는 게이트 룰이 없었고, verify `_placeholder_residue_hits_clean(hits, product)` 의 product 는 받고도 안 쓰는 dead parameter. "개인 상품 x 커플 언어 = FAIL" 테스트 0건.
  - (패턴) "배선됐지만 소비 안 되는 파라미터" 3연속 사례(자시 day_offset P0-1 → 최종발급 verify spec B-1 → 이번 product). 파라미터를 만들면 소비처·분기 테스트까지가 한 단위라는 10-methodology A-5 의 실증.
- 재발 방지(구현·검증 완료):
  - F1 `partner.py _has_person_context`(인물 문맥 게이트: 관계어/역법 라벨/출생 접미 요구) + builder self_solar/ref_year 배선. 양방: 오탐 4형(사건·본인생일·맨6자리·이력) 미감지 + 정상 6형(관계어·생 접미·역법 라벨) 감지 유지(test_partner.py).
  - F3 `couple_pair_reference` 룰 신설(candidate) + verify/builder 가 '1인 문서(파트너 부재)'에서 candidate→hard 승격(`partner_present` 배선: Report23 필드→pipeline/order_flow/hverify). 다인 상품·파트너 있는 개인 풀이는 기존 동작(오탐 0, 완화 0). 양방 test_couple_language.py 8건.
  - F2 재회 전제 문구(붙잡기·예전 문제·재접촉)는 원문에 재회 토큰이 있을 때만 — 결혼운·새 만남 질문은 1인 관점 중립 문단(연애 답변 자체는 유지, 과수정 금지 앵커 포함).
  - F4 compose 가드체인에 placeholder/커플 지칭 lint 부착(strict_pair = 파트너 부재).
  - 부수 발견 수정: partner_block 골격이 운영 라벨 "신청자"(placeholder hard 금지어)를 7곳 사용 → "본인"으로 교정(파트너 포함 개인 풀이의 잠복 hard fail 해소).
- 실측: 결함 입력 재현 → 수정 후 동일 입력 팬텀 0·strict 위반 0. 관련 스위트(couple/partner/p3/client_tone/verify_gate/delivery/gunghap/integrated 등) GREEN.
- 연결 커밋/PR: (이 세션 fix/feat 커밋), 테스트 tests/test_couple_language.py·test_partner.py.
- 남은 수동 검수: CUSTOMER_3 실 풀이 산출물은 위치 미상 — 재생성 필요 시 운영자가 입력 재제공(LLM compose 는 승인 후). 과거 파트너 미포함 개인 발송물 중 고민에 날짜가 든 건이 있으면 동일 증상 여부 육안 1회.

## 2026-07-02 추가: QI-2026-07-02-02 PDF 본문 좌우 비대칭 + 기하 검증 부재 + 레이아웃 재렌더 API 낭비

- 증상: 운영자 육안 "PDF 레이아웃이 다 틀어져 있고, 이 오류가 수십 번 반복된다." 본문 칼럼이 좌 20mm/우 42mm 로 왼쪽 쏠림(전 본문 페이지 일관).
- 영향: 프리미엄 납품물의 시각 품질이 무너지는데 게이트는 gate_pass=true 로 통과. 게다가 레이아웃만 고쳐도 재생성이 재compose(API ~$1)를 강제해 비용 낭비.
- 원인(3겹):
  - (즉시) report.html.j2 `.body{max-width:148mm; margin:0}` — 148mm 칼럼이 중앙정렬(margin:0 auto)이 아니라 왼쪽 고정 → A4 콘텐츠 170mm 중 남는 22mm 가 전부 우측에 쌓임.
  - (시스템) verify.py 게이트가 텍스트/글자수/시맨틱만 검사하고 픽셀·기하 검증이 0 → 글자수를 안 바꾸는 시각 결함이 반복 통과. orphan/저밀도조차 글자수 프록시이고 low_density 는 게이트도 아닌 '보고만'. 자동 rasterize/기하 회귀 전무, 300dpi 는 수동 체크리스트(NOT_RUN 기본).
  - (비용) integrated 재생성 경로(_regen_pdf → `python -m sajugen.integrated --llm`)가 compose 결과를 영속하지 않아, 템플릿/레이아웃만 바꿔도 매번 26섹션(개인12+관계14, Sonnet) 재compose.
- 재발 방지(구현·검증 완료, 커밋 b2143e5):
  - `.body{margin:0 auto}`(중앙정렬, 좌우 ≈31mm 대칭).
  - verify.py `_layout_geometry_hits` — PyMuPDF 텍스트 블록 bbox 로 좌우 여백 대칭(|Δ|≤10mm)·콘텐츠 넘침을 검사(픽셀 diff 아님, 폰트/AA 강건), gate_pass 편입. 표지·목차·짧은 페이지 스코프 제외로 오탐 방지. 기존 게이트 완화 0.
  - integrated.py compose 결과(.content.json, gitignored) 영속 + render-only 재렌더(render_integrated_from_content / CLI `render`, _render_integrated 추출·build 동작 불변) → 레이아웃/템플릿 변경이 API 과금(재compose)을 강제하지 않음.
- 실효 검증(API 0): 합성 렌더 좌31.2/우31.6mm 대칭·기하 게이트 clean. 구 템플릿 customer2 PDF 는 새 게이트가 margin_asymmetry 49건으로 차단. 실 라운드트립(build→저장→render-only 재렌더) 재compose 0(build_report/build_gunghap 예외 패치가 안 터짐). BEFORE/AFTER 시각자료(합성·PII0) tmp/layout_BEFORE.png(좌20/우42) vs tmp/layout_AFTER.png(좌31/우31). pytest 436 passed/3 skipped.
- 연결 커밋/PR: b2143e5(layout feat), STATE/장부 docs 갱신.
- 남은 수동 검수: customer2 교정본은 content 영속 이전 산출이라 저장본이 없어, 필요 시 seed 재compose 1회(운영자 승인) 후 재렌더는 무료. 신규 주문은 compose 시 자동 영속 → 레이아웃 반복 무료. render_verify + 300dpi 시각 점검 + 운영자 전문 검수 전 REVIEW_REQUIRED 유지.

## 2026-07-02 추가: QI-2026-07-02-01 customer2 통합 PDF gate_pass=true인데 육안 품질 미달

- 증상: customer2 integrated_full PDF가 gate_pass=true/all_gates_pass=true였으나 운영자 육안으로 납품 불가. 문서 진행/섹션 예고 메타("자미두수 명궁 이야기도 바로 이어집니다"), 질문 축 미반영이 통과.
- 영향: 자동 게이트를 신뢰하면 저품질 납품이 통과할 수 있다(false-pass). 특히 질문 축 검사가 조용히 no-op 되면 프리미엄 상품이 고객 질문에 답하지 않은 채 기준을 충족한 것으로 보인다.
- 원인:
  - (배선) hverify_pdf.verify_profile이 profile.concern만 읽어, integrated/궁합이 고민을 담는 situation 필드를 놓침 → delivery_quality가 concern 없이 돌아 required_axes=[]로 질문축 검사 no-op.
  - (룰 공백) customer_meta_lint 전이 룰의 앵커가 "살펴보겠습니다"뿐이라 "…이어집니다"/"이야기도 이어" 계열 미탐. compose 프롬프트·가드에도 문서 진행 금지 부재.
  - (지표 괴리) frontloaded_answer가 앞 1800자 기준이라 물리 페이지 p1~p3(표지/목차)와 어긋나 "초반 답변" 체감과 불일치.
- 재발 방지(구현·검증 완료, 커밋 8012a20):
  - P1 concern 정규화(hrun situation→concern) + verify가 product로 context_required 산출 + concern 부재 시 missing_customer_context failure(조용한 no-op 금지).
  - P2 customer_meta_lint.transition_section_preview(구조어+진행 앵커 공기 시만 FAIL, 생활흐름 오탐 0). P3 builder/gunghap compose 가드 부착 + _COMPOSE_SYSTEM/_GH_SYSTEM/relationship SYSTEM 프롬프트 belt.
  - P4 목차 리드 중립화("…다음 순서로 이어집니다"→"차례"). P5 physical_frontloaded_answer(warning 전용·게이트 불변) + PDF 검수 체크리스트(delivery_answer_review).
  - 게이트/차단룰 완화 0(전 diff의 '-'는 린터 재포맷). pytest 425 passed/3 skipped.
- 실효 검증(2026-07-02, regen·LLM·PII 0의 read-only 재검증): 기존 customer2 PDF를 새 게이트로 재검증하니 이전 gate_pass=true였던 동일 PDF가 gate_pass=False로 정확히 실패. transition_section_preview page 5 count 1 포착, has_customer_context=True·required_axes=['action','helper_people','timing'] 복구, physical_frontloaded_answer ok=False answer_page=4(첫 3p=표지/목차) 보고.
- 연결 커밋/PR: 8012a20(feat 게이트 보강), 6bb18db(docs STATE 갱신).
- 남은 수동 검수: 개선 실효를 실제 납품으로 확인하려면 새 stamp로 customer2 Tier2 재생성 1발 필요(운영자 명시 승인 전 regen/발송/push 금지). 재생성물은 REVIEW_REQUIRED에서 운영자 전문 검수 후에만 발송.

## 2026-06-26 추가: QI-2026-06-26-01 Phase 0 문서 운영 containment

- 증상: 구조 검사는 통과했지만 납품 후보 문안에 AI-meta 문장, placeholder residue, 마스킹 잔재가 남을 수 있는 workflow 위험이 확인되었다.
- 영향: 손편집 HTML/PDF가 표준 게이트를 우회하면 고객 납품 기준선이 흔들리고, Claude/Codex/Harness/Operator 역할 혼선으로 검수 책임이 불명확해진다.
- 원인: TASK_PACKET과 context snapshot 같은 handoff artifact가 부족했고, context overflow 뒤 최신 source-of-truth SHA 확인이 약했다.
- 재발 방지:
  - Claude는 Plan Architect/Semantic Reviewer, Codex는 승인된 TASK_PACKET 구현자, Codex Verifier는 별도 세션 검증자로 분리한다.
  - TASK_PACKET, CONTEXT_SNAPSHOT, PDF_REVIEW_REPORT를 handoff 필수 artifact로 둔다.
  - 납품 후보는 표준 게이트 파이프라인에서만 만들고, 손편집 HTML/PDF는 최종 납품 기준선으로 쓰지 않는다.
  - RUN_STATE에는 current_stage, input_sha, output_sha, api_calls, pdf_rendered, retry_blocked, final_status를 남긴다.
  - 최신본은 파일명으로 판단하지 않고 SHA로 판단한다.
- 연결 커밋/PR: Phase 0 docs containment 작업.
- 남은 수동 검수: 실제 고객 PDF는 render_verify, 금칙 텍스트 스캔, 300dpi 시각 점검, 운영자 전문 검수 전 REVIEW_REQUIRED 상태로 둔다.

## 2026-06-27 추가: QI-2026-06-27-01 Phase 1 universal semantic gate verified

- 증상: 손편집 또는 편집 경로를 거친 납품 후보에 AI-meta 문안, placeholder residue, document self-reference가 남을 수 있었다.
- 영향: 구조 검사가 통과해도 최종 고객 문안에 편집자/도구/문서 구조 설명식 잔재가 노출될 위험이 있었다.
- 원인: PDF 최종 추출 본문에 대해 모든 생성 경로에 공통 적용되는 universal semantic gate가 부족했다.
- 재발 방지:
  - `verify.py`의 `gate_pass`에 `customer_meta_clean`, `placeholder_residue_clean`, `style_clean`을 무조건 AND 조건으로 편입했다.
  - 기존 `quality_clean`, `temporal_clean`, `delivery_quality_clean` 의미와 기준은 낮추지 않았다.
  - hit 보고는 `semantic_style_hits`, `ai_meta_hits`, `placeholder_residue_hits`, `role_perspective_hits`처럼 rule/count/page 중심으로 유지하고 본문 문장을 넣지 않는다.
- 검증 근거:
  - clean worktree: `test-project-phase1-verify`
  - semantic focused: 22 passed
  - harness focused: 2 passed, 7 deselected
  - 고객 데이터 접근 0, API 호출 0, PDF 렌더 0, Playwright 실행 0, commit/push 0
- 남은 후속:
  - FOLLOWUP-A: `scripts/hrun.py` RUN_STATE/retry 배선
  - NON_BLOCKING_FOLLOWUP: `scripts/hverify_pdf.py` adapter 확장
  - Phase 2는 운영자 명시 승인 전 금지

## 2026-06-24 추가: QI-2026-06-24-07 도구 우선 조사 없이 직접 진행해 반복 지연

- 증상: 이미 있는 하네스, GitHub Skill, Playwright guard, pytest 진단 순서를 먼저 고정하지 않아 같은 종류의 막힘이 반복되었다.
- 영향: 사용자가 "왜 이렇게 오래 걸리는지", "왜 계속 오류가 나는지"를 물을 정도로 개발 속도와 신뢰가 떨어졌다.
- 원인: 작업 시작 전에 "기존 Skill/MCP/도구로 해결 가능한가"를 체크하는 운영 절차가 문서와 task 템플릿에 없었다. PLAN_VERDICT=BLOCK, API 연결 실패, pytest hang, Playwright sandbox noise를 각각 별도 사건처럼 처리했다.
- 재발 방지:
  - 새 작업은 `docs/17-agent-tooling-runbook.md`의 시작 순서를 먼저 따른다.
  - `handoff/templates/ai_task.md`에 도구/Skill/MCP 사전 확인 항목을 채운다.
  - MCP는 기본 보류한다. 고객 PII, `.env`, `data/`, PDF 산출물이 걸리는 작업은 repo-native 도구와 설치된 Skills가 먼저다.
  - 오류가 나면 같은 명령을 반복하지 말고 runbook의 blocker playbook으로 원인을 먼저 분리한다.
- 연결 커밋/PR: tool-first runbook 도입 PR.
- 다음 세션 검증: 작업 시작 보고에 "사용할 기존 도구/Skill"과 "MCP 사용 여부"가 한 줄로 들어가 있는지 본다.

> 목적: 운영 중 발견한 풀이 품질 사고를 대화방 기억에만 두지 않고, 저장소 안에 남겨 다음 세션과 다른 도구가 같은 실수를 반복하지 않게 한다.
> 이 문서는 고객 원문, 생년월일, 연락처, PDF 전문을 보관하지 않는다. 필요한 경우에도 `P건`, `S건`처럼 최소 식별자만 쓴다.

## 1. 기록 원칙

이 장부는 세 가지 방식을 합쳐서 쓴다.

- Google SRE의 무비난 포스트모템 방식: 증상, 영향, 원인, 재발 방지 조치를 남긴다.
- ADR 방식: 중요한 결정은 맥락, 결정, 결과를 함께 적는다.
- eval 방식: 감으로 좋아졌다고 쓰지 않고, 테스트나 게이트 이름을 붙여 재측정 가능하게 둔다.

참고 자료:

- Google SRE Book, Chapter 15, Postmortem Culture: https://sre.google/sre-book/postmortem-culture/
- Architecture Decision Record 소개와 Nygard 계열 템플릿: https://github.com/architecture-decision-record/architecture-decision-record
- OpenAI Evals 가이드: https://developers.openai.com/api/docs/guides/evals

## 2. 반복 작업 전 필수 루틴

하네스, PDF 생성, 상담 문안, LLM 윤문 작업을 시작하기 전에 다음 파일을 먼저 읽는다.

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.claude/rules/00-immutable.md`
4. `sajugen/STATE.md`
5. `docs/14-tone-spec.md`
6. 이 파일, `docs/16-quality-incident-ledger.md`

작업 전 체크:

- 고객 질문의 핵심 축을 먼저 적는다. 예: 재회, 군복무, 학교 관계, 부동산, 자식복, 위험 시점.
- 고객 원문을 본문에 그대로 밀어 넣지 않는다. 질문 축만 추출한다.
- 원문에 없는 고유명사, 모임명, 지역 비교, 계약 상황을 새로 만들지 않는다.
- 명리 계산과 자미두수 계산은 엔진 결과만 사용한다. LLM은 계산을 만들 수 없다.
- API 윤문은 룰 기반 계산, 질문 축, PDF 게이트가 통과한 뒤에만 한다.
- API 윤문 뒤에도 같은 게이트를 다시 돌린다.

## 3. 사고 장부

### QI-2026-06-23-01: 근거 없는 고객 맥락 삽입

- 증상: 특정 1회성 풀이에서 원문에 없는 모임명과 별칭성 표현이 본문에 들어갔다.
- 영향: 고객이 "이 내용은 어디서 나온 것이냐"고 물을 수 있는 신뢰 사고.
- 원인: 이전 상담 맥락과 현재 질문 맥락의 경계를 코드와 테스트가 충분히 강제하지 못했다.
- 재발 방지:
  - `sajugen/content/delivery_quality.py`의 `context_provenance`로 premium 문서의 기대 맥락과 본문 맥락을 대조한다.
  - `tests/test_delivery_quality.py`에 근거 없는 맥락어를 실패시키는 회귀 테스트를 둔다.
  - 운영 지침: 고객 질문 원문, 운영자가 별도로 준 expected context, 계산 사실 슬롯에 없는 고유 맥락은 쓰지 않는다.
- 연결 커밋/PR: `a4852a3` PR #13, 관련 테스트 `tests/test_delivery_quality.py`.
- 남은 수동 검수: 실고객 메모가 여러 번 이어지는 경우, 이전 상담 맥락을 쓸지 운영자가 명시했는지 확인한다.

### QI-2026-06-23-02: 복합 상담 질문의 핵심 축 누락

- 증상: 복합 질문에서 시기만 크게 잡고, 집, 이사, 지역 비교, 모임 창립, 조력자, 계약 축이 초반 답변에 충분히 반영되지 않았다.
- 영향: 고객 입장에서는 "내가 물어본 것을 제대로 읽지 않았다"고 느낄 수 있다.
- 원인: consult 초반 문장이 질문 전체를 요약하지 않고 대표 축 하나로 좁혀졌다.
- 재발 방지:
  - consult 초반에 질문 축을 안전하게 추출해 반영한다.
  - raw 이름이나 민감 원문은 직접 노출하지 않고, 축 단위로만 쓴다.
  - 관련 묶음 테스트를 통과해야 한다.
- 연결 커밋/PR: `afa5c52` PR #6, `5574772` PR #12.
- 남은 수동 검수: 질문이 세 가지 이상이면 첫 화면에서 모든 핵심 축이 보이는지 읽는다.

### QI-2026-06-23-03: 재회 상담에서 실제 접촉 조건 누락

- 증상: 재회 질문에서 군복무, 학교/전공 선후배, 겹지인이라는 현실 접점이 답변 전략에 충분히 반영되지 않았다.
- 영향: 고객이 원하는 "어떻게 다가가야 하는지"에 비해 답변이 길고 추상적으로 느껴졌다.
- 원인: 재회운을 시기 중심으로만 처리하고, 접촉 가능 경로와 금지 경계를 분리하지 못했다.
- 재발 방지:
  - 군복무, 복무, 입대, 선후배, 학교, 전공, 겹지인 맥락을 관계 답변 축으로 유지한다.
  - 답변은 골라보는 점괘가 아니라, 부담 없는 접점, 금지할 방식, 짧은 첫 문장 예시까지 준다.
  - 상대가 군복무 중이면 답변 지연을 거절로 단정하지 않는다.
- 연결 커밋/PR: `c74600b` PR #7.
- 남은 수동 검수: 연애/재회 질문은 "1년 안의 체감 시기"와 "이번 달 행동"이 분리되어 있는지 본다.

### QI-2026-06-24-01: 부동산/자산/자식복/위험 시점 오분류

- 증상: 땅, 자산, 재산, 자식복, 위험 시점 질문이 대인 중심 축으로 흘렀다.
- 영향: 프리미엄 PDF에서 고객이 가장 궁금한 돈, 자식, 위험 구간 답이 약해졌다.
- 원인: 질문 라우팅과 consult 골격이 자산형 질문의 단어를 충분히 재물/가족/위험 축으로 잡지 못했다.
- 재발 방지:
  - `땅과 자산`, `자식복`, `위험 시점` 축을 질문 분석과 PDF 검증에 반영한다.
  - 땅/토지/자산 질문은 개발 계획, 세금, 명의, 현금화 시점까지 같이 보게 한다.
  - 자식복 질문은 자식의 성패 단정보다 의지, 거리, 간섭 조절을 같이 본다.
- 연결 커밋/PR: `a808136` PR #14, 관련 테스트 `tests/test_llm_sections.py`, `tests/test_delivery_quality.py`.
- 남은 수동 검수: 자산 질문은 "언제 크게 불어나는가"에 대해 대운/세운의 좋은 구간과 조심할 구간이 둘 다 있는지 본다.

### QI-2026-06-24-02: 프리미엄 PDF 말미 저밀도 페이지

- 증상: 프리미엄 PDF 마지막 쪽에 짧은 문단만 남는 저밀도 페이지가 생겼다.
- 영향: 9만원대 상품에서 분량과 완성도가 약해 보인다.
- 원인: HTML/PDF 페이지 나눔에서 말미 단락 고아/과부 처리가 충분하지 않았다.
- 재발 방지:
  - `report.html.j2`에 `orphans:4; widows:4`를 둔다.
  - `render/verify.py`의 `low_density_pages`, `no_orphan` 결과를 확인한다.
  - 프리미엄 PDF는 전체 페이지 수뿐 아니라 말미 밀도를 본다.
- 연결 커밋/PR: `a808136` PR #14, 관련 테스트 `tests/test_render_verify.py`.
- 남은 수동 검수: 최종 PDF는 첫 장, consult 장, 마지막 두 장을 반드시 육안 확인한다.

### QI-2026-06-24-03: "또렷" 계열 반복으로 AI 느낌 발생

- 증상: "또렷하게", "또렷합니다" 계열 표현이 반복되어 AI 문장처럼 보였다.
- 영향: 사람 상담가가 쓴 느낌이 약해지고, 고객 피드백에서 기계적인 인상이 생겼다.
- 원인: 자미/오행 설명에서 같은 표현을 안전한 기본어처럼 반복 사용했다.
- 재발 방지:
  - `style_lint.py`와 `delivery_quality.py`에서 실패/경고 기준을 둔다.
  - 같은 형용사를 반복해 깊이를 만드는 방식은 금지한다.
  - 계산 사실은 분명히 말하되, 표현은 고객 질문의 생활어로 바꾼다.
- 연결 커밋/PR: `6e27806` PR #10, `f83fe49` PR #9.
- 남은 수동 검수: 문서 안에서 같은 단어가 눈에 띄면 API 윤문 전에 룰 문장부터 고친다.

### QI-2026-06-24-04: Playwright sandbox 진단 소음

- 증상: Codex sandbox에서 Playwright subprocess probe가 Windows pipe 생성 문제로 소음성 예외를 냈다.
- 영향: 실제 PDF 로직 문제가 아닌데 작업이 실패처럼 보이고 시간을 낭비했다.
- 원인: sandbox 환경에서 브라우저 subprocess가 막힐 수 있음을 테스트 helper가 먼저 감지하지 못했다.
- 재발 방지:
  - `tests/playwright_guard.py`에서 Codex sandbox를 감지하면 probe를 skip한다.
  - Playwright가 필요한 테스트는 guard 결과를 먼저 확인한다.
- 연결 커밋/PR: `e2060fc` PR #3.
- 남은 수동 검수: PDF 재생성 문제와 sandbox probe 문제를 분리해 보고한다.

### QI-2026-06-24-05: API 윤문 투입 순서 혼동

- 증상: 룰 기반 초안 품질 문제가 남아 있는데 API 윤문으로 해결하려는 흐름이 생겼다.
- 영향: LLM이 계산 사실을 바꿀 수는 없으므로, 질문 축 누락이나 게이트 실패를 덮는 데 쓸 수 없다.
- 원인: PDF 생성, 룰 골격, LLM 윤문, 하네스 검증의 순서가 작업 중에 섞였다.
- 재발 방지:
  - 순서 고정: 계산/질문 축 통과 -> 룰 PDF gate PASS -> API 윤문 -> 동일 gate 재실행 -> 관리자 검수.
  - API 윤문은 말투와 문장 흐름만 다룬다.
  - API 윤문이 새 사실, 새 고유명사, 새 시기를 만들면 실패다.
- 연결 코드: `sajugen/content/llm_polish.py`, `sajugen/content/llm_sections.py`, `scripts/hrun.py`.
- 남은 수동 검수: API 윤문본은 "사실 추가 없음"과 "질문 축 유지"를 별도로 읽는다.

### QI-2026-06-24-06: PS 5.1 UTF-8 no-BOM 파싱 실패

- 증상: PowerShell 5.1에서 `scripts/ai-harness.ps1`의 한글 문자열이 깨져 파서 오류가 났다.
- 영향: 하네스 SelfTest와 DryRun이 환경에 따라 실패했다.
- 원인: PS 5.1은 BOM 없는 스크립트를 ANSI 코드페이지로 읽을 수 있고, UTF-8 한글 바이트가 따옴표 해석을 깨뜨렸다.
- 재발 방지:
  - `scripts/ai-harness.ps1`은 ASCII-only를 유지한다.
  - `tests/test_ai_harness_contract.py`에 ASCII-only 계약 테스트를 둔다.
- 연결 커밋/PR: PR #2 Phase 2A, `tests/test_ai_harness_contract.py`.
- 남은 수동 검수: PowerShell 스크립트에 한글 주석/문자열을 넣지 않는다. 한국어 설명은 문서에 둔다.

### QI-2026-06-24-07: 연애·재회·결혼 답변의 시기 직답 지연

- 증상: 연애·재회·결혼 질문에서 고객이 가장 먼저 알고 싶은 1년 안의 시기, 접근 방식, 멈춤 기준이 뒤로 밀리거나 모호하게 보였다.
- 영향: 고객이 "그래서 언제, 어떻게 해야 하는지"를 바로 잡지 못하고, 위로는 있어도 상담 밀도가 낮게 느껴질 수 있다.
- 원인: 연애 카테고리 안에서 재회, 새 만남, 결혼 축을 한 문단으로 처리해 하위 질문별 행동 기준이 약해졌다.
- 재발 방지:
  - 재회는 연락·접점·멈춤 신호를 초반에 둔다.
  - 새 만남은 소개팅·가벼운 첫 만남·서두름 주의를 초반에 둔다.
  - 결혼은 현재/미래 배우자 기준, 생활 기준, 돈 관리, 가족과의 거리를 초반에 둔다.
  - `delivery_quality.py`에서 유료 연애 축의 근시점, 실사용 행동, 명리·자미 두 관점을 확인한다.
  - `tests/test_llm_sections.py`, `tests/test_delivery_quality.py`, `tests/test_client_tone.py`에 하위 축 회귀를 둔다.
- 연결 커밋/PR: 진행 중.
- 남은 수동 검수: API 윤문 전 룰 본문에서 "좋은 구간/조심할 구간/행동/멈춤"이 앞쪽에 보이는지 먼저 읽는다.

## 4. 새 사고를 추가할 때 템플릿

```
### QI-YYYY-MM-DD-NN: 제목

- 증상:
- 영향:
- 원인:
- 재발 방지:
- 연결 커밋/PR:
- 남은 수동 검수:
```

## 5. 다음 세션용 지시문

새 대화방에서 이어갈 때는 아래처럼 시작한다.

```
현재 저장소 C:\Users\pc\test-project에서 작업한다.
먼저 AGENTS.md, CLAUDE.md, .claude/rules/00-immutable.md, sajugen/STATE.md,
docs/14-tone-spec.md, docs/16-quality-incident-ledger.md를 읽고 시작해라.
계산은 LLM에 맡기지 말고, 고객 질문 축을 먼저 추출해 consult 초반에 반영해라.
PDF 재생성/LLM/API 호출/커밋/푸시는 명시 승인 전 금지다.
오류가 나면 추측하지 말고 관련 코드, 테스트, 공식 문서 또는 검증된 자료를 확인한 뒤 결론을 내라.
```

