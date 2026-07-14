# -*- coding: utf-8 -*-
import logging
import sys
import types

import pytest

from sajugen import gunghap as g
from sajugen.content import llm_polish, llm_sections, llm_usage
from sajugen.content.question_router import QuestionCategory


def _install_anthropic(
    monkeypatch,
    *,
    text="LLM 문장",
    response=None,
    error: Exception | None = None,
):
    calls = []
    constructor_kwargs = []
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            if error is not None:
                raise error
            if response is not None:
                return response
            return types.SimpleNamespace(
                content=[types.SimpleNamespace(type="text", text=text)],
                usage=types.SimpleNamespace(input_tokens=1, output_tokens=1),
            )

    class _Anthropic:
        def __init__(self, *args, **kwargs):
            constructor_kwargs.append(kwargs)
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    return calls, constructor_kwargs


def _classify_tool(payload, *, name=None):
    """실 API 없이 Anthropic tool_use 블록의 최소 구조만 합성한다."""

    return types.SimpleNamespace(
        type="tool_use",
        name=name or llm_sections._CLASSIFY_TOOL_NAME,
        input=payload,
    )


def _classify_response(*blocks):
    """파싱 성공·실패와 무관하게 과금 usage가 붙은 합성 응답을 만든다."""

    return types.SimpleNamespace(
        content=list(blocks),
        usage=types.SimpleNamespace(input_tokens=7, output_tokens=2),
        model="synthetic-classify-model",
        stop_reason="tool_use",
    )


def _install_instructor(monkeypatch, *, response=None, error: Exception | None = None):
    wrapped_clients = []
    fake = types.ModuleType("instructor")

    class _Messages:
        def __init__(self):
            self.calls = []

        def create(self, *args, **kwargs):
            self.calls.append({"args": args, "kwargs": kwargs})
            if kwargs.get("max_retries") != 0:
                raise AssertionError("Instructor messages.create must set max_retries=0")
            if error is not None:
                raise error
            return response

    def from_anthropic(client, mode=None):  # T5.4: classify 가 mode= 를 명시
        wrapped = types.SimpleNamespace(messages=_Messages(), raw_client=client, mode=mode)
        wrapped_clients.append(wrapped)
        return wrapped

    fake.from_anthropic = from_anthropic
    # T5.4: instructor.Mode.ANTHROPIC_TOOLS 참조 지원(classify 가 도구 모드 명시)
    fake.Mode = types.SimpleNamespace(ANTHROPIC_TOOLS="anthropic_tools")
    monkeypatch.setitem(sys.modules, "instructor", fake)
    return wrapped_clients


def test_gunghap_relationship_anthropic_client_disables_sdk_retries(monkeypatch):
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        text="두 사람의 흐름은 안정성을 중심으로 살피면 좋습니다.",
    )

    out = g._compose(
        "overview",
        "두 사람의 관계 흐름은 안정성을 기준으로 정리합니다.",
        {"ganzhi": [], "ganzhi_ko": []},
        "",
        ["하은", "준서"],
        2026,
        fallback_text="두 사람은 서로의 속도를 맞추는 일이 중요합니다.",
        use_llm=True,
    )

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    assert out


def test_gunghap_relationship_first_api_exception_does_not_recall(monkeypatch):
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        error=RuntimeError("synthetic api failure"),
    )

    out = g._compose(
        "overview",
        "두 사람의 관계 흐름은 안정성을 기준으로 정리합니다.",
        {"ganzhi": [], "ganzhi_ko": []},
        "",
        ["하은", "준서"],
        2026,
        fallback_text="두 사람은 서로의 속도를 맞추는 일이 중요합니다.",
        use_llm=True,
    )

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    assert out == "두 사람은 서로의 속도를 맞추는 일이 중요합니다."
    assert "synthetic api failure" not in out


def test_llm_polish_anthropic_client_disables_sdk_retries(monkeypatch):
    _, constructor_kwargs = _install_anthropic(monkeypatch)
    wrapped = _install_instructor(
        monkeypatch,
        response=types.SimpleNamespace(text="다듬은 문장"),
    )

    out = llm_polish.polish("원문 문장", "합성")

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(wrapped) == 1
    assert len(wrapped[0].messages.calls) == 1
    assert wrapped[0].messages.calls[0]["kwargs"]["max_retries"] == 0
    assert out == "다듬은 문장"


def test_llm_polish_first_api_exception_does_not_recall(monkeypatch):
    _, constructor_kwargs = _install_anthropic(monkeypatch)
    wrapped = _install_instructor(monkeypatch, error=RuntimeError("synthetic api failure"))

    out = llm_polish.polish("원문 문장", "합성")

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(wrapped) == 1
    assert len(wrapped[0].messages.calls) == 1
    assert wrapped[0].messages.calls[0]["kwargs"]["max_retries"] == 0
    assert out == "원문 문장"


def test_llm_sections_classify_uses_strict_tool_contract_and_records_usage(monkeypatch):
    response = _classify_response(
        _classify_tool({"category": QuestionCategory.LOVE.value})
    )
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        response=response,
    )
    monkeypatch.setattr(
        llm_sections.cfg,
        "llm_model",
        lambda role: "synthetic-classify-model" if role == "classify" else "unexpected-model",
    )
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    llm_usage.reset()

    out = backend.classify("SYNTHETIC_CLASSIFY_INPUT")

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    kwargs = calls[0]["kwargs"]
    assert kwargs["model"] == "synthetic-classify-model"
    assert kwargs["max_tokens"] == 256
    assert "max_retries" not in kwargs
    assert kwargs["system"] == llm_sections._CLASSIFY_SYSTEM
    assert kwargs["messages"] == [{"role": "user", "content": "SYNTHETIC_CLASSIFY_INPUT"}]
    assert kwargs["tool_choice"] == {
        "type": "tool",
        "name": llm_sections._CLASSIFY_TOOL_NAME,
    }
    assert len(kwargs["tools"]) == 1
    tool = kwargs["tools"][0]
    assert tool["name"] == llm_sections._CLASSIFY_TOOL_NAME
    assert tool["strict"] is True
    assert tool["input_schema"] == {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": [category.value for category in QuestionCategory],
            }
        },
        "required": ["category"],
        "additionalProperties": False,
    }
    assert out == QuestionCategory.LOVE
    assert llm_usage.snapshot() == {"input_tokens": 7, "output_tokens": 2, "calls": 1}
    event = llm_usage.events_snapshot()[-1]
    assert event["role"] == "classify"
    assert event["section"] == "question_category"
    assert event["stop_reason"] == "tool_use"


@pytest.mark.parametrize(
    "blocks",
    [
        pytest.param(
            [_classify_tool({"category": "INVALID_SYNTHETIC_CATEGORY"})],
            id="invalid-enum",
        ),
        pytest.param([_classify_tool({})], id="missing-category"),
        pytest.param(
            [
                _classify_tool(
                    {"category": QuestionCategory.LOVE.value, "unexpected": "synthetic"}
                )
            ],
            id="extra-field",
        ),
        pytest.param(
            [types.SimpleNamespace(type="text", text="SYNTHETIC_NON_TOOL_RESPONSE")],
            id="no-tool",
        ),
        pytest.param(
            [
                _classify_tool(
                    {"category": QuestionCategory.LOVE.value},
                    name="unexpected_tool",
                )
            ],
            id="wrong-tool-name",
        ),
        pytest.param(
            [
                _classify_tool({"category": QuestionCategory.LOVE.value}),
                _classify_tool({"category": QuestionCategory.JOB.value}),
            ],
            id="multiple-tools",
        ),
    ],
)
def test_llm_sections_classify_schema_failures_fallback_after_recording_usage(
    monkeypatch,
    caplog,
    blocks,
):
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        response=_classify_response(*blocks),
    )
    fallback_calls = []
    sentinel = QuestionCategory.RELATION

    def fake_rule_classify(concern):
        fallback_calls.append(concern)
        return sentinel

    monkeypatch.setattr(llm_sections, "_rule_classify", fake_rule_classify)
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    marker = "SYNTHETIC_CONCERN_MARKER"
    llm_usage.reset()
    caplog.set_level(logging.WARNING, logger=llm_sections.__name__)

    out = backend.classify(marker)

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    assert fallback_calls == [marker]
    assert out == sentinel
    assert llm_usage.snapshot() == {"input_tokens": 7, "output_tokens": 2, "calls": 1}
    assert "classify_fallback code=parse_error type=ValueError" in caplog.text
    assert marker not in caplog.text
    assert "INVALID_SYNTHETIC_CATEGORY" not in caplog.text
    assert "SYNTHETIC_NON_TOOL_RESPONSE" not in caplog.text


def test_llm_sections_classify_api_exception_is_single_call_without_usage_or_text_leak(
    monkeypatch,
    caplog,
):
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        error=RuntimeError("SYNTHETIC_PROVIDER_DETAIL"),
    )
    fallback_calls = []
    sentinel = QuestionCategory.RELATION

    def fake_rule_classify(concern):
        fallback_calls.append(concern)
        return sentinel

    monkeypatch.setattr(llm_sections, "_rule_classify", fake_rule_classify)
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    marker = "SYNTHETIC_CONCERN_MARKER"
    llm_usage.reset()
    caplog.set_level(logging.WARNING, logger=llm_sections.__name__)

    out = backend.classify(marker)

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    assert fallback_calls == [marker]
    assert out == sentinel
    assert llm_usage.snapshot() == {"input_tokens": 0, "output_tokens": 0, "calls": 0}
    assert "classify_fallback code=api_error type=RuntimeError" in caplog.text
    assert marker not in caplog.text
    assert "SYNTHETIC_PROVIDER_DETAIL" not in caplog.text


def test_llm_sections_compose_client_disables_sdk_retries(monkeypatch):
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        text="근거 안에서 풀어 쓴 문장입니다.",
    )
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)

    out = backend.compose(
        section_id="consult",
        title="상담",
        category="연애",
        base_text="근거 본문",
        quoted_concern="마스킹된 고민",
        ref_year=2026,
        call_name="고객",
    )

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    assert out == "근거 안에서 풀어 쓴 문장입니다."


def test_llm_sections_compose_first_api_exception_does_not_recall(monkeypatch):
    calls, constructor_kwargs = _install_anthropic(
        monkeypatch,
        error=RuntimeError("synthetic api failure"),
    )
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)

    out = backend.compose(
        section_id="consult",
        title="상담",
        category="연애",
        base_text="근거 본문",
        quoted_concern="마스킹된 고민",
        ref_year=2026,
        call_name="고객",
    )

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(calls) == 1
    assert out == "근거 본문"
    assert "synthetic api failure" not in out
