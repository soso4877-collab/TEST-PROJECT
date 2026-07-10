# 구현 상태 기록 — 2026-07-10 질문 적응형 풀이

- E10 인접 탐색: 패킷에 열거되지 않은 `tests/test_relationship_quality_contracts.py` 1줄에서도 대상 이름 잔존을 확인해 tracked 수용 기준에 따라 동일 치환했다.

## 웨이브2 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 현재 HEAD: `fea0e7a` (`Q7 설계 4항목·Q4 문자 하한 운영자 승인 기록`)
- 구현 커밋: `fec5321` (`R6-1 + Q4~Q6 + Q7 설계`)
- 교차리뷰 라운드7 PASS 기록: `a568170`
- 원격 대비: ahead 11. 상태 기록 직전 워킹트리는 깨끗했으며, 이 문서만 현재 세션에서 수정한다.
- 완료 태스크: R6-1, Q4, Q5, Q6 구현. Q7은 승인된 1페이지 설계까지만 완료하고 코드 구현은 하지 않았다.
- 운영자 승인 완료: Q4 문자 하한(gunghap 3000자·followup 2000자), Q7 B안·분량 공식·RELATION 추천·기본 5모듈 전체.

## 웨이브2 완료 내용

- R6-1: `_PROVENANCE_CONTEXT_TERMS=()` 기본 비활성 상태는 유지하면서 합성 용어 monkeypatch로 `unbacked_context_terms` 차단 분기를 고정했다.
- Q4: gunghap 하한을 16쪽/3000자로 분리하고 followup 10쪽/2000자 상품을 추가했다. integrated_full 30쪽/10000자와 premium 10000자는 유지했다.
- Q4: 15쪽·2999자 차단, 16쪽·3000자 통과, 기존 30쪽 하한에서 막히던 18쪽 gunghap 통과를 양방 회귀로 고정했다.
- Q5: `gen-followup --pdf` opt-in 경로를 추가했다. 저장 Report23과 질문 카테고리별 `love/work/health` 근거 장을 재사용하고 새 consult만 조립한다.
- Q5: 연도·주제 범위 밖 질문, 10~15쪽 범위 위반, 저장 일간 부재를 주문 생성 전에 차단한다. 최종 발급도 저장 `bazi` 기반 identity 스펙과 동일 render_verify/delivery_quality를 사용하며 새 계산은 0회다.
- Q5: `--pdf`가 없는 기존 텍스트 주문의 반환·저장 경로는 유지했다.
- Q6: 접수 concern을 7종 QuestionCategory로 자동분류해 주문 메타에 저장하고 관리자 상세에 표시했다.
- Q6: 운영자 확정 POST가 Report23/후속 메타와 audit_log를 갱신한다. concern 있음+GENERAL+미확정 주문은 승인 409, 빈 질문·비GENERAL 주문은 기존 승인 흐름을 유지한다.
- Q6: APPROVED/DELIVERED 상태머신 전이 규칙은 변경하지 않았다.
- Q7: `handoff/codex-q7-design.md`에 모듈 레지스트리 B안, 조립 경계, 분량 공식, 게이트, CLI/admin 계약과 2안 비교를 작성했다. `sajugen/integrated.py` 변경은 0줄이다.

## 웨이브2 구현 파일 전체 목록

- `sajugen/content/delivery_quality.py`: R6-1 주입점 주석, 상품별 페이지·문자 하한, followup 질문 필수 게이트.
- `sajugen/followup/compose.py`: PDF용 저장 섹션 조립, 카테고리별 근거 장 선택, consult 직답·부모 가드 차단.
- `sajugen/order_flow.py`: 후속 PDF 표준 렌더/검증, 저장 일간 identity 복원, 분류 상태·운영자 확정·GENERAL 승인 전제조건.
- `sajugen/cli.py`: `gen-followup --pdf` opt-in 인터페이스.
- `sajugen/admin.py`: 질문 분류 상세 컨텍스트, 확정 POST, 승인 전제조건.
- `sajugen/web_templates/admin_detail.html.j2`: 7종 분류 표시·확정 드롭다운·차단 안내.
- `tests/test_delivery_quality.py`: R6-1 차단 회귀와 Q4 상품별 경계표.
- `tests/test_followup_pdf.py`: PDF 통과/범위 밖/페이지 초과/일간 부재/텍스트 회귀/CLI 배선.
- `tests/test_orders.py`: 접수 자동분류 저장 회귀.
- `tests/test_question_category_admin.py`: GENERAL 차단·운영자 확정·빈 질문/비GENERAL/텍스트 후속 양방 회귀.
- `handoff/codex-q7-design.md`: Q7 승인 전 설계 1페이지.
- `implementation-notes.md`: 현재 웨이브2 상태 기록(이번 사용자 요청으로 추가).

## 기존 잔존 파일과 분리

- `REVIEW-FEEDBACK.md`와 `sajugen/STATE.md`는 구현 파일이 아니라 별도 커밋 `a568170`·`fea0e7a`의 교차리뷰/운영자 승인 기록이다.
- `handoff/codex-question-adaptive-wave2.md`는 시작 HEAD `985031a`에 이미 있던 승인 TASK_PACKET이며 이번 구현 파일이 아니다.
- 웨이브1 Q1~Q3 코드는 커밋 `6126d7a`에 이미 존재했으며 웨이브2에서 재구현하지 않았다.
- `handoff/codex-pii-anonymize-e10.md`와 E10 실명 익명화 대상은 별도 패킷으로 유지했고 웨이브2에서 수정하지 않았다.
- `sajugen/calc/`, `sajugen/input/`, `sajugen/integrated.py`, 상태머신 허용 전이표는 무변경이다.

## 검증 증거

- Codex 샌드박스: `./.venv/Scripts/python.exe -m pytest tests/ -q` -> `701 passed, 31 skipped`, exit 0. 수정 전 688/31 대비 신규 13건 증가, passed 감소 0.
- 기준환경 교차리뷰: 같은 전체 명령 -> `728 passed, 4 skipped`, exit 0. 기준선 715/4 대비 신규 13건 증가, passed 감소 0.
- 기준환경 골든: `pytest -k golden` -> `28 passed`.
- 변경 Python 파일 Ruff -> `All checks passed!`; `py_compile` -> exit 0.
- `git diff --check` -> exit 0(LF→CRLF 안내만).
- `git diff --name-only -- sajugen/calc sajugen/input sajugen/integrated.py` -> 출력 없음.

## 확인하지 못한 것

- 후속 `--pdf`의 실제 10~15쪽 실렌더·조판·다운로드 동선은 미검증이다. 테스트에서는 렌더 엔진을 모의했다.
- 실제 LLM 호출과 LLM-on 문안은 미검증이다.
- Codex는 금지사항에 따라 `harness/profiles/local/**`를 열지 않았고 표준 hrun을 실행하지 않았다.
- 실제 브라우저 수동 UI 검수는 미실행이며 FastAPI TestClient 회귀만 통과했다.

## 남은 위험

- 실제 저장 섹션 길이에 따라 후속 PDF가 15쪽을 넘으면 fail-closed로 차단된다. 운영상 10~15쪽 안에 안정적으로 들어오는지는 승인된 합성 실렌더가 필요하다.
- 저장 `bazi`가 없는 레거시 부모 주문은 identity 게이트를 비활성화하지 않고 후속 PDF를 차단한다. 레거시 처리 정책은 별도 결정이 필요하다.
- admin `action_error` 문구 범용화로 최종 발급 실패 시 “APPROVED 상태 잔류” 안내가 사라진 비블로커가 라운드7에 기록돼 있다.
- Q7 설계는 승인됐지만 구현은 E10 완료 뒤 별도 TASK_PACKET으로 1단계(레지스트리·조립/게이트)와 2단계(CLI/admin)로 나눠야 한다.

## 다음 스텝

1. E10 익명화 패킷을 기준선 `728 passed / 4 skipped`, HEAD `fea0e7a`에서 별도 실행한다.
2. E10 교차리뷰·커밋 뒤 Q7 1단계 구현 패킷을 발주한다.
3. 운영자 승인 시 후속 `--pdf` 합성 실렌더로 실제 페이지 수·조판·게이트를 확인한다.
4. push는 별도 지시 전까지 하지 않는다.

## 웨이브2 세션 종료

Codex 웨이브2 구현·상태 기록 역할을 종료한다. 현재 세션은 `implementation-notes.md`만 미커밋으로 남기고 다음 작업자에게 인계한다.

---

## 웨이브1 기록

## 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 시작·현재 HEAD: `3a30667` (`Q1~Q3 TASK_PACKET v2`)
- 원격 대비: ahead 3. 이번 세션에서 commit·push·deploy 없음.
- 완료 태스크: Q1 관계 consult 이식, Q2 질문별 풀이 분기·실행 경로 PII 제거, Q3 관계 질문축 직답 게이트 강화·고유 키워드 일반화.
- Q4~Q7은 미착수. 패킷 지시대로 웨이브1에서 중단.

## 완료 내용

- Q1: relationship 섹션을 `overview -> consult -> intent` 순서로 조립한다. 빈 질문은 consult를 생략하고 `skipped=True`로 구분한다.
- Q1: 질문 분류를 context·폴백·LLM 작성 방향이 실제 소비한다. consult 원문은 생년월일·시각·출생지 마스킹 뒤 격리 인용한다.
- Q1: consult 후보는 compose 단계에서 검사하고 최대 2회 재작성한다. 모든 후처리 뒤 최종 직답 하드 게이트를 다시 적용한다.
- Q2: 초기 관계·장기/결혼·가족 조율·재회·일반 관계의 5개 결정론 분기를 추가했다. situation에 따라 폴백과 앞부분 요약이 실제로 달라진다.
- Q2: `gunghap.py`에서 재할당으로 죽어 있던 로컬 relationship 구현을 삭제했다. 살아있는 business 시스템 프롬프트·가이드·도크스트링의 타 고객 PII도 합성 예시 또는 일반 서술로 교체했다.
- Q3: 부모 동의·결혼 이행·장기 관계 축을 추가했다. consult는 감지된 질문축 중 하나가 아니라 각 축의 직접 근거를 모두 포함해야 통과한다.
- Q3: 지역 비교·모임/단체·도움을 주는 사람을 일반 트리거로 바꾸고 고객별 고유 키워드 상수를 제거했다.

## 이번 구현 파일

- `sajugen/relationship/context.py`: consult 슬롯, 질문 분류·축·5개 풀이 기준.
- `sajugen/relationship/fallback.py`: 질문별 consult 골격, 겹침축 보강, 앞부분 요약·중립 필러.
- `sajugen/gunghap.py`: 죽은 코드 삭제, PII 제거, 마스킹 인용, LLM 재작성, 최종 consult 게이트.
- `sajugen/content/delivery_quality.py`: 신규 3축과 축별 전수 evidence 판정.
- `sajugen/content/rules.py`: 지역·모임·조력자 일반화.
- `tests/test_question_adaptive_relationship.py`: Q1~Q2 통합·양방·겹침축 신규 회귀.
- `tests/test_delivery_quality.py`: Q3 차단/통과·동치류·기존 축 회귀.
- `tests/test_gunghap.py`: 빈 질문 consult 생략에 맞춘 이웃 회귀.
- `tests/test_llm_sections.py`: 일반화한 합성 맥락 회귀.
- `implementation-notes.md`: 이번 상태 기록.

## 기존 잔존 파일 구분

- 세션 시작 시 워킹트리는 깨끗했다. 위 구현 파일 외 기존 미커밋·미추적 파일은 없었다.
- HEAD에 이미 있던 패킷·설계·리뷰 기록은 이번 세션에서 수정하지 않았다.
- `sajugen/calc/`·`sajugen/input/`은 무변경이다.
- 기존 테스트 픽스처·주석·도크스트링의 PII 전수 익명화는 E10 별도 패킷 범위라 이번 세션에서 건드리지 않았다.

## 검증 증거

- `./.venv/Scripts/python.exe -m pytest tests/ -q` -> `688 passed, 31 skipped`, exit 0.
- 이 샌드박스 직전 기준 `668 passed, 31 skipped` 대비 신규 테스트 20개만 증가, passed 감소 0.
- 기준환경 기준선 `695 passed, 4 skipped`에 대한 예상값은 `715 passed, 4 skipped`; 기준환경 직접 실행은 미완료.
- 관계·질문 적응 관련 대상 테스트 -> 71 passed, exit 0.
- 최초 전체 실행에서 3건 실패를 확인한 뒤 각각 다른 원인으로 수정; 실패 3건 단독 재검증 -> 3 passed, 최종 전체 GREEN.
- Q2 파일 한정 PII 스윕 -> 0건.
- Q3 파일 한정 고객 고유 키워드 스윕 -> 0건.
- `git diff --name-only -- sajugen/calc sajugen/input` -> 출력 없음.
- `git diff --check` -> exit 0. 기존 LF/CRLF 경고만 있음.
- 변경 파일 Ruff 검사(`rules.py` 제외) -> `All checks passed!`.
- 전체 Ruff는 `rules.py`의 이번 diff 밖 기존 오류 17건 때문에 미통과.

## 확인하지 못한 것

- 실렌더 미검증.
- 실제 LLM 호출 미검증. 테스트는 모의 Anthropic 모듈만 사용했다.
- PDF 재생성·`harness/profiles/local/**` 열람·표준 hrun 미실행.
- 기준환경의 `715 passed / 4 skipped` 기대값 미검증.

## 남은 위험

- 실제 LLM 문안과 PDF 조판에서 질문 직답성과 분량이 유지되는지는 신선 컨텍스트 교차리뷰와 합성 실렌더로 확인해야 한다.
- 장기 관계 축은 승인 동치류인 `3년`, `몇 년`, `오래 만난`, `장기`, `오랜 연애`만 자동 분류한다. 다른 숫자 연도 단독 표현은 현재 범위 밖이다.
- 저장소 이력과 기존 테스트 픽스처의 PII 전수 익명화는 E10에서 별도 처리해야 한다.

## 다음 스텝

1. Claude 신선 컨텍스트 `/cross-review`에서 diff와 기준환경 전체 pytest를 검증한다.
2. 합성 실질문으로 표준 실렌더를 실행해 consult 위치·문안·게이트·조판을 확인한다.
3. 교차리뷰 PASS 후 운영자가 웨이브1을 커밋한다.
4. 이후 E10 익명화 패킷을 별도 발주하고, Q4~Q7은 재승인 전 착수하지 않는다.

## 세션 종료

Codex 구현 세션 역할을 종료한다. 워킹트리는 커밋하지 않은 상태로 교차리뷰에 인계한다.
