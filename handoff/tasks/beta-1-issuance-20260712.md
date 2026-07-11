# 베타 1호 발급·베타 트랙 진행 — SHA 인계 패킷 (2026-07-12)

- task_id: `beta-1-issuance-20260712`
- 성격: 운영 트랙(구현 발주 아님). source of truth = `docs/23-beta-operation.md`(확정) + 이 패킷.
- 다음 작업자: **user(운영자)** — 육안 검수. Claude는 검수 결과 접수 후 기록/수정 발주/베타 2·3 진행.

## 실측한 현재 상태 (2026-07-12)

- HEAD `0b46119`(main == feat, origin 동기, 워킹트리 클린). 기준선 **831 passed / 4 skipped**.
- Q7 전체(1~4단계+given 가드)·월 감사 2026-07(생존 변이 0)·A-1·A-2(실고객 산출물 389파일 repo 밖 보관) 종결.
- **베타 1호 주문 `ord_19f51b98aa69de82ade`**: integrated_full·4모듈(love/job/wealth/health)·LLM-on.
  상태 **DRAFTED** — gate_pass=True, 36p(하한 28p), 커버리지 clean, love·flow 챕터 가드 폴백 2건(정상 방어).
  접수는 로컬 입력 파일 경유(채팅 PII 0, 접수 후 파일 삭제됨).
- **hsweep 파일럿 1호(A-3)**: N=29 → M=0 → K=0, $0.41, 완주. **Z(운영자 육안 신규 발견) 미측정 —
  이번 계측의 결정 지표**. 리포트 `handoff/reports/20260712-001823-sweep/`(gitignored).
- draft PDF: `sajugen/render/out/draft_ord_19f51b98aa69de82ade.pdf`(gitignored).

## 다음 행동 (순서)

1. **운영자**: draft PDF 육안 검수(docs/23 §2-3) — 중점: consult 챕터의 4갈래 질문(직업 전환·출산/자식·
   건강·재물) 직답성, love 챕터(폴백분) 문안 자연스러움, 금칙(적중·AI 언급·실명) 스캔.
2. **운영자 → Claude**: **Z 값 보고**("Z=0" 또는 발견 목록). Claude가 docs/16 hsweep 절에 추기.
   - Z=0: admin(`/admin`)에서 승인(APPROVED) → 최종 발급 → 수동 발송. 이후 베타 2호 접수.
   - Z>0: 결함이면 docs/16 QI 등재 + 수정 라운드 발주(Codex), 개선 희망이면 백로그.
3. **베타 2·3호 접수 절차**(1호와 동일): Claude가 `tmp/reissue-input.txt` 템플릿 생성 → 운영자가 채움
   (PII 채팅 비경유) → "입력했어" → Claude가 접수·모듈 확정·LLM 생성·hsweep(승인 시)·검수 준비.

## 규칙 리마인드 (새 세션용)

- PII: 고객 이름·생년월일·질문 원문은 채팅·커밋·로그 비전재(도구 출력 마스킹 필수). 접수 입력은 로컬 파일 경유.
- 검증 명령은 전부 `./.venv/Scripts/python.exe -m ...`. hsweep 실 API = 3중 잠금(--approve --allow-llm +
  env SAJUGEN_HARNESS_ALLOW_REGEN=1) + 운영자 승인.
- 커밋·push·main 전진 = 운영자 지시("권장대로" 포함) 시에만. APPROVED·발송 = 운영자 전속.
- 피드백 처리: 결함 = docs/16 QI / 개선 희망 = 백로그(베타 종료 시 일괄 트리아지 — "완성 우선" 결정).

## 확인하지 못한 것

- Z 값(운영자 육안) — 이 패킷의 대기 지점.
- LLM-on 정상 쌍 N=5(2인) 실측 — 선택 항목 잔존(2인 베타 주문 발생 시 권장).
- PII 잔여 ②(git 이력 실명 rewrite) ③(docs/11 생년월일) — 운영자 결정 대기.
