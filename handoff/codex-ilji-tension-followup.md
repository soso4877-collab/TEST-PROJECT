# CODEX TASK — 일지 형·해·파·원진 후속 2건 (배선 대칭 + 게이트 커버리지)

작성: 2026-07-07 · 검증자(Claude) → 구현자(Codex) · 브랜치 `codex/gunghap-relationship-quality`
근거: 다층 검증 리뷰의 `/adjacent` 사각 인접 스캔에서 확정된 2갭. 정확성 블로커는 아니며 완결성 보강.

---

## 0. 프로토콜 (Codex 운영 계약 — 이번 승인 범위)
- 역할: **구현자**(이 문서가 승인된 TASK). 수정 허용 파일은 각 태스크에 명시된 것만.
- **상시 금지(승인받아도 금지)**: PDF 재생성, LLM(Anthropic API 포함) 호출, `git commit`, `push`, deploy.
- **데이터 경계**: `harness/profiles/local/**` 비열람. 실 PII 인용 금지. 신규 테스트는 **합성 PII-free**(이름 예: `합성갑`·`합성을`, 기존 실명 3건은 익명화됐으며 재사용 금지 — 신규 코드에서).
- **가드 불변**: `content/` 변경은 3단 가드(safe_lint/factcheck/trace) 완화·우회 금지(절대규칙 12).
- **완료 근거**: `--no-tests` 아님. 아래 §3 전체 pytest 실행본 + passed 수 + 마지막 HEAD SHA(커밋하지 말 것, 워킹트리 상태로 보고). `/done` 형식.

## 1. 기결정 (이미 확정 — 재조사 불필요)
- 워킹트리에 형·해·파·원진 **1차 구현이 이미 존재**(미커밋, HEAD `786ac29`): `calc/partner.py`(표+필드+독립판정), `gunghap.py:_pair_slot`(소비), `relationship/context.py:_RAW_REPLACEMENTS`(순화), 신규 테스트 3파일.
- 검증 완료(신선 컨텍스트): docs/03 §1-1 채택표 ↔ `calc/partner.py` 표 **1:1 일치 + 표준 명리 정설 부합**. 독립 판정(elif 아님) — 巳申=육합+파, 子未=해+원진, 寅巳=해만(형 defer) 정상. 전체 스위트 **652 passed / 4 skipped, exit 0**(회귀 0). factcheck 정적 분석 안전.
- 데이터 모델(변경 금지): `PartnerFacts.ilji_hai/ilji_po/ilji_wonjin`은 값 `"해"/"파"/"원진"`, `ilji_xing`은 `"자형"/"상형"`. 값 없으면 `""`.
- 채택표(참조, `docs/03-engine-validation-plan.md §1-1` 정본): 육해 子未·丑午·寅巳·卯辰·申亥·酉戌 / 육파 子酉·卯午·巳申·寅亥·丑辰·戌未 / 원진 子未·丑午·寅酉·卯申·辰亥·巳戌 / 자형 辰午酉亥 / 상형 子卯. **삼형 완전판 defer**(寅巳는 해만).

---

## 2. 태스크

### TASK 1 — `partner_block` 대칭 배선 (개인 리포트 consult 경로)
**문제**: `PartnerFacts`의 두 번째 활성 소비처 `sajugen/content/rules.py:1706 partner_block`(호출처 `sajugen/content/builder.py:170` — 개인 리포트에서 신청자가 배우자·가족을 물을 때 LLM에 주입되는 consult 근거 슬롯)이 `gan_hap`·`ilji_relation`(육합/충, 라인 1737-1740)·`ilji_banhap`(1741)만 소비하고 **신규 형/해/파/원진은 미배선**. 결과: 같은 두 사람인데 궁합 상품(`_pair_slot`)은 긴장 관계를 노출하고 개인 consult 경로는 더 순하고 불완전.

**수정 파일**: `sajugen/content/rules.py` (partner_block 함수 내부, 1741 `ilji_banhap` 블록 근처).

**구현**:
- `pf.ilji_hai`·`pf.ilji_po`·`pf.ilji_wonjin`·`pf.ilji_xing` 각각 **독립 `if` 블록**(elif 금지 — 한 쌍이 다관계 동시 보유). `_pair_slot`(gunghap.py:333-351)과 동일 패턴.
- 톤: partner_block 기존 register(`~자리다`)에 맞추되 **advisory·경향/구조**(절대규칙 11 단정 금지). 참조 문안(그대로 써도 되고 다듬어도 됨):
  - 해: `f"본인 일지와 {who}의 일지는 해, 생활 리듬이 엇갈리기 쉬워 확인이 필요한 자리다."`
  - 파: `f"본인 일지와 {who}의 일지는 파, 가까워진 뒤에도 약속과 역할을 다시 맞춰야 하는 자리다."`
  - 원진: `f"본인 일지와 {who}의 일지는 원진, 이유 없이 서먹해지기 쉬워 감정을 천천히 확인해야 하는 자리다."`
  - 형: `f"본인 일지와 {who}의 일지는 {pf.ilji_xing}, 비슷한 반응이 반복될 때 속도를 낮춰야 하는 자리다."`
- factcheck 안전 이미 분석됨(한글, 간지쌍 아님) — 가드 등록 불필요.

**테스트**(같은 커밋): `tests/test_partner.py`의 `test_partner_block_text`(259) 인접에 신규 케이스 — 형/해/파/원진을 가진 합성 `PartnerFacts`를 만들어 `partner_block` 출력에 각 문장이 등장함을 단언(소비 증명). `_pair_slot` 소비 테스트(test_gunghap.py:`test_pair_slot_outputs_new_ilji_tension_fields`)와 대칭.

**운영자 결정(2026-07-07 확정): 배선.** scope-out 아님 — 위 구현대로 대칭 배선 진행. 착수 전 재확인 불요.

### TASK 2 — 신규 어휘 가드-안전성 직접 테스트 (전제 정정본)
> **⚠ 전제 정정(2026-07-07, Codex 1차자료 리딩으로 확정)**: 구 지시의 "use_llm=False 폴백이 _compose 가드 스택을 탄다"는 **틀렸다**. `sajugen/gunghap.py:1016-1017`에서 `if not use_llm or not os.environ.get("ANTHROPIC_API_KEY"): return fallback` — `_finalize` 직후 **즉시 반환**하고, safe/style/quality/temporal/loanword/raw_calc/customer_meta/guarantee/factcheck 가드 스택(gunghap.py:1054-1074)은 그 아래 **LLM `cand` 경로 전용**이다. business 폴백(`_pair_slot` 텍스트)의 실제 런타임 게이트는 렌더 시 `render_verify.verify`. 따라서 폴백 build로는 콘텐츠 가드 스택을 실측할 수 없다.

**목표(불변)**: 신규 긴장 어휘(해/파/원진/자형/상형 문장)가 가드에 의해 **거짓 차단(false-positive)되지 않음**을 실측. LLM이 이 어휘를 echo해도, 렌더 verify가 이 어휘를 만나도 스퓨리어스 차단이 없어야 한다.

**수정 파일**: `tests/test_gunghap.py`(신규 테스트 1개). **소스 미변경.**

**방식(정확) — 가드 함수 직접 호출 단위 테스트** (build 폴백 경로 의존 제거):
- 대상 텍스트: 합성 `PartnerFacts`(ilji_hai/po/wonjin/xing 세팅)로 `g._pair_slot` 호출한 출력 문자열. 기존 `test_pair_slot_outputs_new_ilji_tension_fields`(test_gunghap.py) 패턴 재사용 — 합성 이름(`합성갑`·`합성을`), PII 0.
- **gunghap.py:1054-1074의 가드 세트를 그대로 미러**해 그 텍스트에 직접 적용하고 각각 clean(빈 리스트) 단언:
  `safe_lint.lint`, `style_lint.lint`, `quality_lint.lint(text, names)`, `client_tone_lint.loanword_lint`, `client_tone_lint.raw_calc_lint`, `customer_meta_lint.lint`, `delivery_quality.guarantee_lint`, `factcheck.check_with_allow(text, allow)`.
  (모듈명·import 경로는 gunghap.py 상단 import를 그대로 따를 것 — 추정 금지. temporal/name/identity/singang lint는 문맥 인자 의존이라 이 텍스트-단위 테스트에서 제외 가능, 사유 주석.)
- `factcheck`용 `allow`: 합성 saju의 `factcheck.allowed_tokens(...)` 또는 간지 토큰 없는 최소 허용 dict. 목적은 신규 한글 어휘("해"·"자형" 등)가 한글 간지 스캐너에 오검출되지 않음을 실측.
- 단언: 위 가드 전부 `== []`. 하나라도 위반이면 신규 어휘가 가드를 트립 → 실측 실패로 드러남(정적 분석이 아니라 실행으로 증명).
- PII 0 · 렌더 0 · LLM 0 · build 불필요.

**선택(더 강한 통합 커버, 여유 시)**: `use_llm=True` 경로를 **fake anthropic 응답**(긴장 어휘 echo)로 태워 `_compose`가 `fallback` 아닌 `cand`를 반환함을 단언(실제 cand 가드 경로 실측). `_compose`는 함수 내부에서 `import anthropic` 하므로 `sys.modules["anthropic"]`에 fake 주입 필요. **1차는 위 직접 호출 방식으로 충분** — 이 통합판은 옵션.

---

## 3. 검증 (완료 근거 — 전부 실행)
```
PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest tests/ -q
```
- 통과 기준: **passed ≥ 652 + 신규(회귀 0), exit 0.** (기준선: 검증자 환경 652 passed / 4 skipped. Codex 환경은 리소스 부재로 skip 수가 더 많을 수 있음 — passed 절대수 감소가 아니면 정상.)
- 발급 경로 불변: `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest tests/test_orders.py tests/test_final_render_gate.py -q` → GREEN.
- `git diff --stat` 변경 파일 = **TASK1: rules.py + test_partner.py / TASK2: test_gunghap.py** 만(그 외 파일 변경 금지).
- calc/ 미변경(TASK는 content/·tests/) → 골든 스윕은 전체 스위트에 이미 포함, 별도 회귀 불요이나 GREEN 확인.

## 4. Out of scope (Codex 금지 / 운영자 스텝)
- **h153 실 재렌더 + 300dpi 시각·톤 검수**(흉의 문안 인상 확인): 실 PII 프로파일 열람 + PDF 산출이라 **운영자 전용**. Codex 금지.
- 커밋·푸시: 운영자 지시 시에만.

---

## 5. FIX — render-gate 블로커: 신규 해(害) 문안 외래어 "리듬" (2026-07-07 합성 렌더 실측 발견)

> **실측 근거**: 합성 3인(子 1990-01-11 · 未 1990-01-06 · 酉 1990-01-08) business 룰전용 렌더
> → `gate_pass=False`, **유일 실패 GATE_KEY = `loanword_clean=False`**(나머지 19키 True, hard failures 없음).
> `loanword_lint` match = **"리듬"**(alt "호흡"), _pair_slot·partner_block 두 곳. business 폴백은
> `normalize_loanwords`(gunghap.py:1047)를 **미경유**(gunghap.py:1016 조기 `return fallback`)라 외래어가
> PDF로 직행 → **육해 쌍이 있는 business 궁합 빌드가 하드 게이트로 RuntimeError**(발송 불가).
> `loanword_clean`이 유일 실패 키였으므로 **이 한 단어를 고치면 20/20 → gate_pass=True**(합성 렌더도 통과).

**수정 파일 (전수 — "리듬" pin 위치 전부. `git diff --stat` 예상 = 아래 5파일. 구 지시의 "3파일만"은 오류였음)**:
`sajugen/gunghap.py`(_pair_slot 해) · `sajugen/content/rules.py`(partner_block 해) · `docs/03-engine-validation-plan.md`(§1-1 육해 해석 범위 desc) · `tests/test_partner.py`(정확문구 단언) · `tests/test_gunghap.py`(가드 raw 재작성). (+ 권장: `tests/test_raw_term_sweep.py` 감지 갭 — 아래 5.)

**구현**:
1. `gunghap.py:_pair_slot` 해 문장(현재 336행): `생활 리듬이 어긋날 때` → **`생활 흐름이 어긋날 때`** (또는 `호흡`. 둘 다 loanword clean 실측). 다른 신규 문안(파/원진/자형/상형)엔 외래어 없음(실측) — 손대지 말 것.
2. `rules.py:partner_block` 해 문장(현재 1743행): `생활 리듬이 엇갈리기 쉬워` → **`생활 흐름이 엇갈리기 쉬워`**.
3. `docs/03-engine-validation-plan.md` §1-1 육해 행 "해석 범위"(현재 32행): `생활 리듬이 엇갈리기 쉬운 결` → **`생활 흐름이 엇갈리기 쉬운 결`** (문서-코드 정합).
4. `tests/test_partner.py`(현재 294행) 정확문구 단언: `생활 리듬이 엇갈리기 쉬워 확인이 필요한 자리다` → **`생활 흐름이 엇갈리기 쉬워 확인이 필요한 자리다`**로 동기화. **추가**: partner_block 출력에 `ct.loanword_lint(blk) == []` 단언(하드닝).
5. **근본원인 2층 — 감지 시스템 갭 2곳**(왜 green으로 새어 들어왔나):
   - (a) `tests/test_gunghap.py:test_pair_slot_ilji_tension_terms_are_guard_clean`이 `normalize_loanwords`를 **먼저 적용**(현재 391행)해 raw 외래어를 가렸다. business 폴백은 normalize 안 함 → 실경로 미대표(false green). → **normalize 제거, raw `_pair_slot` 출력에 직접 `loanword_lint` 적용**해 clean 단언(수정 전이면 "리듬"으로 실패, 수정 후 통과).
   - (b) `tests/test_raw_term_sweep.py:test_gunghap_and_integrated_skeletons_pass_loanword`(51-66행)의 "리듬 스윕 앵커"가 `inspect.getsource(rf/rc)` + rc.GUIDE + itg._DEPTH만 스캔하고 **gunghap.py(_pair_slot)·content/rules.py(partner_block) 소스를 누락**해 신규 "리듬"을 못 잡았다. → **스윕 대상에 두 소비처의 실제 출력**(모든 긴장 필드 세팅한 `_pair_slot`·`partner_block` 출력 문자열)을 추가하고 `"리듬" not in joined` + loanword_lint 단언 유지. (전체 소스 스캔은 주석·비고객문 오탐 위험 — 출력 문자열 스캔 권장.)

**검증(코드 수정 후 — Codex 몫)**:
- `PYTHONUTF8=1 ./.venv/Scripts/python.exe -m pytest tests/ -q` → 회귀 0, exit 0. 수정된 가드/스윕 테스트가 raw 경로로 통과.
- `git diff --stat` → 위 5(+1)파일 범위. **커밋 금지**, 워킹트리 + pytest 출력 + HEAD SHA(75c65f1)로 보고.

**검증(렌더 gate_pass — 검증자 Claude 몫, Codex 금지)**: 수정 후 합성 3인 business 렌더 재실행 → **빌드 성공·`gate_pass=True`**(loanword_clean 유일 실패였으므로 20/20 회복). `loanword_clean`만 False였던 실측이 근거.

**참고(비블로커)**: 같은 렌더에서 `domain_term_repetition` **경고**(결 34·구조 32·자리 25) — `delivery_quality_clean=True`(게이트 아님). 룰전용 미니 리포트라 과장된 값. 신규 `_ILJI_TENSION_KO`가 "결/구조" 의존이 큰 건 사실이나 하드 블로커 아님. 문안 다양화는 선택.
