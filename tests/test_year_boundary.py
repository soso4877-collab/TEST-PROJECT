# -*- coding: utf-8 -*-
"""T2.4 [F-2] 연주(年柱) 입춘 경계 lunar↔Skyfield 교차검증.

기존엔 연주가 lunar-python 단독 판정(#26 절기시각 이슈 미커버)이었다. 출생 UTC 가 그 해
입춘(황경 315°) 이후면 명리 연도=그레고리 year, 전이면 year-1 — Skyfield 입춘 시각으로
독립 판정해 lunar 연지와 교차, 불일치면 calc_consistent=False(월지 교차와 대칭).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402


def test_year_crosscheck_normal_consistent():
    m = engine.build(2000, 1, 1, 12, 0, is_male=True).myeongni
    assert m.year_branch_crosscheck_ok is True
    assert m.year_branch_lunar == m.year.zhi == m.year_branch_skyfield


def test_year_boundary_before_and_after_ipchun():
    # 2000 입춘 = 2/4 12:40 UTC. 입춘 전(2/4 12:00 KST=utc 03:00)=전년 卯, 후(2/5)=당년 辰.
    before = engine.build(2000, 2, 4, 12, 0, is_male=True).myeongni
    after = engine.build(2000, 2, 5, 12, 0, is_male=True).myeongni
    assert before.year.zhi == "卯" and before.year_branch_skyfield == "卯"
    assert after.year.zhi == "辰" and after.year_branch_skyfield == "辰"
    # 두 케이스 모두 lunar↔Skyfield 일치(경계에서도 교차 통과)
    assert before.year_branch_crosscheck_ok and after.year_branch_crosscheck_ok


def test_year_branch_ok_propagates_to_crosscheck():
    # calc_consistent 편입 계약: 정상 케이스는 year_branch_ok=True (오차단 0)
    c = engine.build(1990, 5, 20, 14, 30, is_male=True).crosscheck
    assert c.year_branch_ok is True
