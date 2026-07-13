# TASK_PACKET — 생시 미상 삼주 풀이·12지지 민감도·출처 게이트 전환

- task_id: `beta-2-unknown-time-three-pillar-20260712`
- base_commit: `084e04c95fc3d72757771b0a39d3dd7b85a2470e`
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰 + Codex 신선 read-only 검증
- 상태: `implementing`

## 0. 우선순위·금지 경계

- 이 태스크는 운영자가 기존 `beta-1-hverify-module-contract-20260712`보다 우선하도록 승인했다.
- 보류 태스크 패킷 `handoff/tasks/beta-1-hverify-module-contract-20260712.md`는 수정하지 않는다.
  시작 SHA-256은 `b981a99642ed47ca9c78c85733af5d114fd9e872acbb65efd905570754a05819`이며,
  이 태스크 종결 뒤 새 HEAD 기준으로 재검토한다.
- 고객 데이터·기존/신규 고객 PDF·`harness/profiles/local/**`·`.env`·secrets·ignored 산출물을
  읽거나 수정하지 않는다. 합성 입력만 사용한다.
- Anthropic API·PDF 생성/재생성·hsweep·APPROVED·발송·commit·push·main 전진 금지.
- 이름·생년월일·질문 원문·본문 전문을 코드·로그·테스트·문서·채팅에 넣지 않는다.
- 검색 시 `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**'
  --glob '!**/data/**'`를 적용한다.
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만 사용한다.

## 1. 확정 정책

1. 공개·내부 계약은 `birth_time_mode = known | three_pillar`다. 기존
   `unknown_time=True`는 호환 입력으로 받아 `three_pillar`로 정규화한다.
2. 생시 미상은 신고된 민간 날짜의 연·월·일 세 기둥을 정본으로 사용한다. 정오를 실제 출생시각처럼
   저장하거나 고객 결과에 노출하지 않는다.
3. 입춘 또는 절입 경계가 신고 날짜 안에 있어 시각 없이는 연주/월주를 하나로 확정할 수 없으면
   임의 선택하지 않고 `NEEDS_INFO_TIME_BOUNDARY`로 fail-closed한다.
4. 연·월·일은 고정한 채 12개 시지 후보를 내부 계산한다. 12/12에서 구조화 값이 완전히 같은 사실만
   `time_invariant`로 승격한다. 11/12 이하 또는 일부 필드만 같은 값은 전부 억제한다.
5. 생시 미상에서는 자미두수 계산을 호출하지 않는다. 시주·시주 십성/신살·궁/별·진태양시 보정·정오
   추정값을 콘텐츠·LLM·PDF·검수 편집 경로에 제공하지 않는다.
6. 불안정한 신강/신약·용신·오행 순위·대운 시작/현재 대운 등은 v1에서 범위로 제시하지 않고 생략한다.
7. 고객 원국 표는 연주·월주·일주 3열만 렌더한다. 고지 문구는 다음 문자열과 정확히 같다.

   `출생시각이 확인되지 않아 연·월·일 세 기둥을 기준으로 풀이했습니다. 시간에 따라 달라지는 세부 해석은 제외했습니다.`

8. `생시가 확인되면 다시 살펴보라`는 식의 재검토·업셀 문구는 제거한다.
9. 생시가 알려진 기존 경로의 계산·콘텐츠·PDF·게이트 결과는 바이트/골든 기준 비악화한다.

## 2. 계산·출처 계약

- `birth_time_mode`를 단일 정규화 함수/enum으로 관리하고 팬텀 boolean 분기를 만들지 않는다.
- 삼주 계산 결과에는 최소 다음 PII-free 메타를 둔다.
  - `three_pillar_schema_version = 1`
  - `candidate_count = 12`
  - 결정론적 `candidate_digest`
  - `stable_fact_ids`
  - `suppressed_fact_ids`
- 후보별 원시 값과 후보별 산문은 영속·로그·LLM 입력에 넣지 않는다.
- LLM에 제공 가능한 출처는 `three_pillar`, `time_invariant`, `calendar_flow`뿐이다.
- `three_pillar`의 기본 사실은 연·월·일, 일간, 월령 기반 격국, 알려진 세 기둥의 십성/신살이다.
  후보 기반 파생 사실은 12개 전체 구조화 값 동일 검사를 통과한 것만 추가한다.
- 기존 `SajuResult`/`Myeongni`의 known-time 계약을 깨뜨리지 않도록 삼주 결과를 명시적 타입/필드로
  표현한다. 빈 시주를 정상 시주 객체처럼 위장하지 않는다.

## 3. 저장·주문·레거시 계약

- `three_pillar` 주문에는 실제 출생시각 필드로 `hour=12`, `minute=0`을 저장하지 않는다.
- 주문/콘텐츠 메타에 §2 출처 메타를 저장하고 최종 렌더/검수에서 재확인한다.
- 과거 `unknown_time` 주문에 새 출처 메타가 없으면 기존 정오 결과를 조용히 재사용하지 않고
  최종 발행을 차단하여 재생성을 요구한다.
- 생시 미상 주문은 자미 관련 계산·섹션을 생성하지 않으며, 단순히 섹션 ID만 나중에 삭제하는 방식은
  수용하지 않는다.
- 현재 고객 주문/상태 DB는 이번 코드 구현에서 수정하지 않는다.

## 4. 콘텐츠·PDF·LLM 계약

- 표지에는 날짜와 정확 고지만 표시하고 추정 시각·진태양시·보정 분수는 표시하지 않는다.
- 원국 차트는 3열이며 시주 행/열/텍스트를 만들지 않는다. 본문·목차·부록도 동일 정책을 따른다.
- 룰 골격은 시주·자미·불안정 파생 사실을 참조하지 않으며, 삼주 전용 문장은 쉬운 설명을 유지한다.
- `ReportContext`, fact allowlist, compose slot에는 허용 출처의 사실만 들어간다.
- known-time용 4주/자미 문맥은 변경하지 않는다.

## 5. 하드 게이트

- 새 키 `unknown_time_provenance_clean`을 기존 `GATE_KEYS`에 추가하고 제거/완화 없이 최종
  `gate_pass`에 포함한다.
- `three_pillar`일 때 cover·toc·본문·appendix·admin 편집·최종 렌더 전 경로를 모두 검사한다.
- 최소 차단 대상: 실제/추정 시각, 정오·진태양시·보정 분수, 시주 값/해석, `네 기둥`, `사주팔자`,
  자미두수·궁·별, 허용 출처에 없는 LLM 사실.
- finding에는 PII/원문을 넣지 않고 rule/token/count/page/source만 기록한다.
- known-time 경로는 같은 게이트에서 정상 통과해야 한다.

## 6. 필수 양방·경계 테스트

1. known-time 골든/기존 결과 비악화 및 자미 계산 유지.
2. three-pillar는 자미 계산 함수를 호출하지 않음(monkeypatch 호출 차단 증명).
3. 생시 미상 주문 저장값에 실제 `hour`/`minute` 없음 + 호환 `unknown_time=True` 정규화.
4. 신고 날짜 연·월·일 고정 + 12개 후보 수/digest 결정론.
5. 12/12 동일 구조화 사실은 승격, 11/12 동일은 억제.
6. 입춘/절입 당일 모호성 `NEEDS_INFO_TIME_BOUNDARY` 차단과 비경계 날짜 통과.
7. 3열 원국·정확 고지·시각/자미/업셀 문구 0.
8. LLM 캡처 입력에 허용 출처만 있고 시주/자미/후보 원시 값 0.
9. cover·본문·appendix 각각 금지 사실 합성 주입 시
   `unknown_time_provenance_clean=False`, `gate_pass=False`; 정상 삼주 문안은 통과.
10. admin 편집 금지 사실 주입 차단, 최종 발행 재검증 차단.
11. 새 provenance가 없는 레거시 unknown 주문 최종 발행 차단.
12. known-time 주문은 새 게이트에 의한 오탐 0.

경계 인접으로 `candidate_count=0/11/13`, 잘못된 schema version, 빈 stable ID, 후보 순서 변화,
날짜 경계 전후, `사주`의 정상 일반 용법과 `사주팔자` 금지 용법을 각각 고정한다.

## 7. 예상 수정 범위

- 정책/계산: `sajugen/calc/**`, `sajugen/input/**`, `sajugen/engine.py`, 관련 모델
- 주문/파이프라인: `sajugen/order_flow.py`, `sajugen/pipeline.py`, 필요한 저장/상태 검증 경로
- 콘텐츠/LLM: `sajugen/content/**`, `sajugen/integrated.py`
- 렌더/게이트: `sajugen/render/**`, 필요한 admin 최종 발행 경로
- 테스트: 관련 기존 테스트 + 삼주 계약 전용 신규 테스트
- 문서: `.claude/rules/00-immutable.md`, `.claude/rules/calc.md`, `.claude/rules/content.md`,
  `docs/03-engine-validation-plan.md`, `docs/07-safety-and-compliance.md`, `docs/16-quality-incident-ledger.md`,
  `docs/20-gate-coverage.md`, `docs/22-*.md`, `docs/23-beta-operation.md`

실제 diff는 필요한 최소 파일로 수렴한다. 기존 hverify 패킷과 고객/ignored 파일은 수정 금지다.

## 8. 검증·완료 기준

- 전체: `.\.venv\Scripts\python.exe -m pytest tests\ -q` exit 0, 기준선
  `949 passed / 4 skipped` 대비 기존 passed 감소 0 + 신규 테스트 증가.
- 골든: `.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden` = 기존 28 passed 유지.
- 변경 Python 전부 Ruff·py_compile GREEN, `git diff --check` exit 0.
- calc/input 변경이므로 삼주 신규 골든과 기존 known-time 골든을 함께 확인한다.
- API 호출·PDF 생성은 0. PDF 레이아웃의 실제 300dpi 육안 검증은 코드 PASS 뒤 별도 승인된
  합성/새 replacement 생성 단계로 승계하며 이번 CODE_PASS에 포함하지 않는다.
- 구현 완료 시 `implementation-notes.md`와 `sajugen/STATE.md`를 갱신하고 manifest를
  `review_requested/next_actor=claude`로 기록한다. commit/push는 운영자 별도 승인 전 금지다.

## 9. 후속 순서

1. Claude 신선 컨텍스트가 packet 대비 diff 전량 + 기준환경 테스트를 교차리뷰한다.
2. PASS 뒤 Codex 신선 read-only 검증자가 SHA·게이트 배선·테스트 수만 독립 확인한다.
3. 운영자 별도 과금 승인 후에만 현재 보류 고객을 새 주문으로 1회 재생성한다.
4. 표준 게이트·hrun·hsweep·300dpi 시각 점검·운영자 전문 검수 Z=0 뒤에만 APPROVED/수동 발송한다.
5. 그 뒤 보류된 hverify 모듈 패킷을 새 HEAD 기준으로 재검토한다.
