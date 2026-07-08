# -*- coding: utf-8 -*-
"""QI-2026-07-04-02 월 단위 시제 오류 — 지난 달을 행동 시기로 권하는 풀이 차단 양방 회귀.

실사고: 2026-07-04 생성 풀이가 "4월 안에 재물 준비를 시작해 두라", "5월 이후부터 열어두고
보시길 권합니다"를 권함(둘 다 이미 지난 달). 기존 월 검사는 도착동사(다가오/오면) 전용이라
행동 권유 프레임을 놓쳤다(사각 인접). 회고 서술·미래 달 권유는 계속 통과(오탐 0).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import temporal_lint as tl  # noqa: E402

_REF = "2026-07-04"  # 실사고 기준일


def test_past_month_deadline_is_flagged():
    # 실사고 문장 그대로 — 지난 달 행동 마감
    hits = tl.lint(
        "지금 당장 할 수 있는 것 하나만 꼽는다면, 4월 안에 재물과 관련된 준비를 하나라도 구체적으로 시작해 두는 것입니다.",
        2026,
        ref_date=_REF,
    )
    assert hits, "4월(지남) 행동 마감을 잡아야 한다"


def test_past_month_anchor_recommendation_is_flagged():
    # 실사고 문장 그대로 — 지난 달을 권유 기점으로
    hits = tl.lint("5월 이후부터 더 열어두고 보시길 권합니다.", 2026, ref_date=_REF)
    assert hits, "5월(지남) 기점 권유를 잡아야 한다"


def test_future_month_recommendations_pass():
    # 미래 달 권유도 맨몸 n월 대신 간지월(절기명 - 양력 M/D~M/D)로 쓰면 정상.
    for text in (
        "정유월(백로 - 양력 9/7~10/8) 안에 준비를 시작해 두면 좋습니다.",
        "무술월(한로 - 양력 10/8~11/7) 이후부터 열어두고 보시길 권합니다.",
        "병신월(입추 - 양력 8/7~9/7)부터 시작되는 흐름을 보세요.",
    ):
        assert not tl.lint(text, 2026, ref_date=_REF), text


def test_retrospective_past_month_passes():
    # 회고 서술도 월운 표기는 절기 구간을 함께 써야 한다.
    for text in (
        "지난 계사월(입하 - 양력 5/5~6/5)에는 지출이 컸을 수 있습니다.",
        "임진월(청명 - 양력 4/4~5/5)의 흐름은 무거웠습니다.",
        "계사월(입하 - 양력 5/5~6/5)에 있었던 일은 정리 국면이었습니다.",
    ):
        assert not tl.lint(text, 2026, ref_date=_REF), text


def test_no_ref_date_keeps_legacy_behavior():
    # ref_date 가 없어도 맨몸 n월 표기는 차단한다. 과거/미래 월 판단만 생략된다.
    assert tl.lint("4월 안에 준비를 시작해 두세요.", 2026)


def test_next_year_past_month_number_passes():
    # 연도 명시가 미래여도 맨몸 n월은 금지다. 간지월 구간 표기를 갖추면 정상.
    assert not tl.lint(
        "2027년 정묘월(경칩 - 양력 3/6~4/5)부터 준비를 시작해 보세요.",
        2026,
        ref_date=_REF,
    )


def test_compose_prompt_carries_month_anchor_and_feedback(monkeypatch):
    # 생성 층 배선: compose 프롬프트에 '오늘은 N월' 닻과 재작성 피드백이 실리는지.
    import sys as _sys
    import types

    captured = {}
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *a, **kw):
            captured["prompt"] = kw["messages"][0]["content"]
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(type="text", text="새 문장")],
                usage=types.SimpleNamespace(input_tokens=1, output_tokens=1),
            )

    class _Anthropic:
        def __init__(self, *a, **kw):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(_sys.modules, "anthropic", fake)

    from sajugen.content import llm_sections

    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    out = backend.compose(
        section_id="consult",
        title="상담",
        category="재물",
        base_text="근거",
        ref_year=2026,
        ref_date="2026-07-04",
        feedback="쯤",
    )
    assert out == "새 문장"
    p = captured["prompt"]
    assert "오늘은 2026년 7월 4일" in p  # 월 단위 닻
    assert "7월부터 12월" in p  # 남은 기간 지시
    assert "간지월(절기명 - 양력 M/D~M/D)" in p  # 월운 표기 규약
    assert "재작성 사유" in p and "쯤" in p  # 위반 피드백
