# TASK_PACKET — 상대 명식 절입 시각축 교정 (partner-axis-fix-20260817)

- **task_id**: `partner-axis-fix-20260817`
- **owner**: **Claude Code (이 세션)** — 운영자 지시 2026-08-17("후속 1순위 partner.py … 구현 시작")
- **next_reviewer**: **별도 신선 Claude Code 세션 (read-only)** — 구현 세션과 반드시 분리
- **base_commit**: `fae34f78900c73f33f39757e8ec3a0aeaa892355` (현재 HEAD, tree clean)
- **선행**: `solar-term-axis-fix-20260817` (CODE_PASS, 커밋 `fae34f7`) 의 이월 finding **F-2**
- **근거 문서**: `REVIEW-FEEDBACK.md` 2026-08-17 §F-2 / `sajugen/STATE.md` 재개 앵커 "[인접 사각]"
- **rev**: 2 (rev2 = §6-11 "시각 미상 × 절입 경계 교집합" 2행 추가 → 신규 테스트 20 → 28건)

---

## 0. 운영자 승인 기록 (AGENTS.md 기본값 이탈)

AGENTS.md 기본값은 **Codex 구현 → Claude 교차리뷰**다. Codex 토큰 부재로 2026-08-17 운영자가
Claude 구현 예외를 승인했고(선행 패킷 §0), 이 후속도 같은 조건에서 진행한다.

| 항목 | 값 |
|---|---|
| 승인일 | 2026-08-17 |
| 승인자 | 운영자 |
| 사유 | Codex 토큰 부재 (선행 패킷 §0 과 동일 조건) |
| 구현 | **Claude Code — 이 패킷을 작성한 세션** |
| 검증 | **별도 신선 Claude Code 세션, read-only** |
| 근거 조항 | AGENTS.md "운영자가 Claude 구현을 별도로 승인한 경우만 예외다" |

### 선행 패킷과 달라지는 경계 — 정직 고지

선행 패킷 §0 은 "이 패킷을 쓴 세션이 구현하지 않는다"를 명시했다. 이번에는 운영자가 같은 세션에
"패킷 갱신 → 구현 시작"을 지시했으므로 **작성 세션 == 구현 세션**이다. 이 이탈을 숨기지 않는다.

- 실제로 정확성을 지키는 경계는 **자기검증 금지**이므로 그쪽은 그대로 유지한다:
  **구현 세션이 자기 결과를 검증하지 않는다.** 검증은 별도 신선 세션 read-only.
- 자기작성 위험(설계 사각이 구현에 그대로 전이)의 대비: 이 패킷의 수용 기준은 **전부 기계적**이다.
  기대 간지 5행은 선행 패킷 §6 표(KASI 원본 기준, 리뷰어 재실측 완료)를 그대로 재사용하고,
  나머지는 passed 수·`RuntimeError` 0건·docstring 문자열 대조다. 리뷰어 판단력 의존도가 낮다.
- Codex 상시 금지(PDF 재생성·LLM 호출·commit·push·배포)는 **Claude 구현에도 동일 적용**한다.

---

## 1. Goal (관측 가능한 결과 하나)

**궁합 상대(`calc/partner.py`)의 연주·월주 절입 판정이 본인(`calc/myeongni.py`)과 동일 축이 되고,
축 불변식이 코드에 단일 소스로 존재한다.**

수용 지표: 선행 패킷 §6 경계 5행을 `partner_pillars` 경로로 실행해 **연·월주 오답 0건**
(현재 2건 오답), 그리고 `partner_pillars` docstring 의 "동일 경로" 주장이 사실이 된다.

## 2. Background — 결함은 하나이고 이미 특정돼 있다

### 2-1. 잔존 결함 (리뷰어 독립 확인)

`sajugen/calc/partner.py:154-157` 은 여전히 **진태양시 단일축**으로 자체 EightChar 를 만든다.

```python
ts = ct.true_solar
ec = Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute, 0).getLunar().getEightChar()
```

이 구성은 선행 리뷰의 `legacy` 프로브와 **정확히 동일**하고, 경계 5건 중 **2건 오답**이었다
(`2000-02-04 21:39` · `2000-06-05 17:58`). 즉 상쇄된 −14분 결함이 상대 명식에 그대로 남아 있다.

### 2-2. 왜 지금 고쳐야 하는가 — 축이 사람마다 다르다

`fae34f7` 이후 **본인 = 교정축 / 상대 = 미교정축**이다. 궁합 리포트는 두 명식을 나란히 놓고
십성·합충을 서술하므로, 경계 출생의 상대는 본인과 **다른 기준으로 판정된 월주**로 관계가 계산된다.
같은 리포트 안에서 축이 갈리는 상태는 단일 결함보다 나쁘다.

### 2-3. docstring 거짓화 (방법론 A-5 문서-코드 정합)

`partner.py:150-151` 의 `"calc/myeongni.build 와 동일 경로(진태양시 보정 → lunar-python EightChar)"`
는 `fae34f7` 로 **거짓이 됐다**. 문구만 고치는 것은 해결이 아니다 — 경로를 실제로 같게 만든 뒤
문구를 축 분리 사실로 갱신한다.

### 2-4. 불변식 단일 소스 (방법론 B-1)

`ct.utc + 8h` 를 partner.py 에 다시 적으면 불변식이 2곳에 복제된다. **금지.**
`LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS` 와 축 분류표(`_SplitAxisLunar`)는 한 곳에만 존재한다.

### 2-5. partner 경로는 대운을 만들지 않는다 → F-1 과 무관

`partner_pillars` 는 성별 미상으로 `getYun` 을 호출하지 않는다(모듈 도크스트링). 따라서 이월 F-1
(대운 `start_year` 달력 앵커)과 **교집합이 없다**. F-1 은 이 패킷 범위 밖(§10-1).

### 2-6. 인접 사이트 전수 분류 (작업 규율 4 — 샘플 아님, `Solar.from*` 전수 grep)

| 사이트 | 프레임 | 처분 |
|---|---|---|
| `calc/myeongni.py:112-118` | 절대축(CST) + 국지축 | `fae34f7` 교정 완료 |
| **`calc/partner.py:156`** | 진태양시 단일축 | **이 패킷의 대상** |
| `calc/three_pillar.py:163,167,177,183` | 시민 KST(=−60분 프레임) | **범위 밖(§10-2)** — 절입일 자체를 `NEEDS_INFO_TIME_BOUNDARY` 가 차단해 실오차 0(2000년 354일 불일치 0, 선행 세션 실측). 별도 판단 |
| `calc/crosscheck.py:55-70` | 절기표를 `_CHINA`(UTC+8)로 명시 정규화 | **정상** — CST 사실을 이미 올바르게 반영(`+8h` 상수의 독립 방증) |
| `sajugen/_poc.py:26-28` | 제품 경로 아님(수동 PoC 스크립트) | 범위 밖 |

## 3. allowed_files

```
sajugen/calc/partner.py
sajugen/calc/myeongni.py                 (헬퍼 공개 이름 변경 + 호출부 1행 — 아래 §5-1 한정)
tests/test_partner_axis.py               (신규)
tests/test_partner.py                    (필요 시 회귀 보강만 — 기존 단언 완화 금지)
docs/03-engine-validation-plan.md        (결정표 행: 상대 명식도 동일 축)
sajugen/STATE.md
implementation-notes.md
handoff/tasks/partner-axis-fix-20260817.md
handoff/current/manifest.json            (handoff.mjs write/validate 로만)
```

## 4. forbidden_files

```
sajugen/calc/ziwei.py            (자미 입춘 해상도 결함 = 원인 다름, 별도 패킷)
sajugen/calc/three_pillar.py     (§10-2 — 별도 판단)
sajugen/calc/solarterms.py       (Skyfield 정확, 손대지 않는다)
sajugen/calc/crosscheck.py       (정상 동작 — §2-6)
sajugen/input/time_correction.py (진태양시 산출 자체는 정상)
sajugen/gunghap.py · sajugen/content/** · sajugen/render/**
sajugen/app.py · sajugen/cli.py
tests/test_golden_sweep.py · tests/test_solar_term_axis.py   (기준선 대조용 — 무변경)
data/** · .env · harness/profiles/local/**
```

## 5. 구현 명세

### 5-1. 헬퍼 단일 소스화 (`myeongni.py` 최소 diff)

`_split_axis_eight_char` 를 **공개 이름 `split_axis_eight_char`** 로 바꾸고 내부 호출부
(`myeongni.py:220`) 1행을 갱신한다. 그 외 로직·상수·축 분류표·주석은 **무변경**.

- 이 심볼을 참조하는 곳은 내부 1곳뿐이다(전수 grep 확인: `tests/test_solar_term_axis.py` 는
  `_SplitAxisLunar` 와 `LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS` 만 참조 — 테스트 수정 불필요).
- `_SplitAxisLunar` 는 **비공개 유지**(프록시는 헬퍼 경유로만 쓰인다).
- `calc/axis.py` 신설안은 채택하지 않는다 — 불변식 주석·모듈 도크스트링이 myeongni 에 있고,
  이동은 diff 를 넓혀 골든 회귀 위험만 키운다. 조건은 "단일 소스"이며 위치는 부차적이다.

### 5-2. `partner.py` 축 교체

```python
from .myeongni import split_axis_eight_char   # 절대축(연·월) / 국지축(일·시) 단일 소스
...
ct = tc.correct(...)
ec = split_axis_eight_char(ct)
if ct.day_offset:
    ec.setSect(1)
```

- `Solar` 직접 호출과 `ts = ct.true_solar` 는 제거한다(미사용 import 도 정리 — Ruff exit 0).
- **`setSect(1)` 은 유지한다.** 프록시가 `getDay*`·`getTime*` 를 국지축으로 라우팅하므로 자시 정책은
  선행 교정 후에도 국지축에서 정확히 작동한다(myeongni.py:227 과 동일 구조).
- import 순환 없음(partner → myeongni 단방향, myeongni 는 partner 를 참조하지 않는다 — grep 확인).

### 5-3. docstring 교정 (F-2 후반부)

`partner_pillars` docstring 의 `"진태양시 보정 → lunar-python EightChar"` 를 **축 분리 사실**로
갱신한다: 연·월주 = 절대축(CST 프레임), 일·시주·자시정책 = 국지축(진태양시), 대운 미산출.
"동일 경로"라는 주장을 유지하려면 실제로 같은 헬퍼를 쓰는 사실로만 뒷받침한다.

### 5-4. 하지 않는 것

- `PartnerFacts` 필드 추가·`note` 문구 변경 (문안·factcheck 파급 — 별건)
- 상대 명식에 시각 추정·대운 산출 도입 (모듈 계약 유지)
- `gunghap.py` 호출부 시그니처 변경 (호출부 무변경으로 끝나야 한다)

## 6. 테스트 (절대규칙 20 — 같은 작업 단위 동반)

### 필수 회귀 (하나라도 어긋나면 §8 발동)

1. **골든 전수**: `tests/test_golden_sweep.py` 22건 GREEN, `pytest -k golden` **28 passed**.
2. **관계·궁합 회귀 불변**: `tests/test_partner.py tests/test_gunghap.py tests/test_raw_term_sweep.py
   tests/test_couple_language.py` → **74 passed / 0 skipped**
   (기준선 출처: `REVIEW-FEEDBACK.md:1515`). 이 묶음이 흔들리면 경계 밖 케이스가 움직인 신호다.
3. **전체**: `pytest tests/ -q` exit 0, passed **>= 1227**, skipped **== 4**, 감소 0.

### 신규 (`tests/test_partner_axis.py`)

4. **경계 5행 — 기대값은 선행 패킷 §6 표(KASI 기준) 재사용.** `partner_pillars` 로 실행해
   `year.ganzhi` · `month.ganzhi` 를 단언한다.

   | 상대 출생(서울) | 기대 연주·월주 | 현행 partner |
   |---|---|---|
   | `2000-02-04 20:41` | 己卯 丁丑 | 통과(우연) |
   | `2000-02-04 21:39` | 己卯 丁丑 | **오답 庚辰 戊寅** |
   | `2000-02-04 21:41` | 庚辰 戊寅 | 통과 |
   | `2000-06-05 17:58` | 庚辰 辛巳 | **오답 庚辰 壬午** |
   | `2000-06-05 17:59` | 庚辰 壬午 | 통과 |

5. **부분수정 차단 (−60분 재발 방지).** `20:41` 행을 4번과 **반드시 함께** 둔다. 진태양시만 걷어내고
   시민 KST 를 넘기면 이 행이 `庚辰 戊寅` 으로 틀린다. 21:39·17:58 만 있으면 완화를 감지하지 못한다
   (작업 규율 3 — 양방).
6. **본인↔상대 축 일치 불변식.** 같은 생년월일시를 `myeongni.build` 와 `partner_pillars` 에 넣어
   **연주·월주·일주 간지가 동일**함을 경계 5행 전부에서 단언한다(같은 헬퍼를 쓴다는 코드 증명).
7. **프록시 축 배정 완전성 — partner 경로 전용 스윕.** partner 가 실제로 호출하는 이름 집합은
   대운·세운·명궁 경로와 **다른 부분집합**이다(`getYear/getMonth/getDay/getTime` + `LunarUtil.SHI_SHEN`).
   시각 미상(hour=None → 정오) · 자시대(23:xx) · 경계 5행을 포함한 표본에서
   `partner_pillars` 실행 중 **`RuntimeError` 0건**.
8. **자시 정책 불변**: 자시대 상대 출생(예 `2000-06-15 23:33`)에서 `day.ganzhi` 가 정책별로
   기존 값 유지(`JST_2300` / `YAJASI_SPLIT` 양방 핀).
9. **시각 미상 경로 불변**: `hour=None` 이면 `hour_known=False` · `hour is None` 유지(3주 계약 불변).
10. **docstring 정합 자동 검사**: `partner_pillars.__doc__` 에 축 분리 사실이 있고,
    거짓 주장 문구(`진태양시 보정 → lunar-python EightChar` 형태의 단일축 서술)가 **없음**.

11. **인접 사각 — 시각 미상 × 절입 경계 교집합**(rev 2 추가, 작업 규율 4). 시각 미상은 12:00 KST 를
    대입하므로 절입이 12:00 직후인 날은 교정 전(진태양시 ~11:14 투입)과 판정이 갈린다.
    1960~2030 절입 1704건 전수 스캔 = **18건** 발생 → 대표 2건을 회귀로 고정한다.

    | 상대 출생(시각 미상) | 절입(Skyfield) | 기대 연·월주 | 교정 전 |
    |---|---|---|---|
    | `1986-02-04` | 立春 12:07:41 KST | 乙丑 己丑 | **丙寅 庚寅**(연주까지 오답) |
    | `2011-04-05` | 淸明 12:11:58 KST | 辛卯 辛卯 | **辛卯 壬辰** |

### 실행 명령 (완료 근거)

```
./.venv/Scripts/python.exe -m pytest tests/test_partner_axis.py -q
./.venv/Scripts/python.exe -m pytest tests/test_partner.py tests/test_gunghap.py tests/test_raw_term_sweep.py tests/test_couple_language.py -q
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m ruff check sajugen/calc/partner.py sajugen/calc/myeongni.py
```

교정 전 코드로 신규 테스트가 **RED 임을 먼저 확인**하고(검출력 실증), 그 수치를 구현노트에 남긴다.

## 7. done_when

- [ ] `partner.py` 가 `split_axis_eight_char` 를 사용하고 `ct.utc + 8h` 재계산·상수 복제 **0**
- [ ] 신규 테스트 4~10 전부 GREEN, 교정 전 RED 수치 기록
- [ ] `pytest -k golden` 28 passed (골든 22건 값 불변)
- [ ] 관계 4파일 묶음 **74 passed / 0 skipped** 불변
- [ ] 전체 `pytest tests/ -q` exit 0, passed >= 1227, skipped == 4
- [ ] `partner_pillars` docstring 이 축 분리 사실과 일치(§5-3)
- [ ] Ruff `All checks passed!` · `py_compile` exit 0
- [ ] `docs/03` 결정표에 "상대 명식(partner)도 동일 축" 행 추가
- [ ] forbidden_files 미수정, `gunghap.py` 무변경
- [ ] `STATE.md` 갱신 + manifest `handoff.mjs write` → `validate` = `HANDOFF_VALID`
- [ ] commit·push·LLM·PDF 재생성 **0** (운영자 승인 사항)

## 8. stop_conditions

- **골든 22건 중 하나라도 값이 바뀌면 즉시 중단·보고** (partner 경로는 골든 산출에 없어야 한다 —
  바뀌면 `myeongni.py` 편집이 최소 diff 를 넘었다는 신호).
- 관계 4파일 묶음 74 passed 가 변하면 중단·보고 (경계 밖 케이스 이동).
- 전체 passed 가 1227 미만이거나 skipped != 4 면 중단·보고.
- `gunghap.py`·`content/**` 수정이 필요하다는 결론이 나오면 중단 (계약 유지가 조건).
- `_SplitAxisLunar` 축 분류표를 넓혀야 통과한다는 결론이 나오면 **중단** — 축 배정은 설계 결정이고
  partner 경로가 새 이름을 요구하면 그 사실 자체가 보고 대상이다(조용히 확장 금지).
- 교차검증(`month_branch_crosscheck_ok`·`year_branch_crosscheck_ok`) 완화가 필요해지면 중단.
- commit·push·배포·LLM·PDF 재생성 필요 시 중단.

## 9. 근본원인 2층 (방법론 A-6)

**표면**: 상대 명식 연·월주가 절입보다 −14분 이르게 전환된다(본인은 교정, 상대는 미교정).

**감지 시스템의 구멍**: `partner.py` 에는 **교차검증이 없다**. `myeongni` 의 −14분 결함을 36/36
False 로 표면화한 `month_branch_crosscheck_ok`·`year_branch_crosscheck_ok` 가 partner 산출에는
존재하지 않아, 같은 결함이 같은 코드베이스에서 **탐지 신호 없이** 살아남았다.

→ 재발방지: 신규 테스트 6(본인↔상대 축 일치 불변식)을 상시 회귀로 둔다. partner 에 교차검증
플래그를 신설하는 방안은 **이 패킷에서 하지 않는다**(`PartnerFacts` 필드 추가 = 문안·factcheck
파급). 축 일치를 테스트로 고정하는 편이 저비용·저오탐이며, 필요성이 재확인되면 별도 판단한다.

## 10. 이 패킷에서 하지 않는 것

1. **이월 F-1 (대운 `start_year` 달력 앵커)** — `partner_pillars` 는 대운을 산출하지 않아 교집합이
   없다(§2-5). 또한 앵커를 시민축으로 둘지는 **유파 판단 + `docs/03` 결정표 변경 = 운영자 승인**
   사항이다. 정책 결정 전에 `start_year` 회귀 핀을 넣으면 **틀릴 수 있는 값을 골든으로 동결**하는
   change-detector 가 된다(방법론 B-3). → 별도 패킷.
2. **`three_pillar.py` 의 −60분 프레임** — 가드가 절입일을 차단해 실오차 0(§2-6). 별도 판단.
3. **자미두수 입춘 해상도 결함** — iztro API 한계, 원인 다름. 별도 패킷 + 설계 결정.
4. `PartnerFacts` 스키마·note 문구 변경, 상대 대운 산출, `gunghap.py` 계약 변경.
5. 실 PDF·실모델·`hrun`·육안 검수 (이 패킷 요구 아님).

## 11. 미결 — 운영자 확인 필요

1. **§0 자기작성 이탈 수용 여부** — 작성 세션 == 구현 세션(검증만 분리). 운영자 지시에 따른 것이라
   그대로 진행하지만 기록으로 남긴다.
2. **F-1 을 이번 범위에서 제외**하는 판단 동의 여부(§10-1).
