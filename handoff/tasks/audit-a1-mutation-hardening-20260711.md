# [Codex 지시문] 감사 A-1 — 생존 변이 차단측 보강 (테스트 전용) (2026-07-11 운영자 승인)

> 형식: TASK_PACKET(산문판, 최소형·테스트 전용). 실행 기준 = 이 문서 + `handoff/reports/audit-2026-07/audit.md` §4(로컬 보고서 — 비열람 시 이 문서의 §1 요약으로 충분).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review(라운드15). 커밋 = 리뷰 PASS 후 운영자.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·sajugen 런타임 LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역 접근.
- **검색(rg/grep 등) 시 ignored 제외 글롭 필수 — `!**/` 프리픽스**:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`.
- **수정 범위 한정: `tests/test_render_verify.py` 1파일(테스트 추가만)**. 제품 코드(`verify.py` 포함) 일체
  비수정 — 이 발주는 게이트를 바꾸는 게 아니라 게이트 완화를 잡는 감지망을 까는 것이다. 범위 초과 시 정지·보고.
- 테스트 픽스처 PII 0(합성 텍스트만). 실렌더 헬퍼 재사용 시 기존 합성 관례 유지.

## 1. 상태(전제) — 2026-07-11 감사 실측
- 브랜치 `codex/gunghap-relationship-quality`(== main), 시작 HEAD = `81ebf3d`. 워킹트리에 `sajugen/STATE.md`·
  `handoff/current/manifest.json` 감사 기록 수정분이 미커밋으로 존재(발주 세션 소유 — Codex 비접촉).
- 기준선(기준환경): **829 passed / 4 skipped / exit 0**. 감소 = 회귀.
- **감사 변이 실측(2026-07 월 감사 §4)**:
  - **M1 SURVIVED**: `verify.py:47 MIN_TEXT_CHARS` 1500→0 무력화를 **전체 829개 테스트가 전부 통과** —
    통이미지 차단 게이트(`text_layer_ok`, 계산 = `verify.py:499` `len(text) >= MIN_TEXT_CHARS`)의
    차단측 테스트 부재.
  - **M3 감지 단일점**: `delivery_quality_clean` 항상-True 변이를 전체에서 단 1개 —
    `test_integrated_product.py::test_integrated_full_without_concern_fails_missing_customer_context` —
    만 잡는다. verify 경유 delivery 차단의 전용 테스트가 없어 그 테스트 하나가 우연히 방어 중.
- 재사용 앵커: `tests/test_render_verify.py:162 _render_sections`(실렌더 헬퍼)·`:177~` 결함 주입 테스트
  선례. verify는 `pdf_path` 하나로 호출 가능(스펙 미전달 게이트는 skip — 단 text_layer는 무조건 계산).

## 2. 구현 (테스트 2건 이상, 같은 파일)
1. **M1 차단측 — text_layer 임계 양방**: fitz(PyMuPDF)로 텍스트 길이를 정확히 제어한 합성 PDF 2개를
   임시 경로에 생성 — (a) `MIN_TEXT_CHARS - 1`자 → `verify()` 결과 `text_layer_ok is False` +
   `gate_pass is False`, (b) `MIN_TEXT_CHARS`자 이상 → `text_layer_ok is True`. 임계는 리터럴이 아니라
   `verify.MIN_TEXT_CHARS` 상수 참조(임계 변경 시 테스트가 따라가되, 0으로의 무력화는 (a)가 잡는다 —
   (a)의 문서 텍스트가 0자가 아닌 이상 `>= 0`은 항상 True가 되어 단언 실패).
   주의: (a) 단언은 `text_layer_ok`·`gate_pass`에 한정(합성 tiny PDF는 폰트 임베드 등 다른 게이트도
   실패할 수 있음 — 그 키들은 단언하지 않는다).
2. **M3 이중화 — verify 경유 delivery 차단 전용 테스트**: `_render_sections`로 만든 실렌더 PDF에
   `verify(pdf, product="integrated_full", selected_modules=["love"], module_sections=정직 맵,
   premerge_section_ids=[..., "personal_health", ...])`처럼 **비선택 모듈 유입을 주입** →
   `delivery_quality_clean is False`·`gate_pass is False`·failures에 `unexpected_module_sections` 존재
   단언. 이 테스트는 "`dq['clean']`이 verify 결과와 gate_pass에 실제 반영된다"를 전용으로 고정해
   aggregate no-op 변이를 직접 잡는다(기존 단일 감지점 의존 해소).
3. 도크스트링에 각 테스트가 "무엇을 검증하고 무엇을 검증하지 않는지"를 명시(방법론 B-4 —
   감사 2026-07 M1/M3 변이 근거 인용).

## 3. 수용 기준 (양방 + 변이 재검)
- 신규 테스트가 정상 코드에서 GREEN.
- **변이 재검(구현 후 셀프 체크, 원복 필수)**: (a) `MIN_TEXT_CHARS = 1500`→`0` 임시 변이 시 신규 테스트
  RED, (b) `r["delivery_quality_clean"] = dq["clean"]`→`= True` 임시 변이 시 신규 테스트 RED — 두 결과를
  완료 보고에 포함하고 `git restore`로 원복(제품 diff 0 재확인).
- 전체 pytest exit 0, **기준선 829/4 대비 감소 0** + 신규 증가분 명시. 수정 1파일 Ruff GREEN.
  `git diff --name-only -- sajugen/` = 출력 없음(제품 무변경 증명).

## 4. 완료 보고 (여기서 멈춤)
실행 명령+출력, diff 요약(테스트 1파일 한정), 변이 재검 2건 RED→원복 증거. **커밋 없이 워킹트리 유지**
→ 교차리뷰 라운드15.

## 범위 밖
다른 임계 상수의 전수 변이(A-4, 차기 감사), 제품 코드 수정 일체, mutation 도구 도입, push.
