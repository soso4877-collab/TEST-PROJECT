# PDF_REVIEW_REPORT

> 기본 상태는 REVIEW_REQUIRED다. 고객 이름, 생년월일, 질문 원문, PDF 본문 전문을 넣지 않는다.

## input_pdf
- anonymous_id: `DOC_A`
- location_policy: `gitignored artifact path only; do not paste PDF text`

## input_sha12
- value: `aaaaaaaaaaaa`

## render_verify_result
- status: `PASS | FAIL | NOT_RUN`
- evidence: `summary path or tool output reference without PII`

## forbidden_text_scan
- status: `PASS | FAIL | NOT_RUN`
- checked_for:
  - `AI-meta wording`
  - `placeholder residue`
  - `masking residue`
  - `raw calculation leakage`
- notes: `PII-free summary only`

## semantic_style_review
- status: `PASS | FAIL | NOT_RUN`
- notes: `AI-like phrasing, unsupported facts, repeated filler, tone mismatch`

## delivery_answer_review
> P1~P5 회귀 항목 — 게이트가 놓칠 수 있는 '납품 답변 품질'을 수동으로 확인한다.
- customer_concern_reached_delivery_quality: `PASS | FAIL | NOT_RUN`  # has_customer_context=true (P1)
- required_axes_non_empty_when_concern_has_triggers: `PASS | FAIL | NOT_RUN`  # required_axes != [] (P1)
- first_physical_customer_pages_contain_direct_answer: `PASS | FAIL | NOT_RUN`  # physical_frontloaded_answer.ok (P5); 표지/목차로 물리 p1~p3에 답변 없으면 FAIL
- transition_section_preview_meta_absent: `PASS | FAIL | NOT_RUN`  # 문서 진행/섹션 예고 발화 0 (P2/P3)
- repeated_or_general_filler_checked: `PASS | FAIL | NOT_RUN`  # 반복/빈말/일반론
- notes: `PII-free; count/page/rule only`

## visual_review_300dpi
- status: `PASS | FAIL | NOT_RUN`
- pages_checked: `first page, consult page, last two pages, sampled dense pages`
- notes: `layout, orphan/widow, clipping, low-density page, image/text overlap`

## brand_review
- status: `PASS | FAIL | NOT_RUN`
- notes: `brand voice and product tier fit`

## pii_review
- status: `PASS | FAIL | NOT_RUN`
- notes: `no customer PII quoted in this report`

## retry_blocked
- value: `true | false`
- reason: `operator approval needed | gate failure | missing source artifact | none`

## operator_reading_status
- status: `REVIEW_REQUIRED | IN_REVIEW | APPROVED | REJECTED`
- reviewer: `OPERATOR`

## final_status
- value: `REVIEW_REQUIRED`

## release_allowed
- value: `false`
- rule: `true only after render_verify, forbidden text scan, 300dpi visual review, PII review, and operator full-text approval all pass`
