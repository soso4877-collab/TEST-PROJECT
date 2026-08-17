# TASK_PACKET — 출생지 시간대·경도 배선 (birthplace-timezone-wiring-20260817)

- **task_id**: `birthplace-timezone-wiring-20260817`
- **owner**: Codex Implementer (운영자가 Claude 구현을 승인하면 Claude)
- **next_reviewer**: 신선 컨텍스트 리뷰어
- **base_commit**: `444420d`
- **rev**: 3 (rev2 이후 재개 실측 3건 반영 — §5-0 기존 팬텀 필드, §6-2 후보 라이브러리 실측, §7 감사 라벨 테스트)
- **관련 문서**: 이 패킷이 나온 세션의 조사 결론·결정·미결은
  `handoff/tasks/webapp-direction-decisions-20260817.md` 에 있다(지시문 아님, 배경 자료).

---

## 1. Goal (관측 가능한 결과 하나)

`engine.build()` 가 **출생지 시간대(IANA tz)** 를 인자로 받아 시민시각을 그 지역 시각으로
해석한다. 인자 미지정 시 현행 동작(`Asia/Seoul`)과 **바이트 단위로 동일**해야 한다.

> **범위 경계**: 이 패킷은 **엔진 계층(`input/`·`calc/`)만** 다룬다. 도시 검색 UI 와
> 지오코딩 데이터 소스는 §6 에서 **결정만 하고 구현하지 않는다**(웹앱 구성 확정 후 별도 패킷).

## 2. Background — 왜 필요한가 (실측)

### 2-1. 결함

`sajugen/input/time_correction.py:21,90` 이 시간대를 하드코딩한다.

```python
_KST = ZoneInfo("Asia/Seoul")                                  # 21행
civil = datetime(year, month, day, hour, minute, tzinfo=_KST)  # 90행
```

`longitude`/`latitude` 는 인자인데 **시간대만 인자가 없다.**

| 출생지 | 올바른 진태양시 | 엔진 산출 | 오차 |
|---|---|---|---|
| 서울 | 14:01:28 | 14:01:28 | 0 |
| 시드니 | 14:38:23 | 15:38:23 | 1시간 |
| 런던 | 13:33:01 | 05:33:02 | 8시간 |
| **뉴욕** | 13:37:30 | **익일 00:37:31** | **11시간 + 날짜** |

(측정: `tmp/_intl_probe.py`, 1990-05-20 14:30 기준)

### 2-2. 국내도 영향 — 출생지 미입력 시

웹폼(`app.py:59`)·CLI 기본값이 서울 경도 고정이라, 출생지를 넣지 않으면 전원 서울로 계산된다.
500건 표본:

| 출생지 | 서울 대비 보정차 | 시지 바뀜 | 일주 바뀜 |
|---|---|---|---|
| 부산 | +8.4분 | **9.2%** | 0.8% |
| 강릉 | +7.6분 | 8.4% | 0.8% |
| 대구 | +6.5분 | 7.2% | 0.8% |
| 울릉도 | +15.7분 | **15.8%** | 2.2% |

(측정: `tmp/_domestic_lon.py`)

### 2-3. 외부 대조 기준 — 포스텔러 만세력 2.2 (2026-08-17 실측)

동일 입력(1990-05-20 14:30, 남, 뉴욕)을 넣은 결과:

```
양 1990/05/20 14:30 남자 뉴욕
양 1990/05/20 13:33 남자 뉴욕 (지역시 +3분, 서머타임 -60분)
사주: 庚午 辛巳 乙酉 癸未
```

| | 사주 | 판정 |
|---|---|---|
| 포스텔러 | 庚午 辛巳 **乙酉 癸未** | 기준 |
| 우리(현재) | 庚午 辛巳 **丙戌 戊子** | ❌ 일주·시주 오류 |
| 우리(수정 후 목표) | 庚午 辛巳 **乙酉 癸未** | 이 패킷의 수용 기준 |

**역사적 시간대는 이미 정확하다.** `zoneinfo` 가 1957년 한국 서머타임(UTC+9:30), 1988년
서머타임(UTC+10)을 정확히 반영함을 실측 확인했다. tz 이름만 올바로 넘기면 미국·유럽
서머타임 역사도 자동으로 처리된다.

## 3. allowed_files

```
sajugen/input/time_correction.py
sajugen/calc/engine.py
sajugen/calc/partner.py
tests/test_p1.py
tests/test_birthplace_tz.py        (신규)
docs/03-engine-validation-plan.md  (결정표 행 추가)
handoff/tasks/birthplace-timezone-wiring-20260817.md
implementation-notes.md
```

`app.py`·`cli.py` 는 **이번 범위에서 제외**한다(§6-2 결정 후 별도 패킷). 엔진이 인자를
받기만 하면 소비처는 나중에 붙여도 회귀가 없다.

## 4. forbidden_files

```
sajugen/content/**      (풀이 계층 — 웹앱 구성 확정 후)
sajugen/render/**
sajugen/app.py          (UI — 별도 패킷)
sajugen/cli.py          (UI — 별도 패킷)
data/**
.env
harness/profiles/local/**
sajugen/calc/ziwei.py   (별도 패킷)
```

## 5. 구현 명세

### 5-0. 선행 확인 — 스키마에 이미 있는 미배선 필드 (2026-08-17 재개 실측)

`sajugen/models/report.py:22-27` 에 **이미 `tz` 필드가 존재한다.**

```python
class Birthplace(BaseModel):
    label: str = "서울"
    lon: float = 126.978
    lat: float = 37.566
    tz: str = "Asia/Seoul"        # ← 선언만 되어 있고 읽는 코드가 0개
```

전수 확인: `grep -rn "\.tz\b" --include=*.py sajugen/` → **0건**. `BirthInput.birthplace` 도
`tests/test_insight.py`(PII 제외 검증)에서만 쓰인다. 즉 `Birthplace` 는 docs/04 통합 스키마에만
존재하고 엔진은 `longitude`·`latitude` 를 별도 스칼라로 받으며 tz 는 하드코딩한다.

**이것이 `20_Coding-Style/팬텀-파라미터-소비처-배선.md` 가 금지하는 상태다**(선언만 있고 소비처
없음 → 값이 흐르는 착시). 그리고 `scripts/deadparam_scan.py` 는 `visit_FunctionDef`·
`visit_AsyncFunctionDef` 만 방문하므로(87·107·141·150-151행) **dataclass·pydantic 필드는
스캔 범위 밖**이다. 게이트가 못 잡는 사각이라 이 패킷에서 사람이 판정한다.

> **구현 지시**: `tz_name` 을 새로 만들되 `Birthplace.tz` 와 **이중 표현을 만들지 않는다.**
> 둘 중 하나다.
> - (가) `Birthplace.tz` 를 정본으로 두고 소비처에서 `engine.build(tz_name=bp.tz)` 로 넘긴다
>   — 단 소비처(`app.py`·`cli.py`·`order_flow.py`)는 이번 범위 밖이므로 **배선은 UI 패킷에서**.
> - (나) 이번 패킷에서는 엔진 인자만 만들고, `Birthplace.tz` 는 **손대지 않는다**(기존 팬텀 유지).
>
> 현재 안은 **(나)**. 이유: 소비처가 forbidden_files 라 같은 작업 단위에서 배선을 끝낼 수 없고,
> 반쯤 배선하면 팬텀이 하나 더 늘어난다. 대신 **UI 패킷 done_when 에 "`Birthplace.tz` 소비처
> 배선 + 분기 테스트"를 필수 항목으로 승계**한다. 이 승계를 빠뜨리면 팬텀이 영구화된다.

### 5-1. `input/time_correction.py`

`correct()` 에 `tz_name: str = "Asia/Seoul"` 인자 추가. 90행을 다음으로 교체:

```python
civil = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz_name))
```

- `CorrectedTime` dataclass 에 `tz_name: str` 필드 추가 (감사·재현용)
- 잘못된 tz 이름은 `ZoneInfoNotFoundError` 를 그대로 올린다 — **조용한 폴백 금지**
  (fail-closed, `.claude/rules/10-methodology.md` B-2)
- 모듈 상수 `_KST` 는 기본값 문서화용으로 유지하거나, 미사용이면 제거

### 5-2. `calc/engine.py`

`build()` 시그니처에 `tz_name: str = "Asia/Seoul"` 추가, 116행 `tc.correct(...)` 로 전달.
`SajuResult` 에 `tz_name` 노출(감사 라벨).

### 5-3. `calc/partner.py:153`

`tc.correct(...)` 에 `tz_name` 전달. 궁합 상대 출생지가 다를 수 있으므로 인자를 열되,
**미지정 시 본인과 동일**.

### 5-4. 도시→(경도, 위도, tz) 해석 — **이번 패킷에서 구현하지 않음**

> **rev1 폐기 사유**: rev1 은 "국내 17개 도시 상수표"를 만들라고 했으나, 포스텔러 실측 결과
> 자체 표 방식이 아님이 확인됐다. "뉴욕" 검색에 뉴욕주 20여 개 도시가 자치구 단위
> (맨해튼·브루클린·Queens·The Bronx·Staten Island)까지 나오고 한글·영문이 혼재한다 →
> 외부 지오코딩 연동. 자체 표로는 이 범위를 감당할 수 없다.

엔진은 **`longitude`·`latitude`·`tz_name` 세 값을 받기만 한다.** 이 값을 어디서 얻는지는
소비처 책임이며 §6-2 에서 방식만 결정하고 구현은 별도 패킷으로 넘긴다.

## 6. 정책 결정 (docs/03 결정표에 기록)

### 6-1. 확정

| 항목 | 결정 | 근거 |
|---|---|---|
| 경도 보정 기준 | **출생지별 실제 경도** | 천을귀인의 127.5도 고정보다 정밀. 기본값 서울 |
| 시간대 | **출생지 IANA tz** | 역사·서머타임을 tzdata 가 보증. 1957·1988 실측 확인 |
| 균시차 | **Skyfield 실제 태양 위치 유지** | 포스텔러는 경도차만 적용(뉴욕 +3분)하나 우리는 균시차 포함 → 더 정밀. 시지 판정에는 양쪽 동일 결과 |
| 남반구 절기 | **뒤집지 않음** (현행 유지) | 학설 차. 이번 범위 아님, note 로만 표기 |
| 해외 음력 | **KASI 한국 기준 유지** | 절대규칙 3. 이번 범위 아님 |

### 6-2. 미결 — 지오코딩 데이터 소스 (운영자 결정 필요)

**절대규칙 4 와 충돌 가능성이 있다.** 규칙은 KASI 에 대해 "런타임 실시간 API 의존 금지,
사전 캐싱만"을 요구한다. 같은 원칙을 지오코딩에 적용하면 런타임 외부 호출은 부적합하다.
웹앱에서는 요청마다 지연·과금·장애 지점이 추가되는 문제도 있다.

#### 6-2-a. rev2 의 오류 — "지오코딩"은 한 덩어리가 아니다

rev2 는 서로 성격이 다른 두 조회를 한 항목으로 묶어 결정을 통째로 막고 있었다.

| 단계 | 입력 → 출력 | 성격 |
|---|---|---|
| **(가) 도시 검색** | "뉴욕" → (위도, 경도) | 지명 데이터셋 + 검색 UI. 커버리지·다국어·자치구 단위가 문제 |
| **(나) tz 판정** | (위도, 경도) → `America/New_York` | 폴리곤 점포함 판정. 순수 함수, 오프라인으로 끝남 |

**(나)만 지금 결정하면 된다.** (가)는 UI 패킷 소관이고, 엔진은 세 값을 받기만 하므로
어느 쪽으로 가도 이 패킷은 재작업이 없다.

#### 6-2-b. (나) 후보 실측 — 2026-08-17, PyPI JSON API 직접 조회

| 항목 | `timezonefinder` 8.2.5 | `tzfpy` 1.3.3 |
|---|---|---|
| 코드 라이선스 | MIT | **MIT + "Anti CSDN" 부가조항** (비표준, 원문 확인 필요) |
| 번들 데이터 | timezone-boundary-builder | 동일(2026c, Douglas-Peucker 단순화) |
| **데이터 라이선스** | **ODbL** | **ODbL** |
| 배포 크기 | wheel 49.4 MB / sdist 50.7 MB | **win_amd64 wheel 약 6.1 MB** |
| 필수 의존성 | numpy≥2, h3≥4, cffi, flatbuffers (**4종**) | **0종** (pytz·tzdata 는 extra) |
| Python | ≥3.11 | ≥3.10 |
| 경계 정확도 | "border 최대 정확도" 표방 | 약 111 m (단순화 대가) |
| 구현 | Python + 선택적 numba | Rust + PyO3, 런타임 메모리 약 70 MB |

출처: `https://pypi.org/pypi/timezonefinder/json`, `https://pypi.org/pypi/tzfpy/json`,
데이터 라이선스는 상류 `github.com/evansiroky/timezone-boundary-builder` 원문 직접 확인
("The code ... is licensed under the MIT License", "The outputted data is licensed under the
Open Data Commons Open Database License (ODbL)").

#### 6-2-c. ODbL — 수익화 검토에서 반드시 확인할 것 (**미검증**)

두 후보 **모두** ODbL 데이터를 번들한다. MIT 하나로 정리되지 않는다.

ODbL 은 산출물을 **Produced Work**(데이터로 만든 결과물 — 여기서는 사주 PDF)와
**Derivative Database**(데이터셋 자체의 파생본)로 구분하고, 일반적으로 전자는 출처 표기,
후자는 동일조건 공개를 요구하는 것으로 알려져 있다. 우리 사용은 전자로 보이나 **[추정]이며
원문 대조를 하지 않았다.** 유료 서비스 개시 전에 다음을 확정한다.

1. ODbL 원문에서 Produced Work / Derivative Database 정의와 §4 의무 대조
2. 어느 화면·문서에 출처 표기를 넣을지 (PDF 본문은 절대규칙 18 로 도구 언급 금지 →
   **판매 페이지·약관 쪽**이 후보)
3. `tzfpy` 의 "Anti CSDN" 부가조항 원문 — 비표준 조항은 읽기 전 채택 금지

#### 6-2-d. 방식 비교 (갱신)

| 방식 | 장점 | 단점 |
|---|---|---|
| A. 오프라인 (나) 라이브러리 | 런타임 외부 호출 0, 절대규칙 4 정합 | ODbL 출처 표기 의무, 배포 크기 |
| B. 외부 지오코딩 API | 커버리지 최대, 유지보수 0 | 절대규칙 4 충돌, 지연·과금·장애 |
| C. 국내 표 + 해외만 API | 국내는 빠르고 안전 | 두 경로 유지 |

**권고(확정 아님)**: (나)는 **A + `tzfpy`**. 근거는 크기 8배 차·의존성 0종이며, 이미
`de440s.bsp` 32 MB 를 안고 있는 배포에 49 MB 를 더하는 것보다 유리하다. 다만 **채택 전
"Anti CSDN" 조항 원문 확인이 선결**이고, 111 m 단순화가 국경·표준시 경계 근처 출생지에서
문제가 되는지는 **미측정**이다. 조항이 걸리면 `timezonefinder`(순수 MIT 코드)로 되돌린다.

## 7. 테스트 (절대규칙 20 — 같은 작업 단위 동반)

### 필수 회귀
1. **기본값 불변**: `tz_name` 미지정 호출이 현행과 동일한 4기둥·진태양시를 낸다.
   골든 케이스 `2000-01-01 12:00 KST 남 = 己卯 丙子 戊午 戊午` 포함.
2. **골든 전수**: `tests/test_golden_sweep.py` 22건 GREEN 유지.

### 신규 (`tests/test_birthplace_tz.py`)
3. **외부 대조 (뉴욕)**: `1990-05-20 14:30`, `tz_name="America/New_York"`,
   `longitude=-74.006`, `latitude=40.713` → 사주 **`庚午 辛巳 乙酉 癸未`**
   (포스텔러 만세력 2.2 실측 일치, §2-3)
4. **해외 정합**: 런던·시드니 각 1건. 진태양시가 독립 계산값(`ZoneInfo` 변환 + 경도차)과
   **60초 이내** 일치.
5. **국내 경도**: 부산 좌표 지정 시 서울 기본값과 시지가 달라지는 케이스 1건 이상
   (경계 시각을 골라 결정론으로 고정).
6. **역사 시간대**: 1957-05-20 서울(UTC+9:30), 1988-08-15 서울(UTC+10) 보정량 회귀.
7. **fail-closed**: 존재하지 않는 tz 이름 → 예외 발생 확인 (조용한 폴백 없음).
8. **감사 라벨 비-팬텀** (§5-0): `CorrectedTime.tz_name` 이 `SajuResult.tz_name` 으로 흐르고,
   `model_dump()` 직렬화 결과에 실제 값이 담기는지 확인한다. 기본값·비기본값 **두 케이스**로
   서로 다른 값이 나오는 것까지 본다(값이 고정이면 no-op 과 구분되지 않는다).
   - 이유: `SajuResult.longitude`·`zasi_policy` 는 현재 **읽는 코드가 0개**이고 직렬화로만
     소비된다(실측: `grep -rn "\.longitude\b" sajugen/ tests/` 리더 0건). `tz_name` 을 같은
     모양으로 추가하면서 테스트가 없으면 팬텀 필드가 하나 더 늘어난다.
   - `scripts/deadparam_scan.py` 는 함수 파라미터만 보므로 이 사각을 **잡지 못한다**(§5-0).

### 실행 명령 (완료 근거)
```
./.venv/Scripts/python.exe -m pytest tests/ -q
```
통과 기준: **exit code 0**, passed 수가 기준선 **1136** 미만이 아닐 것.

## 8. done_when

- [ ] `tz_name` 미지정 경로가 기존과 동일 (회귀 1·2 통과)
- [ ] 뉴욕 케이스가 `庚午 辛巳 乙酉 癸未` 산출 (신규 3)
- [ ] 런던·시드니가 독립 계산값과 60초 이내 일치 (신규 4)
- [ ] 국내 경도 차이가 시지에 반영됨 (신규 5)
- [ ] 잘못된 tz 가 예외로 표면화됨 (신규 7)
- [ ] `tz_name` 감사 라벨이 직렬화까지 흐름, 두 값이 다르게 나옴 (신규 8)
- [ ] `Birthplace.tz` 를 건드리지 않았고, UI 패킷에 배선 의무를 승계 기록함 (§5-0)
- [ ] `pytest tests/ -q` exit 0, passed ≥ 1136
      (재개 시점 실측 기준선: **1136 passed / 4 skipped / exit 0**, 2026-08-17 `444420d`)
- [ ] `docs/03` 결정표에 §6-1 기록됨
- [ ] forbidden_files 미수정

## 9. stop_conditions

- 기본값 경로에서 골든 케이스가 하나라도 바뀌면 **즉시 중단**하고 보고
- `content/`·`app.py`·`cli.py` 수정이 필요해지면 중단 (범위 이탈)
- 지오코딩 구현이 필요해지면 중단 (§6-2 미결)
- commit·push·배포가 필요해지면 중단 (운영자 승인 사항)

## 10. 미결 — 운영자 확인 필요

**진짜 막고 있는 것은 1번 하나다.** 2·3 은 기본안이 있으므로 이의가 없으면 그대로 간다.

1. **구현 주체** — Codex 구현(AGENTS.md 기본값) vs Claude 직접 구현.
   **이것만 운영자 결정이 필요하다.**
2. **(나) tz 판정 방식** — §6-2-b 실측 완료. 권고 = **오프라인 `tzfpy`**,
   단 "Anti CSDN" 조항 원문 확인 선결. **(가) 도시 검색은 UI 패킷으로 분리** —
   이 패킷은 세 값을 받기만 하므로 어느 쪽이든 재작업 없음.
3. 뉴욕 대조값 좌표 기준 → **기본안: 우리 기준 유지**(균시차 포함, 시지 결과 동일).
   이의 없으면 확정.
4. (신규, §5-0) `Birthplace.tz` 팬텀 처리 → **기본안: 이번 패킷에서 손대지 않고
   UI 패킷에 배선 의무 승계.**

## 11. 이번 패킷에서 **하지 않는 것**

- 도시 검색 UI, 지오코딩 연동 (별도 패킷)
- `content/rules.py` 판박이 개선 (측정치 48.8%, `tmp/_repeat_rate.json`) — 웹앱 화면
  구성 확정 후
- 자미 음력 KASI 전환 — 별도 패킷
- 합·충·형·파·해·원진 산출 — 별도 패킷
  (포스텔러는 12종 탭 제공: 궁성·천간합·지지육합·지지삼합·지지방합·천간충·지지충·공망·형·파·해·원진)
- 궁성(기둥→인물/시기 매핑), 조후용신, 신강약 백분위 — 별도 검토
- 남반구 절기 정책, 해외 음력 기준

## 12. 참고 — 포스텔러 실측에서 확인된 우리 미보유 기능

이번 범위는 아니나 후속 과제 후보로 기록한다.

| 기능 | 포스텔러 | 우리 |
|---|---|---|
| 합·충·형·파·해·원진 | 12종 탭 | 공망만 |
| 신강약 백분위 | "16.82%의 사람이 여기에 해당" | 없음 |
| 궁성 | 기둥→인물·시기 매핑 | 없음 |
| 용신 | 조후 + 억부 2종 | 억부만 |
| 신살 | 기둥별 표기 11종 | 기둥별 표기 있음 |
