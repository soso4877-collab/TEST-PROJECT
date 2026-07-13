# -*- coding: utf-8 -*-
"""생시 미상 삼주 계산 계약의 양방·경계 회귀."""

from __future__ import annotations

import pytest

from sajugen.calc import engine
from sajugen.calc.three_pillar import NeedsInfoTimeBoundary, reduce_candidate_facts
from sajugen.input.birth_time import BirthTimeMode, normalize_birth_time_mode


def test_birth_time_mode_normalizes_legacy_and_rejects_conflicts() -> None:
    assert normalize_birth_time_mode(hour=9) is BirthTimeMode.KNOWN
    assert normalize_birth_time_mode(hour=None) is BirthTimeMode.THREE_PILLAR
    assert (
        normalize_birth_time_mode(unknown_time=True, hour=12)
        is BirthTimeMode.THREE_PILLAR
    )
    assert normalize_birth_time_mode("known", unknown_time=False, hour=9) is BirthTimeMode.KNOWN

    with pytest.raises(ValueError):
        normalize_birth_time_mode("known", unknown_time=True, hour=9)
    with pytest.raises(ValueError):
        normalize_birth_time_mode("three_pillar", unknown_time=False, hour=None)


def test_known_time_default_and_explicit_mode_are_identical() -> None:
    implicit = engine.build(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
    )
    explicit = engine.build(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
        birth_time_mode="known",
    )

    assert isinstance(implicit, engine.SajuResult)
    assert isinstance(explicit, engine.SajuResult)
    assert implicit.birth_time_mode is BirthTimeMode.KNOWN
    assert implicit.model_dump(mode="json") == explicit.model_dump(mode="json")


def test_three_pillar_never_calls_ziwei_and_has_no_hour_contract(monkeypatch) -> None:
    def forbidden_ziwei(*args, **kwargs):
        raise AssertionError("three_pillar 에서 ziwei.build를 호출하면 안 됩니다")

    monkeypatch.setattr(engine.mod_zw, "build", forbidden_ziwei)
    result = engine.build(
        2000,
        1,
        1,
        None,
        None,
        is_male=True,
        horoscope_date="2026-06-01",
        birth_time_mode="three_pillar",
    )

    assert isinstance(result, engine.ThreePillarSajuResult)
    assert result.birth_time_mode is BirthTimeMode.THREE_PILLAR
    assert result.ziwei is None
    assert not hasattr(result, "myeongni")
    assert not hasattr(result.three_pillar, "hour")
    assert not hasattr(result.three_pillar, "elements")
    assert not hasattr(result.three_pillar, "singang")
    assert result.provenance.three_pillar_schema_version == 1
    assert result.provenance.candidate_count == 12
    assert len(result.provenance.candidate_digest) == 64
    assert set(result.three_pillar.fact_sources.values()) <= {
        "three_pillar",
        "time_invariant",
        "calendar_flow",
    }


def test_legacy_unknown_time_ignores_noon_and_uses_three_pillar(monkeypatch) -> None:
    def forbidden_ziwei(*args, **kwargs):
        raise AssertionError("legacy unknown_time도 ziwei.build를 호출하면 안 됩니다")

    monkeypatch.setattr(engine.mod_zw, "build", forbidden_ziwei)
    legacy = engine.build(
        2000,
        1,
        1,
        12,
        0,
        is_male=False,
        unknown_time=True,
    )
    native = engine.build(
        2000,
        1,
        1,
        None,
        None,
        is_male=False,
        birth_time_mode="three_pillar",
    )

    assert isinstance(legacy, engine.ThreePillarSajuResult)
    assert legacy.model_dump(mode="json") == native.model_dump(mode="json")


def test_candidate_reducer_requires_full_twelve_of_twelve_and_is_order_invariant() -> None:
    candidates = [{"stable": {"a": [1, 2]}, "fragile": "same"} for _ in range(12)]
    candidates[-1]["fragile"] = "different"

    stable, suppressed, digest = reduce_candidate_facts(candidates)
    reversed_stable, reversed_suppressed, reversed_digest = reduce_candidate_facts(
        list(reversed(candidates))
    )

    assert stable == {"stable": {"a": [1, 2]}}
    assert suppressed == ["fragile"]
    assert reversed_stable == stable
    assert reversed_suppressed == suppressed
    assert reversed_digest == digest


def test_candidate_reducer_suppresses_missing_key_and_rejects_wrong_count() -> None:
    candidates = [{"shared": 1, "missing_once": 2} for _ in range(12)]
    candidates[-1].pop("missing_once")

    stable, suppressed, _ = reduce_candidate_facts(candidates)
    assert stable == {"shared": 1}
    assert suppressed == ["missing_once"]

    for invalid_count in (0, 11, 13):
        with pytest.raises(ValueError, match="candidate_count must be 12"):
            reduce_candidate_facts([{"shared": 1}] * invalid_count)


def test_jie_boundary_day_fails_closed_but_adjacent_day_passes() -> None:
    # 2000년 입춘은 한국시각 2월 4일 안에 있으므로 시각 없이 월주·연주를 확정할 수 없다.
    with pytest.raises(NeedsInfoTimeBoundary) as caught:
        engine.build(
            2000,
            2,
            4,
            None,
            None,
            is_male=True,
            birth_time_mode="three_pillar",
        )
    assert caught.value.code == "NEEDS_INFO_TIME_BOUNDARY"
    assert "2000" not in str(caught.value)

    adjacent = engine.build(
        2000,
        2,
        5,
        None,
        None,
        is_male=True,
        birth_time_mode="three_pillar",
    )
    assert isinstance(adjacent, engine.ThreePillarSajuResult)


def test_non_ipchun_jie_day_fails_closed_and_both_adjacent_days_pass() -> None:
    # 1995년 소서는 한국 민간 날짜 7월 7일 안에 있다. 입춘 이외의 월 절입도
    # 같은 fail-closed 계약을 타며, 경계 양옆 날짜까지 과잉 차단하면 안 된다.
    with pytest.raises(NeedsInfoTimeBoundary) as caught:
        engine.build(
            1995,
            7,
            7,
            None,
            None,
            is_male=True,
            birth_time_mode="three_pillar",
        )
    assert caught.value.code == "NEEDS_INFO_TIME_BOUNDARY"

    for day in (6, 8):
        result = engine.build(
            1995,
            7,
            day,
            None,
            None,
            is_male=True,
            birth_time_mode="three_pillar",
        )
        assert isinstance(result, engine.ThreePillarSajuResult)
