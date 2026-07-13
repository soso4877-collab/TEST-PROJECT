# TASK_PACKET — 라운드20 잔존 블로커 3건 수정 (삼주 E2E 게이트 3키: style·quality·delivery)

> 개정 v2 (2026-07-13): Codex 정지 보고(§4 계약 모순 — 정당)를 반영해 §4의 style/quality 매트릭스
> 적용 층을 raw 골격에서 **빌더 final_text 층**으로 교정. 근거 실측(Claude 기준환경, no-LLM 빌더):
> raw 골격의 가운뎃점(cover 고지·intro/wonguk `연주·월주·일주`)은 빌더 표시 직전 정규화가 제거해
> final_text 층에서는 **cover 포함 전 섹션 가운뎃점 0**이며, 발화는 정확히 블로커 2곳뿐
> (frame quality 1건 · appendix_terms style 1건). 고지·골격 소개문·lint는 그대로 두면 된다.
> §4 외 다른 절은 v1과 동일.

- task_id: `beta-2-unknown-time-three-pillar-20260712` (동일 태스크의 수정 라운드 — 새 태스크 아님)
- fix_packet: `handoff/tasks/beta-2-round20-blockers-fix-20260713.md` (이 문서)
- 동결 문서(수정 금지): 원 패킷 `beta-2-unknown-time-three-pillar-20260712.md`(SHA-256 `20ee5efb…04ba`),
  라운드18 수정 패킷 `beta-2-round18-blockers-fix-20260713.md`(`65b98207…54a0`),
  라운드19 수정 패킷 `beta-2-round19-blocker-fix-20260713.md`(`0912acf9…b752`),
  보류 패킷 `beta-1-hverify-module-contract-20260712.md`(`b981a996…5819`)
- base_commit: `084e04c95fc3d72757771b0a39d3dd7b85a2470e` + **미커밋 워킹트리(라운드20 리뷰 대상 그대로)**
- 구현자: Codex / 재검증: Claude 신선 컨텍스트 (라운드21)
- 판정 정본: `REVIEW-FEEDBACK.md` 라운드20 절 (2026-07-13, changes_requested)

## 상태(전제) — 라운드20 실측 (2026-07-13, Claude 기준환경)

- 라운드19 잔존 수정(wonguk `살핍니다` 치환 + 골격×meta/loanword/raw_calc 회귀)은 **사양 충족 완결**
  — 이 범위 재작업·리팩터 금지. customer_meta 충돌은 해소됐다(`customer_meta_clean=True` 실측).
- 잔존 = E2E `test_p8.py::test_e2e_unknown_time`이 **별개 게이트 3키로 gate_pass=False**
  (라운드19 리뷰의 열거 누락 — pytest repr 절단만 보고 첫 실패 축만 봤다). verify 전체 덤프 실측:
  1. `style_clean=False` — ai_signature_punctuation(가운뎃점) 4쪽·13쪽 각 1건.
  2. `quality_clean=False` — internal_meta_label `이 장에서` 1건(6쪽 frame).
  3. `delivery_quality_clean=False` — failures 3: `premium_pages`(14<20)·`premium_text_chars`(4,615<10,000)·
     `missing_usable_ziwei`(자미 마커 0 — 삼주는 자미 서술 금지라 구조적 충족 불가).
- 기준환경 전체 pytest = **1 failed / 1032 passed / 4 skipped / exit 1**. golden 28,
  Ruff 부채 = rules.py 17 + verify.py 1(신규 0), py_compile 36 exit 0, diff-check 0.
- 대조 실측: known E2E PDF 2건(e2e_pipeline·e2e_p8_solar)은 **전 페이지 가운뎃점 0** — known 리포트
  본문에는 가운뎃점 차트가 아예 없다(`manse_table`은 본문 미주입). 삼주 3열 표가 신규 도입한 결함.
- 운영자 결정(2026-07-13, "권장사항대로"): 블로커 3은 **삼주 전용 delivery 프로파일 신설**로 확정.
  이 패킷이 그 사안별 구현 승인이다(§3). 게이트 완화가 아니라 상품 클래스 정합 분기이며,
  known 경로의 기존 기준은 바이트 하나도 변하지 않아야 한다(비악화).
- 스코프 밖 변경 2건(라운드18 rules 문구 순화·order_flow enum 정본화)의 "운영자 추가 승인" 플래그는
  계속 유지 — 이번 라운드에서 건드리지 않는다.
- manifest = `changes_requested / next_actor=codex` (validate exit 0).

## 0. 역할·금지 경계 (승인 범위)

- 이 패킷은 운영자가 승인한 잔존 블로커 3건 수정에 한정한 사안별 구현 승인이다. 그 밖의 제품 변경 금지.
- 수정 허용 파일:
  - `sajugen/render/charts.py` — §1-A의 `three_pillar_table` 내부 표기만 (`manse_table`·자미 명반 불가침)
  - `sajugen/content/rules.py` — §1-B 부록 골격·§2 frame 문장만 (다른 골격/known 경로 문구 변경 금지)
  - `sajugen/content/delivery_quality.py` — §3의 삼주 프로파일 분기만
  - `sajugen/render/verify.py` — §3의 `birth_time_mode` 전달 배선 1곳만
    (GATE_KEYS 키 집합·순서 불변, 기존 기준 하향·키 제거·완화 절대 금지 — `test_gate_keys_frozen` 무수정)
  - 테스트: `tests/test_unknown_time_provenance_gate.py`(§4 매트릭스 확장),
    `tests/test_delivery_quality.py`(§3 양방), 필요 시 신규 테스트 파일 1개
  - `docs/16-quality-incident-ledger.md` — §5 QI 기록 1건 추가(기존 항목 수정 금지)
  - 인계 3종(`implementation-notes.md`, `sajugen/STATE.md`, manifest는 handoff.mjs 경유)
- **lint/게이트 완화 금지**: `style_lint.py`·`quality_lint.py`·`customer_meta_lint.py`·`client_tone_lint.py`
  수정 금지. verify의 `_APPENDIX_MARK`·구역 분리 로직 수정 금지(부록이 마커를 쓰도록 골격을 고치는
  것이지, 마커를 부록에 맞추는 것이 아니다). `THREE_PILLAR_NOTICE` 문안 변경 금지(운영자 확정,
  표지 전용이라 게이트 비발화 — 실측 확인됨).
- `REVIEW-FEEDBACK.md`는 리뷰어 소유 — 수정 금지.
- 상시 금지(변경 없음): Anthropic API 등 LLM 호출, 고객/실상품 PDF 재생성, hsweep, hrun,
  git commit, push, main 전진, APPROVED/발송, 고객 데이터·`harness/profiles/local/**`·`.env`·
  ignored 산출물 접근. 합성 입력만, PII 0.
  **예외: pytest 실행이 만드는 합성 테스트 PDF/HTML은 허용.**
- 검색 시 반드시 다음 글롭 적용:
  `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`
- 모든 Python 실행은 `.\.venv\Scripts\python.exe -m ...` 형식만.

## 1. 블로커 1 — style_clean (가운뎃점 2곳)

### 1-A. 삼주 명식표 `charts.py:317·321`
- `three_pillar_table`이 지장간(`"·".join(pillar.hide_gan)`)·지지십성(`"·".join(pillar.shishen_zhi)`)을
  가운뎃점으로 나열 → 원국 장(고객 본문 페이지)에 · 8개 노출 → `style_lint` r"·" 즉시 위반.
- 수정: 두 join의 구분자를 가운뎃점이 아닌 표기로(권장 = 공백 `" "` — 셀 폭이 좁고 한자 나열이라
  쉼표보다 표 관례에 맞다. 최종 표기는 구현자 재량이되 `·`·`—`·`–`·화살표·불릿 등
  `style_lint` 차단 문자는 전부 불가). `three_pillar_table` 함수 밖(특히 `manse_table` 242·246행)은
  본문 미주입 상태를 건드리지 않기 위해 수정 금지.
- 수용 기준: `charts.three_pillar_table(...)` 반환 문자열에 `·` 0 (단위 단언), 삼주 E2E PDF
  **표지 제외 전 페이지 가운뎃점 0**(표지 2개는 고정 고지 문안 — 게이트 비발화, 변경 금지).

### 1-B. 삼주 부록 골격 `rules.py:1081-1089` (이중 결함)
- (i) `"세운·월운:"`(1088행)의 가운뎃점 제거 — 권장 `"세운과 월운:"`.
- (ii) 삼주 부록에 verify 부록 구역 마커(`verify.py:117 _APPENDIX_MARK = "본문에 나온"`)가 없어
  부록 제외가 미적용된다. known 부록 도입부(`rules.py:1791` "본문에 나온 전문 용어를 한곳에 모아
  쉬운 말로 풀었습니다.")와 같은 규약으로, 삼주 부록 첫머리("용어 풀이\n" 다음)에 "본문에 나온"을
  포함한 도입 문장을 1개 추가한다. 문장은 삼주 금지 토큰(시주·자미·사주팔자·추정 등)과
  기존 lint 전부에 비충돌이어야 한다(§4 매트릭스가 판정).
- 수용 기준: 삼주 E2E verify에서 13쪽(부록)이 body 스캔에서 제외되고 style hit 0.

## 2. 블로커 2 — quality_clean (internal_meta_label 1곳)

- `rules.py:1013-1015` frame 골격 "…순위와 시작점은 **이 장에서** 말하지 않습니다"가
  `quality_lint._INTERNAL_META_RX`의 `이\s*장\s*에서`에 매치.
- 수정: 문장 1곳 재서술 — 권장 "…순위와 시작점은 이번 풀이에서 다루지 않습니다"
  (의미 보존: 시간 의존 정보를 다루지 않는다는 관법 서술 유지). 인접 지뢰(선택 표현이 피해야 할 것):
  - `이 장에서`(이번 결함)·`이 풀이는/이 풀이에서(는)`(_CUSTOMER_FRAMING_RX)·`근거 자료`·`프롬프트`·
    `폴백`·`LLM`·`API` 등 `_INTERNAL_META_RX` 전부
  - customer_meta 8룰(`~보겠습니다`·`함께 읽습니다`·`차례로/순서대로 확인` 등 — 라운드19 목록)
  - 사각 인접: wonguk `rules.py:1000` "따라서 **이 장에는** …"은 현재 패턴 비매치(실측 hit 1건뿐)이나
    같은 클래스 — frame 수정 시 이 문장도 같은 재서술 원칙으로 함께 정리할지 §4 매트릭스 결과로
    판단(매트릭스 GREEN이면 유지 가능, RED면 함께 수정).
- 수용 기준: §4 매트릭스에서 frame 포함 골격 전 키 quality_lint clean + E2E quality_clean=True.

## 3. 블로커 3 — delivery 삼주 전용 프로파일 (운영자 승인 완료, 게이트 비악화 필수)

- 결정 사항(운영자 2026-07-13): 삼주 상품 클래스 전용 delivery 기준 신설. 승인 범위:
  1. `delivery_quality.analyze(...)`에 `birth_time_mode: str | None = None` 파라미터 추가
     (기본 None = 기존 동작 그대로 — known/궁합/후속 경로 **바이트 동일 비악화**).
  2. `verify.py`의 analyze 호출(708행 부근) 1곳에 이미 보유한 `birth_time_mode`를 전달(배선).
     그 외 verify 변경 금지.
  3. three_pillar일 때 분기:
     - 분량 하한: `MIN_THREE_PILLAR_PAGES = 12`, `MIN_THREE_PILLAR_TEXT_CHARS = 3500`
       (근거: 실측 14쪽/4,615자 + 정상 변동(챕터 드롭·문형 변주) 여유. 목적은 통이미지·빈 문서·
       챕터 소실 차단이지 분량 벤치마크가 아니다. **이 수치 자체가 운영자 승인 항목** — 구현 후
       notes에 실측 대비 여유율을 수치로 남긴다.)
     - `missing_usable_ziwei` 검사 면제(삼주는 자미 서술 자체가 불변규칙 8로 금지 — 요구가 모순).
       다른 failures(보장 표현·external advice·반복 FAIL어 등)는 전부 유지.
  4. **파라미터를 만들면 소비처 배선과 분기 테스트까지가 한 단위다**(방법론 A5, 팬텀 파트너 교훈).
- 양방 회귀(같은 커밋, `tests/test_delivery_quality.py`):
  - 통과측: three_pillar 모드 + 삼주 실측 규모(14쪽/4,600자급 합성 텍스트) → `clean=True`.
  - 차단측: three_pillar 모드 + 하한 미달(예: 8쪽 또는 2,000자) → `premium_pages`/`premium_text_chars`
    failure 유지 증명. three_pillar 모드 + 보장 표현 합성 → `absolute_guarantee` 여전히 차단.
  - 비악화측: known(모드 None/`known`) 기존 테스트 전부 무수정 GREEN + `missing_usable_ziwei`가
    known 경로에서 여전히 작동하는 단언 1건.
- 수용 기준: 삼주 E2E `delivery_quality_clean=True`, known 계열 delivery 테스트 무수정 GREEN.

## 4. 동반 회귀 — 매트릭스를 verify 소비 lint로 확장 (근본원인 2층) [v2 교정]

- 층 구분이 핵심이다(v1의 계약 모순 원인): raw 골격(`rules.build_all`)에는 빌더가 아직 정규화하지
  않은 가운뎃점(cover 고지·intro/wonguk `연주·월주·일주`)이 정당하게 남아 있다. style/quality
  단언은 **verify가 실제로 보는 텍스트에 가장 가까운 비Playwright 층 = 빌더 final_text**에 건다.
- (a) 기존 raw 골격 매트릭스(전 키 × customer_meta/loanword/raw_calc)는 **그대로 유지**(이미 GREEN,
  수정 금지).
- (b) 신규(같은 테스트 파일): `builder.build_report(saju, use_llm=False, ref_year=…,
  birth_time_mode="three_pillar", product="integrated_full")`의 **전 섹션 final_text**에 대해
  `style_lint.lint(text) == []`와 `quality_lint.lint(text) == []`를 단언한다(섹션 제외 없음 —
  기준환경 실측: §1-B·§2 수정 전 발화는 frame quality 1건·appendix_terms style 1건뿐이고,
  cover 포함 나머지 전 섹션은 이미 0. 수정 후 전 섹션 0이 성립한다).
  - 만약 위 실측과 달리 다른 섹션이 스코프 밖 사유로 RED면 **lint를 건드리지 말고 즉시 정지·보고**
    (스코프 확장은 운영자 결정).
- (c) 차단측(양방): 수정 전 문장 2건(`이 장에서 말하지 않습니다` 합성 문자열 → internal_meta_label,
  `세운·월운` 합성 문자열 → 가운뎃점)이 각각 실제로 잡히는 단언을 둔다.
- (d) 렌더 층: `charts.three_pillar_table` 반환값 `·` 0 단언(§1-A) — Playwright 불필요.
- 도크스트링에 "무엇을 검증하고(빌더 final_text×최종 lint 충돌·차트 표기) 무엇을 검증하지
  않는지(LLM 후보·조판·페이지 분량·render 주입 텍스트)"와 이번 실사고(라운드20 게이트 3키),
  층 구분 사유(raw 골격의 가운뎃점은 빌더 정규화로 제거됨)를 근거로 남긴다.
- 분량(delivery)은 렌더 의존이라 이 매트릭스로 못 잡는다 — §3 양방 회귀와 E2E가 담당(분리 명시).
  표지 render 주입 고지(연·월·일)는 verify 표지 제외 구역이라 판정 밖 — E2E가 최종 심판.

## 5. docs/16 QI 기록 (근본원인 2층 — 감지 시스템)

- 항목 1건 추가: 증상(삼주 E2E gate 3키 RED가 2라운드 잠복) / 원인 2층(① 삼주 신규 골격·차트가
  verify 전용 lint·구역 규약과 미대조 ② 라운드19 리뷰가 pytest repr 절단만 보고 블로커를 과소 열거) /
  재발 방지(① §4 매트릭스 확장 ② 리뷰 절차: E2E 게이트 실패 시 verify 전체 False 키 덤프 표준화 —
  교차리뷰 규약에 이미 반영됨). PII 0, 익명 메타만.

## 6. 검증·완료 기준 (YOU MUST — 증거 없는 완료 주장 금지)

```
.\.venv\Scripts\python.exe -m pytest tests\ -q
.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
.\.venv\Scripts\python.exe -m pytest tests\test_p8.py tests\test_unknown_time_provenance_gate.py tests\test_delivery_quality.py tests\test_three_pillar_calc.py -q
```
- Codex 환경 기준: 전체 exit 0 + 시작치(1005 passed / 32 skipped) 대비 기존 passed 감소 0 + 신규 증가.
  golden 28 유지. test_p8 E2E는 로컬 skip이면 그 사실을 notes에 명시(실렌더 판정은 Claude 라운드21
  기준환경에 위임 — skip을 통과로 보고하지 않는다).
- 변경 Python(diff+untracked 합집합) Ruff·py_compile GREEN(기존 부채 rules.py 17·verify.py 1 외
  신규 0 — 부채 구성이 바뀌면 수치로 보고), `git diff --check` exit 0.
- calc/·input/ 무변경 확인(diff + `git status --short --untracked-files=all -- sajugen/calc sajugen/input`
  양쪽 0) — 이 패킷은 계산 코드를 건드리지 않는다.
- 완료 시: `implementation-notes.md`·`sajugen/STATE.md` 갱신 후 manifest를 handoff.mjs 전체 형식으로 —
  `node C:\Users\pc\.ai-harness\handoff.mjs write --replace --repo C:\Users\pc\test-project
  --task-id beta-2-unknown-time-three-pillar-20260712 --status review_requested
  --packet handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md --next-actor claude
  --next-action "라운드20 잔존 블로커 3건 수정분 라운드21 재검증. API·PDF·commit·push 금지"`
  → `validate` exit 0. write는 notes/STATE 편집 완료 후에만 실행.

## 7. 후속 순서

1. Codex가 §1~§5만 구현하고 §6 증거와 함께 review_requested로 넘긴다.
2. Claude 라운드21 재검증(기준환경 전체 pytest — test_p8 E2E 실렌더 포함 + verify 전체 False 키 덤프).
3. PASS 시 Codex 신선 read-only 확인 → 운영자 checkpoint commit 결정
   (스코프 밖 변경 2건 플래그 + §3 하한 수치 최종 확인 포함).
4. advisory 3건·유료 replacement·hsweep·300dpi 육안은 별도 운영자 결정 전 착수 금지.
