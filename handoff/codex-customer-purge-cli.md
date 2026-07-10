# [Codex 지시문] customer-purge CLI — E9 식별자 차등 파기 실행 경로

> 형식: 승인된 TASK_PACKET(산문판). 신선 컨텍스트에서 이 문서만으로 실행 가능.
> 계기: 발급 런북(`docs/22-issuance-runbook.md` §1-2) 작성 중 **E9 2계층 차등 파기(식별자만)의 운영자 실행 경로 부재**가 드러남.
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = 별도 Claude 세션 /cross-review. 커밋 = 운영자.

## 0. 역할·금지
- Codex 상시 금지: git commit·push·deploy·LLM 호출·PDF 재생성. 완료 시 pytest 전체 실행 + diff·증거 보고까지.
- 범위 = `customer-purge` CLI 1개 추가로 **한정**. 다른 개선·리팩터링 금지(동결 E12). 한국어. PII 0.

## 1. 배경 (왜)
E9 2계층 보관은 **식별자(이름)만 30일/요청 시 파기, 명식·content·별칭은 보존**을 요구한다. store에 이미 `OrderStore.purge_identifier(alias)`가 구현돼 있으나(`name_masked=NULL, purged_at=now`), **운영자가 부를 CLI가 없다**. 현재 CLI는 `customer-find`·`gen-followup`·`gen` 셋뿐이고, `delete_order`는 **하드 삭제**(명식까지 제거)라 차등 파기와 다르다. → 식별자 차등 파기를 실행할 진입점이 비어 있다.

## 2. 대상·구현
**대상**: `sajugen/cli.py` (Typer 앱, 기존 `customer-find`:18 패턴 재사용).

신규 서브커맨드:
```
python -m sajugen.cli customer-purge --alias SD-0007 [--yes] [--db <경로>]
```
- `--alias`(필수): 파기할 단골 별칭.
- `--yes`(선택): 미지정 시 파기 전 확인 프롬프트(`typer.confirm`). 지정 시 무확인 실행(`delete_order --yes` 관례와 일치).
- `--db`(선택): `order_flow.DEFAULT_DB` 기본.
- 동작: `OrderStore(db).purge_identifier(alias)` 호출 → 성공 시 "식별자 파기 완료(alias=…, purged_at=…, 명식·별칭 보존)" 출력. **PII(name_masked 원문) 미출력.**
- 존재하지 않는 alias: `purge_identifier`가 던지는 `KeyError`를 잡아 `typer.echo` + `typer.Exit(code=1)`(명확한 "단골 없음" 메시지).
- store 연결은 기존 커맨드처럼 `try/finally`로 `close()`.

**구현 금지**: `purge_identifier` 로직 변경(이미 검증됨)·`delete_order` 통합·상태머신 개입. CLI 래퍼만 추가.

## 3. 수용 기준 (양방 — 방법론 A-3)
- 파기 후: `customers.name_masked IS NULL` + `purged_at` 기록 + **orders 행·report_json·alias 보존** 실증.
- 존재하지 않는 alias → exit code 1 + 에러 메시지(정상 파기와 구분).
- `--yes` 없이 확인 프롬프트 동작(CliRunner `input`으로 검증).
- 하드 삭제(`delete_order`)와 **다름** 확인: purge는 명식 보존.

## 4. 동반 테스트
`tests/test_customer_purge.py`(신규) 또는 `tests/test_followup_schema.py` 확장 — CliRunner로 customer-purge 호출, 위 수용 기준 4개 양방. 합성·익명 데이터(PII 0).

## 5. 검증 (완료 근거 — 절대규칙 19)
- `./.venv/Scripts/python.exe -m pytest tests/ -q` → exit 0. **기준선 692/4(기준환경) 대비 신규 테스트만큼 증가, 감소 0.**
- `calc/`·`input/` 무변경 → 골든 불변.
- 완료 보고: 실행 명령 + 출력(passed/exit) + diff 요약. 커밋은 운영자. Claude 신선 컨텍스트 /cross-review.

## 범위 밖 — 손대지 않음
`purge_identifier`/`delete_order`/store 스키마/상태머신/후속 기능 코드. 발급 런북 문서(docs/22)는 이 CLI 반영이 이미 돼 있음(재수정 불요).
