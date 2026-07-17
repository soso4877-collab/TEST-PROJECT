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
    # 생성 층 배선: 회피 사유와 형식 교정 사유가 서로 섞이지 않은 채 함께 실리는지 확인한다.
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
    fix_reason = (
        "월운은 간지월(절기명 - 양력 M/D~M/D) 또는 음력 n월 무렵으로 표기"
    )
    out = backend.compose(
        section_id="consult",
        title="상담",
        category="재물",
        base_text="근거",
        ref_year=2026,
        ref_date="2026-07-04",
        feedback="쯤",
        feedback_fix=fix_reason,
    )
    assert out == "새 문장"
    p = captured["prompt"]
    assert "오늘은 2026년 7월 4일" in p  # 월 단위 닻
    assert "7월부터 12월" in p  # 남은 기간 지시
    assert "간지월(절기명 - 양력 M/D~M/D)" in p  # 월운 표기 규약
    avoid_block = p.split("[재작성 사유 — 반드시 반영하라]", 1)[1].split(
        "[재작성 사유 — 형식 교정", 1
    )[0]
    fix_block = p.split("[재작성 사유 — 형식 교정", 1)[1].split(
        "[신청자가 묻고 싶어 한 영역]", 1
    )[0]
    assert "쯤" in avoid_block and "쓰지 말고" in avoid_block
    assert fix_reason in fix_block and "고쳐 다시 써라" in fix_block
    assert "간지월(절기명 - 양력 M/D~M/D)" not in avoid_block
    assert "쓰지 말고" not in fix_block


def test_retry_feedback_labels_routes_temporal_why_to_fix():
    # temporal 계열은 raw match를 금칙어처럼 되먹이지 않고 정답 형식이 든 why만 교정한다.
    from sajugen.content import builder

    why = "간지월(절기명 - 양력 M/D~M/D) 또는 음력 n월 무렵으로 표기"
    for violation_type in (
        "month_notation",
        "temporal",
        "relative_month_boundary",
    ):
        avoid, fix = builder._retry_feedback_labels(
            [{"type": violation_type, "match": "신사월", "why": why}],
            [],
            three_pillar=False,
        )

        assert fix == {why}
        assert "신사월" not in avoid

    # why가 없는 예외 finding은 정보를 버리지 않고 기존 회피형으로 안전하게 폴백한다.
    avoid, fix = builder._retry_feedback_labels(
        [{"type": "temporal", "match": "7월"}],
        [],
        three_pillar=False,
    )
    assert avoid == {"7월"}
    assert fix == set()


def test_retry_feedback_labels_keeps_safe_and_fact_tokens_in_avoid():
    # 진짜 금칙 표현과 근거 밖 간지는 기존 회피형을 유지해 가드가 느슨해지지 않게 한다.
    from sajugen.content import builder

    avoid, fix = builder._retry_feedback_labels(
        [{"match": "반드시 이루어집니다"}],
        [{"token": "경술"}],
        three_pillar=False,
    )

    assert avoid == {"반드시 이루어집니다", "경술"}
    assert fix == set()


def test_retry_feedback_labels_three_pillar_never_leaks_raw_or_why():
    # 삼주는 기존 보호 계약대로 고정 라벨만 전달하고 raw 토큰과 why를 모두 숨긴다.
    from sajugen.content import builder

    raw = "경오월"
    why = "간지월(절기명 - 양력 M/D~M/D)으로 표기"
    avoid, fix = builder._retry_feedback_labels(
        [{"type": "month_notation", "match": raw, "why": why}],
        [{"token": "경오"}],
        three_pillar=True,
    )

    assert avoid == {"작성 규칙 위반", "현재 장 근거에 없는 사실"}
    assert fix == set()
    assert raw not in avoid and why not in avoid


def test_known_time_builder_forwards_temporal_fix_feedback(monkeypatch):
    # helper만 바뀌고 실제 재시도 호출이 옛 feedback에 머무는 팬텀 배선을 막는다.
    from sajugen.calc import engine
    from sajugen.content import builder, llm_sections

    why = "간지월(절기명 - 양력 M/D~M/D) 또는 음력 n월 무렵으로 표기"
    calls = []

    class _Backend:
        name = "anthropic"

        def compose(
            self,
            *,
            section_id,
            base_text,
            attempt=1,
            feedback=None,
            feedback_fix=None,
            **_kwargs,
        ):
            calls.append((section_id, attempt, feedback, feedback_fix))
            if section_id == "flow" and feedback_fix is None:
                suffix = "신사월의 흐름을 살펴봅니다."
            elif section_id == "flow":
                suffix = "형식을 바로잡아 흐름을 살펴봅니다."
            else:
                suffix = "확인된 내용은 생활의 속도를 정하는 기준으로 활용해 주세요."
            return llm_sections.ComposeResult(
                base_text + "\n\n" + suffix,
                cache_observed=True,
                api_succeeded=True,
            )

    def _temporal_lint(text, *_args, **_kwargs):
        if "신사월의 흐름을 살펴봅니다" in text:
            return [{"type": "month_notation", "match": "신사월", "why": why}]
        return []

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _Backend())
    monkeypatch.setattr(builder.temporal_lint, "lint", _temporal_lint)
    monkeypatch.setattr(builder.factcheck, "check", lambda *_args, **_kwargs: [])

    saju = engine.build(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-07-04",
    )
    builder.build_report(
        saju,
        use_llm=True,
        ref_year=2026,
        ref_date="2026-07-04",
        product="integrated_full",
    )

    flow_retry = next(call for call in calls if call[:2] == ("flow", 2))
    assert flow_retry[2] is None
    assert flow_retry[3] == why
