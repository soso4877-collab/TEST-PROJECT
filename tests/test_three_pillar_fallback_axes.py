# -*- coding: utf-8 -*-
"""삼주 룰 폴백의 질문 축·시기·문체 최소 보장 회귀."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sajugen.calc import engine
from sajugen.content import delivery_quality, rules, style_lint
from sajugen.render import verify as verify_pdf


_COMPLEX_CONCERN = "직업과 돈 관리, 건강, 월별 시기, 이사, 모임 취미의 방향"


@pytest.fixture(scope="module")
def three_pillar_result():
    """실고객 값 없이 고정 합성 입력으로 삼주 계산 결과를 한 번만 만든다."""

    return engine.build(
        2000,
        1,
        15,
        None,
        None,
        is_male=False,
        birth_time_mode="three_pillar",
        horoscope_date="2026-07-12",
    )


def _fallback_consult(saju, *, concern: str, category: str) -> str:
    """LLM 없이 실제 삼주 rules 분기가 반환하는 consult 골격만 꺼낸다."""

    skeletons = rules.build_all(
        saju,
        ref_year=2026,
        concern_category=category,
        concern_text=concern,
        work_modules=("job", "wealth"),
        birth_time_mode="three_pillar",
    )
    return skeletons["consult"]


def test_three_pillar_fallback_covers_complex_axes_with_real_seun(
    three_pillar_result,
):
    """복합 고민 폴백이 현재 delivery 축과 최종 style 층을 함께 충족한다."""

    consult = _fallback_consult(
        three_pillar_result,
        concern=_COMPLEX_CONCERN,
        category="직업",
    )
    required = delivery_quality._required_axes(_COMPLEX_CONCERN)
    assert required == {
        "work_career",
        "money_contract",
        "move_house",
        "club_group",
        "timing",
        "action",
    }

    # 질문축 검사는 문구 존재가 아니라 production과 같은 evidence 함수로 고정한다.
    coverage = {
        axis: delivery_quality._axis_evidence_hits(consult, axis)
        for axis in sorted(required)
    }
    assert all(coverage.values()), coverage
    assert delivery_quality.consult_direct_result(consult, _COMPLEX_CONCERN)["ok"] is True

    # 시기는 계산된 세운 연도만 쓰며, 절기 순서를 보장할 수 없는 월운 값은 펼치지 않는다.
    seun_years = [
        int(year)
        for year, _ganzhi in three_pillar_result.three_pillar.seun
        if int(year) >= 2026
    ][:2]
    assert seun_years
    assert all(f"{year}년" in consult for year in seun_years)
    assert all(
        month_label not in consult
        for month_label, _ganzhi in three_pillar_result.three_pillar.worun
    )

    # PDF를 만들지 않고도 최종 verify가 쓰는 페이지 단위 style 함수를 같은 입력에 적용한다.
    assert style_lint.lint(consult) == []
    assert verify_pdf._semantic_style_hits([(2, consult)]) == []


def test_three_pillar_fallback_single_axis_boundary(three_pillar_result):
    """축 트리거가 하나뿐이어도 그 축과 공통 timing/action만 정확히 닫는다."""

    concern = "이사 방향"
    consult = _fallback_consult(
        three_pillar_result,
        concern=concern,
        category="시기",
    )
    required = delivery_quality._required_axes(concern)
    assert required == {"move_house", "timing", "action"}
    assert all(
        delivery_quality._axis_evidence_hits(consult, axis)
        for axis in sorted(required)
    )
    assert "집과 이사" in consult
    assert "모임과 단체 운영" not in consult
    assert "수입과 지출의 흐름" not in consult
    assert delivery_quality.consult_direct_result(consult, concern)["ok"] is True
    assert style_lint.lint(consult) == []


def test_three_pillar_fallback_no_axis_does_not_invent_topics(three_pillar_result):
    """축 트리거가 없으면 생활 주제를 임의로 만들어 넣지 않는다."""

    concern = "전반이 궁금합니다."
    consult = _fallback_consult(
        three_pillar_result,
        concern=concern,
        category="전반",
    )
    assert delivery_quality._required_axes(concern) == set()
    assert "집과 이사" not in consult
    assert "모임과 단체 운영" not in consult
    assert "수입과 지출의 흐름" not in consult
    direct = delivery_quality.consult_direct_result(consult, concern)
    assert direct["ok"] is True, direct
    assert style_lint.lint(consult) == []


@pytest.mark.parametrize(
    ("word", "kind", "expected"),
    [
        ("정축", "이가", "정축이"),
        ("임신", "이가", "임신이"),
        ("경오", "은는", "경오는"),
        ("병오년", "은는", "병오년은"),
        ("정축", "을를", "정축을"),
        ("경오", "을를", "경오를"),
    ],
)
def test_three_pillar_ganzhi_josa_table(word, kind, expected):
    """받침 유무가 다른 간지의 주격·보조사·목적격을 결정론적으로 고른다."""

    assert rules._J(word, kind) == expected


def test_three_pillar_nature_routes_ganzhi_particles_through_josa_helper():
    """실제 삼주 nature 골격이 간지 뒤 하드코딩 조사를 다시 만들지 않는다."""

    three_pillar = SimpleNamespace(
        year=SimpleNamespace(ganzhi="庚午"),
        month=SimpleNamespace(ganzhi="丁丑"),
        day=SimpleNamespace(ganzhi="壬申"),
        day_master="壬",
        geukguk="합성 격국",
        geukguk_note="",
        seun=((2026, "丙午"), (2027, "丁未")),
        worun=(),
    )
    saju = SimpleNamespace(
        three_pillar=three_pillar,
        birth_time_mode="three_pillar",
    )
    skeletons = rules.build_all(
        saju,
        ref_year=2026,
        concern_category="전반",
        birth_time_mode="three_pillar",
    )
    nature = skeletons["nature"]
    joined = "\n".join(skeletons.values())

    assert "연주 경오와 월주 정축이" in nature
    assert "일주 임신이" in nature
    assert "정축가" not in joined
    assert "임신가" not in joined
    assert all(token not in joined for token in ("이(가)", "은(는)", "을(를)", "�"))

    # 같은 실제 문형에 무받침 간지를 넣어 반대편 조사도 확인한다. 일간의 보조사까지
    # 같은 헬퍼를 타야 `무은`처럼 하드코딩된 받침형이 되살아나지 않는다.
    three_pillar.year.ganzhi = "丁丑"
    three_pillar.month.ganzhi = "庚午"
    three_pillar.day.ganzhi = "戊午"
    three_pillar.day_master = "戊"
    no_batchim = rules.build_all(
        saju,
        ref_year=2026,
        concern_category="전반",
        birth_time_mode="three_pillar",
    )
    assert "일간 무는" in no_batchim["nature"]
    assert "연주 정축과 월주 경오가" in no_batchim["nature"]
    assert "일주 무오가" in no_batchim["nature"]
    assert "무은" not in "\n".join(no_batchim.values())
