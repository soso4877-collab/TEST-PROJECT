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
