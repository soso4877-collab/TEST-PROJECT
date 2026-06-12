# -*- coding: utf-8 -*-
"""검수 UI(Phase 6 — /admin) E2E: 접수→생성→검수→승인→발급 루프 + 가드 재검증.

LLM 무키·Playwright 무실행: pipeline.generate 를 가짜로 주입(order_flow 가 호출
시점에 해석하므로 monkeypatch 유효), 최종 발급은 order_flow.final_render_fn 을
대체. DB 는 tmp_path(SAJUGEN_ORDERS_DB)로 격리.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from sajugen import order_flow  # noqa: E402
from sajugen import pipeline  # noqa: E402
from sajugen.app import app  # noqa: E402
from sajugen.content.sections_schema import GuardReport, Report23, Section  # noqa: E402
from sajugen.models.report import (  # noqa: E402
    BirthInput,
    CalendarVerification,
    UnifiedReport,
)
from sajugen.pipeline import GenResult  # noqa: E402
from sajugen.store.orders import OrderState, OrderStore  # noqa: E402

# ─────────────────── 픽스처 ───────────────────


def _mini_report23(final_text: str = "순한 흐름이 이어지는 해입니다.") -> Report23:
    return Report23(
        sections=[
            Section(
                id="intro",
                title="이 풀이를 읽는 법",
                source_keys=["myeongni"],
                rule_text="룰 골격 본문",
                final_text=final_text,
                polished=True,
            )
        ],
        guard=GuardReport(
            safe_lint_total=0,
            factcheck_total=0,
            grounding_ok=True,
            polished_sections=1,
            fallback_sections=0,
            clean=True,
        ),
        allow_tokens={
            "ganzhi": ["庚午"],
            "ganzhi_ko": ["경오"],
            "ziwei_majors_in_chart": [],
            "all_star_ko": [],
        },
    )


def _gen_result(tmp_path: Path, **over) -> GenResult:
    base = dict(
        pdf_path=str(tmp_path / "draft.pdf"),
        ok=True,
        reasons=[],
        verify={
            "gate_pass": True,
            "pages": 3,
            "text_chars": 1200,
            "tagged": True,
            "fonts_embedded": True,
        },
        guard={
            "safe_lint_total": 0,
            "factcheck_total": 0,
            "grounding_ok": True,
            "polished_sections": 1,
            "fallback_sections": 0,
            "clean": True,
        },
        crosscheck_warnings=[],
        bazi="庚午 辛巳 庚午 癸未",
        report=_mini_report23(),
        calc_consistent=True,
        input_civil="1990-05-20 14:30",
    )
    base.update(over)
    return GenResult(**base)


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    p = tmp_path / "orders.sqlite"
    monkeypatch.setenv("SAJUGEN_ORDERS_DB", str(p))
    return p


@pytest.fixture
def client(db_path) -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_gen(tmp_path, monkeypatch):
    """pipeline.generate 대체 — 즉시 성공 GenResult. over 로 변형 가능."""

    def install(**over):
        def _fake(*args, **kwargs):
            return _gen_result(tmp_path, **over)

        monkeypatch.setattr(pipeline, "generate", _fake)

    install()
    return install


_FORM = {
    "birth": "1990-05-20 14:30",
    "name": "홍길동",
    "gender": "male",
    "product": "integrated",
    "brand": "default",
    "horoscope": "2026-06-01",
}


def _intake(client: TestClient) -> str:
    """접수 → (TestClient 가 백그라운드 생성까지 완료) → order_id 반환."""
    resp = client.post("/admin/orders", data=_FORM)
    assert resp.status_code == 200
    oid = str(resp.url).rstrip("/").split("/")[-1]
    assert oid.startswith("ord_")
    return oid


def _to_in_review(client: TestClient, oid: str) -> None:
    assert client.post(f"/admin/orders/{oid}/review").status_code == 200


# ─────────────────── 1. happy path ───────────────────


def test_happy_path_to_delivered(client, db_path, fake_gen, tmp_path, monkeypatch):
    oid = _intake(client)
    st = OrderStore(db_path)
    assert st.get_state(oid) == OrderState.DRAFTED  # 접수+백그라운드 생성 완료

    _to_in_review(client, oid)
    assert st.get_state(oid) == OrderState.IN_REVIEW
    assert client.post(f"/admin/orders/{oid}/approve").status_code == 200
    assert st.get_state(oid) == OrderState.APPROVED

    final = tmp_path / "final.pdf"
    final.write_bytes(b"%PDF-1.7 fake")
    monkeypatch.setattr(order_flow, "final_render_fn", lambda rep: str(final))
    assert client.post(f"/admin/orders/{oid}/deliver").status_code == 200
    assert st.get_state(oid) == OrderState.DELIVERED
    assert st.get_report(oid).render_meta["final_pdf"] == str(final)

    actions = [a.action for a in st.audit(oid)]
    assert "create" in actions and "issue_final_pdf" in actions
    trans = [(a.from_state, a.to_state) for a in st.audit(oid) if a.action == "transition"]
    assert ("APPROVED", "DELIVERED") in trans
    st.close()

    # 최종 PDF 다운로드
    dl = client.get(f"/admin/orders/{oid}/pdf?kind=final")
    assert dl.status_code == 200 and dl.headers["content-type"] == "application/pdf"


# ─────────────────── 2. 승인 전 발급 차단(절대규칙 16) ───────────────────


def test_deliver_blocked_before_approved(client, db_path, fake_gen, monkeypatch):
    oid = _intake(client)
    _to_in_review(client, oid)
    called = {"n": 0}
    monkeypatch.setattr(
        order_flow, "final_render_fn", lambda rep: called.__setitem__("n", 1) or "x"
    )
    resp = client.post(f"/admin/orders/{oid}/deliver")
    assert resp.status_code == 409
    assert "절대규칙 16" in resp.json()["detail"]
    assert called["n"] == 0  # render_fn 호출조차 안 됨
    st = OrderStore(db_path)
    assert st.get_state(oid) == OrderState.IN_REVIEW
    st.close()


# ─────────────────── 3. 반려 회귀 ───────────────────


def test_reject_returns_to_drafted(client, db_path, fake_gen):
    oid = _intake(client)
    _to_in_review(client, oid)
    resp = client.post(f"/admin/orders/{oid}/reject", data={"note": "호명 오기"})
    assert resp.status_code == 200
    st = OrderStore(db_path)
    assert st.get_state(oid) == OrderState.DRAFTED
    notes = [a.note for a in st.audit(oid) if a.action == "transition"]
    assert any("반려: 호명 오기" in n for n in notes)
    st.close()


# ─────────────────── 4. CALC_MISMATCH 차단 ───────────────────


def test_calc_mismatch_blocks_and_shows_badge(client, db_path, fake_gen):
    fake_gen(calc_consistent=False, ok=False, reasons=["명리↔자미 사주팔자 불일치"])
    oid = _intake(client)
    st = OrderStore(db_path)
    assert st.get_state(oid) == OrderState.CALC_MISMATCH
    notes = [a.note for a in st.audit(oid) if a.to_state == "CALC_MISMATCH"]
    assert any("불일치" in n for n in notes)
    st.close()

    page = client.get(f"/admin/orders/{oid}")
    assert "교차검증 불일치" in page.text and "진행 차단" in page.text
    # 차단 상태에서 검수 시작 불가
    assert client.post(f"/admin/orders/{oid}/review").status_code == 409


# ─────────────────── 5. 섹션 직접 수정 가드 ───────────────────


def test_edit_rejected_by_safe_lint(client, db_path, fake_gen):
    oid = _intake(client)
    _to_in_review(client, oid)
    resp = client.post(
        f"/admin/orders/{oid}/sections/intro", data={"text": "내년에는 반드시 결혼합니다."}
    )
    assert resp.status_code == 422
    assert "결과 보장" in resp.text
    st = OrderStore(db_path)
    r23 = Report23.model_validate(st.get_report(oid).content)
    assert r23.section("intro").final_text == "순한 흐름이 이어지는 해입니다."  # 미변경
    st.close()


def test_edit_rejected_by_factcheck(client, db_path, fake_gen):
    oid = _intake(client)
    _to_in_review(client, oid)
    resp = client.post(
        f"/admin/orders/{oid}/sections/intro", data={"text": "갑자년에 큰 변화가 옵니다."}
    )
    assert resp.status_code == 422
    assert "갑자" in resp.text  # 허용 토큰(경오) 밖 한글 간지


def test_edit_saved_and_audited(client, db_path, fake_gen):
    oid = _intake(client)
    _to_in_review(client, oid)
    new_text = "경오 일주의 결이 살아나는, 마음이 한결 가벼워지는 해입니다."
    resp = client.post(f"/admin/orders/{oid}/sections/intro", data={"text": new_text})
    assert resp.status_code == 200  # 303 → 상세 재표시
    st = OrderStore(db_path)
    r23 = Report23.model_validate(st.get_report(oid).content)
    assert r23.section("intro").final_text == new_text
    edits = [a for a in st.audit(oid) if a.action == "edit_section"]
    assert edits and edits[0].section == "intro"
    st.close()


def test_edit_forbidden_outside_in_review(client, db_path, fake_gen):
    oid = _intake(client)  # DRAFTED 상태
    resp = client.post(f"/admin/orders/{oid}/sections/intro", data={"text": "수정 시도"})
    assert resp.status_code == 403


# ─────────────────── 6. 수정 반영 발급(복사 아님 증명) ───────────────────


def test_deliver_renders_edited_content(client, db_path, fake_gen, tmp_path, monkeypatch):
    oid = _intake(client)
    _to_in_review(client, oid)
    new_text = "검수에서 직접 다듬은 문장입니다."
    assert (
        client.post(f"/admin/orders/{oid}/sections/intro", data={"text": new_text}).status_code
        == 200
    )
    assert client.post(f"/admin/orders/{oid}/approve").status_code == 200

    captured = {}

    def _capture(rep: UnifiedReport) -> str:
        captured["r23"] = Report23.model_validate(rep.content)
        p = tmp_path / "final2.pdf"
        p.write_bytes(b"%PDF-1.7 fake")
        return str(p)

    monkeypatch.setattr(order_flow, "final_render_fn", _capture)
    assert client.post(f"/admin/orders/{oid}/deliver").status_code == 200
    assert captured["r23"].section("intro").final_text == new_text  # 드래프트 복사 아님


# ─────────────────── 7. needs_review 표시 ───────────────────


def test_guard_unclean_marks_needs_review(client, db_path, fake_gen):
    bad_guard = {
        "safe_lint_total": 1,
        "factcheck_total": 0,
        "grounding_ok": True,
        "polished_sections": 0,
        "fallback_sections": 2,
        "clean": False,
    }
    fake_gen(ok=False, reasons=["콘텐츠 가드 미통과(§12=1)"], guard=bad_guard)
    oid = _intake(client)
    st = OrderStore(db_path)
    assert st.get_state(oid) == OrderState.DRAFTED  # 차단 아님 — 검수 강화
    assert st.get_report(oid).safety_flags.needs_review is True
    st.close()
    page = client.get(f"/admin/orders/{oid}")
    assert "검수 필요" in page.text and "콘텐츠 가드 미통과" in page.text


# ─────────────────── 8. 목록 필터 ───────────────────


def test_list_filter_by_state(client, db_path, fake_gen):
    oid1 = _intake(client)
    oid2 = _intake(client)
    _to_in_review(client, oid2)
    page = client.get("/admin?state=IN_REVIEW")
    assert oid2 in page.text and oid1 not in page.text


# ─────────────────── 9. 신규 필드 직렬화 왕복 ───────────────────


def test_unified_report_roundtrip_with_new_fields():
    r = UnifiedReport(
        order_id="ord_x",
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        content=_mini_report23().model_dump(),
        render_meta={"draft_pdf": "out/draft.pdf", "gen_params": {"year": 1990}},
    )
    again = UnifiedReport.model_validate_json(r.model_dump_json())
    assert again == r
    assert Report23.model_validate(again.content).section("intro").polished is True
