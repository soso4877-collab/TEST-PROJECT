# HANDOFF — 2026-07-10 (Codex customer-purge CLI까지 완료)

프로젝트: `C:\Users\pc\test-project` (sajugen — 사주+자미 종합 PDF 리포트 생성기)
브랜치: `codex/gunghap-relationship-quality` · HEAD `c8b48ad`
역할: Codex 구현 세션 인계. 커밋/푸시/PDF 재생성/LLM 호출 없음.

## 현재 상태
- 후속·재방문 상담 T0~T4와 수정 라운드 A/B/C는 커밋 완료 상태.
- 남은 코드 작업으로 발주된 `handoff/codex-customer-purge-cli.md`도 구현 완료 후 커밋됨: `c8b48ad feat(sajugen): 단골 식별자 차등 파기 CLI customer-purge (E9)`.
- 현재 `git status -sb` 기준 코드 변경은 없음. 워킹트리 변경은 `HANDOFF.md`뿐이고, 리뷰/지시문 문서가 미추적 상태로 남아 있음.
- 미추적 파일: `REVIEW-FEEDBACK.md`, `handoff/codex-customer-purge-cli.md`, `handoff/codex-followup-fixups.md`, `handoff/codex-ilji-tension-followup.md`, `handoff/codex-metadiscourse-t0-4.md`, `handoff/design-question-adaptive.md`.

## 완료한 것
- T0/T0-④: 상담 유도형·면책 선언형·의료 회피형 메타발화 제거, 월운 표기 규약, 상대시제 절기경계 lint 및 회귀.
- T1~T4: customers/orders 후속 스키마, 후속 답변 게이트, 저장 사실 기반 컴포저, `customer-find`/`gen-followup` CLI와 상태머신 배선.
- 수정 라운드 A/B/C: 메타발화 제거 검증, `.claude/rules/content.md` 의료 규칙 문서 정합, `compose.py` allowed_years 빈 경계와 "내년" 상대연도 factcheck 백스톱 회귀.
- E9 추가 작업: `customer-purge --alias ... [--yes] [--db ...]` CLI. `OrderStore.purge_identifier(alias)`만 호출해 `customers.name_masked`만 NULL 처리하고, `purged_at` 기록·orders/report_json/alias 보존. `tests/test_customer_purge.py`로 `--yes`, 확인 프롬프트, 없는 alias exit 1, report 보존을 검증.

## 최근 검증 증거
- Codex 샌드박스 최종: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **668 passed / 31 skipped / exit 0**.
- Codex 샌드박스 골든: `.\.venv\Scripts\python.exe -m pytest tests/ -q -k golden` → **28 passed / 671 deselected / exit 0**.
- 신규 customer-purge 단독: `.\.venv\Scripts\python.exe -m pytest tests/test_customer_purge.py -q` → **3 passed / exit 0**.
- `git diff --check` → exit 0, LF→CRLF 경고만 있음.
- `git diff --name-only -- calc input sajugen/calc sajugen/input` → 출력 없음(계산/input 무변경).
- 기준환경 교차리뷰 기대값: 라운드4 기준 **692 passed / 4 skipped** 대비 customer-purge 신규 테스트 3개 증가 → **695 passed / 4 skipped** 예상.

## 수정 파일 구분
- 이번 customer-purge 커밋 핵심: `sajugen/cli.py`, `tests/test_customer_purge.py`.
- 후속 기능 커밋 핵심: `sajugen/followup/*`, `sajugen/store/orders.py`, `sajugen/order_flow.py`, `sajugen/cli.py`, 관련 `tests/test_followup_*.py`.
- 문안·정책 정합 커밋 핵심: `sajugen/content/rules.py`, `sajugen/content/llm_sections.py`, `sajugen/content/temporal_lint.py`, `.claude/rules/content.md`, `docs/03-engine-validation-plan.md`, 관련 테스트.
- 현재 미커밋 수정 파일: `HANDOFF.md`만.

## 확인하지 못한 것 / 남은 위험
- Codex는 PDF 재생성, LLM 호출, `harness/profiles/local/**` 열람을 하지 않음.
- 기준환경 4-skip 전체 검증은 라운드5 교차리뷰에서 실행 필요.
- 운영 DB에 대한 실제 `customer-purge` 실행은 별도 운영자 승인·백업 후 진행 필요.
- 미추적 리뷰/지시문 문서들은 커밋 포함 여부를 운영자가 결정해야 함. `HANDOFF.md`도 이전 2026-07-07 메모와 이번 2026-07-10 메모가 같이 미커밋 상태.

## 다음 행동
1. 라운드5 교차리뷰: `customer-purge` diff와 `tests/test_customer_purge.py`를 기준환경에서 검증한다.
2. 기준환경 전체 테스트 예상: **695 passed / 4 skipped**(라운드4 692/4 + 신규 3).
3. 리뷰 PASS 후 `HANDOFF.md`와 미추적 handoff/review 문서의 커밋 포함 여부를 결정한다.
4. 운영 반영 전에는 실제 DB 백업 후 `python -m sajugen.cli customer-purge --alias <alias> --yes --db <운영DB>` 경로를 사용한다.

---

# HANDOFF — 2026-07-07 (Codex 후속·재방문 상담 T0~T4 구현)

프로젝트: `C:\Users\pc\test-project` (sajugen — 사주+자미 종합 PDF 리포트 생성기)
브랜치: `codex/gunghap-relationship-quality` · HEAD `f38d1e3`
요청 패킷: `C:\Users\pc\.claude\plans\ai-brain-50-decisions-2026-07-07-sajugen-shimmering-popcorn.md`
역할: Codex 구현 세션. 패킷은 재해석하지 않고 T0부터 T4까지 순서대로 실행. 모순/범위 이탈로 판단해 멈춘 항목 없음.

## 현재 상태
- T0~T4 구현 완료. 커밋/푸시/PDF 재생성/LLM 호출 없음.
- 최종 전체 테스트 GREEN: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **660 passed / 31 skipped / exit 0** (`142.48s`).
- T0 완료 시점 별도 보고 기준도 충족: 전체 테스트 GREEN + `상담에서` grep 0건.
- `git diff --check` exit 0. 단, 기존 파일 개행 정책에 따른 LF→CRLF 경고만 출력됨.

## 완료한 것
- T0 문구 교체·월 표기 규약·상대시제 절기경계: `상담에서` 원천 문구 제거, 월 표기 `간지월(절기명 - 양력 M/D~M/D)` 고정, 상대시제 절기경계 lint 추가, LLM prompt/docs/tests 갱신.
- T1 고객 축: `customers` 테이블과 `orders.alias/parent_order_id/kind` additive migration, 고객 연결/식별자 삭제 API, 주문 스키마 회귀 추가.
- T2 후속 답변 가드: `sajugen/followup/answer_gate.py` 추가, 23년 리포트 미참조·출처 없는 답변·금칙/형식 결함 차단 테스트 추가.
- T3 후속 상담 합성: `sajugen/followup/compose.py` 추가, 저장된 Report23만 근거로 follow-up 입력을 구성하고 follow-up 질문·출처 슬롯을 보존.
- T4 운영 경로: `OrderStore.issue_final_text`, `order_flow.run_followup`, CLI `customer-find`/`gen-followup` 추가. 기존 단일 `gen` 호출 테스트는 Typer 다중 명령 구조에 맞춰 보정.

## 검증 증거
- T0 후: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **631 passed / 31 skipped / exit 0**.
- T1 후: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **634 passed / 31 skipped / exit 0**.
- T2 후: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **651 passed / 31 skipped / exit 0**.
- T3 후: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **656 passed / 31 skipped / exit 0**.
- T4 최종: `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **660 passed / 31 skipped / exit 0**.
- grep: `rg -n "상담에서" sajugen -g '*.py' -g '*.md' -g '!render/out/**'` → **0건**.
- whitespace: `git diff --check` → **exit 0**. LF→CRLF 경고만 있음.

## 수정 파일
- 기존 파일: `docs/03-engine-validation-plan.md`, `sajugen/calc/advanced.py`, `sajugen/cli.py`, `sajugen/content/llm_sections.py`, `sajugen/content/rules.py`, `sajugen/content/temporal_lint.py`, `sajugen/order_flow.py`, `sajugen/store/orders.py`, `tests/test_gunghap.py`, `tests/test_p5.py`, `tests/test_quality_lint.py`, `tests/test_temporal_month.py`.
- 신규 파일: `sajugen/followup/__init__.py`, `sajugen/followup/answer_gate.py`, `sajugen/followup/compose.py`, `tests/test_followup_compose.py`, `tests/test_followup_flow.py`, `tests/test_followup_gate.py`, `tests/test_followup_schema.py`, `tests/test_month_notation.py`.
- 기존 더티/미추적 주의: `HANDOFF.md`, `REVIEW-FEEDBACK.md`, `handoff/codex-ilji-tension-followup.md`는 이번 구현 전부터 존재하던 기록물/미추적 파일이다. 이번 섹션만 새로 추가했다.

## 확인하지 못한 것 / 남은 위험
- `scripts/hrun.py` PDF 산출 검증은 실행하지 않음. Codex 금지 범위와 로컬 harness profile 열람 금지 때문에 `harness/profiles/local/**`도 읽지 않음.
- LLM 호출과 PDF 재생성은 하지 않음.
- DB migration은 additive/idempotent 테스트로 검증했지만, 실제 운영 DB 적용은 별도 승인·백업 후 실행 필요.

## 다음 행동
1. 신선 컨텍스트 검증 세션에서 이 diff와 위 테스트 증거를 교차리뷰한다.
2. 교차리뷰 GREEN 후 의미 단위 커밋을 T0 → T1 → T2 → T3 → T4 순서로 나눌지 결정한다.
3. 운영 산출 검증이 필요하면 Codex 금지 범위를 벗어나므로 운영자 승인 세션에서 `hrun.py`를 별도 실행한다.

---

# HANDOFF — 2026-07-07

프로젝트: `C:\Users\pc\test-project` (sajugen — 사주+자미 종합 PDF 리포트 생성기)
브랜치: `codex/gunghap-relationship-quality` · HEAD `f38d1e3` · origin 대비 **ahead 2**(미push)
세션 시작 커밋: `786ac29` → 현재 `f38d1e3` (이번 라운드 신규 2커밋: `75c65f1` 기능 + `f38d1e3` FIX)
역할 분리: 구현 = Codex(GPT), 계획·검증 = Claude(이 세션). 참조 [[feedback-claude-plan-verify-codex-implements]].

## 완료한 것 (검증자 신선 컨텍스트 실측 — 최종 판정 PASS)

### 기능: 궁합 일지 상호작용 판정 확장 (형·해·파·원진) + consult 대칭 배선
- 커밋 `75c65f1` — 육해·육파·원진·자형(辰午酉亥)·子卯상형을 `sajugen/calc/partner.py`에 추가(삼형 완전판은 defer, 寅巳=해만). 소비처 배선: `sajugen/gunghap.py:_pair_slot`(궁합 상품) + `sajugen/content/rules.py:partner_block`(개인 consult 경로) 대칭. `docs/03-engine-validation-plan.md §1-1`에 채택표를 SSOT로 기록(코드보다 먼저). 표 docs↔code 1:1 + 표준 명리 정설 부합 확인.
- 커밋 `f38d1e3` (FIX) — render-gate 블로커 해소: 신규 해(害) 문안의 외래어 "리듬"→"흐름". `business` 폴백은 `normalize_loanwords`를 미경유(`sajugen/gunghap.py:1016` 조기 반환)라 외래어가 PDF로 직행 → `loanword_clean=False`로 육해 쌍 business 궁합 빌드가 하드게이트 실패였음. 근본원인 2층(감지 갭)도 동봉: 가드 유닛 테스트의 normalize 사전적용 은폐 정정 + "리듬 스윕"(`tests/test_raw_term_sweep.py`)에 두 소비처 실제 출력 추가.

### 이 결함을 잡은 경로 (교훈)
초기 코드-레벨 리뷰의 "no blocker" 판정은 불완전(정적/유닛 GREEN). **운영자 지시로 돌린 합성 실렌더가 실경로 결함(loanword)을 포착.** "정적/유닛 GREEN ≠ 실경로 안전" — vault 기록 대상.

## 수정한 주요 파일 (전체 경로)
- `C:\Users\pc\test-project\sajugen\calc\partner.py` (표·PartnerFacts 필드·독립 판정)
- `C:\Users\pc\test-project\sajugen\gunghap.py` (`_pair_slot` 소비 + 해 문안 흐름)
- `C:\Users\pc\test-project\sajugen\content\rules.py` (`partner_block` 소비 + 해 문안 흐름)
- `C:\Users\pc\test-project\sajugen\relationship\context.py` (`_RAW_REPLACEMENTS` 순화)
- `C:\Users\pc\test-project\docs\03-engine-validation-plan.md` (§1-1 채택표)
- `C:\Users\pc\test-project\tests\test_partner.py` · `tests\test_gunghap.py` · `tests\test_couple_language.py` · `tests\test_raw_term_sweep.py`

## 실행한 검증 명령과 결과 (검증자 전 리소스 환경)
- `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest tests/ -q -rs` → **654 passed / 4 skipped / exit 0** (skip 4건은 전부 E2E opt-in — 운영자 승인/`SAJUGEN_RUN_E2E` 게이트).
- 변경 관련 파일만: `pytest tests/test_partner.py tests/test_gunghap.py tests/test_raw_term_sweep.py tests/test_couple_language.py -q` → **74 passed / 0 skipped** (변경 검증 테스트가 실제 실행됨 = GREEN 착시 아님).
- 합성 3인 business 룰전용 렌더(PII 0, `build_gunghap(render=True)`) → **`gate_pass=True` · `loanword_clean=True` · false GATE_KEYS=[]** (블로커 해소 실측).
- 집계 주의: Codex 구현 환경은 627 passed / 31 skipped(합계 658 동일) — 샌드박스 리소스 부재(chromium/veraPDF/API키/KASI)로 27건 추가 skip. **기준 환경 = 검증자 654/4.**

## 확인하지 못한 것 / 남은 위험
- **미push**: origin 대비 ahead 2. 유실 방어용 push는 운영자 지시 시.
- **main 전진·실발송 미완**: feat는 베이스라인(main) 아님. main ff·실발송 전 운영자 최종 검수 게이트 남음.
- **비블로커 관찰**: 합성 렌더에서 `domain_term_repetition` **경고**(결·구조·자리 반복) — `delivery_quality_clean=True`(게이트 아님), 룰전용 미니 리포트라 과장. `_ILJI_TENSION_KO`의 "결/구조" 의존 문안 다양화는 선택 개선(미착수).
- **자형/상형 실렌더 톤 미확인**: 합성 렌더는 子·未·酉(해·원진·파)만 커버. 자형(辰辰 등)·상형(子卯)의 실렌더 문안 인상은 미검수(문안 register 동일이라 위험 낮음, 필요 시 합성 프로파일 추가).
- **미커밋 프로세스 산출물**: `C:\Users\pc\test-project\REVIEW-FEEDBACK.md`(검증 판정 기록), `C:\Users\pc\test-project\handoff\codex-ilji-tension-followup.md`(Codex 지시문) — untracked. 커밋 여부는 운영자 판단.

## 다음 행동 (구체적 첫 스텝부터)
1. (선택) `git push origin codex/gunghap-relationship-quality` — 유실 방어(운영자 지시 시).
2. main 전진 원하면: pytest 전체 GREEN 확인 후 `main`을 이 feat로 fast-forward(머지 커밋 없이 선형). 계산(`calc/`) 변경 포함이라 골든 회귀는 654에 포함됨.
3. 관계 품질 추가 작업 후보(미착수): 자미 관계자리 실데이터 배선(`relationship/context.py:_ziwei_context` 고정 템플릿 탈피), 정량 궁합 지표(내부 grounding 한정), relationship 2인 골든 프로파일 추가. 착수 전 플랜 모드 + 운영자 승인.

## 참고할 vault 노트 / 문서
- `C:\Users\pc\test-project\REVIEW-FEEDBACK.md` (이 라운드 검증 판정 전문)
- `C:\Users\pc\test-project\handoff\codex-ilji-tension-followup.md` (TASK 1·2 + §5 FIX 지시문)
- `C:\Users\pc\test-project\docs\03-engine-validation-plan.md` §1-1 (형·해·파·원진 채택표 SSOT)
- `C:\Users\pc\test-project\docs\16-quality-incident-ledger.md` (품질 사고 장부 — 이 loanword 건 기록 대상)
- [[feedback-claude-plan-verify-codex-implements]] · [[할루시네이션-방어]]

---

# HANDOFF — 2026-07-06

프로젝트: `C:\Users\pc\test-project` (sajugen — 사주+자미 종합 PDF 리포트 생성기)
브랜치: `codex/gunghap-relationship-quality` · main·origin·HEAD 전부 `00a5938` 정합(clean tree)
세션 시작 커밋: `100f4d9` → 세션 종료 `00a5938` (이번 세션 21커밋)
SSOT: 세션 시작 시 `sajugen/STATE.md` 최상단 앵커 먼저 읽기(진행상태 정본).

## 완료한 것 (전부 pytest GREEN 검증됨 — 각 Phase 커밋에 증거)

### 다층 검증 로드맵 Phase 0~8 전부 완주 ("운영자보다 먼저 버그를 잡는" 프로세스)
- **Phase 0** `8db7aa3` — ref_date 오늘 기본값. 운영자 대면 CLI(gunghap·integrated)·hrun regen이 ref_date 미지정 시 오늘 주입. 라이브러리(build_gunghap/build_integrated_full) None→6-13 폴백은 유지(테스트 결정론). 신규 `sajugen/refdate.py`.
- **Phase 1** `519f7a1` — 게이트 키 SSOT + 요약↔원천 정합 계약(C4 관측 갭). `sajugen/render/verify.py`에 `GATE_KEYS`(20키 상수), `gate_pass = all(r[k] for k in GATE_KEYS)`. `scripts/hsummary.py`·`scripts/hrun.py`가 GATE_KEYS에서 파생(수동 목록 제거). 실결함 수확: layout_geometry_clean·text_layer_ok 등이 요약·retry에서 누락되던 갭.
- **Phase 2** `7e2e045` — dead-param 정적 스캐너(C2). `scripts/deadparam_scan.py`(stdlib AST) + `tests/deadparam_allowlist.txt`(참 사유 필수). 즉시 제거: geukguk(day_master)·analyze(page_texts).
- **Phase 3** `9f9698e`·`6b4e7a1`·`603f1fd`·`b98e784` — 골격×lint 매트릭스(C1) + 게이트 커버리지(C3) + 프록시 레지스트리(C5). `docs/20-gate-coverage.md`, `tests/test_gate_registry.py`(docs↔live GATE_KEYS 양방), `tests/test_skeleton_lint_matrix.py`(완전성 단언), `tests/test_lint_properties.py`(hypothesis).
- **Phase 4** `df1b362`·`10372f7` — 이질 렌즈 스윕 인프라(L2 advisory, API 0 빌드). `scripts/hsweep.py` + `harness/prompts/sweep/lens_*.md` 5종. 백엔드 주입형·PII fail-closed·비용 상한 $3·렌즈≠judge 모델·게이트 무접촉(구조적).
- **Phase 5** `6fd4655` — 설계 논쟁 프로토콜. `.claude/agents/sg-design-critic.md`(Opus·읽기전용·승자 선택 안 함) + `handoff/templates/design_debate.md`(one-way door 트리거만).
- **Phase 6** `6e71b3f` — 운영 스킬. `.claude/skills/audit/`·`adjacent/`·`done/` (+ `.gitignore`에 `!.claude/skills/` 화이트리스트 추가 — 안 하면 미커밋됨).
- **Phase 7** `03055e9` — 이식 키트 vkit. `docs/21-verification-kit.md` + `handoff/kit/`(README·manifest.template.json·논쟁기록) + `.claude/skills/vkit/`. Phase 5 프로토콜 첫 실전(sg-design-critic 실제 소환·설계 개선).
- **Phase 8** `9aa1b73` — 플레이북 배선. `docs/19-operator-playbook.md`에 스킬 연결·경고 다이어트 원칙·논쟁 트리거 표·세션 템플릿 L0~L4 줄.

### 그 외
- **P4 customer2 합성 드라이런** `c6d2c52` (운영자 승인 실 API 지출) — 후보30→생존0→확정0, **비용 $0.617**(상한 $3의 21%), PII 0 실측. 발견·선제수정: mask_for_api가 한글 형식 생년월일 못 막던 갭 → self_civils 정밀 마스킹 추가.
- **age 팬텀 파라미터 체인 제거** `00a5938` (QI-2026-07-06-01) — order_flow→pipeline→render_pdf→render_html 4단계 미소비 인자 제거. 순수 dead-code(출력 불변).
- **세션 초반(로드맵 이전)**: `9eec8d8`~`493a4cf` — 1장 직답 문단 제거+frontload 게이트 철거(운영자 지시), h153 픽스처 P5 lint 동기화(룰 전용 재렌더·무과금), 임시 probe 파일 정리.
- **AI-Brain vault 지식 기록**(git 미커밋 — weekly-review가 백업): `C:\Users\pc\AI-Brain\50_Decisions\다층-검증-키트-vkit.md`, `C:\Users\pc\AI-Brain\20_Coding-Style\팬텀-파라미터-소비처-배선.md`, Brain-Index 등재, auto memory 포인터.

## 수정한 주요 파일 (신규/핵심)
- 신규: `sajugen/refdate.py`, `scripts/deadparam_scan.py`, `scripts/hsweep.py`, `harness/prompts/sweep/lens_*.md`(5), `docs/20-gate-coverage.md`, `docs/21-verification-kit.md`, `handoff/kit/*`, `.claude/agents/sg-design-critic.md`, `.claude/skills/{audit,adjacent,done,vkit}/SKILL.md`, `handoff/templates/design_debate.md`, 신규 테스트 8개(test_gate_contract·gate_registry·skeleton_lint_matrix·lint_properties·deadparam_scan·hsweep_contract·design_debate_protocol·ops_skills·verification_kit·playbook_wiring).
- 핵심 수정: `sajugen/render/verify.py`(GATE_KEYS), `scripts/hsummary.py`·`scripts/hrun.py`(파생), `sajugen/render/pdf.py`·`sajugen/pipeline.py`·`sajugen/order_flow.py`(age 제거), `sajugen/config.py`(sweep 모델 역할), `docs/16-quality-incident-ledger.md`, `docs/19-operator-playbook.md`, `sajugen/STATE.md`.

## 실행한 검증 명령과 결과
- 전체: `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest tests/ -q` → **643 passed / 4 skipped / exit 0** (세션 시작 610 → +33, 회귀 0).
- 발급 경로 회귀: `pytest tests/test_orders.py tests/test_final_render_gate.py -q` → GREEN (APPROVED-전-발송 상태머신 불변).
- dead-param 게이트: `./.venv/Scripts/python.exe scripts/deadparam_scan.py` → 미해결 0.
- P4 드라이런: PII 프리플라이트(무과금) SAFE → 실 API 스윕 $0.617.
- 주의: 터미널 cp949 한글 깨짐 있음 — 파이썬 실행 시 `PYTHONUTF8=1` 권장.

## 확인하지 못한 것 / 남은 위험
- **실 파일럿 계측 미실측(미검증)**: customer2는 정제 납품물이라 생존0(M=0) → judge 경로 미발화, 정밀도 K/M 산출 불가. 실 계측은 검수 전 신선 발송물 필요.
- **P4 PII residual**: 이름·날짜 belt는 있으나 지명·직장 등 타 PII 클래스는 프롬프트+벨트로 축소만(완전제거 보장 아님 — docs/16 명시). 리포트는 gitignored.
- **customer3 v9 미생성**: customer3 생년월일시·성별·질문(PII, 저장소 밖)이 없어 미실행.

## 다음 행동 (구체적 첫 스텝부터)
1. 세션 시작: `sajugen/STATE.md` 최상단 앵커 → `AGENTS.md` → `.claude/rules/00-immutable.md`·`10-methodology.md` 순 Read.
2. **실 파일럿 계측 또는 customer3 v9**를 하려면: 운영자에게 customer3 입력(생년월일시·성별·질문) 요청 → API 0 룰 전용 프로브 PASS 선검증 → 승인 시 LLM 재생성/스윕. 스윕 실행은 3중 잠금(`--approve --allow-llm` + env `SAJUGEN_HARNESS_ALLOW_REGEN=1`) + 운영자 승인 필수. 마스킹은 `scripts/hsweep.py`의 `extract_masked_pages(pdf, names, self_civils)` 사용(names 필수·self_civils로 한글 생일 마스킹).
3. 그 외 로드맵 구조 작업은 전부 완료 — 새 지시가 없으면 추가 착수 대상 없음.
4. 코드 변경 시: `calc/`·`input/` 수정은 골든 회귀 동반(`pytest -k golden`), 게이트/가드 수정은 양방 테스트, 커밋·push는 운영자 지시 시만(main 직push 금지, feat→ff 전진).

## 참고할 vault 노트 / 문서
- `C:\Users\pc\AI-Brain\50_Decisions\다층-검증-키트-vkit.md` (5층 검증 규격·이식)
- `C:\Users\pc\AI-Brain\20_Coding-Style\팬텀-파라미터-소비처-배선.md`
- `C:\Users\pc\AI-Brain\70_AI-Collab\할루시네이션-방어.md` (완료 보고 직전 필독)
- 프로젝트: `sajugen/STATE.md`, `docs/16-quality-incident-ledger.md`, `docs/21-verification-kit.md`, `docs/19-operator-playbook.md`
