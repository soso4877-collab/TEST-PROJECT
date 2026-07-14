# -*- coding: utf-8 -*-
"""Q7 3-A·4 integrated_full 주문 생성·재시도·2인·최종발급 분기 회귀.

실제 계산·LLM·PDF는 호출하지 않는다. 합성 결과를 주입해 주문 상태머신과 native
integrated 렌더 게이트의 파라미터 관통, content.json 영속, 기존 integrated 분리를
양방으로 검증한다.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from sajugen import integrated, order_flow
from sajugen import modules as integrated_modules
from sajugen.content.sections_schema import GuardReport, Report23, Section
from sajugen.content import llm_usage
from sajugen.input import time_correction as tc
from sajugen.store.orders import OrderState, OrderStore


def _guard() -> GuardReport:
    return GuardReport(
        safe_lint_total=0,
        factcheck_total=0,
        grounding_ok=True,
        polished_sections=0,
        fallback_sections=2,
        clean=True,
    )


def _module_sections(
    selected_modules: tuple[str, ...] = ("love",),
) -> dict[str, list[str]]:
    sections = integrated_modules.empty_module_sections()
    sections["core"] = ["personal_intro"]
    sections["tail"] = ["personal_closing"]
    representatives = {
        "love": "personal_love",
        "job": "personal_work",
        "wealth": "personal_work",
        "health": "personal_health",
        "gunghap": "relationship_overview",
    }
    for module_id in selected_modules:
        sections[module_id] = [representatives[module_id]]
    return sections


def _integrated_result(
    tmp_path: Path,
    *,
    ref_year: int = 2028,
    ref_date: str = "2026-07-11",
    calc_consistent: bool = True,
    selected_modules: tuple[str, ...] = ("love",),
    partner_present: bool = False,
) -> dict:
    content_path = tmp_path / "draft_synthetic.content.json"
    content_path.write_text("{}", encoding="utf-8")
    module_sections = _module_sections(selected_modules)
    premerge = list(
        dict.fromkeys(
            section_id
            for section_ids in module_sections.values()
            for section_id in section_ids
        )
    )
    people = [{"name": "DOC_A"}]
    identity = ({"甲"}, {"갑목"}, [(["DOC_A"], "갑목")])
    singang = [{"name": "DOC_A", "expected": "신강"}]
    roles = [{"name": "DOC_A", "role": "receiver"}]
    if partner_present:
        people.append({"name": "DOC_B"})
        identity = (
            {"甲", "乙"},
            {"갑목", "을목"},
            [(["DOC_A"], "갑목"), (["DOC_B"], "을목")],
        )
        singang.append({"name": "DOC_B", "expected": "신약"})
        roles.append({"name": "DOC_B", "role": "partner"})
    sections = [
        SimpleNamespace(
            id="personal_intro",
            title="합성 도입",
            source_keys=["myeongni"],
            final_text="순한 흐름을 차분히 살핍니다.",
        ),
        SimpleNamespace(
            id="personal_love",
            title="합성 관계",
            source_keys=["myeongni"],
            final_text="관계의 기준을 하나씩 확인합니다.",
        ),
    ]
    if "gunghap" in selected_modules:
        sections.append(
            SimpleNamespace(
                id="relationship_overview",
                title="합성 궁합",
                source_keys=["gunghap"],
                final_text="두 사람의 흐름을 함께 살핍니다.",
            )
        )
    return {
        "product": "integrated_full",
        "pdf_path": str(tmp_path / "draft_synthetic.pdf"),
        "content_path": str(content_path),
        "sections": sections,
        "people": people,
        "receiver": "DOC_A",
        "identity": identity,
        "singang": singang,
        "role_perspective": roles,
        "honorific": roles,
        "modules": list(selected_modules),
        "module_schema_version": integrated.MODULE_SCHEMA_VERSION,
        "module_sections": module_sections,
        "premerge_section_ids": premerge,
        "guard": _guard().model_dump(),
        "allow_tokens": {
            "ganzhi": [],
            "ganzhi_ko": [],
            "ziwei_majors_in_chart": [],
            "all_star_ko": [],
        },
        "concern_category": "직업",
        "partner_present": partner_present,
        "calc_consistent": calc_consistent,
        "crosscheck_warnings": [],
        "bazi": "甲子 乙丑 丙寅 丁卯",
        "input_civil": "2000-01-01 12:00",
        "near_term_boundary": False,
        "ref_year": ref_year,
        "ref_date": ref_date,
        "verify": {
            "gate_pass": True,
            "module_coverage": {"skipped": False},
        },
    }


def _create_confirmed_order(
    db: Path,
    *,
    retry: bool = False,
    partner_present: bool = False,
    modules: list[str] | None = None,
) -> str:
    order_id, _warnings = order_flow.create_order(
        birth="2000-01-01 12:00",
        gender="male",
        longitude=129.0756,
        latitude=35.1796,
        yajasi=True,
        horoscope="2028-03-01",
        name="DOC_A",
        partner_name="DOC_B" if partner_present else "",
        partner_birth="2001-02-02 13:30" if partner_present else "",
        partner_gender="female",
        product="integrated_full",
        concern="이직 준비 순서가 궁금합니다.",
        brand="default",
        db_path=str(db),
    )
    selected_modules = modules or ["love"]
    order_flow.confirm_module_selection(order_id, selected_modules, db_path=str(db))
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
        assert report.report_plan.sections == list(
            integrated_modules.normalize_modules(selected_modules)
        )
        if retry:
            store.transition(order_id, OrderState.CALC_MISMATCH, actor="system")
    finally:
        store.close()
    if retry:
        order_flow.retry_calc(order_id, db_path=str(db))
    return order_id


@pytest.mark.parametrize("retry", [False, True])
def test_confirmed_integrated_generation_and_retry_use_native_builder(
    tmp_path, monkeypatch, retry
):
    db = tmp_path / f"integrated-{retry}.sqlite"
    order_id = _create_confirmed_order(db, retry=retry)
    calls: list[dict] = []
    llm_usage.reset()

    def fake_integrated_build(people, **kwargs):
        calls.append({"people": people, "kwargs": dict(kwargs)})
        llm_usage.add(
            10,
            2,
            role="compose",
            model="claude-sonnet-4-6",
            section="intro",
        )
        return _integrated_result(tmp_path)

    monkeypatch.setattr(order_flow.integrated, "build_integrated_full", fake_integrated_build)
    monkeypatch.setattr(order_flow, "default_ref_date_iso", lambda: "2026-07-11")

    def forbidden_pipeline(*args, **kwargs):
        raise AssertionError("integrated_full must not call pipeline.generate")

    order_flow.run_generation(order_id, generate_fn=forbidden_pipeline, db_path=str(db))

    assert len(calls) == 1
    assert calls[0]["people"] == [("DOC_A", (2000, 1, 1, 12, 0), True)]
    kwargs = calls[0]["kwargs"]
    assert kwargs["modules"] == ["love"]
    assert kwargs["longitude"] == 129.0756
    assert kwargs["latitude"] == 35.1796
    assert kwargs["policy"] == tc.ZasiPolicy.YAJASI_SPLIT
    assert kwargs["horoscope_date"] == "2028-03-01"
    assert kwargs["ref_year"] == 2028
    assert kwargs["ref_date"] == "2026-07-11"
    assert kwargs["situation"] == "이직 준비 순서가 궁금합니다."
    assert kwargs["render"] is True

    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.DRAFTED
        report = store.get_report(order_id)
        report23 = Report23.model_validate(report.content)
        assert [section.id for section in report23.sections] == [
            "personal_intro",
            "personal_love",
        ]
        assert report23.concern_category == "직업"
        assert report23.partner_present is False
        assert report.render_meta["integrated_full"]["content_path"].endswith(
            "draft_synthetic.content.json"
        )
        assert report.render_meta["integrated_full"]["selected_modules"] == ["love"]
        assert report.render_meta["verify"]["module_coverage"]["skipped"] is False
        assert report.render_meta["llm_usage"]["calls"] == 1
        assert report.render_meta["llm_usage"]["input_tokens"] == 10
        assert len(report.render_meta["llm_usage"]["events"]) == 1
        assert order_flow.module_selection_state(report)["confirmed"] is True
    finally:
        store.close()
    assert llm_usage.snapshot() == {"input_tokens": 0, "output_tokens": 0, "calls": 0}


def test_generation_error_persists_isolated_llm_usage(tmp_path, monkeypatch):
    db = tmp_path / "integrated-usage-error.sqlite"
    order_id = _create_confirmed_order(db)
    llm_usage.reset()

    def fail_after_usage(*args, **kwargs):
        # 실제 API 없이 응답 계측 뒤 생성 후처리가 실패한 경로만 합성한다.
        llm_usage.add(
            17,
            5,
            role="compose",
            model="unknown",
            section="intro",
            attempt=2,
            cache_creation_input_tokens=11,
            stop_reason="end_turn",
        )
        raise RuntimeError("synthetic generation failure")

    monkeypatch.setattr(
        order_flow.integrated,
        "build_integrated_full",
        fail_after_usage,
    )

    order_flow.run_generation(order_id, db_path=str(db))

    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.NORMALIZED
        report = store.get_report(order_id)
        assert report.render_meta["llm_usage"] == {
            "input_tokens": 17,
            "output_tokens": 5,
            "calls": 1,
            "cache_creation_input_tokens": 11,
            "cache_read_input_tokens": 0,
            "events": [
                {
                    "role": "compose",
                    "model": "unknown",
                    "section": "intro",
                    "attempt": 2,
                    "input_tokens": 17,
                    "cache_creation_input_tokens": 11,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 5,
                    "stop_reason": "end_turn",
                }
            ],
        }
        errors = [
            entry.note
            for entry in store.audit(order_id)
            if entry.action == "generation_error"
        ]
        assert errors == ["RuntimeError: synthetic generation failure"]
    finally:
        store.close()

    # 주문 collector는 영속된 뒤 외부 ContextVar 상태로 복귀해 다음 주문과 섞이지 않는다.
    assert llm_usage.snapshot() == {"input_tokens": 0, "output_tokens": 0, "calls": 0}


def test_partner_gunghap_generation_passes_two_people_and_persists_partner_flag(
    tmp_path,
    monkeypatch,
):
    db = tmp_path / "integrated-partner.sqlite"
    order_id = _create_confirmed_order(
        db,
        partner_present=True,
        modules=["gunghap", "love"],
    )
    calls: list[dict] = []

    def fake_integrated_build(people, **kwargs):
        calls.append({"people": people, "kwargs": dict(kwargs)})
        result = _integrated_result(
            tmp_path,
            selected_modules=("love", "gunghap"),
            partner_present=True,
        )
        # 실제 개인 빌더가 False를 반환하더라도 주문의 partner 입력이 최종 진실원이어야 한다.
        result["partner_present"] = False
        return result

    monkeypatch.setattr(order_flow.integrated, "build_integrated_full", fake_integrated_build)
    monkeypatch.setattr(order_flow, "default_ref_date_iso", lambda: "2026-07-11")

    order_flow.run_generation(order_id, db_path=str(db))

    assert len(calls) == 1
    assert calls[0]["people"] == [
        ("DOC_A", (2000, 1, 1, 12, 0), True),
        ("DOC_B", (2001, 2, 2, 13, 30), False),
    ]
    assert calls[0]["kwargs"]["receiver_name"] == "DOC_A"
    assert calls[0]["kwargs"]["modules"] == ["love", "gunghap"]
    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.DRAFTED
        report = store.get_report(order_id)
        report23 = Report23.model_validate(report.content)
        assert report23.partner_present is True
        assert report.render_meta["integrated_full"]["names"] == ["DOC_A", "DOC_B"]
        assert report.render_meta["integrated_full"]["selected_modules"] == [
            "love",
            "gunghap",
        ]
    finally:
        store.close()


def test_partner_birth_is_masked_from_generation_error_audit(tmp_path, monkeypatch):
    db = tmp_path / "integrated-partner-error.sqlite"
    order_id = _create_confirmed_order(db, partner_present=True)
    partner_civil = "2001-02-02 13:30"

    def fail_generation(*args, **kwargs):
        raise RuntimeError(f"synthetic failure {partner_civil}")

    monkeypatch.setattr(order_flow, "_run_integrated_generation", fail_generation)

    order_flow.run_generation(order_id, db_path=str(db))

    store = OrderStore(db)
    try:
        errors = [
            entry
            for entry in store.audit(order_id)
            if entry.action == "generation_error"
        ]
        assert len(errors) == 1
        assert partner_civil not in errors[0].note
        assert "2001-02-02" not in errors[0].note
        assert "13:30" not in errors[0].note
    finally:
        store.close()


def test_integrated_generation_fails_closed_without_persisted_content(tmp_path, monkeypatch):
    db = tmp_path / "missing-content.sqlite"
    order_id = _create_confirmed_order(db)
    result = _integrated_result(tmp_path)
    result["content_path"] = str(tmp_path / "missing.content.json")
    monkeypatch.setattr(
        order_flow.integrated,
        "build_integrated_full",
        lambda *args, **kwargs: result,
    )

    order_flow.run_generation(order_id, db_path=str(db))

    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.NORMALIZED
        errors = [entry for entry in store.audit(order_id) if entry.action == "generation_error"]
        assert len(errors) == 1
        assert "content persistence missing" in errors[0].note
    finally:
        store.close()


def test_integrated_calc_mismatch_uses_existing_blocked_state(tmp_path, monkeypatch):
    db = tmp_path / "calc-mismatch.sqlite"
    order_id = _create_confirmed_order(db)
    monkeypatch.setattr(
        order_flow.integrated,
        "build_integrated_full",
        lambda *args, **kwargs: _integrated_result(tmp_path, calc_consistent=False),
    )

    order_flow.run_generation(order_id, db_path=str(db))

    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.CALC_MISMATCH
    finally:
        store.close()


def test_existing_integrated_order_still_uses_pipeline(tmp_path, monkeypatch):
    db = tmp_path / "legacy-integrated.sqlite"
    order_id, _warnings = order_flow.create_order(
        birth="2000-01-01 12:00",
        gender="male",
        name="DOC_A",
        product="integrated",
        brand="default",
        db_path=str(db),
    )
    report23 = Report23(
        sections=[
            Section(
                id="intro",
                title="합성 도입",
                source_keys=["myeongni"],
                rule_text="순한 흐름을 살핍니다.",
                final_text="순한 흐름을 살핍니다.",
            )
        ],
        guard=_guard(),
    )
    calls = {"pipeline": 0}

    def fake_pipeline(*args, **kwargs):
        calls["pipeline"] += 1
        return SimpleNamespace(
            pdf_path=str(tmp_path / "legacy.pdf"),
            ok=True,
            reasons=[],
            verify={"gate_pass": True},
            guard=report23.guard.model_dump(),
            crosscheck_warnings=[],
            bazi="甲子 乙丑 丙寅 丁卯",
            report=report23,
            calc_consistent=True,
            input_civil="2000-01-01 12:00",
            near_term_boundary=False,
        )

    monkeypatch.setattr(
        order_flow.integrated,
        "build_integrated_full",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("legacy integrated must not call native builder")
        ),
    )
    order_flow.run_generation(order_id, generate_fn=fake_pipeline, db_path=str(db))

    store = OrderStore(db)
    try:
        assert calls["pipeline"] == 1
        assert store.get_state(order_id) == OrderState.DRAFTED
        assert "integrated_full" not in store.get_report(order_id).render_meta
    finally:
        store.close()


def test_integrated_final_render_reuses_saved_specs_and_modules(tmp_path, monkeypatch):
    db = tmp_path / "final-integrated.sqlite"
    order_id = _create_confirmed_order(db)
    monkeypatch.setattr(
        order_flow.integrated,
        "build_integrated_full",
        lambda *args, **kwargs: _integrated_result(tmp_path),
    )
    order_flow.run_generation(order_id, db_path=str(db))
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
    finally:
        store.close()

    captured: dict = {}

    def fake_render(report_arg, **kwargs):
        captured["section_ids"] = [section.id for section in report_arg.sections]
        captured.update(kwargs)
        return (
            str(tmp_path / "final-integrated.pdf"),
            {"gate_pass": True, "module_coverage": {"skipped": False}},
            [],
        )

    monkeypatch.setattr(order_flow.integrated, "_render_integrated", fake_render)
    path = order_flow.final_render_fn(report)

    assert path.endswith("final-integrated.pdf")
    assert captured["section_ids"] == ["personal_intro", "personal_love"]
    assert captured["names"] == ["DOC_A"]
    assert captured["selected_modules"] == ("love",)
    assert captured["module_sections"] == _module_sections()
    assert captured["premerge_section_ids"] == [
        "personal_intro",
        "personal_love",
        "personal_closing",
    ]
    assert captured["ref_year"] == 2028
    assert captured["ref_date"] == "2026-07-11"


def test_integrated_final_render_blocks_module_mismatch_and_skipped_gate(tmp_path, monkeypatch):
    db = tmp_path / "final-blocked.sqlite"
    order_id = _create_confirmed_order(db)
    monkeypatch.setattr(
        order_flow.integrated,
        "build_integrated_full",
        lambda *args, **kwargs: _integrated_result(tmp_path),
    )
    order_flow.run_generation(order_id, db_path=str(db))
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
    finally:
        store.close()

    mismatched_meta = dict(report.render_meta)
    mismatched_full = dict(mismatched_meta["integrated_full"])
    mismatched_full["selected_modules"] = ["job"]
    mismatched_meta["integrated_full"] = mismatched_full
    mismatched = report.model_copy(update={"render_meta": mismatched_meta})
    with pytest.raises(RuntimeError, match="module metadata mismatch"):
        order_flow.final_render_fn(mismatched)

    monkeypatch.setattr(
        order_flow.integrated,
        "_render_integrated",
        lambda *args, **kwargs: (
            str(tmp_path / "blocked.pdf"),
            {"gate_pass": True, "module_coverage": {"skipped": True}},
            [],
        ),
    )
    with pytest.raises(RuntimeError, match="모듈 게이트 실패"):
        order_flow.final_render_fn(report)


def test_integrated_render_passes_product_and_coverage_to_verify(monkeypatch):
    captured: dict = {}
    module_sections = _module_sections()
    premerge = ["personal_intro", "personal_love", "personal_closing"]
    monkeypatch.setattr(integrated.render_pdf, "render_pdf", lambda *args, **kwargs: "fake.pdf")

    def fake_verify(path, **kwargs):
        captured.update(kwargs)
        coverage = integrated_modules.module_coverage(
            kwargs["selected_modules"],
            kwargs["module_sections"],
            kwargs["premerge_section_ids"],
        )
        return {"gate_pass": True, "module_coverage": coverage}

    monkeypatch.setattr(integrated.render_verify, "verify", fake_verify)
    _path, verify, _attempts = integrated._render_integrated(
        SimpleNamespace(sections=[]),
        names=["DOC_A"],
        ref_year=2026,
        situation="합성 맥락",
        identity=({"甲"}, {"갑목"}, []),
        singang=[{"name": "DOC_A", "expected": "신강"}],
        role_specs=[{"name": "DOC_A", "role": "receiver"}],
        brand="default",
        out_name="fake.pdf",
        out_dir=None,
        selected_modules=["love"],
        module_sections=module_sections,
        premerge_section_ids=premerge,
        ref_date="2026-07-11",
    )

    assert captured["product"] == "integrated_full"
    assert captured["selected_modules"] == ["love"]
    assert verify["module_coverage"]["skipped"] is False
