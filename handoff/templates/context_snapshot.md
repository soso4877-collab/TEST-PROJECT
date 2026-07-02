# CONTEXT_SNAPSHOT

> 대화 전문, 고객 PII, HTML/PDF 본문 전문을 붙이지 않는다. 파일 경로, SHA, 결정사항, 실패 rule만 남긴다.

- snapshot_id: `SNAPSHOT_YYYYMMDD_HHMM`
- created_at: `YYYY-MM-DDTHH:MM:SS+09:00`
- current_stage: `PLAN | IMPLEMENT | VERIFY | PDF_REVIEW | OPERATOR_REVIEW | HOLD`
- last_completed_stage: `NONE | PLAN | IMPLEMENT | VERIFY | PDF_REVIEW`
- next_action: `다음 세션에서 수행할 한 가지 행동`
- run_state:
  - current_stage: `PLAN | IMPLEMENT | VERIFY | PDF_REVIEW | OPERATOR_REVIEW | HOLD`
  - input_sha: `aaaaaaaaaaaa`
  - output_sha: `bbbbbbbbbbbb`
  - api_calls: `0`
  - pdf_rendered: `false`
  - retry_blocked: `false`
  - final_status: `PHASE0_DOCS_READY_FOR_VERIFICATION | HOLD`
- source_of_truth_files:
  - path: `handoff/current/task_packet.json`
    sha12: `aaaaaaaaaaaa`
  - path: `handoff/current/RUN_STATE.json`
    sha12: `bbbbbbbbbbbb`
- artifact_sha12:
  - input_sha12: `cccccccccccc`
  - output_sha12: `dddddddddddd`
- decisions:
  - `DECISION_1`
- open_risks:
  - `RISK_1`
- stop_conditions:
  - `STOP if TASK_PACKET missing or SHA mismatch`
  - `STOP if customer PII or full PDF/HTML text is required in chat`
  - `STOP if hand-edited HTML/PDF is proposed as delivery baseline`
- forbidden_context:
  - `customer name`
  - `birth date or birth time`
  - `original customer question`
  - `full PDF/HTML body`
  - `secret values or local customer profile contents`
- no_customer_pii_confirmation: `confirmed | not_confirmed`
