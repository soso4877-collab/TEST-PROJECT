# TASK_PACKET — 起運 격자 전수 테스트를 운영자 옵트인으로 분리 (daewoon-grid-optin-20260823)

- **task_id**: `daewoon-grid-optin-20260823`
- **owner**: **Codex 구현자** / **next_reviewer**: Claude Code 교차리뷰(read-only)
- **base_commit**: `97d9dd1` (F-1 마감 직후, tree clean)
- **근거**: `REVIEW-FEEDBACK.md` 2026-08-23 F-1 리뷰 §3 — 격자 테스트 10건(각 ~200초)이 전체 스위트를 3.5분→23.5분으로 늘림.
  테스트 피라미드(방법론 B-4)·측정 후 최적화(B-5). 리뷰어 실측 `--durations=5`: 210.79/199.01/198.40/195.40/194.27s 전부 격자.
- **rev**: 1

## 0. 역할·금지
Codex 상시 금지(PDF 재생성·LLM 호출·git commit·push·배포) 유지. **제품 코드 무수정**(tests 1파일만).

## 1. Goal
`tests/test_daewoon_qiyun_axis.py::test_grid_before_after_change_rate_and_ganzhi_invariants[1985..1994]` 10건이 **기본 실행에서 skip**
되고(사유 명시), 환경변수 `SAJUGEN_QIYUN_GRID_SWEEP=1` 일 때만 실행된다. 나머지 테스트(앵커 4·나머지 단언 4·축 역할·23시대 양방 3·
절입 귀속)는 상시 유지.

## 2. 설계
- 저장소 관행 재사용: `tests/test_integrated_render_e2e.py:24` 의 `pytest.mark.skipif(os.environ.get("...") != "1", reason=...)` 패턴.
  격자 테스트 함수 **하나에만** 데코레이터를 붙인다(파일 전체 `pytestmark` 금지 — 앵커까지 꺼진다).
- reason 문구에 실행 방법과 소요(약 20분)를 적는다. 예: `"起運 격자 25,440건(약 20분)은 SAJUGEN_QIYUN_GRID_SWEEP=1 로 옵트인"`.
- `_axis_year_stats` 등 본문·단언·격자 정의 **무수정**. 간지/방향 불변 단언 완화 금지.

## 3. 파일 경계
allowed: `tests/test_daewoon_qiyun_axis.py`, `implementation-notes.md`, `sajugen/STATE.md`. 그 외 전부 forbidden(특히 `sajugen/**`).

## 4. 수용 기준 (양방)
1. 기본: `./.venv/Scripts/python.exe -m pytest tests/test_daewoon_qiyun_axis.py -q -rs` → 격자 **10 skipped**(사유 출력) + 나머지 전부 passed, exit 0.
2. 옵트인: 환경변수 `SAJUGEN_QIYUN_GRID_SWEEP=1` 로 **1개 연도만** 선택 실행(`-k "1985"`) → passed, exit 0 (전수 10건 재실행은 불필요 —
   직전 태스크에서 GREEN 실증됨; 1건으로 데코레이터가 실제 해제되는지만 본다).
3. 전체: `./.venv/Scripts/python.exe -m pytest tests/ -q` → **1293 passed / 14 skipped / exit 0** 예상(1303−10 / 4+10), 소요 ≤ 5분.
   구현환경은 Playwright skip 28 추가(환경차 규칙).
4. ruff 변경 파일 0 위반.

## 5. 산출물
`CODEX_IMPLEMENTATION_REPORT`(notes 최상단): 명령·출력·소요 시간 전후. 커밋 금지.
