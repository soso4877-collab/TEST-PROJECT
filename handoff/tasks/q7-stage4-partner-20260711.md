# [Codex 지시문] Q7 4단계 — 2인 접수·gunghap 모듈 주문화 (2026-07-11 운영자 승인)

> 형식: TASK_PACKET(산문판). 실행 기준 = 이 문서 + 승인 설계 `handoff/codex-q7-stage4-design.md`(A안 ①~⑤).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review(라운드13) + 합성 실렌더 N=5(검증 세션 몫).
> 커밋 = 리뷰 PASS 후 운영자.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·sajugen 런타임 LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역 접근.
- **검색(rg/grep 등) 시 ignored 제외 글롭 필수 — 반드시 `!**/` 프리픽스 형식**:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'` (QI-2026-07-11-01).
- `sajugen/calc/`·`sajugen/input/` 무변경. 가드 완화 금지. 상태머신 전이·APPROVED 발송 차단 무변경(절대규칙 16).
- **수정 범위 한정(예상)**: `sajugen/app.py`(폼·접수 인자)·`sajugen/order_flow.py`(접수·confirm 조건·생성 분기)·
  `sajugen/admin.py`+`admin_detail.html.j2`(옵션 조건·상대 표시)·`sajugen/modules.py`(추천 시그니처만 —
  **R9-1 커버리지·레지스트리 로직 비변경**)·관련 테스트. `integrated.py`·게이트(`delivery_quality`·`verify`)·
  `cli.py`·store 스키마 비수정. 범위 초과 필요 시 정지·보고.
- 테스트 픽스처 PII 0(익명 ID·명백 합성명·합성 생일만). 모순 발견 시 임의 해석 말고 정지·보고.

## 1. 상태(전제) — 2026-07-11 실측
- 브랜치 `codex/gunghap-relationship-quality`, 시작 HEAD = `d71fb35`(Q7 3단계+실렌더 기록 종결, origin 동기).
- 기준선(기준환경): **801 passed / 4 skipped / exit 0**. 감소 = 회귀. 샌드박스 skip 상이 가능.
- **완료(재발주 금지)**: Q7 1~3단계 전체. `build_integrated_full`은 **2인+gunghap을 이미 지원**(CLI 검증) —
  이번 작업은 엔진이 아니라 주문 접수→생성 배선이다. 분량 정책 확정: 무LLM 폴백 발급 N≤2, N≥3 = LLM-on 전제
  (gunghap 포함 조합 승계).
- **운영자 승인(재질의 불요)**: A안(gen_params additive, 스키마 0 변경) / 상대 시진 불명 = 접수 차단 /
  상대 PII는 gen_params 내 본인과 동일 보호 수준·개별 파기는 주문 하드삭제로만 / RELATION+상대 있음 →
  gunghap 추천(없으면 love 유지) / 단일 패킷·라운드13.
- 실측 앵커:
  - `order_flow.py:392` 근방 `create_order` — 1인 접수·시진 불명 차단(3-A)·`gen_params` 저장.
  - `order_flow.py:904` confirm의 gunghap 거부·`admin.py:173` 옵션의 gunghap 제외 — 조건화할 2곳.
  - `_run_integrated_generation` — people 1인 3원소 튜플 하드코딩(2인 확장 지점). receiver_name 파라미터 실존.
  - `modules.py.recommended_modules_for_category(category)` — partner 분기 추가 지점(기본값 하위호환 필수).
  - `models/report.py` `partner_present` — 필드 실존. **2인 주문에서 True로 실소비되는 분기 테스트가 없으면
    팬텀(QI-2026-07-04-01 원조 지점) — 이번에 반드시 고정**.
  - `gunghap.py:940` — 관계 빌더는 사람별 unknown_time 4원소를 지원하나 integrated_full 튜플은 3원소.
    사람별 시진 불명 배선은 범위 밖(접수 차단으로 대신).

## 2. 구현
1. **접수 확장** (`app.py` 폼 + `order_flow.create_order` additive 인자):
   - 폼 선택 필드: 상대 이름·생년월일시·성별·음력/윤달. 상대 birth 미입력 = 기존 1인 접수와 완전 동일
     (**gen_params에 partner 키 자체를 만들지 않는다** — 3-A modules 패턴).
   - 상대 입력 시: 본인과 동일 KASI 정규화(`norm.normalize_date`) 재사용, 정규화 경고를 기존 warnings에
     병합. 정규화된 양력 값만 `gen_params["partner"] = {name·year·month·day·hour·minute·is_male·is_leap}` 저장.
   - fail-closed 2건: (a) integrated_full + 상대 시진 불명(시각 없음) → ValueError·주문 미생성.
     (b) integrated_full 외 상품에 상대 입력 → ValueError·주문 미생성(소비처 없는 데이터 저장 금지, 조용한 무시 금지).
2. **추천 분기** (`modules.py`): `recommended_modules_for_category(category, partner_present: bool = False)` —
   RELATION은 partner_present에 따라 `("gunghap",)` / `("love",)`. 나머지 6종·미등록은 현행 불변.
   기본값 False로 기존 호출 하위호환. 표시 전용(저장 부작용 0) 유지.
3. **admin 조건 분기** (`admin.py`+템플릿): partner 존재 주문이면 모듈 옵션 = 5모듈(gunghap 포함),
   추천 계산에 partner_present 전달. 상세에 상대는 **이름·성별만 표시**(상대 생년월일 원문 비표시 —
   본인과 달리 화면 노출 최소화). 1인 주문 상세는 현행 그대로(회귀 고정).
4. **confirm 조건화** (`order_flow.confirm_module_selection`): gunghap 거부를 "partner 부재 시 거부"로
   변경(메시지에 사유 명시). partner 존재 + gunghap = 정상 확정(정규 순서에 gunghap 포함 저장).
   나머지 검증(NORMALIZED 한정·정규화 위임·audit 모듈 ID만)은 불변.
5. **생성 분기 확장** (`_run_integrated_generation`): `gen_params["partner"]` 존재 시
   people = [본인 3원소, 상대 3원소] + `receiver_name=본인 이름` 명시 전달. `build_integrated_full` 비수정.
   partner 존재 + gunghap 미선택 확정도 허용 — 이때 관계 compose가 호출되지 않음을 테스트로 고정.
6. **partner_present 실소비 고정**: 2인 생성 결과에서 `partner_present=True`가 Report23/가드 경로로
   흐르는 분기 단언(1인=False 대조 포함).

## 3. 수용 기준 (양방)
- (접수) 상대 정상 입력 → `gen_params.partner` 정규화 저장 + 경고 병합. 상대 미입력 → partner 키 부재
  (기존 접수 완전 동일 회귀). 상대 시진 불명 → 주문 미생성. 비integrated_full + 상대 → 주문 미생성.
- (추천) RELATION × partner 유무 2분기 + 기존 6종 불변 표 + 시그니처 하위호환(기존 3-B 테스트 GREEN 유지).
- (admin) partner 주문 = 5모듈 옵션·gunghap 추천 배지 가능, 1인 주문 = 현행 4모듈 회귀. 상세 응답에
  상대 생년월일 원문 0(TestClient 검사).
- (confirm) partner 있음 + gunghap → 확정 성공(정규 순서 포함 저장·audit 모듈 ID만). partner 없음 +
  gunghap → 422 유지(기존 테스트 GREEN). NORMALIZED 한정·잘못된 값 거부 회귀 유지.
- (생성) partner + gunghap 확정 → `build_integrated_full`에 2인 people·receiver=본인 도달(kwargs 캡처)
  + partner_present=True 실소비. partner 있음 + 개인 모듈만 확정 → 관계 compose 미호출.
  1인 주문 생성 경로 무변경 회귀.
- (PII) audit·admin 응답·예외 문자열에 상대 생년월일 원문 0.
- 상태머신 회귀(`tests/test_orders.py`·`tests/test_final_render_gate.py`) GREEN. 전체 pytest exit 0,
  **기준선 801/4 대비 감소 0** + 신규 증가분 명시. calc/input diff 0. 수정 파일 Ruff GREEN.

## 4. 완료 보고 (여기서 멈춤)
실행 명령+출력(passed 수/exit code), diff 요약(파일별), 접수/추천/confirm/생성 양방 증거,
미검증(합성 실렌더 N=5·실브라우저·LLM-on 문안) 명시. **커밋 없이 워킹트리 유지** → 교차리뷰 라운드13.

## 범위 밖
사람별 시진 불명 배선, 상대 PII purge 확장(주문 하드삭제로 커버), integrated_full 후속 지원,
합성 실렌더 N=5(라운드13 검증 세션 몫), 실브라우저 수동 검수, LLM-on 문안, push.
