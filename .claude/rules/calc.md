---
paths:
  - "sajugen/calc/**"
  - "sajugen/input/**"
---

# 계산 레이어 규칙 (calc/, input/)

- 이 레이어 수정은 반드시 같은 작업 단위에 테스트 동반(tests/test_p1.py, test_p2.py 또는 신규). 커밋 전 pytest p1~p5 GREEN.
- 골든 케이스 회귀 필수: 2000-01-01 12:00 KST 남 서울 = 己卯 丙子 戊午 戊午 (절입 연주경계 케이스 포함).
- 절기는 lunar-python(중국시 UTC+8 → +1h 환산)과 Skyfield 교차가 기본, KASI 캐시 추가 시 3원. 허용오차: Skyfield↔KASI 2분, lunar↔Skyfield 기존 0.02~0.21분 수준 유지.
- lunar-python 1.4.8 고정. getDayJiShen/XiongSha는 택일 신살 체계라 사주 신살에 사용 금지(왜곡) — 신살은 calc/advanced.py 자체 표.
- 진태양시: 시각은 태양 시각각 기준, 날짜는 시민(KST) 날짜 기준 고정(자정 경계 ±12h 보정) — UTC 날짜 기준 사용 금지(KST 새벽 출생 -1일 버그 재발 방지).
- 자시정책(ZasiPolicy)·윤달 정책은 enum/설정으로만 분기, 하드코딩 금지. 새 유파 분기는 docs/03 결정표에 먼저 기록 후 구현.
- 출생시각 계약은 `birth_time_mode=known|three_pillar` 단일 정본으로 관리한다. `three_pillar`는 신고한 시민 날짜의 연·월·일주를 고정하고 12개 시지 후보의 구조화 값이 12/12 동일할 때만 시간 불변 사실로 승격한다. 정오 대입·시주/자미 계산·후보 원문 영속은 금지하고, 입춘·절입이 신고 날짜 안에 있어 시각 없이 연주·월주를 확정할 수 없으면 `NEEDS_INFO_TIME_BOUNDARY`로 차단한다.
- 학설 차이가 있는 산출(격국 단순화, 신살 일지 기준 등)은 결과에 note 명시, 단정 금지.
