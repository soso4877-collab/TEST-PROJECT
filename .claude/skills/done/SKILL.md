---
name: done
description: sajugen 완료 보고의 증거 3종(마지막 pytest 출력 + HEAD SHA + 실행 명령) 정형 블록을 조립한다. "완료됐다"고 보고하기 직전에 사용 — 증거 없는 완료 주장(사용자 2회 교정 이력)을 구조적으로 막는다.
user-invocable: true
allowed-tools:
  - Bash(./.venv/Scripts/python.exe -m pytest *)
  - Bash(git rev-parse *)
  - Bash(git log *)
  - Bash(git status *)
  - Read
---

# /done — 증거 있는 완료 보고 (증거 3종 정형)

**규율(절대규칙 19 / 방법론 A-2)**: 검증하지 않은 것을 "완료/정확/해결"이라 단정 보고 금지.
완료 주장 = **실행 명령 + 출력(passed 수/exit code) + 커밋 SHA**. 증거가 없으면 미완료로 간주한다.
이 스킬은 그 3종을 실제로 실행해 조립한다(주장으로 대체하지 않는다).

## 절차
1. **테스트 실측**: `./.venv/Scripts/python.exe -m pytest tests/ -q` 를 실행하고 마지막 줄
   (`N passed, M skipped ... exit code`)을 그대로 캡처한다. bare `pytest`/`python` 금지.
   - calc/·input/ 변경이 포함됐으면 `-k golden` 도 함께 실측(골든 회귀 근거).
   - PDF 산출 검증이 필요한 변경이면 `scripts/hrun.py`(--no-tests 금지)의 `summary.json`
     `pytest.returncode`·`gate_pass` 비악화를 함께 인용.
2. **SHA 확정**: `git rev-parse --short HEAD` + `git log --oneline -1`.
3. **작업 트리 상태**: `git status --short`(미커밋 잔여가 있으면 "완료"가 아니다 — 먼저 커밋).
4. **정합 확인**: passed 수 증감을 기준선과 대조하고 증감 사유를 한 줄로(신규 N건/삭제 사유).
   기준선 감소가 설명되지 않으면 회귀로 간주하고 완료로 보고하지 않는다.

## 출력 정형 블록
```
## 완료 보고 (증거 3종)
- 실행 명령: ./.venv/Scripts/python.exe -m pytest tests/ -q
- 출력: <N> passed, <M> skipped / exit <code>   (기준선 <B> → 신규/삭제 <±k> = <N>, 정합)
- 커밋 SHA: <shortsha>  <제목>
- 작업 트리: clean (또는 미커밋 목록 — 있으면 완료 아님)
- (calc 변경 시) 골든: <G> passed
- (PDF 변경 시) hrun summary: pytest.returncode=0 · gate_pass 비악화
```

## 금지
- 테스트를 돌리지 않고 "아마 통과할 것"으로 블록을 채우지 마라(추정 금지 — 실측만).
- 미커밋 변경이 있는데 SHA 만 적지 마라(그 SHA 는 보고 내용을 담지 않는다).
- passed 감소를 설명 없이 넘기지 마라.
