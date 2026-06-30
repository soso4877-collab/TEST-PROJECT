# -*- coding: utf-8 -*-
import sys
import types

from sajugen import gunghap as g
from sajugen.content import llm_polish, llm_sections
from sajugen.content.question_router import QuestionCategory


def _install_anthropic(monkeypatch, *, text="LLM 문장", error: Exception | None = None):
    calls = []
    constructor_kwargs = []
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            if error is not None:
                raise error
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

    def from_anthropic(client):
        wrapped = types.SimpleNamespace(messages=_Messages(), raw_client=client)
        wrapped_clients.append(wrapped)
        return wrapped

    fake.from_anthropic = from_anthropic
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
        ["가현", "상철"],
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
        ["가현", "상철"],
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


def test_llm_sections_classify_instructor_client_disables_sdk_retries(monkeypatch):
    _, constructor_kwargs = _install_anthropic(monkeypatch)
    wrapped = _install_instructor(
        monkeypatch,
        response=types.SimpleNamespace(category=QuestionCategory.LOVE),
    )
    backend = llm_sections.AnthropicBackend()

    out = backend.classify("전남친 재회")

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(wrapped) == 1
    assert len(wrapped[0].messages.calls) == 1
    assert wrapped[0].messages.calls[0]["kwargs"]["max_retries"] == 0
    assert out == QuestionCategory.LOVE


def test_llm_sections_classify_first_api_exception_does_not_recall(monkeypatch):
    _, constructor_kwargs = _install_anthropic(monkeypatch)
    wrapped = _install_instructor(monkeypatch, error=RuntimeError("synthetic api failure"))
    fallback_calls = []
    sentinel = QuestionCategory.RELATION

    def fake_rule_classify(concern):
        fallback_calls.append(concern)
        return sentinel

    monkeypatch.setattr(llm_sections, "_rule_classify", fake_rule_classify)
    backend = llm_sections.AnthropicBackend()

    out = backend.classify("관계 흐름")

    assert constructor_kwargs == [{"max_retries": 0}]
    assert len(wrapped) == 1
    assert len(wrapped[0].messages.calls) == 1
    assert wrapped[0].messages.calls[0]["kwargs"]["max_retries"] == 0
    assert fallback_calls == ["관계 흐름"]
    assert out == sentinel
    assert "synthetic api failure" not in str(out)


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
