# -*- coding: utf-8 -*-
"""ref_date(풀이 기준 일자) 기본값 단일 소스.

Phase 0(2026-07-06, 운영자 승인 로드맵): 운영자 대면 진입점(gunghap·integrated CLI,
scripts/hrun.py regen 분기)에서 ref_date 미지정 시 '오늘'을 주입해 운영자 기억 의존
(docs/19 §11 "생성 당일 기억해 전달")을 제거한다.

경계(불변식 B-1 단일화): 라이브러리 함수(build_gunghap/build_integrated_full)와
integrated `--content` 재렌더 경로는 이 헬퍼를 쓰지 않는다 — None→{ref_year}-06-13
폴백(라이브러리)·저장된 ref_date 재현(재렌더)을 유지해야 테스트 결정론과
재렌더 content.json 영속 불변이 지켜진다.

테스트는 이 함수를 monkeypatch 해 고정값을 주입한다(date.today() 자정 경계 flakiness 회피).
"""

from datetime import date


def default_ref_date_iso() -> str:
    """운영자 대면 진입점에서 ref_date 미지정 시 쓰는 '오늘' 기본값(YYYY-MM-DD)."""
    return date.today().isoformat()
