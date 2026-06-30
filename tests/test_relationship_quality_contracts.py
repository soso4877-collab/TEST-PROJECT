# -*- coding: utf-8 -*-
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import hrun  # noqa: E402
from sajugen import config as cfg  # noqa: E402
from sajugen import gunghap as g  # noqa: E402
from sajugen.relationship import delivery_gate  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402


_MODEL_ENVS = (
    "SAJUGEN_LLM_COMPOSE_MODEL",
    "SAJUGEN_LLM_RELATIONSHIP_COMPOSE_MODEL",
    "SAJUGEN_LLM_CLASSIFY_MODEL",
    "SAJUGEN_LLM_POLISH_MODEL",
)


def _install_counting_anthropic(monkeypatch):
    calls = []
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return types.SimpleNamespace(content=[types.SimpleNamespace(text="LLM 문장")])

    class _Anthropic:
        def __init__(self, *args, **kwargs):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    return calls


@pytest.mark.parametrize(
    ("fallback_text", "raw_fragment", "must_be_removed_by_finalize"),
    [
        ("고객 질문: 원문 노출", "원문 노출", True),
        ("상담 대상: 가현 씨", "가현", True),
        ("이 장에서 가장 중요한 기준은 반복 태도입니다.", "이 장에서", True),
        ("사주도령 전문 상담 안내입니다", "전문 상담", False),
        ("내부 근거 자료입니다", "근거 자료", False),
    ],
)
def test_relationship_raw_fallback_gate_violation_blocks_anthropic_api(
    monkeypatch, fallback_text, raw_fragment, must_be_removed_by_finalize
):
    calls = _install_counting_anthropic(monkeypatch)
    finalized = g._finalize(fallback_text)
    if must_be_removed_by_finalize:
        assert raw_fragment not in finalized

    with pytest.raises(delivery_gate.DeliveryGateError) as ei:
        g._compose(
            "overview",
            "두 사람의 관계 흐름은 반복 태도와 안정성을 기준으로 정리합니다.",
            {"ganzhi": [], "ganzhi_ko": []},
            "",
            [],
            2026,
            fallback_text=fallback_text,
            use_llm=True,
        )

    assert calls == []
    failure_summary = {"failures": ei.value.failures}
    assert fallback_text not in str(ei.value)
    assert fallback_text not in str(failure_summary)
    assert raw_fragment not in str(ei.value)
    assert raw_fragment not in str(failure_summary)
    assert ei.value.failures[0]["field"] == "fallback"


@pytest.mark.parametrize(
    ("regen_returncode", "verify_result", "expected_reason"),
    [
        (1, {"status": "verified", "gate_pass": True}, "pdf_regen_failed"),
        (0, {"status": "verified", "gate_pass": False, "quality_clean": False}, "quality_clean"),
    ],
)
def test_hrun_retry_blocked_stops_api_after_pdf_failure(
    monkeypatch, regen_returncode, verify_result, expected_reason
):
    monkeypatch.setenv("SAJUGEN_HARNESS_ALLOW_REGEN", "1")
    monkeypatch.setattr(hrun, "_load_common", lambda: {"python": "python", "report_dir": "memory"})
    monkeypatch.setattr(
        hrun.hpreflight,
        "run",
        lambda: {"branch": "test", "preflight_ok": True, "status_short_count": 0},
    )
    monkeypatch.setattr(
        hrun.hsummary,
        "write_report",
        lambda summary, report_dir, stamp: {"json": "memory.json", "md": "memory.md"},
    )
    monkeypatch.setattr(hrun.hstate, "write_state", lambda path, state: state)
    monkeypatch.setattr(
        hrun.hverify_pdf,
        "load_profile",
        lambda path: {"type": "personal", "pdf": f"{path}.pdf"},
    )

    api_calls = []

    def fake_regen(profile, python):
        api_calls.append(profile["type"])
        return {"returncode": regen_returncode}

    def fake_verify(profile):
        out = {"type": profile["type"], "pdf": profile["pdf"]}
        out.update(verify_result)
        return out

    monkeypatch.setattr(hrun, "_regen_pdf", fake_regen)
    monkeypatch.setattr(hrun.hverify_pdf, "verify_profile", fake_verify)

    s = hrun.run(
        ["synthetic-a", "synthetic-b"],
        types.SimpleNamespace(regen=True, allow_llm=True, no_tests=True, stamp="pytest-api-block"),
    )

    assert api_calls == ["personal"]
    assert s["retry_blocked"] is True
    assert s["retry_reasons"][0] == expected_reason
    assert s["pdfs"][1]["regen"] == "blocked_after_failure"


def test_llm_model_environment_override(monkeypatch):
    for env_name in _MODEL_ENVS:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv("SAJUGEN_LLM_COMPOSE_MODEL", "compose-test-model")
    monkeypatch.setenv("SAJUGEN_LLM_RELATIONSHIP_COMPOSE_MODEL", "relationship-test-model")
    monkeypatch.setenv("SAJUGEN_LLM_CLASSIFY_MODEL", "classify-test-model")
    monkeypatch.setenv("SAJUGEN_LLM_POLISH_MODEL", "polish-test-model")

    assert cfg.llm_model("compose") == "compose-test-model"
    assert cfg.llm_model("relationship_compose") == "relationship-test-model"
    assert cfg.llm_model("classify") == "classify-test-model"
    assert cfg.llm_model("polish") == "polish-test-model"


def test_llm_model_default_ids_without_environment(monkeypatch):
    for env_name in _MODEL_ENVS:
        monkeypatch.delenv(env_name, raising=False)

    assert cfg.llm_model("compose") == "claude-sonnet-4-6"
    assert cfg.llm_model("relationship_compose") == "claude-sonnet-4-6"
    assert cfg.llm_model("classify") == "claude-haiku-4-5-20251001"
    assert cfg.llm_model("polish") == "claude-haiku-4-5-20251001"


@pytest.mark.parametrize(
    ("brand", "match"),
    [
        (None, "brand"),
        ({"cover_title": "합성 표지", "closing_sign": "합성 서명"}, "seal"),
    ],
)
def test_render_pdf_requires_explicit_brand_before_pdf_generation(monkeypatch, brand, match):
    makedirs_calls = []
    monkeypatch.setattr(render_pdf.os, "makedirs", lambda *args, **kwargs: makedirs_calls.append(args))

    report = types.SimpleNamespace(sections=[])
    saju = types.SimpleNamespace(input_civil="synthetic")

    with pytest.raises(ValueError, match=match):
        render_pdf.render_pdf(report, saju, "should_not_be_created.pdf", brand=brand)

    assert makedirs_calls == []
