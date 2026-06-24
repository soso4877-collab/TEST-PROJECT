# AI 하네스 작업 요청 (운영자 작성)

## 도구/Skill/MCP 사전 확인
- 이미 확인한 도구:
  - repo-native: <scripts/hrun.py | scripts/ai-harness.ps1 | pytest | render/verify.py | 해당 없음>
  - Codex/GitHub Skill: <github:github | github:gh-address-comments | github:gh-fix-ci | github:yeet | 해당 없음>
  - MCP/connectors: <사용 안 함 | 읽기 전용으로 사용할 공식/검증 MCP 이름>
- 직접 구현이 필요한 이유:
  - <기존 도구로 해결되지 않는 구체적 이유>
- MCP를 쓰지 않는 이유:
  - <PII/secret/data/PDF 위험, 기존 도구로 충분함, 또는 공식/검증 도구 없음>

> 이 파일을 `handoff/current/task.md`로 복사한 뒤 내용을 채워 실행한다.
> 경고: 생년월일·출생시간·출생지·실고객 정보·API 키/secret을 여기에 적지 마라.
> 하네스가 고신뢰 secret을 발견하면 fail-closed(종료코드 10)로 중단한다.

## 목표
<한 줄로 무엇을 이루려는가>

## 허용 파일 (변경 가능 범위)
- <path>
- <path>

## ALLOWED_FILES
- handoff/current/README.md

## 금지 파일 (절대 변경 금지)
- 기존 계산 코드(sajugen/calc/, sajugen/input/) — 별도 승인·골든 회귀 없이는 금지
- <필요 시 추가>

## FORBIDDEN_FILES
- sajugen/calc/**
- sajugen/input/**
- .env
- data/**

## 제약
- <지켜야 할 규칙·경계>

## 수용 기준
- <측정 가능한 완료 조건 1>
- <측정 가능한 완료 조건 2>

## 비고
- <참고 사항>
