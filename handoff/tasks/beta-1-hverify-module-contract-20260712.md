# TASK_PACKET — 하네스 프로파일 모듈 계약 배선 (HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP 종결)

- task_id: `beta-1-hverify-module-contract-20260712`
- base_commit: `2d91933` (HEAD, working tree clean 실측 2026-07-14 **재베이스라인** — 구 base `084e04c`는 삼주 라인 완결 전 값. task_id는 동일 태스크라 유지)
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰
- 상태: `planned` (2026-07-14 재활성 — 삼주 라인 종결 뒤 보류 해제, 갭 잔존 재확인)

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

- **현재 기준선(2026-07-14 재베이스라인 실측, HEAD `2d91933`)**: `.\.venv\Scripts\python.exe -m pytest tests\ -q`
  → **1061 passed / 4 skipped / exit 0**, `-k golden` **28 passed**. (구 949/4는 삼주 라인 착수 전 값 —
  그 사이 삼주 생시 미상·근거화·품질 후속이 종결되며 신규 테스트가 누적됐다.)
- ~~Phase C replacement 옛 증거(주문 `ord_19f55b6b…`·PDF SHA `63383335…`·29p)~~ = **stale(2026-07-14)**:
  해당 replacement PDF는 현재 `render/out`에 없음(파일명 부재 — PII 정리로 소멸 추정). §7.3의 옛 PDF 의존
  수용 기준은 이행 불가 → **합성 모듈 제한 픽스처로 재정의(아래 §7.3)**. 실 replacement 재생성은 하지 않는다.
- **판정 HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP — 2026-07-14 현재 HEAD에서 갭 잔존 재확인**:
  `scripts/hverify_pdf.py:178`의 `V.verify(...)` 호출에 `selected_modules` 인자가 없고(제품 verify는 받지만
  하네스가 전달 안 함), `scripts/hrun.py`에 module 참조 0, 비-local 프로파일 스키마에 `modules` 필드 0.
  → 4모듈 주문(하한 `module_minimums([love,job,wealth,health])=(28, 9000)`)을 기본 5모듈 스펙
  (`module_minimums(None)=(30, 10000)`)으로 오판 → 거짓 실패 `premium_pages`. 제품 경로(verify/
  delivery_quality/builder/integrated)는 Q7에서 `selected_modules` 배선 완료 — **갭은 하네스 증거 경로 한정**.
  방법론 A-5 "팬텀 파라미터" 클래스: `V.verify(selected_modules=...)`가 프로파일 경계에서 미소비.
- 부수 관측 갭: hrun summary에 `pytest.skipped`가 null — `passed / skipped`가 요약 파일 자체에 보존되지 않는다.

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

- 시작 전: HEAD `2d91933`·clean 실측(다르면 정지·보고).
- 완료 근거: `.\.venv\Scripts\python.exe -m pytest tests\ -q` 전체 GREEN, 기존 감소 0
  (기준선 **1061/4** + 신규 테스트 수 명시), `-k golden` 28, 변경 Python Ruff·py_compile,
  `git diff --check`, `sajugen/**` diff 0 확인.
- 검증 중 API 호출 0. 실행 명령 + 출력(passed/exit code)을 notes에 기록.

## 7. 교차리뷰·후속 게이트

1. 구현 완료 → `implementation-notes.md` 기록 → manifest `review_requested/next_actor=claude`.
2. Claude 신선 컨텍스트 교차리뷰(diff 전량 + 기준환경 pytest 직접 실행) → PASS 시
   `verified/next_actor=user`.
3. PASS 뒤 운영자 지시로 **합성 모듈 제한 픽스처 PDF로 hrun/hverify 1회 검증**(`--regen` 없이·API 0·
   옛 고객 replacement PDF 의존 제거 — 그 PDF는 소멸). 픽스처 = 4모듈(love/job/wealth/health) 프로파일 +
   그 주문 meta의 PII-free `module_sections`/`premerge_section_ids`(합성). 최종 수용값:
   - 4모듈 프로파일이 **5모듈이 아니라 4모듈 스펙(`minimum_pages=28`·`minimum_text_chars=9000`)으로 판정**됨을
     summary로 확인 = 거짓 5모듈 오판 소멸(수용 핵심). `gate_pass`는 픽스처 페이지수에 따르되 모듈 스펙 적용이 요점.
   - `retry_blocked` 정합 · `api_calls=0` · `regen_allowed=False`
   - hsummary에 `selected_modules`·`module_schema_version`·`minimum_pages=28`·`minimum_text_chars=9000` 보존
   - 전체 pytest GREEN(passed·skipped 요약 보존 포함)
4. 그 뒤에만 별도 승인으로 hsweep 진행.

## 8. 미검증·범위 밖 (정직 경계)

- 이 패킷은 **하네스 증거 경로 전용**(제품/calc/input diff 0)이라 실제 고객 PDF·육안 품질은 범위 밖이다.
  (옛 Phase C replacement PDF는 소멸했고 §7.3은 합성 픽스처로 재정의됨 — 실 replacement 재생성 없음.)
- prompt cache 비용·hsweep K/Z·Z=0·실고객 발송은 이 패킷 밖의 후속 단계다.
