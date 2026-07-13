# TASK_PACKET — 하네스 프로파일 모듈 계약 배선 (HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP 종결)

- task_id: `beta-1-hverify-module-contract-20260712`
- base_commit: `084e04c` (HEAD, working tree clean 실측 2026-07-12)
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰
- 상태: `planned`

## 0. 역할·금지 경계 (YOU MUST)

- 수정 허용은 §5 예상 범위의 하네스 코드·테스트·계약 문서뿐이다. **제품 코드(`sajugen/**`)와
  `sajugen/calc/**`·`sajugen/input/**`는 수정 금지.**
- Anthropic API·PDF 재생성·두 번째 replacement·hsweep·APPROVED·발송·commit·push 전부 금지.
- `.env`·secrets·고객/ignored 산출물 비열람. `harness/profiles/local/**`는 열람 금지 —
  로컬 프로파일 실측이 필요하면 존재/ignored 여부만 확인한다.
- 검색(rg 등)은 ignored 영역 제외 글롭 필수:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
- 이름·생년월일·출생시각·질문 원문을 stdout·로그·테스트 픽스처·커밋에 넣지 않는다. 테스트는
  합성 데이터만 사용한다(PII 0).
- 모든 실행은 `.\.venv\Scripts\python.exe -m ...`(bare python/pytest 금지).

## 1. 상태(전제) — 실측 근거

- 라운드17까지 종결: register/외부조언 게이트·`일정(?!한|하게|하지)` 경계 배선 완료, 기준선
  **949 passed / 4 skipped / exit 0**(hrun 2회 재확인, `pytest.returncode=0`).
- Phase C replacement 완료(파이프라인 정확 1회, 재실행 금지): 주문 `ord_19f55b6b8f8becf6ba0`
  = DRAFTED, 인라인 verify **gate_pass=True·실패 키 0·29p**, PDF SHA256
  `63383335e830bd04681ccd655bc300098779e204e79b6ce925f989b12e5704d0`. 이 PDF는 검수 후보로
  유지하며 재생성하지 않는다.
- **판정 HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP**: hrun/hverify 프로파일 경로가
  `selected_modules`를 선언·전달할 수단이 없어 4모듈 주문(하한 28p, 런타임 실측
  `module_minimums([love,job,wealth,health])=(28, 9000)`)을 기본 5모듈 스펙
  (`module_minimums(None)=(30, 10000)`)으로 판정 → 유일 실패 `premium_pages: 29 < 30`.
  나머지 게이트 키 전부 GREEN(register_hard=0·external_advice=0). 방법론 A-5 "팬텀 파라미터"
  클래스: `V.verify(selected_modules=...)` 파라미터가 프로파일 경계에서 소비되지 않았다.
- 부수 관측 갭: hrun summary에 `pytest.skipped`가 null — `949 passed / 4 skipped`가 요약
  파일 자체에 보존되지 않는다.

## 2. 목표

하네스 프로파일의 모듈 계약을 검증(hverify)·재생성 명령 구성(hrun)·요약(hsummary)까지
**원자적으로** 배선한다. 부분 배선(예: hverify만)은 이 패킷의 수용 기준 미달이다.

## 3. 필수 계약 (전부 충족 — 부분 구현 반려)

1. 외부 프로파일 정본 키는 제품·CLI와 같은 **`modules`**로 한다(내부 verify 인자명은 기존
   `selected_modules` 유지).
2. hverify_pdf 경계에서 다음 3개를 **함께** `V.verify`로 전달한다:
   `selected_modules = profile.modules` · `module_sections` · `premerge_section_ids`.
3. `modules`가 명시됐는데 `module_sections` 또는 `premerge_section_ids`가 빠지면 레거시
   5모듈 맵으로 **조용히 보정하지 말고 fail-closed**한다(명시적 오류·검증 실패).
4. `module_schema_version`도 현재 스키마와 일치하는지 검증한다(불일치 = fail-closed).
5. `modules` 미지정 레거시 프로파일은 기존 5모듈/30쪽 동작을 그대로 유지한다(회귀 0).
6. 실제 replacement용 `module_sections`/`premerge_section_ids` 증거는 임의 생성하지 말고
   **저장 주문의 PII-free render/module 메타에서 가져온다**(주문 meta의 모듈/섹션 ID만 —
   본문·PII 비접촉).
7. hrun.py의 regen 명령 구성에도 `modules`를 반복 `--module` 인자로 전달한다.
   **이번 작업에서 실제 regen/API는 실행하지 않고 명령 구성(argv) 테스트만 한다.**
8. hsummary에 PII 없는 관측값 4종을 남긴다: `selected_modules` ·
   `module_schema_version` · `minimum_pages` · `minimum_text_chars`.
9. hrun summary의 `pytest.skipped` null 갭을 수정해 passed·skipped가 모두 요약 파일에
   보존되게 한다.

## 4. 필수 양방 테스트 (같은 커밋 동반 — 한쪽만 있으면 반려)

- 4모듈 + 일치하는 커버리지 증거: 29쪽 / `minimum_pages=28` / `gate_pass=True`.
- `modules` 미지정 레거시: 29쪽 / `minimum_pages=30` / `premium_pages` 실패 유지.
- 4모듈인데 gunghap 섹션이 섞인 경우: `unexpected_module_sections`로 차단.
- `modules`만 있고 커버리지 증거(module_sections/premerge)가 빠진 경우: fail-closed.
- regen 명령 구성: `--module love --module job --module wealth --module health` 전달.
- `modules` 미지정 regen 명령: `--module` 플래그 없음.
- pytest 결과: passed와 skipped 모두 summary에 기록.

전부 합성 주입(실 PDF 필요 시 기존 테스트 픽스처 패턴 재사용), PII 0. 경계 인접(모듈 0개·
미등록 모듈·schema_version 불일치)도 각각 테스트 또는 "커버 안 함(사유)"을 명시한다.

## 5. 예상 수정 범위

- `scripts/hverify_pdf.py` · `scripts/hprofile_check.py` · `scripts/hrun.py` · `scripts/hsummary.py`
- `tests/test_harness.py`
- `harness/profiles/integrated_full.example.yml` (modules 계약 예시)
- 필요한 계약 문서(docs/20 등)와 docs/16 QI 기록(HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP —
  표면 결함 + "왜 못 잡았나" 2층)

범위 밖 파일 수정 금지. 제품 diff 0이어야 한다.

## 6. 기준선·검증 명령 (구현자 실측 의무)

- 시작 전: HEAD `084e04c`·clean 실측(다르면 정지·보고).
- 완료 근거: `.\.venv\Scripts\python.exe -m pytest tests\ -q` 전체 GREEN, 기존 감소 0
  (기준선 949/4 + 신규 테스트 수 명시), `-k golden` 28, 변경 Python Ruff·py_compile,
  `git diff --check`, `sajugen/**` diff 0 확인.
- 검증 중 API 호출 0. 실행 명령 + 출력(passed/exit code)을 notes에 기록.

## 7. 교차리뷰·후속 게이트

1. 구현 완료 → `implementation-notes.md` 기록 → manifest `review_requested/next_actor=claude`.
2. Claude 신선 컨텍스트 교차리뷰(diff 전량 + 기준환경 pytest 직접 실행) → PASS 시
   `verified/next_actor=user`.
3. PASS 뒤 운영자 지시로 **기존 replacement PDF SHA가 동일한 상태에서 hrun 1회만 재실행**
   (`--regen` 없이, API 0). 최종 수용값:
   - 같은 PDF SHA(`63383335e830…`) · `pages=29` · `minimum_pages=28` · `gate_pass=True`
   - 실패 게이트 키 0 · `retry_blocked=False` · `api_calls=0` · `regen_allowed=False`
   - 전체 pytest GREEN(passed·skipped 요약 보존 포함)
4. 그 뒤에만 별도 승인으로 hsweep 진행.

## 8. 미검증·범위 밖 (정직 경계)

- replacement PDF의 육안 품질(consult·love 룰 폴백 직답성/자연스러움, 36→29쪽 감소의 내용
  누락 여부, register warning 4건의 실제 어색함)은 운영자 검수 몫 — 이 패킷 범위 밖.
- prompt cache 비용 절감률 확정(기존 1호 계측 부재)·hsweep K/Z·Z=0은 후속 단계.
