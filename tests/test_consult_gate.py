# -*- coding: utf-8 -*-
"""P2(2026-07-05) consult 직답성 게이트 + 폴백 억제 — QI-2026-07-05-03 양방 회귀.

v7 실사고: 질문 답변 챕터가 388자 유보 골격으로 붕괴했는데 게이트는 intro 초반만
검사해 false-PASS. 이 스위트는 (a) consult_direct_result 양방, (b) builder compose
가드 배선, (c) consult 한정 2차 재시도, (d) pipeline 하드 게이트를 고정한다. PII 0.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, delivery_quality, llm_polish, llm_sections  # noqa: E402
from sajugen.content.question_router import QuestionCategory  # noqa: E402

_CONCERN = "요즘 돈 문제와 매매 계약 시기가 크게 고민이 됩니다."

# 직답형(방향+시기+행동+질문축) 합성 텍스트 — 500자+ (통과 케이스)
_DIRECT = (
    "결론부터 말하면, 이 고민은 2026년 하반기부터 2027년 상반기까지 안에 매듭을 짓는 쪽이 "
    "맞습니다. 계약과 큰돈이 걸린 자리에서는 확정된 조건과 말뿐인 조건을 나누어 확인하고, "
    "가장 작은 것부터 실행해 반응을 보십시오. "
) * 6

# v7형 유보 골격(388자급, 시기·행동 표지 빈약) — 차단 케이스
_VAGUE = (
    "신청해 주신 고민은 재물 영역에 닿아 있습니다. 좋다 나쁘다를 한마디로 끝내기보다 "
    "천천히 읽어 주세요. 이 결과지는 기준을 잡기 위한 글로 읽어 주세요."
)


def _cached(text: str):
    return llm_sections.ComposeResult(text, cache_observed=True, api_succeeded=True)


def test_consult_direct_result_two_way():
    ok = delivery_quality.consult_direct_result(_DIRECT, _CONCERN)
    assert ok["ok"] is True and ok.get("skipped") is False
    bad = delivery_quality.consult_direct_result(_VAGUE, _CONCERN)
    assert bad["ok"] is False
    assert any(m.startswith("min_chars") for m in bad["missing"])
    # concern 부재 = skipped 구분 보고(조용한 no-op 금지, B-2)
    skipped = delivery_quality.consult_direct_result(_VAGUE, None)
    assert skipped["ok"] is True and skipped["skipped"] is True


def test_skeleton_consult_passes_gate():
    # 정상 통과: P1 재작성 골격은 이 게이트를 통과한다(폴백 경로 성립 보장).
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    from sajugen.content import rules

    T = rules.build_all(
        saju, ref_year=2026, name="테스트", concern_category="재물", concern_text=_CONCERN
    )
    r = delivery_quality.consult_direct_result(T["consult"], _CONCERN)
    assert r["ok"] is True, r


class _VagueThenDirectBackend:
    """1차·재시도 1회는 유보 문안, 2차 재시도에서 직답 문안 — consult 2차 재시도 검증용."""

    name = "anthropic"

    def __init__(self):
        self.consult_calls = 0

    def classify(self, concern):
        return QuestionCategory.WEALTH

    def compose(self, *, base_text, section_id, **kw):
        if section_id != "consult":
            return _cached(base_text + " 흐름을 차분히 살피면 좋습니다.")
        self.consult_calls += 1
        if self.consult_calls <= 2:
            return _cached(_VAGUE)
        return _cached(_DIRECT)


def test_consult_second_retry_recovers_direct_answer(monkeypatch):
    # 1차(유보)→재시도1(유보)→재시도2(직답) 시나리오: consult 한정 2차 재시도로 회복.
    be = _VagueThenDirectBackend()
    monkeypatch.setattr(llm_sections, "get_backend", lambda: be)
    monkeypatch.setattr(llm_polish, "polish", lambda text, title, **kw: text)
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    r = builder.build_report(saju, use_llm=True, ref_year=2026, name="테스트", concern=_CONCERN)
    assert be.consult_calls == 3  # 본경로 1 + 재시도 2(consult 한정)
    assert r.section("consult").polished is True
    assert "결론부터 말하면" in r.section("consult").final_text
    assert "consult" not in r.guard.fallback_section_ids


class _AlwaysVagueBackend(_VagueThenDirectBackend):
    def compose(self, *, base_text, section_id, **kw):
        if section_id != "consult":
            return _cached(base_text + " 흐름을 차분히 살피면 좋습니다.")
        self.consult_calls += 1
        return _cached(_VAGUE)


def test_consult_falls_back_to_skeleton_when_llm_stays_vague(monkeypatch):
    # 차단 측: 2차 재시도까지 유보 문안이면 골격 폴백(직답 골격이 최종 표면).
    be = _AlwaysVagueBackend()
    monkeypatch.setattr(llm_sections, "get_backend", lambda: be)
    monkeypatch.setattr(llm_polish, "polish", lambda text, title, **kw: text)
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    r = builder.build_report(saju, use_llm=True, ref_year=2026, name="테스트", concern=_CONCERN)
    assert be.consult_calls == 3  # 재시도 상한 소진
    sec = r.section("consult")
    assert sec.polished is False
    assert "consult" in r.guard.fallback_section_ids
    assert "먼저 핵심부터 말하면" in sec.final_text  # 폴백 = P1 직답 골격(topics 분기)
    # 폴백 골격도 게이트 통과(파이프라인 하드 게이트에서 안 막힘)
    assert delivery_quality.consult_direct_result(sec.final_text, _CONCERN)["ok"] is True


def test_other_sections_keep_single_retry(monkeypatch):
    # 이웃 사각: consult 외 챕터는 재시도 1회 유지(비용 상한 불변).
    calls = {"nature": 0}

    class _NatureVague(_VagueThenDirectBackend):
        def compose(self, *, base_text, section_id, **kw):
            if section_id == "nature":
                calls["nature"] += 1
                return _cached(base_text + " 반드시 성공합니다.")  # 가드 위반 지속
            return _cached(base_text + " 흐름을 차분히 살피면 좋습니다.")

    be = _NatureVague()
    monkeypatch.setattr(llm_sections, "get_backend", lambda: be)
    monkeypatch.setattr(llm_polish, "polish", lambda text, title, **kw: text)
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    r = builder.build_report(saju, use_llm=True, ref_year=2026, name="테스트", concern=_CONCERN)
    assert calls["nature"] == 2  # 본경로 1 + 재시도 1(2차 없음)
    assert "nature" in r.guard.fallback_section_ids
