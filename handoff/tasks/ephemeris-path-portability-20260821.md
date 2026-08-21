# TASK_PACKET — 천체력 경로 하드코딩 제거 (ephemeris-path-portability-20260821)

- **task_id**: `ephemeris-path-portability-20260821`
- **owner**: **Codex 구현자** (AGENTS.md 기본 사이클. 토큰 부재 시 운영자 승인 후 Claude 신선 세션 대체 — §0)
- **next_reviewer**: **Claude Code 교차리뷰** (read-only, 구현 세션과 분리)
- **base_commit**: `b821602` (현재 HEAD, tree clean, branch `codex/gunghap-relationship-quality`)
- **근거 문서**: `docs/26-engine-eval-2026-08-20.md` §4-1·§5 / 이 패킷 §2 의 2026-08-21 설계 세션 실측
- **rev**: 1

---

## 0. 역할 배정

AGENTS.md 기본값 = **Codex 구현 → Claude 교차리뷰**다. 이 패킷은 기본값을 그대로 쓴다.
Codex 토큰 부재로 구현자를 바꿔야 하면 **운영자 승인을 먼저 받고** 이 절에 기록한다
(선행 `solar-term-axis-fix-20260817`·`partner-unknown-time-boundary-20260818` 과 동일 절차).

Codex 상시 금지(PDF 재생성 · LLM/Anthropic API 호출 · git commit · push · 배포)는 그대로 적용된다.
커밋은 운영자가 checkpoint 로 직접 한다.

---

## 1. Goal (관측 가능한 결과 하나)

**천체력(de440s.bsp) 디렉터리를 패키지 상대 경로로 해석해, 저장소를 다른 경로·다른 OS 로 옮겨도
`sajugen.calc.solarterms` 와 `sajugen.input.time_correction` 의 import 가 성공한다.**

수용 지표: 두 모듈 어디에도 절대경로 리터럴이 없고, 천체력 디렉터리 상수가 **단일 소스**이며,
전체 pytest 가 기준선 이상으로 GREEN(골든 22건 포함).

## 2. Background — 실측 (2026-08-21 설계 세션, read-only)

### 2-1. 결함 문장 (2곳, 동일 결함)

```
sajugen/calc/solarterms.py:18       _loader = Loader(r"C:\Users\pc\test-project\sajugen\assets\ephemeris")
sajugen/input/time_correction.py:22 _EPHEM_DIR = r"C:\Users\pc\test-project\sajugen\assets\ephemeris"
```

둘 다 **모듈 로드 시점**에 실행된다(`_eph = _loader("de440s.bsp")` 가 import 부작용).
따라서 경로가 틀리면 함수 호출 전에 import 단계에서 깨진다.

### 2-2. 범위 확정 — 제품 코드에서는 이 2곳뿐

git 추적 대상 `*.py` 전수 스캔(`C:\Users` 리터럴):

| 경로 | 추적 | 판정 |
|---|---|---|
| `sajugen/calc/solarterms.py:18` | 추적 | **대상** |
| `sajugen/input/time_correction.py:22` | 추적 | **대상** |
| `sajugen/_poc.py:10` | **gitignore**(`.gitignore:67` `_[!_]*.py`) | 범위 밖 |
| 루트 `_h151_*.py`~`_h1532_*.py` 8개 | **gitignore** 동일 규칙 | 범위 밖 |
| `saju-growth-system/automation/*.py` 2곳 | 별개 서브프로젝트, Downloads 경로 | **범위 밖**(별도 판단) |
| `.claude/settings.json` 훅 2곳 | 기계 로컬 설정 | 범위 밖(이식 대상 아님) |

**주의 — 테스트 설계에 직결**: 절대경로 스캔 테스트를 파일시스템 워크로 짜면 gitignore 된
`sajugen/_poc.py` 에 걸려 **즉시 RED** 가 된다. 스캔 대상은 **git 추적 파일**로 한정해야 한다.

### 2-3. 자산은 추적되고 있다

`sajugen/assets/ephemeris/de440s.bsp` (32,726,016 bytes) 는 **git 추적 중**이다
(`git ls-files sajugen/assets/` 확인). 즉 새 클론·컨테이너에 별도 provisioning 이 필요 없고,
경로만 고치면 이식이 성립한다.

### 2-4. 숨은 실패 모드 — 조용한 네트워크 다운로드

Skyfield `Loader` 는 지정 디렉터리에 파일이 **없으면 네트워크에서 받아온다**.
현재 구조에서 경로가 틀리면 "명확한 에러" 가 아니라 **32MB 다운로드 시도 또는 네트워크 오류**가 된다.
컨테이너·CI 에서 이건 진단이 어려운 실패다(방법론 B-2 fail-closed 위반).

---

## 3. 변경 설계

### 3-1. 단일 소스 (방법론 B-1 — 불변식 복제 금지)

같은 경로 불변식이 2개 파일에 복제되는 것이 결함의 뿌리다. `docs/03` 이 기록한 F-2 사고
(`partner.py` 가 축 프레임을 복제 → 헬퍼 공유로만 해결)와 **같은 계열**이다.

**신설**: `sajugen/paths.py` — 의존성 0(표준 라이브러리만). 순환 import 위험이 없다.

```python
PACKAGE_DIR = Path(__file__).resolve().parent          # .../sajugen
EPHEMERIS_DIR = PACKAGE_DIR / "assets" / "ephemeris"
EPHEMERIS_BSP = "de440s.bsp"
```

`sajugen/config.py` 에 얹지 않는 이유: `config.py` 는 `yaml` 을 import 하므로 계산 레이어가
설정 로더에 의존하게 된다. 경로 상수는 의존성 0 이어야 한다.

두 소비처는 `from sajugen.paths import EPHEMERIS_DIR, EPHEMERIS_BSP` 로 바꾼다.
`Loader()` 가 `Path` 를 거부하면 `str(EPHEMERIS_DIR)` 로 넘긴다(실측해서 결정).

### 3-2. fail-closed (§2-4 해소)

`Loader(...)` 호출 전에 `EPHEMERIS_DIR / EPHEMERIS_BSP` 존재를 확인하고, 없으면
**무슨 경로를 봤는지 담은 명확한 예외**를 던진다. 조용한 다운로드로 흘러가지 않게 한다.
예외 타입·문구는 구현자 재량이되, 메시지에 기대 경로가 들어가야 한다.

### 3-3. 하지 않을 것

- 환경변수 오버라이드(`SAJUGEN_EPHEM_DIR` 등) **도입 금지** — 이번 범위 밖이다.
  웹앱 이식 시 필요해지면 별도 패킷에서 판단한다.
- `_DE440S_MIN_YEAR`·`_DE440S_MAX_YEAR`, 절기 계산 로직, `lru_cache` 상한(§4-3) **무수정**.
- `sajugen/_poc.py`·루트 `_h15*.py`·`saju-growth-system/**` **무수정**.

---

## 4. 파일 경계

**allowed_files**
```
sajugen/paths.py                     (신설)
sajugen/calc/solarterms.py           (import·경로만)
sajugen/input/time_correction.py     (import·경로만)
tests/test_path_portability.py       (신설)
implementation-notes.md              (구현 보고)
sajugen/STATE.md                     (진행 기록, 마지막에)
```

**forbidden_files** — 위 목록 밖 전부. 특히:
```
sajugen/calc/** (solarterms.py 외) · sajugen/render/** · sajugen/content/**
config/** · docs/** · handoff/current/manifest.json · .env · data/**
harness/profiles/local/**  (비열람)
```

요구사항 충족에 위 경계 밖 수정이 필요하면 **우회하지 말고 `BLOCKED_CONTRACT` 로 정지**한다.

---

## 5. 수용 기준 — 양방 테스트 (작업 규율 3)

`tests/test_path_portability.py` 신규. **정상 통과 + 결함 차단** 양쪽을 같은 커밋에 둔다.

**(가) 정상 통과**
1. `sajugen.paths.EPHEMERIS_DIR` 가 절대경로이고 `sajugen/assets/` 아래를 가리킨다.
2. `EPHEMERIS_DIR / "de440s.bsp"` 가 존재한다.
3. `solarterms` 와 `time_correction` 이 **같은** 디렉터리 상수를 쓴다(단일 소스 실증 — 두 모듈이
   참조하는 값이 `paths.EPHEMERIS_DIR` 와 동일 객체/동일 경로).
4. 기존 계산이 불변: 골든 케이스 `2000-01-01 12:00 KST 남 서울 = 己卯 丙子 戊午 戊午`
   (calc.md 지정)와 절기 시각 산출이 교정 전과 동일하다.

**(나) 결함 차단**
5. **git 추적 파일 한정** 절대경로 스캔: 추적되는 `sajugen/**/*.py` 에 `C:\`·`/Users/`·`/home/`
   형태의 절대경로 리터럴이 **0건**이어야 한다. (§2-2 주의 — gitignore 파일을 포함하면 오탐 RED)
   구현 힌트: `git ls-files -- "sajugen/*.py"` 결과만 순회.
6. 천체력 파일이 없는 상황을 합성해 §3-2 의 **명확한 예외가 실제로 발생**하는지 확인한다
   (조용한 다운로드로 새지 않는다). 네트워크를 실제로 타지 않게 구성할 것.

**주의(테스트 함정)**: 5번을 정규식으로 짤 때 백슬래시 이스케이프를 틀리면 **아무것도 매치하지
않는 조용한 no-op 테스트**가 된다(이 설계 세션이 실제로 한 번 겪었다). 교정 전 코드에 대해
**RED 가 나는지 반드시 먼저 확인**하고 그 사실을 보고에 적어라.

---

## 6. 검증 명령 (전부 실행 · 증거 필수)

```
./.venv/Scripts/python.exe -m pytest tests/ -q
```
- 통과 기준: **exit 0**, passed 수 **감소 0**(직전 기준선 = 1266 passed / 4 skipped),
  신규 테스트만큼 증가. 골든 `-k golden` **28** GREEN.
- `calc/`·`input/` 변경이므로 골든 전수 동반은 **필수**다(절대규칙 20, calc.md).

```
git diff --check
git status --short
./.venv/Scripts/python.exe -m ruff check sajugen tests
./.venv/Scripts/python.exe -m py_compile sajugen/paths.py sajugen/calc/solarterms.py sajugen/input/time_correction.py
```

추가 증거 1건 — **이식성 실증**:
CWD 를 저장소 밖으로 바꾼 뒤 `-c "import sajugen.calc.solarterms, sajugen.input.time_correction"`
이 성공하는지 보인다(현행 코드에서도 통과하므로 이것만으로는 부족하다 — 5번 스캔 테스트가 본 증거).

---

## 7. 정지 조건 (BLOCKED_CONTRACT)

- allowed_files 밖 수정이 필요해질 때
- `Loader` 가 패키지 상대 경로를 받지 못해 계산 결과가 달라질 때(= 무해한 리팩터가 아님)
- 골든 22건 중 1건이라도 값이 바뀔 때 — **경로 변경으로 계산이 바뀌면 그 자체가 결함 신호**다
- PDF 렌더·LLM 호출·commit·push 가 필요해질 때

## 8. 산출물

- `CODEX_IMPLEMENTATION_REPORT` (implementation-notes.md) — 실행 명령 + 출력(passed 수/exit code),
  교정 전 신규 테스트 RED 실증, 미검증 항목 분리 명시
- `sajugen/STATE.md` 재개 앵커 갱신
- 커밋 금지. 운영자 checkpoint 대기.

## 9. 리스크 메모

- **저위험 리팩터**로 보이지만 `calc/`·`input/` 이라 골든 회귀가 필수다. "경로만 바꿨으니
  계산은 그대로일 것" 은 추정이며, 실행 출력으로 증명해야 한다(방법론 A-1).
- 이 태스크는 F-1(대운 축)과 **무관**하다. F-1 은 유파 1차 자료 조사 대기로 별도 보류 중이며,
  이 패킷에서 `docs/03`·`myeongni.py` 를 건드리지 않는다.
