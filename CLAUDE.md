# sajugen — 사주(명리 메인) + 자미두수(보완) 종합형 PDF 리포트 생성기

운영자 1인 내부 도구. 입력(생년월일시·출생지·고민) -> 진태양시 보정 -> 명리+자미 결정론 계산
-> 27섹션 룰 NLG + 부분 LLM(공식 API 4구간) -> 3단 가드 -> tagged PDF -> 관리자 검수 후 수동 발송.

## SSOT 체인 (작업 시작 전 반드시 이 순서로 참조)
1. `sajugen/STATE.md` — 진행 상태 (세션 시작/압축 시 훅이 자동 주입)
2. `docs/03-engine-validation-plan.md` — 유파·정책 결정표 (자시/윤달/연경계/사화표/상충 처리)
3. `docs/06-llm-usage-policy.md` — LLM 허용/금지 구간
4. `docs/09-roadmap.md` — Phase 로드맵과 완료 기준
5. 절대 규칙 상세: `.claude/rules/00-immutable.md` (항상 로드됨)

## 스택 (확정 — 임의 변경 금지)
- Python 올인: lunar-python 1.4.8 고정 / iztro-py / Skyfield(de440s.bsp, 절기) / KASI 캐시(3원 교차)
- Jinja2 + Playwright Chromium tagged PDF / veraPDF(포터블 Java 21, 측정만·빌드 불차단)
- FastAPI + SQLite(주문·검수) / pydantic + Instructor / LLM = Anthropic 공식 API만

## 실행/테스트 명령
- 테스트:
  `./.venv/Scripts/python.exe -m pytest tests/test_p1.py tests/test_p2.py tests/test_p3.py tests/test_p4.py tests/test_p5.py tests/test_kasi.py tests/test_normalize.py tests/test_ziwei_parity.py tests/test_orders.py tests/test_shinsal.py tests/test_golden_sweep.py`
- CLI: `./.venv/Scripts/python.exe -m sajugen.cli --birth "1990-05-20 14:30" --gender 남 --horoscope 2026-06-01 --out x.pdf`
- 웹폼: `./.venv/Scripts/python.exe -m uvicorn sajugen.app:app --host 127.0.0.1 --port 8765`
- 산출 PDF: `sajugen/render/out/`

## 절대 규칙 요약 (상세·근거는 .claude/rules/00-immutable.md)
- 계산은 LLM에게 절대 위임 금지. 전체 PDF 원샷 LLM 생성 금지. 헤드리스 웹 UI 자동화 금지.
- APPROVED(관리자 승인) 전 발송 금지. 가드(safe_lint/factcheck/trace) 우회·완화 금지.
- 음력 변환 1차 기준 = KASI. 자미 윤달 = 15일 분할법. 자시 기본 = JST_2300.
- 통합 해석은 명리가 최종 권위, 자미는 12궁 영역 서술 한정. 예측 정확도 주장 전면 금지.
- 계산 코드(calc/, input/) 수정 시 테스트 동반 + 골든 케이스 회귀 필수.
- 검증하지 않은 것을 "완료/정확"이라고 단정 보고 금지 (사용자 2회 교정 이력).

## Compact Instructions (컨텍스트 압축 시 보존 지시)
- 압축 시 반드시 보존: 현재 진행 중인 Phase와 다음 단계, 이번 세션에서 수정한 파일 목록, 테스트 실행 명령과 마지막 테스트 결과(PASS/FAIL 수), 미해결 블로커(예: KASI 키 대기).

## 환경 규칙
- 터미널 응답은 평문 위주 (이모지/장식 특수기호 금지 — cp949·xterm.js 한글 렌더 이슈 이력).
- Bash 도구로 PowerShell/cmd 실행 금지. 파일 탐색은 Read/Glob/Grep 사용.
- 한 번에 한 작업(Phase 단위), 각 Phase 완료 시 STATE.md 갱신 + pytest 전체 GREEN 확인.
- 커밋 메시지·주석·문서는 한국어. 푸시는 사용자 지시가 있을 때만.

## Git 컨벤션 (2026-06-13 확정 — 솔로 내부도구, GitHub Flow/트렁크 기반)
- 브랜치 모델: `main` = 항상 GREEN인 안정 베이스라인(복구·발송 기준점). `feat/...` = 활성 작업.
  Phase 완료 + pytest 전체 GREEN 시점에만 `main`을 feat로 fast-forward 전진(머지 커밋 없이 선형 유지).
- 커밋 단위: 논리적 1변경 = 1커밋. 한국어 Conventional Commit.
  type 매핑 — 기능=feat / 버그=fix / 문서·STATE=docs / 테스트=test / 잡무=chore / 성능=perf.
- 커밋 시점: 의미 있는 작업 경계(서브태스크/Phase)마다. 커밋 전 항상 pytest GREEN.
  계산(calc/, input/) 수정은 같은 커밋에 테스트 + 골든 회귀 동반(절대규칙 20).
- 푸시 시점: 어시스턴트(claude)는 사용자 지시가 있을 때만 push(절대 자동 push 금지).
  운영자는 유실 방어를 위해 매 작업 세션/Phase 종료 시 feat를 push 권장. main을 전진시킨 회차엔 main도 push.
- 커밋 안전: `.env`·`data/`(KASI)·`sajugen/tools/`(288MB)·`render/out/` 등은 .gitignore로 격리됨.
  커밋 훅(block-env-commit.js·pre-commit-security.js)이 비밀정보 커밋을 이중 차단.
- 원격: `origin` = github.com/soso4877-collab/TEST-PROJECT (단일 운영자).
