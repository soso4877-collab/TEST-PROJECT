# -*- coding: utf-8 -*-
"""T0 월운 표기 규약 — 맨몸 n월 금지와 절기 경계 상대 시제 양방 회귀."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import rules, temporal_lint as tl  # noqa: E402


def _types(text: str, ref_date: str | None = None) -> set[str]:
    return {h["type"] for h in tl.lint(text, 2026, ref_date=ref_date)}


def test_naked_month_lint_blocks_and_allows_required_forms():
    # 차단: 양력·음력·절기월 중 무엇인지 알 수 없는 맨몸 n월과 구간 없는 간지월.
    assert "month_notation" in _types("7월 병신월부터 지금 이 달이 시작됩니다.", "2026-08-06")
    assert "month_notation" in _types("9월 이후부터 준비를 시작해 보세요.", "2026-07-04")
    assert "month_notation" in _types("병신월부터 준비를 시작해 보세요.", "2026-07-04")

    # 허용: 실제 날짜, 음력 보조 표기, 절기명·양력 구간을 갖춘 간지월 표기.
    assert not tl.lint("오늘은 2026년 7월 4일입니다.", 2026, ref_date="2026-07-04")
    assert not tl.lint("음력 7월 무렵의 감각으로 보조해 읽습니다.", 2026)
    assert not tl.lint("병신월(입추 - 양력 8/7~9/7)부터 속도를 조절하세요.", 2026)


def test_relative_current_month_boundary_uses_solar_term_range():
    # 경계 전: 2026-08-06은 입추 전이므로 병신월을 "지금 이 달"로 부르면 안 된다.
    bad = tl.lint(
        "병신월(입추 - 양력 8/7~9/7)은 지금 이 달의 시작입니다.",
        2026,
        ref_date="2026-08-06",
    )
    assert [h for h in bad if h["type"] == "relative_month_boundary"]

    # 경계 후: 2026-08-08은 병신월 절기 구간 안이므로 같은 상대 시제가 통과한다.
    assert not tl.lint(
        "병신월(입추 - 양력 8/7~9/7)은 지금 이 달의 흐름입니다.",
        2026,
        ref_date="2026-08-08",
    )


def test_relative_next_month_boundary_uses_term_start():
    # 2026-07-20 기준 병신월은 다음 양력월인 8월에 시작하므로 "다음 달"이 맞다.
    assert not tl.lint(
        "다음 달 병신월(입추 - 양력 8/7~9/7)부터 속도를 올립니다.",
        2026,
        ref_date="2026-07-20",
    )

    # 2026-08-20 기준 병신월은 이미 시작한 간지월이므로 "다음 달"로 부르면 경계가 어긋난다.
    bad = tl.lint(
        "다음 달 병신월(입추 - 양력 8/7~9/7)부터 속도를 올립니다.",
        2026,
        ref_date="2026-08-20",
    )
    assert [h for h in bad if h["type"] == "relative_month_boundary"]


def test_rules_monthly_text_uses_term_ranges():
    # 룰 골격의 월운 표시가 "1월 경인" 같은 서수 라벨을 쓰지 않고 절기 구간을 붙이는지 고정한다.
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    sections = rules.build_all(saju, ref_year=2026, name="테스트", concern_category="전반")
    joined = sections["flow"]
    assert "양력" in joined and "입추" in joined
    assert not tl.lint(joined, 2026, ref_date="2026-07-04")
