# [Codex 지시문] 질문 적응 웨이브2 — R6-1 + Q4~Q6 구현 + Q7 설계 게이트

> 형식: 승인된 TASK_PACKET(산문판). 신선 컨텍스트에서 이 문서 + `handoff/codex-question-adaptive-q1-q7.md`(v2, Q4~Q7 개요)만으로 실행 가능.
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = 별도 Claude 세션 /cross-review(라운드7). 커밋 = 리뷰 PASS 후.

## 0. 역할·금지 (웨이브1과 동일)
- Codex 상시 금지: git commit·push·deploy·LLM 호출·PDF 재생성·`harness/profiles/local/**` 열람.
- `sajugen/calc/`·`sajugen/input/` 무변경(골든 불변). 가드 완화·우회 금지 — 게이트 수정은 사각 축소 방향만 + 양방 회귀.
- 실행 단위: **R6-1 → Q4 → Q5 → Q6 구현 + Q7은 설계 1페이지만 작성 후 멈추고 보고**(Q7 구현은 설계 승인 뒤 별도).
- 한국어. PII 0(합성 데이터만). 모순 발견 시 임의 해석 말고 정지·보고(웨이브1 정지 보고가 좋은 선례).

## 1. 상태(전제) — 2026-07-10 실측
- 브랜치 `codex/gunghap-relationship-quality`, 시작 HEAD = `6899bf5`(웨이브1 코드 `6126d7a` + 리뷰·실렌더 기록).
- 기준선(기준환경): **715 passed / 4 skipped / exit 0**. 감소 = 회귀. 샌드박스는 skip 상이 가능 — passed 감소 0 + 신규 증가분 일치가 기준.
- **완료(재발주 금지)**: 웨이브1 Q1~Q3(교차리뷰 라운드6 PASS + 실렌더 검증 — consult 실경로 결함 0).
- 실렌더 실측(참고): 무LLM 궁합 relationship 폴백 = **18p / dense 3540자**. gate_pass=False 원인 = premium_pages(18<30)·premium_text_chars(3540<10000)·veraPDF 7.1-3(기존 잔여, 손대지 않음).
- E10(실명 익명화)은 **별도 패킷** `handoff/codex-pii-anonymize-e10.md` — 이 웨이브에서 실명 관련 작업 금지(중복·충돌 방지).

## 2. 공통 수용 기준
- 전체 pytest exit 0, 기준선 715/4 대비 감소 0. `git diff --name-only -- sajugen/calc sajugen/input` 출력 없음.
- 게이트·상수 변경은 양방 테스트(하한-1 차단 + 하한 통과) 동반. 새 파라미터·컬럼은 소비처 배선+분기 테스트까지 한 단위.
- 불변: 계산 LLM 위임 0 / 3단 가드 / **APPROVED 전 발송 물리차단(상태머신 무변경)** / 예측 보장 표현 0.

---

### R6-1 unbacked_context_terms 주입점 회귀 복원 (소형 — 먼저)
**대상**: `tests/test_delivery_quality.py` (+ 필요시 `sajugen/content/delivery_quality.py` 주석만).
- 웨이브1에서 `_PROVENANCE_CONTEXT_TERMS=()`로 비우며 `unbacked_context_terms` 검사(504-516·652)가 항구 no-op이 되고 차단측 테스트가 소실됨(REVIEW-FEEDBACK 라운드6 ③).
- 복원: monkeypatch로 `_PROVENANCE_CONTEXT_TERMS`에 합성 용어(예: "합성고유명") 주입 → 본문에 그 용어가 있고 concern/expected에 없으면 `unbacked_context_terms` 실패 발생을 단언하는 차단측 테스트 1건 + 기본 상태(빈 튜플)에서 검사가 비활성임을 문서화하는 주석.
- 룰 키 제거는 하지 않는다(운영자 승인 필요 사항 — 주입점 유지가 결정).
**수용**: 신규 테스트 GREEN + 기존 통과측(`test_customer_specific_context_uses_explicit_expected_terms`) 유지.

### Q4 분량 게이트 상품별 차등 (값·매핑 조정)
**대상**: `sajugen/content/delivery_quality.py:19-22`(상수)·`_min_pages`(334 부근)·관측 키(min_* 노출부), `tests/test_delivery_quality.py`.
- `MIN_GUNGHAP_PAGES` 30 → **16**(운영 목표 16~20p의 하한).
- **`MIN_GUNGHAP_TEXT_CHARS` 신설 = 3000** [운영자 확정 필요 — 실렌더 폴백 실측 3540자 근거, 완화가 아니라 상품 정합]. `_min_text_chars(product)` 헬퍼로 premium 10000/gunghap 3000 분기(현 `MIN_PREMIUM_TEXT_CHARS` 전역 적용을 상품 분기로).
- Q5의 후속 상품 키 `followup` 하한 = **10p / 2000자**를 같은 매핑에 추가(소비는 Q5).
- integrated_full 30p/10000자 유지. 관측 필드(min_gunghap_pages 등)에 신설 값 노출.
**수용(양방)**: 상품×경계 표 테스트 — gunghap 15p 차단/16p 통과, gunghap 2999자 차단/3000자 통과, integrated_full 29p 차단(기존 유지), premium 문자 하한 10000 유지. 기존 30p 기준 차단되던 gunghap 18p 케이스의 판정 변화(차단→통과)를 보고에 명시(운영자 승인 근거).

### Q5 재방문 "분량 있는 새 질문 풀이" — 슬림 PDF 경로
**대상**: `sajugen/followup/compose.py`, `sajugen/order_flow.py:263 run_followup`, `sajugen/cli.py:87 gen_followup`, 렌더 재사용(`sajugen/render/` 기존 파이프라인 호출만 — verify 게이트 무변경), `tests/test_followup_*.py`.
- 현행 텍스트 답변 = 기본 유지. **opt-in `--pdf`** 플래그 신설: 저장 Report23 사실(명식 요약·기존 근거 섹션 재사용) + 새 질문 consult 답변(웨이브1 구조 재사용)을 조립해 **10~15p 슬림 PDF** 산출.
- product 키 = `followup`(Q4 하한 10p/2000자 소비). 표준 게이트 파이프라인 경유(render_verify + delivery_quality) — 손편집·게이트 우회 금지.
- 범위 밖 거부(연도·주제, compose.py 123-136)와 allowed_years factcheck 백스톱은 **그대로**(거부되는 질문은 PDF 경로도 거부).
- 새 계산 0(저장 사실만) — followup 원칙 유지. LLM은 기존 backend 주입 구조 그대로(기본 RuleBackend, 실호출 없음).
**수용(양방)**: (통과) 범위 내 질문 `--pdf` → PDF 생성 + consult 직답 게이트 GREEN + followup 하한 충족. (차단) 범위 밖 질문 → 텍스트 경로와 동일 거부(PDF 미생성). (회귀) `--pdf` 없는 기존 텍스트 경로 출력 불변. 렌더 실행이 무거우면 렌더 자체는 모의하고 조립·게이트·하한 판정은 실검사.

### Q6 접수 자동분류 + 운영자 확인 UI
**대상**: `sajugen/order_flow.py:64 create_order`(concern → `question_router.classify` 결과를 Report23 `concern_category`에 저장 — 기존 필드, followup 경로에서 이미 소비 중), `sajugen/admin.py`(상세 뷰 121 `_detail_response`·승인 195 `approve`·신규 카테고리 확정 POST 라우트), 관리자 템플릿, `tests/test_orders.py`·admin 테스트.
- 접수 시 자동분류를 주문 상세에 표시(7종 QuestionCategory) + 운영자 확정/수정 드롭다운(POST → report_json 갱신 + audit_log 기록, `edit_section` 패턴 재사용).
- **GENERAL(전반) 분류 = 저신뢰 취급**: 운영자가 카테고리를 확정하기 전에는 승인 불가 — 기존 `approve`의 `confirm` Form 체크 패턴(195-) 재사용해 물리 차단. concern 자체가 빈 주문은 대상 아님(분류 표시만 "질문 없음").
- 상태머신 전이 규칙 자체는 무변경(승인 전제조건 추가 = 차단 강화, 절대규칙 16 방향과 일치).
**수용(양방)**: (차단) concern 있음+GENERAL+미확정 → approve 409/422. (통과) 운영자 확정 후 approve 정상. (회귀) concern 빈 주문·비GENERAL 주문의 기존 승인 흐름 불변 + `tests/test_orders.py`·`tests/test_final_render_gate.py` GREEN.

### Q7 질문 영역 모듈 조합 — **설계 1페이지만** (구현 금지)
- `sajugen/integrated.py` `_assemble_sections` 일반화(연애/직업/재물/건강/궁합 모듈 선택 조합, 분량=모듈 비례 — Q4 매핑 연동) 설계를 `handoff/codex-q7-design.md` 1페이지로: 모듈 경계·섹션 조립 규칙·게이트 연동·CLI/admin 인터페이스·트레이드오프 2안 비교.
- one-way door 방지 게이트: 설계 승인 전 코드 0줄.

---

## 3. 완료 보고 (여기서 멈춤)
- 실행 명령 + pytest 출력(passed/exit) + diff 요약 + Q4 판정 변화표 + Q7 설계 문서 경로 + 미검증(실렌더 등) 분리 명시. 커밋 없이 워킹트리 유지 → Claude /cross-review 라운드7.

## 범위 밖
Q7 구현, E10(별도 패킷), veraPDF 7.1-3, 상태머신 전이 규칙, 가드 3단, docs/23, push.
