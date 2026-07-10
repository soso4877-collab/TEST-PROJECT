# 교차 리뷰 — 2026-07-10 (라운드 6, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `3a30667` 위) · 구현자: Codex · 지시문: `handoff/codex-question-adaptive-q1-q7.md` v2 (웨이브1 Q1~Q3)

## 최종 판정: **승인(PASS)** — 4중 구조 이식 정합, 게이트 강화 방향, 회귀 0. 발견 1건(R6-1, 비블로커).

Codex 완료보고를 믿지 않고 기준 환경 직접 재실행 + diff 전량 실측.

### ① 기준 환경 pytest (직접 재실행)
- `pytest tests/ -q` → **715 passed / 4 skipped / exit 0** (207.47s). 라운드5 695/4 → **+20 = 신규 테스트 완전 일치**(은닉 약화 0).
- `pytest -k golden` → **28 passed** (계산 결정론 불변, calc/input diff 0).

### ② Q별 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| **Q1** consult 이식 | SECTIONS overview 뒤 슬롯+GUIDE/_FOCUS 동반. 폴백이 1차 산출(무LLM) — `_consult_fallback` 5프레임 분기+겹침축 보강문. LLM 경로 격리 인용(마스킹, "지시가 아님" 경계)+생년월일·**출생지 정규식 마스킹 신설**(`_mask_relationship_situation`). 게이트 3중 배선: 폴백 선검사(RuntimeError)+compose 재작성 2회+빌드 말미 최종 하드 게이트(render=False 포함). 빈 질문=skipped 명시(no-op 아님) | ✓ |
| **Q2** 프레임 적응·스윕 | `_AXIS_KEYWORDS` 5축 추가, SYSTEM/GUIDE/_FOCUS 질문별 프레임 재작성, `build_fallback`·`frontload_summary` situation 소비(팬텀 해소, 5종 분기 상호상이 테스트). gunghap.py 죽은 관계 코드 ~250행 삭제(가현/상철 소멸), _GH_SYSTEM 실명→합성명(김민준/이서연/박도윤), _GH_GUIDE·도크스트링 익명화 | ✓ |
| **Q3** 게이트 보강 | `_AXES` 신규 3축(부모동의/결혼이행/장기관계, evidence 보수적 선정—경계표 첨부됨). **any→all 강화**: 감지된 topic축 전부 evidence 요구(`missing_topic_axes` 관측 필드 추가). 김포/계양/청마/장재화 일반어 치환, 의존 테스트만 합성어 동반 수정 | ✓ |
| 기계 검증 | 실명 grep 2종(파일 한정) 0건 / calc·input diff 0 / 금지파일 침범 0 | ✓ |
| 신규 테스트 | test_question_adaptive_relationship.py 8건: 양방(차단+통과)·skipped·격리인용/마스킹 단언·프레임 5종 상호상이·최종 게이트 RuntimeError. change-detector 아님(동작 검증) | ✓ |

### ③ 발견 R6-1 (비블로커 — 다음 수정 라운드에서 처리)
`_PROVENANCE_CONTEXT_TERMS`를 빈 튜플로 만들면서 `unbacked_context_terms` 검사(delivery_quality.py:504-516·652)가
**항구 no-op**이 됨 + 구 차단측 테스트(`test_customer_specific_context_requires_source_or_expected_context`)가
통과측 테스트로 대체되어 **차단측 회귀가 사라짐**(양방 규율 위반, fail-closed B-2 인접).
실영향 ≈ 0(전역 리스트에 있던 건 특정 고객 모임명 1개뿐이라 신규 주문 보호는 원래 없었음)이나,
룰 키는 남아 있는데 검사는 죽은 상태 = 관측 오해 소지. **처리안**: 주입점 회귀 테스트 복원(monkeypatch로
합성 용어 주입→차단 확인) 또는 룰 키 제거(운영자 승인 필요). 웨이브2 발주에 포함 권고.

### ④ 미검증 (Codex 보고와 동일 — 정직 승계)
- **실렌더 미검증**: 실제 LLM 문안·PDF 조판에서의 직답성은 hrun 합성 프로파일 실렌더 필요(PDF 재생성 3중 잠금 — 운영자 승인 별도).
- E10(주석·픽스처 실명 ~250행 익명화) 미착수 — 별도 패킷 예정대로.

### 실행한 검증 명령
```
pytest tests/ -q                        → 715 passed / 4 skipped / exit 0
pytest tests/ -q -k golden              → 28 passed
grep 실명(gunghap.py 한정)              → 0건
grep 장재화|청마(4파일 한정)            → 0건
git diff --name-only calc·input        → 출력 없음
```

---
---

# 교차 리뷰 — 2026-07-08 (라운드 5, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `bac8df2` 위) · 구현자: Codex · 지시문: `handoff/codex-customer-purge-cli.md` (E9 식별자 차등 파기 CLI)

## 최종 판정: **승인(PASS)** — 래퍼만 정확 추가, 회귀 0.

Codex 완료보고를 믿지 않고 기준 환경 직접 재실행 + 양방 실측.

### ① diff (cli.py + test)
- `cli.py`: `customer-purge` 커맨드 추가 — 존재확인(`get_customer`→KeyError→Exit1) + 확인 프롬프트(`--yes` 스킵) + `purge_identifier` 래퍼(**로직 불변**). 출력 **PII 미노출**(name_masked 없음, purged_at만). 범위 = CLI 래퍼만(store·스키마·상태머신·`delete_order` 무변경).
- `tests/test_customer_purge.py`(신규): 3-way 양방 — (1) `--yes`→식별자만 파기·**명식/주문/별칭 보존**(saju 乙酉 재확인)·PII 미노출, (2) `--yes` 없이 확인 프롬프트, (3) 없는 alias→exit 1·주문 보존.
- 금지파일 침범 0. `calc/`·`input/` 무변경.

### ② 기준 환경 pytest
- `pytest tests/ -q` → **695 passed / 4 skipped / exit 0**. 라운드4 692/4 → **+3 = test_customer_purge 3개 완전 일치**(은닉 약화 0). 골든 불변(calc/input 무변경).

### ③ 상태
- 후속·재방문 라인 **코드 완결**. REVIEW-FEEDBACK 미해결 코드/문서 항목 0.
- 미커밋: cli.py·test_customer_purge.py(이번 구현) + HANDOFF.md·REVIEW-FEEDBACK.md·handoff/*.md(제외분). 커밋=운영자.

### 실행한 검증 명령
```
pytest tests/ -q   → 695 passed / 4 skipped / exit 0
git diff cli.py / read test_customer_purge.py   → 래퍼만·양방 정합, 가드 약화 0
```

---
---

# 교차 리뷰 — 2026-07-08 (라운드 4, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `f38d1e3` 위) · 구현자: Codex · 지시문: `handoff/codex-followup-fixups.md` (수정 라운드 항목 A·B·C)

## 최종 판정: **승인(PASS)** — 세 항목 정합, 회귀 0, 금지파일 침범 0.

Codex 완료보고를 믿지 않고 **기준 환경 직접 재실행** + 항목별 실측.

### ① 항목별 검증 (A·B·C)
| 항목 | 실측 | 판정 |
|---|---|---|
| **A** T0-④ 메타발화 | 제거 확정분(1240 합격/취업·1257 수익/손실 면책·1266·1285 병원 보일러·1375 "결과지에서는…단정하지 않습니다") **grep 0** / 유지 확정분(`775` 지역·`1263` "병을 진단하는 자리가 아니라" 프레이밍·`1659`·`1668` 완화형) **생존** — 회귀·과삭제 0 | ✓ |
| **B** content.md:12 두 층 분리 | "의료 단정 절대 금지, 투자·법률 단정 금지" **생존** + `"의료 전문가 상의" 문구 고정` **grep 0건** + vault 경로 포인터 포함. 코드/테스트 diff 0(문서 전용). frontmatter `paths: sajugen/content/**` 추가(스코프 지정, 무해) | ✓ |
| **C** compose.py 경계 명시 | `compose.py:120-123` 주석("allowed_years 빈 구저장본은 절대연도 사전판정 근거 없음 → factcheck 백스톱") + 회귀 2건: `test_empty_allowed_years_boundary_uses_factcheck_backstop`(빈→backend 호출됨·factcheck ganzhi 차단), `test_relative_next_year_question_is_backstopped_after_generation`(상대 "내년"→factcheck year 차단). `out_of_scope` 로직 불변(가드만 명문화) | ✓ |

- **금지파일 침범 0**(.env·harness/profiles/local·secret 무변경). `calc/`·`input/` 무변경(문안·문서·테스트만).
- 라운드3 관찰 2건(compose 경계) = **항목 C로 종결**. 라운드2 ④·라운드3 관찰(content.md) = A·B로 종결. **REVIEW-FEEDBACK 미해결 코드/문서 항목 0.**

### ② 기준 환경 pytest (직접 재실행)
- `pytest tests/ -q` → **692 passed / 4 skipped / exit 0**. 라운드3 690/4 → **+2 = 항목 C 신규 백스톱 테스트 2개 완전 일치**(은닉 약화 0). skip 4 불변.
- **골든 28 passed** 불변(계산 결정론 유지).

### ③ 남은 것 (비블로커 — 운영자)
- 미커밋 워킹트리 유지. 커밋 분리안(라운드2 ③): 무관 선행분(`handoff/codex-ilji-tension-followup.md`·`REVIEW-FEEDBACK.md`·`HANDOFF.md` 세션시작분) `git add -p`로 제외, T0/T0-④/T1~T4 태스크 경계 커밋. `handoff/codex-*.md` 지시문 3종은 문서라 별도/제외 판단.
- 연애 완화형 1659·1668 = 유지 비준 완료(라운드3 ③).

### 실행한 검증 명령
```
pytest tests/ -q                        → 692 passed / 4 skipped / exit 0
pytest tests/ -q -k golden              → 28 passed
grep 면책/의료 보일러(rules.py)          → 제거확정 0건 / 유지확정(775·1263·1659·1668) 생존
grep "문구 고정"(content.md)             → 0건 ("의료 단정" 규칙 생존)
git status(.env/harness local/secret)   → 침범 0
```

---
---

# 교차 리뷰 — 2026-07-07 (라운드 3, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋) · 구현자: Codex · 지시문: `handoff/codex-metadiscourse-t0-4.md` (T0-④ 메타발화 면책·의료 회피 제거)

## 최종 판정: **승인(PASS)** — 패킷 범위 정합, 경계 처분 정확, 회귀 0.

Codex 완료보고(샌드박스 663/31)를 믿지 않고 **기준 환경 직접 재실행** + diff 전수 + 경계 사례 처분 검증.

### ① diff 대조 (4파일 — 누락·이탈·금지파일·가드 약화)
| 파일 | 실측 | 판정 |
|---|---|---|
| `rules.py` | 면책 2건 제거(1240 "합격/취업 결과 단정 안함"→"찾는 관점입니다.", 1257 "수익/손실 단정·보장 안함" 삭제) + 의료 보일러(병원 진료/확인)→"몸 상태 변화는 그때그때 기록" 자연화 + **경계 1375(면책+문서메타 "결과지에서는…단정하지 않습니다") 제거** | ✓ |
| `llm_sections.py` | `_COMPOSE_SYSTEM`·`_COMPOSE_GUIDE[health]`에서 "병원에서 확인/전문가와 상의" 보일러 제거, **"질병 단정 절대 금지" 유지** | ✓ |
| `test_metadiscourse.py`(신규) | 3-way 양방: 제거 6문자열 부재 + 유지(프레이밍 "병을 진단하는 자리가 아니라"·지역 "병원과 장보기") 존재 + safe_lint·guarantee_lint clean, 하드게이트 미신설(B-8), 합성 PII 0 | ✓ |
| `test_p3.py`(수정) | **약화 아님** — 의료 단정어 가드(병에 걸린·불치·사망·단명) 불변, `assert "병원" in ht`(보일러 강제)→프레이밍·자연화 존재 assert 교체, 금지 hedge에 "병원에서 확인해 보세요" **추가(강화)** | ✓ |

- **유지 확정 present**: `rules.py:775`(지역 병원 문맥형)·`1263`(장 성격 프레이밍) 잔존 확인. **과삭제 0.**
- **경계 처분 정확**: 1375(문서메타 동반)=제거 / 775·1263=유지 — 판별 기준 부합.
- 금지파일 침범 0. `calc/`·`input/` 무변경(문안만) → 골든 불변.

### ② 기준 환경 pytest (직접 재실행)
- `pytest tests/ -q` → **690 passed / 4 skipped / exit 0**. 라운드2 기준선 687/4 → **+3 = 신규 test_metadiscourse 3개 완전 일치**(은닉 약화 0). skip 4 불변(샌드박스 31은 E3 리소스 부재).
- **골든 28 passed** 불변(계산 결정론 유지).

### ③ 경계 사례 — 운영자 비준 완료
- `rules.py:1659`·`1668` 연애 완화형("재회나 결혼을 단정하지는 않지만, "·"어떤 결론도 미리 단정하지는 않지만, ") = **운영자 비준: 유지 확정**(2026-07-07). 긍정 유도로 이어지는 문맥형 hedge라 면책 낭독(보일러플레이트)이 아님 — vault "완화형 검토" 항목 종결. 코드 변경 없음. (후속 수정 라운드 지시문: `handoff/codex-followup-fixups.md`.)
- `question_router.py`의 "병원" = 질문 분류 키워드(고객 대면 문안 아님) → 유지 정당.

### 관찰(비블로커)
- `.claude/rules/content.md`의 "health '의료 전문가 상의' 문구 고정"은 이번 제거와 표면 충돌하나, `rules.py:1263` 주석(2026-06-12 운영자 지시 "보일러플레이트 금지") + vault 스펙(2026-07-07)으로 **이미 대체됨** → 위반 아님. content.md 해당 줄은 차기 문서 정합 시 갱신 권장(이번 범위 밖).

### 실행한 검증 명령
```
pytest tests/ -q                         → 690 passed / 4 skipped / exit 0
pytest tests/ -q -k golden               → 28 passed
git diff (rules/llm_sections/test_p3/test_metadiscourse)  → 범위이탈 0, 가드 약화 0
grep 면책·의료 패턴(content)              → 제거확정 0건 / 유지확정(775·1263) 잔존
```

---
---

# 교차 리뷰 — 2026-07-07 (라운드 2, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `f38d1e3` 위) · 구현자: Codex · 지시문: `~/.claude/plans/ai-brain-50-decisions-2026-07-07-sajugen-shimmering-popcorn.md` (후속·재방문 상담 패킷 T0①②③ + T1~T4)

## 최종 판정: **승인(PASS)** — 승인된 패킷 범위 전부 구현·정합. 단 아래 ④ 1건 후속 등록.

Codex 완료보고(샌드박스 660/31)를 믿지 않고 **기준 환경(전 리소스)에서 직접 재실행**해 검증함.

---

## ① diff 전수 대조 (패킷 대비 — 누락·이탈·금지파일 침범)

수정 14파일 전부 패킷 태스크에 매핑, **범위 이탈 0 · 금지파일 침범 0 · 미커밋(요구대로)**.

| 태스크 | 구현 실측 | 판정 |
|---|---|---|
| T0-① 자기모순 문구 | `calc/advanced.py:109`(axis "단정 대신 참고로 제시") + `rules.py` 7앵커 교체 → **소스 "상담에서" grep 0건**(STATE.md 2건은 작업설명 문자열, render/out 산출물 제외) | ✓ |
| T0-② 월운 표기 규약 | `temporal_lint.py` 맨몸 n월(`_MONTH_TOKEN`+면제)·간지월 구간(`_GANJI_MONTH_*`) 린트 + `llm_sections.temporal_anchor_block` 프롬프트 규약 + `docs/03` SSOT 명문화 (3층 전부) | ✓ |
| T0-③ 상대시제×절기경계 | `_GANJI_MONTH_RANGE`+`_CURRENT/_NEXT_MONTH_WORD`+`_interval_contains/_starts_next_month`(3개년 경계 처리) — 김명기 병신월 실사례 로직 | ✓ |
| T1 스키마+마이그레이션 | `customers` 테이블 + orders additive(alias FK·parent_order_id·kind) + **멱등 마이그레이션**(`pragma table_info` 후 부재 시 ALTER, 2회차 무크래시) + `purge_identifier`(식별자만 파기·명식/alias 보존) + `issue_final_text`(APPROVED 게이트) | ✓ |
| T2 게이트 서브셋 | `followup/answer_gate.py` — KEEP 14종 개별 호출(safe_lint·`factcheck.check_with_allow`·trace·temporal·loanword·raw_calc·customer_meta·placeholder·style·quality·guarantee·`consult_direct_result`·markdown), 조건부 6종 **skipped 명시**(silent True 없음), DROP(PDF 레이아웃/기하/밀도) 미호출, `_norm`으로 실패보고 PII 제거 | ✓ |
| T3 슬림 컴포저 | `followup/compose.py` — 저장 사실만(신규계산 0), E7 이중기준(anchor=현재연도·사실지평=저장 allowed_years), **fail-closed 범위밖 연도/주제 거부**, 마스킹 인용격리(E6) | ✓ |
| T4 CLI+상태머신 | `cli.py` customer-find·gen-followup(PII 미출력) + `order_flow.run_followup`(**게이트 실패 시 주문 미생성**, RECEIVED→…→IN_REVIEW 정지, APPROVED는 수동, 원질문 미영속·마스킹본만 저장) | ✓ |

- 금지파일(.env·secret·harness/profiles/local·gitignore 데이터) 침범 0. `calc/` 수정은 `advanced.py` axis 라벨 1건뿐(계산값 불변) — 골든 28건 GREEN으로 무영향 실증(절대규칙 20 충족).
- 수정된 기존 테스트 4건(test_gunghap·test_p5·test_quality_lint·test_temporal_month) = **게이트 약화 아님, 신정책(맨몸 n월 금지) 적응·강화**. 특히 test_p5 `"gen"` 인자 = T4 멀티커맨드 반영, test_temporal_month `test_no_ref_date` `assert not`→`assert` = 강화.

## ② 기준 환경 pytest 전체 재실행 (증거)

- `./.venv/Scripts/python.exe -m pytest tests/ -q` → **687 passed / 4 skipped / exit 0** (203s).
- 이전 기준선(라운드1) **654/4** → **687/4 = +33 passed. 신규 테스트 = 정확히 33 passed**(5파일 별도 실행 33/0). **증가분 = 신규 테스트 수 완전 일치** → 은닉 약화 0.
- skip **4로 불변**. Codex 샌드박스 31 skip = E3 이원화(샌드박스 리소스 부재로 skip, 전 리소스 환경선 실행·통과). **은닉 비활성화 아님.**
- **골든 불변**: `pytest -k golden` → **28 passed** (test_golden_sweep 포함) — 계산 결정론 유지.

## ③ 커밋 분리안 (작업 전 존재 파일 ↔ 이번 구현 분리)

**이번 구현과 분리해 제외/별도 처리**:
- `handoff/codex-ilji-tension-followup.md` (?? — 라운드1 궁합 지시문, 본 패킷 무관 → 커밋 제외 또는 별도)
- `REVIEW-FEEDBACK.md` (?? — 리뷰 산출물, 코드 아님 → 커밋 제외)
- `HANDOFF.md` (세션시작 시 이미 M + Codex 추가분 혼재 → `git add -p`로 패킷분만 분리, 무관 선행분 제외)

**구현 커밋(각 pytest GREEN 후 논리 1커밋, 태스크 경계)**:
1. **T0**: `calc/advanced.py`·`content/rules.py`·`content/llm_sections.py`·`content/temporal_lint.py`·`docs/03-…md` + tests(`test_month_notation`·`test_temporal_month`·`test_quality_lint`·`test_gunghap`) — **골든 회귀 동반**
2. **T1**: `store/orders.py` + `tests/test_followup_schema.py`
3. **T2**: `followup/__init__.py`·`followup/answer_gate.py` + `tests/test_followup_gate.py`
4. **T3**: `followup/compose.py` + `tests/test_followup_compose.py`
5. **T4**: `cli.py`·`order_flow.py` + tests(`test_followup_flow`·`test_p5`)
6. **docs**: `sajugen/STATE.md` + `HANDOFF.md`(패킷분)

## ④ 후속 등록 (수정 필요 — 이번 패킷 밖, 다음 라운드 발주 대상)

- [ ] **T0-④ 상담가 페르소나 메타발화 3종 미구현** — 승인 패킷에 미반영 상태로 발주돼 잔존. 스펙 정본: `C:\Users\pc\AI-Brain\75_Content-Domain\상담가-페르소나-메타발화-금지.md`. 실측 잔존 앵커(현재 라인): `content/rules.py:1240`(면책 선언 "합격이나 취업의 결과를 단정하지는 않습니다")·`1257`(면책 "수익이나 손실을 단정하거나 보장하지는 않습니다")·`1265~1266`(병원 보일러플레이트 "병을 진단하는 자리가 아니라… 병원 진료로 먼저"). → 이번 구현의 결함 아님(범위 밖). 다음 TASK_PACKET으로 별도 발주 필요.

## 관찰(비블로커 — 참고)

- `compose.py` out-of-scope 가드는 저장 `allowed_years`가 비면 스킵(factcheck 백스톱). 질문에 명시연도 없는 "내년" 상대표현 + 리포트 연도지평 통째 stale일 때는 anchor=현재연도로 진행 → factcheck가 저장연도 밖 발화를 차단하나, E7 경계의 잔여 리스크로 기록. 다음 실파일럿에서 관찰 권장.
- `issue_final_text`가 `derived_interpretation["followup_answer"]` 우선·`customer_questions[].answer_text` 폴백 — 모델 필드 존재 확인됨(회귀 GREEN).

## 실행한 검증 명령 (직접 실행)
```
./.venv/Scripts/python.exe -m pytest tests/ -q                → 687 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest <followup 5파일> -q      → 33 passed / 0 skipped
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden      → 28 passed
git grep "상담에서" (render/out 제외)                          → 소스 0건(STATE.md 작업설명 2건뿐)
git diff --stat                                               → 14 files, +649/-50, 범위이탈 0
```

---
---

# REVIEW-FEEDBACK — 궁합 일지 형·해·파·원진 확장 (검증자 판정)

작성: 2026-07-07 · 검증자(Claude, 신선 컨텍스트) · 구현자(Codex)
대상 브랜치: `codex/gunghap-relationship-quality`
관련 지시문: `handoff/codex-ilji-tension-followup.md` (TASK 1·2 + §5 FIX)

## 최종 판정: **PASS** (정확성·회귀·render-gate 실측 통과)

기능 = 궁합 일지 상호작용 판정을 형(자형·子卯상형)·해·파·원진으로 확장 + 개인 consult 경로(partner_block) 대칭 배선 + 가드/스윕 하드닝. 삼형 완전판은 defer.

---

## 검증 항목과 실측 증거

### ① 렌더 하드 게이트 실측 (블로커 해소 확인)
합성 3인 business 룰전용 렌더(子 1990-01-11 · 未 1990-01-06 · 酉 1990-01-08, PII 0):
- **`gate_pass = True`**, `loanword_clean = True`, **false GATE_KEYS = []** (20/20).
- 신규 흉의 어휘(해/파/원진/자형/상형)가 실제 렌더 파이프라인의 verify 게이트를 통과함을 실측.

### ② diff 대조 (FIX 6파일, 커밋 `75c65f1` 이후 워킹트리)
`git diff --stat` = 6 files / 35+ / 9- — 범위 이탈 0. 5개 수정 항목 전부 반영:
- `sajugen/gunghap.py:336` _pair_slot 해: 리듬→흐름
- `sajugen/content/rules.py:1743` partner_block 해: 리듬→흐름
- `docs/03-engine-validation-plan.md:32` §1-1 육해 해석 범위: 리듬→흐름 (문서-코드 정합)
- `tests/test_partner.py:294` 정확문구 sync + `loanword_lint(blk)==[]` 하드닝
- `tests/test_gunghap.py` 가드 테스트: normalize 사전적용 제거 → raw _pair_slot 직접 검사
- `tests/test_raw_term_sweep.py` 스윕에 _pair_slot·partner_block **실제 출력** 추가(소스 아닌 출력 문자열 — 오탐 회피) + `loanword_lint(joined)==[]`

### ③ 테스트 집계 규명 (기준 환경 확정)
| 환경 | passed | skipped | 합계 |
|---|---|---|---|
| 검증자(전 리소스) | **654** | 4 | 658 |
| Codex 샌드박스 | 627 | 31 | 658 |

- 합계 658 동일 → skip↔pass 환경 차이(코드 아님). 검증자 4 skip = 전부 E2E opt-in(operator 승인/`SAJUGEN_RUN_E2E`). Codex 31 = 4(동일) + 27(샌드박스 리소스 부재: chromium/veraPDF/API키/KASI).
- **GREEN 착시 아님 실증**: 변경 관련 테스트(test_partner·test_gunghap·test_raw_term_sweep·test_couple_language) = **74 passed / 0 skipped**(검증자 환경 실제 실행). 27 skip 집합에 이번 변경 검증 테스트 없음. → **기준 = 검증자 654/4**.

### 계산·설계 정합 (초기 리뷰에서 확정, 유지)
- docs/03 §1-1 채택표 ↔ `calc/partner.py` 표 1:1 + 표준 명리 정설 부합.
- 독립 판정(elif 아님): 巳申=육합+파, 子未=해+원진, 寅巳=해만(삼형 defer) — 양방/충돌/경계 테스트로 고정.
- 소비처 배선 대칭(_pair_slot·partner_block) — 팬텀 파라미터 0.

---

## 검증 여정 (정직한 기록 — 초기 판정의 정정)
1. 초기 코드-레벨 리뷰: "no blocker" 판정(pytest GREEN·정적 분석). **불완전했음.**
2. Codex가 TASK 2 전제 오류(폴백은 가드 스택 미경유, gunghap.py:1016)를 1차자료로 지적 → 테스트 메커니즘 정정.
3. **합성 실렌더(운영자 지시)가 실경로 결함 포착**: 신규 해 문안 "생활 리듬"의 외래어 → `loanword_clean=False` → 육해 쌍 business 궁합 빌드 실패. business 폴백이 `normalize_loanwords` 미경유라 정적/유닛 GREEN이 가렸음.
4. 근본원인 2층: (a) 가드 유닛 테스트가 normalize 사전적용으로 raw 외래어 은폐, (b) "리듬 스윕" 앵커가 두 소비처 소스를 미스캔. 둘 다 FIX에서 닫음.
5. FIX 재검증 → 본 문서 ①②③ 전부 통과.

교훈: **정적 분석·유닛 GREEN ≠ 실경로 안전.** 고객 대면 신규 어휘는 실렌더 게이트까지 실측해야 한다(실측 우선, docs/16 QI 계열).

---

## 남은 것 (블로커 아님)
- **FIX 커밋 미완**: 현재 워킹트리(6파일)는 미커밋. HEAD=`75c65f1`(기능 1차). FIX는 fix-forward 후속 커밋 필요(운영자 지시 시).
- **main 전진/발송 게이트**: feat는 베이스라인 아님. main ff·실발송 전 운영자 최종 검수.
- **참고(비블로커)**: 합성 렌더에서 `domain_term_repetition` **경고**(결·구조·자리) — delivery_quality_clean=True(게이트 아님), 룰전용 미니 리포트라 과장. `_ILJI_TENSION_KO`의 "결/구조" 의존 문안 다양화는 선택 개선.

## 실행한 검증 명령
```
# ① 렌더 gate_pass (build_gunghap render=True, 합성 3인 business)  → gate_pass=True / loanword_clean=True / false keys=[]
# ② git diff --stat (vs 75c65f1)  → 6 files, 35+/9-
# ③ pytest tests/ -q -rs  → 654 passed / 4 skipped / exit 0 (skip=E2E opt-in만)
#    pytest tests/test_partner.py tests/test_gunghap.py tests/test_raw_term_sweep.py tests/test_couple_language.py -q  → 74 passed / 0 skipped
```
