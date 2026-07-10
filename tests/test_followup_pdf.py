# -*- coding: utf-8 -*-
"""Q5 후속 슬림 PDF의 조립·게이트·텍스트 회귀.

실제 PDF 엔진과 계산 엔진은 호출하지 않는다. 저장 Report23 재사용, 표준
render/verify 배선, 10~15쪽 범위, 범위 밖 질문 차단을 합성 데이터로 검증한다.
"""

import sys
from pathlib import Path

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import order_flow  # noqa: E402
from sajugen.cli import app as cli_app  # noqa: E402
from sajugen.content.sections_schema import GuardReport, Report23, Section  # noqa: E402
from sajugen.models.report import BirthInput, CalendarVerification, UnifiedReport  # noqa: E402
from sajugen.store.orders import OrderState, OrderStore  # noqa: E402

_ANSWER = (
    "결론부터 말하면, 이 질문은 올해 하반기 안에서 조건을 좁혀 확인하는 방식이 맞습니다. "
    "먼저 맡을 역할과 돈의 조건을 나누어 보세요. 확인 순서는 세 가지입니다. "
    "첫째, 현재 자리에서 남길 수 있는 조건을 확인합니다. 둘째, 옮길 자리의 계약 조건과 "
    "실제 업무 범위를 문서로 확인합니다. 셋째, 답이 늦어지면 바로 결정하지 말고 다음 확인 "
    "시점을 잡습니다. 질문하신 이직 문제는 직업과 재물 조건이 함께 움직이는 고민이라, "
    "속도보다 확인 순서가 중요합니다. 결과를 보장하려는 말이 아니라 저장된 흐름 안에서 "
    "선택 기준을 좁혀 드리는 답변입니다. "
) * 2

_STORED = (
    "저장된 명식 요약에서는 일과 재물, 사람과 생활의 조건을 분리해 살핍니다. "
    "자미두수에서는 일의 자리와 돈의 자리, 사람의 자리와 이동의 자리를 함께 참고합니다. "
    "결정을 서두르기보다 계약과 역할을 문서로 확인하는 순서가 중요합니다. "
) * 5


class _Backend:
    name = "fake"

    def available(self):
        return True

    def classify(self, concern):
        raise AssertionError("classify 직접 호출 금지")

    def polish(self, rule_text, title):
        return rule_text

    def compose(self, **kwargs):
        return _ANSWER


def _section(section_id: str) -> Section:
    return Section(
        id=section_id,
        title=f"합성 {section_id}",
        source_keys=[] if section_id in {"cover", "toc"} else ["report_json"],
        rule_text=_STORED,
        final_text=_STORED,
    )


def _parent_report() -> UnifiedReport:
    section_ids = (
        "cover",
        "toc",
        "intro",
        "wonguk",
        "nature",
        "work",
        "flow",
        "ziwei",
        "together",
        "consult",
        "closing",
    )
    report23 = Report23(
        sections=[_section(section_id) for section_id in section_ids],
        guard=GuardReport(
            safe_lint_total=0,
            factcheck_total=0,
            grounding_ok=True,
            polished_sections=0,
            fallback_sections=len(section_ids),
            clean=True,
        ),
        concern_category="직업",
        allow_tokens={
            "ganzhi": [],
            "ganzhi_ko": [],
            "ziwei_majors_in_chart": ["자미"],
            "allowed_years": [2026],
        },
        partner_present=False,
    )
    return UnifiedReport(
        order_id="",
        birth=BirthInput(gender="M", input_date="2000-01-01", birth_time="12:00"),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        content=report23.model_dump(),
        render_meta={
            "input_civil": "2000-01-01 12:00",
            "bazi": "甲子 乙丑 丙寅 丁卯",
            "gen_params": {
                "brand": "default",
                "unknown_time": False,
            },
        },
    )


def _seed_parent(db: Path) -> tuple[str, str]:
    store = OrderStore(db)
    try:
        alias = store.link_customer("SD-1000", name_masked="MASKED_SYNTHETIC")
        parent_id = store.create(_parent_report(), alias=alias, kind="new")
        return alias, parent_id
    finally:
        store.close()


def _install_pdf_doubles(monkeypatch, tmp_path: Path, *, pages: int = 10):
    rendered: list[dict] = []
    verified: list[dict] = []

    def fake_render(report, cover, **kwargs):
        rendered.append({"report": report, "cover": cover, **kwargs})
        return str(tmp_path / kwargs["out_name"])

    def fake_verify(path, **kwargs):
        verified.append({"path": path, **kwargs})
        return {
            "gate_pass": True,
            "pages": pages,
            "text_chars": 2500,
            "tagged": True,
            "fonts_embedded": True,
        }

    monkeypatch.setattr(order_flow.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(order_flow.render_verify, "verify", fake_verify)
    return rendered, verified


def test_pdf_followup_reuses_stored_sections_and_standard_gate_without_new_calc(
    tmp_path, monkeypatch
):
    db = tmp_path / "orders.sqlite"
    alias, parent_id = _seed_parent(db)
    rendered, verified = _install_pdf_doubles(monkeypatch, tmp_path)
    monkeypatch.setattr(
        order_flow.engine,
        "build",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("새 계산 금지")),
    )

    result = order_flow.run_followup(
        alias=alias,
        question="이직을 준비해도 될까요?",
        pdf=True,
        db_path=str(db),
        backend=_Backend(),
        today="2026-07-10",
    )

    assert result["ok"] is True, result
    assert result["pdf"] is True
    assert result["consult_direct"]["ok"] is True
    assert result["verify"]["followup_gate_pass"] is True
    assert result["verify"]["followup_page_range"]["value"] == 10
    assert rendered and verified
    assert verified[0]["product"] == "followup"
    assert verified[0]["concern"] == "이직을 준비해도 될까요?"
    assert verified[0]["identity"] is not None

    store = OrderStore(db)
    try:
        child = store.get_report(result["order_id"])
        assert store.get_state(result["order_id"]) == OrderState.IN_REVIEW
        assert child.report_plan.product == "followup"
        assert child.render_meta["draft_pdf"] == result["draft_pdf"]
        child_report23 = Report23.model_validate(child.content)
        assert [section.id for section in child_report23.sections] == [
            "cover",
            "toc",
            "intro",
            "nature",
            "work",
            "flow",
            "ziwei",
            "together",
            "consult",
            "closing",
        ]
        assert child_report23.section("consult").final_text == _ANSWER
        assert child.render_meta["followup"]["parent_order_id"] == parent_id
    finally:
        store.close()

    # 최종 발급 재렌더도 저장 Report23 전용 분기를 사용하므로 engine.build에 도달하지 않는다.
    final_path = order_flow.final_render_fn(child)
    assert final_path.endswith(f"final_{child.order_id}.pdf")
    assert len(rendered) == 2 and len(verified) == 2


def test_pdf_followup_rejects_out_of_scope_year_and_topic_before_render(tmp_path, monkeypatch):
    db = tmp_path / "orders.sqlite"
    alias, _parent_id = _seed_parent(db)
    monkeypatch.setattr(
        order_flow.render_pdf,
        "render_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("PDF 생성 금지")),
    )

    for question, reason in (
        ("2099년에 이직해도 될까요?", "범위 밖 연도"),
        ("연애는 언제 좋아질까요?", "범위 밖 주제"),
    ):
        result = order_flow.run_followup(
            alias=alias,
            question=question,
            pdf=True,
            db_path=str(db),
            backend=_Backend(),
            today="2026-07-10",
        )
        assert result["ok"] is False
        assert reason in result["reason"]
    store = OrderStore(db)
    try:
        assert len(store.list_orders()) == 1
    finally:
        store.close()


def test_pdf_followup_rejects_more_than_15_pages_without_creating_order(tmp_path, monkeypatch):
    db = tmp_path / "orders.sqlite"
    alias, _parent_id = _seed_parent(db)
    _install_pdf_doubles(monkeypatch, tmp_path, pages=16)

    result = order_flow.run_followup(
        alias=alias,
        question="이직을 준비해도 될까요?",
        pdf=True,
        db_path=str(db),
        backend=_Backend(),
        today="2026-07-10",
    )

    assert result["ok"] is False
    assert result["reason"] == "후속 PDF 게이트 실패"
    assert result["failures"][0]["page_range_clean"] is False
    store = OrderStore(db)
    try:
        assert len(store.list_orders()) == 1
    finally:
        store.close()


def test_pdf_followup_fails_closed_without_stored_day_master(tmp_path, monkeypatch):
    db = tmp_path / "orders.sqlite"
    alias, parent_id = _seed_parent(db)
    store = OrderStore(db)
    try:
        parent = store.get_report(parent_id)
        parent_meta = dict(parent.render_meta)
        parent_meta.pop("bazi")
        store.save_report(
            parent_id,
            parent.model_copy(update={"render_meta": parent_meta}),
            actor="system",
        )
    finally:
        store.close()
    monkeypatch.setattr(
        order_flow.render_pdf,
        "render_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("게이트 전 렌더 금지")),
    )

    result = order_flow.run_followup(
        alias=alias,
        question="이직을 준비해도 될까요?",
        pdf=True,
        db_path=str(db),
        backend=_Backend(),
        today="2026-07-10",
    )

    assert result["ok"] is False
    assert result["reason"] == "후속 PDF 생성 실패(ValueError)"
    store = OrderStore(db)
    try:
        assert len(store.list_orders()) == 1
    finally:
        store.close()


def test_default_followup_path_stays_text_only(tmp_path, monkeypatch):
    db = tmp_path / "orders.sqlite"
    alias, _parent_id = _seed_parent(db)
    monkeypatch.setattr(
        order_flow.render_pdf,
        "render_pdf",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("기본 경로 렌더 금지")),
    )

    result = order_flow.run_followup(
        alias=alias,
        question="이직을 준비해도 될까요?",
        db_path=str(db),
        backend=_Backend(),
        today="2026-07-10",
    )

    assert result["ok"] is True
    assert result["answer"] == _ANSWER
    assert "pdf" not in result and "draft_pdf" not in result
    store = OrderStore(db)
    try:
        child = store.get_report(result["order_id"])
        assert child.content == {}
        assert set(child.render_meta) == {"followup"}
    finally:
        store.close()


def test_gen_followup_cli_pdf_flag_is_opt_in_and_default_output_is_unchanged(monkeypatch):
    calls: list[dict] = []

    def fake_run_followup(**kwargs):
        calls.append(kwargs)
        result = {
            "ok": True,
            "order_id": "ord_synthetic",
            "parent_order_id": "ord_parent",
            "state": "IN_REVIEW",
            "answer": "합성 답변",
        }
        if kwargs["pdf"]:
            result["draft_pdf"] = "out/synthetic.pdf"
        return result

    monkeypatch.setattr(order_flow, "run_followup", fake_run_followup)
    runner = CliRunner()
    text_result = runner.invoke(
        cli_app,
        ["gen-followup", "--alias", "SD-1000", "--question", "합성 질문"],
    )
    assert text_result.exit_code == 0, text_result.output
    assert calls[-1]["pdf"] is False
    assert "draft_pdf=" not in text_result.output
    assert text_result.output.endswith("합성 답변\n")

    pdf_result = runner.invoke(
        cli_app,
        ["gen-followup", "--alias", "SD-1000", "--question", "합성 질문", "--pdf"],
    )
    assert pdf_result.exit_code == 0, pdf_result.output
    assert calls[-1]["pdf"] is True
    assert "draft_pdf=out/synthetic.pdf" in pdf_result.output
