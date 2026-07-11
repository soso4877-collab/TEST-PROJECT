# [Codex 지시문] Q7 잔여 — 동명 given 커플 접수 차단 (2026-07-11 운영자 승인)

> 형식: TASK_PACKET(산문판, 소형). 실행 기준 = 이 문서 + `REVIEW-FEEDBACK.md` 라운드13 ③-정정 절.
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review(라운드14). 커밋 = 리뷰 PASS 후 운영자.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·sajugen 런타임 LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역 접근.
- **검색(rg/grep 등) 시 ignored 제외 글롭 필수 — 반드시 `!**/` 프리픽스**:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'` (QI-2026-07-11-01).
- **수정 범위 한정**: `sajugen/order_flow.py`(create_order 검증 1지점) + 관련 테스트 1~2파일. 그 외
  (app.py·admin·gunghap.py·client_tone_lint.py·modules.py·게이트·calc/input) 비수정. 범위 초과 시 정지·보고.
- 가드 완화 금지·상태머신 무변경. 테스트 픽스처 PII 0(공인 합성명만).

## 1. 상태(전제) — 2026-07-11 실측
- 브랜치 `codex/gunghap-relationship-quality`, 시작 HEAD = `6105ed9`(R13-1 정정 기록, origin 동기).
- 기준선(기준환경): **820 passed / 4 skipped / exit 0**. 감소 = 회귀.
- **배경(R13-1 정정)**: 수신자/상대의 성 제외 이름(given)이 동일한 2인 주문은 호칭 변환
  (`gunghap.py:583` — 정상 로직)이 두 사람을 구분할 수 없어 role/honorific 게이트가 발급을 차단한다
  (fail-closed — 유출 0, 단 생성 단계 원인 불명 실패로 보임). given 상이 쌍은 무LLM N=5 전 게이트 clean
  실측 완료. **이번 작업 = 이 엣지를 접수 시점의 명확한 차단으로 앞당기는 것**(호칭 로직 개선 아님 — 기각됨).
- 실측 앵커: `client_tone_lint.py:273 given_name(full)` — 성 제외 이름 추출의 단일 소스(재사용, 복제 금지).
  `order_flow.create_order`의 partner 검증 블록(4단계 — 상대 시진 불명 차단과 같은 위치가 자연스러움).
  app.py는 create_order의 ValueError를 이미 422로 변환(3-A 배선) — 수정 불필요.

## 2. 구현 (v2 정정 2026-07-11 — Codex 정지 보고 타당, 외자 경계 요구 폐기)
**충돌 술어 = strip 후 `given_name(name) == given_name(partner_name)`** — 근거: 호칭 생성(gunghap.py:570·
587·617)과 게이트 스펙(`client_tone_lint.role_perspective_specs:655`)이 **같은 `given_name()`을 쓴다**.
따라서 이 함수의 출력이 다르면 본문 호칭·게이트 별칭이 서로 구분되어 충돌이 발생하지 않는다.
2자 이하 이름은 `given_name`이 풀네임을 그대로 반환하므로(예: 김민→"김민") **외자 상이 성 쌍(김민/이민)은
충돌하지 않는 정상 접수 대상**이다 — v1의 "외자 given 1자 충돌 차단" 요구는 시스템 실태와 불일치해 폐기한다.
`create_order`에서 integrated_full + partner 존재 시 위 술어가 참이면 ValueError로 주문 미생성.
메시지는 원인 안내형이며 **이름 원문·생년월일 비전재**. `client_tone_lint.py` 수정·로직 복제 금지
(함수 재사용만). 기존 상품·1인 주문은 무변경.

## 3. 수용 기준 (양방, v2)
- (차단) 3자 동given(김민준/이민준) → 주문 미생성 + 메시지에 이름 원문 0. 완전 동명(김민준/김민준) → 차단.
  공백 차이("이민준 ") → strip 후 차단. 2자 완전 동명(김민/김민) → 차단.
  교차 케이스(민준/김민준 — 2자 풀네임 == 3자 given) → 차단.
- (통과) **외자 상이 성 쌍(김민/이민) → 정상 접수**(호칭·게이트가 풀네임으로 구분 — 술어의 존재 이유를
  증명하는 경계). given 상이 일반 쌍(김민준/이서연) 정상 접수 회귀 + 1인 접수·기존 상품 무변경 회귀 +
  기존 4단계 테스트 GREEN 유지.
- 커버 안 함(사유 명시): 4자 이상 비정형 이름의 별칭 교차 — `given_name`이 원형을 유지하는 영역으로
  술어 밖이며, 발생 시 기존 role/honorific 게이트가 최종 방어한다(fail-closed).
- 전체 pytest exit 0, **기준선 820/4 대비 감소 0** + 신규 증가분 명시. calc/input diff 0. Ruff GREEN.

## 4. 완료 보고 (여기서 멈춤)
실행 명령+출력, diff 요약, 차단/통과 양방 증거. **커밋 없이 워킹트리 유지** → 교차리뷰 라운드14.

## 범위 밖
호칭 로직의 동명 처리 개선(기각 — B-8), admin 사전 안내 UI, 실렌더, push.
