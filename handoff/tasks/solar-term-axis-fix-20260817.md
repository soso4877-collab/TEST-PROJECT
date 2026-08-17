# TASK_PACKET — 명리 절입 판정 시각축 교정 (solar-term-axis-fix-20260817)

- **task_id**: `solar-term-axis-fix-20260817`
- **owner**: Codex Implementer (운영자가 Claude 구현을 승인하면 Claude)
- **next_reviewer**: 신선 컨텍스트 리뷰어
- **base_commit**: `444420d`
- **rev**: 1
- **근거 문서**: `handoff/evidence/20260817-postteller-chart-survey/solar-term-axis-defect.md`
  (지시문 아님, 배경·실측 자료)

---

## 1. Goal (관측 가능한 결과 하나)

**연주·월주의 절입 판정이 실제 절기 시각(KASI·Skyfield 기준)과 분 단위로 일치한다.**

수용 기준 단일 지표: `eot-window-measure.py` 재실행 시 36개 절입의 불일치 창 폭이
**전부 0분** (현재 평균 27.7분 / 최대 41분+).

## 2. Background — 결함은 **두 개**이고 서로 상쇄되고 있었다

### 2-1. 실측된 오차

| | 실제 절기 (KASI) | 우리 전환 | 오차 |
|---|---|---|---|
| 2000 입춘 | 02-04 **21:40:00** KST | 21:27 | **−13분** |
| 2000 망종 | 06-05 **17:59:00** KST | 17:30 | **−29분** |

입춘 8개년 전수: 오차 **−13 ~ −14분**, 편차 거의 없음.

### 2-2. 원인 분해 — 여기가 핵심이다

**결함 A. lunar-python 의 절기표는 중국 표준시(UTC+8)다.**

시민 KST 를 그대로 먹이면 입춘이 **20:41** 에 뒤집힌다. 그 값은 입춘의 CST 표기(20:40:22)다.
→ KST 기준으로 **−60분** 오차.

```
Solar.fromYmdHms(2000,2,4,20,41,0) → 연주 己卯 → 庚辰 전환
입춘 KST 21:40:22 / 입춘 CST 20:40:22
```

**결함 B. 진태양시를 시민시각처럼 넘긴다** (`calc/myeongni.py:144-147`).

```python
ts = ct.true_solar                    # 경도차 + 균시차 보정 완료
solar = Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute, ...)
ec = solar.getLunar().getEightChar()  # ← 4기둥 전부를 이 축에서 뽑는다
```

2월 서울 보정량 −45.94분 → **+45.94분** 만큼 전환을 늦춘다.

**합계: −60 + 45.94 = −14.06분** — 실측 −13~−14분과 정확히 일치한다.

> ### ★ 가장 중요한 경고
> **결함 B 만 고치면(진태양시 대신 시민 KST 투입) 오차가 −60분으로 더 나빠진다.**
> 두 결함이 우연히 상쇄되고 있었다. **A 와 B 를 같이 고쳐야 한다.**

### 2-3. 왜 진태양시를 절입에 쓰면 안 되는가

절기는 태양 황경이 특정 각도가 되는 **절대 시각**이다. 관측지 경도·균시차와 무관하다.
서울에서 태어나든 뉴욕에서 태어나든 입춘 순간은 같은 물리적 순간이다.

반면 **시지(時支)** 는 태양의 실제 시각각 문제이므로 진태양시가 맞다. 축을 분리해야 한다.

### 2-4. 검증된 수정 방향

lunar-python 에 **`ct.utc + 8h`(= CST 프레임)** 를 넘기면 절입이 정확해진다. 실측:

| 대상 | `utc+8h` 투입 시 전환 | 실제 절기 |
|---|---|---|
| 2000 입춘 | **21:41** | 21:40:22 ✔ |
| 2000 망종 | **17:59** | 17:59:00 ✔ |

포스텔러 만세력 2.2 의 전환 시각(21:41)과도 일치한다.

### 2-5. 영향 범위 실측 (`fix-impact.json`)

랜덤 3,000건에서 현행 축 vs 수정 축 비교:

```
연주 변경                 0 건
월주 변경                 0 건
대운 시작연도 변경       17 건  (0.57%)
```

4기둥은 경계가 좁아 랜덤 표본에서 안 바뀌지만 **대운수는 0.57% 에서 바뀐다.**
`getYun()` 이 절입까지의 거리로 대운수를 내므로 14분 이동이 하루 경계를 넘길 수 있다.

> **운영자 확인 필요**: 이미 발급한 리포트가 있다면 그 고객의 대운수가 바뀔 수 있다.
> 발급 이력 대조는 이 패킷 범위 밖이다.

## 3. allowed_files

```
sajugen/calc/myeongni.py
tests/test_p1.py
tests/test_solar_term_axis.py          (신규)
docs/03-engine-validation-plan.md      (결정표 행 추가)
handoff/tasks/solar-term-axis-fix-20260817.md
implementation-notes.md
```

## 4. forbidden_files

```
sajugen/calc/ziwei.py         (자미도 결함 있으나 원인이 다름 — 별도 패킷)
sajugen/calc/solarterms.py    (Skyfield 계산은 이미 정확 — 손대지 않는다)
sajugen/input/time_correction.py  (진태양시 산출 자체는 정상)
sajugen/content/**
sajugen/render/**
sajugen/app.py · sajugen/cli.py
data/**  ·  .env  ·  harness/profiles/local/**
```

## 5. 구현 명세

### 5-1. 축 분리 — `myeongni.build`

lunar-python EightChar 를 **두 축에서** 만들고 기둥별로 골라 쓴다.

| 산출 | 축 | 이유 |
|---|---|---|
| **연주 · 월주** | `ct.utc + 8h` (CST) | 절입 = 절대 시각. lunar-python 절기표가 CST 라 이 프레임이 정본 |
| **일주 · 시주** | `ct.true_solar` (현행 유지) | 자시 경계·시지는 국지 태양시 문제. 현행이 정당 |
| **대운 (`getYun`)** | `ct.utc + 8h` (CST) | 절입까지의 거리로 산출 → 절입 축과 같아야 함 |

`ct.day_offset` 에 따른 `setSect(1)` 은 **일주·시주 인스턴스에만** 적용한다
(자시 정책은 국지 시각 축의 문제다).

```python
# 예시 골격 — 구현자가 프로젝트 스타일에 맞춰 정리
ts = ct.true_solar                                  # 국지 축(일주·시주)
cst = ct.utc.replace(tzinfo=None) + timedelta(hours=8)   # 절대 축(연주·월주·대운)

ec_local = Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute,
                            ts.second or 0).getLunar().getEightChar()
if ct.day_offset:
    ec_local.setSect(1)                             # 자시 정책 — 국지 축에만
ec_abs = Solar.fromYmdHms(cst.year, cst.month, cst.day, cst.hour, cst.minute,
                          cst.second or 0).getLunar().getEightChar()

pillars = {
    "Year":  _pillar(ec_abs,   "Year"),
    "Month": _pillar(ec_abs,   "Month"),
    "Day":   _pillar(ec_local, "Day"),
    "Time":  _pillar(ec_local, "Time"),
}
yun = ec_abs.getYun(1 if is_male else 0, 1)         # 대운도 절대 축
```

- **`+8h` 를 매직넘버로 두지 않는다.** 명명 상수 + "lunar-python 절기표는 CST(UTC+8)" 근거
  주석 필수. 이 사실이 코드에서 사라지면 다음 사람이 다시 −60분을 만든다.
- 축이 두 개라는 사실 자체를 주석으로 남긴다(불변식: 절입=절대축 / 시지=국지축).

### 5-2. 교차검증 정합

`myeongni.py:193-201` 의 Skyfield 교차검증은 **이미 절대 UTC** 를 쓴다. 수정 후에는
주 산출과 같은 축이 되므로 **경계에서도 일치해야 한다**(현재는 36/36 불일치).

`month_branch_crosscheck_ok` / `year_branch_crosscheck_ok` 를 **약화·삭제하지 말 것.**
이 검사가 결함을 잡아준 유일한 장치다. 통과하게 만드는 것이지 없애는 것이 아니다.

### 5-3. 하지 않는 것

- `ZasiPolicy` 의미 변경 (외부 대조로 정합 확인됨 — `results-measured.md` §13)
- 시지·자시 축 변경 (유파 차이이고 우리가 정당)
- 대운수 관례(만나이 vs 세는나이) 변경 — §10 미결

## 6. 테스트 (절대규칙 20 — 같은 작업 단위 동반)

### 필수 회귀

1. **골든 전수**: `tests/test_golden_sweep.py` **22건(현행 28 수집)** GREEN 유지.
   하나라도 바뀌면 **즉시 중단·보고** (§7).
2. **전체**: `pytest tests/ -q` exit 0, passed **≥ 1136**.

### 신규 (`tests/test_solar_term_axis.py`)

3. **절입 정확도 — KASI 기준 대조.** 기준값 출처 `kasi-terms-2000.json`
   (KASI 원본, Skyfield 와 분 단위 일치 확인됨). **아래 표는 3개 경로를 실측한 값이다** —
   구현자는 `fixed` 열을 기대값으로 쓴다.

   | 출생 (서울) | 현행(진태양시) | B만 수정(시민 KST) | **fixed (`utc+8h`)** | 정답 |
   |---|---|---|---|---|
   | `2000-02-04 20:41` | 己卯 丁丑 ✔ | **庚辰 戊寅 ✘** | 己卯 丁丑 | 己卯 丁丑 |
   | `2000-02-04 21:39` | **庚辰 戊寅 ✘** | **庚辰 戊寅 ✘** | 己卯 丁丑 | 己卯 丁丑 |
   | `2000-02-04 21:41` | 庚辰 戊寅 ✔ | 庚辰 戊寅 ✔ | 庚辰 戊寅 | 庚辰 戊寅 |
   | `2000-06-05 17:58` | **庚辰 壬午 ✘** | **庚辰 壬午 ✘** | 庚辰 辛巳 | 庚辰 辛巳 |
   | `2000-06-05 17:59` | 庚辰 壬午 ✔ | 庚辰 壬午 ✔ | 庚辰 壬午 | 庚辰 壬午 |

   `21:39` 와 `17:58` 은 **현행에서 실패한다** — 이 결함을 직접 겨냥한 앵커다.

4. **부분 수정 차단 (−60분 재발 방지) — `2000-02-04 20:41`**
   진태양시만 걷어내고 시민 KST 를 넘기면(=결함 B 만 수정) 이 케이스가 `庚辰 戊寅` 으로
   **틀린다**. 정답은 `己卯 丁丑` 이다.
   **현행 코드는 이 케이스를 통과하므로, 이것만으로는 결함을 못 잡는다.**
   3번의 `21:39`·`17:58` 과 **반드시 함께** 둬야 양방(결함 검출 + 부분수정 차단)이 성립한다.
   (작업 규율 3 — 한쪽만 있는 테스트는 완화를 감지하지 못한다)
5. **축 분리 불변식**: 같은 출생에서
   - 경도만 바꾸면(서울↔울릉도) **연주·월주는 불변**, 시지는 바뀔 수 있다
   - 이것이 "절입은 절대 시각" 의 코드 증명이다
6. **교차검증 정합**: 위 3·4·5 전 케이스에서
   `month_branch_crosscheck_ok` 와 `year_branch_crosscheck_ok` 가 **True**.
7. **절입 창 폭 0**: 최소 3개 절입에 대해 절입 ±40분을 1분 간격으로 훑어
   교차검증 False 가 **0건**.
8. **대운 축 정합**: 대운수가 절입 거리에서 나오므로, 절입 직전/직후 1분 차이 케이스에서
   대운수가 **결정론으로 고정**됨을 확인(값 하드코딩이 아니라 두 호출이 같은 값을 내는지).
9. **자시 정책 불변**: `JST_2300` / `YAJASI_SPLIT` 각각에서
   `2000-06-15 23:33` 이 `乙巳` / `甲辰` 로 나오는 기존 동작 유지
   (외부 대조 확인값 — `results-measured.md` §13).

### 실행 명령 (완료 근거)

```
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe handoff/evidence/20260817-postteller-chart-survey/eot-window-measure.py
```

두 번째 명령의 `summary.width_min_max` 가 **0** 이어야 한다.

## 7. done_when

- [ ] 골든 22건 불변 (바뀌면 중단·보고)
- [ ] `pytest tests/ -q` exit 0, passed ≥ 1136
- [ ] 신규 테스트 3~9 전부 GREEN
- [ ] `eot-window-measure.py` 의 `width_min_max == 0` (현재 41+)
- [ ] `+8h` 근거가 명명 상수 + 주석으로 코드에 남음
- [ ] `month_branch_crosscheck_ok`·`year_branch_crosscheck_ok` 완화·삭제 0
- [ ] `docs/03` 결정표에 "절입=절대축(CST) / 시지=국지축(진태양시)" 행 추가
- [ ] forbidden_files 미수정
- [ ] **대운수 0.57% 변동**을 보고서에 명시 (숨기지 말 것)

## 8. stop_conditions

- **골든 22건 중 하나라도 값이 바뀌면 즉시 중단·보고.** 경계 밖 케이스는 안 바뀌어야 한다
  (실측 근거: 랜덤 3,000건에서 연주·월주 변경 0건).
- `ziwei.py` 수정이 필요해지면 중단 (별도 패킷)
- 교차검증을 완화해야 통과한다는 결론이 나오면 중단 (방향이 거꾸로다)
- 대운수 변동이 0.57% 를 크게 벗어나면 중단·보고 (다른 것을 건드린 신호)
- commit·push·배포·LLM·PDF 재생성 필요 시 중단 (운영자 승인 사항)

## 9. 근본원인 2층 (방법론 A-6)

**표면**: 연주·월주가 절입보다 13~14분 이르게 전환된다.

**감지 시스템의 구멍**: 교차검증(`month_branch_crosscheck_ok`)은 **정상 작동했다.**
36개 절입 전부에서 False 를 냈다. 그런데도 3주 이상 안 잡힌 이유는

1. 경계 폭이 좁아(연 0.063%) 랜덤 골든·스윕에 안 걸렸다 —
   `sweep100c.json` 100건에서 0건
2. False 가 떠도 **어느 쪽이 맞는지 알려주지 않아** 운영자가 판단할 수 없었다
3. **두 결함이 상쇄돼** 오차가 −60분이 아니라 −14분으로 작아 보였다

→ 재발방지: 신규 테스트 7(절입 ±40분 전수 스캔)을 상시 회귀로 둔다. 랜덤 표본이 아니라
**경계를 직접 겨냥**해야 잡힌다. `docs/16` 품질사고 장부에 기록한다.

## 10. 미결 — 운영자 확인 필요

1. **구현 주체**: Codex(AGENTS.md 기본값) vs Claude 직접
2. **대운수 0.57% 변동 수용 여부** — 발급 이력이 있으면 소급 영향. 이력 대조는 범위 밖
3. **대운수 관례**: 포스텔러는 우리보다 **항상 +1**(2건 실측, `results-measured.md` §4).
   코드 주석은 "한국 관행=만나이, 레퍼런스 만세력 일치"라고 주장한다.
   **이 패킷에서 바꾸지 않는다.** 별도 전수 검증 후 판단
4. **`docs/16` 등재**: 품질사고로 기록할지(권고: 등재)

## 11. 이 패킷에서 하지 않는 것

- **자미두수 입춘 해상도 결함** — iztro 가 분을 받지 않아 최대 103분/평균 55.5분 오차.
  원인이 다르고 라이브러리 API 한계다. **별도 패킷 + 설계 결정 필요**
  (`solar-term-axis-defect.md` §6-5)
- 출생지 tz 배선 (`birthplace-timezone-wiring-20260817`)
- 자정 구간 진태양시 날짜 밀림의 정당성 검증 (36표본 중 21건 발생, 미검증)
- 절대규칙 7 의 `±2분` 변경 — **실측 결과 그대로 두는 것이 맞다**
  (Skyfield↔KASI 절기 차이 669/672행 2분 이내)
- `CALC_MISMATCH` 화면에 판정 근거 표시 (별도 개선, `defect.md` §6-3)
