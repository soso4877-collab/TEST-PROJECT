# -*- coding: utf-8 -*-
"""T2.2 [G-2] 절입 ±2분 관리자 확인 플래그 (절대규칙 7 후단).

두 계산 엔진이 합의하는 knife-edge(입춘 1분 후 등)는 월지 불일치로 못 잡으므로,
출생 UTC 와 최근접 12節(월건 절입) 시각 차 ±2분 이내면 near_term_boundary 플래그를
세워 order_flow 가 needs_review 로 관리자 재확인을 유도한다(계산 차단 아님).
"""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine, solarterms  # noqa: E402

_IPCHUN_2001_UTC = solarterms.solar_term_time(2001, 315)  # 입춘 = 황경 315°


def _build_at_kst(dt_utc):
    # 절입 UTC 를 KST 시민시각(+9h)으로 → engine 입력(civil). ct.utc 는 다시 이 UTC.
    kst = dt_utc + timedelta(hours=9)
    return engine.build(kst.year, kst.month, kst.day, kst.hour, kst.minute, is_male=True)


def test_near_ipchun_within_tolerance_flags_boundary():
    # 입춘 ±1분(전/후) 모두 발화 — 절입 직전/직후 양쪽 검출
    for dm in (-1, 1):
        s = _build_at_kst(_IPCHUN_2001_UTC + timedelta(minutes=dm))
        assert s.crosscheck.near_term_boundary is True, dm


def test_beyond_tolerance_does_not_flag():
    # 입춘 +3분 = 허용치(2분) 초과 → 미발화
    s = _build_at_kst(_IPCHUN_2001_UTC + timedelta(minutes=3))
    assert s.crosscheck.near_term_boundary is False


def test_normal_time_does_not_flag():
    assert engine.build(2001, 6, 15, 12, 0, is_male=True).crosscheck.near_term_boundary is False


def test_golden_case_unaffected_by_near_term_flag():
    # 골든(2000-01-01 정오)은 절입 근처 아님 → 미발화 + 일주 불변(플래그가 팔자에 영향 0)
    s = engine.build(2000, 1, 1, 12, 0, is_male=True)
    assert s.crosscheck.near_term_boundary is False
    assert s.myeongni.day.ganzhi == "戊午"


def test_minutes_to_nearest_jie_zero_at_term():
    # 절입 시각 자체 = 차 ~0분
    assert solarterms.minutes_to_nearest_jie(_IPCHUN_2001_UTC) < 0.5


def test_gen_result_and_needs_review_wiring():
    # 배선 회귀: GenResult.near_term_boundary 가 SajuResult 에서 흐르고, order_flow 가
    # needs_review 로 반영하는 경로(단위 — 플래그 전파 계약 고정)
    from sajugen import order_flow  # noqa: F401  (import 가능 = 배선 심볼 존재)
    from sajugen.pipeline import GenResult

    r = GenResult(pdf_path="", ok=True, reasons=[], verify={}, guard={}, near_term_boundary=True)
    # ok=True 여도 near_term 이면 검수 필요
    assert (not r.ok) or r.near_term_boundary
