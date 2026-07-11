# 교차 리뷰 — 2026-07-11 (라운드 13, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `d71fb35` 위) · 구현자: Codex · 지시문: `handoff/tasks/q7-stage4-partner-20260711.md` (Q7 4단계 2인 접수·gunghap 주문화)

## 최종 판정: **승인(PASS)** — 4단계 수용기준 전 항목 GREEN, 절차 이탈 0. 발견 R13-1(비블로커 — 4단계 diff 밖 기존 경로, 실렌더가 첫 노출).

파일 상태 기준 인계 — diff 전량 실측 + 기준환경 직접 재실행 + 실경로 프로브 + 합성 실렌더 N=5(2인).

### ⓪ 범위 무결성
- HEAD `d71fb35` 불변. 수정 = 제품 5파일(app/order_flow/admin/템플릿/modules) + 테스트 5파일(+692/-57). integrated.py·cli.py·store·게이트·gunghap.py·calc/input diff 0(패킷 §0 정합).

### ① 기준환경 pytest (직접 재실행)
- `pytest tests/ -q` → **820 passed / 4 skipped / exit 0** (191.6s). 기준선 801/4 → **+19 = 신규 테스트 완전 일치**(감소 0). golden 28. Ruff 수정 9파일 GREEN.

### ② 항목별 실측 (패킷 §2·§3)
| 항목 | 실측 | 판정 |
|---|---|---|
| 접수 additive | partner 미입력 = 키 부재(1인 형상 보존 회귀). 정상 입력 = KASI 정규화 재사용+경고 병합+양력 저장. fail-closed 2건(상대 시진 불명·비대상 상품) 주문 미생성 — **프로브 실측** | ✓ |
| PII 방어 | KASI 예외·파싱 실패를 원문 비전재 메시지로 래핑(`from None` 체이닝 차단), generation_error audit에 **상대 생년월일 마스킹 추가**(E-2 이웃 자발 처리), admin 상세 = 상대 이름·성별만 | ✓ |
| 추천 분기 | RELATION × partner 2분기 + 비대인 6종 불변 + 기본값 False 하위호환(3-B 테스트 GREEN 유지) | ✓ |
| admin·confirm 조건화 | partner 주문 = 5모듈 옵션·gunghap 확정 허용(**프로브: `[gunghap,love]` → `(love,gunghap)` 정규 순서 저장**), 1인 주문 = 4모듈·gunghap 거부 유지(프로브 재확인) | ✓ |
| 생성 분기 | 2인 people+receiver 명시 도달(캡처 테스트). `partner_present`를 주문 진실원으로 덮어씀 — **Report23 변환 전 순서 정확**, 팬텀 아닌 실소비 단언(1인 False 대조 포함). partner 있음+개인만 확정 → 관계 compose 미호출 | ✓ |
| 합성 실렌더 N=5(2인, 무LLM) | **35쪽 실물**(하한 30 통과 — 관계 조립이 실렌더에서 실작동, 분량 GREEN). 커버리지·조판 clean. 단 role/honorific 게이트 차단 → R13-1 | ✓* |

### ③ 발견 R13-1 (비블로커 — 4단계 diff 밖, 기존 경로): 무LLM 2인 관계 문안의 수신자 '씨' 호칭
합성 실렌더 N=5에서 `receiver_third_person_honorific` 위반 13회+(관계 챕터 29~33쪽) — 룰 폴백 관계 문안이 수신자를 "님" 대신 "씨"로 3인칭 호명. `build_integrated_full` 직접 경로는 이번 diff가 비변경이므로 **기존 상태의 첫 노출**(무LLM 2인 integrated_full 실렌더가 최초). 게이트는 fail-closed로 정확히 차단(발급 불가 = 안전). 실운영 영향 제한적: N=5는 분량 정책상 LLM-on 전제 구간. **LLM-on에서 해소되는지 미검증** — 처리안: (a) LLM-on N=5 합성 1건 실측(과금 승인) 후 결정(N=4 선례 패턴), 또는 (b) 관계 룰 문안 호칭 수정 별도 발주. 운영자 결정 대기.

### ④ 미검증 (정직 승계)
- LLM-on 2인 문안(R13-1 해소 여부 포함)·실브라우저 수동 검수: 미실행.
- 사람별 시진 불명 배선·상대 PII purge 확장: 범위 밖 유지(승인 항목 ③ 잔여 수용).

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 820 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed
./.venv/Scripts/python.exe -m ruff check (수정 9파일)      → All checks passed
실경로 프로브(2인 접수·gunghap 확정·1인 거부·비대상 차단)   → 전부 정상
합성 실렌더 N=5 2인 무LLM + verify 상세 재추출             → 35p·R13-1 원인 확정
```

---
---

# 교차 리뷰 — 2026-07-11 (라운드 12, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `3b2aa7b` 위) · 구현자: Codex · 지시문: `handoff/tasks/q7-stage3b-admin-20260711.md` (Q7 3-B admin 모듈 추천·확정 UI)

## 최종 판정: **승인(PASS)** — 3-B 수용기준 전 항목 GREEN, 미해결 0, 절차 이탈 0(글롭 `!**/` 형식 첫 적용 라운드). Q7 3단계 완결.

Codex 완료보고 없이 파일 상태 기준 인계("이어받아 교차리뷰") — diff 전량 실측 + 기준환경 직접 재실행 + 실경로 프로브.

### ⓪ 범위 무결성
- HEAD `3b2aa7b` 불변. 수정 = 제품 4파일(admin.py +31 / modules.py +23 / order_flow.py +55 / admin_detail.html.j2 +37) + 테스트 3파일(신규 test_module_selection_admin.py). app.py·integrated.py·cli.py·게이트·calc/input diff 0(패킷 §0 정합). STATE·manifest 변경은 발주 세션 선행분.

### ① 기준환경 pytest (직접 재실행)
- `pytest tests/ -q` → **801 passed / 4 skipped / exit 0** (208.5s). 기준선 778/4 → **+23 = 신규 테스트 완전 일치**(감소 0, 은닉 약화 0).
- `pytest -q -k golden` → **28 passed**. 3-B 대상 3파일 단독 62 passed.

### ② 항목별 실측 (패킷 §2·§3)
| 항목 | 실측 | 판정 |
|---|---|---|
| 추천 매핑 | `modules.py.recommended_modules_for_category` — 순수 표시 함수(주문 메타 읽기/쓰기 0), 7종 전수 표 테스트(RELATION→love·TIMING/GENERAL→빈 튜플) + 미지정/미등록 빈 튜플. **R9-1 커버리지 로직 비변경**(추가만) | ✓ |
| admin 패널 | integrated_full 주문만 표시(기존 상품 상세 무변경 회귀), 미확정 red 강조, 추천 배지 + "자동 선택되지 않습니다" 명시, NORMALIZED에서만 확정 폼, 확정 후 기존 `/retry` 재사용(새 생성 버튼 0) | ✓ |
| 확정 함수 | `confirm_module_selection` — NORMALIZED 한정(`EditNotAllowed`→409, 기존 예외 재사용), integrated_full 한정(422), `normalize_modules` 위임 + gunghap 이중 거부, `gen_params.modules`+`report_plan.sections` 동기 저장, audit note = 모듈 ID만, 상태 전이 0 | ✓ |
| 실경로 프로브(리뷰어 독립) | P1 gunghap 확정 → ValueError 거부 / P2 역순 입력 `[job,love]` → **정규 순서 `(love,job)` 저장**·confirmed True·plan.sections 동기·audit `"love,job"` / P3 상태 전이 후 확정 → EditNotAllowed 거부 | ✓ |
| 3-A 테스트 변경 | 수동 gen_params 주입 → `confirm_module_selection` 실호출로 교체 = **약화 아닌 실경로 강화**(+plan.sections 단언 추가) | ✓ |
| 신규 테스트 23건 | 추천 표시/자동 선택 없음 증명/기존 상품 패널 부재/확정 저장(생성 미발동)/차단 parametrize(잘못된 값·**비NORMALIZED 전수**·검증 순서·기존 상품)/매핑 전수 표 | ✓ |
| Ruff | 수정 6파일 `All checks passed!` / exit 0 | ✓ |

### ③ 미검증 (정직 승계)
- 실브라우저 수동 UI 검수(TestClient 회귀만)·실렌더·LLM-on 문안: 미실행(별도 승인 영역).
- 이로써 Q7 3단계(3-A+3-B) 완결 — "접수 → 모듈 확정 → native 생성 → 검수 → 발급" 전 구간 배선. 남은 검증 관문 = 합성 실렌더(N=1·N=4, 설계 프리모템 항목).

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 801 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed
./.venv/Scripts/python.exe -m pytest (3-B 대상 3파일)      → 62 passed
./.venv/Scripts/python.exe -m ruff check (수정 6파일)      → All checks passed / exit 0
실경로 프로브 P1~P3(확정 함수 직접 호출)                    → gunghap/비NORMALIZED 거부·정규 순서 저장 실측
git diff --name-only (금지 경계)                          → app/integrated/cli/게이트/calc/input 0
```

---
---

# 교차 리뷰 — 2026-07-11 (라운드 11, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `1401dbf` 위) · 구현자: Codex · 지시문: `handoff/tasks/q7-stage3a-order-20260711.md` (Q7 3-A 주문 플로우 integrated_full 편입)

## 최종 판정: **승인(PASS)** — 3-A 수용기준 전 항목 GREEN, 코드 미해결 0. 단 ③ 절차 이탈 2회차(비블로커) — 패킷 글롭 예시 결함이 원인, 정정 조치 포함.

Codex 완료보고를 믿지 않고 기준환경 직접 재실행 + diff 전량 실측 + 임시 DB 실경로 프로브.

### ⓪ 범위 무결성
- HEAD `1401dbf` 불변. 수정 = 제품 3파일(integrated.py +44 / app.py +43 / order_flow.py +368) + 테스트 5파일(신규 test_integrated_order_flow.py 포함). admin·템플릿·modules.py·게이트·cli.py·calc/input diff 0(패킷 §0 정합). STATE·manifest 변경은 발주 세션 선행분(Codex 비접촉 — 보고 일치).

### ① 기준환경 pytest (직접 재실행)
- `pytest tests/ -q` → **778 passed / 4 skipped / exit 0** (205.0s). 기준선 758/4 → **+20 = 신규 테스트 완전 일치**(감소 0, 은닉 약화 0). Codex "환산 예상" 확정.
- `pytest -q -k golden` → **28 passed**(calc/input diff 0). 상태머신 회귀(test_orders·test_final_render_gate) 전체 실행에 포함 GREEN.

### ② 항목별 실측 (패킷 §2·§3)
| 항목 | 실측 | 판정 |
|---|---|---|
| 계산 입력 배선 | `build_integrated_full`에 longitude/latitude/policy/horoscope_date 신설 — **기본값 = 현행 동일**(SEOUL·JST_2300·6월1일, 바이트 회귀 테스트 동반). engine.build 도달 캡처 단언. crosscheck 4필드(`bazi_consistent` 등) **engine.py 실존 확인**(fail-open 아님) | ✓ |
| 접수 확장 | 웹폼 integrated_full 노출 + 즉시 PDF 강등 없이 주문 우회(422/redirect). **프로브 P1**: 시진 불명 → ValueError·주문 0 실측. modules 빈 목록은 integrated_full에만(기존 상품 gen_params 하위호환 — **프로브 P3** 키 부재 실측) | ✓ |
| 미확정 차단 | `module_selection_state` 결정론 판정, 생성·재시도 공유 차단점. **프로브 P2**: NORMALIZED 상태 불변 + audit_log에 `generation_blocked / modules unconfirmed`(PII 0) 실측 | ✓ |
| 생성·재시도 분기 | `_run_integrated_generation` — gen_params 전부 소비(모듈·좌표·yajasi→policy·horoscope·brand·concern→situation·ref_date=생성 당일). content.json 영속 fail-closed(부재 시 RuntimeError) + 게이트 메타 전수 검증(identity/singang/role/coverage `skipped is not False`) + CALC_MISMATCH 기존 차단 상태 재사용 | ✓ |
| 최종 발급 분기 | 저장 Report23을 동일 `_render_integrated`+동일 스펙으로 재검증, 메타 불완전/모듈 불일치/skipped → **RuntimeError(개인 경로 강등 금지, B-1 정합)** — 차단측 테스트 동반 | ✓ |
| 후속 차단 | run_followup 공용 지점에서 integrated_full 부모 텍스트·PDF 거부(compose 진입 전) + CLI 배선 테스트. 기존 부모 회귀 유지 | ✓ |
| 신규 테스트 20건 | 3지점 분기 양방·차단·하위호환·verify 관통 전부 동작 단언, PII 0 | ✓ |
| Ruff | 수정 8파일 `All checks passed!` / exit 0 | ✓ |

### ③ 절차 이탈 2회차 (비블로커 — 원인은 패킷 글롭 예시 결함, 정정 포함)
초기 검색에서 ignored 일부가 검색 결과에 재노출(내용 사용·전재·수정 없음, 자진 보고). **근본원인 2층**: (표면) 패킷 0절이 제시한 예시 `--glob '!render/out/**'`가 저장소 루트 기준이라 하위 경로 검색에서 미적용 — Codex가 `!**/render/out/**`로 자가 강화. (시스템) **발주 패킷 예시 자체가 불충분했음 = 리뷰어(패킷 작성자) 몫**. 조치: 이후 모든 패킷 0절 예시를 `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'` 형식으로 고정. 2회 반복이므로 docs/16 기록을 권고(운영자 결정).

### ④ 미검증 (정직 승계)
- 실제 PDF 조판·페이지 하한 실달성·브라우저 수동 검수·LLM-on 문안·표준 hrun: 미실행(별도 승인 영역).
- 3-B admin 추천·확정 UI: 다음 패킷. 그 전까지 integrated_full 주문은 의도대로 NORMALIZED에서 대기(프로브 P2로 안전 실측).

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 778 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed
./.venv/Scripts/python.exe -m ruff check (수정 8파일)      → All checks passed / exit 0
임시 DB 실경로 프로브 P1~P3                                → 시진불명 차단·미확정 차단·하위호환 실측
git status / git diff                                     → 승인 범위 한정, calc/input/admin/cli 0
```

---
---

# 교차 리뷰 — 2026-07-11 (라운드 10, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `6c0d673` 위) · 구현자: Codex · 지시문: `handoff/tasks/q7-stage2-cli-20260710.md` (Q7 2단계 CLI `--module`)

## 최종 판정: **승인(PASS)** — 2단계 수용기준 전 항목 GREEN, 코드 미해결 0. 단 ③ 절차 이탈 1건(비블로커, 데이터 경계) 기록 — 운영자 확인 필요.

Codex 완료보고를 믿지 않고 기준환경 직접 재실행 + diff 전량 실측 + 실 프로세스 차단 프로브.

### ⓪ 범위 무결성
- HEAD `6c0d673` 불변. 수정 = 승인 2파일(`sajugen/integrated.py` +28/-11 CLI gen 부분만, `tests/test_integrated_modules.py` +93/-1)뿐. STATE.md·manifest 변경은 발주 세션(Claude) 선행분 — Codex 비접촉(보고와 일치). 1단계 조립·게이트·레지스트리·render 커맨드 diff 0.

### ① 기준환경 pytest (직접 재실행)
- `pytest tests/ -q` → **758 passed / 4 skipped / exit 0** (203.2s). 기준선 753/4 → **+5 = 신규 CLI 테스트 완전 일치**(감소 0, 은닉 약화 0). Codex "환산 예상" 확정.
- `pytest -q -k golden` → **28 passed**. calc/input diff 0. 대상 파일 단독 30 passed 직접 재실행.

### ② 항목별 실측 (패킷 §2·§3)
| 항목 | 실측 | 판정 |
|---|---|---|
| `--module` 반복 옵션 | 기본 None → `build_integrated_full(modules=None)` = 5모듈 하위호환(kwargs 캡처 단언). 기존 gen 호출 형태 무변경 | ✓ |
| 검증 레지스트리 위임 | CLI 자체 정규화·보정 0 — 원값 그대로 전달, ValueError → stderr 원인 + `typer.Exit(1)`. 조용한 보정·부분 진행 없음 | ✓ |
| 관측 출력 | `modules: love,job (schema v1)` — `result["modules"]` SSOT만 사용, 자체 재계산 금지 준수. 메타 없는 구 테스트 더블 하위호환 가드 | ✓ |
| 실 프로세스 차단 프로브(리뷰어 독립) | `--module fake`/중복/`gunghap`+1인 실 CLI 실행 → **전부 exit 1 + 원인 메시지, PDF 미산출**(3종 모두 계산·렌더 진입 전 실패 — 안전 확인 후 실행) | ✓ |
| 신규 테스트 5건 | 하위호환(None 전달)/조합(원값 전달+정규화 출력)/차단 3종 parametrize — 렌더만 끄고 **실제 레지스트리 검증 경로** 사용(모의 아님), PII 0 | ✓ |
| Ruff | 수정 2파일 `All checks passed!` / exit 0 | ✓ |

### ③ 절차 이탈 1건 (비블로커 — Codex 자진 보고, 운영자 확인 필요)
Codex 초기 광역 rg 검색에서 제외 패턴 누락으로 **ignored `sajugen/render/out/**` 일부가 읽기 전용 검색 결과에 포함**됨(계약 4a 데이터 경계 — 해당 영역은 실고객 산출물 55파일이 있는 구역). 수정·재생성·추가 접근·내용 전재는 없었고 자진 보고됨. 코드 산출물과 무관(비블로커). **재발 방지 권고**: 이후 Codex 패킷 0절에 "검색 시 ignored 제외 글롭 필수(`--glob '!render/out/**'` 등)" 명시 + docs/16 기록 여부는 운영자 결정.

### ④ 미검증 (정직 승계)
- 성공 경로 실 CLI(실렌더 동반)·LLM-on 문안: 미실행(별도 승인 영역 — 성공 경로는 CliRunner+렌더 오프로만 검증).
- admin·주문 플로우: 3단계 이연(범위 밖).

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 758 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed
./.venv/Scripts/python.exe -m pytest (대상 파일 단독)      → 30 passed
./.venv/Scripts/python.exe -m ruff check (수정 2파일)      → All checks passed / exit 0
실 CLI 차단 3종 프로브                                     → 전부 exit 1·원인 메시지·PDF 미산출
git status / git diff                                     → 승인 2파일 한정, calc/input 0
```

---
---

# 교차 리뷰 — 2026-07-10 (라운드 9 재검, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `0b3134f` 위) · 구현자: Codex · 지시문: `handoff/codex-q7-r9-fixup.md` (R9-1 수정 라운드)

## 최종 판정: **승인(PASS)** — R9-1 종결. Q7 1단계 전 항목 GREEN, 미해결 0. 다음 = 운영자 checkpoint commit 결정.

Codex 완료보고를 믿지 않고 기준환경 직접 재실행 + diff 실측 + 라운드9 동일 프로브 재실행.

### ⓪ 범위 무결성
- HEAD `0b3134f` 불변. **허용 밖 동결 7파일 SHA-256 전부 라운드9 동결값과 일치**(Get-FileHash 재계산) — 수정은 승인된 2파일(`sajugen/modules.py`·`tests/test_integrated_modules.py`)뿐. 예상 밖 변경 파일 0.

### ① 기준환경 pytest (직접 재실행)
- `pytest tests/ -q` → **753 passed / 4 skipped / exit 0** (240.9s). 라운드9 기준선 745/4 → **+8 = 신규 R9-1 테스트 완전 일치**(감소 0, 은닉 약화 0). Codex의 "확정 불가" 예상값 확정.
- `pytest -q -k golden` → **28 passed** (calc/input diff 0 유지).

### ② R9-1 구현 실측 (수정 패킷 §3·§4 대조)
| 항목 | 실측 | 판정 |
|---|---|---|
| 불변식 구현 | `module_coverage`가 맵의 (주장 모듈, 섹션ID) 쌍마다 `_modules_for_unmapped_section` 소유자 대조 — **기존 복원 경로 재사용, 로직 복제 0**. 거부 쌍은 effective에서 제외 후 기존 미배정 단일 경로로 재귀속(mapped_ids 미포함 → 이중 계상 구조적 불가) | ✓ |
| 게이트 형상 | 새 failure 룰·GATE 키 0. `misattributed_section_ids`는 coverage dict 관측 필드만(원인 분리 — claimed/section/owners 구조) | ✓ |
| 프로브 재실행(라운드9 동일 스크립트) | P1 위조 맵 → **unexpected=['health']**(구: []), P3 fake ID → **unknown=['fake_zone']**, P4 관계 세탁 → **unexpected=['gunghap']**, P5 analyze 경유 → **unexpected_module_sections failure 발생**. P2 대조군 동작 불변 | ✓ |
| 통과측 무오탐(신규 프로브 G1~G4) | legacy 대표맵·work 이중 소유·core/tail 등록 ID 전수 자기 소유·5모듈 조립기 형태 맵 → **전부 CLEAN**(misattributed 포함 0) | ✓ |
| 신규 테스트 8건 | 차단측 P1(+P2 대조)·P3/P4 parametrize·missing 우회(missing+unexpected 동시 실패)·analyze 경유 + 통과측 legacy/work 이중/raw·personal_ prefix 이웃(A-4) — 동작 단언(change-detector 아님) | ✓ |
| 리뷰어 독립 이웃 검사 | core/tail의 부당 주장(core가 personal_love 주장)·미지원 모듈 키의 유효 ID 주장·중복 주장 — 코드 경로상 전부 거부→재귀속으로 수렴(claimed_module 무관 동일 로직이라 P1 케이스가 대변) | ✓ |
| Ruff | 수정 2파일 `All checks passed!` / exit 0 | ✓ |
| PII·금지경계 | 합성 ID만, 금지파일 침범 0, ignored 비접촉, commit/push/PDF/sajugen LLM 호출 없음 | ✓ |

### ③ 미검증 (정직 승계 — 변동 없음)
- 실렌더·부분 조합 실제 조판·LLM-on 문안: 미실행(별도 승인 영역).
- 메타 없던 손상 레거시 번들의 실누락 증명: 대표맵 복원의 구조적 한계 유지(R9-1은 위조 주장 차단으로 부분 축소).

### 실행한 검증 명령
```
Get-FileHash SHA256 (동결 7 + 수정 2)                     → 동결 7 전부 MATCH, 수정 2만 변경
./.venv/Scripts/python.exe -m pytest tests/ -q           → 753 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed
./.venv/Scripts/python.exe -m ruff check (수정 2파일)      → All checks passed / exit 0
./.venv/Scripts/python.exe ownership_probe.py (P1~P5 재실행) → 전부 차단 전환 확인
./.venv/Scripts/python.exe ownership_probe_pass_side.py (G1~G4) → 전부 CLEAN
```

---
---

# 교차 리뷰 — 2026-07-10 (라운드 9, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `0b3134f` 위) · 구현자: Codex · 지시문: `handoff/codex-q7-stage1.md` v3 (Q7 1단계 모듈 레지스트리·조립·게이트) · 패킷: `handoff/tasks/q7-stage1-modules-20260710.md`

## 최종 판정: **수정 요청(changes_requested)** — v3 수용기준·회귀·범위·게이트 비악화 전 항목 GREEN. 단 패킷이 라운드9에 위임한 module_sections 소유권 사각 판정 = **보완 필요(R9-1, 유일 미해결)**. R9-1 수정 + 양방 회귀 후 재검이 PASS 조건.

Codex 완료보고를 믿지 않고 기준환경 직접 재실행 + diff 전량 실측 + 합성 프로브.

### ⓪ 전제 무결성
- HEAD `0b3134f` 일치. 패킷 동결 SHA-256 10건(제품 9파일 + 지시문 v3) 전부 MATCH — PowerShell `Get-FileHash -Algorithm SHA256` 재계산 대조. 리뷰 대상 = 패킷이 동결한 그 물건.

### ① 기준환경 pytest (직접 재실행)
- `pytest tests/ -q` → **745 passed / 4 skipped / exit 0** (195.59s). 기준선 728/4 → **+17 = 신규 test_integrated_modules 수집분 완전 일치**(감소 0, 은닉 약화 0). 패킷의 "확정 불가" 예상값을 확정.
- `pytest -q -k golden` → **28 passed**. `git diff --name-only calc·input·cli·admin·order_flow·store·app` → 출력 없음(계산·주문 경로 불변).

### ② 항목별 실측 (v3 §2 구현항목·§3 수용기준)
| 항목 | 실측 | 판정 |
|---|---|---|
| 레지스트리 | `sajugen/modules.py` 신규 — schema v1, 5모듈 정규 순서 고정(입력 순서 무관), 빈/중복/미등록 fail-closed(ValueError). calc/input 미참조 | ✓ |
| work 제공자 분리 | `rules.py` `work_job`/`work_wealth` 독립 노출 + `work=_join(*selected_work)` 기본값 `("job","wealth")` = 옛 바이트 동일. **실룰 회귀**(test 2번)가 base==explicit·job≠wealth·결합=단독+단독 바이트 고정 | ✓ |
| 조립 일반화 | `_assemble_sections`: 현행 순서 필터링(재배열 없음)→병합 전 module_sections/premerge_ids 캡처→현행 sparse 병합 그대로. 미등록 유입·중복 ID·unexpected 모듈 = 조립 ValueError. **closing/appendix/colophon 순서 이웃**: 기존 `insert(0)` → 자연 순회로 바뀌었으나 SECTION_SPECS 실순서(closing<appendix_terms<colophon)에서 동작 동일 + **Q7 이전 알고리즘 인라인 독립 오라클 테스트**(test 4번)가 바이트 고정 | ✓ |
| 병합 전 판정 | 커버리지 판정 입력 = 조립기의 병합 전 목록(PDF 역추정 아님). sparse 병합으로 최종 ID에서 love/work/health가 사라져도 오탐 0 회귀(test 9번) | ✓ |
| 게이트 연동 | `_min_pages/_min_text_chars`에 `module_minimums` 편입(5모듈=30p/10000자 유지). missing/unexpected가 `delivery_quality_clean` failures로 편입 — **GATE_KEYS 20키 무변경**(우회 경로·완화·기준 하향 0). 비integrated 상품은 `skipped=True` 관측 명시, integrated 레거시 미전달=5모듈 복원(skipped 아님 — test_integrated_product 단언) | ✓ |
| 파라미터 관통 | build→_render_integrated→verify→content.json 저장→재렌더 복원까지 배선(test 12·13번 kwargs 캡처로 증명). schema version 불일치 재렌더 = ValueError(fail-closed). 팬텀 파라미터 0 | ✓ |
| builder LLM 제외 | `include_section_ids`로 선택 밖 챕터를 LLM 작성 후보에서 제외, 미등록 include는 ValueError. None=옛 호출 그대로 | ✓ |
| gunghap 경계 | 1인+gunghap 선택 → ValueError(조립 전 차단), 2인 통과, 미선택 시 관계 compose 미호출(test 5·7번) | ✓ |
| N 경계표 | N=1..5 × (하한-1 차단 / 하한 통과) 파라미터라이즈(test 11번) — 승인 공식 min(30,12+4N)/min(10000,1000+2000N) | ✓ |
| Ruff | 신규 2파일 GREEN(exit 0). 전체 29건 = 전부 기존 부채. 수정 7파일 HEAD 대비 21→18로 **신규 위반 0 + 기존 3건 해소**(미사용 `re` import, F821 pytest×2) | ✓ |
| PII·금지경계 | 테스트 = 익명 ID(DOC_A/B)·합성 생일만. 금지파일 침범 0, ignored 비접촉 | ✓ |

### ③ R9-1 (수정 요구 — 유일 미해결): module_coverage가 구조화 맵의 소유권 주장을 교차검증하지 않음
패킷 §판정4가 라운드9에 위임한 사각. **합성 프로브로 실존 확정**(modules.py 로직 직접 호출 + analyze 경유, PII 0):
- P1 위조 맵: `["love"]` 선택 + 맵이 `personal_health`를 love 소유로 주장(평면 목록에도 실존) → missing/unexpected/unknown **전부 [] = 세탁 통과**.
- P2 대조군(정직 맵, 같은 평면 목록): unexpected=`['health']` 정상 차단 — 즉 레지스트리 복원 경로(`_modules_for_unmapped_section`)는 작동하지만 **맵이 선점 주장한 ID는 검증 없이 신뢰**됨.
- P3 미등록 `fake_zone`을 맵이 주장 → unknown 미탐. P4 관계 섹션(`relationship_overview`)을 love가 주장 → unexpected 미탐. **missing도 가짜 ID 주장으로 우회 가능 = 커버리지 게이트 양쪽 룰 전체가 위조 맵에 무력화**.
- P5 `delivery_quality.analyze` 경유 최종 확인: P1 시나리오에서 module 계열 failure 0.

**판정 근거(보완 필요)**: (a) 이 게이트의 존재 이유가 비선택 콘텐츠 유입 차단인데 유일한 독립 기준(레지스트리)을 복원 경로에만 반쪽 사용 — 게이트 주석의 "조용한 통과 금지"(fail-closed, 방법론 B-2)와 코드 실태 불일치. (b) 실경로: 정상 빌드는 조립기 예외가 선차단하므로 발현 경로는 content.json 손상/변조/미래 구현 버그의 재렌더뿐 — 그러나 verify 게이트는 바로 그 "자기 생성 메타의 버그"를 잡으라고 있는 방어선(팬텀 파트너 QI-2026-07-04-01 계열). (c) 보완 = 레지스트리 dict 조회 몇 줄, 오탐 없음 → B-8(어설픈 게이트 회피) 비저촉. (d) 커밋 전 = 가장 싼 수정 시점, 2단계(CLI/admin)가 이 메타를 더 만지기 전에 닫아야 함.

**수정 방향(Codex, `sajugen/modules.py` + `tests/test_integrated_modules.py` 한정 예상)**: `module_coverage`에서 맵이 주장한 각 섹션 ID의 레지스트리 소유자(`_modules_for_unmapped_section` 상당)를 주장 모듈과 대조 — 불일치는 unexpected/unknown으로 격상. work는 job/wealth 이중 소유 허용, core/tail 주장은 항상 허용. 양방 회귀 동반: (차단) P1·P3·P4 시나리오, (통과) 조립기 산출 맵·legacy 대표맵·work 이중 소유·기존 17건 GREEN 유지.

### ④ 미검증 (Codex 보고와 동일 — 정직 승계)
- 실렌더(실제 부분 조합 PDF 조판·페이지 수)·LLM-on 문안: 미실행(승인 필요 — 렌더 브리지·게이트는 합성/모의로 검증됨).
- 메타 없던 레거시 손상 번들의 실누락 증명: 대표 커버리지 맵 복원의 구조적 한계(패킷 명시 승계). R9-1 보완이 이 한계도 부분 축소.
- 실제 새 codex exec 프로세스의 hook 주입: 외부 전송 보안 검토 차단으로 확정 불가(패킷 승계).

### 실행한 검증 명령
```
Get-FileHash SHA256 (동결 10파일)                        → 전부 MATCH, HEAD 0b3134f
./.venv/Scripts/python.exe -m pytest tests/ -q          → 745 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden → 28 passed
./.venv/Scripts/python.exe -m ruff check (신규 2파일)     → All checks passed / exit 0
./.venv/Scripts/python.exe -m ruff check (수정 7파일)     → 18건 = HEAD 21건의 부분집합(신규 0)
./.venv/Scripts/python.exe ownership_probe.py (합성 P1~P5) → R9-1 사각 실존 확정
git diff --name-only calc·input·cli·admin·order·store    → 출력 없음
```

---
---

# 교차 리뷰 — 2026-07-10 (라운드 8, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `5bd8cb1` 위) · 구현자: Codex · 지시문: `handoff/codex-pii-anonymize-e10.md` v2 (E10 실명 익명화 전수)

## 최종 판정: **승인(PASS)** — 순수 문자열 치환 증명, 회귀 0. 리뷰어 보정 2건(문서) 적용 후 커밋.

Codex 완료보고를 믿지 않고 기준 환경 직접 재실행 + diff 실측.

### ① 기준 환경 pytest (직접 재실행)
- `pytest tests/ -q` → **728 passed / 4 skipped / exit 0** (246.61s). 라운드7과 **증감 0 = 순수 치환 증명**(테스트 수·판정 불변).
- `pytest -k golden` → **28 passed** — input/partner.py 주석 diff 동반 조건(패킷 §0 예외) 충족.

### ② 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| 로직 0 | 운영 코드 3파일(client_tone_lint·rules·partner) diff 전량 = 주석·도크스트링 문자열만. 함수·분기·게이트·상수 불변 | ✓ |
| 매핑 일관 | 테스트 15파일 치환이 §2 매핑 그대로(입력·단언 동시 치환 = 의미 보존, pytest 증감 0이 증명). "순조롭-" 보존 확인 | ✓ |
| 잔존 스캔 | v2 git grep 3종(tracked 전용) 직접 재실행 → 전부 0건(원복 예외 1건 제외 — 아래 R8-2) | ✓ |
| 자기 정화 | E10 패킷 §2 실명 열 = N1~N7(파기), grep 패턴도 브래킷 형식으로 자기 비매칭 처리(영리) | ✓ |
| ignored 비접촉 | 금지 경로 diff 0, 열람·검색 기록 없음 | ✓ |
| docs/11 | 케이스 라벨만 치환·생년월일시/계산 데이터 보존(플래그 유지 — 실존 생년월일 보관 여부는 운영자 결정 잔여) | ✓ |

### ③ 리뷰어 보정 2건 (문서 한 줄씩 — 커밋에 포함)
- **R8-1**: `handoff/codex-question-adaptive-q1-q7.md`의 웨이브1 수용 기준 grep 라인이 합성명으로 치환되며
  "재실행 시 hit"이 되는 거짓 역사 기록이 됨(gunghap.py에 합성 예시명이 정당 존재) → 서술형으로 보정.
- **R8-2**: `docs/00-research-ledger.md`의 "(2022) 박사논문" 저자명은 **공개 학술 저작 인용** — 치환 시 출처
  위조(이름이 유일한 검색 키)라 원복 + E10 패킷 §4에 허용 예외 1건 명시. 공개 저작 저자명은 PII 익명화 대상 아님.
  (해당 인용도 삭제 원하시면 운영자 재지시 — 현재는 인용 무결성 우선.)

### ④ 잔여 (E10 범위 밖 — STATE 추적 중)
- ignored 실고객 산출물 55파일 정리(운영자 액션) / git 이력 실명(history rewrite 미결) / docs/11 실존 생년월일 보관 여부.

### 실행한 검증 명령
```
pytest tests/ -q            → 728 passed / 4 skipped / exit 0 (증감 0)
pytest tests/ -q -k golden  → 28 passed
git grep 3종(tracked 전용)   → 0건(학술 인용 예외 1건)
git diff 운영 코드 3파일      → 주석·도크스트링 한정
```

---
---

# 교차 리뷰 — 2026-07-10 (라운드 7, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `985031a` 위) · 구현자: Codex · 지시문: `handoff/codex-question-adaptive-wave2.md` (R6-1+Q4~Q6+Q7 설계)

## 최종 판정: **승인(PASS)** — 전 항목 패킷 정합, 게이트 강화·fail-closed 일관, 회귀 0.

Codex 완료보고를 믿지 않고 기준 환경 직접 재실행 + diff 전량 실측.

### ① 기준 환경 pytest (직접 재실행)
- `pytest tests/ -q` → **728 passed / 4 skipped / exit 0** (222.32s). 라운드6 715/4 → **+13 = 신규 테스트 완전 일치**(은닉 약화 0).
- `pytest -k golden` → **28 passed**. `git diff calc·input` → 출력 없음(계산 불변).

### ② 항목별 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| **R6-1** | monkeypatch 합성 용어 주입 → `unbacked_context_terms` 차단 발생 단언 + 기본 빈 튜플 상태 명시 단언 + 비활성 사유 주석. 라운드6 발견 종결 | ✓ |
| **Q4** | 상수 30→16 + `_min_text_chars` 상품 분기 신설(gunghap 3000/followup 2000·10p — 운영자 확정 필요 플래그 유지) + 관측 필드(minimum_pages/minimum_text_chars) 노출. 양방 경계표 테스트(15/16·2999/3000·29 유지·9999 유지·followup 9/10) + 18p 실렌더 케이스 통과 회귀. followup을 CONTEXT_REQUIRED에 편입(누락 신호 강화) | ✓ |
| **Q5** | `--pdf` opt-in. 조립=저장 Report23 복사+consult만 교체(새 계산 0 — `engine.build` 호출 시 AssertionError 테스트로 증명). 표준 render→verify(product=followup) 경유 + 10~15p 범위 게이트 + consult 직답 게이트 + 부모 가드 미통과 거부 + 저장 일간 부재 fail-closed(레거시 차단). **최종 발급(final_render_fn)도 followup 분기에서 동일 게이트 + RuntimeError fail-closed**. 기본 텍스트 경로 반환 스키마 불변 회귀 | ✓ |
| **Q6** | 접수 시 자동분류를 render_meta에 저장(생성 완료 후 Report23.concern_category와 이중 소스 — `question_category_state`가 우선순위 정리) + admin 드롭다운(IN_REVIEW 한정) + **GENERAL 미확정 승인 409 물리 차단**(기존 confirm 패턴 앞단) + audit note에 카테고리 값만(질문 원문 비복제 — 절대규칙 17 정합). 상태머신 전이 무변경, `test_orders`·`test_final_render_gate` GREEN | ✓ |
| **Q7** | `handoff/codex-q7-design.md` 설계 1페이지만, 코드 0줄. 승인 대기 항목 4개 명시(B안·분량 공식·RELATION 추천·기본값 5모듈) | ✓ |
| 기계 검증 | 변경 파일 실명 grep 0건 / calc·input·integrated.py 무변경 / 금지파일 침범 0 | ✓ |

### ③ 관찰 (비블로커)
- admin 템플릿 `action_error` 문구가 범용화("작업 차단:")되며 기존 최종발급 실패 시 "상태는 APPROVED에 머물러 있음" 안내가 사라짐 — 사소한 UX 정보 손실, 차단 동작은 동일. 다음 라운드에 문구만 보강 권고.

### ④ 미검증 (Codex 보고와 동일 — 정직 승계)
- 후속 `--pdf` 실렌더(실제 10~15p 조판)·실브라우저 UI 미확인(TestClient 회귀만). LLM 문안 미검증.
- Q7 구현은 운영자 설계 승인 전 착수 불가(설계 게이트 정상 작동).

### 실행한 검증 명령
```
pytest tests/ -q            → 728 passed / 4 skipped / exit 0
pytest tests/ -q -k golden  → 28 passed
grep 실명(변경 파일 11개)    → 0건
git diff --name-only calc·input → 출력 없음
```

---
---

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
| **Q2** 프레임 적응·스윕 | `_AXIS_KEYWORDS` 5축 추가, SYSTEM/GUIDE/_FOCUS 질문별 프레임 재작성, `build_fallback`·`frontload_summary` situation 소비(팬텀 해소, 5종 분기 상호상이 테스트). gunghap.py 죽은 관계 코드 ~250행 삭제(익명화 전 하드코딩 이름 2건 포함), _GH_SYSTEM 실명→합성명(김민준/이서연/박도윤), _GH_GUIDE·도크스트링 익명화 | ✓ |
| **Q3** 게이트 보강 | `_AXES` 신규 3축(부모동의/결혼이행/장기관계, evidence 보수적 선정—경계표 첨부됨). **any→all 강화**: 감지된 topic축 전부 evidence 요구(`missing_topic_axes` 관측 필드 추가). 김포/계양/고유 모임명·실명 1건(익명화됨) 일반어 치환, 의존 테스트만 합성어 동반 수정 | ✓ |
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
grep 익명화 대상|고유 모임명(4파일 한정)   → 0건
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
