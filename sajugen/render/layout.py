# -*- coding: utf-8 -*-
"""렌더 레이아웃 기하 상수 — 단일 소스.

pdf.py(@page 마진·본문폭 CSS 주입)와 verify.py(기하 게이트)가 같은 값을 참조한다
(render.md: @page 마진과 pg.pdf margin·게이트 기대값은 반드시 동기화). 무거운 의존이 없어
(순수 상수) verify 임포트 그래프에 Playwright 를 끌어오지 않는다.
"""

from __future__ import annotations

# @page 마진(mm) — Chromium pg.pdf margin + @page CSS 공용.
PAGE_MARGIN_MM: dict[str, float] = {"top": 22.0, "bottom": 22.0, "left": 20.0, "right": 20.0}

# 본문 칼럼 최대폭(mm) — 템플릿 .body max-width(중앙정렬). 중앙정렬이므로
# 본문 칼럼 기대 좌단 = (페이지폭 - BODY_MAXW_MM)/2, 기대 칼럼폭 ≈ BODY_MAXW_MM.
BODY_MAXW_MM: float = 148.0
