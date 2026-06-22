# Claude Code 작업 지시 — <작업명>

## 범위
- 목표: <한 줄>
- 수정 허용 파일: <목록>
- 절대 금지: calc/ 수정, report_type/order_flow/admin/단품/토정/택일/작명, push, 배포, 미승인 LLM/PDF 재생성, .env/secrets 출력

## 진행 방식
- 한 번에 한 작업(plan→승인→구현→검증→보고). auto mode 금지. 검증 실패 시 자동 수정 금지.

## 수용 기준
- 전체 `tests/` PASS(현재 기준선: <N> passed 이상).
- `scripts/hrun.py`(no-regen) preflight_ok + all_gates_pass(또는 missing_pdf 명시).
- calc/ diff 없음. `.env`·render/out·local 프로파일·reports 추적 0.

## 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe scripts/hrun.py --profile <local.yml> ...
```

## 보고 형식
`handoff/templates/final_report.md` 사용.
