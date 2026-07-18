# CODEX_VERIFICATION_REPORT — ziwei-temperament-wiring-20260717

- 검증일: 2026-07-17
- 역할: Claude 직접 구현분 신선 Codex read-only 검증
- 기준: HEAD/base `461a0e9ec68ef33ef9fa60283901773f5afa4aa6`
- handoff: `HANDOFF_VALID task_id=ziwei-temperament-wiring-20260717 status=review_requested next_actor=codex`
- 최종 판정: **CHANGES_REQUESTED**

## 1. 블로커

### B-1. docs/24 정본 테이블이 코드의 단일 소스로 온전히 보존되지 않음

- `docs/24-ziwei-star-temperament.md:24`의 천부 化氣는 `印·庫`인데
  `sajugen/content/ziwei_temperament.py:49`는 `hwagi: "인"`만 저장한다. packet §3의
  `STAR_TEMPERAMENT = 14주성 × {化氣, 핵심기질, 그늘}, docs/24 §1 표 그대로` 계약과 불일치한다.
- `docs/24:45-48`의 사화 방향에 있는 정본 축 가운데 코드 `SIHUA_DIRECTION`(`:99-102`)은
  화록의 `기회`, 화권의 `경쟁·강화`, 화과의 `품격`, 화기의 `결핍·장애`를 생략한다.
  방향 문구를 짧게 바꿀 수는 있으나, 정본 의미를 어떤 규칙으로 축약해도 되는지 승인된 매핑이 없으므로
  현재 상태를 `docs/24 §1~§3 단일 소스 정합`으로 확정할 수 없다.

필요 조치: docs/24의 化氣·사화 방향을 손실 없이 보존하거나, 축약이 의도라면 운영자 승인으로 docs/packet에
허용 매핑을 먼저 고정한 뒤 코드와 테스트를 그 계약에 맞춘다.

### B-2. 정본 정합 회귀 테스트가 B-1을 검출하지 못함

- `tests/test_ziwei_temperament.py:39-47`은 14개 별 키와 `core`·`shadow`의 비어 있지 않음만 검사하고
  `hwagi`의 존재·정확한 값은 단언하지 않는다. 따라서 천부 `庫` 누락이 `10 passed`로 통과한다.
- 같은 파일 `:59-72`의 데이터 순정 검사는 `core`·`shadow`·사화·프레임만 합치며 `hwagi`는 제외한다.
  테스트 이름은 성별 단정까지 고정한다고 적었지만 금칙 목록에 `여성` 축도 없다.

필요 조치: docs/24에서 승인된 14개 化氣의 정확한 기대 맵과 사화 4방향의 필수 의미 축을 테스트로 동결하고,
모든 canon 필드를 데이터 순정 검사에 포함한다. 성별 단정 차단측도 실제로 실패하는 회귀를 추가한다.

## 2. 통과 확인

- **사실 슬롯 불변**: `rules.py`의 `_star_one`·`_stars_full`은 HEAD 대비 변경 0. 신규
  `_palace_temperament`는 기존 별 이름·밝기·사화 문자열 뒤에 의미 문장만 추가한다.
- **정본 밖 별-의미 fail-closed**: 테이블 조회 실패 시 서술을 생략하고, 공궁/미등록 `가상성` 테스트가
  빈 문자열을 단언한다. 별별 의미의 다른 생성 경로는 diff에서 발견되지 않았다.
- **가드/GATE_KEYS/calc 완화 0**: HEAD 대비 `sajugen/calc/**`, `sajugen/input/**`,
  `factcheck.py`, `safe_lint.py`, `style_lint.py`, `quality_lint.py`, `trace.py`,
  `render/verify.py` diff 0. `GATE_KEYS` 23개 유지.
- **joined 챕터 명궁 기질 무중복**: summary는 사실 슬롯·오리엔테이션만 유지하고 기질은
  `ziwei_palaces`의 `_palace_para`가 전담한다. 합성 joined 챕터에서 명궁 core count `<= 1` 테스트 통과.
- **밝기/사화 문형 반복 방지**: 별 이름을 seed로 한 기존 `_pick(md5)` 결정론을 사용하고,
  동일 밝기·사화로 14주성을 렌더한 회귀에서 각각 2개 이상 프레임이 실제 선택됨을 단언한다.
- **정적 검사**: 신규/변경 Python 3파일 Ruff `All checks passed!`, py_compile exit 0,
  `git diff --check` exit 0.

## 3. 테스트 증거

```text
.\.venv\Scripts\python.exe -m pytest tests/test_ziwei_temperament.py -q
  -> 10 passed / exit 0

.\.venv\Scripts\python.exe -m pytest tests/ -q -k golden
  -> 28 passed, 1100 deselected / exit 0

.\.venv\Scripts\python.exe -m pytest tests/ -q
  -> 1096 passed, 32 skipped / exit 0

.\.venv\Scripts\python.exe -m pytest tests/ -q -rs
  -> 1096 passed, 32 skipped / exit 0
  -> 기준 4 skip: 운영자 opt-in E2E 4
  -> 환경 추가 28 skip: Playwright subprocess skipped in Codex sandbox

.\.venv\Scripts\python.exe -m pytest tests/ --collect-only -q -rs
  -> 1128 tests collected / exit 0
```

수집 총수 `1128 = 1124 + 4 = 1096 + 32`로 테스트 감소는 없다. 추가 28건은 공용 Playwright guard
19건과 `test_p4.py` 9건이며 모두 동일한 Codex sandbox 사유다. 샌드박스 밖 권한으로 같은 전체 명령을
재실행해도 `1096/32`로 동일했으므로 현 환경에서는 `1124/4` 직접 재현이 불가능하다. 환경 증거만 보면
`EVIDENCE_SPLIT_PASS` 조건이나, B-1/B-2가 있어 전체 판정은 `CHANGES_REQUESTED`다.

## 4. diff / git status

검증 대상 구현·인계 변경:

```text
M  docs/03-engine-validation-plan.md
M  handoff/current/manifest.json
M  implementation-notes.md
M  sajugen/STATE.md
M  sajugen/content/rules.py
?? sajugen/content/ziwei_temperament.py
?? tests/test_ziwei_temperament.py
```

tracked diff는 5파일 `+91/-9`, 신규 구현·테스트 2파일이다. 제품 변경은 `rules.py`와 신규 canon 모듈,
테스트 1파일이며 calc/input/가드/render 변경은 0이다. 이 보고서 작성으로
`?? CODEX_VERIFICATION_REPORT.md`만 추가된다. 구현 파일은 수정하지 않았다.

## 5. 확인하지 못한 것 / 남은 위험

- 실모델 자미 서술 품질, 실제 PDF 조판·300dpi 육안, 비용은 범위 밖이며 미검증이다.
- 28개 Playwright 테스트는 Codex 환경에서 실행되지 않았다. 기준환경 Claude 보고의 `1124/4`를
  동일 수집 총수와 skip 사유로만 분리 합성했으며, Codex가 pass 결과를 직접 재현한 것은 아니다.
- B-1을 해소하기 전 이 canon 모듈을 후속 1e 프롬프트 근거로 사용하면 누락된 정본 축이 그대로 전파된다.

## 6. 다음 행동

결론: B-1 정본 손실과 B-2 감지 사각만 별도 수정 라운드로 고친 뒤 재검증한다. 그 전에는 commit/push하지
않는다. 이번 검증에서 commit·push·LLM/API·PDF 재생성·deploy는 실행하지 않았다.
