# -*- coding: utf-8 -*-
"""삼주 계산 결과가 CLI·웹·파이프라인을 통과하는 오케스트레이션 계약."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from sajugen import app as web_app
from sajugen import cli, gunghap, pipeline
from sajugen.input.birth_time import BirthTimeMode


class _BoundaryError(ValueError):
    code = "NEEDS_INFO_TIME_BOUNDARY"


class _Dumpable(SimpleNamespace):
    def model_dump(self, **_kwargs):
        return dict(vars(self))


def _fake_gen_result(*, three_pillar: bool) -> pipeline.GenResult:
    guard = SimpleNamespace(
        polished_section_ids=[],
        fallback_section_ids=[],
    )
    return pipeline.GenResult(
        pdf_path="synthetic.pdf",
        ok=True,
        reasons=[],
        verify={"pages": 1, "text_chars": 1, "tagged": True},
        guard={"clean": True},
        bazi="甲子 乙丑 丙寅" if three_pillar else "甲子 乙丑 丙寅 丁卯",
        report=SimpleNamespace(guard=guard),
        three_pillar_provenance={"three_pillar_schema_version": 1}
        if three_pillar
        else None,
    )


def test_pipeline_forwards_three_pillar_mode_and_provenance(monkeypatch) -> None:
    captured: dict[str, dict] = {}
    provenance = _Dumpable(
        three_pillar_schema_version=1,
        candidate_count=12,
        candidate_digest="a" * 64,
        stable_fact_ids=["pillar.day"],
        suppressed_fact_ids=["ziwei"],
    )
    three = SimpleNamespace(
        year=SimpleNamespace(ganzhi="甲子"),
        month=SimpleNamespace(ganzhi="乙丑"),
        day=SimpleNamespace(ganzhi="丙寅"),
    )
    crosscheck = SimpleNamespace(
        month_branch_ok=True,
        year_branch_ok=True,
        kasi_consistent=True,
        near_term_boundary=False,
        warnings=[],
    )
    saju = SimpleNamespace(
        three_pillar=three,
        provenance=provenance,
        crosscheck=crosscheck,
        input_civil_date="2000-01-01",
    )
    guard = _Dumpable(clean=True)
    report = SimpleNamespace(
        guard=guard,
        partner_present=False,
        section=lambda _sid: SimpleNamespace(final_text="합성 상담 문장"),
    )

    def fake_engine(*args, **kwargs):
        captured["engine"] = {"args": args, **kwargs}
        return saju

    def fake_builder(*args, **kwargs):
        captured["builder"] = kwargs
        return report

    def fake_render(*args, **kwargs):
        captured["render"] = kwargs
        return "synthetic.pdf"

    def fake_verify(*args, **kwargs):
        captured["verify"] = kwargs
        return {"gate_pass": True, "pages": 1, "text_chars": 1, "tagged": True}

    monkeypatch.setattr(pipeline.engine, "build", fake_engine)
    monkeypatch.setattr(pipeline.builder, "build_report", fake_builder)
    monkeypatch.setattr(pipeline.builder, "personal_identity_spec", lambda *_args: None)
    monkeypatch.setattr(pipeline.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(pipeline.render_verify, "verify", fake_verify)
    monkeypatch.setattr(
        pipeline._delivery_quality,
        "consult_direct_result",
        lambda *_args, **_kwargs: {"ok": True},
    )

    result = pipeline.generate(
        2000,
        1,
        1,
        None,
        None,
        is_male=True,
        birth_time_mode="three_pillar",
        brand="default",
    )

    assert captured["engine"]["args"][3:5] == (None, None)
    assert captured["engine"]["birth_time_mode"] is BirthTimeMode.THREE_PILLAR
    assert captured["builder"]["birth_time_mode"] is BirthTimeMode.THREE_PILLAR
    assert captured["render"]["birth_time_mode"] is BirthTimeMode.THREE_PILLAR
    assert captured["verify"]["birth_time_mode"] is BirthTimeMode.THREE_PILLAR
    assert captured["verify"]["three_pillar_provenance"]["candidate_count"] == 12
    assert result.bazi.split() == ["甲子", "乙丑", "丙寅"]
    assert result.calc_consistent is True
    assert result.three_pillar_provenance["candidate_count"] == 12


def test_pipeline_real_three_pillar_content_without_pdf(monkeypatch) -> None:
    """실제 계산·골격을 연결하되 PDF/API는 호출하지 않는 통합 회귀."""

    monkeypatch.setattr(
        pipeline.render_pdf,
        "render_pdf",
        lambda *_args, **_kwargs: "synthetic.pdf",
    )
    monkeypatch.setattr(
        pipeline.render_verify,
        "verify",
        lambda *_args, **_kwargs: {
            "gate_pass": True,
            "pages": 1,
            "text_chars": 1,
            "tagged": True,
        },
    )

    result = pipeline.generate(
        2000,
        1,
        1,
        None,
        None,
        is_male=True,
        birth_time_mode="three_pillar",
        horoscope_date="2026-06-01",
        use_llm=False,
        name="합성",
        brand="default",
    )

    assert result.ok is True, result.reasons
    assert result.three_pillar_provenance["candidate_count"] == 12
    assert getattr(result.report, "birth_time_mode") == "three_pillar"
    assert len(result.bazi.split()) == 3


def test_pipeline_known_time_keeps_four_pillar_contract_without_pdf(monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline.render_pdf,
        "render_pdf",
        lambda *_args, **_kwargs: "synthetic.pdf",
    )
    monkeypatch.setattr(
        pipeline.render_verify,
        "verify",
        lambda *_args, **_kwargs: {
            "gate_pass": True,
            "pages": 1,
            "text_chars": 1,
            "tagged": True,
        },
    )

    result = pipeline.generate(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        birth_time_mode="known",
        horoscope_date="2026-06-01",
        use_llm=False,
        name="합성",
        brand="default",
    )

    assert result.ok is True, result.reasons
    assert result.three_pillar_provenance is None
    assert getattr(result.report, "birth_time_mode") == "known"
    assert len(result.bazi.split()) == 4


def test_pipeline_three_pillar_rejects_ziwei_product_before_calculation(monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline.engine,
        "build",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("삼주 자미 상품이 계산으로 진입하면 안 됩니다")
        ),
    )

    with pytest.raises(ValueError, match="자미두수 단독 상품"):
        pipeline.generate(
            2000,
            1,
            1,
            None,
            None,
            is_male=True,
            birth_time_mode="three_pillar",
            product="ziwei",
        )


def test_cli_date_only_passes_none_and_prints_three_pillar_label(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_generate(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _fake_gen_result(three_pillar=True)

    monkeypatch.setattr(cli, "generate", fake_generate)
    result = CliRunner().invoke(
        cli.app,
        ["gen", "--birth", "2000-01-01", "--gender", "여", "--name", "합성"],
    )

    assert result.exit_code == 0, result.output
    assert captured["args"][3:5] == (None, None)
    assert captured["kwargs"]["birth_time_mode"] is BirthTimeMode.THREE_PILLAR
    assert "삼주:" in result.output
    assert "사주팔자:" not in result.output


def test_cli_boundary_error_is_explicit_without_traceback(monkeypatch) -> None:
    monkeypatch.setattr(cli, "generate", lambda *_args, **_kwargs: (_ for _ in ()).throw(_BoundaryError()))
    result = CliRunner().invoke(
        cli.app,
        ["gen", "--birth", "2000-02-04", "--gender", "여", "--name", "합성"],
    )

    assert result.exit_code == 1
    assert "NEEDS_INFO_TIME_BOUNDARY" in result.output
    assert "Traceback" not in result.output
    assert "2000-02-04" not in result.output


def test_app_date_only_passes_none_and_boundary_is_422(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}
    output = tmp_path / "synthetic.pdf"
    output.write_bytes(b"%PDF-synthetic")

    def fake_success(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        result = _fake_gen_result(three_pillar=True)
        result.pdf_path = str(output)
        return result

    monkeypatch.setattr(web_app, "generate", fake_success)
    client = TestClient(web_app.app)
    response = client.post(
        "/generate",
        data={"birth": "2000-01-01", "gender": "female", "name": "합성"},
    )
    assert response.status_code == 200
    assert captured["args"][3:5] == (None, None)
    assert captured["kwargs"]["birth_time_mode"] is BirthTimeMode.THREE_PILLAR

    monkeypatch.setattr(
        web_app,
        "generate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(_BoundaryError()),
    )
    blocked = client.post(
        "/generate",
        data={"birth": "2000-02-04", "gender": "female", "name": "합성"},
    )
    assert blocked.status_code == 422
    assert blocked.json()["reasons"][0].startswith("NEEDS_INFO_TIME_BOUNDARY:")
    assert "2000-02-04" not in blocked.text


def test_gunghap_unknown_time_fails_closed_before_calculation(monkeypatch) -> None:
    monkeypatch.setattr(
        gunghap,
        "person_facts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("생시 미상 궁합이 계산으로 진입하면 안 됩니다")
        ),
    )

    people = [
        ("합성갑", (2000, 1, 1, None, None), True, True),
        ("합성을", (2001, 2, 2, 10, 0), False, False),
    ]
    try:
        gunghap.build_gunghap(people, render=False)
    except ValueError as exc:
        assert "GUNGHAP_UNKNOWN_TIME_UNSUPPORTED" in str(exc)
    else:
        raise AssertionError("생시 미상 궁합은 fail-closed여야 합니다")


def test_gunghap_cli_unknown_time_exits_without_calling_builder(monkeypatch) -> None:
    monkeypatch.setattr(
        gunghap,
        "build_gunghap",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("생시 미상 궁합이 builder로 진입하면 안 됩니다")
        ),
    )
    result = CliRunner().invoke(
        gunghap.app,
        [
            "--person",
            "합성갑,2000-01-01,,남",
            "--person",
            "합성을,2001-02-02,10:00,여",
        ],
    )
    assert result.exit_code == 1
    assert "GUNGHAP_UNKNOWN_TIME_UNSUPPORTED" in result.output
    assert "정오" not in result.output
