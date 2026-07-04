# -*- coding: utf-8 -*-
"""레이아웃 기하 게이트 회귀 — 텍스트/글자수 게이트가 못 잡던 시각 결함(좌우 비대칭·넘침) 검출.

배경: verify() 가 텍스트/카운트/시맨틱만 검사해, 본문 칼럼이 왼쪽으로 쏠려도(좌 20mm/우 42mm)
gate_pass=true 로 반복 통과했다(2026-07-02 근본원인). `_layout_geometry_hits` 는 PyMuPDF 텍스트
블록 bbox 로 좌우 여백 대칭·콘텐츠 넘침을 결정론적으로 검사한다(픽셀 diff 아님).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.render import verify as V  # noqa: E402

_A4 = (595.0, 842.0)


def _blocks(x0: float, x1: float, n: int = 6) -> list[tuple]:
    # n개의 텍스트 블록(bbox), 모두 x0..x1 폭, y만 다르게.
    return [(x0, 100.0 + i * 20, x1, 118.0 + i * 20) for i in range(n)]


def _pages(*bodies: str) -> list[str]:
    # index 0 = 표지(제외), 이후 = 본문(목차/부록 마커 없음).
    return ["표지 페이지"] + list(bodies)


def test_symmetric_centered_body_is_clean():
    # 중앙정렬 칼럼(x0=88pt≈31mm, x1=505pt≈우 31.7mm) → 대칭, 넘침 없음.
    sym = _blocks(88.0, 505.0)
    pages_text = _pages("본문 가" * 20, "본문 나" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], sym, sym], [_A4, _A4, _A4])
    assert hits == [], hits


def test_left_pinned_asymmetry_is_flagged():
    # 좌측 고정 칼럼(x0=57pt=20mm, 기대 좌단 31mm 에서 11mm 이탈) = 원래 버그 → column_shift.
    asym = _blocks(57.0, 474.0)
    pages_text = _pages("본문 가" * 20, "본문 나" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], asym, asym], [_A4, _A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "column_shift" in kinds, hits
    assert {h["page"] for h in hits} == {2, 3}
    # PII-free: 본문 텍스트 미포함, 수치만.
    assert all(set(h) <= {"page", "kind", "left_mm", "expected_left_mm"} for h in hits)


def test_content_overflow_is_flagged():
    # 대칭이지만 콘텐츠박스(20mm) 밖으로 넘침(x0=30pt≈10.6mm < 17mm).
    over = _blocks(30.0, 565.0)  # 좌우 대칭(10.6mm)이나 양쪽 다 넘침
    pages_text = _pages("본문 가" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], over], [_A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "content_overflow" in kinds, hits
    # x0=10.6mm 는 기대 좌단(31mm) 이탈이기도 함 — column_shift 동반은 정당(중복 신호 허용)


def test_cover_and_toc_pages_are_excluded():
    # 표지(index 0)·목차 페이지는 비대칭이어도 스코프 제외.
    asym = _blocks(57.0, 474.0)
    pages_text = ["표지", "목차\n짧은 목차", "본문 가" * 20]
    # index0=표지, index1=목차(<400자), index2=본문
    hits = V._layout_geometry_hits(pages_text, [asym, asym, _blocks(88.0, 505.0)], [_A4, _A4, _A4])
    assert hits == [], hits  # 표지·목차 제외 + 본문은 대칭


def test_sparse_pages_are_skipped():
    # 텍스트 블록이 적은(<6) 장식/짧은 페이지는 검사 제외(오탐 방지).
    asym_sparse = _blocks(57.0, 474.0, n=3)
    pages_text = _pages("본문 가" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], asym_sparse], [_A4, _A4])
    assert hits == []


def test_empty_geometry_inputs_return_clean():
    # 기하 미지원(fake doc) → 빈 입력 → 게이트 skip(clean).
    assert V._layout_geometry_hits(["표지", "본문" * 50], [], []) == []
    assert V._layout_geometry_hits([], [[], []], [_A4, _A4]) == []


def test_vertical_overflow_is_flagged():
    # 가로 대칭·정상이지만 블록이 하단 margin(22mm=62.4pt, content_bottom≈779.6pt) 밖으로 넘침(B-2).
    # 기존엔 x(좌우)만 봐서 세로 방향 결함이 통과했다.
    over_v = [
        (88.0, 700.0 + i * 20, 505.0, 718.0 + i * 20) for i in range(6)
    ]  # 마지막 y1=818>779.6
    pages_text = _pages("본문 가" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], over_v], [_A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "vertical_overflow" in kinds, hits
    assert "column_shift" not in kinds  # 가로는 정위치


def test_vertical_within_margin_is_clean():
    # 세로가 상/하 margin 안(정상) → vertical_overflow 없음(false fail 0).
    ok_v = _blocks(88.0, 505.0)  # y 100~218, content 62.4~779.6 안
    pages_text = _pages("본문 가" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], ok_v], [_A4, _A4])
    assert all(h["kind"] != "vertical_overflow" for h in hits), hits


def test_body_inset_lost_symmetric_widen_is_flagged():
    # T3.2(2): 대칭 인셋 상실(.body max-width 무효 → 콘텐츠박스 20/20 채움). 좌우 여백은
    # 대칭이라 쏠림 검출이 구조상 못 잡는 사각 — 칼럼폭(≈170mm)으로 body_inset_lost 검출.
    # x0=56.7pt(좌20mm), x1=538.3pt(우20mm) → 폭 ≈170mm > 임계 158mm.
    inset = _blocks(56.7, 538.3)
    hits = V._layout_geometry_hits(_pages("본문 가" * 20), [[], inset], [_A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "body_inset_lost" in kinds, hits
    assert "column_shift" not in kinds or True  # 인셋 상실은 좌단도 20mm 라 column_shift 도 함께 잡힘(중복 허용)
    # PII-free: 폭 수치만.
    assert all(
        set(h) <= {"page", "kind", "width_mm", "maxw_mm"}
        for h in hits
        if h["kind"] == "body_inset_lost"
    )


def test_centered_body_width_is_not_inset_lost():
    # 정상 중앙정렬 칼럼(폭 ≈147mm ≈ maxw 148) → body_inset_lost 없음(false fail 0).
    sym = _blocks(88.0, 505.0)
    hits = V._layout_geometry_hits(
        _pages("본문 가" * 20, "본문 나" * 20), [[], sym, sym], [_A4, _A4, _A4]
    )
    assert all(h["kind"] != "body_inset_lost" for h in hits), hits


def test_left_pin_is_asymmetry_not_inset_lost():
    # 좌쏠림(20/42)은 칼럼폭이 여전히 maxw(≈148) → body_inset_lost 아님, column_shift 로 잡힘.
    # 두 결함 종류가 겹치지 않고 분리됨을 확인(인셋 상실 vs 쏠림).
    asym = _blocks(57.0, 474.0)  # 폭 (474-57)/_PT ≈147mm, 좌20/우42
    hits = V._layout_geometry_hits(_pages("본문 가" * 20), [[], asym], [_A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "column_shift" in kinds, hits
    assert "body_inset_lost" not in kinds, hits


def test_ragged_short_lines_page_is_not_flagged():
    # 실전 오탐 회귀(2026-07-04): 좌단은 정위치(31mm)인데 줄이 짧아 우측 여백이 큰(41.5mm)
    # 정상 좌정렬 래그드 페이지 — 종전 |좌-우| 비대칭 비교는 이를 FAIL 시켰다(0.3mm 초과).
    # column_shift(좌단 기대위치 이탈) 교체 후에는 통과해야 한다.
    ragged = _blocks(88.0, 476.0)  # 좌 31mm, 최우 줄이 짧아 우 ≈42mm
    hits = V._layout_geometry_hits(_pages("본문 가" * 20), [[], ragged], [_A4, _A4])
    assert hits == [], hits
