# 16. 품질 사고 장부와 재발 방지 규칙

## 2026-07-02 추가: QI-2026-07-02-01 customer2 통합 PDF gate_pass=true인데 육안 품질 미달

- 증상: customer2 integrated_full PDF가 gate_pass=true/all_gates_pass=true였으나 운영자 육안으로 납품 불가. 문서 진행/섹션 예고 메타("자미두수 명궁 이야기도 바로 이어집니다"), 질문 축 미반영이 통과.
- 영향: 자동 게이트를 신뢰하면 저품질 납품이 통과할 수 있다(false-pass). 특히 질문 축 검사가 조용히 no-op 되면 프리미엄 상품이 고객 질문에 답하지 않은 채 기준을 충족한 것으로 보인다.
- 원인:
  - (배선) hverify_pdf.verify_profile이 profile.concern만 읽어, integrated/궁합이 고민을 담는 situation 필드를 놓침 → delivery_quality가 concern 없이 돌아 required_axes=[]로 질문축 검사 no-op.
  - (룰 공백) customer_meta_lint 전이 룰의 앵커가 "살펴보겠습니다"뿐이라 "…이어집니다"/"이야기도 이어" 계열 미탐. compose 프롬프트·가드에도 문서 진행 금지 부재.
  - (지표 괴리) frontloaded_answer가 앞 1800자 기준이라 물리 페이지 p1~p3(표지/목차)와 어긋나 "초반 답변" 체감과 불일치.
- 재발 방지(구현·검증 완료, 커밋 8012a20):
  - P1 concern 정규화(hrun situation→concern) + verify가 product로 context_required 산출 + concern 부재 시 missing_customer_context failure(조용한 no-op 금지).
  - P2 customer_meta_lint.transition_section_preview(구조어+진행 앵커 공기 시만 FAIL, 생활흐름 오탐 0). P3 builder/gunghap compose 가드 부착 + _COMPOSE_SYSTEM/_GH_SYSTEM/relationship SYSTEM 프롬프트 belt.
  - P4 목차 리드 중립화("…다음 순서로 이어집니다"→"차례"). P5 physical_frontloaded_answer(warning 전용·게이트 불변) + PDF 검수 체크리스트(delivery_answer_review).
  - 게이트/차단룰 완화 0(전 diff의 '-'는 린터 재포맷). pytest 425 passed/3 skipped.
- 실효 검증(2026-07-02, regen·LLM·PII 0의 read-only 재검증): 기존 customer2 PDF를 새 게이트로 재검증하니 이전 gate_pass=true였던 동일 PDF가 gate_pass=False로 정확히 실패. transition_section_preview page 5 count 1 포착, has_customer_context=True·required_axes=['action','helper_people','timing'] 복구, physical_frontloaded_answer ok=False answer_page=4(첫 3p=표지/목차) 보고.
- 연결 커밋/PR: 8012a20(feat 게이트 보강), 6bb18db(docs STATE 갱신).
- 남은 수동 검수: 개선 실효를 실제 납품으로 확인하려면 새 stamp로 customer2 Tier2 재생성 1발 필요(운영자 명시 승인 전 regen/발송/push 금지). 재생성물은 REVIEW_REQUIRED에서 운영자 전문 검수 후에만 발송.

## 2026-06-26 추가: QI-2026-06-26-01 Phase 0 문서 운영 containment

- 증상: 구조 검사는 통과했지만 납품 후보 문안에 AI-meta 문장, placeholder residue, 마스킹 잔재가 남을 수 있는 workflow 위험이 확인되었다.
- 영향: 손편집 HTML/PDF가 표준 게이트를 우회하면 고객 납품 기준선이 흔들리고, Claude/Codex/Harness/Operator 역할 혼선으로 검수 책임이 불명확해진다.
- 원인: TASK_PACKET과 context snapshot 같은 handoff artifact가 부족했고, context overflow 뒤 최신 source-of-truth SHA 확인이 약했다.
- 재발 방지:
  - Claude는 Plan Architect/Semantic Reviewer, Codex는 승인된 TASK_PACKET 구현자, Codex Verifier는 별도 세션 검증자로 분리한다.
  - TASK_PACKET, CONTEXT_SNAPSHOT, PDF_REVIEW_REPORT를 handoff 필수 artifact로 둔다.
  - 납품 후보는 표준 게이트 파이프라인에서만 만들고, 손편집 HTML/PDF는 최종 납품 기준선으로 쓰지 않는다.
  - RUN_STATE에는 current_stage, input_sha, output_sha, api_calls, pdf_rendered, retry_blocked, final_status를 남긴다.
  - 최신본은 파일명으로 판단하지 않고 SHA로 판단한다.
- 연결 커밋/PR: Phase 0 docs containment 작업.
- 남은 수동 검수: 실제 고객 PDF는 render_verify, 금칙 텍스트 스캔, 300dpi 시각 점검, 운영자 전문 검수 전 REVIEW_REQUIRED 상태로 둔다.

## 2026-06-27 추가: QI-2026-06-27-01 Phase 1 universal semantic gate verified

- 증상: 손편집 또는 편집 경로를 거친 납품 후보에 AI-meta 문안, placeholder residue, document self-reference가 남을 수 있었다.
- 영향: 구조 검사가 통과해도 최종 고객 문안에 편집자/도구/문서 구조 설명식 잔재가 노출될 위험이 있었다.
- 원인: PDF 최종 추출 본문에 대해 모든 생성 경로에 공통 적용되는 universal semantic gate가 부족했다.
- 재발 방지:
  - `verify.py`의 `gate_pass`에 `customer_meta_clean`, `placeholder_residue_clean`, `style_clean`을 무조건 AND 조건으로 편입했다.
  - 기존 `quality_clean`, `temporal_clean`, `delivery_quality_clean` 의미와 기준은 낮추지 않았다.
  - hit 보고는 `semantic_style_hits`, `ai_meta_hits`, `placeholder_residue_hits`, `role_perspective_hits`처럼 rule/count/page 중심으로 유지하고 본문 문장을 넣지 않는다.
- 검증 근거:
  - clean worktree: `test-project-phase1-verify`
  - semantic focused: 22 passed
  - harness focused: 2 passed, 7 deselected
  - 고객 데이터 접근 0, API 호출 0, PDF 렌더 0, Playwright 실행 0, commit/push 0
- 남은 후속:
  - FOLLOWUP-A: `scripts/hrun.py` RUN_STATE/retry 배선
  - NON_BLOCKING_FOLLOWUP: `scripts/hverify_pdf.py` adapter 확장
  - Phase 2는 운영자 명시 승인 전 금지

## 2026-06-24 추가: QI-2026-06-24-07 도구 우선 조사 없이 직접 진행해 반복 지연

- 증상: 이미 있는 하네스, GitHub Skill, Playwright guard, pytest 진단 순서를 먼저 고정하지 않아 같은 종류의 막힘이 반복되었다.
- 영향: 사용자가 "왜 이렇게 오래 걸리는지", "왜 계속 오류가 나는지"를 물을 정도로 개발 속도와 신뢰가 떨어졌다.
- 원인: 작업 시작 전에 "기존 Skill/MCP/도구로 해결 가능한가"를 체크하는 운영 절차가 문서와 task 템플릿에 없었다. PLAN_VERDICT=BLOCK, API 연결 실패, pytest hang, Playwright sandbox noise를 각각 별도 사건처럼 처리했다.
- 재발 방지:
  - 새 작업은 `docs/17-agent-tooling-runbook.md`의 시작 순서를 먼저 따른다.
  - `handoff/templates/ai_task.md`에 도구/Skill/MCP 사전 확인 항목을 채운다.
  - MCP는 기본 보류한다. 고객 PII, `.env`, `data/`, PDF 산출물이 걸리는 작업은 repo-native 도구와 설치된 Skills가 먼저다.
  - 오류가 나면 같은 명령을 반복하지 말고 runbook의 blocker playbook으로 원인을 먼저 분리한다.
- 연결 커밋/PR: tool-first runbook 도입 PR.
- 다음 세션 검증: 작업 시작 보고에 "사용할 기존 도구/Skill"과 "MCP 사용 여부"가 한 줄로 들어가 있는지 본다.

> 목적: 운영 중 발견한 풀이 품질 사고를 대화방 기억에만 두지 않고, 저장소 안에 남겨 다음 세션과 다른 도구가 같은 실수를 반복하지 않게 한다.
> 이 문서는 고객 원문, 생년월일, 연락처, PDF 전문을 보관하지 않는다. 필요한 경우에도 `P건`, `S건`처럼 최소 식별자만 쓴다.

## 1. 기록 원칙

이 장부는 세 가지 방식을 합쳐서 쓴다.

- Google SRE의 무비난 포스트모템 방식: 증상, 영향, 원인, 재발 방지 조치를 남긴다.
- ADR 방식: 중요한 결정은 맥락, 결정, 결과를 함께 적는다.
- eval 방식: 감으로 좋아졌다고 쓰지 않고, 테스트나 게이트 이름을 붙여 재측정 가능하게 둔다.

참고 자료:

- Google SRE Book, Chapter 15, Postmortem Culture: https://sre.google/sre-book/postmortem-culture/
- Architecture Decision Record 소개와 Nygard 계열 템플릿: https://github.com/architecture-decision-record/architecture-decision-record
- OpenAI Evals 가이드: https://developers.openai.com/api/docs/guides/evals

## 2. 반복 작업 전 필수 루틴

하네스, PDF 생성, 상담 문안, LLM 윤문 작업을 시작하기 전에 다음 파일을 먼저 읽는다.

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.claude/rules/00-immutable.md`
4. `sajugen/STATE.md`
5. `docs/14-tone-spec.md`
6. 이 파일, `docs/16-quality-incident-ledger.md`

작업 전 체크:

- 고객 질문의 핵심 축을 먼저 적는다. 예: 재회, 군복무, 학교 관계, 부동산, 자식복, 위험 시점.
- 고객 원문을 본문에 그대로 밀어 넣지 않는다. 질문 축만 추출한다.
- 원문에 없는 고유명사, 모임명, 지역 비교, 계약 상황을 새로 만들지 않는다.
- 명리 계산과 자미두수 계산은 엔진 결과만 사용한다. LLM은 계산을 만들 수 없다.
- API 윤문은 룰 기반 계산, 질문 축, PDF 게이트가 통과한 뒤에만 한다.
- API 윤문 뒤에도 같은 게이트를 다시 돌린다.

## 3. 사고 장부

### QI-2026-06-23-01: 근거 없는 고객 맥락 삽입

- 증상: 특정 1회성 풀이에서 원문에 없는 모임명과 별칭성 표현이 본문에 들어갔다.
- 영향: 고객이 "이 내용은 어디서 나온 것이냐"고 물을 수 있는 신뢰 사고.
- 원인: 이전 상담 맥락과 현재 질문 맥락의 경계를 코드와 테스트가 충분히 강제하지 못했다.
- 재발 방지:
  - `sajugen/content/delivery_quality.py`의 `context_provenance`로 premium 문서의 기대 맥락과 본문 맥락을 대조한다.
  - `tests/test_delivery_quality.py`에 근거 없는 맥락어를 실패시키는 회귀 테스트를 둔다.
  - 운영 지침: 고객 질문 원문, 운영자가 별도로 준 expected context, 계산 사실 슬롯에 없는 고유 맥락은 쓰지 않는다.
- 연결 커밋/PR: `a4852a3` PR #13, 관련 테스트 `tests/test_delivery_quality.py`.
- 남은 수동 검수: 실고객 메모가 여러 번 이어지는 경우, 이전 상담 맥락을 쓸지 운영자가 명시했는지 확인한다.

### QI-2026-06-23-02: 복합 상담 질문의 핵심 축 누락

- 증상: 복합 질문에서 시기만 크게 잡고, 집, 이사, 지역 비교, 모임 창립, 조력자, 계약 축이 초반 답변에 충분히 반영되지 않았다.
- 영향: 고객 입장에서는 "내가 물어본 것을 제대로 읽지 않았다"고 느낄 수 있다.
- 원인: consult 초반 문장이 질문 전체를 요약하지 않고 대표 축 하나로 좁혀졌다.
- 재발 방지:
  - consult 초반에 질문 축을 안전하게 추출해 반영한다.
  - raw 이름이나 민감 원문은 직접 노출하지 않고, 축 단위로만 쓴다.
  - 관련 묶음 테스트를 통과해야 한다.
- 연결 커밋/PR: `afa5c52` PR #6, `5574772` PR #12.
- 남은 수동 검수: 질문이 세 가지 이상이면 첫 화면에서 모든 핵심 축이 보이는지 읽는다.

### QI-2026-06-23-03: 재회 상담에서 실제 접촉 조건 누락

- 증상: 재회 질문에서 군복무, 학교/전공 선후배, 겹지인이라는 현실 접점이 답변 전략에 충분히 반영되지 않았다.
- 영향: 고객이 원하는 "어떻게 다가가야 하는지"에 비해 답변이 길고 추상적으로 느껴졌다.
- 원인: 재회운을 시기 중심으로만 처리하고, 접촉 가능 경로와 금지 경계를 분리하지 못했다.
- 재발 방지:
  - 군복무, 복무, 입대, 선후배, 학교, 전공, 겹지인 맥락을 관계 답변 축으로 유지한다.
  - 답변은 골라보는 점괘가 아니라, 부담 없는 접점, 금지할 방식, 짧은 첫 문장 예시까지 준다.
  - 상대가 군복무 중이면 답변 지연을 거절로 단정하지 않는다.
- 연결 커밋/PR: `c74600b` PR #7.
- 남은 수동 검수: 연애/재회 질문은 "1년 안의 체감 시기"와 "이번 달 행동"이 분리되어 있는지 본다.

### QI-2026-06-24-01: 부동산/자산/자식복/위험 시점 오분류

- 증상: 땅, 자산, 재산, 자식복, 위험 시점 질문이 대인 중심 축으로 흘렀다.
- 영향: 프리미엄 PDF에서 고객이 가장 궁금한 돈, 자식, 위험 구간 답이 약해졌다.
- 원인: 질문 라우팅과 consult 골격이 자산형 질문의 단어를 충분히 재물/가족/위험 축으로 잡지 못했다.
- 재발 방지:
  - `땅과 자산`, `자식복`, `위험 시점` 축을 질문 분석과 PDF 검증에 반영한다.
  - 땅/토지/자산 질문은 개발 계획, 세금, 명의, 현금화 시점까지 같이 보게 한다.
  - 자식복 질문은 자식의 성패 단정보다 의지, 거리, 간섭 조절을 같이 본다.
- 연결 커밋/PR: `a808136` PR #14, 관련 테스트 `tests/test_llm_sections.py`, `tests/test_delivery_quality.py`.
- 남은 수동 검수: 자산 질문은 "언제 크게 불어나는가"에 대해 대운/세운의 좋은 구간과 조심할 구간이 둘 다 있는지 본다.

### QI-2026-06-24-02: 프리미엄 PDF 말미 저밀도 페이지

- 증상: 프리미엄 PDF 마지막 쪽에 짧은 문단만 남는 저밀도 페이지가 생겼다.
- 영향: 9만원대 상품에서 분량과 완성도가 약해 보인다.
- 원인: HTML/PDF 페이지 나눔에서 말미 단락 고아/과부 처리가 충분하지 않았다.
- 재발 방지:
  - `report.html.j2`에 `orphans:4; widows:4`를 둔다.
  - `render/verify.py`의 `low_density_pages`, `no_orphan` 결과를 확인한다.
  - 프리미엄 PDF는 전체 페이지 수뿐 아니라 말미 밀도를 본다.
- 연결 커밋/PR: `a808136` PR #14, 관련 테스트 `tests/test_render_verify.py`.
- 남은 수동 검수: 최종 PDF는 첫 장, consult 장, 마지막 두 장을 반드시 육안 확인한다.

### QI-2026-06-24-03: "또렷" 계열 반복으로 AI 느낌 발생

- 증상: "또렷하게", "또렷합니다" 계열 표현이 반복되어 AI 문장처럼 보였다.
- 영향: 사람 상담가가 쓴 느낌이 약해지고, 고객 피드백에서 기계적인 인상이 생겼다.
- 원인: 자미/오행 설명에서 같은 표현을 안전한 기본어처럼 반복 사용했다.
- 재발 방지:
  - `style_lint.py`와 `delivery_quality.py`에서 실패/경고 기준을 둔다.
  - 같은 형용사를 반복해 깊이를 만드는 방식은 금지한다.
  - 계산 사실은 분명히 말하되, 표현은 고객 질문의 생활어로 바꾼다.
- 연결 커밋/PR: `6e27806` PR #10, `f83fe49` PR #9.
- 남은 수동 검수: 문서 안에서 같은 단어가 눈에 띄면 API 윤문 전에 룰 문장부터 고친다.

### QI-2026-06-24-04: Playwright sandbox 진단 소음

- 증상: Codex sandbox에서 Playwright subprocess probe가 Windows pipe 생성 문제로 소음성 예외를 냈다.
- 영향: 실제 PDF 로직 문제가 아닌데 작업이 실패처럼 보이고 시간을 낭비했다.
- 원인: sandbox 환경에서 브라우저 subprocess가 막힐 수 있음을 테스트 helper가 먼저 감지하지 못했다.
- 재발 방지:
  - `tests/playwright_guard.py`에서 Codex sandbox를 감지하면 probe를 skip한다.
  - Playwright가 필요한 테스트는 guard 결과를 먼저 확인한다.
- 연결 커밋/PR: `e2060fc` PR #3.
- 남은 수동 검수: PDF 재생성 문제와 sandbox probe 문제를 분리해 보고한다.

### QI-2026-06-24-05: API 윤문 투입 순서 혼동

- 증상: 룰 기반 초안 품질 문제가 남아 있는데 API 윤문으로 해결하려는 흐름이 생겼다.
- 영향: LLM이 계산 사실을 바꿀 수는 없으므로, 질문 축 누락이나 게이트 실패를 덮는 데 쓸 수 없다.
- 원인: PDF 생성, 룰 골격, LLM 윤문, 하네스 검증의 순서가 작업 중에 섞였다.
- 재발 방지:
  - 순서 고정: 계산/질문 축 통과 -> 룰 PDF gate PASS -> API 윤문 -> 동일 gate 재실행 -> 관리자 검수.
  - API 윤문은 말투와 문장 흐름만 다룬다.
  - API 윤문이 새 사실, 새 고유명사, 새 시기를 만들면 실패다.
- 연결 코드: `sajugen/content/llm_polish.py`, `sajugen/content/llm_sections.py`, `scripts/hrun.py`.
- 남은 수동 검수: API 윤문본은 "사실 추가 없음"과 "질문 축 유지"를 별도로 읽는다.

### QI-2026-06-24-06: PS 5.1 UTF-8 no-BOM 파싱 실패

- 증상: PowerShell 5.1에서 `scripts/ai-harness.ps1`의 한글 문자열이 깨져 파서 오류가 났다.
- 영향: 하네스 SelfTest와 DryRun이 환경에 따라 실패했다.
- 원인: PS 5.1은 BOM 없는 스크립트를 ANSI 코드페이지로 읽을 수 있고, UTF-8 한글 바이트가 따옴표 해석을 깨뜨렸다.
- 재발 방지:
  - `scripts/ai-harness.ps1`은 ASCII-only를 유지한다.
  - `tests/test_ai_harness_contract.py`에 ASCII-only 계약 테스트를 둔다.
- 연결 커밋/PR: PR #2 Phase 2A, `tests/test_ai_harness_contract.py`.
- 남은 수동 검수: PowerShell 스크립트에 한글 주석/문자열을 넣지 않는다. 한국어 설명은 문서에 둔다.

### QI-2026-06-24-07: 연애·재회·결혼 답변의 시기 직답 지연

- 증상: 연애·재회·결혼 질문에서 고객이 가장 먼저 알고 싶은 1년 안의 시기, 접근 방식, 멈춤 기준이 뒤로 밀리거나 모호하게 보였다.
- 영향: 고객이 "그래서 언제, 어떻게 해야 하는지"를 바로 잡지 못하고, 위로는 있어도 상담 밀도가 낮게 느껴질 수 있다.
- 원인: 연애 카테고리 안에서 재회, 새 만남, 결혼 축을 한 문단으로 처리해 하위 질문별 행동 기준이 약해졌다.
- 재발 방지:
  - 재회는 연락·접점·멈춤 신호를 초반에 둔다.
  - 새 만남은 소개팅·가벼운 첫 만남·서두름 주의를 초반에 둔다.
  - 결혼은 현재/미래 배우자 기준, 생활 기준, 돈 관리, 가족과의 거리를 초반에 둔다.
  - `delivery_quality.py`에서 유료 연애 축의 근시점, 실사용 행동, 명리·자미 두 관점을 확인한다.
  - `tests/test_llm_sections.py`, `tests/test_delivery_quality.py`, `tests/test_client_tone.py`에 하위 축 회귀를 둔다.
- 연결 커밋/PR: 진행 중.
- 남은 수동 검수: API 윤문 전 룰 본문에서 "좋은 구간/조심할 구간/행동/멈춤"이 앞쪽에 보이는지 먼저 읽는다.

## 4. 새 사고를 추가할 때 템플릿

```
### QI-YYYY-MM-DD-NN: 제목

- 증상:
- 영향:
- 원인:
- 재발 방지:
- 연결 커밋/PR:
- 남은 수동 검수:
```

## 5. 다음 세션용 지시문

새 대화방에서 이어갈 때는 아래처럼 시작한다.

```
현재 저장소 C:\Users\pc\test-project에서 작업한다.
먼저 AGENTS.md, CLAUDE.md, .claude/rules/00-immutable.md, sajugen/STATE.md,
docs/14-tone-spec.md, docs/16-quality-incident-ledger.md를 읽고 시작해라.
계산은 LLM에 맡기지 말고, 고객 질문 축을 먼저 추출해 consult 초반에 반영해라.
PDF 재생성/LLM/API 호출/커밋/푸시는 명시 승인 전 금지다.
오류가 나면 추측하지 말고 관련 코드, 테스트, 공식 문서 또는 검증된 자료를 확인한 뒤 결론을 내라.
```

