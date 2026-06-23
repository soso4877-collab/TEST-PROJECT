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


def test_rule_backend_compose_passthrough(monkeypatch):
    # 구간2·3·4 본문 생성: 무키(RuleBackend)면 근거 본문 그대로(결정론·무비용)
    _no_key(monkeypatch)
    b = llm_sections.get_backend()
    for sid in ("together", "consult", "closing"):
        out = b.compose(section_id=sid, title="제목", category="직업", base_text="근거 본문 그대로")
        assert out == "근거 본문 그대로", sid


# --- 질문 분류 골든(결정론 키워드) ---


def test_classify_golden():
    cases = [
        ("올해 이직 고민이에요", _C.JOB),
        ("남자친구랑 재회하고 싶어요", _C.LOVE),
        ("전남친과 다시 만날 수 있을까요", _C.LOVE),
        ("소개팅은 언제가 좋을까요", _C.LOVE),
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
    assert classify("재회 시기 언제가 좋을까요") == _C.LOVE


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
    # 무키 → LLM 미수행(polished False). final 은 한자 표시정리만 적용될 수 있음(LLM 아님).
    for s in rep.sections:
        assert s.polished is False


# --- 고민 입력 배선(구간1 분류 + 구간3 라우팅 섹션) ---


def test_strip_artifacts_markdown_leak():
    # 2026-06-12 실사고: LLM 출력의 '---' 수평선이 본문에 인쇄됨 — 재발 방지 앵커
    raw = (
        "그래서 구체적으로 이야기하면,\n\n- 쉬는 것을 일과로 넣어야 해요.\n"
        "1. 수면이 중요합니다.\n---\n***\n> 몸의 신호를 그냥 넘기지 마세요.\n"
        "**강조**도 `코드`도 안 됩니다."
    )
    out = builder._strip_artifacts(raw)
    assert "---" not in out and "***" not in out
    assert "- 쉬는" not in out and "1. 수면" not in out
    assert "**" not in out and "`" not in out and "> " not in out
    assert "쉬는 것을 일과로 넣어야 해요." in out  # 내용은 보존
    assert "몸의 신호를 그냥 넘기지 마세요." in out


def test_no_ai_tells_in_nonstatic_chapters(monkeypatch):
    # 재편 회귀 앵커: 룰 폴백(무키)이라도 해석 챕터에 AI틱 표식이 없어야 한다.
    # 한자·원문자·라벨·불릿·화살표·나열('첫째/먼저,')·수평선·'당신' 부재. (정적 면제)
    import re

    _no_key(monkeypatch)
    rep = builder.build_report(_saju(), use_llm=False, ref_year=2026, concern="올해 이직")
    static = {"cover", "toc", "appendix_terms", "colophon"}
    bad = re.compile(
        r"첫째,|둘째,|셋째,|먼저, |그리고, |끝으로, |[①②③④⑤]|→|\[원국\]"
        r"|\[기운 분포\]| · |[一-鿿]|^-{3,}\s*$|당신|점수|—|–"
        r"|물길|항해|여정|등불|수놓|결을 따라 걷",
        re.M,
    )
    offenders = {
        s.id: sorted(set(bad.findall(s.final_text)))
        for s in rep.sections
        if s.id not in static and bad.search(s.final_text)
    }
    assert not offenders, offenders


def test_concern_flows_to_category_and_consult_section(monkeypatch):
    _no_key(monkeypatch)
    rep = builder.build_report(_saju(), use_llm=False, concern="올해 이직해도 될까요")
    assert rep.concern_category == "직업", rep.concern_category
    consult = next(s for s in rep.sections if s.id == "consult")
    assert "직업" in consult.final_text and consult.final_text.strip()
    # 라우팅 섹션도 가드 clean(비단정·간지 없음)
    assert rep.guard.clean is True


def test_love_concern_answers_near_term_first(monkeypatch):
    _no_key(monkeypatch)
    rep = builder.build_report(
        _saju(),
        use_llm=False,
        ref_year=2026,
        concern="전남친과 재회 시기 언제가 좋을까요",
    )
    assert rep.concern_category == "연애", rep.concern_category
    consult = rep.section("consult").final_text
    assert consult.startswith("먼저 핵심부터 말하면"), consult
    assert "앞으로 1년 안" in consult
    assert "판단 지점" in consult
    assert "상대가 실제로 대화를 이어 오는지" in consult
    assert "재회합니다" not in consult and "결혼합니다" not in consult
    assert rep.guard.clean is True


def test_compose_prompt_has_no_ttorot_repetition():
    text = Path("sajugen/content/llm_sections.py").read_text(encoding="utf-8")
    assert text.count("또렷") == 0


def test_no_concern_defaults_general_and_section_present():
    rep = builder.build_report(_saju(), use_llm=False)  # concern 없음
    assert rep.concern_category == "전반"
    consult = next(s for s in rep.sections if s.id == "consult")
    assert "전반" in consult.final_text
    assert rep.guard.clean is True


def test_concern_raw_text_not_injected_into_body():
    # 고객 원문(단정·간지 포함)이 본문에 그대로 들어가지 않아야 함(주입 차단)
    rep = builder.build_report(
        _saju(), use_llm=False, concern="저는 甲寅생인데 반드시 100% 성공하나요"
    )
    consult = next(s for s in rep.sections if s.id == "consult")
    assert "甲寅" not in consult.final_text  # 차트에 없는 간지 미주입
    assert "100%" not in consult.final_text and "반드시" not in consult.final_text
    assert rep.guard.clean is True  # 카테고리(전반) 기반 안전 템플릿만
