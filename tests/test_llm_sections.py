# -*- coding: utf-8 -*-
"""Phase 5 룰 폴백 골격 — 무키 경로 결정론·가드 clean 검증.

키 없는 환경에서: 백엔드=Rule, 질문분류=키워드 룰, 윤문=원문 패스스루,
build_report(use_llm=True)도 전 섹션 룰 폴백으로 가드 통과(비용 0).
Anthropic 실호출 경로는 키 환경 수동 A/B 대상(여기선 비검증).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, llm_sections  # noqa: E402
from sajugen.content.question_router import QuestionCategory, classify  # noqa: E402

_C = QuestionCategory


def _no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


# --- 백엔드 선택 ---


def test_get_backend_rule_when_no_key(monkeypatch):
    _no_key(monkeypatch)
    b = llm_sections.get_backend()
    assert b.name == "rule", b.name
    assert b.available() is True
    assert isinstance(b, llm_sections.RuleBackend)


def test_backend_protocol_surface(monkeypatch):
    _no_key(monkeypatch)
    b = llm_sections.get_backend()
    # 프로토콜 메서드 존재
    assert b.classify("올해 이직") == _C.JOB
    assert b.polish("원문 그대로", "직업·일") == "원문 그대로"  # 패스스루


# --- 질문 분류 골든(결정론 키워드) ---


def test_classify_golden():
    cases = [
        ("올해 이직 고민이에요", _C.JOB),
        ("남자친구랑 재회하고 싶어요", _C.LOVE),
        ("주식 투자 시기 괜찮을까요", _C.WEALTH),  # 투자/주식이 시기보다 우선
        ("요즘 건강이 걱정돼요", _C.HEALTH),
        ("부모님과 갈등이 있어요", _C.RELATION),
        ("이사 가기 좋은 때가 언제일까요", _C.TIMING),
        ("그냥 운이 궁금해요", _C.GENERAL),
        (None, _C.GENERAL),
        ("", _C.GENERAL),
    ]
    for concern, expect in cases:
        assert classify(concern) == expect, (concern, classify(concern))


def test_classify_priority_love_over_timing():
    # '언제 결혼'은 연애(앞) 우선
    assert classify("언제 결혼할 수 있을까요") == _C.LOVE


def test_rule_backend_classify_matches_router(monkeypatch):
    _no_key(monkeypatch)
    b = llm_sections.get_backend()
    assert b.classify("창업 준비 중이에요") == classify("창업 준비 중이에요") == _C.JOB


# --- build_report 무키 통합(기존 폴백 패턴 보존) ---


def _saju():
    return engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")


def test_build_report_no_key_is_rule_fallback_and_clean(monkeypatch):
    _no_key(monkeypatch)
    rep = builder.build_report(_saju(), use_llm=True, ref_year=2026)
    # 무키 → 윤문 0(전부 룰 원문), 가드 clean
    assert rep.guard.polished_sections == 0, rep.guard.polished_sections
    assert rep.guard.clean is True
    assert rep.guard.safe_lint_total == 0 and rep.guard.factcheck_total == 0
    # 모든 섹션 final == rule(폴백)
    for s in rep.sections:
        assert s.final_text == s.rule_text
        assert s.polished is False
