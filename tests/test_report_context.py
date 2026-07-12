# -*- coding: utf-8 -*-
"""PDF 공유 문맥·prompt cache 배선 — 실제 API 없이 계약을 고정한다."""

from __future__ import annotations

import sys
import threading
import time
import types

import pytest

from sajugen.calc import engine
from sajugen.content import builder, llm_sections, llm_usage, report_context
from sajugen.content.question_router import QuestionCategory


def test_report_context_is_deterministic_and_cannot_accept_customer_text():
    first = report_context.build_report_context(
        selected_modules=["wealth", "love"],
        question_category="직업",
        active_section_ids=["consult", "intro", "work"],
    )
    second = report_context.build_report_context(
        selected_modules=["love", "wealth"],
        question_category="직업",
        active_section_ids=["work", "intro", "consult"],
    )
    assert first == second
    assert first.selected_modules == ("love", "wealth")
    assert first.to_prompt() == second.to_prompt()
    active_owners = dict(first.glossary_owner_by_concept)
    active_sections = {section_id for section_id, _ownership in first.section_ownership}
    assert set(active_owners.values()) <= active_sections
    for concept, explanation in report_context.GLOSSARY_EXPLANATIONS.items():
        owner = active_owners[concept]
        assert (
            f"- {concept} (이번 상품 설명 소유 장: {owner}): {explanation}"
            in first.to_prompt()
        )

    # 합성 PII/질문/이전 산문을 받는 인터페이스 자체가 없고, 출력은 허용 ID에서만 만들어진다.
    prompt = first.to_prompt()
    for forbidden in ("합성고객", "1990-01-02", "10:30", "시험에 합격할까요"):
        assert forbidden not in prompt

    # 값 객체를 직접 만들더라도 허용 목록 밖 문자열은 fail-closed로 거부한다.
    with pytest.raises(ValueError, match="narrative"):
        report_context.ReportContext(
            selected_modules=("love",),
            question_category="직업",
            narrative_anchor_ids=("customer_free_text",),
            section_ownership=first.section_ownership,
            glossary_explanation_ids=first.glossary_explanation_ids,
            advice_boundary_ids=first.advice_boundary_ids,
            repetition_guard_ids=first.repetition_guard_ids,
        )


def test_report_context_rejects_omitted_or_noncanonical_policy_fields():
    valid = report_context.build_report_context(
        selected_modules=["job"],
        question_category="직업",
        active_section_ids=["intro", "consult"],
    )
    invalid_fields = (
        ("narrative_anchor_ids", valid.narrative_anchor_ids[:-1]),
        ("section_ownership", ()),
        ("section_ownership", tuple(reversed(valid.section_ownership))),
        ("glossary_explanation_ids", valid.glossary_explanation_ids[:-1]),
        ("glossary_owner_by_concept", valid.glossary_owner_by_concept[:-1]),
        ("advice_boundary_ids", valid.advice_boundary_ids[:-1]),
        ("repetition_guard_ids", valid.repetition_guard_ids[:-1]),
        ("selected_modules", ("job", "job")),
    )
    for field, value in invalid_fields:
        payload = dict(valid.__dict__)
        payload[field] = value
        with pytest.raises(ValueError):
            report_context.ReportContext(**payload)


def test_anthropic_compose_uses_explicit_five_minute_cached_system_prefix(monkeypatch):
    captured: dict[str, object] = {}
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(
                model="claude-sonnet-4-6",
                stop_reason="end_turn",
                content=[types.SimpleNamespace(type="text", text="합성 본문")],
                usage=types.SimpleNamespace(
                    input_tokens=40,
                    output_tokens=10,
                    cache_creation_input_tokens=30,
                    cache_read_input_tokens=0,
                ),
            )

    class _Anthropic:
        def __init__(self, **kwargs):
            assert kwargs == {"max_retries": 0}
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    context = report_context.build_report_context(
        selected_modules=["job"],
        question_category="직업",
        active_section_ids=["consult"],
    )

    llm_usage.reset()
    out = backend.compose(
        section_id="consult",
        title="질문 답변",
        category="직업",
        base_text="결정론 근거",
        report_context=context,
        attempt=2,
    )

    assert out == "합성 본문"
    system = captured["system"]
    assert isinstance(system, list) and len(system) == 2
    assert system[0] == {"type": "text", "text": llm_sections._COMPOSE_SYSTEM}
    assert system[1]["text"] == context.to_prompt()
    assert system[1]["cache_control"] == {"type": "ephemeral", "ttl": "5m"}
    assert captured["messages"][0]["content"].startswith(
        "[현재 장 ID]\nconsult\n\n[이 챕터에서 쓸 글]"
    )
    event = llm_usage.events_snapshot()[-1]
    assert event == {
        "role": "compose",
        "model": "claude-sonnet-4-6",
        "section": "consult",
        "attempt": 2,
        "input_tokens": 40,
        "cache_creation_input_tokens": 30,
        "cache_read_input_tokens": 0,
        "output_tokens": 10,
        "stop_reason": "end_turn",
    }


def test_glossary_owners_are_remapped_to_active_ziwei_product_sections():
    active_sections = ("intro", "love", "work", "health", "ziwei", "consult", "closing")
    context = report_context.build_report_context(
        selected_modules=["love", "job", "wealth", "health"],
        question_category="전반",
        active_section_ids=active_sections,
    )

    owners = dict(context.glossary_owner_by_concept)
    assert set(owners.values()) <= set(active_sections)
    assert owners["자미 계열 별 이름"] == "ziwei"
    assert owners["십성"] != report_context.GLOSSARY_OWNER_BY_CONCEPT["십성"]


def test_builder_warms_first_call_then_parallelizes_with_one_shared_context(monkeypatch):
    state_lock = threading.Lock()
    calls: list[tuple[str, int, int]] = []
    context_ids: list[int] = []
    context_prompts: list[str] = []
    active = 0
    max_active = 0
    warm_done = False
    main_thread = threading.get_ident()

    class _StubBackend:
        name = "anthropic"

        def classify(self, concern):
            return QuestionCategory.JOB

        def compose(self, *, section_id, base_text, report_context, attempt, **kwargs):
            nonlocal active, max_active, warm_done
            with state_lock:
                sequence = len(calls)
                calls.append((section_id, attempt, threading.get_ident()))
                context_ids.append(id(report_context))
                context_prompts.append(report_context.to_prompt())
                if sequence == 0:
                    assert section_id == "intro"
                    assert threading.get_ident() == main_thread
                else:
                    assert warm_done, "첫 compose 완료 전에 병렬 호출이 시작됨"
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.02)
            with state_lock:
                active -= 1
                if sequence == 0:
                    warm_done = True
            return llm_sections.ComposeResult(
                base_text,
                cache_observed=True,
                api_succeeded=True,
            )

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _StubBackend())
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    builder.build_report(
        saju,
        use_llm=True,
        ref_year=2026,
        name="합성고객",
        concern="시험 합격 시기가 궁금합니다",
    )

    initial_calls = [call for call in calls if call[1] == 1]
    assert len(initial_calls) == 12
    assert {section_id for section_id, _attempt, _thread in initial_calls} == builder._COMPOSE_SECTIONS
    # 다른 가드 작업이 consult 골격을 재작성시켜도 재시도는 같은 context와 증가한 attempt를 쓴다.
    assert all(section_id == "consult" for section_id, attempt, _thread in calls if attempt > 1)
    assert len(set(context_ids)) == 1
    assert len(set(context_prompts)) == 1
    assert max_active >= 2, "첫 호출 뒤 남은 챕터가 병렬로 실행되지 않음"
    shared_prompt = context_prompts[0]
    # 이름·질문 원문은 공통 문맥이 아니라 consult 전용 user 블록에만 들어갈 수 있다.
    assert "합성고객" not in shared_prompt
    assert "시험 합격 시기가 궁금합니다" not in shared_prompt


@pytest.mark.parametrize("fail_mode", ["not_observed", "api_error", "legacy_string"])
def test_builder_stops_after_warm_call_when_cache_is_unavailable(monkeypatch, fail_mode):
    calls: list[str] = []

    class _NoCacheBackend:
        name = "anthropic"

        def classify(self, concern):
            return QuestionCategory.JOB

        def compose(self, *, section_id, base_text, **kwargs):
            calls.append(section_id)
            if fail_mode == "api_error":
                raise RuntimeError("synthetic cache request failure")
            if fail_mode == "legacy_string":
                return base_text
            return llm_sections.ComposeResult(
                base_text,
                cache_observed=False,
                api_succeeded=True,
            )

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _NoCacheBackend())
    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    result = builder.build_report(
        saju,
        use_llm=True,
        ref_year=2026,
        name="합성고객",
        concern="직업 방향이 궁금합니다",
    )

    assert calls == ["intro"]
    assert not result.guard.polished_section_ids


def test_cache_control_without_observed_cache_is_visible(monkeypatch, capsys):
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, **kwargs):
            return types.SimpleNamespace(
                model="claude-sonnet-4-6",
                stop_reason="end_turn",
                content=[types.SimpleNamespace(type="text", text="합성 본문")],
                usage=types.SimpleNamespace(input_tokens=40, output_tokens=10),
            )

    class _Anthropic:
        def __init__(self, **kwargs):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    context = report_context.build_report_context(
        selected_modules=["job"],
        question_category="직업",
        active_section_ids=["consult"],
    )

    result = backend.compose(
        section_id="consult",
        title="질문 답변",
        category="직업",
        base_text="결정론 근거",
        report_context=context,
    )
    assert result == "합성 본문"
    assert result.cache_observed is False
    assert "[compose-fallback] consult: cache-not-observed" in capsys.readouterr().err
