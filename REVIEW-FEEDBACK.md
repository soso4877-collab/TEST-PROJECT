# 교차 리뷰 — 2026-07-17 (1a 재시도 피드백 형식교정형 전환, 리뷰어: Claude 신선 컨텍스트)

대상: `temporal-retry-format-feedback-20260717` 구현(base=HEAD `d55a006` 위 미커밋) · 구현자: Codex.
로드맵: 말투 개편 Stage 1 항목 1a(폴백 템플릿 제거, 비용중립).

## 최종 판정: **승인(CODE_PASS)** — 미해결 블로커 0.

폴백 최대 유발원(temporal 맨몸월/간지월)의 재시도 피드백을 "토큰 회피"→"형식 교정"으로 정확히 분기.
가드가 이미 제공하는 `why`(정답 형식 내장)를 소비만 하고, 실제 재시도 호출까지 배선됨을 E2E로 확증(팬텀 아님).

### 실측 표

| 항목 | 실측 | 판정 |
|---|---|---|
| 변경 범위 | `builder.py`(`_retry_feedback_labels`→(avoid,fix)·두 풀 누적·`_compose_one` +feedback_fix) · `llm_sections.py`(compose 3 backend +feedback_fix + 형식교정 주입 블록) · `test_temporal_month.py`(+5테스트) + Codex 메타 3(notes/STATE/manifest). scope 이탈 0 | ✓ |
| **분기 정확성** | known-time: type∈{month_notation,temporal,relative_month_boundary}+why → **fix**, 그 외 → **avoid**. format_types type은 `temporal_lint.py`만 emit(타 lint 충돌 0, grep 실측) | ✓ |
| **삼주 보호 유지** | three_pillar → `(고정라벨, set())`, raw 토큰·why 누출 0(테스트 실증) | ✓ |
| **가드 완화 0** | `temporal_lint`·`factcheck`·`safe_lint`·`style_lint` 로직 무변경(소비만). GATE_KEYS 무관·무변경 | ✓ |
| 비용중립 | feedback_fix는 재시도(attempt≥2) user 블록 전용, 첫 호출 캐시 prefix 불변. 호출 수 불변 | ✓ |
| **비-no-op·양방·팬텀 차단** | ①프롬프트 분리(형식 문구가 fix에만·avoid엔 부재) ②helper 3계열 라우팅(신사월 avoid에 없음) ③safe`반드시…`+fact`경술` avoid 유지 ④삼주 raw/why 누출 0 ⑤**E2E: 실 build_report flow 재시도가 `feedback=None·feedback_fix=why` 실수신**(소비처 배선 확증) | ✓ |
| 전체 pytest | **1114 passed / 4 skipped / exit 0**(211s) — 기준선 1110/4 + 신규 4, 감소 0, skip==4 불변 | ✓ |
| golden | **28 passed** | ✓ |
| 정적 | 변경 3 py Ruff `All checks passed!`·py_compile·`git diff --check` exit 0. calc/input diff 0 | ✓ |

### 미검증(정직 보고 — CODE_PASS 범위 밖)
- 실모델 폴백률 실제 감소(맨몸월/간지월 재시도 교정 통과)는 운영자 승인 유료 재run 몫. 이 판정은 "형식교정
  피드백이 정답 형식을 전달하고 회피형과 정확히 분기·실배선됨"의 결정론 실증에 한정.

---

# 교차 리뷰 라운드2 — 2026-07-15 (서양 점성술 off-domain 가드 B-1 수정 재검, 리뷰어: Claude)

대상: 라운드1 changes_requested의 B-1 수정분(base=HEAD `0325ce7` 위 미커밋) · 구현자: Codex.

## 최종 판정: **승인(CODE_PASS)** — 미해결 블로커 0.

라운드1 블로커 B-1(followup 텍스트 발급 게이트에 서양 점성술 하드 가드 미배선)이 **해소 확정**. `answer_gate.check`에 `western_astrology_lint`가 다른 고객정책 lint와 동일 패턴으로 배선됐고, 라운드1에서 유출됐던 바로 그 입력이 이제 실차단된다. 라운드1 사양 충족 항목은 19파일 SHA 불변으로 재확인(재작업·회귀 0).

### B-1 해소 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| 변경 범위 | `sajugen/followup/answer_gate.py`(+7: import +6배선) · `tests/test_followup_gate.py`(+31: 양방 2건). **순수 추가**(기존 15종 lint·완화 0). 다른 파일 변경 0 | ✓ |
| **B-1 실차단 확증** | 라운드1 유출 입력 `_DIRECT + "…사자자리 기질…"`을 `answer_gate.check` → **ok=False, 실패 rule=`western_astrology`**(라운드1=ok=True/failures=[]). 전용 가드가 직접 차단(우연 아님·비-no-op) | ✓ |
| 오탐 0(비-no-op) | `_DIRECT + "자미의 주성과 별… 관록궁 자리…"` → `western_astrology` rule 미발생 | ✓ |
| 라운드1 19파일 불변 | 라운드1 경계 스냅샷 전수 SHA 재대조 = 변경 0(제품/테스트/docs 재작업·회귀 0) | ✓ |
| 전체 pytest | **1110 passed / 4 skipped / exit 0**(212.41s) — 라운드1 1108/4 + 신규 2, 감소 0, skip==4 불변 | ✓ |
| golden | **28 passed** | ✓ |
| 정적 | 변경 2 py Ruff `All checks passed!`·py_compile·`git diff --check` exit 0. calc/input diff 0. 경계 스냅샷(허용4 제외 21파일) 시작=종료 SHA 무변경 | ✓ |

### 태스크 종합(라운드1+2)

전용 `western_astrology_lint`가 **개인 builder(후보·재작성·룰 골격·최종 집계) + 궁합(후보·폴백) + followup(텍스트 발급 게이트) + 최종 PDF verify() 23키(전 페이지)**에 배선돼, 서양 점성술 off-domain이 명리+자미 전용 상품의 어느 발급 표면에서도 유출 0(fail-closed)이다. packet §2 목표1(보편 유출 0)·§4(사각 축소·완화 0)·§5(compose 체인+최종 게이트 경유 양방) 충족.

### 비블로커 관찰(운영자 checkpoint 인지 — 라운드1에서 이월)

- `verify._verapdf_ua1` packet §7 범위 밖 죽은코드(F841) 정리 — 동작 보존·GREEN.
- 황도/점성 동음이의어는 고정 토큰 계약 대상·fail-closed(무해). 의미적 우회는 계약 밖(미검증).

### 미검증(정직 보고 — 판정 밖)

- 실모델 폴백률 감소(closing·followup 별자리 미생성)·실 PDF·300dpi 육안·비용 = 운영자 승인 유료 재run 몫(packet §6 분리, CODE_PASS 미포함).

### 절차·경계

- 리뷰어 수정 = 허용 4파일뿐(경계 스냅샷 대조 무변경). commit·push·API·PDF 재생성 0. 합성 테스트 산출물 외 PDF 0.
- manifest는 이 판정으로 `verified/next_actor=user`(packet §8: PASS 뒤 운영자 승인 유료 재run 결정 — Codex read-only 재확인 단계 없음). Codex 라운드1+2 구현(제품·테스트·docs 18파일)은 미커밋 = 운영자 checkpoint commit 대기.

---

# 교차 리뷰 — 2026-07-15 (서양 점성술 off-domain 가드, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `098b737`) `offdomain-zodiac-guard-20260715` 구현분 · 구현자: Codex · 지시문: `handoff/tasks/offdomain-zodiac-guard-20260715.md`(SHA `07f47dac…7af4`, manifest 핀 일치) · 근거: 4모듈 LLM-on 유료 확인에서 closing이 서양 별자리 생성 + 유출 프로브 실측(전용 가드 부재).

## 최종 판정: **수정 요청(CHANGES_REQUESTED)** — 블로커 1건.

핵심 가드 구현(전용 `western_astrology_lint`)·개인/궁합 compose 배선·GATE_KEYS 23키·최종 PDF 게이트·docs/매트릭스 등록은 **전부 사양 충족**이며 기준환경 pytest·정적 게이트·양방·오탐 0 실측 GREEN이다. 다만 **followup(후속 상담) 텍스트 발급 게이트에 신규 하드 가드가 미배선**되어 packet §2 목표1(보편 유출 0)을 그 발급 표면에서 충족하지 못한다. 아래 B-1만 수정하면 재검(라운드2) 대상이다.

### 블로커 B-1 — followup 텍스트 발급 경로가 서양 점성술 하드 가드를 우회(유출 가능)

- **결함**: `sajugen/followup/answer_gate.py:179-204` `check()`는 safe/factcheck/trace/temporal/loanword/raw_calc/register/**external_domain_advice**/customer_meta/placeholder/style/quality/guarantee/consult/markdown 15종 고객정책 lint를 돌리지만 **`western_astrology_lint`가 빠져 있다**. 이 게이트가 `sajugen/followup/compose.py:229`에서 followup 답변의 유일한 텍스트 게이트이고, `:256 if not pdf: return result`로 **pdf=False(텍스트 전용) 답변은 이 게이트만 통과하면 발급**된다. 소비 경로 = `order_flow.run_followup`(기본 `pdf=False`) → `cli.py:106·124 gen-followup`이 answer 텍스트를 emit + order 생성.
- **실행 확증(실측)**: 기존 통과 픽스처 `tests/test_followup_gate.py::_DIRECT`(실제형 followup 직답)는 `ok=True/failures=[]`. 여기에 `" 덧붙이면, 사자자리 기질이 강해 리더십이 돋보입니다."`를 주입해도 **`ok=True/failures=[]`**(게이트 통과). 같은 문자열에 `western_astrology_lint.lint`는 `사자자리`를 hard finding으로 잡지만 `answer_gate`는 못 잡는다(`western_astrology` 룰 부재). = QI 메커니즘 재현(별자리가 우연히 다른 lint에 걸릴 때만 반려, 직답형은 유출).
- **왜 최종 PDF 게이트로 안 잡히나**: pdf=True followup은 `_render_followup_pdf`(order_flow.py:178-229)가 `render_verify.verify()` 23키(신규 `western_astrology_clean` 포함)를 경유해 fail-closed로 차단된다 — **PDF 경로는 안전**. 그러나 pdf=False 텍스트 경로는 render/verify 백스톱이 없어 `answer_gate`가 사실상 최종 게이트다. 이 경로는 현재 **프롬프트 억제만** 있고 하드 가드가 없다(= 이 태스크가 "억제만으로 부족, 하드 가드 필요"라고 선언한 바로 그 구성).
- **수정 방향(Codex, 생성/발급 측 — 게이트 완화 아님)**: `answer_gate.check`에 `western_astrology_lint.lint(text)`를 다른 `_add_hits` 고객정책 lint와 동일 패턴으로 추가(예: external_domain_advice 다음, rule=`western_astrology`·severity=hard 일관) + `tests/test_followup_gate.py` 양방(별자리 followup 답변 차단 + 자미 `주성`/`별`·`관록궁 자리` 오탐 0). calc/input·기존 lint 완화 0.

### 사양 충족(재작업 불필요 — 실측 GREEN)

| 항목 | 실측 | 판정 |
|---|---|---|
| 전체 pytest(기준환경) | **1108 passed / 4 skipped / exit 0**(217.12s) — 기준선 1071/4 + 신규 37, 감소 0, skip==4 불변. Codex 기대 1108/4 정확 일치 | ✓ |
| golden | **28 passed**. 자미두수(별/주성) 포함 실콘텐츠 gate_pass=True 테스트가 23키 AND에서 전부 통과 = 신규 키 오탐 0 애그리게이트 증명 | ✓ |
| 전용 가드 로직 | `western_astrology_lint`: 최장 토큰 우선 단일 정규식(중복집계 0), 컴파운드 sign name 12종(사수/궁수 별칭)+`별자리·황도·점성·점성술`. 독립 프로브 차단 3/3·오탐 0/6(`관록궁 자리`·bare `자리/사자/게/처녀궁/물고기`·자미 `주성/별`)·`사주/시주` 정상용법 0 | ✓ |
| 개인·궁합 compose 배선 | builder `_customer_policy_lints`(후보·재작성·룰 골격·최종 집계 4소비처) + gunghap `_compose` 후보+폴백 배선. `test_register_advice_gate` 양방(별자리 후보 거부·룰폴백 RuntimeError·최종 PDF FakeDoc) | ✓ |
| 최종 PDF 게이트 | `verify.GATE_KEYS` 23키(멤버십+순서 동결 갱신 22→23), 전 페이지(표지·목차·본문·부록) 스캔, hits/count/clean. **실 PyMuPDF PDF**에서 `western_astrology_clean=False`·hits_count=2·`gate_pass=False`(test_render_verify) | ✓ |
| 재시도 판정 배선 | integrated·relationship 저밀도 단독 실패 판정에 `western_astrology_clean` 추가 = 별자리 실패를 레이아웃 재시도로 오판 안 함(진짜 콘텐츠 실패). test_integrated_product 양방 | ✓ |
| 관측(PII-free) | hverify_pdf·hsummary 화이트리스트에 `western_astrology_clean`·`_hits_count`·`_hits`(토큰/count/page만) 등록 | ✓ |
| 프롬프트 억제 | `_COMPOSE_SYSTEM` +2줄·closing guide +1문장. **SHA 핀 독립 재계산 = `76e1645d…fa32d` 정확 일치**(known-time·삼주 파생 시스템 모두 금지 계약 보존, test_western_astrology_guard) | ✓ |
| 정적 게이트 | 변경 16 py Ruff `All checks passed!`·py_compile·`git diff --check` exit 0. **calc/input diff 0**. 리뷰어 경계 스냅샷(허용 4파일 제외 19파일) 시작=종료 SHA 무변경 | ✓ |

### 비블로커 관찰(운영자 checkpoint 인지 — 재작업 아님)

- **범위 밖 소변경**: `verify.py:_verapdf_ua1`가 packet §7 범위 밖에서 기존 죽은코드(`base = None`, F841)를 정리했다. 동작 보존(구/신 분기 결과 동일 — 포터블·시스템 둘 다 없을 때만 unavailable)·Ruff GREEN. 완료 checkpoint 시 운영자 scope 인지.
- **황도/점성 동음이의어**: bare `황도`(황도 복숭아)·`점성`(粘性)은 사주 도메인에서 사실상 미출현이고 packet §3 고정 토큰 계약 대상이며 fail-closed(오차단=룰 폴백, 고객 무해). 의미적 우회는 고정 토큰 계약 밖(미검증으로 정직 보고).

### 미검증(정직 보고 — 판정 밖)

- 실모델 폴백률 감소(closing 별자리 미생성)·실 PDF·300dpi 육안·비용 = 운영자 승인 유료 재run 몫(packet §6 분리).
- B-1 수정 후 followup 텍스트 경로 실차단은 라운드2 재검 대상.

### 절차·경계

- 리뷰어 수정 = 허용 4파일뿐. 제품/테스트/docs 미수정(경계 스냅샷 대조 무변경). commit·push·API·PDF 재생성 0. 합성 테스트 산출물 외 PDF 생성 0. 고객 실데이터·local profile 비열람.
- 발주 커밋 `098b737`은 메시지가 '발주(planned)'이나 커밋 시점 manifest는 이미 review_requested였다(레이스). 실제 = Codex 완료 → Claude 교차리뷰(이 절). manifest는 이번 판정으로 `changes_requested/codex`로 전환.

---

# 교차 리뷰 — 2026-07-14 (하네스 모듈 계약 배선, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `519fc61`) `beta-1-hverify-module-contract-20260712` 구현분 · 구현자: Codex · 지시문: `handoff/tasks/beta-1-hverify-module-contract-20260712.md`(SHA `15030847…20ce8b`, manifest 핀 일치) · 근거: HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP(하네스 증거 경로가 모듈 제한 주문을 5모듈 하한으로 오판).

## 최종 판정: **승인(CODE_PASS)** — 기준환경 전체 pytest **1071 passed / 4 skipped / exit 0**(기준선 1061/4 대비 +10·감소 0·skip 불변). 하네스 모듈 계약이 프로파일→hverify→verify→hsummary + hrun argv로 원자 배선되고 fail-closed·회귀 0가 양방·비-no-op으로 실증됨. **제품 diff 0**. 미해결 블로커 0.

### 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| 제품 diff 0(하드 경계) | `git diff --stat -- sajugen/` 비어있음 + untracked sajugen 0 = **제품/calc/input 변경 0**. 변경 10파일 전부 하네스(scripts 4·profiles 1)·테스트·문서(docs/16·20)·handoff | ✓ |
| 전체 pytest | **1071 passed / 4 skipped / exit 0**(226.51s) — 기준선 1061/4 +10, 감소 0, skip==4 불변. Codex 기대값 1071/4 정확 일치 | ✓ |
| golden | 28 passed / 1047 deselected / exit 0 | ✓ |
| **실 verify() 시그니처·전달(자문 사각 — 소스 확인)** | 하네스 테스트는 `V.verify`를 mock하므로 소스로 확인: `verify.py:484-485` `module_sections`·`premerge_section_ids` **시그니처 존재**, `719-720` `analyze`로 **전달**, `735` 표면화. → hverify의 3원자 전달이 TypeError·silent drop 없음(A-5 팬텀 재발 아님). 런타임 증명은 §7.3(운영자 hrun) 몫 | ✓ |
| 배선(§3.2·§3.5) | `hverify_pdf.py`가 `selected_modules`·`module_sections`·`premerge_section_ids`를 `V.verify`에 함께 전달. explicit=False 레거시는 3인자 None → 제품이 5모듈/30p 복원(회귀 0) | ✓ |
| 계약 fail-closed(§3.1·§3.3·§3.4) | `hprofile_check.module_contract`가 제품 `sajugen.modules` 정본(normalize·`MODULE_SCHEMA_VERSION`)으로 검증, 커버리지/스키마 누락·형태오류·빈/미등록을 `invalid_module_contract`로 차단(조용한 5모듈 보정 없음). PDF 존재 검사보다 **먼저** 닫아 증거누락 미마스킹. verify 응답 역불일치도 gate 실패 | ✓ |
| §4 양방·비-no-op | 핵심 `test_hverify_applies_four_module_floor_and_preserves_legacy_floor`: captured kwargs로 **3원자 전달 실증**(4모듈=28p 통과 / 레거시=None·30p 실패). minimums는 제품 `module_minimums` 실호출(하드코딩 아님). + fail-closed(커버리지 누락·3중잠금 열려도 regen 차단=`pytest.fail` 도달 시 실패)·gunghap 혼입 차단(real coverage)·argv·pytest.skipped 보존·경계(빈/미등록/schema+1) | ✓ |
| 관측(§3.8·§3.9) | hsummary 4종(`selected_modules`·`module_schema_version`·`minimum_pages`·`minimum_text_chars`) 제품 enum·비음수 int(bool 제외)만 PII-free 보존. hrun `_run_pytest`가 passed·skipped 함께 파싱(skip 0=토큰 생략→0 확정, 형식 미파싱만 None) | ✓ |
| 정적 | Ruff 변경 5 py **All checks passed** · py_compile 5 exit 0 · `git diff --check` exit 0 | ✓ |
| 문서 | docs/16 QI-2026-07-14-01(근본원인 2층 포스트모템·false-fail 정직 명시) + docs/20 하네스 모듈 계약표(경계별 fail-closed) — §5 범위 | ✓ |
| 경계 스냅샷 | 리뷰어 read-only 8파일(docs/16·20·profile·scripts 4·test) 시작/종료 SHA 전수 일치(무변경) | ✓ |

### HEAD 경계 확인

- base HEAD `519fc61`은 **Claude(리뷰어)가 만든 재활성 커밋**이고 Codex 구현은 그 위 미커밋 8파일이다. Codex commit·push 0 실측(HEAD=519fc61 불변, working tree dirty). Codex notes의 "commit/push해"는 이 외부(Claude) 활성화 커밋을 가리키며 자기 작업으로 주장하지 않는다고 명시 — 계약 위반 아님.

### 실행한 검증 명령

```
./.venv/Scripts/python.exe -m pytest tests/ -q            # 1071 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  # 28 passed
./.venv/Scripts/python.exe -m ruff check <변경 5 py>       # All checks passed!
./.venv/Scripts/python.exe -m py_compile <변경 5 py>       # exit 0
git diff --stat -- sajugen/                               # 비어있음(제품 diff 0)
grep -n module_sections\|premerge_section_ids sajugen/render/verify.py  # 484-485 sig · 719-720 forward
```

### 미검증 (판정 밖 — 정직 보고)

- 실 `V.verify`를 통과하는 합성 모듈 제한 PDF의 hrun/hverify 1회(4모듈=28p 실적용 summary 확인) = packet §7.3, 운영자 hrun 지시 몫. 테스트가 V.verify를 mock하므로 이 층은 소스 확인으로 대체하고 런타임은 §7.3에 위임.
- 합성 테스트 산출물 외 PDF 0. commit·push·API·고객/local/ignored 비접촉.

### 다음

- manifest `verified / next_actor=user`(packet §7에 Codex 재확인 단계 없음). 운영자 = commit 여부 + (별도 지시 시) §7.3 합성 픽스처 hrun 1회로 런타임 확정.

---

# 교차 리뷰 — 2026-07-14 (삼주 실모델 품질 후속, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `74e94e5`) `three-pillar-real-model-quality-followup-20260714` 구현분 · 구현자: Codex · 지시문: `handoff/tasks/three-pillar-real-model-quality-followup-20260714.md`(SHA `7533f515…647167`, manifest 핀 일치) · 근거: QI-2026-07-13-02 유료 재run(2026-07-14) 실측 거동·육안 nit 2건.

## 최종 판정: **승인(CODE_PASS — no-LLM/mock 층)** — 기준환경 전체 pytest **1061 passed / 4 skipped / exit 0**(기준선 1049/4 대비 +12, 감소 0, skip 불변). 프롬프트 억제 강화(생성 측 한정)·조사 `_J` 배선·표지 h1 keep-all이 양방·비-no-op 회귀로 실증. 미해결 블로커 0. 비차단 scope 플래그 1건(운영자 checkpoint 확인).

**⚠️ CODE_PASS ≠ "품질 개선 완료".** 이 판정은 no-LLM/mock 층에서 (a) 프롬프트가 관측 금칙(`시주`·맨몸월·§12 메타)을 더는 **포함하지 않고** 억제 지시를 **포함하며**, (b) 조사가 결정론임을 증명한다. **packet 목표 #1(실 Sonnet의 4챕터 폴백률↓)은 이 층에서 증명 불가** — 실모델이 실제로 금칙 생성을 멈추는지는 운영자 승인 유료 재run(packet §6·§8)으로만 확정된다. 운영자의 다음 결정은 "이미 고쳤다"가 아니라 **유료 재run으로 폴백률 감소·조사 육안 재측정**이다.

### 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| diff 범위 | packet §7 정합 — 프롬프트(`llm_sections.py` 삼주 파생 system·override·temporal), 조사(`rules.py` 삼주 골격 `_J` + meta 순화), 표지(`report.html.j2` h1 keep-all), 테스트 3파일, 문서(docs/16·notes·STATE·manifest). **calc/input·`render/verify.py` 게이트·factcheck/safe/style lint·`GATE_KEYS` 변경 0**(diff+`git status -uall -- sajugen/calc sajugen/input` 양쪽 0) | ✓ |
| 전체 pytest | **1061 passed / 4 skipped / exit 0**(241.31s) — 기준선 1049/4 +12, 감소 0, skip==4 불변(passed→skipped 은닉 0). Codex 기대값 1061/4와 정확 일치 | ✓ |
| golden | 28 passed / 1037 deselected / exit 0 | ✓ |
| 억제 강화(생성 측 한정) | `llm_sections.py` 변경 전량이 삼주 게이팅(`three_pillar` 분기) 또는 삼주 파생 system 전용(`_THREE_PILLAR_SYSTEM_REPLACEMENTS` +2·`_THREE_PILLAR_SYSTEM_OVERRIDE`·`_THREE_PILLAR_COMPOSE_GUIDE`). known `_COMPOSE_SYSTEM` 정의·`temporal_anchor` else-branch(`이 풀이의`·`ref_date` 주입) 바이트 불변. **게이트/가드/factcheck/safe/style 미변경** | ✓ |
| §4 known 바이트 | `test_known_time_compose_request_preserves_original_system_and_user_bytes` SHA 핀(`a17f90fb…380a`) — `_COMPOSE_SYSTEM` diff 미변경 → 전체 run 포함 GREEN | ✓ |
| §5 억제 지시 배선(A-5 팬텀 아님) | `test_three_pillar_failed_chapter_prompts_suppress_observed_output_tokens`가 SDK 경계에서 **realized 요청**을 캡처 → "누락된 자리를 이름 붙이지 않는다"가 `system_text`에 실재 + `운명이 정해`·`이 풀이`·`시주`·맨몸월(정규식 `(?<!\d)\d{1,2}월`) 부재를 4챕터(intro/nature/flow/consult) 장별 1차원인+공통계약으로 단언. 정의만이 아닌 **소비 증명** | ✓ |
| §5 조사 결정론 | `test_three_pillar_ganzhi_josa_table`(받침 유무 6종 `_J` 직접) + `…nature_routes_ganzhi_particles_through_josa_helper`(production `build_all` 실골격 양방 — `정축이`/`임신이`/`무는` present·`정축가`/`무은` absent·병기 `이(가)`·mojibake `�` absent). Codex 보고 구현 전 RED | ✓ |
| §5 폴백 축 비악화 | 기존 `test_three_pillar_fallback_axes` 3종 유지(diff 추가만·삭제 0) | ✓ |
| §5 표지 h1 | `test_report_template_keeps_cover_heading_syllables_together`가 `.cover h1` 셀렉터에 keep-all/overflow-wrap/line-break 고정(정적, 제거 시 RED). template diff = `.cover h1`에 3속성 추가만 | ✓ |
| rules.py 바이트 | 조사·meta 순화 = 삼주 전용(의도적 바이트 변경=테스트 커버). F541/F841 정리(scope 플래그 참조)는 바이트 불변 — F541=placeholder 없는 f-string→일반 문자열(전부 `{}` 부재), F841 `day_sg`=전체 참조 0(grep). golden 28 GREEN이 known-time 문자열 바이트 불변 담보 | ✓ |
| 정적 | Ruff 변경 5 py **All checks passed**(rules.py 부채 완전 해소) · py_compile(5) exit 0 · `git diff --check` exit 0 · calc/input 무변경 | ✓ |
| 경계 스냅샷 | 리뷰어 read-only 7파일(docs/16·llm_sections·rules·report.html.j2·테스트 3) 시작/종료 SHA 전수 일치(무변경) | ✓ |

### 비차단 scope 플래그 (운영자 checkpoint 확인)

- Codex가 `rules.py`의 **기존 Ruff 부채(F541 16 + F841 1)를 packet scope 밖에서 함께 제거**했다. 이유 = "변경 Python Ruff GREEN"(packet §6) 완료 조건을 문자 그대로 충족. 바이트 불변은 검증됨(F541 자명 · `day_sg` 미사용 실측 · golden 28). 이전 라운드는 이 부채를 "기존 구성 동일 = 신규 0"으로 수용해 왔으나 이번엔 정리를 택했다 → **checkpoint 시 운영자가 scope 확장을 인지**할 것(정당·비악화이나 packet 명시 변경 유형 밖).

### 실행한 검증 명령

```
./.venv/Scripts/python.exe -m pytest tests/ -q            # 1061 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  # 28 passed
./.venv/Scripts/python.exe -m ruff check <변경 5 py>       # All checks passed!
./.venv/Scripts/python.exe -m py_compile <변경 5 py>       # exit 0
git diff --check                                          # exit 0
```

### 미검증 (판정 밖 — 정직 보고)

- 실모델 4챕터 폴백률 감소·실 PDF 조사(`정축이`) 육안·표지 h1 개행 조판 = 운영자 승인 유료 재run(packet §6·§8) 몫. no-LLM/mock 층은 프롬프트·조사·정적 CSS만 증명한다.
- 합성 테스트 산출물 외 PDF 생성 0. commit·push·API·고객/local/ignored 비접촉.

### 다음

- manifest `verified / next_actor=user`(packet §8에 Codex 재확인 단계 없음 — grounding-fix 라운드와 동일). 운영자 checkpoint = (1) scope 플래그 확인 (2) commit 여부 결정 (3) **유료 재run으로 폴백률·조사 육안 재측정**. 통과 전 APPROVED·발송 금지.

---

# 교차 리뷰 — 2026-07-14 (삼주 LLM 근거화, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `c4cd93b`) `three-pillar-llm-grounding-fix-20260713` 구현분 · 구현자: Codex · 지시문: `handoff/tasks/three-pillar-llm-grounding-fix-20260713.md` (SHA `3e119a5a…b600c4`, manifest 핀 일치) · 근거 사고: QI-2026-07-13-02.

## 최종 판정: **승인(CODE_PASS — no-LLM/mock 층)** — 기준환경 전체 pytest **1049 passed / 4 skipped / exit 0**(기준선 1036/4 대비 +13, 기존 감소 0, skip 불변). 삼주 근거화·폴백 축·오류경로 usage 영속이 양방·비-no-op 회귀로 실증됨. 미해결 블로커 0. 비차단 문서 finding 1건(정정 완료). 실모델 `gate_pass` 재측정은 판정 밖(운영자 승인 유료 재run 몫).

### 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| diff 범위 | packet §7 정합 — 생성/근거(`llm_sections.py`·`rules.py`·`report_context.py`), 배선(`builder.py`), 관측(`order_flow.py`), 테스트 4+신규 1, 문서(docs/16·notes·STATE·manifest). **calc/input·`render/verify.py` 게이트·factcheck/safe/style lint 변경 0**(diff+`git status -uall -- sajugen/calc sajugen/input` 양쪽 0) | ✓ |
| 전체 pytest | **1049 passed / 4 skipped / exit 0** (199.75s) — 기준선 1036/4 +13, 기존 감소 0, skip==4 불변(passed→skipped 은닉 회귀 0). Codex 환경 1021/32와는 raw 미비교(환경 skip 차 28) | ✓ |
| golden | 28 passed / exit 0 | ✓ |
| 집중 | 변경 4테스트 + 신규 `test_three_pillar_fallback_axes.py` = **62 passed / exit 0** | ✓ |
| §4 known 바이트 보존 | `test_known_time_compose_request_preserves_original_system_and_user_bytes`가 `_COMPOSE_SYSTEM` SHA-256 핀(`a17f90fb…380a`)+system block 구조+`_THREE_PILLAR_SYSTEM_OVERRIDE` 부재로 고정. 삼주 분기(`source_scope`/`temporal_anchor(three_pillar=)`/compose)는 전부 `birth_time_mode=="three_pillar"` 게이팅, known은 `source_scope=""`로 바이트 동일 → builder.py 스코프 우려 해소 | ✓ |
| §5.1 구조적 부재 | `test_three_pillar_compose_request…`: system+user 전량에 고정 예시 토큰(임술일주·경오·신금·병오년·7월 병신월) 부재 + `factcheck.check(full_request, saju)==[]`. 실 `rules.build_all` base_text 사용 | ✓ |
| §5.2 fail-closed | `…fails_closed_before_api_for_invalid_source_scope`: scope 4종(None·()·불일치·계약외) → `base_text` 반환, API `create` 도달 시 `pytest.fail`(비-no-op 증명). 정상 scope는 API 도달(통과측) | ✓ |
| §5.3 폴백 축 | `test_three_pillar_fallback_axes.py`: 복합 6축·단일축·무축 경계를 production `_axis_evidence_hits`·`consult_direct_result`·`style_lint`·`verify._semantic_style_hits`로 검증(tautology 아님). 시기=실 세운 연도만, 월운 원시값 미노출 | ✓ |
| §5.4 오류경로 usage | `test_generation_error_persists_isolated_llm_usage`: 생성 예외 주입 → `NORMALIZED`+`render_meta["llm_usage"]` 정확 영속+`generation_error` audit+collector reset. 성공 경로 중복 저장 회피 | ✓ |
| §5.5 classify strict | 정상 tool-use(strict·enum·tool_choice·max_retries 부재·usage 7/2/1) + 6-case parse 실패(invalid-enum·missing·extra-field·no-tool·wrong-name·multi) → 룰 폴백+usage 유지(7/2/1)+PII 미유출. api 오류=usage 0/0/0 구분 | ✓ |
| §5.6 경계·오탐 | 재시도 sanitize: 금칙 `경오월` 재시도 피드백 미복제(고정 라벨만). `_retry_feedback_labels` consult_direct 분기 live(builder.py:554-561이 실제 violation 생성) | ✓ |
| concern_text 배선 | `build_report`(builder.py:316) → `build_all`(rules.py:1166) → `_build_three_pillar_all` → `_consult_context` 생산 경로 실전달(A-5 팬텀 아님, 소스 실측) | ✓ |
| 정적 | py_compile(9) exit 0 · `git diff --check` exit 0 · Ruff: rules.py 기존 17건(F841 1+F541 16) **HEAD==worktree 구성 동일=신규 0**, 다른 8파일 GREEN | ✓ |
| 경계 스냅샷 | 허용 4파일 제외 dirty+untracked 10파일 시작 SHA 수집(종료 대조는 산출 기록 후) | ✓ |

### 비차단 finding (정정 완료)

- Codex `implementation-notes.md`가 인용한 HEAD full SHA `c4cd93b17421f781bd602c1eb2d9df99aaf7e410`가 실제 HEAD `c4cd93b17421c408a1757b387a772a7f2365c2f3`와 12자 이후 불일치. short prefix `c4cd93b`는 정확해 리뷰 대상(워킹트리 diff)엔 영향 0. notes에서 실제 HEAD로 정정하고 정정 주석을 남겼다.

### 실행한 검증 명령
```
Get-FileHash(경계 스냅샷 시작 10파일) + calc/input diff·status                 → 무변경(양쪽 0)
py_compile(9) / git diff --check                                              → exit 0 / exit 0
ruff check(9) + git show HEAD:rules.py 대조                                    → rules.py 17(구성 동일·신규 0), 8파일 GREEN
./.venv/Scripts/python.exe -m pytest tests/ -q                                → 1049 passed / 4 skipped / exit 0 (199.75s)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden                      → 28 passed / exit 0
./.venv/Scripts/python.exe -m pytest (집중 4+신규 1) -q                        → 62 passed / exit 0
소스 추적: consult_direct violation(builder.py:554) · concern_text 배선(builder.py:316→rules.py:1166)
```

### 정적 확인 완료 (구현 검증)
- classify tool의 `"strict": True`는 **유효한 GA 필드**로 확인. Anthropic Messages API는 custom tool 정의에 `name`/`description`/`input_schema`와 나란히 top-level `strict: true`를 허용하며(no beta), 스키마의 `additionalProperties:false`+`required`와 함께 `tool_use.input`을 정확히 강제한다. 구현이 정확히 이 형태다(claude-api 레퍼런스 대조). 지원 모델 = Fable 5/Opus 4.8/Sonnet 5/**Haiku 4.5**이며 classify 모델이 `claude-haiku-4-5-20251001`(config.py:38)이라 지원 범위 안이다 → 400 위험 없음(advisor 지적대로 실모델 질문이 아니라 정적 계약 질문이라 무과금 확인).

### 미검증(정직 보고)
- 실모델 삼주 `integrated_full` × 실복합 고민의 `gate_pass=True`, 실 PDF·300dpi 육안·비용은 이 CODE_PASS 범위 밖 = **운영자 승인 유료 재run(운영자/Claude 환경) 몫**. pytest 합성 테스트 산출물 외 PDF 생성 0. commit·push·API·LLM 없음.
- 사고 당시 `InstructorRetryException` 내부 원인은 로그 부재로 사후 확정 불가(설정 취약점은 direct strict tool로 보강).

다음: 운영자 checkpoint — 승인 유료 재run 1회로 실 `gate_pass` 재측정 결정. 통과 시에만 표준 게이트→hrun→hsweep(과금 선보고)→300dpi 육안→운영자 전문 검수 Z=0 뒤 APPROVED/수동 발송. Claude PASS 뒤 Codex 재확인은 열지 않는다(역할 계약).

---
---

# 운영자 checkpoint 종결 — 2026-07-13 (표지 keep-all + 낙관 안전 여백)

대상: `cover-sub-keepall-20260713` · 제품 commit `2fc7309` · 역할 계약 commit `7ff7f56`

## 최종 판정: **승인(EVIDENCE_SPLIT_PASS) / checkpoint 완료**

Claude 라운드23의 기준환경 실렌더와 Codex의 코드·스코프·전체 회귀를 동일 tree의 분리 증거로 수용했다. 운영자 승인 후 표지 1쪽을 실제 PNG로 확인했고, 기존 keep-all만으로 생긴 오른쪽 낙관 충돌을 `max-width:var(--maxw)`와 실제 PDF 좌표 회귀로 닫았다. 미해결 코드·조판 블로커는 0이다.

| 항목 | 최종 실측 | 판정 |
|---|---|---|
| 제품 변경 | `report.html.j2`의 `.cover .sub`에 keep-all 3종 + 본문과 같은 최대 폭 적용. 게이트·고지 문안·낙관 배치 코드는 무변경 | ✓ |
| 실제 좌표 회귀 | `test_p8.py`가 표지 고지 line bbox와 PDF에 실제 삽입된 오른쪽 아래 낙관 image XObject bbox를 비교. 수평 여백 약 **4.16mm**, 계약 하한 **2mm** | ✓ |
| 육안 검수 | 최신 합성 `e2e_p8_unknown.pdf` 표지 1쪽을 PDFium으로 PNG 렌더. 음절 분리·글자 잘림·낙관 겹침·깨진 글자 0, 좌우 균형 정상 | ✓ |
| 기준환경 증거 | Claude 라운드23: 전체 **1036 passed / 4 skipped**, `test_p8` **3 passed**, golden 28 | ✓ |
| Codex 재검증 | 전체 **1008 passed / 32 skipped**, golden 28, Playwright 실렌더 `test_p8` **3 passed**, 최종 unknown-time 좌표 E2E **1 passed**, Ruff·py_compile·diff-check GREEN | ✓ |
| commit 경계 | `2fc7309` = 제품+회귀 2파일, `7ff7f56` = `AGENTS.md` 역할 계약 1파일. push 없음 | ✓ |

### 계약 정리

- Codex 환경의 기본 28건 추가 skip은 코드 실패가 아니라 환경 capability 차이다. 기준환경 실렌더와 Codex 전체/정적 증거를 합성하고 같은 검증을 세 번째 actor에게 반복시키지 않는다.
- 미고정 `handoff/tasks/cover-sub-keepall-codex-confirm-20260713.md`는 활성 packet이 아니며 commit·후속 실행에서 제외한다. 권위 지시문은 manifest가 SHA로 고정한 `handoff/tasks/cover-sub-keepall-20260713.md` 하나다.
- 라운드18의 범위 밖 2변경과 삼주 delivery 하한은 이미 beta-2 제품·검증·handoff checkpoint(`2cad29c`·`02b3c48`·`763ed73`)에 포함돼 main에 반영된 역사 항목이다. 운영자의 권장 경로 진행 승인에 따라 이번 표지 태스크의 미해결 조건으로 다시 이월하지 않는다.

### 미검증(정직 보고)

- 실고객 PDF 재생성·300dpi 전문 검수·Anthropic API·hrun·hsweep·APPROVED·발송은 이번 checkpoint 범위 밖이다.
- 이번 시각검수는 PII 0 합성 표지만 사용했다. 고객 데이터·고객 PDF는 열람하지 않았다.

다음: handoff를 `done / next_actor=none`으로 종결한다. push와 실고객 작업은 별도 운영자 승인 대상이다.

---

# 교차 리뷰 — 2026-07-13 (라운드 23, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `79cdec1` 위, base=`763ed73`) 표지 고지 keep-all 수정분 · 구현자: Codex · 지시문: `handoff/tasks/cover-sub-keepall-20260713.md`

## 최종 판정: **승인(CODE_PASS)** — 기준환경 전체 pytest **1036 passed / 4 skipped / exit 0**. test_p8 삼주 E2E 실렌더 통과 + 표지 추출 실측으로 고지 개행이 어절 경계에서만 일어남을 확정. **양방(RED/GREEN) 실렌더 증거 확보** — 라운드22가 상속받았던 무공백 테스트와 달리 이번 keep-all 가드의 RED를 직접 실측. 미해결 블로커 0.

### 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| 수정 내용 | `report.html.j2:60` `.cover .sub`에 `word-break:keep-all;overflow-wrap:normal;line-break:strict` +1줄(`.toc-name`·`h2.ctitle`과 동일 3종, 기존 속성 유지) + `test_p8.py:111` 공백 보존 정규화(`" ".join(text.split())`) 고지 1회 단언 추가(기존 무공백 단언 유지 — 층 추가) + 검증/비검증 도크스트링. 패킷 §1·§2 사양 그대로, 게이트·lint·고지 문안·다른 셀렉터 무변경 | ✓ |
| 변경 집합 | 제품/테스트 2파일(`report.html.j2` +1 / `test_p8.py` +5) + 인계 3종(manifest·notes·STATE). 그 외 변경 0 | ✓ |
| 전체 pytest | **1036 passed / 4 skipped / exit 0** (215.66s) — 라운드22 기준선 1036/4 유지, passed 감소 0 | ✓ |
| test_p8 실렌더 | 3/3 PASSED (solar·leap·unknown_time 전부 Playwright 실행, 35.77s — skip 아님). `_assert_gate`로 세 상품 렌더 전부 `gate_pass=True` — 전 상품 표지 변경 비악화 근거 | ✓ |
| 표지 추출 실측 | 방금 렌더된 `e2e_p8_unknown.pdf` 표지(0쪽) 원문: 고지의 **유일 개행 = `세부\n해석은`**(어절 경계). 무공백 count 1 / 공백보존 count 1 / 원문 부분문자열 존재 True | ✓ |
| **양방(RED) 증거** | keep-all 1줄 임시 제거 → `test_e2e_unknown_time` **line 111(공백보존) RED(`assert 0==1`) / line 110(무공백) GREEN**. 새 단언이 no-op 아님을 실증하고 라운드21 음절 중간 개행("해석\n은") 결함을 재현. 복원 후 template diff = keep-all +1줄뿐(정확 복원) | ✓ |
| golden | 28 passed | ✓ |
| 정적 | Ruff(test_p8.py) `All checks passed!` · py_compile exit 0 · `git diff --check` exit 0 | ✓ |

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q             → 1036 passed / 4 skipped / exit 0 (215.66s)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden   → 28 passed
./.venv/Scripts/python.exe -m pytest tests/test_p8.py -v   → 3 passed (전부 실렌더, unknown_time 포함 skip 아님)
표지 추출 프로브(기존 PDF 재사용, 읽기 전용)                → 고지 개행 = 세부\n해석은 (어절 경계), count 1/1
keep-all 제거 후 test_e2e_unknown_time                     → line 111 RED / line 110 GREEN (양방), 복원 후 diff = +1줄
Ruff test_p8.py / py_compile / git diff --check            → All checks passed / exit 0 / exit 0
```

### 미검증(정직 보고)
- **표지 좌우 균형·시각 조판 품질은 미검증** — `layout_geometry`는 이 환경 skip(비게이트 키)이라 자동 게이트가 표지 기하를 검증하지 않는다. keep-all은 **어절 경계 개행만** 보장하며 좌우 균형은 별개(운영자 육안 몫, 패킷 §4.3 — checkpoint 전 표지 1쪽 육안 권장).
- 실 Anthropic API·고객 주문 PDF·실상품 재생성·hrun·hsweep·300dpi·육안 Z=0 — CODE_PASS 교차리뷰 범위 밖. pytest·프로브 합성 산출물 외 PDF 생성 0. commit·push·API 없음.
- 누적 checkpoint 확인 3건(운영자 몫): ① 스코프 밖 변경 2건(라운드18 rules 문구 순화·order_flow enum 정본화)의 "운영자 추가 승인" 주장 ② 삼주 delivery 하한 12쪽/3,500자 수치 ③ 표지 고지 좌우 균형 육안.

다음: Codex 신선 read-only 확인 → PASS 시 운영자 checkpoint commit 결정(위 확인 3건 포함). API·유료 재생성·commit·push 금지 유지.

---
---

# 교차 리뷰 — 2026-07-13 (라운드 22, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `084e04c` 위) 라운드21 잔존 1건 수정분(test_p8 무공백 정규화) · 구현자: Codex · 지시문: `handoff/tasks/beta-2-round21-blocker-fix-20260713.md` (SHA `db54f027…dd46`)

## 최종 판정: **승인(CODE_PASS)** — 기준환경 전체 pytest **1036 passed / 4 skipped / exit 0** (beta-2 삼주 태스크 최초 전체 GREEN). 삼주 E2E 실렌더가 skip 아닌 실행으로 게이트+후단 계약 전부 통과. 미해결 블로커 0.

### 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| 수정 내용 | test_p8.py 101-125행 — 추출문·고지 상수·양성 3토큰(年柱 등)·금지 9토큰 전부 무공백(`re.sub(r"\s+", "", …)`) 기준 판정 + 사유·fail-closed 과탐 주석. 생성 인자·게이트 단언·제품 코드·조판 무변경 — 패킷 §1 사양 그대로 | ✓ |
| 변경 집합 | **SHA 증명**(라운드21 종료 vs 라운드22 시작 스냅샷 전수 대조): 경계 54파일 중 변경 = `tests/test_p8.py` 정확히 1개. 인계 3종 외 그 외 변경 0. 동결 핀 5종 불변 | ✓ |
| 전체 pytest | **1036 passed / 4 skipped / exit 0** (229.8s) — 라운드21 1035+1(E2E 전환), 기존 감소 0 | ✓ |
| test_p8 실렌더 | 3/3 PASSED (solar·leap·unknown_time 전부 Playwright 실행, 26.7s — skip 아님) | ✓ |
| golden | 28 passed | ✓ |
| 정적 | 변경 38파일 합집합: Ruff 부채 rules.py 17 + verify.py 1(구성 동일·신규 0) · py_compile exit 0 · `git diff --check` exit 0 | ✓ |
| 절차 | manifest validate exit 0(Codex write 성공) · REVIEW-FEEDBACK 라운드 절 구조 불변 · 리뷰어 제품/테스트 무수정 | ✓ |

### 실행한 검증 명령
```
node handoff.mjs validate                                  → HANDOFF_VALID / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q             → 1036 passed / 4 skipped / exit 0 (229.8s)
./.venv/Scripts/python.exe -m pytest tests/test_p8.py -v   → 3 passed (unknown_time 포함 전부 실렌더 PASSED)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden   → 28 passed
./.venv/Scripts/python.exe -m ruff check / py_compile (38) → 부채 18(구성 동일·신규 0) / exit 0 · git diff --check → exit 0
Get-FileHash(.ps1) 스냅샷 전수 대조                          → 라운드21 종료 대비 변경 = test_p8.py 1개뿐
```

### 미검증(정직 보고)
- 실제 Anthropic API·고객 주문 PDF·실상품 재생성·hrun·hsweep·300dpi·육안 Z=0 — 이 판정은 CODE_PASS 교차리뷰 범위다. pytest 합성 산출물 외 PDF 생성 0. commit·push·API 없음.
- checkpoint 시 운영자 확인 3건(누적): ① 스코프 밖 변경 2건(라운드18 rules 문구 순화·order_flow enum 정본화)의 "운영자 추가 승인" 주장 ② 삼주 delivery 하한 12쪽/3,500자 수치 ③ 표지 고지 음절 중간 개행 조판(word-break: keep-all 후보, advisory).

다음: Codex 신선 read-only 확인 → PASS 시 운영자 checkpoint commit 결정(위 확인 3건 포함). API·유료 재생성·commit·push 금지 유지.

---
---

# 교차 리뷰 — 2026-07-13 (라운드 21, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `084e04c` 위) 라운드20 잔존 블로커 3건 수정분 · 구현자: Codex · 지시문: `handoff/tasks/beta-2-round20-blockers-fix-20260713.md` v2 (SHA `04d5ee5f…d59d`)

## 최종 판정: **수정 요청(changes_requested)** — 라운드20 블로커 3건(style·quality·delivery)은 제품 수준에서 전부 해소 실측(**gate_pass=True**). 잔존 1건은 **테스트 전용 잠복 결함**(test_p8 정규화 방식)으로, 게이트가 처음 통과한 이번 라운드에야 처음 실행된 단언이다. 제품 코드 수정 불요.

### 라운드20 블로커 처리 실측 (전부 완결)

| 항목 | 실측 | 판정 |
|---|---|---|
| B1 style | `three_pillar_table` 공백 join(charts.py:317·321, manse_table 불가침) + 부록 "세운과 월운"·마커 "본문에 나온" 추가(rules.py:1083·1089). E2E 동일 입력 verify: `style_clean=True`. PDF 실측: 표지 고지(불가침) 외 전 페이지 가운뎃점 0, 부록 구역 제외 적용 | ✓ |
| B2 quality | frame "이번 풀이에서 다루지 않습니다"(rules.py:1014) — `quality_clean=True`, final_text 매트릭스 전 섹션 quality 0 | ✓ |
| B3 delivery | `analyze(birth_time_mode=None)` 신설 + verify:722 배선 + 명시 three_pillar만 12쪽/3,500자·`missing_usable_ziwei` 면제(delivery_quality.py:800·863-872·933). `delivery_quality_clean=True`·failures=[] 실측. 3방 회귀 실재(통과 14쪽/4,600자·차단 8쪽/2,000자+보장표현·비악화 None==known dict 완전 동일+known ziwei 요구 유지) + 배선 spy 테스트 | ✓ |
| §4 회귀 | final_text 전 섹션 × quality/style 0(리뷰어 독립 프로브 동일 재현: 14섹션 전부 DOTS/STYLE/QUALITY 0) + 차단측 2건 + 차트 `·` 0 단언 + 층 구분 도크스트링 | ✓ |
| §5 QI | `QI-2026-07-13-01` docs/16 기록(2층 원인·재발 방지·PII 0) | ✓ |
| 게이트 비악화 | GATE_KEYS 무변경, lint 4파일(style/quality/customer_meta/client_tone) git 무수정, verify 변경 = analyze 인자 전달 1곳 | ✓ |

### 잔존 블로커 (신규 발견 — 테스트 전용)

1. **`tests/test_p8.py:101-115` 공백 보존 정규화가 한국어 음절 중간 개행을 복원하지 못함**
   - 실측: 전체 pytest **1 failed / 1035 passed / 4 skipped / exit 1**. 실패 = `test_e2e_unknown_time` `assert 0 == 1`(102행 고지 카운트). 원인: 표지에서 고지가 "…세부 해석"|"은 제외했습니다."로 **음절 중간 줄바꿈** → 추출 텍스트 "해석\n은" → `" ".join(text.split())`이 단어 내부 개행을 "해석 은"으로 만들어 상수(65자, 바이트 동일)와 불일치.
   - 제품 정상 실측: **공백 전제거 기준 고지 정확 1회·금지 토큰 9종 전부 0**. HTML 층 고지 1회 테스트도 GREEN. 즉 계약 위반 없음 — 카운트 방법만 조판 현실과 불일치.
   - 이 단언은 라운드18에 작성됐으나 게이트 실패로 한 번도 도달한 적이 없던 잠복 결함(게이트 통과 후에만 실행되는 코드 + Codex 환경 E2E skip).
   - 수정 방향(테스트만): 101-115행 판정을 **무공백 기준**(`re.sub(r"\s+", "", …)`)으로 — 고지 카운트·"年柱" 등 양성 단언(2자 한자 토큰도 같은 개행 취약, 인접)·금지 스캔 전부. 금지 스캔의 무공백화는 어절 경계 결합 과탐 가능성이 있으나 fail-closed 방향이라 허용(도크스트링에 명시). 제품·게이트 수정 금지.
   - advisory(비차단): 표지 고지의 음절 중간 개행 자체는 조판 품질 사안(`word-break: keep-all` 후보) — 운영자 육안 검수 시 판단, 이번 스코프 아님.

### GREEN 실측 / 실행한 검증 명령
```
node handoff.mjs validate                                  → HANDOFF_VALID / exit 0 (Codex write 성공 — 직전 GIT_COMMAND_FAILED 재발 없음)
./.venv/Scripts/python.exe -m pytest tests/ -q             → 1 failed / 1035 passed / 4 skipped / exit 1 (217.9s; +3 신규, 기존 감소 0, 실패는 위 1건뿐)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden   → 28 passed
./.venv/Scripts/python.exe -m pytest (집중 4파일) -q        → 82 passed / 1 failed (동일 재현)
r20_diag(-m, 합성): verify 전체 덤프                        → gate_pass=True, False 키 = layout_geometry_skipped·verapdf(비게이트, 7.1-3 비악화)뿐, DQ_FAILURES=[]
r20_finaltext(-m): 빌더 final_text 14섹션                   → DOTS/STYLE/QUALITY 전부 0
r21_nospace(-m): 무공백 기준                                → 고지 1회 / 금지 9종 0 (제품 정상 확정)
Ruff(38 합집합) → 부채 rules.py 17 + verify.py 1(구성 동일·신규 0) · py_compile exit 0 · git diff --check exit 0
경계 스냅샷 53파일 시작 수집 + 동결 핀 4종·REVIEW-FEEDBACK 불변 확인(종료 대조는 기록 후)
```

### 미검증(정직 보고)
- 실LLM·고객 PDF·비용·hsweep K/Z·300dpi·육안 Z=0 동일. pytest·진단 프로브 합성 산출물 외 PDF 생성 0. commit·push·API 없음.
- 스코프 밖 변경 2건 플래그·삼주 delivery 하한 수치(12쪽/3,500자) 최종 확인은 checkpoint 시 운영자 몫.

다음: Codex가 잔존 1건(test_p8 무공백 정규화)만 수정 → Claude 라운드22 재검증(전체 GREEN 기대) → Codex 신선 read-only 확인 → 운영자 checkpoint commit.

---
---

# 교차 리뷰 — 2026-07-13 (라운드 20, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `084e04c` 위) 라운드19 잔존 블로커 수정분 · 구현자: Codex · 지시문: `handoff/tasks/beta-2-round19-blocker-fix-20260713.md` (+ REVIEW-FEEDBACK 라운드19 절)

## 최종 판정: **수정 요청(changes_requested)** — 패킷 범위(wonguk 문장 치환 + 골격×meta 회귀)는 사양대로 완결이나, E2E는 라운드19 리뷰가 열거하지 못했던 별개 게이트 3키로 여전히 RED. 잔존 블로커 3건(그중 1건은 운영자 정책 결정 선행 필요).

### 패킷 이행 실측 (Codex 구현 자체 = 사양 충족)

- `rules.py:999` "함께 읽습니다" → "살핍니다" 1곳 치환 확인, "세 자리를 따로 떼어 길흉 단정하지 않는다" 관법 의미 보존. repo 전체 "함께 읽습니다" 잔존 0. `customer_meta_lint.py`·`client_tone_lint.py`·`temporal_lint.py`는 git 기준 전 라운드 통틀어 무변경(lint 완화·예외 추가 0).
- 신규 회귀 `test_unknown_time_provenance_gate.py::test_three_pillar_rule_skeletons_do_not_conflict_with_final_text_lints`: 실계산(`engine.build` 삼주) 골격 전 키 × customer_meta/loanword/raw_calc == [] + 차단측(수정 전 문장 → `guided_structure_walkthrough` 정확 1건) 양방 단언 + 도크스트링(검증 범위/비범위·라운드19 실사고 근거) — 패킷 §2 사양 충족, 기준환경 GREEN.
- 리뷰어 독립 프로브(합성, PII 0, venv -m 형식): SKELETON_KEYS=17 전수 HITS=0, **TOTAL_HIT_RULES=0**, 차단측 `guided_structure_walkthrough` 재현. E2E verify 실측에서도 `ai_meta_hits=[]`·`customer_meta_clean=True` — 라운드19 잔존 충돌 자체는 해소.

### 잔존 블로커 (라운드19 리뷰의 열거 누락 — E2E gate_pass=False 지속)

전체 pytest = **1 failed / 1032 passed / 4 skipped / exit 1**(216.4s). 실패 = `test_p8.py::test_e2e_unknown_time` 단건, 집중 재실행 동일 재현(결정론). 동일 합성 입력의 verify 전체 덤프로 게이트 실패 키 3개를 실측 열거(모두 GATE_KEYS 구성원, verapdf 7.1-3은 비게이트·기존 비악화):

1. **style_clean=False — `ai_signature_punctuation` 2건 (가운뎃점)**
   - 4쪽: 삼주 명식표 `charts.py:317·321`이 지장간·지지십성을 `"·".join`으로 나열 — 대조 실측: known E2E PDF 2건(e2e_pipeline·e2e_p8_solar)은 **전 페이지 가운뎃점 0**. 삼주 차트가 고객 본문 페이지에 가운뎃점을 신규 도입한 결함.
   - 13쪽: 삼주 부록 골격 "세운·월운"(`rules.py:1088`) + 삼주 부록에 verify 부록 구역 마커 문구 "본문에 나온"(`verify.py:117 _APPENDIX_MARK`)이 없어 **부록 제외 자체가 미적용**(이중 결함 — 전문용어 허용·저밀도 제외 등 부록 구역 정책 전반에 영향).
   - 표지(1쪽)의 고정 고지 "연·월·일"은 표지 제외 구역이라 비발화 — 고지 문안(불변규칙 8, 운영자 확정)은 변경 대상 아님.
   - 수정 방향: 차트 구분자를 known 경로와 정합하게 제거/치환 + 부록 골격 문구 재서술("세운과 월운" 등) + 부록 도입부에 구역 마커 규약 반영. 게이트/lint 수정 금지.
2. **quality_clean=False — `internal_meta_label` 1건**
   - 6쪽 frame 골격 "…순위와 시작점은 **이 장에서** 말하지 않습니다"(`rules.py:1013-1015`). 문장 재서술 필요. 인접: wonguk "이 장에는"(`rules.py:1000`)은 현재 패턴 비매치(실측 hit 1건뿐)이나 같은 클래스 — 수정 시 인접 동반 점검.
3. **delivery_quality_clean=False — failures 3건 (운영자 정책 결정 선행 필요)**
   - `premium_pages`(14 < 20) · `premium_text_chars`(4,615 < 10,000) · `missing_usable_ziwei`(자미 마커 0).
   - 삼주 상품은 자미 서술 자체가 금지(불변규칙 8)라 missing_usable_ziwei는 **구조적으로 충족 불가**, 분량도 시간 의존 챕터 제외로 known 프리미엄 하한과 양립 불가 — 골격 문장 수정으로 해결되지 않는다.
   - 필요 결정: 삼주 상품 클래스 전용 delivery 프로파일(분량 하한·자미 요구 재정의) 신설 vs 삼주 콘텐츠 확충/상품 재정의. 게이트 기준 변경이므로 **운영자 승인 + (정상 통과/결함 차단) 양방 회귀 필수** — Codex 단독 수정 불가.
   - 참고(비차단): 반복어 "흐름" 14회·"중심" 11회(>8)는 `domain_term_repetition` warning 전용(FAIL 승격어는 "또렷"뿐), `premium_low_density_pages`는 실주문(has_customer_context) 경로에서 failure로 승격되는 구조 — 현재 low_density_pages=[].

### 근본원인 2층 (왜 라운드19가 "잔존 1건"으로 오판했나)

- 라운드19 리뷰는 E2E 실패를 pytest assertion repr(절단 출력)로만 진단해 첫 실패 축(customer_meta)만 열거했다 — 같은 시점에 style/quality/delivery도 이미 False였다(분량·문구 동일). **재발 방지(리뷰 절차): E2E 게이트 실패 시 verify 전체 False 키 덤프를 표준 진단 절차로 고정**(이번 라운드 진단 프로브 방식). docs/16 QI 기록 추가는 리뷰어 파일 경계 밖 — checkpoint 시 운영자/구현자 몫.
- 신규 매트릭스 회귀는 3개 lint 군만 커버 — verify가 소비하는 문안 lint(`style_lint` 시맨틱·quality `internal_meta_label`)로 확장해야 같은 클래스 재발을 차단한다(비Playwright 가능). 분량/구성(delivery)은 렌더 의존이라 회귀 설계 별도.

### GREEN 실측

| 항목 | 실측 | 판정 |
|---|---|---|
| 전체 pytest | 1 failed / **1032 passed** / 4 skipped / exit 1 — 라운드19 1031 대비 +1(신규 회귀), 기존 passed 감소 0, 실패는 위 E2E 단건뿐 | 부분 |
| golden | 28 passed / exit 0 | ✓ |
| 집중 3파일 | 39 passed + 동일 1 failed | 부분 |
| 정적 | 변경 Python 36(합집합) py_compile exit 0 · Ruff 18건 = rules.py 17 + verify.py 1(라운드19와 동일 구성, 신규 0) · `git diff --check` exit 0 | ✓ |
| 절차 | manifest validate exit 0 · packet/notes/review SHA 핀 일치 · 보류 패킷 `b981a996…5819` 불변 · 경계 스냅샷 50파일 시작 수집(종료 대조는 기록 후) · 리뷰어 제품 코드 무수정 | ✓ |

### 실행한 검증 명령
```
node handoff.mjs validate                                  → HANDOFF_VALID / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q             → 1 failed / 1032 passed / 4 skipped / exit 1 (216.4s)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden   → 28 passed / exit 0
./.venv/Scripts/python.exe -m pytest (집중 3파일) -q        → 39 passed / 1 failed (동일 재현)
./.venv/Scripts/python.exe -m r20_probe (scratchpad, -m)   → 17키 전수 0 / TOTAL_HIT_RULES=0 / 차단측 재현
./.venv/Scripts/python.exe -m r20_diag (scratchpad, -m)    → gate 실패 키 3개 + delivery failures 3건 실측
./.venv/Scripts/python.exe -m ruff check / py_compile (36) → 부채 18(구성 동일·신규 0) / exit 0 · git diff --check → exit 0
known E2E PDF 가운뎃점 분포 대조(PyMuPDF, 읽기 전용)        → known 2건 전 페이지 0 vs 삼주 1·4·13쪽 발화
Get-FileHash(.ps1): 시작 스냅샷 50파일 + 핀 4종 대조 일치
```

### 미검증(정직 보고)
- 라운드19 종료 SHA 스냅샷이 세션 소멸로 부재 — "이번 수정 라운드 변경 = 정확히 rules.py+테스트 1+인계 3종"의 SHA 증명은 불가. 보완 증거(Ruff 부채 구성 동일·lint/게이트 파일 git 무변경·신규 테스트 전문 리뷰·프로브 재현)로 대체했고 Codex 자진 보고와 정합. 라운드 종료 스냅샷의 세션 밖 영속화는 운영자 결정 사항으로 제안.
- 실제 Anthropic API·고객 주문 PDF·실상품 재생성·hrun·hsweep 미실행 — compose 실품질·비용·조판·hsweep K/Z·육안 Z=0 확정 불가. pytest·진단 프로브의 합성 테스트 산출물 외 PDF 생성 0.
- 스코프 밖 변경 2건(라운드18 rules 문구 순화·order_flow enum 정본화)의 "운영자 추가 승인" 주장은 계속 확인 불가 — checkpoint commit 시 운영자 확인.

다음: ① 운영자 — 블로커 3(delivery 프로파일) 정책 결정. ② 결정 후 Codex 수정 패킷(블로커 1·2 골격/차트/부록 마커 + 매트릭스 회귀를 style_lint·quality lint로 확장) → Claude 라운드21 재검증. API·유료 재생성·commit·push 금지 유지.

---
---

# 교차 리뷰 — 2026-07-13 (라운드 19, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `084e04c` 위) 라운드18 블로커 수정분 · 구현자: Codex · 지시문: `handoff/tasks/beta-2-round18-blockers-fix-20260713.md` (+ REVIEW-FEEDBACK 라운드18 절)

## 최종 판정: **수정 요청(changes_requested)** — 블로커 4건 중 B2·B3·B4 완결, B1은 테스트 갱신 자체는 올바르나 복구된 E2E가 라운드18부터 잠복해 있던 제품 결함 1건을 새로 적발. 잔존 블로커 1건만 수정.

수정 라운드 변경 파일 실측(라운드18 종료 스냅샷과 SHA 대조) = 정확히 8파일 + 리뷰어 지시문 패킷 1: `tests/test_p8.py`, `sajugen/render/pdf.py`, `sajugen/content/llm_sections.py`, `sajugen/content/rules.py`, `sajugen/order_flow.py`, 테스트 3파일. REVIEW-FEEDBACK·동결 패킷 2·보류 패킷 SHA 전부 불변 — Codex 자진 보고 목록과 일치.

### 잔존 블로커 (미해결 — Codex 수정 필요)

1. **삼주 wonguk 골격 문장이 기존 AI-meta 게이트와 충돌 — E2E `gate_pass=False`**
   - 실측: `pytest tests/ -q` → **1 failed / 1031 passed / 4 skipped / exit 1**. 실패 = `test_p8.py::test_e2e_unknown_time`, 이번에는 경계 차단이 아니라 `_assert_gate`: `ai_meta_hits = [{rule: guided_structure_walkthrough, page: 4, count: 1}]` → `customer_meta_clean=False`. 집중 재실행에서도 동일 재현(결정론).
   - 원인: `sajugen/content/rules.py:999` wonguk 골격 "…서로 어떤 방향을 보태는지 **함께 읽습니다**"가 `customer_meta_lint.py:31`의 `guided_structure_walkthrough` 패턴(`함께\s*읽습니다`)에 정확히 매치. 이 문장은 라운드18 구현부터 있었으나 당시엔 E2E가 경계 차단으로 먼저 죽어 게이트까지 도달하지 못했고, 빌더 pre-render 벨트(`_customer_policy_lints`)에 customer_meta 계열이 없어 최종 PDF verify에서만 발화한다("유닛 GREEN ≠ 실경로 안전" 클래스). 라운드18 리뷰도 골격 텍스트를 meta 패턴과 전수 대조하지 않아 놓쳤다.
   - 사각 인접 전수 프로브(리뷰어 실측): 삼주 골격 17개 키 전부 × customer_meta_lint 8룰 → 충돌은 **wonguk 1건뿐** (`TOTAL_HIT_RULES=1`). 수정 범위는 문장 1곳으로 특정됨.
   - 수정 방향: (a) rules.py:999 문장을 meta 패턴 비충돌 표현으로 재서술(게이트 완화 금지 — lint 수정이 아니라 골격 수정). (b) **근본원인 2층**: 삼주 골격 전 섹션 × `customer_meta_lint` clean을 고정하는 비Playwright 단위 회귀를 동반 — Codex 환경에서 E2E가 skip이므로 이 회귀 없이는 같은 클래스가 재발한다.

### 라운드18 블로커 처리 실측 (B2·B3·B4 완결, B1 부분)

| 항목 | 실측 | 판정 |
|---|---|---|
| B1 test_p8 갱신 | 비절입일 `2000-01-15` + 레거시 `12:00+unknown_time=True` 정규화 겸증 + 정확 고지 1회·금지 토큰 9종 0 단언 — 테스트 설계는 지시문 사양 충족. 단 위 잔존 블로커로 E2E 자체는 아직 RED | 부분 |
| B2 원국표 배선 | `pdf.py` anchor 단일 index 고정(wonguk→personal_* 폴백→첫 고객 장, 정확 1회) + known은 anchor 없음. 실빌드 테스트로 integrated 삼주 표 1회·고지 1회·時柱 0, content.json 라운드트립 복원 소비, known integrated 표 0 전부 실재·GREEN | ✓ |
| B3 compose 상충 제거 | `_THREE_PILLAR_SYSTEM_REPLACEMENTS` 9쌍 결정론 치환(원문 count!=1이면 import-time RuntimeError — 드리프트 fail-closed). known `_COMPOSE_SYSTEM` 바이트 불변을 SHA-256 `a17f90fb…380a` 핀으로 고정. SDK 경계 캡처 양방 테스트: 삼주 = 중립 시스템+override+cache 블록 구조·금지 긍정 지시 4종 부재·user 근거 축소, known = 블록/user 바이트 동일·override 부재. `_LAYER_WEAVE`(자미 겹쳐 읽기)는 known 가이드 전용으로 삼주 미전달 확인 | ✓ |
| B4 경계 테스트 3건 | 소서 1995-07-07 차단+07-06/08 통과 · three_pillar+시각 접수 ValueError+주문 0 · 레거시 known(mode 키 없음, legacy false 유무 parametrize) KNOWN 복원+최종 발급 통과 — 전부 실재·GREEN | ✓ |
| 스코프 밖 변경(자진 보고 2건) | `rules.py` "추정값" 문구 순화(B1 단언 `추정` 0과 정합에 필요) · `order_flow.py` create_order 정규화 1블록(명시 enum일 때 가짜 legacy boolean 합성 중단 — 양쪽 다 fail-closed 유지, 오류 정밀도만 개선, B4-2 단언에 필요). 변경 자체는 최소·비악화 실측 GREEN. **Codex가 주장한 "운영자 추가 승인"은 리뷰어가 확인 불가 — 운영자 확인 필요** | 플래그 |
| 기준환경 | 전체 **1 failed / 1031 passed / 4 skipped / exit 1**(232.6s) — 라운드18 1022 대비 +9, 기존 감소 0, 실패는 위 잔존 1건뿐. golden **28** · 집중 6파일 **124 passed + 동일 1 failed** | 부분 |
| 정적 | 변경 Python 36(합집합) — 부채 2파일 제외 34 Ruff GREEN, 부채 18건 HEAD 동일 구성(신규 0) · py_compile 36 exit 0 · `git diff --check` exit 0 | ✓ |
| 절차 | packet/notes/review SHA manifest MATCH · 보류 패킷 `b981a996…5819` 불변 · 경계 스냅샷 49파일 시작 수집(종료 대조는 기록 후) · 리뷰어 제품 코드 무수정 | ✓ |

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 1 failed / 1031 passed / 4 skipped / exit 1 (잔존 블로커)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed / exit 0
./.venv/Scripts/python.exe -m pytest (집중 6파일) -q       → 124 passed / 1 failed (동일 재현)
./.venv/Scripts/python.exe -m ruff check / py_compile (36파일) → 신규 0 / exit 0 · git diff --check → exit 0
삼주 골격 17키 × customer_meta_lint 전수 프로브(합성, PII 0) → HIT wonguk guided_structure_walkthrough 1건뿐
Get-FileHash(.ps1): 스냅샷 대조 — 수정 파일 8 + 지시문 1 외 변경 0
```

### 미검증(정직 보고)
- 실제 Anthropic API·고객 주문 PDF·실상품 재생성·hrun·hsweep 미실행 — compose 실품질·prompt cache·비용·조판·hsweep K/Z·육안 Z=0 확정 불가. pytest 합성 테스트 산출물 외 PDF 생성 0.
- 스코프 밖 변경 2건의 "운영자 추가 승인" 주장은 세션 밖 사실이라 확인 불가 — checkpoint commit 결정 시 운영자 확인 필요.

다음: Codex가 잔존 블로커 1건만 수정(rules.py:999 문장 재서술 + 골격×meta lint 비Playwright 회귀) → Claude 라운드20 재검증. 통과 시에만 Codex 신선 read-only 확인 → 운영자 checkpoint commit.

---
---

# 교차 리뷰 — 2026-07-13 (라운드 18, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, base=HEAD `084e04c` 위, tracked 41파일 +1712/-246 + 현 태스크 신규 8파일) · 구현자: Codex · 지시문: `handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md` (생시 미상 삼주 전환·12지지 민감도·출처 게이트)

## 최종 판정: **수정 요청(changes_requested)** — 설계·배선·게이트·문서 정합은 광범위하게 GREEN이나, 기준환경 pytest exit 1(기존 테스트 1건 회귀)을 포함한 블로커 4건. 아래 미해결 항목만 수정.

판정 범위는 CODE_PASS 교차리뷰다. 실제 API·고객 PDF·300dpi 조판·비용·hsweep K/Z·육안 Z=0은 판정 밖(여전히 확정 불가). 전체 pytest에 포함된 합성 PDF 렌더 테스트(test_p8·test_consistency·test_harness 등)가 만드는 **합성 테스트 PDF/HTML 산출은 운영자 승인 예외**이며, 고객 주문 PDF·실상품 pipeline 재생성·API 호출은 0.

### 블로커 (미해결 — Codex 수정 필요)

1. **기준환경 전체 pytest exit 1 — `tests/test_p8.py::test_e2e_unknown_time` FAILED (기존 passed 감소 1)**
   - 실측: `pytest tests/ -q` → **1 failed / 1022 passed / 4 skipped / 207.2s / exit 1**. 수용 기준 §8(exit 0, 기존 passed 감소 0) 위반.
   - 원인: `tests/test_p8.py:78`은 구계약 테스트 — 1995-07-07(**소서 절입일**)을 `unknown_time=True`+정오로 생성하고 `"추정" in text`(구 고지)와 자미 미렌더를 단언한다. 새 계약에서 (a) 절입일이라 `NEEDS_INFO_TIME_BOUNDARY`로 차단되고, (b) 날짜를 바꿔도 `추정` 고지 자체가 제거된 계약이라 단언이 이중으로 무효다. 이 파일은 수정 목록에 없다.
   - Codex 환경에서 미관측된 이유: playwright 계열 32건 skip(995/32) — 이 테스트가 그 안에 있었다. 기준환경(4 skip)에서만 발화.
   - 수정 방향: test_p8을 새 계약으로 갱신(비절입 날짜 + 정확 고지 문자열 + 3열/시주 부재 단언). 부수 효과로 이 실패는 비입춘 절입 차단이 실경로에서 작동함을 실증했다.

2. **integrated_full 삼주 원국표 팬텀 배선 — 3열 표가 실제로 렌더되지 않음 (A-5 소비처 미배선 클래스)**
   - 실측: 원국표 삽입 조건은 `sajugen/render/pdf.py:128` `section.id == "wonguk"` 하나뿐인데, integrated 조립 섹션 ID는 `sajugen/integrated.py:117,256`의 `_copy_section(prefix="personal")`로 전부 `personal_wonguk`이 된다 → 조건이 영구 False.
   - 결과: `_render_integrated`의 `fake_saju.three_pillar` 배선(integrated.py:501), 재렌더용 `three_pillar_chart` 영속·`_three_pillar_from_chart_data` 복원 헬퍼가 전부 **받기만 하고 소비되지 않는다**. integrated_full(삼주 주문의 주력 상품) 고객 PDF에 원국표가 없다 — 패킷 §4·notes "3열 원국표" 주장과 불일치. personal 경로(`wonguk` 비프리픽스)만 표가 들어간다(테스트 실재).
   - 수정 방향: 조건을 raw ID 기준(`removeprefix("personal_")` 등)으로 확장 + integrated 삼주 고객 표면 테스트(3열 표 존재 + 정확 고지 1회 + 時柱 0)를 동반. 게이트 완화 없음.

3. **삼주 compose의 상충 시스템 지시 + override 배선 캡처 테스트 부재 (운영자 교정 4호 렌즈)**
   - 실측: `_COMPOSE_SYSTEM`(sajugen/content/llm_sections.py:46 "사주·자미두수 상담가" 페르소나, :108 "사실 토큰(간지·연도·신살·**궁 이름**)을 챕터당 충분히 호명", :154-157 "자미두수 궁 이야기를 …같은 호흡 안에서 겹쳐")이 삼주 compose에도 그대로 1블록으로 전달되고, 뒤의 `_THREE_PILLAR_SYSTEM_OVERRIDE`(:252)가 이를 금지한다. 금지 사실을 쓰라는 긍정 지시가 남은 채 뒤에서 덮는 구조 — 모델이 궁/자미 표현을 내면 후보 lint가 죽이고 재시도→룰 폴백을 **유도할 수 있다**(fail-closed라 고객 유출은 없으나 품질·비용 방향). 실LLM 미검증이므로 유도 빈도는 확정 불가.
   - 배선 사각: `_compose_system_blocks`의 override 분기 자체를 단언하는 테스트가 0(`grep _THREE_PILLAR_SYSTEM_OVERRIDE tests/` 무매치) — 분기가 사라져도 어떤 테스트도 RED가 되지 않는다. 패킷 §6.8(LLM 캡처 입력 검증)은 report_context prompt까지만 커버.
   - 수정 방향: 삼주 모드에서 자미/궁 긍정 지시가 시스템 표면에 남지 않게 분리(삼주 전용 시스템 블록 또는 조건 조립) + 삼주 compose 전체 system blocks·user payload 캡처 양방 테스트(override 존재·금지 지시 부재·허용 출처만). 게이트 완화 아님.

4. **필수 경계 테스트 누락 3건 (운영자 교정 7호 — 프로브 대체 불가 항목)**
   - (a) **비입춘 월 절입 당일 차단 + 전날·다음날 통과** 테스트 부재 — 현재는 입춘(2000-02-04 차단·02-05 통과)만 고정(test_three_pillar_calc.py:145). 블로커 1의 소서 실패가 실증 증거이나 설계된 회귀로 고정 필요.
   - (b) **`birth_time_mode=three_pillar` + 시각 동시 입력 접수 차단** 테스트 부재 — 코드는 존재(order_flow.create_order "must not include a birth time")하나 `grep` 무매치.
   - (c) **레거시 known 주문(mode 키 없음 + hour/minute 존재) 오분류 방지** 테스트 부재 — `report_birth_time_mode`의 legacy 복원 분기(store/orders.py)를 직접 단언하는 테스트 0. 현재 테스트는 전부 explicit mode 저장본만 사용.

### advisory (비블로커)

- `unknown_time_policy._FORBIDDEN_TEXT_RULES`의 `ziwei_fact` 궁 폐쇄 목록이 12궁 중 7개(명·신·부처·관록·재백·질액·천이)만 커버 — 형제·자녀·노복·전택·복덕·부모궁 단독 언급은 이 규칙 미포착(자미 주성 14종은 factcheck가 전면 차단 실측 확인). 사각 축소 방향의 저비용 확장 후보.
- engine 표면 한정: mode 미지정 + `hour=None, minute=30` 호출 시 three_pillar로 minute을 조용히 무시(접수 경로는 "HH:MM" 원자 파싱이라 발생 불가). 라이브러리 직접 호출 방어는 후속 후보.
- (관찰) 12후보 대표점은 짝수 정각(조자시 기준) — JST_2300 야자시(23시) 변형의 시간간 차이는 스윕 범위 밖이나, docs/03 §1-2 "후보 시각 때문에 연·월·일주가 바뀌는 계산은 허용하지 않는다"는 운영자 결정과 정합(정책 준수).

### GREEN 확인 (실측 근거 — 재작업 불필요 범위)

| 항목 | 실측 | 판정 |
|---|---|---|
| 전제 | HEAD=base `084e04c` · packet/notes/review SHA-256 3건 manifest MATCH(Get-FileHash 재대조) · 보류 패킷 `b981a996…5819` 시작/종료 불변 · 경계 스냅샷 47파일 시작/종료 전수 일치 | ✓ |
| golden / 집중 | **28 passed** · 신규 4파일+핵심 수정 4파일 **176 passed** | ✓ |
| 정적 | 변경 Python 35(tracked 27+untracked 8) — rules.py·verify.py 제외 33파일 Ruff GREEN, 두 파일 18건은 HEAD 추출본과 동일 구성(F541 16·F841 2 — **신규 0**) · py_compile 35 exit 0 · `git diff --check` exit 0 | ✓ |
| 계산·정규화 | `birth_time.py` 단일 enum 정규화+모순 ValueError · `three_pillar.py` 12/12 승격·11/12 억제·digest 순서불변·candidate_count 0/11/13 거부·`NEEDS_INFO_TIME_BOUNDARY`(월건 변화 검사라 입춘 포함 전 절입 커버) · 명시적 `ThreePillarMyeongni`(hour/elements/singang/yongshin/daewoon 필드 부재를 테스트로 고정) | ✓ |
| 자미 미생성 정밀 판정(교정 5호) | 자미 계산 비호출(monkeypatch 테스트) + Section 객체 0·LLM 대상 0·직렬화 ID 0(rule_texts가 drop 후에만 구성). rules의 빈 `ziwei:""` 호환 키는 골격 dict 내부 표면일 뿐 Section·LLM·직렬화에 진입하지 않음 → 패킷 "사후 ID 삭제 불수용"과 **비충돌 판정**(생성 후 삭제가 아니라 생성 대상 제외) | ✓ |
| 주문·레거시 | 접수 시각/모드 모순 4종 ValueError·절입 접수 전 차단(주문 0)·gunghap/ziwei/partner 명시 차단 · three_pillar 주문 hour/minute/unknown_time 비저장+성공 시 잔재 scrub · provenance 계산→콘텐츠→verify 3표면 일치 검증 후에만 DRAFTED · 레거시 정오 잔재/`provenance_missing` 최종 발급 차단(발급 함수 2경로 모두 render_fn 호출 전) · store/content validator 동등성 테스트 | ✓ |
| 게이트 | GATE_KEYS 21→22키(제거·완화 0 — diff+22키 동결 테스트) · cover/toc/본문/appendix 주입 차단+정상 통과 양방 · mode 미전달 우회 차단(notice/provenance 신호로 복원) · known 오탐 0(네 기둥·사주팔자 포함 known 문서 clean 실측 테스트) · finding 5키 고정·PII 0 | ✓ |
| 금지어 문맥 판정(교정 6호) | 차단측 8룰 전부 문맥 패턴(시각값 결합·정오 대입·시주 표현·네 기둥/사주팔자·자미 사실·업셀) + 허용측(일반 `사주`·생활 시각 `오후 3시 산책`·정확 고지) 비오탐 테스트 실재 · 정확 고지 **HTML 1회** 실렌더 단언(personal 경로) | ✓ |
| known 비악화(교정 8호) | golden 28 · known implicit/explicit `model_dump` 동일 테스트 · known 4주/자미/대운 allow_tokens 분기 보존 · known compose 시스템 블록 의미 불변(_COMPOSE_SYSTEM 원문 무변경·override는 삼주에만 삽입) · Report23 additive 필드 기본값으로 직렬화 하위호환 | ✓ |
| 문서-코드 | 00-immutable §8·calc.md·content.md·docs/03 §1-2·07·16(QI-2026-07-12-02 2층 원인)·20(22키 레지스트리)·22(20키 표기 오류도 22로 정정)·23 전부 코드 실동작과 일치 | ✓ |
| 하네스 | hverify_pdf 날짜-only None/None·mode/provenance 전달 테스트 · hsummary 화이트리스트에 hits/count 등재(관측 드롭 없음) | ✓ |

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 1 failed / 1022 passed / 4 skipped / exit 1 (블로커 1)
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed / exit 0
./.venv/Scripts/python.exe -m pytest (신규 4+수정 4파일) -q → 176 passed / exit 0
./.venv/Scripts/python.exe -m ruff check (변경 35 중 부채 2 제외 33) → All checks passed / HEAD 추출 대조 신규 0
./.venv/Scripts/python.exe -m py_compile (35파일) → exit 0 · git diff --check → exit 0
Get-FileHash(.ps1): packet/notes/review vs manifest 3건 MATCH · 보류 패킷 SHA 불변 · 경계 스냅샷 47파일 시작/종료 전수 대조
```

### 미검증(정직 보고)
- 실제 Anthropic API·고객 주문 PDF·실상품 재생성·hrun·hsweep 미실행 — 삼주 compose 실품질·상충 지시의 실제 폴백률·prompt cache·비용·조판·hsweep K/Z·육안 Z=0 확정 불가. pytest가 만든 합성 테스트 PDF/HTML 외 PDF 생성 0.
- 리뷰어는 제품 코드·테스트를 수정하지 않았다(허용 4파일 외 diff 0 — 경계 스냅샷 47파일 SHA 전수 대조).

다음: Codex가 블로커 1~4만 수정(승인 범위 밖 변경 금지) → Claude 재검증. 통과 시에만 Codex 신선 read-only 확인 → 운영자 checkpoint commit.

---
---

# 교차 리뷰 — 2026-07-12 (라운드 17, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `1b46b47` 위, 제품 2파일 + 인계 3파일) · 구현자: Codex · 지시문: `handoff/tasks/beta-1-schedule-boundary-20260712.md` (라운드16 advisory `일정/일정한` 오탐 소수정)

## 최종 판정: **승인(PASS)** — 수용 기준 전 항목 실측 GREEN, 미해결 0. 승인 범위(오탐 1건) 밖 변경 없음.

### 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| 전제 | HEAD `1b46b47` 일치 · packet/notes/review SHA-256 3건 manifest MATCH · base_commit ancestor 확인 · 제품 diff = delivery_quality.py(+3/-1)·test_register_advice_gate.py(+29)뿐 | ✓ |
| pytest | **949 passed / 4 skipped / exit 0**(195.9s) — 라운드16 기준선 941/4 + 신규 8, 감소 0. 산술 예상과 일치. **새 기준선 = 949/4** | ✓ |
| golden / 집중 | 28 passed / 집중 3파일(register_advice·tone_spec·skeleton_matrix) 70 passed | ✓ |
| 정적 | 변경 2파일 Ruff `All checks passed`(exit 0) · py_compile exit 0 · `git diff --check` exit 0 | ✓ |
| 정규식 경계 | `일정(?!한|하게|하지)` 직접 프로브 — 차단측 5건(시험/채용 일정·접수 일정·일정을·명사+조사 `일정하고`) + 인접 `일정 한번` 전부 hit, `advice_terms`에 고정 토큰 `일정` 실제 포함(타 규칙 의존 없음). 허용측 3건(일정한 속도·일정하게 유지·일정하지 않은) 전부 0 hit | ✓ |
| 회귀 무손상 | 기존 매트릭스 프로브 — 연령·요건 / 마감·접수·제출 결합 차단 유지, 간지·세운 연도 비오탐 유지. 게이트 키·finding 구조·호출부·타 패턴 diff 0 | ✓ |
| 테스트 양방성 | 신규 8건 = 차단 5 + 허용 3 parametrize, 차단측은 `일정 in advice_terms` 단언으로 해당 패턴 발화를 직접 고정 | ✓ |

### 관찰 (비블로커)
- **인접 활용형 잔존**: `일정하다`·`일정해서`는 여전히 hit(프로브 실측). 패킷 §1이 승인 스코프를 세 활용형(`일정한/일정하게/일정하지`)으로 명시했으므로 스코프 준수이며, 방향은 fail-closed(LLM 후보 폴백)다. 실측(holdout/실런)에서 잔존 오탐이 관측되면 그때 동일 방식으로 확장.
- **절차 이탈 1건(자진 보고)**: 구현 세션 초기 broad `rg`가 비대상 `sajugen/render/out/**`까지 1회 매치(인용·전재·수정·재열람 0, 이후 탐색 제한). 라운드 10·11과 같은 클래스 — 이번 패킷 §0에 ignored 제외 글롭 문구가 누락돼 재발한 것으로, 이후 Codex 패킷 0절에 `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'` 문구를 필수 포함해야 한다. docs/16 기록 여부 = 운영자 결정.

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 949 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed / exit 0
./.venv/Scripts/python.exe -m pytest (집중 3파일) -q       → 70 passed / exit 0
./.venv/Scripts/python.exe -m ruff check / py_compile (변경 2파일) → exit 0 / exit 0 · git diff --check → exit 0
경계 프로브 14건(차단 6/허용 3/인접 2/기존 매트릭스 3, 합성·PII 0) → 전부 기대 일치
Get-FileHash: packet/notes/review vs manifest → 3건 MATCH · read-only 3파일 시작/종료 스냅샷 대조
```

### 미검증(정직 보고)
- API·PDF·hsweep·유료 재생성·hrun 미실행 — replacement 문안·prompt cache·비용·조판·hsweep K/Z·육안 Z=0은 판정 범위 밖, 여전히 확정 불가.
- 리뷰어는 제품 코드·테스트를 수정하지 않았다(read-only 3파일 SHA 스냅샷 대조).

다음: 운영자 checkpoint commit 결정(untracked packet 1개 경로 명시 추가). 이후 별도 과금 승인 시에만 Phase C replacement 1회.

---
---

# 교차 리뷰 — 2026-07-12 (라운드 16, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `5ebd3b6` 위, 54 수정 + 5 신규) · 구현자: Codex · 지시문: `handoff/tasks/beta-1-register-harness-20260712.md` (베타 1호 Z>0 문체·조언·가독성·hsweep/비용 개선)

## 최종 판정: **승인(PASS — CODE_PASS 교차리뷰)** — 수용 기준 A~D 전 항목 diff 근거 확인, 기준환경 941/4 GREEN, 미해결 블로커 0. advisory 1건(비블로커, 아래).

판정 범위는 패킷 §0대로 CODE_PASS만이다. 새 replacement PDF 품질·실비용 절감·운영자 Z=0은 이번 판정에 포함하지 않으며 여전히 **확정 불가**다.

### 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| 전제 | HEAD `5ebd3b6` 일치 · packet/notes/review SHA-256 3건 manifest와 MATCH · `git status` 59건 = notes 목록과 정합 · calc/input diff 0(tracked+`--untracked-files=all` 양쪽) | ✓ |
| pytest | **941 passed / 4 skipped / exit 0**(210.6s) — 기존 기준선 831/4 + 신규 110, 감소 0. 산술 예상 941/4와 일치. **새 기준선 = 941/4** | ✓ |
| golden | 28 passed / exit 0 | ✓ |
| Ruff | 변경+신규 .py 43개(untracked 4개 포함) 검사 → 19건 전부 rules.py(17)/render/pdf.py(1)/render/verify.py(1). HEAD 추출본 동일 3파일 재검 = 동일 19건(F541 16·F841 2·F401 1) → **신규 위반 0 확정**. 나머지 20개 소스 GREEN | ✓ |
| py_compile / diff-check | 43파일 exit 0 / `git diff --check` exit 0 | ✓ |
| A 문체 register | `REGISTER_RULES`/`register_lint()` 외래어와 분리 신설(client_tone_lint.py) — 하드 8룰(결과지·참고·구간·준비 구간·정보 수집·커트라인·큰 그림·그림을 잡다 활용형 `잡으세요/잡으십시오` 포함)+warning 6종. finding = rule/token/count/page/severity 5키 고정, 원문 0. verify.py GATE_KEYS 21키에 `client_register_clean` 등재·전 페이지(표지·목차·본문·부록) 검사. builder `_customer_policy_lints` 4지점(룰 골격 rule_viol·최초 후보·재시도·최종 섹션 재집계) 배선, `GuardReport.customer_policy_lint_total>0 → clean=False`(pre-render false-PASS 폐쇄, sections_schema additive 하위호환). gunghap(폴백 위반 시 RuntimeError 빌드 중단)·relationship delivery_gate·followup answer_gate·hverify_pdf/hsummary 동일 판정. 룰 골격의 참고/결과지/구간/큰 그림 계열 전량 대체어 치환 실측 | ✓ |
| B 외부 조언·직답 | `external_domain_advice_lint` = 같은 문장 내 도메인(시험·직업·영어·자격증·원서·서류)+사실/절차 결합만 차단, 문장 경계 보존(줄바꿈=경계)·PDF block 단위 segments API(페이지/블록 경계 비월경). 프로브 실측: 결합 지시 2건 차단 / 간지·세운 연도 및 사주 근거 완급·방향 4건 통과 / 순수 미러링 2건 허용(fullmatch만, 후행 조언 비은닉). consult action에서 먼저/확인/말 제거+사주 근거 행동어로 교체, `work_career` 축 신설(독립 근거 요구), timing `월` substring → `N월` 정규식(월급/세월 오탐 제거) | ✓ |
| C ReportContext·비용 | report_context.py = 화이트리스트 ID 전용 frozen dataclass, `__post_init__`이 비정규 모듈·카테고리·소유권·용어 정책 전부 fail-closed 거부 — 이름·생년월일·질문 원문·이전 산문 필드 자체가 없음. 12개 compose가 동일 객체/직렬화 prefix 공유(`_compose_system_blocks` explicit 5m cache), 호출별 user에 `[현재 장 ID]`. glossary owner는 `resolve_glossary_owner_by_concept`로 활성 장 결정론 재배정(ziwei 상품 테스트 고정). cache 판정 = `ComposeResult.cache_observed is True`만 병렬 허용(문자열/False/None/예외 → warm 1회 후 룰 폴백 = fail-closed). usage는 ContextVar run 격리(`usage_run`/`isolated_run`/`bind_current`)+role/model/section/stop allowlist(모델은 설정 등재값+unknown만)+ASCII JSON detail, order_flow가 주문 메타에 run 단위 저장. config `compose=claude-sonnet-4-6` 불변 | ✓ |
| D hsweep v2 | raw 후보 opaque `c%04d` ID로 원형 보존, ranker = 비파괴 advisory(출력 길이=입력 길이, disposition만), 후보 전수 batch judge(normal/reverse 2콜). 단계별 stage_status(malformed_output/invalid_page_evidence/complete_empty 구분)+stage_trace+usage. 운영자 `review_status=complete`+파이프라인 완전+후보 전수 라벨 전에는 K/Z/Z_new/Z_known 전부 null, v1 confirmed는 `judge_confirmed`로만 이관(K 자동 이관 없음, migration 명시). CLI는 `--name/--birth` 등 원시 PII 인자 거부, manifest는 repo 내부·비symlink·`git check-ignore` 실측 통과+엄격 스키마만. 한국어 생년·시각은 manifest civils 기반 `masking.mask_birth_in_text` 정밀 마스킹. review subcommand는 canonical 재구성만 출력(rationale·임의 필드 비보존), temp `.hsweep-review-*.json`은 ignored 확인+전 실패 경로 finally 제거 | ✓ |
| 문서↔코드 계약 | docs/14 §7 tone-contract-v1 JSON ↔ REGISTER_RULES/외부조언 고정어/용어 12개군·설명·소유 맵 양방 테스트(test_tone_spec_contract.py). docs/20 레지스트리 21키 갱신+열린 품질 차원 책임표. 렌즈 프롬프트 2종에 register/외부조언 층+novelty 제안 필드(운영자 확정값 아님 명시) | ✓ |
| 테스트 양방성 | 신규 3파일 33 테스트 표본 검토 — cover·toc·본문·appendix 합성 주입 차단측+warning 비차단·정상 통과측, builder 재시도 수용/지속 위반 폴백/골격 위반 aggregate unclean, cache 실패 모드별 폴백, hsweep canonical/temp 실패 경로까지 양방 고정 | ✓ |

### advisory (비블로커, 다음 라운드 후보)
- **`일정` 사실 패턴이 형용사 `일정한`에 오탐**: 프로브 실측 `"직장 생활에서 일정한 속도를 유지하는 편이 좋습니다"` → external_domain_advice 1건. 룰 골격·정적 문안은 전수 무저촉(941 GREEN + grep 실측)이라 납품 차단·빌드 실패는 없고, 영향은 LLM 후보의 조용한 룰 폴백(품질·비용) 방향 = fail-closed. 다만 compose 프롬프트가 "속도" 계열 표현을 권장하므로 "일정한 속도/리듬" 산문에서 폴백률이 오를 수 있다. 개선 후보: `일정(?!한|하)` 등 활용형 예외 또는 holdout 실측 후 조정. 수정은 게이트 완화가 아닌 오탐 축소 방향으로만, 양방 테스트 동반(작업 규율 3).

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 941 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed / exit 0
./.venv/Scripts/python.exe -m ruff check (변경+신규 43파일) → 19건 = HEAD 부채 3파일과 동일 구성(신규 0)
./.venv/Scripts/python.exe -m py_compile (43파일)          → exit 0 · git diff --check → exit 0
외부조언 경계 프로브 8건(합성, PII 0)                       → 차단 2/통과 4/미러 2 전부 기대 일치 + 오탐 1건 발견(advisory)
Get-FileHash SHA-256: packet/notes/review vs manifest      → 3건 MATCH · read-only 56파일 시작/종료 스냅샷 대조
```

### 미검증(정직 보고)
- 실제 Anthropic API·PDF 재생성·hrun 미실행 → prompt cache 실효·실비용 절감·새 Sonnet 문안 품질·조판·hsweep K/Z·운영자 육안 Z=0 전부 확정 불가.
- 리뷰어는 제품 코드·테스트를 수정하지 않았다(허용 4파일 외 diff 0, SHA 스냅샷 대조).

다음: 운영자 checkpoint commit 결정(신규 필수 5파일 경로 명시 추가 — `git commit -am` 금지, 패킷 §3). 이후 별도 과금 승인 시에만 replacement 주문 1회 → 표준 게이트 → hsweep → 육안 Z 재측정.

---
---

# 교차 리뷰 — 2026-07-11 (라운드 15, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `81ebf3d` 위) · 구현자: Codex · 지시문: `handoff/tasks/audit-a1-mutation-hardening-20260711.md` (감사 A-1, 테스트 전용)

## 최종 판정: **승인(PASS)** — 감사 생존 변이 M1·단일점 M3의 차단측 배치 완료, 변이 재검으로 격추 실증. 절차 이탈 0.

### 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| 범위 | `tests/test_render_verify.py` +91만. **제품 코드 diff 0**(`git diff --name-only -- sajugen/render/` 출력 없음) | ✓ |
| pytest | **831 passed / 4 skipped / exit 0**(기준선 829/4 + 신규 2, 감소 0, 골든 28 포함). Ruff GREEN | ✓ |
| M1 차단측 | fitz 정밀 합성 PDF로 임계 양방(하한-1 차단/경계 통과), `MIN_TEXT_CHARS` 상수 참조 + `max(1,…)`로 0-무력화 변이가 반드시 단언 실패하는 설계. 다른 게이트 키 비단언(과단언 회피) 명시 | ✓ |
| M3 이중화 | 실렌더 PDF + 비선택 모듈 유입 주입 → `delivery_quality_clean`·`gate_pass`·`unexpected_module_sections` 전용 단언 — 단일 감지점 의존 해소 | ✓ |
| **변이 재검(리뷰어 직접 재실행)** | M1 변이(1500→0) 주입 → **1 failed**(신규 테스트 격추) / M3 변이(clean→True) 주입 → **1 failed**. 각각 `git restore` 원복·제품 diff 0 재확인 | ✓ |
| 도크스트링 | 검증/비검증 범위 명시(B-4) + 감사 근거 인용 | ✓ |

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q          → 831 passed / 4 skipped / exit 0
변이 M1·M3 주입 → pytest test_render_verify.py → 각 1 failed → git restore 원복
./.venv/Scripts/python.exe -m ruff check (테스트 1파일)  → All checks passed
```

감사 2026-07 후속 중 코드 몫(A-1) 종결. 잔여 = A-2(55파일 정리)·A-3(hsweep 파일럿) 운영자 액션, A-4 차기 감사.

---
---

# 교차 리뷰 — 2026-07-11 (라운드 14, 리뷰어: Claude 신선 컨텍스트)

대상: 워킹트리(미커밋, HEAD `6105ed9` 위) · 구현자: Codex · 지시문: `handoff/tasks/q7-given-guard-20260711.md` v2 (동명 given 커플 접수 차단)

## 최종 판정: **승인(PASS)** — v2 수용기준 전 항목 GREEN, 미해결 0, 절차 이탈 0. **Q7 알려진 잔여 0으로 완결.**

패킷 이력: v1 발주 → Codex 정지 보고(외자 given_name 반환 실태 — **타당, 4/4 선례 유지**) → 리뷰어 실측(게이트 스펙도 동일 함수 사용 = 외자 쌍은 충돌 자체가 없음)으로 v1의 외자 차단 요구를 과잉으로 폐기, v2 정정(술어 = given_name 출력 동등성) 후 재발주.

### 실측
| 항목 | 실측 | 판정 |
|---|---|---|
| 범위 | 수정 = `order_flow.py` +21(차단 1지점 + import) / `tests/test_orders.py` +121. client_tone_lint 비수정(재사용만), 그 외 diff 0 | ✓ |
| pytest | **829 passed / 4 skipped / exit 0** (기준선 820/4 + 신규 9 완전 일치, 감소 0). golden 28. Ruff GREEN | ✓ |
| 구현 | 술어 = strip 후 `given_name(name) == given_name(partner_name)`, 정규화·DB 개설 전 차단, 메시지 원인 안내형·이름 원문 0(프로브 확인) | ✓ |
| 경계표 v2 | 차단 5(3자 동given·완전 동명·공백·2자 완전 동명·교차 민준/김민준) + 통과 4(**외자 상이 성 김민/이민 정상 접수** — v2 핵심 경계·일반 상이·1인·기존 상품) 전부 테스트 고정 | ✓ |
| 실경로 프로브 | 충돌 쌍 차단(이름 비전재) + 외자 상이 성 쌍 정상 접수 실측 | ✓ |

### 실행한 검증 명령
```
./.venv/Scripts/python.exe -m pytest tests/ -q            → 829 passed / 4 skipped / exit 0
./.venv/Scripts/python.exe -m pytest tests/ -q -k golden  → 28 passed
./.venv/Scripts/python.exe -m ruff check (수정 2파일)      → All checks passed
실경로 프로브(차단·외자 통과)                              → 정합
```

---
---

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

### ③-정정 (2026-07-11 발주 준비 실측 — R13-1 재판정: 코드 결함 아님, 리뷰어 프로브 입력 엣지)
후속 실측으로 아래 ③의 판정을 **정정**한다. 잔존 문형 추출 결과 위반이 전부 "합성 씨" — 프로브의 두 합성 인물(김합성/이합성)의 **성 제외 이름(given)이 동일**해 호칭 변환(`gunghap.py:583` 기존 로직)이 수신자/상대를 구분할 수 없는 입력이었다. **given이 다른 공인 합성 쌍(김민준/이서연)으로 재실렌더 → 무LLM N=5 gate_pass=True, 35쪽, role/honorific/identity 전부 clean, dq_failures 0.** LLM-on FAIL·identity_role·저밀도 실패도 같은 입력의 산물. 잔여 이슈(좁아짐): **동명 given 커플 주문은 호칭 구분 불가로 게이트가 발급 차단**(fail-closed — 유출 위험 0, 단 그런 주문은 처리 불가) — 접수 시점 차단 추가 여부는 운영자 결정. 원판정(아래)은 이력 보존용으로 유지.

### ③ 발견 R13-1 (비블로커 — 4단계 diff 밖, 기존 경로): 무LLM 2인 관계 문안의 수신자 '씨' 호칭 **[③-정정으로 대체됨]**
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
