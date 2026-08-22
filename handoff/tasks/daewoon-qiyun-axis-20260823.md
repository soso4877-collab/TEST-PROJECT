# TASK_PACKET — 대운 起運 산출을 lunar-python 에서 회수해 docs/03 확정 축으로 자체 계산 (daewoon-qiyun-axis-20260823)

- **task_id**: `daewoon-qiyun-axis-20260823`
- **owner**: **Codex 구현자** (AGENTS.md 기본 사이클)
- **next_reviewer**: **Claude Code 교차리뷰** (read-only, 구현 세션과 분리)
- **base_commit**: manifest `base_commit` 참조 (docs/03·docs/27·research-ledger 등재 커밋)
- **근거**: `docs/16` QI-2026-08-17-01 이월 **F-1** → 조사 `docs/27` → 운영자 O1 확정(2026-08-23) → `docs/03` 「대운 起運 산출 축」 행
- **rev**: 1

---

## 0. 역할·금지

Codex 상시 금지(PDF 재생성 · LLM/Anthropic API 호출 · git commit · push · 배포)는 그대로다. 커밋은 운영자가 checkpoint 로 직접 한다.
검색 시 ignored 영역 제외 글롭 필수: `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`.
`calc/` 변경이므로 **골든 22건 포함 전체 GREEN 없이는 완료가 아니다**(절대규칙 20).

## 1. Goal (관측 가능한 결과 하나)

**대운수(起運 년수)·대운 `start_year`·세운/월운 선택이 `docs/03` 확정 축으로 계산되고, 동일 출생의 결과가 lunar-python
절기표 프레임(CST)에 더 이상 의존하지 않는다.** 구체적으로: 거리 = 출생 UTC ↔ Skyfield 절입(초), 시진 버킷 = 시주와
같은 `ct.hour_branch`, 앵커·birth_year = `ct.civil_local`, 折除 = 3日1歲·1日4月·1時辰10日, 나머지 내림.

## 2. Background — 실측 (2026-08-22~23, read-only)

### 2-1. 현행 경로
```
calc/myeongni.py:244   yun = ec.getYun(1 if is_male else 0, 1)        # lunar 流派1
calc/myeongni.py:249   qiyun = yun.getStartYear()
calc/myeongni.py:255   start_year=d.getStartYear()                      # lunar DaYun(CST 프레임 앵커)
calc/myeongni.py:300   seun, worun = advanced.seun_worun(yun, ref_year) # lunar DaYun start/end 로 현재 대운 선택
calc/myeongni.py:309   daewoon_count=yun.getStartYear()
```
`ec` 는 `_SplitAxisLunar` 프록시라 `getYun` 은 절대축(CST) Lunar 에 배정돼 있다. 그래서 lunar `Yun.__compute_start` 가
(a) 거리 끝점 ✔ (b) 시진 버킷 ✘(CST 시진) (c) 달력 앵커 ✘(CST 날짜) 를 모두 CST 로 계산한다(`docs/26` §3-2, `docs/16` 정정 블록).

### 2-2. 프로브(docs/27 §2, 25,440건)
현행↔국지축 시진 `start_year` 불일치 **0.53%**(136건), 대운수 0.59%. 00시대 잔차(12건)는 (c) 앵커. 부록 C: 분 변화 무관(0.44%),
부산 1.06%(경도 보정이 작을수록 현행과 간격이 커짐) — **변동률은 출생지 경도에 비례**하므로 §6 변동 보고는 서울 기준으로 읽는다. 流派2 도 프레임 불변 아님(거리
60분 틀어짐) → 거리는 절대축 유지가 물리적으로 맞다.

### 2-3. 대운 간지는 起運과 무관
`lunar DaYun.getGanZhi()` = 월주 간지 ± index. 월주는 절대축이고 교정 완료 상태라 **간지열은 그대로 쓴다**(이관 대상은 起運 수·연도만).
`daewoon_forward` 판정(`myeongni.py:266-269`)도 무수정.

### 2-4. 세운·월운 결합
`advanced.seun_worun(yun, ref_year)` 은 lunar `DaYun.getStartYear()<=ref<=getEndYear()` 로 현재 대운을 고른 뒤 `LiuNian/LiuYue`
를 노출한다. 起運이 바뀌면 **같은 ref_year 에서 lunar 와 우리 `daewoon` 이 다른 대운을 가리킬 수 있다** → 세운 연도 집합이
어긋난다. 세운 간지(연간지)·월운 간지(월간지)는 起運과 무관한 달력값이므로, **현재 대운 선택만 우리 `start_year` 로 바꾸고**
간지는 lunar 연·월 간지 조회로 유지한다.

## 3. 변경 설계

### 3-1. 신규 함수 `calc/myeongni.py: compute_qiyun(ct, *, forward) -> QiyunResult`
```
입력: ct: CorrectedTime, forward: bool(daewoon_forward)
1) 절입 시각: forward 면 출생 UTC 이후 첫 12節, 역행이면 직전 12節 — solarterms.solar_term_time/TWELVE_JIE 로 (y-1,y,y+1) 후보 중 선택.
   month_pillar_branch(dt_utc) 가 '직전 절' 을 이미 주므로 역행은 그것을 재사용, 순행은 같은 후보 목록에서 dt_utc 초과 최소값.
2) 거리: start/end = 절대축 시각(UTC 그대로. CST 환산 불필요 — 차이는 불변).
   day_diff  = (end.date - start.date) 달력 일수  ← 고전 '日' (三命通會: 巳時→다음날 巳時 = 1日)
   hour_diff = 절입 時辰 idx − 출생 時辰 idx      ← 時辰 idx 는 국지축:
       출생 時辰 = ct.hour_branch (진태양시·자시정책 반영, 23시=子)
       절입 時辰 = 절입 UTC 를 ct 와 **같은 방식**으로 진태양시 환산한 시각의 시진
                  (input/time_correction 의 진태양시 변환을 함수로 노출해 재사용 — 복제 금지; 경도 = ct.longitude)
   hour_diff < 0 → hour_diff += 12, day_diff -= 1   (lunar 와 동일 자리올림)
   month = day_diff*4 + hour_diff*10 // 30 ; day = hour_diff*10 − (hour_diff*10//30)*30
   year  = month // 12 ; month %= 12                 ← 내림(현행 유지, docs/03)
3) 앵커: start_solar = ct.civil_local + year 년 + month 월 + day 일 (달력 가산, lunar getStartSolar 와 같은 순서)
   birth_year = ct.civil_local.year
   daewoon[i].start_year = start_solar.year + 10*i (i=0..7)
반환: QiyunResult(years=year, months=month, days=day, start_date=date, jie_name, jie_utc, hour_diff, day_diff)
```
주의 — **일수 정의**: lunar `Solar.subtract` 는 달력 일수 차(시각 무시). 고전도 "巳時→巳時=1日" 이므로 달력 일수 + 시진 차로 두 단위를
분리해 센다. 초 단위 거리를 4320분=1년으로 환산하는 流派2 방식을 쓰지 마라(docs/03 은 流派1 折除 확정).
주의 — **날짜의 축**: day_diff 는 국지축 날짜로 센다(출생 진태양시 날짜 ↔ 절입 진태양시 날짜). 절입 시각 자체는 절대(UTC)지만 그
순간을 같은 경도의 진태양시로 표현해 출생 시각과 같은 시계에서 日·時辰을 센다 — 한 시계에서만 세야 자리올림이 일관된다.

### 3-2. `build()` 배선
- `yun = ec.getYun(...)` 은 **간지열·방향 판정용으로만 유지**. `qiyun`·`start_year`·`daewoon_count` 는 `compute_qiyun` 결과로 교체.
- `advanced.seun_worun(yun, ref_year)` → 시그니처를 `seun_worun(yun, ref_year, daewoon)` 로 바꾸고 현재 대운 선택을 우리
  `daewoon` 의 `start_year` 로 한다(`current_daewoon` 과 동일 규칙 재사용 — 복제 금지). 세운 연도 범위 `ref-1..ref+3` 과 월운은
  lunar `LiuNian/LiuYue` 대신 `Lunar.fromYmd(yy,6,1).getYearInGanZhiExact()` 류의 연간지·월간지 조회로 만든다. **간지 결과가 교정
  전과 동일한지** 회귀로 고정(변해야 할 것은 '어느 해가 현재 대운에 속하는가' 뿐).
- `Myeongni.daewoon_count` 의미 불변(起運 년수 = 만 나이 대운수).

### 3-3. 하지 않을 것
- 대운 **간지열**·`daewoon_forward`·연주/월주/일주/시주·`_SplitAxisLunar` 축 분류표 **무수정**.
- `month_branch_crosscheck_ok`·`year_branch_crosscheck_ok` **완화·삭제 금지**.
- `docs/03` 행 재해석 금지(나머지 반올림·流派2 도입 등은 별도 운영자 결정).
- 상대 명식(`calc/partner.py`)은 대운 미산출 — 무수정.
- `content/`·`render/` 는 무수정. `factcheck` 허용 토큰은 `Myeongni.daewoon` 을 소비하므로 인터페이스 불변이면 자동 추종.

## 4. 파일 경계

**allowed_files**
```
sajugen/calc/myeongni.py            (compute_qiyun 신설 + build 배선)
sajugen/calc/advanced.py            (seun_worun 현재 대운 선택 교체)
sajugen/input/time_correction.py    (진태양시 변환 함수 공개 노출만 — 기존 correct() 동작 불변)
tests/test_daewoon_qiyun_axis.py    (신설: 양방 앵커·반사실·세운 정합)
tests/test_golden_sweep.py          (:221 구조 불변식에 축 단언 추가만 — 기존 단언 완화 금지)
implementation-notes.md / sajugen/STATE.md
```
**forbidden**: 위 외 전부. 특히 `calc/solarterms.py`(읽기만)·`calc/partner.py`·`content/**`·`render/**`·`docs/**`·
`handoff/current/manifest.json`·`config/**`·`harness/profiles/local/**`(비열람). 경계 밖 필요 시 `BLOCKED_CONTRACT`.

## 5. 수용 기준 — 양방 테스트 (작업 규율 3)

`tests/test_daewoon_qiyun_axis.py` 신설. PII 0(합성 날짜만).

**(가) 정상 통과 — 불변 확인**
1. 골든 `test_golden_sweep.py` 22건 + `_NAMED` 7건 GREEN. 단 `_NAMED` 의 대운수 7개는 **스냅샷**이라(docs/16) 값이 바뀌는 케이스가
   나오면 **고치지 말고 정지 보고**(어느 건이 왜 바뀌는지 三命通會 방식 손계산 첨부). docs/27 예측: 7건 모두 (qiyun,start_year) 세 축
   동일이라 **바뀌지 않아야 한다**.
2. 대운 간지열·방향: 격자 전수에서 교정 전후 동일(교정 전 값은 `git stash` 없이 — lunar `DaYun.getGanZhi()` 직접 호출과 대조).
3. 세운·월운 **간지**: 격자 전수에서 교정 전후 동일(연도 집합만 달라질 수 있음 — 달라진 건수 보고).
4. `start_age == daewoon_count + 10i`, `start_year == start_year[0] + 10i` 불변식 유지(:212-221).

**(나) 결함 차단 — 축이 실제로 바뀌었음을 실증**
5. **양방 앵커 4건**(docs/27 부록 B 방법으로 추출: 홀수시 2·00시 1·짝수시 1): 기대 대운수·`start_year` 를 **三命通會 방식 손계산**
   (출생 時辰→절입 時辰 日·時辰 세기, 도크스트링에 과정 기재)으로 적는다. 교정 전 코드는 이 4건 중 최소 3건 **RED** 여야 한다 —
   교정 전 실행 출력을 보고에 첨부(RED 실증 의무).
6. **반사실 불변식**: 같은 출생을 `correct()` 에 넣고 `ct.utc` 를 ±1h 시프트한 가짜 CST 프레임으로 `compute_qiyun` 을 다시 부르면
   결과가 **달라져야**(거리가 바뀌므로) 하고, 반대로 `hour_branch` 만 같은 채 `civil_local` 표기를 바꿔도(앵커 연도 불변 범위 내)
   `years/months/days` 는 **불변**이어야 한다 — 세 역할(거리/버킷/앵커)이 분리됐음을 단언.
7. **23시 특례 제거**: 진태양시 23:30 출생(자시 정책 JST_2300 → `hour_branch='子'`) 의 起運 時辰 idx 가 0(子)이지 11(亥)이 아님을
   단언(lunar 流派1 과 다른 지점).
8. **세운 정합**: `current_daewoon(m, ref)` 가 가리키는 대운과 `seun` 연도 집합이 같은 대운 구간 안에 있음을 격자 전수 단언.
9. `:221` 에 축 단언 추가: `d.start_year - ct.civil_local.year == d.start_age + {0,1}` (내림 折除 + 달력 가산이면 잔차는 0 또는 1.
   2 는 CST 앵커 잔재였다) — 기존 `0..2` 단언은 **남겨 두고** 더 좁은 단언을 **추가**한다(완화 금지).

## 6. 검증 명령 (전부 실행 · 증거 필수)
```
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m pytest tests/test_golden_sweep.py tests/test_daewoon_qiyun_axis.py tests/test_solar_term_axis.py -q
./.venv/Scripts/python.exe -m ruff check sajugen/calc/myeongni.py sajugen/calc/advanced.py sajugen/input/time_correction.py tests/test_daewoon_qiyun_axis.py
```
- 기준선(2026-08-22) = **1280 passed / 4 skipped / exit 0**, 수집 1284. 환경차 규칙(AGENTS.md §10): 구현환경은 Playwright skip 28 더 많음.
- 추가 보고: 격자 전수에서 교정 전후 `start_year` 가 바뀐 건수·비율(docs/27 예측 0.5% 내외). **크게 벗어나면 정지 보고**.

## 7. 정지 조건
- `_NAMED` 대운수 스냅샷이 바뀜 / 양방 앵커 손계산과 구현이 불일치 / `month_branch_crosscheck_ok` 실패 발생 / allowed 밖 수정 필요 /
  교정 전후 `start_year` 변동이 2% 초과 → 모두 **정지 후 실측 보고**.

## 8. 산출물
`CODEX_IMPLEMENTATION_REPORT`(`implementation-notes.md` 최상단): 명령+출력, RED 실증, 변동 건수표, 손계산 4건, 미검증 분리. 커밋 금지.
