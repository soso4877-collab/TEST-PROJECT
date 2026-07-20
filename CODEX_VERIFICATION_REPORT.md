# CODEX_VERIFICATION_REPORT — ilgan-personality-wiring-20260720

- 검증일: 2026-07-20
- 역할: Claude 직접 구현분 Codex round-2 read-only 재검
- 기준 HEAD/base: `48376056446df72c6c39c1be45f34c5259b9da4b`
- handoff: `HANDOFF_VALID task_id=ilgan-personality-wiring-20260720 status=review_requested next_actor=codex`
- packet SHA-256: `49698f44a5a081d67ec00f883b5e917f4eb0d225fbc0c8b150c31205bc11fb6a` 일치
- 최종 판정: **EVIDENCE_SPLIT_PASS — 코드 블로커 0**

## 1. round-1 B-1/B-2/B-3 해소 확인

### B-1. 표시 상징 계약 — 해소

- `docs/25 §1-1`에 고객 렌더용 표시 상징 10개가 별도 승인 계약으로 고정됐다. `GAN_PERSONA.symbol`과
  `_RENDER_CONTRACT.symbol`은 10천간 전부 이 표와 정확히 일치한다.
- §1의 전통 대안 상징 `동량·등불·성벽·화원`은 정본에 보존하면서, 고객 문안은 style-safe 표시 상징을
  사용하도록 근거와 렌더 표현을 분리했다. `등불`은 코드 렌더에 유입되지 않는다.
- `test_render_contract_symbol_and_axes_frozen`이 코드 테이블과 별도로 §1-1 표시 상징을 동결한다.

### B-2. core/shadow 정본 축 및 회귀망 — 해소

- `myeongni_persona.py`의 10천간 core/shadow를 docs/25 §1과 전수 대조했다. round-1에서 누락했던
  `자기과신·심미·공명정대·산만·문예·대국관·휘둘림·구속 싫어함·관찰력·자존·기지·직관·유약함 속 강함`
  축을 포함해 §1의 의미 축이 관형형 문안에 보존됐다.
- §1-1 오라클은 표시 상징 10개, core 필수 토큰 30개, shadow 필수 토큰 29개를 전수 검사한다.
  특정 6간 core 일부만 보던 round-1 감지 사각이 제거됐다.
- 戊 core는 register 금칙 `큰 그림` 대신 승인된 `넓은 시야`를 사용한다.

### B-3. 신약 modifier 강약 프레임 및 중복 — 해소

- `SINGANG_MODIFIER["신약"]`은 `신중하게 다듬고 조율하며 받아들이는` 발현 방향만 말한다.
  modifier 전수에서 `강한·여린·약한·나약` 토큰은 0건이다.
- 신약의 `약함 아님` 설명은 기존 `strength` 골격 한 곳만 소유한다. 합성 `nature`에서
  `나약하다는 뜻이 아니라`는 정확히 1회이고 `여린 편·약한 편`은 0회다.
- 회귀는 exact count뿐 아니라 승인 방향 존재와 modifier 강약 프레임 0을 함께 단언한다.

## 2. 정합·가드·불변 경계

- **docs/25 §1-1 ↔ persona 전수 정합**: 표시 상징과 core/shadow 필수축 전수 오라클 통과.
- **persona 문안 가드**: `GAN_PERSONA` 30개 필드 + modifier 3개 + 없는 오행 5개, 총 38개 문자열을
  `style_lint + register_lint + raw_calc_lint + safe_lint`로 독립 스캔한 결과 `hits=0`이다. 전용 테스트도
  10천간 × 3 modifier의 실제 lead/mod 문장을 같은 고객 가드로 검사한다.
- **사실 슬롯 불변**: HEAD 대비 `sajugen/calc/**`, `sajugen/input/**` diff 0. `rules.py`의 일간·연월시
  십성·일지 십성·신강·신살 사실 표현은 유지되고, 정본 성격 의미와 연결 문장만 추가·재배열됐다.
- **가드/게이트 완화 0**: `factcheck.py`, `safe_lint.py`, `style_lint.py`, `quality_lint.py`,
  `customer_meta_lint.py`, `trace.py`, `render/verify.py` diff 0. `GATE_KEYS`는 23개·중복 0으로 유지됐다.
- **비단정·fail-closed**: 10천간 lead는 `경향/갈래/보곤` 톤을 사용하며, 정본 밖 일간은 빈 문자열로
  생략한다. 정본 밖 성격 의미를 생성하는 별도 경로는 diff에서 발견되지 않았다.
- **없는 오행 양가**: 목·화·토·금·수 전수 문구가 존재하고, 화·수는 `오히려` 갈망 축을 함께 보존한다.

## 3. 테스트·정적 검증 증거

```text
.\.venv\Scripts\python.exe -m pytest tests/test_myeongni_persona.py -q
  -> 10 passed / exit 0

.\.venv\Scripts\python.exe -m pytest tests/ -q
  -> 1108 passed, 32 skipped / exit 0 / 160.38s

.\.venv\Scripts\python.exe -m pytest tests/ -q -k golden
  -> 28 passed, 1112 deselected / exit 0

.\.venv\Scripts\python.exe -m ruff check sajugen/content/myeongni_persona.py \
  sajugen/content/rules.py sajugen/content/llm_sections.py tests/test_myeongni_persona.py
  -> All checks passed! / exit 0

.\.venv\Scripts\python.exe -m py_compile sajugen/content/myeongni_persona.py \
  sajugen/content/rules.py sajugen/content/llm_sections.py tests/test_myeongni_persona.py
  -> exit 0

git diff --check
  -> exit 0
```

현재 환경 총수 `1108 + 32 = 1140`은 기준환경 보고 `1136 + 4 = 1140`과 정확히 같다. 차이 28건은
`tests/playwright_guard.py`가 `CODEX_THREAD_ID` 또는 `CODEX_SANDBOX_NETWORK_DISABLED` 환경에서 의도적으로
skip하는 Playwright subprocess 계열이다. 호출 테스트 수 역시 `test_p4` 9 + `test_render_verify` 11 +
`test_p5` 3 + `test_p8` 3 + `test_consistency` 1 + `test_harness` 1 = 28로 일치한다. 따라서 코드 실패나
수집 감소로 바꾸지 않고 **EVIDENCE_SPLIT_PASS**로 판정한다.

## 4. diff / git status

검증 대상은 HEAD `4837605` 위 미커밋 변경이다. 제품 변경은 `rules.py`, `llm_sections.py`, 신규
`myeongni_persona.py`; 정본·정책은 `docs/25`, `docs/03`; 회귀는 신규 `test_myeongni_persona.py`다.
나머지는 handoff·상태·보고 메타다. calc/input/render/가드 구현 변경은 0이다.

Codex가 이번 round-2에서 수정한 파일은 이 `CODEX_VERIFICATION_REPORT.md` 하나뿐이다. 구현·정본·테스트·
manifest는 수정하지 않았다.

## 5. 확인하지 못한 것 / 남은 위험

- 기준환경의 원시 `1136 passed / 4 skipped` 출력은 이 Codex 환경에서 직접 재현하지 못했다. 동일 tree·동일
  수집 총수와 예정된 28 skip 경계를 합성한 판정이다.
- 실제 LLM 문안, 실제 PDF·300dpi 육안, 비용은 범위 밖이며 미검증이다.
- 코드 미해결 블로커는 없다. 남은 위험은 운영자 승인 전 미커밋 상태와 환경 분리 증거뿐이다.

## 6. 다음 행동

결론: round-1 B-1/B-2/B-3는 해소됐으므로 **EVIDENCE_SPLIT_PASS**로 운영자에게 넘긴다. 운영자가
기준환경 `1136/4` 증거와 이 보고서를 합성해 commit 여부를 결정한다. 이번 검증에서 commit·push·LLM/API·
PDF 재생성·deploy는 실행하지 않았다.
