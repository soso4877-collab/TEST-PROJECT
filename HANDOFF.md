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
