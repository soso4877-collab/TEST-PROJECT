# -*- coding: utf-8 -*-
"""T2.1 [P0-1] 자시 정책(ZasiPolicy)이 일주에 반영되는지 — calc/ 골든 앵커.

절대규칙 6: 자시 기본 = JST_2300(23시부터 자시·일주 전환). 명리와 자미 동일 자시 축.
근본원인(수정 전): myeongni/partner 가 lunar-python setSect 를 설정 안 해(기본 sect2=당일)
day_offset 이 일주에 무효 → 자시 출생 일간부터 오류 + 명리↔자미 CALC_MISMATCH 오발동.

기대값은 code-match 가 아니라 first-principles 로 도출:
- 진태양시 1999-06-11 23:18 = 子시(day_offset=1). 당일 일주 = 甲午(lunar-python 22:30 케이스로
  독립 확인). JST_2300(23시→일주 익일)이면 60갑자 인접 = 甲午 다음 = 乙未.
- iztro(자미)도 독립적으로 이 자시를 익일(乙未)로 산출 → 60갑자 산술과 iztro 두 소스가 乙未 확증.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402

_ZASI = (1999, 6, 11, 23, 50)  # 진태양시 23:18 = 子시(day_offset=1)


def _my(policy):
    return engine.build(*_ZASI, is_male=True, horoscope_date="2026-06-01", policy=policy).myeongni


def test_jst2300_advances_day_pillar_to_next_60gapja():
    m = _my(tc.ZasiPolicy.JST_2300)
    # 당일 甲午 → 익일 60갑자 인접 = 乙未 (JST_2300: 23시 자시 → 일주 익일)
    assert m.day.ganzhi == "乙未", m.day.ganzhi
    assert m.day.gan == "乙"
    # 시/월/연주는 보존(setSect(1) 은 일주만 전환)
    assert (m.year.ganzhi, m.month.ganzhi, m.hour.ganzhi) == ("己卯", "庚午", "丙子")


def test_jst2300_restores_myeongni_ziwei_consistency():
    # 자미도 자시를 익일로 처리하므로, 명리 일주 익일 전환 후 명리↔자미 팔자 일치(수정 전엔 False)
    s = engine.build(
        *_ZASI, is_male=True, horoscope_date="2026-06-01", policy=tc.ZasiPolicy.JST_2300
    )
    assert s.crosscheck.bazi_consistent is True


def test_yajasi_split_keeps_same_day_pillar():
    # 야자시(23~24시)는 당일 유지 → 일주 불변(甲午)
    m = _my(tc.ZasiPolicy.YAJASI_SPLIT)
    assert m.day.ganzhi == "甲午", m.day.ganzhi


def test_zasi_policy_produces_different_day_pillar():
    # 동일 입력에서 두 정책이 서로 다른 일주 → enum 분기가 실제로 작동
    jst = _my(tc.ZasiPolicy.JST_2300).day.ganzhi
    yaj = _my(tc.ZasiPolicy.YAJASI_SPLIT).day.ganzhi
    assert jst == "乙未" and yaj == "甲午" and jst != yaj


def test_setsect_does_not_leak_into_daewoon():
    # setSect(1) 은 일주만 — 대운(getYun, 절기 기반)은 불변이어야(누수 검증, advisor)
    from lunar_python import Solar

    e1 = Solar.fromYmdHms(1999, 6, 11, 23, 18, 0).getLunar().getEightChar()
    e2 = Solar.fromYmdHms(1999, 6, 11, 23, 18, 0).getLunar().getEightChar()
    e2.setSect(1)
    assert e1.getYun(1, 1).getStartYear() == e2.getYun(1, 1).getStartYear()
    assert [d.getGanZhi() for d in e1.getYun(1, 1).getDaYun()[1:5]] == [
        d.getGanZhi() for d in e2.getYun(1, 1).getDaYun()[1:5]
    ]


def test_non_zasi_input_unaffected_by_policy():
    # day_offset=0(정오)은 setSect 미발동 → 정책 무관 동일 + 골든 일주 보존(회귀 보증)
    jst = engine.build(2000, 1, 1, 12, 0, is_male=True, policy=tc.ZasiPolicy.JST_2300).myeongni
    yaj = engine.build(2000, 1, 1, 12, 0, is_male=True, policy=tc.ZasiPolicy.YAJASI_SPLIT).myeongni
    assert jst.day.ganzhi == yaj.day.ganzhi == "戊午"  # 골든 2000-01-01 일주


# ── 자시 축의 두 코드 경로 커버(만자시=setSect / 조자시=base 날짜) + 연속성·경계(advisor) ──
# 자시 축(진태양시 23:00~01:00)은 하나의 일주여야 한다. 서울 보정(약 -32분) 기준:
#   만자시 시민 6/11 23:50 → 진태양시 23:18(day_offset=1, setSect 경로) → 일주 6/12=乙未
#   조자시 시민 6/12 01:20 → 진태양시 00:48(day_offset=0, base 날짜 경로) → 일주 6/12=乙未
# 두 다른 메커니즘이 같은 일주에 도달해야 연속성이 성립(이중전진/미전진 결함 검출).
_LATE_ZI = (1999, 6, 11, 23, 50)  # 진태양시 23:18
_EARLY_ZI = (1999, 6, 12, 1, 20)  # 진태양시 00:48
_BELOW_ZI = (1999, 6, 11, 23, 20)  # 진태양시 22:48 (자시 전)


def test_early_zi_uses_base_date_without_setsect():
    # 조자시: day_offset=0(setSect 미발동), 일주는 base Solar 날짜(6/12)에서 도출 = 乙未
    m = engine.build(*_EARLY_ZI, is_male=True, policy=tc.ZasiPolicy.JST_2300).myeongni
    assert m.day.ganzhi == "乙未", m.day.ganzhi


def test_zi_continuity_across_2300_boundary():
    # 만자시(setSect 경로)와 조자시(base 날짜 경로)가 같은 자시 축 → 동일 일주(연속성)
    late = engine.build(*_LATE_ZI, is_male=True, policy=tc.ZasiPolicy.JST_2300).myeongni
    early = engine.build(*_EARLY_ZI, is_male=True, policy=tc.ZasiPolicy.JST_2300).myeongni
    assert late.day.ganzhi == early.day.ganzhi == "乙未"


def test_just_below_zi_boundary_does_not_advance():
    # 진태양시 22:48(자시 전) → day_offset=0 → 일주 미전진(당일 甲午). 경계 아래 오탐 방지.
    m = engine.build(*_BELOW_ZI, is_male=True, policy=tc.ZasiPolicy.JST_2300).myeongni
    assert m.day.ganzhi == "甲午", m.day.ganzhi
