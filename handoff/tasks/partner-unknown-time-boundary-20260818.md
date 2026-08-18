# TASK_PACKET — 사연 파싱 상대의 시각 미상 x 절입 경계일 비단정 (partner-unknown-time-boundary-20260818)

- **task_id**: `partner-unknown-time-boundary-20260818`
- **owner**: **Claude Code — 별도 신선 세션**(이 패킷을 쓴 설계 세션이 아니다). 운영자 승인 2026-08-19, §0
- **next_reviewer**: **또 다른 신선 Claude Code 세션 (read-only 교차리뷰)** — 구현 세션과 분리
- **base_commit**: `c9a5a1fd0150e79291745b3568d3c0179c2619f7` (현재 HEAD, tree clean, branch `codex/gunghap-relationship-quality`)
- **선행**: `partner-axis-fix-20260817` (CODE_PASS, 커밋 `1151483`) 교차리뷰 **소견 ②**
- **근거 문서**: `REVIEW-FEEDBACK.md` 2026-08-18 §5(+2026-08-19 정정) / 이 패킷 §2 의 조사 세션 실측
- **rev**: 2 (rev2 = 운영자 결정 2건 확정 — 절대규칙 8-1 문구 확정 · 구현자=Claude 예외)

---

## 0. 운영자 승인 기록 (AGENTS.md 기본값 이탈)

AGENTS.md 기본값은 **Codex 구현 → Claude 교차리뷰**다. Codex 토큰 부재로 운영자가 Claude 구현
예외를 승인했다(선행 `solar-term-axis-fix-20260817`·`partner-axis-fix-20260817` 과 동일 조건).

| 항목 | 값 |
|---|---|
| 승인일 | 2026-08-19 |
| 승인자 | 운영자 |
| 사유 | Codex 토큰 부재 (선행 2건과 동일 조건) |
| 구현 | **Claude Code — 별도 신선 세션** (이 패킷 작성 세션 아님) |
| 검증 | **또 다른 신선 Claude Code 세션, read-only 교차리뷰** |
| 근거 조항 | AGENTS.md "운영자가 Claude 구현을 별도로 승인한 경우만 예외다" |

선행 `partner-axis-fix-20260817` 은 작성 세션 == 구현 세션이었고 그 이탈을 §0 에 기록했다.
**이번에는 운영자가 3단 분리를 명시했다**: 설계(이 세션) / 구현(신선 세션) / 검증(또 다른 신선 세션).
자기검증 금지와 자기작성-구현 결합 회피가 둘 다 성립한다.

Codex 상시 금지(PDF 재생성·LLM 호출·git commit·push·배포)는 **Claude 구현에도 동일 적용**한다.

---

## 1. Goal (관측 가능한 결과 하나)

**사연에서 감지한 상대의 출생 시각이 미상이고 그 날짜 안에서 월건이 바뀌면, 고객 가시 문안과
factcheck 허용 토큰 양쪽에서 상대의 연주·월주가 사라지고 일주 중심 서술 + 고지로 대체된다.**

수용 지표: 경계일 합성 케이스에서 상대 연·월주 간지가 `partner_block` 출력과
`factcheck.allowed_tokens` 에 **둘 다 부재**, 비경계일·시각 기지 케이스는 **현행과 동일**.

## 2. Background — 실측 (2026-08-18 조사 세션, read-only 프로브)

### 2-1. 결함 문장

`calc/partner.py:157-158` 이 시각 미상 상대에 정오(12:00)를 대입하고, 그 연·월주가
`content/rules.py:2146-2153` 에서 `"OO년 OO월 OO일생"` 으로 고객 가시 근거 슬롯에 **사실로 단정**된다.
`hour_note`(`rules.py:2142-2144`)는 **시주만** 면책한다. 절대규칙 8이 본인에게 요구하는
`NEEDS_INFO_TIME_BOUNDARY` 등가 가드가 이 경로에는 없다.

### 2-2. 노출 폭 — "18일"은 폐기한다 (전제 교정)

선행 리뷰의 18일 목록은 **이번 축 교정이 정오 대입 판정을 뒤집은 날**의 집합이지 노출 집합이 아니다.
절 이름 화이트리스트 없이, 제품이 본인 경로에서 쓰는 술어
`three_pillar.ensure_unambiguous_civil_date`(`calc/three_pillar.py:147-154`)로만 1960~2030 전수 재측정:

```
boundary_days(blocked)=852        = 12.0일/년 = 전체 날짜의 3.29%
days_with_any_mismatch=815/852    (95.7%)
total_mismatch_hour_buckets=5101/20448   (경계일 시간대의 24.9%)
listed_18_inside_boundary_set=18/18      (18일은 852일의 부분집합)
boundary_days_with_term_in_12:00-12:59=36
```

- 임의 시각 기준 오단정 확률 = 5101/622386 = **0.82%(약 122명 중 1명)** [균등분포 가정].
- 18일 목록을 키로 삼는 게이트는 **틀린 게이트**다. 판별 술어는 위 함수 하나뿐이며 새 상수표를 만들지 않는다.

### 2-3. 축 정합 — 신규 결함 없음 (같은 세션 실측)

본인 삼주 축(`three_pillar._base_eight_char`, 원시 정오)과 상대 축(`partner_pillars(hour=None)`)의
연·월주 비교: **경계일 밖 불일치 0**, 불일치 36건은 전부 본인 경로가 차단하는 경계일.
두 번째 축 결함은 없으므로 이 패킷은 축을 건드리지 않는다.

### 2-4. 제품 안의 정책 비대칭

| 경로 | 시각 미상 + 경계일 | 근거 |
|---|---|---|
| 본인 | 하드 차단 `NEEDS_INFO_TIME_BOUNDARY` | `order_flow.py:598-603` |
| 구조화 상대 입력(integrated_full) | 접수 거부 "requires a known birth time" | `order_flow.py:577-578` |
| **사연 파싱 상대** | **정오 대입 후 단정** | `calc/partner.py:157-158`, `rules.py:2146-2153` |

사연 파싱 상대만 예외다.

### 2-5. 소급 영향 — 0건 (+ 확인 불가 3항)

`data/orders.sqlite` read-only 조회: `orders_total=5`, 상대 감지 **0건**,
`issue_final_pdf`/`issue_final_text`/`DELIVERED` **0회**. 따라서 기발급·발송 피해 0건.
확인 불가로 남는 것: (a) 삭제된 3주문(PII 파기 설계상 스캔 불가) (b) store 를 우회하는 CLI·harness
직접 렌더 (c) 상대 감지 0이라 파서 커버리지 자체는 미검증.

### 2-6. 일주에 남는 정책 잔여 (숨기지 않는다)

시각 미상이면 일주도 진태양시 보정(-32분) 때문에 약 23:32 KST 이후 출생에서 갈린다
(실측: 1999-01-18 에서 23:45·23:50·23:55). 하루의 약 1.9%이며 경계일과 무관하게 상시다.
절대규칙 8이 본인에 대해 "신고 날짜 기준 일주 고정"으로 이미 수용한 값이므로, 상대에게 같은
계약을 적용하는 것으로 정합시킨다(§3-1 확장 결정). **이 패킷은 일주를 억제하지 않는다.**

## 3. 운영자 결정 기록 (2026-08-18)

### 3-1. 확정된 3건

| 질문 | 결정 |
|---|---|
| 방향 | **(나) 비단정 + (다) 고지 흡수** — 접수 차단·인물 생략은 채택하지 않는다 |
| 절대규칙 8 확장 | **확장한다** — 사연 파싱 상대에게도 세 기둥 계약 적용(문서 개정 동반) |
| 파생 서술(보완 오행) | **일주 기준으로 축소** |

접수 차단((가-1))을 채택하지 않은 근거: 상대 날짜는 자유문 파서 산출이며, 오탐 날짜가 경계일과
겹치면 정상 주문이 차단된다(QI-2026-07-04 팬텀 파트너의 역방향 사고). 인물 생략((가-2))은
확정 가능한 일주·십성·합충 사실까지 버린다.

### 3-2. 구현자 — 확정 (2026-08-19)

**Claude 구현 예외**로 확정(Codex 토큰 부재). 단 **이 패킷을 쓴 설계 세션은 구현하지 않는다** —
구현은 별도 신선 세션, 검증은 또 다른 신선 세션의 read-only 교차리뷰다(§0).

## 4. allowed_files

```
sajugen/calc/partner.py                  (플래그 신설 + 파생 오행 축소)
sajugen/content/rules.py                 (partner_block 문안 분기 — §6-2 한정)
sajugen/content/builder.py               (partner_gz 축소 — §6-3 한정)
.claude/rules/00-immutable.md            (절대규칙 8 확장 문구 — §6-5)
.claude/rules/calc.md                    (한 줄 — §6-5)
docs/03-engine-validation-plan.md        (결정표 행)
docs/16-quality-incident-ledger.md       (감지 구멍 기록 — §10)
tests/test_partner_unknown_time.py       (신규)
tests/test_partner.py                    (회귀 보강만 — 기존 단언 완화 금지)
sajugen/STATE.md
implementation-notes.md
handoff/tasks/partner-unknown-time-boundary-20260818.md
handoff/current/manifest.json            (handoff.mjs write/validate 로만)
```

## 5. forbidden_files

```
tests/test_partner_axis.py        무변경 — 시각 미상 2행은 계약 테스트로 유효(교차리뷰 판정)
sajugen/calc/myeongni.py          축은 이 패킷 대상 아님(§2-3)
sajugen/calc/three_pillar.py      술어는 재사용만, 수정 금지
sajugen/calc/solarterms.py · crosscheck.py
sajugen/order_flow.py · app.py · cli.py    접수 차단은 채택 안 함(§3-1)
sajugen/gunghap.py · sajugen/render/**
sajugen/input/partner.py          파서 정확도는 별건
tests/test_golden_sweep.py        기준선 대조용 무변경
data/** · .env · harness/profiles/local/**
```

## 6. 구현 명세

### 6-1. `calc/partner.py` — 판정 플래그 (술어 재사용, 복제 금지)

- `PartnerFacts` 에 **`ym_time_dependent: bool = False`** 를 추가한다.
  기본값 False 는 합성 `PartnerFacts` 를 직접 만드는 기존 테스트
  (`test_partner.py:276`, `test_raw_term_sweep.py:71`, `test_couple_language.py:91`)를 그대로 통과시킨다.
- `partner_pillars` 에서 **`hour is None` 일 때만** 판정한다:

```python
ym_time_dependent = False
if not hour_known:
    try:
        ensure_unambiguous_civil_date(year, month, day)
    except NeedsInfoTimeBoundary:
        ym_time_dependent = True
```

- 술어는 `from .three_pillar import NeedsInfoTimeBoundary, ensure_unambiguous_civil_date` 로 **재사용**한다.
  월건 비교 로직을 partner 에 다시 적는 것은 **금지**(방법론 B-1 단일 소스).
  모듈 상단 import 가 순환·부작용(`three_pillar` 는 `kasi` 를 import 한다)을 일으키면 함수 내 지연
  import 로 낮추되, **술어 재구현은 어떤 경우에도 하지 않는다**.
- **연·월주 필드 자체는 계산해서 그대로 담는다**(소비처가 2곳뿐이라 표시·허용 단계에서 억제한다).

### 6-2. 파생 오행 축소 (운영자 결정 §3-1)

`partner.py:201-210` 의 `partner_elems` 는 현재 연·월·일(+시)주 간지 오행을 모은다.
`ym_time_dependent` 가 True 면 **일주(간+지)만**으로 계산한다.

- `matches_my_yongshin`(`partner.py:212-213`)은 이미 일간 오행만 쓰므로 **무변경**이다.
  이 패킷에서 축소 대상은 `complements_elems_ko` 하나뿐이다 — 정확히 그것만 바꾼다.

### 6-3. `content/builder.py:292-294` — 허용 토큰 축소 (가장 중요한 배선)

```python
gz_all |= {p.ganzhi for p in (pf.day, pf.hour) if p is not None} if pf.ym_time_dependent \
          else {p.ganzhi for p in (pf.year, pf.month, pf.day, pf.hour) if p is not None}
```

(표현은 자유, 조건이 핵심.) **문안에서만 빼고 allow-set 에 남기면 LLM 이 연·월주를 되살려도
factcheck 가 통과시킨다 — 감지 불가능한 우회로다.** 선례: `factcheck.py:68-74` 가 삼주 모드에서
시주를 allow-set 에서 빼는 것과 같은 기전.

이 배선이 실제 방어가 되는 근거(소스 실측, 조사 세션):

- 고객 가시 문안은 한글 간지("병인년")인데 `factcheck.py:159-172` 가 접미 문맥(`년|월|일|일주|대운…`)
  붙은 **한글 간지도 검사**하고, 그 허용 집합 `ganzhi_ko` 는 `factcheck.py:111` 에서 `gz`(= `extra_ganzhi`
  포함)로부터 파생된다. 즉 `partner_gz` 축소는 한자·한글 양쪽 표기를 동시에 막는다.
- **사각 1개 — 일상어 동형 예외**: `_GANZHI_KO_COMMON_WORDS`(`factcheck.py:31` = 계신·임신·기사·무사·
  병사·정사·기미)는 허용 집합에 없으면 **검사에서 건너뛴다**. 억제 대상 연·월주가 `임신`·`기사`·`정사`·
  `기미` 이면 allow-set 에서 빼도 factcheck 는 통과시킨다. 이건 이 패킷이 고치지 않는 기존 구조이므로,
  **T6 결함 주입 케이스는 이 집합 밖 간지로 고른다**(그러지 않으면 방어를 검증하지 못한 채 GREEN 이 된다).
  이 잔여는 §12-3 에 미결로 올린다.

### 6-4. `content/rules.py:2142-2153` — 문안 분기 (고지 흡수)

- `ym_time_dependent` 가 True 면 `pillars` 문장에서 연·월주를 빼고 일주만 쓴다.
- 고지는 기존 `hour_note` 를 확장한다(별도 문단 신설 금지). 초안:

```
" 태어난 시간은 미상이라 시주는 제외, 대운도 산출하지 않았다."
+ " 이 날은 절기가 바뀌는 날이라 태어난 시간에 따라 연주와 월주가 갈려, 확정할 수 있는 일주를 중심으로 봤다."
```

- 상담가 문체 유지: AI·도구·자동화 언급 금지(절대규칙 18), 조사는 `_J`/`_josa` 헬퍼 사용,
  `client_tone_lint.loanword_lint` 통과.

### 6-5. 문서 개정 (절대규칙 8 확장 — 운영자 승인 §3-1)

`.claude/rules/00-immutable.md` 절대규칙 8에 하위 조항을 추가한다. **범위를 넓게 읽히지 않도록
"무엇이 넘어오고 무엇이 안 넘어오는가"를 문구에 명시한다** — "같은 계약"이라고만 쓰면 본인 경로의
12시지 후보 축약·`time_invariant` 승격·`three_pillar_provenance` 까지 보장하는 것으로 읽히고,
그것이 이 프로젝트가 반복해 맞은 문서-코드 불일치(방법론 A-5)다. 초안:

> 8-1. 사연에서 감지한 상대(가족 포함)에게는 절대규칙 8의 **비단정 원칙만** 확장한다. 시각 미상이면
> 신고 날짜 기준 연·월·일주를 쓰되, 그 날짜 안에서 월건(입춘 포함)이 바뀌면 연주·월주를 확정된
> 사실로 서술하지 않고 고객 가시 문안과 factcheck 허용 토큰 양쪽에서 제외하며, 확정 가능한 일주를
> 중심으로 서술한다. **넘어오지 않는 것**: 주문 차단(상대 날짜는 자유문 파서 산출이라 오탐 차단
> 비용이 크다), 12시지 후보 축약과 `time_invariant` 승격, `three_pillar_provenance` 계약 — 상대
> 명식에는 적용하지 않는다. (2026-08-18 운영자 승인 개정.)

**위 8-1 문구는 2026-08-19 운영자가 초안 그대로 확정했다** — 구현 세션은 이 문구를 그대로 삽입하고
임의로 다듬지 않는다(절대규칙 개정은 운영자 명시 지시 사항이다).

`.claude/rules/calc.md` 에 한 줄, `docs/03` 결정표에 한 행을 같은 취지로 추가한다(요약 표현은 자유,
"비단정 원칙만 확장 / 차단·provenance·후보 축약은 비확장" 경계는 반드시 유지).

### 6-6. 하지 않는 것

- 접수 단계 차단·되묻기 도입, 사연 파서를 접수 단계로 이동
- 일주 억제(§2-6 — 절대규칙 8과 같은 계약으로 유지)
- 상대 대운·시주 산출, `PartnerFacts.note` 문구 변경
- 18일 상수표 도입(§2-2)

## 7. 테스트 (절대규칙 20 — 같은 작업 단위, 작업 규율 3 양방)

신규 `tests/test_partner_unknown_time.py`:

1. **차단 방향**: 경계일 + 시각 미상(`2011-04-05`, `1986-02-04`) → `partner_block` 출력에
   상대 연주·월주 한글 간지 **부재**, 일주 서술 **존재**, 고지 문장 **존재**.
2. **정상 통과 방향(완화 감지)**: 비경계일 + 시각 미상(`1999-01-18`) → 현행과 동일하게
   연·월·일주 3기둥 표기 **유지**(`test_partner.py:259` 와 모순 없음).
3. **과탐 감지**: 경계일 + 시각 기지(`2011-04-05 07:00`) → 억제 **없음**, 4기둥 현행 유지.
4. **플래그 경계 3행**: `(경계일, hour=None)=True` / `(경계일, hour 지정)=False` /
   `(비경계일, hour=None)=False`.
5. **허용 토큰**: 경계일 시각 미상 상대를 담은 합성 concern 으로 `build_report` →
   `factcheck.allowed_tokens` 에 상대 **연·월 간지 부재 + 일주 간지 존재**.
6. **결함 주입 차단**: 억제된 연·월 간지를 넣은 합성 텍스트가 `factcheck.check` 에서 **위반으로 잡힘**
   (allow-set 축소가 실제로 방어로 작동함을 증명).
7. **파생 축소**: 경계일 시각 미상에서 `complements_elems_ko` 가 일주 오행만 근거로 산출됨을
   합성 `my_elements` 로 단언(연·월주에만 있던 오행이 빠진다).
8. **다인 케이스(allow-set 공유)**: `builder.py:267` 은 최대 4인의 간지를 **한 개의 `gz_all`** 로 합친다.
   경계일 상대 A(억제)와 비경계일 상대 B(유지)를 같은 합성 concern 에 넣고, A 의 억제된 연·월 간지가
   B 때문에 허용 집합에 되살아나지 않는지 단언한다. 두 사람의 간지가 실제로 겹치는 경우는
   토큰 수준 허용이라 원리적으로 분리 불가이므로, 겹치지 않는 날짜 쌍으로 케이스를 만들고
   **겹칠 때 허용되는 잔여는 §12-4 에 명시**한다.
9. **PII 0**: 합성 입력만, 실명·실생년월일 사용 금지.

필수 회귀:

10. `pytest -k golden` **28 passed**(골든 값 불변 — partner 경로는 골든 산출에 없어야 한다).
11. `tests/test_partner_axis.py` **28 passed 무변경**(시각 미상 2행 그대로).
12. 관계 4파일 묶음(`test_partner.py test_gunghap.py test_raw_term_sweep.py test_couple_language.py`)
    기존 단언 **감소 0**(신규 추가로 인한 증가는 허용).
13. 전체 `pytest tests/ -q` exit 0, passed **>= 1255**, skipped **== 4**.

실행 명령(완료 근거):

```
./.venv/Scripts/python.exe -m pytest tests/test_partner_unknown_time.py -q
./.venv/Scripts/python.exe -m pytest tests/test_partner_axis.py -q
./.venv/Scripts/python.exe -m pytest tests/test_partner.py tests/test_gunghap.py tests/test_raw_term_sweep.py tests/test_couple_language.py -q
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m ruff check sajugen/calc/partner.py sajugen/content/rules.py sajugen/content/builder.py
```

교정 전 코드로 신규 테스트 1·5·6·7 이 **RED 임을 먼저 확인**하고 그 수치를 구현노트에 남긴다(검출력 실증).

## 8. done_when

- [ ] `ym_time_dependent` 가 `ensure_unambiguous_civil_date` **재사용**으로 산출되고 술어 복제 0
- [ ] 경계일 시각 미상에서 연·월주가 **문안과 allow-set 양쪽에서** 부재
- [ ] 비경계일·시각 기지 케이스 현행 동일(완화·과탐 양방 테스트 GREEN)
- [ ] `complements_elems_ko` 가 경계일에서 일주 기준으로 축소, `matches_my_yongshin` 무변경
- [ ] 신규 테스트 1~9 GREEN, 교정 전 RED 수치 기록
- [ ] `sajugen/STATE.md` 재개 앵커의 "절입 1704건 전수에서 18건" 문구를
      `ensure_unambiguous_civil_date` 술어 기준(852일/71년 = 12.0일/년 = 3.29%)으로 교정
      — STATE.md 는 SSOT 체인 1번이라 여기가 낡으면 다음 세션이 폐기된 전제를 다시 상속한다
- [ ] `pytest -k golden` 28 passed · `test_partner_axis.py` 28 passed 무변경
- [ ] 전체 exit 0, passed >= 1255, skipped == 4
- [ ] Ruff `All checks passed!` · `py_compile` exit 0
- [ ] 절대규칙 8-1 · `calc.md` · `docs/03` 결정표 문구 반영(운영자 확인 문구로)
- [ ] `docs/16` 에 감지 구멍 기록(§10)
- [ ] forbidden_files 미수정
- [ ] `STATE.md` 갱신 + `handoff.mjs write` → `validate` = `HANDOFF_VALID`
- [ ] commit·push·LLM·PDF 재생성 **0**

## 9. stop_conditions

- 골든 22건 값이 하나라도 바뀌면 즉시 중단·보고.
- 전체 passed < 1255 또는 skipped != 4 면 중단·보고.
- `tests/test_partner_axis.py` 수정이 필요하다는 결론(특히 시각 미상 2행) → **중단**.
- `ensure_unambiguous_civil_date` 를 완화·복제해야 통과한다는 결론 → **중단**(술어는 단일 소스).
- `order_flow.py`·`app.py`·`gunghap.py`·`input/partner.py` 수정이 필요하다는 결론 → 중단
  (이번 범위는 접수 차단이 아니다).
- 순환 import 를 지연 import 로도 못 푸는 경우 → 중단·보고.
- commit·push·배포·LLM·PDF 재생성이 필요해지면 중단.

## 10. 근본원인 2층 (방법론 A-6)

**표면**: 시각 없이는 정해지지 않는 연·월주를 고객 가시 문안이 사실로 단정한다.

**감지 시스템의 구멍**: 본인 경로에는 `ensure_unambiguous_civil_date` 게이트와 `three_pillar`
provenance 계약(`store/orders.py:99-144`)이 있는데, 상대 경로에는 **같은 성질의 사실을 다루는
어떤 술어도 배선되지 않았다**. 파라미터·정책이 한쪽에만 배선된 방법론 A-5 재발형이다
(팬텀 파트너 QI-2026-07-04 와 같은 형상).

재발방지: 신규 테스트 4·5(플래그 경계 + allow-set 부재)를 상시 회귀로 둔다.
`docs/16` 에 QI 항목으로 기록하고, 교차리뷰가 이 갭을 잡은 경로(선행 패킷 소견 ②)도 함께 남긴다.

## 11. 이 패킷에서 하지 않는 것

1. 접수 차단·되묻기 UI(운영자 미채택, §3-1).
2. 사연 파서 정확도 개선(`input/partner.py`) — 별건.
3. 이월 F-1(대운 `start_year` 앵커) — 유파 판단 선행, 별도 패킷.
4. 자미두수 입춘 해상도 결함 — 원인 다름, 별도 패킷.
5. 실 PDF·실모델·`hrun`·육안 검수.

## 12. 미결 — 운영자 확인 필요

1. ~~절대규칙 8-1 최종 문구~~ → **해소(2026-08-19)**: §6-5 초안 그대로 확정.
2. ~~구현자 지정~~ → **해소(2026-08-19)**: Claude 구현 예외, 설계·구현·검증 3단 신선 세션 분리(§0).
3. **factcheck 일상어 동형 예외**(§6-3): `임신`·`기사`·`정사`·`기미` 가 억제 대상 간지일 때는
   allow-set 축소가 무효다. 이 패킷은 기존 구조를 건드리지 않고 테스트 케이스로만 회피한다.
   접미 문맥이 붙은 경우(`임신년`)만 예외에서 제외하는 개선은 오탐 재발 위험이 있어 별도 판단.
4. **다인 allow-set 공유 잔여**(§7-8): 허용 토큰은 주문 단위·토큰 수준이라, 억제된 상대 A 의 연·월주가
   같은 주문의 다른 상대 B 의 실제 간지와 겹치면 허용된다. 인물별 allow-set 분리는 구조 변경이라
   이 패킷 범위 밖 — 수용 가능한 잔여인지 운영자 확인.
5. **`PartnerFacts.note`**(`calc/partner.py:129-132`)는 현재 어떤 소비처도 읽지 않는다(전수 grep 확인).
   경계일에는 "시간 미상으로 시주 제외"라는 문구가 불완전해지지만 출력에 닿지 않으므로 이번엔 두고,
   소비처가 생기면 그때 갱신 대상이다.
