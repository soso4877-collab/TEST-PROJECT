# -*- coding: utf-8 -*-
"""생시 미상 주문 저장·관리자 편집·최종 발급 provenance 계약 회귀.

실고객 데이터·PDF·API를 사용하지 않는다. 모든 입력과 렌더 함수는 합성값이며,
정오 잔재 또는 provenance 결손이 최종 발급 전에 물리 차단되는지 양방으로 검증한다.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from sajugen import integrated, modules as integrated_modules, order_flow
from sajugen.calc.three_pillar import NeedsInfoTimeBoundary
from sajugen.content import unknown_time_policy
from sajugen.content.sections_schema import GuardReport, Report23, Section
from sajugen.input.birth_time import BirthTimeMode
from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport
from sajugen.store.orders import (
    BirthTimeProvenanceRequired,
    OrderState,
    OrderStore,
    final_birth_time_contract_error,
    report_birth_time_mode,
    three_pillar_provenance_error,
)


_PROVENANCE = {
    "three_pillar_schema_version": 1,
    "candidate_count": 12,
    "candidate_digest": "a" * 64,
    "stable_fact_ids": ["day_master", "three_pillars"],
    "suppressed_fact_ids": ["singang", "yongshin"],
}


def _report23(
    text: str = "세 기둥의 흐름을 차분히 살핍니다.",
    *,
    mode: str = "three_pillar",
    provenance: dict | None = _PROVENANCE,
) -> Report23:
    return Report23(
        sections=[
            Section(
                id="intro",
                title="합성 도입",
                source_keys=["three_pillar"],
                rule_text=text,
                final_text=text,
            )
        ],
        guard=GuardReport(
            safe_lint_total=0,
            factcheck_total=0,
            grounding_ok=True,
            polished_sections=0,
            fallback_sections=1,
            clean=True,
        ),
        allow_tokens={
            "ganzhi": [],
            "ganzhi_ko": [],
            "ziwei_majors_in_chart": [],
            "all_star_ko": [],
        },
        birth_time_mode=mode,
        three_pillar_provenance=dict(provenance or {}),
        fact_source_ids=["three_pillar"] if mode == "three_pillar" else [],
    )


def _stored_report(*, mode: str, provenance: dict | None = None) -> UnifiedReport:
    known = mode == "known"
    render_meta = {
        "gen_params": {
            "year": 2000,
            "month": 1,
            "day": 1,
            "birth_time_mode": mode,
            "is_male": True,
            "brand": "default",
            "product": "integrated",
            **({"hour": 9, "minute": 30} if known else {}),
        },
    }
    if provenance is not None:
        render_meta["three_pillar_provenance"] = provenance
    return UnifiedReport(
        order_id="",
        birth=BirthInput(
            gender="M",
            input_date="2000-01-01",
            birth_time="09:30" if known else None,
        ),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        content=_report23(mode=mode, provenance=provenance).model_dump(),
        render_meta=render_meta,
    )


def _approve(store: OrderStore, report: UnifiedReport) -> str:
    order_id = store.create(report)
    for state in (
        OrderState.NORMALIZED,
        OrderState.CALC_OK,
        OrderState.DRAFTED,
        OrderState.IN_REVIEW,
        OrderState.APPROVED,
    ):
        store.transition(order_id, state)
    return order_id


def test_unknown_intake_persists_mode_without_clock_or_legacy_boolean(tmp_path: Path) -> None:
    db = tmp_path / "three-pillar-intake.sqlite"
    order_id, warnings = order_flow.create_order(
        birth="2000-01-01",
        gender="male",
        product="integrated_full",
        brand="default",
        db_path=str(db),
    )

    assert warnings == []
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
        params = report.render_meta["gen_params"]
        assert report.birth.birth_time is None
        assert params["birth_time_mode"] == "three_pillar"
        assert "hour" not in params and "minute" not in params
        assert "unknown_time" not in params
        assert params["modules"] == []
    finally:
        store.close()

def test_known_intake_keeps_clock_and_known_mode(tmp_path: Path) -> None:
    db = tmp_path / "known-intake.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01 09:30",
        gender="male",
        brand="default",
        db_path=str(db),
    )
    store = OrderStore(db)
    try:
        report = store.get_report(order_id)
        params = report.render_meta["gen_params"]
        assert report.birth.birth_time == "09:30"
        assert params["birth_time_mode"] == "known"
        assert (params["hour"], params["minute"]) == (9, 30)
        assert "unknown_time" not in params
    finally:
        store.close()


def test_three_pillar_mode_with_clock_is_rejected_without_creating_order(
    tmp_path: Path,
) -> None:
    db = tmp_path / "three-pillar-with-clock.sqlite"
    with pytest.raises(ValueError, match="must not include a birth time"):
        order_flow.create_order(
            birth="2000-01-01 09:30",
            birth_time_mode="three_pillar",
            gender="male",
            brand="default",
            db_path=str(db),
        )
    store = OrderStore(db)
    try:
        assert store.list_orders() == []
    finally:
        store.close()


@pytest.mark.parametrize("legacy_false_flag", [False, True])
def test_legacy_known_without_mode_key_is_restored_from_clock_fields(
    tmp_path: Path,
    legacy_false_flag: bool,
) -> None:
    report = _stored_report(mode="known")
    params = dict(report.render_meta["gen_params"])
    params.pop("birth_time_mode")
    params.pop("unknown_time", None)
    if legacy_false_flag:
        params["unknown_time"] = False
    report = report.model_copy(
        update={
            # 초기 저장본 일부는 BirthInput 문자열이 비어 있고 gen_params 시계만 남았다.
            "birth": report.birth.model_copy(update={"birth_time": None}),
            "render_meta": {**report.render_meta, "gen_params": params},
        }
    )

    assert report_birth_time_mode(report) is BirthTimeMode.KNOWN
    assert final_birth_time_contract_error(report) is None
    store = OrderStore(tmp_path / f"legacy-known-{legacy_false_flag}.sqlite")
    called = {"count": 0}
    try:
        order_id = _approve(store, report)
        assert (
            store.issue_final_pdf(
                order_id,
                lambda _report: called.__setitem__("count", 1) or "synthetic.pdf",
            )
            == "synthetic.pdf"
        )
        assert called["count"] == 1
        assert store.get_state(order_id) == OrderState.DELIVERED
    finally:
        store.close()


def test_legacy_unknown_input_normalizes_to_three_pillar(tmp_path: Path) -> None:
    db = tmp_path / "legacy-unknown-input.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01",
        unknown_time=True,
        gender="male",
        brand="default",
        db_path=str(db),
    )
    store = OrderStore(db)
    try:
        params = store.get_report(order_id).render_meta["gen_params"]
        assert params["birth_time_mode"] == "three_pillar"
        assert "hour" not in params and "minute" not in params
    finally:
        store.close()


def test_legacy_known_flag_without_clock_is_rejected_before_storage(tmp_path: Path) -> None:
    db = tmp_path / "legacy-known-missing-clock.sqlite"
    with pytest.raises(ValueError, match="requires a birth time"):
        order_flow.create_order(
            birth="2000-01-01",
            unknown_time=False,
            gender="male",
            brand="default",
            db_path=str(db),
        )
    store = OrderStore(db)
    try:
        assert store.list_orders() == []
    finally:
        store.close()


def test_three_pillar_boundary_blocks_before_order_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "boundary.sqlite"

    def boundary(*_args):
        raise NeedsInfoTimeBoundary()

    monkeypatch.setattr(order_flow, "ensure_unambiguous_civil_date", boundary)
    with pytest.raises(ValueError, match="NEEDS_INFO_TIME_BOUNDARY") as exc_info:
        order_flow.create_order(
            birth="2000-01-01",
            gender="male",
            brand="default",
            db_path=str(db),
        )
    assert "2000-01-01" not in str(exc_info.value)
    store = OrderStore(db)
    try:
        assert store.list_orders() == []
    finally:
        store.close()


def test_three_pillar_partner_and_gunghap_are_fail_closed(tmp_path: Path) -> None:
    partner_db = tmp_path / "partner.sqlite"
    with pytest.raises(ValueError, match="do not support partner"):
        order_flow.create_order(
            birth="2000-01-01",
            partner_birth="2001-01-01 10:00",
            product="integrated_full",
            brand="default",
            db_path=str(partner_db),
        )

    module_db = tmp_path / "modules.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01",
        product="integrated_full",
        brand="default",
        db_path=str(module_db),
    )
    with pytest.raises(ValueError, match="gunghap"):
        order_flow.confirm_module_selection(
            order_id,
            ["gunghap"],
            db_path=str(module_db),
        )


def test_three_pillar_ziwei_product_is_rejected_before_storage(tmp_path: Path) -> None:
    db = tmp_path / "ziwei.sqlite"
    with pytest.raises(ValueError, match="does not support ziwei"):
        order_flow.create_order(
            birth="2000-01-01",
            product="ziwei",
            brand="default",
            db_path=str(db),
        )
    store = OrderStore(db)
    try:
        assert store.list_orders() == []
    finally:
        store.close()


def test_generation_persists_provenance_and_scrubs_legacy_clock(
    tmp_path: Path,
) -> None:
    db = tmp_path / "generation.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01",
        gender="male",
        brand="default",
        db_path=str(db),
    )
    calls: list[tuple[tuple, dict]] = []

    def fake_generate(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(
            pdf_path="synthetic-draft.pdf",
            ok=True,
            reasons=[],
            verify={"gate_pass": True},
            guard=_report23().guard.model_dump(),
            crosscheck_warnings=[],
            bazi="甲子 乙丑 丙寅",
            report=_report23(),
            calc_consistent=True,
            input_civil="2000-01-01",
            near_term_boundary=False,
            three_pillar_provenance=dict(_PROVENANCE),
        )

    order_flow.run_generation(order_id, generate_fn=fake_generate, db_path=str(db))
    assert calls[0][0][3:5] == (None, None)
    assert calls[0][1]["birth_time_mode"] == "three_pillar"
    assert "unknown_time" not in calls[0][1]

    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.DRAFTED
        report = store.get_report(order_id)
        assert report.render_meta["three_pillar_provenance"] == _PROVENANCE
        params = report.render_meta["gen_params"]
        assert params["birth_time_mode"] == "three_pillar"
        assert "hour" not in params and "minute" not in params
    finally:
        store.close()


def test_integrated_three_pillar_passes_none_clock_and_persists_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = tmp_path / "integrated-generation.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01",
        gender="male",
        name="DOC_A",
        product="integrated_full",
        brand="default",
        db_path=str(db),
    )
    order_flow.confirm_module_selection(order_id, ["love"], db_path=str(db))
    calls: list[tuple[list, dict]] = []

    def fake_integrated(people, **kwargs):
        calls.append((people, kwargs))
        content_path = tmp_path / "synthetic.content.json"
        content_path.write_text("{}", encoding="utf-8")
        module_sections = integrated_modules.empty_module_sections()
        module_sections["core"] = ["personal_intro"]
        module_sections["love"] = ["personal_love"]
        module_sections["tail"] = ["personal_closing"]
        return {
            "pdf_path": str(tmp_path / "synthetic.pdf"),
            "content_path": str(content_path),
            "sections": [
                SimpleNamespace(
                    id="personal_intro",
                    title="합성 도입",
                    source_keys=["three_pillar"],
                    rule_text="세 기둥의 흐름을 살핍니다.",
                    final_text="세 기둥의 흐름을 살핍니다.",
                ),
                SimpleNamespace(
                    id="personal_love",
                    title="합성 관계",
                    source_keys=["time_invariant"],
                    rule_text="관계의 속도를 살핍니다.",
                    final_text="관계의 속도를 살핍니다.",
                ),
            ],
            "people": [{"name": "DOC_A"}],
            "receiver": "DOC_A",
            "identity": ({"甲"}, {"갑목"}, [(["DOC_A"], "갑목")]),
            "singang": [],
            "role_perspective": [{"name": "DOC_A", "role": "receiver"}],
            "honorific": [{"name": "DOC_A", "role": "receiver"}],
            "modules": ["love"],
            "module_schema_version": integrated.MODULE_SCHEMA_VERSION,
            "module_sections": module_sections,
            "premerge_section_ids": [
                "personal_intro",
                "personal_love",
                "personal_closing",
            ],
            "guard": _report23().guard.model_dump(),
            "allow_tokens": _report23().allow_tokens,
            "concern_category": "연애",
            "partner_present": False,
            "calc_consistent": True,
            "crosscheck_warnings": [],
            "bazi": "甲子 乙丑 丙寅",
            "input_civil": "2000-01-01",
            "near_term_boundary": False,
            "ref_year": 2026,
            "ref_date": "2026-07-12",
            "verify": {"gate_pass": True, "module_coverage": {"skipped": False}},
            "birth_time_mode": "three_pillar",
            "three_pillar_provenance": dict(_PROVENANCE),
            "fact_source_ids": ["three_pillar", "time_invariant"],
        }

    monkeypatch.setattr(order_flow.integrated, "build_integrated_full", fake_integrated)
    monkeypatch.setattr(order_flow, "default_ref_date_iso", lambda: "2026-07-12")
    order_flow.run_generation(order_id, db_path=str(db))

    assert calls[0][0] == [("DOC_A", (2000, 1, 1, None, None), True)]
    assert calls[0][1]["birth_time_mode"] == "three_pillar"
    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.DRAFTED
        report = store.get_report(order_id)
        assert report.render_meta["three_pillar_provenance"] == _PROVENANCE
        assert report.render_meta["integrated_full"]["singang"] == []
    finally:
        store.close()


def test_generation_without_provenance_never_reaches_drafted(tmp_path: Path) -> None:
    db = tmp_path / "generation-no-provenance.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01",
        gender="male",
        brand="default",
        db_path=str(db),
    )

    def fake_generate(*_args, **_kwargs):
        return SimpleNamespace(
            pdf_path="synthetic-draft.pdf",
            ok=True,
            reasons=[],
            verify={"gate_pass": True},
            guard=_report23().guard.model_dump(),
            crosscheck_warnings=[],
            bazi="甲子 乙丑 丙寅",
            report=_report23(),
            calc_consistent=True,
            input_civil="2000-01-01",
            near_term_boundary=False,
        )

    order_flow.run_generation(order_id, generate_fn=fake_generate, db_path=str(db))
    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.NORMALIZED
        errors = [entry.note for entry in store.audit(order_id) if entry.action == "generation_error"]
        assert errors == ["three_pillar provenance invalid(provenance_missing)"]
    finally:
        store.close()


@pytest.mark.parametrize(
    ("surface", "error_code"),
    [
        ("content", "content_provenance_mismatch"),
        ("verify", "verify_provenance_mismatch"),
    ],
)
def test_generation_blocks_cross_surface_provenance_mismatch(
    tmp_path: Path,
    surface: str,
    error_code: str,
) -> None:
    db = tmp_path / f"mismatch-{surface}.sqlite"
    order_id, _ = order_flow.create_order(
        birth="2000-01-01",
        gender="male",
        brand="default",
        db_path=str(db),
    )
    other = {**_PROVENANCE, "candidate_digest": "b" * 64}

    def fake_generate(*_args, **_kwargs):
        report = _report23(provenance=other if surface == "content" else _PROVENANCE)
        verify = {"gate_pass": True}
        if surface == "verify":
            verify["three_pillar_provenance"] = other
        return SimpleNamespace(
            pdf_path="synthetic-draft.pdf",
            ok=True,
            reasons=[],
            verify=verify,
            guard=report.guard.model_dump(),
            crosscheck_warnings=[],
            bazi="甲子 乙丑 丙寅",
            report=report,
            calc_consistent=True,
            input_civil="2000-01-01",
            near_term_boundary=False,
            three_pillar_provenance=dict(_PROVENANCE),
        )

    order_flow.run_generation(order_id, generate_fn=fake_generate, db_path=str(db))
    store = OrderStore(db)
    try:
        assert store.get_state(order_id) == OrderState.NORMALIZED
        notes = [entry.note for entry in store.audit(order_id) if entry.action == "generation_error"]
        assert notes == [f"three_pillar provenance invalid({error_code})"]
    finally:
        store.close()


@pytest.mark.parametrize("count", [0, 11, 13])
def test_invalid_candidate_count_blocks_final_issue(tmp_path: Path, count: int) -> None:
    provenance = {**_PROVENANCE, "candidate_count": count}
    store = OrderStore(tmp_path / f"invalid-{count}.sqlite")
    try:
        order_id = _approve(store, _stored_report(mode="three_pillar", provenance=provenance))
        called = {"count": 0}
        with pytest.raises(BirthTimeProvenanceRequired, match="candidate_count_invalid"):
            store.issue_final_pdf(
                order_id,
                lambda _report: called.__setitem__("count", 1) or "synthetic.pdf",
            )
        assert called["count"] == 0
        assert store.get_state(order_id) == OrderState.APPROVED
    finally:
        store.close()


@pytest.mark.parametrize(
    ("update", "error_code"),
    [
        ({"three_pillar_schema_version": 2}, "schema_version_invalid"),
        ({"candidate_digest": "not-a-digest"}, "candidate_digest_invalid"),
        ({"stable_fact_ids": [""]}, "stable_fact_ids_invalid"),
    ],
)
def test_invalid_provenance_shape_blocks_final_issue(
    tmp_path: Path,
    update: dict,
    error_code: str,
) -> None:
    provenance = {**_PROVENANCE, **update}
    store = OrderStore(tmp_path / f"invalid-{error_code}.sqlite")
    try:
        order_id = _approve(store, _stored_report(mode="three_pillar", provenance=provenance))
        with pytest.raises(BirthTimeProvenanceRequired, match=error_code):
            store.issue_final_pdf(order_id, lambda _report: "synthetic.pdf")
        assert store.get_state(order_id) == OrderState.APPROVED
    finally:
        store.close()


@pytest.mark.parametrize(
    "provenance",
    [
        _PROVENANCE,
        {**_PROVENANCE, "three_pillar_schema_version": 2},
        {**_PROVENANCE, "candidate_count": 11},
        {**_PROVENANCE, "candidate_digest": "x"},
        {**_PROVENANCE, "stable_fact_ids": []},
        {**_PROVENANCE, "stable_fact_ids": ["day_master", "day_master"]},
        {**_PROVENANCE, "suppressed_fact_ids": "singang"},
        {
            **_PROVENANCE,
            "stable_fact_ids": ["day_master"],
            "suppressed_fact_ids": ["day_master"],
        },
    ],
)
def test_store_and_content_provenance_validators_have_parity(provenance: dict) -> None:
    store_invalid = three_pillar_provenance_error(provenance) is not None
    content_invalid = bool(
        unknown_time_policy.provenance_contract_lint(
            provenance,
            birth_time_mode="three_pillar",
            source="test",
        )
    )
    assert store_invalid is content_invalid


def test_legacy_unknown_noon_order_is_blocked_before_render(tmp_path: Path) -> None:
    report = _stored_report(mode="three_pillar", provenance=None)
    report = report.model_copy(
        update={
            "render_meta": {
                "gen_params": {
                    "year": 2000,
                    "month": 1,
                    "day": 1,
                    "hour": 12,
                    "minute": 0,
                    "unknown_time": True,
                }
            }
        }
    )
    store = OrderStore(tmp_path / "legacy.sqlite")
    try:
        order_id = _approve(store, report)
        called = {"count": 0}
        with pytest.raises(BirthTimeProvenanceRequired, match="clock_fields_present"):
            store.issue_final_pdf(
                order_id,
                lambda _report: called.__setitem__("count", 1) or "synthetic.pdf",
            )
        assert called["count"] == 0
    finally:
        store.close()


def test_known_and_valid_three_pillar_final_issue_both_pass(tmp_path: Path) -> None:
    for mode, provenance in (("known", None), ("three_pillar", _PROVENANCE)):
        store = OrderStore(tmp_path / f"pass-{mode}.sqlite")
        try:
            order_id = _approve(store, _stored_report(mode=mode, provenance=provenance))
            assert store.issue_final_pdf(order_id, lambda _report: "synthetic.pdf") == "synthetic.pdf"
            assert store.get_state(order_id) == OrderState.DELIVERED
        finally:
            store.close()


def test_admin_edit_blocks_hour_fact_and_keeps_original(tmp_path: Path) -> None:
    db = tmp_path / "admin-edit.sqlite"
    report = _stored_report(mode="three_pillar", provenance=_PROVENANCE)
    store = OrderStore(db)
    try:
        order_id = store.create(report)
        for state in (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
            OrderState.IN_REVIEW,
        ):
            store.transition(order_id, state)
    finally:
        store.close()

    violations = order_flow.edit_section(
        order_id,
        "intro",
        "시주는 합성값으로 확정합니다.",
        db_path=str(db),
    )
    assert any(hit.get("rule") == "hour_pillar" for hit in violations)
    store = OrderStore(db)
    try:
        saved = Report23.model_validate(store.get_report(order_id).content)
        assert saved.section("intro").final_text == "세 기둥의 흐름을 차분히 살핍니다."
    finally:
        store.close()


def test_admin_edit_allows_three_pillar_clean_text(tmp_path: Path) -> None:
    db = tmp_path / "admin-edit-clean.sqlite"
    report = _stored_report(mode="three_pillar", provenance=_PROVENANCE)
    store = OrderStore(db)
    try:
        order_id = store.create(report)
        for state in (
            OrderState.NORMALIZED,
            OrderState.CALC_OK,
            OrderState.DRAFTED,
            OrderState.IN_REVIEW,
        ):
            store.transition(order_id, state)
    finally:
        store.close()

    text = "세 기둥에서 공통으로 보이는 흐름만 차분히 살핍니다."
    assert order_flow.edit_section(order_id, "intro", text, db_path=str(db)) == []
    store = OrderStore(db)
    try:
        saved = Report23.model_validate(store.get_report(order_id).content)
        assert saved.section("intro").final_text == text
    finally:
        store.close()


def test_three_pillar_final_render_forwards_mode_and_provenance_without_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _stored_report(mode="three_pillar", provenance=_PROVENANCE).model_copy(
        update={"order_id": "ord_synthetic"}
    )
    engine_call: dict = {}
    render_call: dict = {}
    verify_call: dict = {}

    def fake_engine(*args, **kwargs):
        engine_call["args"] = args
        engine_call["kwargs"] = kwargs
        return SimpleNamespace()

    monkeypatch.setattr(order_flow.engine, "build", fake_engine)
    monkeypatch.setattr(
        order_flow.builder,
        "personal_identity_spec",
        lambda _saju, _name: ({"甲"}, {"갑목"}, [([], "갑목")]),
    )

    def fake_render(*args, **kwargs):
        render_call.update(kwargs)
        return "synthetic-final.pdf"

    def fake_verify(_path, **kwargs):
        verify_call.update(kwargs)
        return {
            "gate_pass": True,
            "text_chars": 2000,
            "tagged": True,
            "fonts_embedded": True,
            "name_policy_clean": True,
            "identity_role_clean": True,
        }

    monkeypatch.setattr(order_flow.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(order_flow.render_verify, "verify", fake_verify)

    assert order_flow.final_render_fn(report) == "synthetic-final.pdf"
    assert engine_call["args"][3:5] == (None, None)
    assert engine_call["kwargs"]["birth_time_mode"] == "three_pillar"
    assert render_call["birth_time_mode"] == "three_pillar"
    assert render_call["three_pillar_provenance"] == _PROVENANCE
    assert verify_call["birth_time_mode"] == "three_pillar"
    assert verify_call["three_pillar_provenance"] == _PROVENANCE


def test_three_pillar_final_render_blocks_stored_content_provenance_mismatch() -> None:
    other = {**_PROVENANCE, "candidate_digest": "b" * 64}
    report = _stored_report(mode="three_pillar", provenance=_PROVENANCE).model_copy(
        update={
            "order_id": "ord_synthetic_mismatch",
            "content": _report23(provenance=other).model_dump(),
        }
    )
    with pytest.raises(RuntimeError, match="content_provenance_mismatch"):
        order_flow.final_render_fn(report)


def test_final_contract_helper_known_is_non_degrading() -> None:
    assert final_birth_time_contract_error(_stored_report(mode="known")) is None
