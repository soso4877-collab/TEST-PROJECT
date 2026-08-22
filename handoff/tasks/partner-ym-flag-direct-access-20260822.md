# TASK_PACKET — 상대 연·월주 억제 플래그 duck-typing 제거 (partner-ym-flag-direct-access-20260822)

- **task_id**: `partner-ym-flag-direct-access-20260822`
- **owner**: **Codex 구현자** (AGENTS.md 기본 사이클)
- **next_reviewer**: **Claude Code 교차리뷰** (read-only, 구현 세션과 분리)
- **base_commit**: `3a26505` (현재 HEAD, tree clean, branch `codex/gunghap-relationship-quality`; rev1 작성 시점은 `bfa1e2d`, 그 사이 커밋은 handoff 기록·천체력 경로 태스크뿐이라 `content/rules.py:2147` 결함 문장은 실측 동일)
- **근거**: `partner-unknown-time-boundary-20260818` 교차리뷰 비블로커 **N-1**
  (`REVIEW-FEEDBACK.md` 2026-08-19 절 / `sajugen/STATE.md` 122-123행)
- **rev**: 1

---

## 0. 역할·금지

Codex 상시 금지(PDF 재생성 · LLM/Anthropic API 호출 · git commit · push · 배포)는 그대로다.
커밋은 운영자가 checkpoint 로 직접 한다.

검색(rg 등) 시 ignored 영역 제외 글롭 필수:
`--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`

---

## 1. Goal (관측 가능한 결과 하나)

**절대규칙 8-1 의 고객 가시 억제 가드가 fail-open 하지 않는다** — 억제 플래그를 읽는 경로가
기본값으로 조용히 통과하지 못하고, 플래그가 없는 객체는 소리 내어 실패한다.

## 2. Background — 실측 (2026-08-22 설계 세션, read-only)

### 2-1. 결함 문장

```
sajugen/content/rules.py:2147   ym_dep = bool(getattr(pf, "ym_time_dependent", False))
```

바로 다음 줄이 고객 가시 억제를 건다 — `ym_dep` 이 True 여야 "절기가 바뀌는 날이라 시간에 따라
연주·월주가 갈린다" 고지가 붙고 연·월주가 확정 사실에서 빠진다(절대규칙 8-1).

`getattr` 기본값 `False` 때문에 **플래그가 없는 객체가 들어오면 억제가 조용히 꺼진다.**
차단이 아니라 통과 = fail-open 이고, 결과는 고객 문서에 연·월주가 **단정**되는 것이다.
이건 방법론 B-2("조용한 no-op 금지, 부재는 실패로 취급") 위반이다.

### 2-2. 비대칭 — 같은 플래그를 다른 곳은 직접 읽는다

```
sajugen/content/builder.py:296   if pf.ym_time_dependent            <- 직접 접근
sajugen/content/rules.py:2147    getattr(pf, "ym_time_dependent", False)   <- 기본값
```

같은 필드, 같은 호출 흐름인데 한쪽만 방어적이다. 둘 중 하나는 틀렸고, **틀린 쪽은 기본값이 있는
쪽**이다(아래 2-3).

### 2-3. 기본값은 사문(死文)이다 — 실측

| 확인 | 결과 |
|---|---|
| `PartnerFacts.ym_time_dependent` 선언 | `calc/partner.py:119` — `bool = False` 필드, **항상 존재** |
| `partner_block` 제품 호출부 | `content/builder.py:290` **1곳뿐** |
| 그 호출부가 넘기는 값 | `calc/partner.py:234` 가 반환한 `PartnerFacts` |
| 테스트 호출부 | `test_partner.py` · `test_partner_unknown_time.py` · `test_couple_language.py` · `test_raw_term_sweep.py` — 전부 실제 `PartnerFacts` |
| duck-typing 호출자 | **0건** |

즉 기본값은 한 번도 쓰이지 않으면서 **가드만 약화시킨다.** 소비처 배선이 없는 방어값은
"파라미터를 만들면 소비처 배선과 분기 테스트까지가 한 단위"(방법론 A-5) 의 반대 사례다.

### 2-4. 인접 사각 — 조사했고 **범위에 넣지 않는다**

`sajugen/**` 의 `getattr(x, "필드", 기본값)` 형태를 전수 훑었다. 같은 계열로 의심되는 것은
`birth_time_mode` 3곳(`builder.py:120`·`builder.py:208`·`integrated.py:497`)이다.

**그러나 위험 등급이 다르다.** `builder.py:120` 은 기본값이 실제로 발동하면 `saju.myeongni` 로
분기하는데, 삼주 객체에는 그 속성이 없어 `AttributeError` 로 **소리 내어 실패**한다
(`calc/engine.py:58` 도크스트링). fail-open 이 아니라 fail-loud 다. 게다가 `SajuResult`(property)와
`ThreePillarResult`(field) 양쪽에 필드가 실재하므로 기본값은 역시 사문이다.

→ **이번 범위에 넣지 않는다.** 구현자는 이 3곳을 **수정하지 말고**, §5-3 의 조사 보고만 한다.

---

## 3. 변경 설계

`rules.py:2147` 을 직접 접근으로 좁힌다.

```python
ym_dep = bool(pf.ym_time_dependent)
```

`bool()` 은 유지한다(호출부 계약을 좁히지 않는다). 주변 주석·문안·조건 분기 **무수정**.

### 하지 않을 것

- `partner_block` 시그니처에 타입 힌트 추가 **금지** — `content` → `calc` import 가 새로 생기고
  순환 위험 판단이 이번 범위 밖이다. 필요하면 별도 패킷.
- `builder.py:296` **무수정**(이미 직접 접근이다).
- §2-4 의 `birth_time_mode` 3곳 **무수정**.
- 고객 가시 문안·고지 문구·절대규칙 8-1 확정 문구 **무수정**.

---

## 4. 파일 경계

**allowed_files**
```
sajugen/content/rules.py                 (2147행 1줄만)
tests/test_partner_unknown_time.py       (양방 테스트 추가)
implementation-notes.md                  (구현 보고)
sajugen/STATE.md                         (진행 기록, 마지막에)
```

**forbidden_files** — 위 목록 밖 전부. 특히:
```
sajugen/calc/**  ·  sajugen/content/builder.py  ·  sajugen/content/factcheck.py
sajugen/render/**  ·  docs/**  ·  .claude/rules/**  ·  handoff/current/manifest.json
config/**  ·  harness/profiles/local/** (비열람)
```

경계 밖 수정이 필요하면 우회하지 말고 **`BLOCKED_CONTRACT` 로 정지**한다.

---

## 5. 수용 기준 — 양방 테스트 (작업 규율 3)

`tests/test_partner_unknown_time.py` 에 추가한다. 이 파일이 이미 절대규칙 8-1 계약을 담고 있다.

**(가) 정상 통과 — 기존 거동 불변**
1. 기존 8-1 테스트 전부 GREEN 유지(경계일 억제 · 비경계일 비억제 · 시각 기지 비억제).
   **기존 단언 수정 금지** — 하나라도 고쳐야 한다면 그건 거동 변경이므로 정지 보고 대상이다.

**(나) 결함 차단 — fail-open 이 닫혔음을 실증**
2. `ym_time_dependent` 속성이 **없는** 합성 객체를 `partner_block` 에 넘기면
   `AttributeError` 가 발생한다. 교정 전에는 이 테스트가 **RED**(예외 없이 통과해 버린다)여야 한다.

**주의(no-op 함정)**: 2번을 `PartnerFacts` 인스턴스에서 `delattr` 로 만들려 하면 dataclass 기본값이
클래스 속성으로 남아 **속성이 계속 보인다**. 실제로 속성이 없는 객체여야 한다.

**교정 전 RED 실증 의무**: 2번을 교정 전 코드에서 먼저 돌려 RED 를 확인하고, 그 출력을 보고에 적어라.
RED 를 못 보이면 그 테스트는 검출력이 없다.

---

## 6. 검증 명령 (전부 실행 · 증거 필수)

```
./.venv/Scripts/python.exe -m pytest tests/ -q
```
- 통과 기준: **exit 0**, 그 환경 안에서 passed 감소 0 + 신규만큼 증가.
- **기준선(2026-08-22) = `1279 passed / 4 skipped / exit 0`, 수집 총수 1283.**
- **환경차 판정 규칙(AGENTS.md §10)**: 다른 환경의 raw passed 를 직접 비교하지 마라. 구현환경은
  Playwright 제한으로 skip 이 더 많다(직전 태스크 실측: 구현 1251/32 ↔ 기준 1279/4, 총수 1283 동일).
  같은 형태면 `EVIDENCE_SPLIT_PASS` 로 보고하되 **수집 총수와 skip 사유를 함께** 제시해야 성립한다.

```
./.venv/Scripts/python.exe -m pytest tests/test_partner_unknown_time.py tests/test_partner.py tests/test_couple_language.py -q
./.venv/Scripts/python.exe -m ruff check sajugen tests
./.venv/Scripts/python.exe -m py_compile sajugen/content/rules.py
git diff --check
git status --short --untracked-files=all
```
- 관계 3파일 묶음은 기준선 대비 **비감소**여야 한다.
- 전체 Ruff 는 기존 부채 3건(`content/temporal_lint.py:11` · `insight.py:152` · `tests/test_p2.py:10`)
  으로 exit 1 이 정상이다. **변경 파일 신규 위반 0** 을 따로 보여라.
- `calc/`·`input/` 은 **무변경**이어야 한다:
  `git status --short --untracked-files=all -- sajugen/calc sajugen/input` 이 **무출력**임을 보여라.
  (이번 변경은 `content/` 한정이라 골든 전수는 필수가 아니지만, 무변경 증명은 필요하다.)

### 5-3. 조사 보고 (수정 없음)

§2-4 의 `birth_time_mode` 3곳에 대해 **읽기만 하고** 아래를 보고에 적어라. 수정하면 계약 위반이다.
- 각 지점의 기본값이 실제로 발동 가능한지(= 필드가 없는 호출자가 존재하는지)
- 발동 시 fail-open 인지 fail-loud 인지
- 별도 패킷이 필요한지에 대한 판단 1줄

---

## 7. 정지 조건 (BLOCKED_CONTRACT)

- allowed_files 밖 수정이 필요해질 때
- 기존 8-1 테스트 단언을 고쳐야 통과할 때 — **거동이 바뀐 것이므로 고치지 말고 정지 보고**
- `bool(pf.ym_time_dependent)` 로 바꿨을 때 제품 경로에서 `AttributeError` 가 실제로 발생할 때
  (= duck-typing 호출자가 실재한다는 뜻 → §2-3 실측이 틀린 것이므로 즉시 보고)
- PDF 렌더·LLM 호출·commit·push 가 필요해질 때

## 8. 산출물

- `CODEX_IMPLEMENTATION_REPORT` (`implementation-notes.md` 최상단) — 실행 명령 + 출력(passed 수/exit code),
  **교정 전 신규 테스트 RED 실증**, §5-3 조사 보고, 미검증 항목 분리 명시
- `sajugen/STATE.md` 재개 앵커 갱신
- 커밋 금지. 운영자 checkpoint 대기.

## 9. 리스크 메모

- **1줄 변경이지만 고객 가시 절대규칙 가드다.** "한 줄이니 안전하다" 는 추정이며, 관계 상품
  회귀로 증명해야 한다(방법론 A-1).
- 이 태스크는 F-1(대운 축)·N-5(factcheck 일상어 동형·다인 allow-set)와 **무관**하다.
  둘 다 별도 보류 중이며 이 패킷에서 건드리지 않는다.
