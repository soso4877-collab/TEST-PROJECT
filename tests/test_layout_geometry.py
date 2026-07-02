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
    # 좌측 고정 칼럼(x0=57pt=20mm, x1=474pt → 우 42.7mm) = 원래 버그 → margin_asymmetry.
    asym = _blocks(57.0, 474.0)
    pages_text = _pages("본문 가" * 20, "본문 나" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], asym, asym], [_A4, _A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "margin_asymmetry" in kinds, hits
    assert {h["page"] for h in hits} == {2, 3}
    # PII-free: 본문 텍스트 미포함, 수치만.
    assert all(set(h) <= {"page", "kind", "left_mm", "right_mm"} for h in hits)


def test_content_overflow_is_flagged():
    # 대칭이지만 콘텐츠박스(20mm) 밖으로 넘침(x0=30pt≈10.6mm < 17mm).
    over = _blocks(30.0, 565.0)  # 좌우 대칭(10.6mm)이나 양쪽 다 넘침
    pages_text = _pages("본문 가" * 20)
    hits = V._layout_geometry_hits(pages_text, [[], over], [_A4, _A4])
    kinds = {h["kind"] for h in hits}
    assert "content_overflow" in kinds, hits
    assert "margin_asymmetry" not in kinds  # 대칭이므로 비대칭은 아님


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
