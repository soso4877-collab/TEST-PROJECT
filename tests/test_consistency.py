# -*- coding: utf-8 -*-
"""교차챕터 대운 일관성(content.consistency) 검증 — 정미/병오 혼서 모순 재발 차단.

실사고 2026-06-14: 같은 PDF에서 현재 대운이 정미(8장)와 병오(11장)로 섞여 모순.
이 모듈이 (a) '현재로 서술된 대운 간지'를 추출하고, (b) 결정론 현재 대운과 불일치하거나
2종 이상이면 위반으로 보고하는지 검증한다.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import consistency as c  # noqa: E402


def _sec(sid, text):
    return SimpleNamespace(id=sid, final_text=text)


def test_current_framed_extracts_current_daewoon():
    # B 패턴: '{간지} 대운 초입' (실제 결함 문장 형태)
    assert "병오" in c.current_framed("지금 태수님은 병오 대운 초입에 들어서는 자리입니다")
    # A 패턴: '지금은 {간지} 대운'
    assert "정미" in c.current_framed("지금은 정미 대운을 지나는 시기입니다")
    # 미래/과거 단순 언급(현재 맥락 없음)은 잡지 않음
    assert c.current_framed("다음 대운으로 넘어가는 흐름을 봅니다") == set()


def test_check_flags_mixed_current_daewoon():
    sections = [
        _sec("flow", "지금은 정미 대운을 지나는 시기입니다."),
        _sec("closing", "지금 병오 대운 초입에 들어서는 자리입니다."),
    ]
    ok, bad = c.check(sections, expected_ko="정미")
    assert not ok
    # 잘못된 간지(병오)를 현재로 쓴 closing 이 위반에 잡혀야 함
    assert any(b.get("id") == "closing" and b.get("ganzhi") == "병오" for b in bad)
    # 전체 2종 이상 모순도 보고
    assert any("2종 이상" in b.get("why", "") for b in bad)


def test_check_passes_single_correct_current():
    sections = [
        _sec("flow", "지금은 정미 대운을 지나는 시기입니다."),
        _sec("closing", "마무리하며 강점을 정리합니다. 특정 대운을 현재로 단정하지 않습니다."),
    ]
    ok, bad = c.check(sections, expected_ko="정미")
    assert ok, bad


def test_offending_ids_targets_wrong_section():
    sections = [
        _sec("flow", "지금은 정미 대운을 지나는 시기입니다."),
        _sec("closing", "지금 병오 대운 초입입니다."),
    ]
    ids = c.offending_ids(sections, expected_ko="정미")
    assert ids == {"closing"}
    # 기대값 없으면 폴백 대상 없음(보수적)
    assert c.offending_ids(sections, None) == set()


def test_verify_gate_fails_on_mixed_daewoon_pdf():
    # 핵심 요구 검증: 같은 PDF에 현재 대운이 2종으로 섞이면 렌더 후 게이트가 빌드 실패시킨다.
    # (PyMuPDF 추출이 간지를 '대운/초입'에서 분리해 정규식을 무력화하지 않는지도 함께 확인.)
    from sajugen import config as cfg
    from sajugen.render import pdf as render_pdf
    from sajugen.render import verify as v

    secs = [
        SimpleNamespace(
            id="flow",
            title="시간의 흐름",
            source_keys=["m"],
            final_text="지금은 정미 대운을 지나는 시기입니다. " * 30,
        ),
        SimpleNamespace(
            id="closing",
            title="마무리",
            source_keys=["m"],
            final_text="지금 병오 대운 초입에 들어서는 자리입니다. " * 30,
        ),
    ]
    report = SimpleNamespace(sections=secs)
    fake_saju = SimpleNamespace(input_civil="테스트")
    bp = dict(cfg.brand("seodam"))
    path = render_pdf.render_pdf(report, fake_saju, "test_daewoon_gate.pdf", name="", brand=bp)
    r = v.verify(path)
    assert set(r["daewoon_current"]) == {"정미", "병오"}, r["daewoon_current"]
    assert r["daewoon_consistent"] is False
    assert r["gate_pass"] is False


def test_builder_report_daewoon_single_and_consistent(monkeypatch):
    # 통합(룰 경로·무API): 골격이 현재 대운(정미)을 단일 사실로 주입 → 전 챕터 단일 일치.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(saju, use_llm=False, ref_year=2026, name="김태수")
    assert rep.guard.daewoon_consistent is True
    assert "정미 대운 하나입니다" in rep.section("flow").final_text  # 단일 사실 주입
    allcur = set()
    for s in rep.sections:
        allcur |= c.current_framed(s.final_text)
    assert allcur == {"정미"}, allcur  # 병오 등 다른 대운이 '현재'로 새지 않음


def test_builder_reverts_section_that_frames_wrong_daewoon(monkeypatch):
    # revert 분기 검증(무LLM): compose 가 closing 챕터에서 병오(미래 대운)를 '현재'로 잘못
    # 서술하면 빌더가 그 챕터를 결정론 골격으로 되돌린다.
    from sajugen.calc import engine
    from sajugen.content import builder, llm_sections
    from sajugen.content.question_router import classify

    class _FakeBackend:
        name = "anthropic"

        def classify(self, concern):  # concern=None 이라 호출 안 됨
            return classify(concern)

        def compose(self, *, section_id, base_text, **kw):
            if section_id == "closing":
                return "마무리하며 한마디 드립니다. 지금 병오 대운 초입에 들어서는 자리예요. 강점을 살려 보세요."
            return base_text  # 그 외 챕터는 변화 없음(골격 유지)

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _FakeBackend())
    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(saju, use_llm=True, ref_year=2026, name="김태수")
    closing = rep.section("closing").final_text
    assert "병오 대운 초입" not in closing  # 잘못된 현재 대운 서술 → 골격 폴백
    assert rep.guard.daewoon_consistent is True
    allcur = set()
    for s in rep.sections:
        allcur |= c.current_framed(s.final_text)
    assert "병오" not in allcur
