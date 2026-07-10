# 구현 상태 기록 — 2026-07-10 질문 적응형 풀이 웨이브1

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
