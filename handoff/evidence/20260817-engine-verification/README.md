# 엔진 검증 측정 원자료 (2026-08-17)

`handoff/tasks/webapp-direction-decisions-20260817.md` 의 근거 자료다.
결론은 그 문서에, 재현 방법과 원측정치는 여기에 있다.

## 재현 방법

모든 `.py` 는 **시드 고정**이라 재실행하면 같은 결과가 나온다.

```
./.venv/Scripts/python.exe handoff/evidence/20260817-engine-verification/<script>.py
```

단, 스크립트는 `tmp/` 경로에 산출물을 쓰도록 작성돼 있으므로 필요하면 경로를 조정한다.
시드: `random.seed(20260816)` 또는 `random.seed(20260817)`.

## 파일 색인

### 종합
| 파일 | 내용 |
|---|---|
| `engine-accuracy-report.md` | **엔진 검증 종합 보고** — 대조 축 9개, 오류 0건 |

### 명리 — 사주 4기둥·일주·대운
| 파일 | 측정 |
|---|---|
| `verify-sample.py` / `verify-out.json` | 랜덤 6 + 경계 프로브 4 = 10건 엔진 산출 |
| `verify-oracle.py` / `oracle-out.json` | 독립 오라클(JDN 60갑자 + 五虎遁/五鼠遁) 대조 10/10 |
| `sweep100.py` / `sweep100.json` | 1차 스윕 100건 (**순환 참조 결함 있음** — c판 사용) |
| `sweep100b.py` / `sweep100b.json` | 2차 — 시민날짜 키로 교정, 진태양시 날짜 불변식 프로브 |
| `sweep100c.py` / `sweep100c.json` | **최종** — NOAA 독립 진태양시. 4기둥 100/100, 일주 vs KASI 100/100, 대운수 floor 99/round 1/미설명 0 |
| `kasi-wide.py` / `kasi-wide.json` | KASI 일진 전수 대조 **55,152/55,152**, 월건=음력월 증명 53,515/53,515 |
| `kasi-rows.json` | 표본 10건의 KASI 원본 행 |
| `1976.json` | 1976-01-30 자시 경계 KASI 일진 확인 |

### 천문 — 절기·진태양시
| 파일 | 측정 |
|---|---|
| `terms-vs-kasi.py` / `terms-vs-kasi.json` | Skyfield vs KASI 절기 672행. 669행 2분 이내(최대 0.64분), 초과 3건 = KASI 자체 결함 |
| `spike-solar.py` / `spike-solar.json` | **해석식으로 Skyfield 대체 가능한가** → 불가. 평균 4.4분/최대 14.1분, 2분 초과 502/672 |
| `intl-probe.py` / `intl-probe.json` | **해외 시간대 결함** — 뉴욕 11시간 오차 + 날짜 넘어감 |
| `domestic-lon.py` / `domestic-lon.json` | **국내 경도 영향** — 부산 시지 9.2%, 울릉도 15.8% |

### 자미두수
| 파일 | 측정 |
|---|---|
| `ziwei-oracle.py` / `ziwei-oracle.json` | 고전 공식 재도출(命宮·身宮·五行局·起紫微訣) 10/10 |
| `ziwei-tail.py` / `ziwei-tail.json` | 起紫微訣 꼬리 구간 240건. 局數 2~6 × 음력일 {1,28,29,30}, 差 0~5 전 구간 |
| `tail-ng.txt` | 위 240건 중 불일치 1건 상세 (晚子時 유파 — 엔진 정확) |
| `probe3.py` / `probe3.json` | 晚子 가설 검증 + iztro/KASI 음력 괴리 주간 표본 |
| `probe4.py` / `probe4.json` | **한·중 음력 괴리 전수** 25,933일. 월 갈림 0.57% / 일만 갈림 3.24%, 연속 30구간 |
| `probe2.json` | 1976-01-30 · 2005-12-01 개별 프로브 |
| `parser-test.json` | 음력 한자 파서 단위 검증 |

### 풀이 계층
| 파일 | 측정 |
|---|---|
| `repeat-rate.py` / `repeat-rate.json` | **룰 출력 판박이율** 30명분. 전체 48.8%, together 74.7% / work_job 11.4% |

### 라이선스·의존성
| 파일 | 내용 |
|---|---|
| `closure.json` | `engine.build` 임포트 클로저 — fitz/playwright/verapdf **없음** |
| `licenses.json` / `lic2.json` | 의존성 라이선스 전수. **pymupdf = AGPL-3.0** |
| `authors.json` / `iztro-js.json` / `iztro-api.json` | 라이브러리 저자·버전·API 표면 |

### 운영
| 파일 | 내용 |
|---|---|
| `manifest-backup-20260817.json` | 갱신 전 `handoff/current/manifest.json` 백업 |

---

## 이관 제외 항목 (절대규칙 4/17)

아래는 `tmp/` 에만 두고 **커밋하지 않는다.**

| 파일 | 사유 |
|---|---|
| `_ruleonly.json` | 생년월일(1997-10-27) + 룰 본문 전문 19,999자 |
| `_compare1997.json` | 생년월일 — 외부 계정 프로필 유래 |
| `_sample_nature.txt` | 룰 생성 본문 전문 2,083자 |
| `_sample_wonguk.txt` | 룰 생성 본문 전문 989자 |

`_ruleonly.json` 은 `repeat-rate.py` 를 재실행하면 재생성되므로 보관 필요가 없다.

## 파일명 규칙

`.gitignore` 의 `_[!_]*.{py,txt,json}` 이 **위치 무관 전역 차단**이라, 선행 밑줄을 떼고
kebab-case 로 개명했다. 원본명은 위 표에서 밑줄을 붙이면 된다.
