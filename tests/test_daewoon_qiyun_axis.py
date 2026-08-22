# -*- coding: utf-8 -*-
"""대운 起運 축 이관 회귀 — docs/03 O1 결정의 독립 앵커와 구조 검증."""

import os
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import lru_cache

import pytest

from sajugen.calc import advanced, engine
from sajugen.calc import myeongni as mod_my
from sajugen.input import time_correction as tc


# 합성 입력만 사용한다. 각 기대값은 코드 출력이 아니라 三命通會의 日·時辰 折除로 손계산했다.
_HAND_CALCULATED_ANCHORS = [
  ((1985, 1, 1, 0, 30), False, 8, 2, 20, date(1993, 3, 21), "00시-역행"),
  ((1985, 2, 12, 11, 30), False, 7, 2, 10, date(1992, 4, 22), "홀수시-순행-1"),
  ((1985, 2, 12, 13, 30), False, 7, 2, 0, date(1992, 4, 12), "홀수시-순행-2"),
  ((1985, 2, 12, 10, 30), False, 7, 2, 10, date(1992, 4, 22), "짝수시-순행"),
]


@pytest.mark.parametrize("case", _HAND_CALCULATED_ANCHORS, ids=[case[-1] for case in _HAND_CALCULATED_ANCHORS])
def test_hand_calculated_qiyun_anchors(case):
  """양방 4건을 三命通會의 `三日一歲·一時辰十日` 방식으로 독립 고정한다.

  - 1985-01-01 00:30, 역행: 大雪 辰시→출생 子시. 출생 진태양시
    1984-12-31 23시는 JST_2300 정책에서 익일이므로, 자리내림 뒤 24日8辰이다.
    24*4개월 + floor(8*10/30)개월 = 98개월 = 8年2月, 잔여 20日.
    시민 KST 1985-01-01 + 8年2月20日 = 1993-03-21.
  - 1985-02-12 11:30, 순행: 출생 巳시→驚蟄 子시. 절입 진태양시
    1985-03-05 23시는 익일 귀속이므로 자리내림 뒤 21日7辰이다.
    84+floor(70/30) = 86개월 = 7年2月, 잔여 10日. 시민 앵커는 1992-04-22.
  - 같은 날 13:30, 순행: 午시→子시 = 21日6辰. 84+2 = 86개월 =
    7年2月, 잔여 0日. 시민 앵커는 1992-04-12.
  - 같은 날 10:30, 순행: 진태양시 시지는 巳이므로 21日7辰. 첫 홀수시
    앵커와 같은 7年2月10日이며 시민 앵커는 1992-04-22.
  """
  birth, is_male, years, _months, _days, start_date, _label = case
  m = engine.build(*birth, is_male=is_male, horoscope_date="2026-06-01").myeongni
  assert (m.daewoon_count, m.daewoon[0].start_year) == (years, start_date.year)
  assert m.month_branch_crosscheck_ok is True


@pytest.mark.parametrize("case", _HAND_CALCULATED_ANCHORS, ids=[case[-1] for case in _HAND_CALCULATED_ANCHORS])
def test_compute_qiyun_exposes_hand_calculated_remainders(case):
  """제품 배선뿐 아니라 起運 자체 산술의 年·月·日 나머지도 손계산과 일치한다."""
  birth, is_male, years, months, days, start_date, _label = case
  ct = tc.correct(*birth)
  m = engine.build(*birth, is_male=is_male, horoscope_date="2026-06-01").myeongni
  result = mod_my.compute_qiyun(ct, forward=m.daewoon_forward)
  assert (result.years, result.months, result.days) == (years, months, days)
  assert result.start_date == start_date


def test_qiyun_distance_bucket_and_anchor_roles_are_separate():
  """가짜 CST 거리·국지 時辰·시민 앵커의 세 역할이 서로 섞이지 않는다."""
  ct = tc.correct(2000, 2, 4, 21, 39)
  minus = mod_my.compute_qiyun(replace(ct, utc=ct.utc - timedelta(hours=1)), forward=True)
  plus = mod_my.compute_qiyun(replace(ct, utc=ct.utc + timedelta(hours=1)), forward=True)
  # 절입 직전 앵커라 가짜 UTC ±1시간은 서로 다른 다음 절을 골라 거리가 달라진다.
  assert (minus.years, minus.months, minus.days) != (plus.years, plus.months, plus.days)

  # 시민 표기만 같은 연도 안에서 옮겨도 거리와 時辰 折除는 변하지 않는다.
  relabeled = replace(ct, civil_local=ct.civil_local + timedelta(minutes=30))
  original = mod_my.compute_qiyun(ct, forward=True)
  shifted_label = mod_my.compute_qiyun(relabeled, forward=True)
  assert (original.years, original.months, original.days) == (
    shifted_label.years,
    shifted_label.months,
    shifted_label.days,
  )


def test_true_solar_2330_uses_zi_index_zero_not_lunar_hai_special_case():
  """진태양시 23:30은 자시 정책의 子(idx 0)이며 lunar 流派1의 亥(idx 11)가 아니다."""
  ct = tc.correct(1985, 1, 1, 0, 6)
  assert (ct.true_solar.hour, ct.true_solar.minute, ct.hour_branch) == (23, 30, "子")
  assert mod_my._QIYUN_BRANCHES.index(ct.hour_branch) == 0
  zi = mod_my.compute_qiyun(ct, forward=False)
  lunar_special = mod_my.compute_qiyun(replace(ct, hour_branch="亥"), forward=False)
  assert (zi.years, zi.months, zi.days) != (
    lunar_special.years,
    lunar_special.months,
    lunar_special.days,
  )


@pytest.mark.parametrize(("forward", "jst_delta"), [(False, 1), (True, -1)])
def test_qiyun_birth_zi_hour_date_follows_zasi_policy(forward, jst_delta):
  """같은 진태양시 날짜의 23:30은 JST만 起運 날짜를 하루 넘겨 소비한다."""
  jst_before = tc.correct(1984, 12, 31, 23, 6, policy=tc.ZasiPolicy.JST_2300)
  jst_after = tc.correct(1985, 1, 1, 0, 6, policy=tc.ZasiPolicy.JST_2300)
  assert (jst_before.true_solar.hour, jst_before.true_solar.minute) == (22, 30)
  assert (jst_after.true_solar.hour, jst_after.true_solar.minute) == (23, 30)
  assert (jst_before.day_offset, jst_after.day_offset) == (0, 1)

  yajasi_before = tc.correct(1984, 12, 31, 23, 6, policy=tc.ZasiPolicy.YAJASI_SPLIT)
  yajasi_after = tc.correct(1985, 1, 1, 0, 6, policy=tc.ZasiPolicy.YAJASI_SPLIT)
  assert (yajasi_before.day_offset, yajasi_after.day_offset) == (0, 0)
  assert yajasi_before.true_solar.date() == yajasi_after.true_solar.date()

  # 같은 23:30 순간에서 정책만 바꾸면 JST의 명리 날짜 하루 이동이 起運 日에 반영된다.
  jst_result = mod_my.compute_qiyun(jst_after, forward=forward)
  yajasi_result = mod_my.compute_qiyun(yajasi_after, forward=forward)
  assert jst_result.day_diff - yajasi_result.day_diff == jst_delta


def test_qiyun_jie_zi_hour_date_uses_next_policy_day():
  """1985 驚蟄 23시대는 JST_2300에서 익일 귀속돼 21日7辰이 된다."""
  ct = tc.correct(1985, 2, 12, 11, 30, policy=tc.ZasiPolicy.JST_2300)
  result = mod_my.compute_qiyun(ct, forward=True)
  jie_true_solar = tc.apparent_solar_datetime(result.jie_utc, longitude=ct.longitude)
  assert (jie_true_solar.hour, jie_true_solar.minute) == (23, 32)
  assert (result.day_diff, result.hour_diff) == (21, 7)
  assert (result.years, result.months, result.days) == (7, 2, 10)


def _legacy_seun_worun(yun, ref_year):
  """교정 전 DaYun/LiuNian/LiuYue 경로를 회귀 대조용으로만 재현한다."""
  seun = []
  worun = []
  current = next(
    (
      item
      for item in yun.getDaYun()
      if item.getStartYear() <= ref_year <= item.getEndYear()
    ),
    None,
  )
  if current is None:
    return seun, worun, None
  ref_liu_nian = None
  for year in current.getLiuNian():
    if ref_year - 1 <= year.getYear() <= ref_year + 3:
      seun.append((year.getYear(), year.getGanZhi()))
    if year.getYear() == ref_year:
      ref_liu_nian = year
  if ref_liu_nian is not None:
    worun = [
      (month.getMonthInChinese(), month.getGanZhi())
      for month in ref_liu_nian.getLiuYue()
    ]
  return seun, worun, current


@lru_cache(maxsize=None)
def _axis_year_stats(grid_year):
  """docs/27 서울 격자의 한 연도 2,544건을 측정한다(10개년 합계 25,440)."""
  stats = {
    "total": 0,
    "qiyun_changed": 0,
    "start_year_changed": 0,
    "direction_changed": 0,
    "daewoon_ganzhi_changed": 0,
    "current_daewoon_changed": 0,
    "seun_year_set_changed": 0,
    "seun_ganzhi_changed": 0,
    "worun_ganzhi_changed": 0,
  }
  day = datetime(grid_year, 1, 1)
  while day.year == grid_year:
    for hour in range(24):
      for is_male in (True, False):
        ct = tc.correct(day.year, day.month, day.day, hour, 30)
        yun = mod_my.split_axis_eight_char(ct).getYun(1 if is_male else 0, 1)
        qiyun = mod_my.compute_qiyun(ct, forward=yun.isForward())
        lunar_items = [item for item in yun.getDaYun()[1:9] if item.getGanZhi()]
        target_items = [
          mod_my.DaYunItem(
            start_age=qiyun.years + 10 * index,
            end_age=qiyun.years + 10 * index + 9,
            start_year=qiyun.start_date.year + 10 * index,
            ganzhi=item.getGanZhi(),
          )
          for index, item in enumerate(lunar_items)
        ]
        legacy_start_years = [item.getStartYear() for item in lunar_items]
        target_start_years = [item.start_year for item in target_items]
        stats["total"] += 1
        stats["qiyun_changed"] += yun.getStartYear() != qiyun.years
        stats["start_year_changed"] += legacy_start_years != target_start_years
        stats["direction_changed"] += yun.isForward() != (
          target_items[1].ganzhi[0] != target_items[0].ganzhi[0]
          and ("甲乙丙丁戊己庚辛壬癸".index(target_items[1].ganzhi[0])
               - "甲乙丙丁戊己庚辛壬癸".index(target_items[0].ganzhi[0])) % 10 == 1
        )
        stats["daewoon_ganzhi_changed"] += [item.getGanZhi() for item in lunar_items] != [
          item.ganzhi for item in target_items
        ]

        # 같은 ref_year에서 현재 대운 선택만 우리 start_year로 바뀌고 간지는 그대로여야 한다.
        old_seun, old_worun, old_current = _legacy_seun_worun(yun, 2026)
        new_seun, new_worun = advanced.seun_worun(yun, 2026, target_items)
        new_current = advanced.current_daewoon(target_items, 2026)
        old_current_gz = old_current.getGanZhi() if old_current is not None else None
        new_current_gz = new_current.ganzhi if new_current is not None else None
        stats["current_daewoon_changed"] += old_current_gz != new_current_gz
        stats["seun_year_set_changed"] += [row[0] for row in old_seun] != [
          row[0] for row in new_seun
        ]
        old_seun_map = dict(old_seun)
        new_seun_map = dict(new_seun)
        overlap = old_seun_map.keys() & new_seun_map.keys()
        stats["seun_ganzhi_changed"] += any(
          old_seun_map[ref] != new_seun_map[ref] for ref in overlap
        )
        stats["worun_ganzhi_changed"] += old_worun != new_worun

        # 새 세운 연도 집합은 현재 대운의 10년 구간 밖으로 나가면 안 된다.
        if new_current is not None:
          current_index = target_items.index(new_current)
          end_year = (
            target_items[current_index + 1].start_year - 1
            if current_index + 1 < len(target_items)
            else new_current.start_year + 9
          )
          assert all(new_current.start_year <= ref <= end_year for ref, _ in new_seun)
    day += timedelta(days=7)
  return stats


@pytest.mark.skipif(
  os.environ.get("SAJUGEN_QIYUN_GRID_SWEEP") != "1",
  reason="起運 격자 25,440건(약 20분)은 SAJUGEN_QIYUN_GRID_SWEEP=1 로 옵트인",
)
@pytest.mark.parametrize("grid_year", range(1985, 1995))
def test_grid_before_after_change_rate_and_ganzhi_invariants(grid_year):
  """연도별 분할 전수에서 방향·간지 불변을 검증하고 전체 합산용 수치를 출력한다."""
  stats = _axis_year_stats(grid_year)
  print(f"QIYUN_GRID_YEAR={grid_year} STATS={stats}")
  assert stats["total"] == 2_544
  assert stats["direction_changed"] == 0
  assert stats["daewoon_ganzhi_changed"] == 0
  assert stats["seun_ganzhi_changed"] == 0
  assert stats["worun_ganzhi_changed"] == 0
