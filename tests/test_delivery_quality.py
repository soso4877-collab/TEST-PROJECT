# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import delivery_quality as dq  # noqa: E402


def _premium_text() -> str:
    lead = (
        "자미두수로 보면 집과 터전의 판단이 강하고, 돈과 계약은 서류 확인이 먼저입니다. "
        "이사는 김포와 계양을 모두 놓고 생활 거리와 병원, 사람의 도움을 같이 보아야 합니다. "
        "로타리 클럽 창립은 모임의 역할을 작게 나누고 돈 관리는 따로 두면 좋습니다. "
        "배우자의 도움은 받을 수 있지만 명의와 큰돈은 직접 확인해야 합니다. "
        "올해 하반기에는 매매 조건을 고르고, 내년 상반기에는 실제 거처를 굳히는 판단 지점이 옵니다. "
        "먼저 가격과 계약 조건을 적고, 서두르지 말고 사람의 말보다 문서를 확인하세요. "
        "청마라는 이름은 이전 맥락으로만 짧게 참고하면 충분합니다. "
    )
    filler = (
        "이 풀이에서는 집 문제와 사람 문제를 분리해서 봅니다. "
        "매매는 급히 낮추기보다 조건을 고르는 쪽이 낫고, 이동은 생활의 편함을 먼저 보아야 합니다. "
        "돈은 새 일을 키우는 힘이 되지만 약속을 말로만 두면 부담이 커집니다. "
    )
    return lead + filler * 95


def test_nonpremium_default_reports_without_paid_threshold_failure():
    r = dq.analyze("짧은 일반 점검 본문입니다.", pages=3)
    assert r["clean"] is True
    assert r["premium"] is False


def test_nonpremium_without_question_reports_repetition_as_warning_only():
    r = dq.analyze("또렷 " * 4, pages=2)
    assert r["clean"] is True
    assert "repetitive_phrasing" in {w["rule"] for w in r["warnings"]}
    assert "repetitive_phrasing" not in {f["rule"] for f in r["failures"]}


def test_premium_thin_report_fails_density_and_ziwei():
    r = dq.analyze("짧은 본문입니다.", pages=14, premium=True)
    rules = {f["rule"] for f in r["failures"]}
    assert "premium_pages" in rules
    assert "premium_text_chars" in rules
    assert "missing_usable_ziwei" in rules
    assert r["clean"] is False


def test_premium_without_customer_context_reports_layout_and_repetition_only():
    text = (
        "자미두수로 보면 집과 돈과 일이 함께 보이고 흐름도 함께 봅니다. "
        "자미두수의 사람과 관계, 이동의 단서도 흐름으로 참고합니다. "
    ) * 220
    r = dq.analyze(
        text,
        pages=24,
        product="integrated",
        low_density_pages=[{"page": 3, "chars": 50, "text": "짧은 페이지"}],
    )
    failure_rules = {f["rule"] for f in r["failures"]}
    warning_rules = {w["rule"] for w in r["warnings"]}
    assert r["clean"] is True
    assert "premium_low_density_pages" not in failure_rules
    assert "repetitive_phrasing" not in failure_rules
    assert "premium_low_density_pages" in warning_rules
    assert "repetitive_phrasing" in warning_rules


def test_premium_integrated_question_passes_when_axes_and_ziwei_are_present():
    concern = "아파트 매매와 김포 이사, 로타리 클럽 창립, 도와주는 사람과 시기가 궁금합니다"
    r = dq.analyze(
        _premium_text(),
        pages=27,
        product="integrated",
        concern=concern,
        expected_context_terms=["청마"],
    )
    assert r["clean"] is True, r
    assert r["premium"] is True
    assert r["missing_axes"] == []
    assert r["ziwei"]["ok"] is True
    assert r["expected_context_hits"]["청마"] == 1
    assert r["frontloaded_answer"]["ok"] is True
    assert r["ziwei"]["cross_domains"]


def test_love_or_reunion_question_requires_near_term_timing_and_action():
    text = (
        "재회 문제는 상대의 연락과 대화 태도를 보아야 합니다. "
        "상대가 실제로 대화를 이어 오는지 확인하세요. "
        "자미두수로 보면 사람과 관계, 돈의 부담이 함께 걸립니다. "
    ) * 70
    r = dq.analyze(text, pages=22, premium=True, concern="헤어진 사람과 재회가 될까요")
    assert "timing" in r["missing_axes"]
    assert r["clean"] is False


def test_premium_question_requires_frontloaded_answer_not_late_only():
    late_answer = (
        "정성스럽게 전체 흐름을 천천히 살펴보겠습니다. "
        "여러 갈래가 겹쳐 있으니 배경부터 길게 보겠습니다. "
    ) * 45
    late_answer += _premium_text()
    r = dq.analyze(
        late_answer,
        pages=27,
        product="integrated",
        concern="아파트 매매와 김포 이사, 로타리 클럽 창립 시기가 궁금합니다",
        expected_context_terms=["청마"],
    )
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_frontloaded_answer" in rules
    assert r["frontloaded_answer"]["ok"] is False


def test_reunion_question_requires_near_term_timing_not_only_generic_timing():
    text = (
        "결론부터 말하면 재회 문제는 상대의 연락과 대화 태도를 먼저 보아야 합니다. "
        "다가갈 때는 학교와 겹지인을 이용하되 부담을 주지 않는 말부터 시작하세요. "
        "시기는 너무 멀리 보지 말고 상대가 실제로 대화를 이어 오는지 확인해야 합니다. "
        "자미두수로 보면 사람과 관계, 돈의 부담이 함께 걸립니다. "
    ) * 45
    r = dq.analyze(text, pages=24, product="integrated", concern="헤어진 사람과 재회 시기가 궁금합니다")
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_near_term_timing" in rules
    assert r["near_term_timing"]["required"] is True


def test_reunion_question_passes_with_one_year_timing_and_contact_action():
    text = (
        "결론부터 말하면 1년 안에서는 올해 하반기보다 내년 초가 더 조심스럽게 볼 구간입니다. "
        "먼저 연락을 세게 밀지 말고, 겹지인과 학교 접점을 통해 짧은 안부부터 여는 편이 좋습니다. "
        "상대가 대화를 이어 오면 다음 단계로 가고, 반응이 끊기면 한 번 물러서야 합니다. "
        "자미두수로 보면 관계와 사람의 자리가 함께 움직여, 연락보다 분위기 회복이 먼저입니다. "
    ) * 45
    r = dq.analyze(text, pages=24, product="integrated", concern="헤어진 사람과 재회 시기와 다가가는 방법")
    assert r["near_term_timing"]["ok"] is True
    assert r["frontloaded_answer"]["ok"] is True
    assert "missing_near_term_timing" not in {f["rule"] for f in r["failures"]}


def test_ziwei_name_only_without_cross_domains_fails_premium():
    text = "자미두수도 참고했습니다. " + ("설명을 이어갑니다. " * 40) + (
        "집 문제와 돈 문제와 사람 문제를 충분히 설명합니다. "
        "이사와 계약과 관계를 차분히 보아야 합니다. "
    ) * 120
    r = dq.analyze(text, pages=27, premium=True)
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_usable_ziwei" in rules
    assert r["ziwei"]["markers"]
    assert len(r["ziwei"]["cross_domains"]) < 2


def test_customer_specific_context_requires_source_or_expected_context():
    r = dq.analyze(_premium_text(), pages=27, product="integrated")
    rules = {f["rule"] for f in r["failures"]}
    assert "unbacked_context_terms" in rules
    assert r["context_provenance"]["unbacked_terms"] == ["청마"]


def test_repetitive_ai_like_word_and_absolute_guarantee_fail():
    text = _premium_text() + " 또렷 또렷 100% 재회합니다"
    r = dq.analyze(text, pages=27, premium=True, concern="재회 시기가 궁금합니다")
    rules = {f["rule"] for f in r["failures"]}
    assert "repetitive_phrasing" in rules
    assert "absolute_guarantee" in rules


def test_expected_context_missing_fails_and_overuse_warns():
    missing = dq.analyze(_premium_text(), pages=27, premium=True, expected_context_terms=["청마", "새이름"])
    assert "새이름" in missing["missing_context_terms"]
    assert missing["clean"] is False

    overused_text = _premium_text() + " 청마 청마 청마 청마"
    overused = dq.analyze(overused_text, pages=27, premium=True, expected_context_terms=["청마"])
    assert overused["overused_context_terms"]["청마"] > 3
    assert overused["warnings"]


def test_pipeline_passes_product_and_concern_to_pdf_verify(monkeypatch):
    from sajugen import pipeline

    captured = {}

    def fake_verify(pdf_path, **kwargs):
        captured.update(kwargs)
        return {
            "gate_pass": True,
            "text_chars": 12_000,
            "tagged": True,
            "fonts_embedded": True,
        }

    monkeypatch.setattr(pipeline.render_pdf, "render_pdf", lambda *a, **k: "fake.pdf")
    monkeypatch.setattr(pipeline.render_verify, "verify", fake_verify)

    r = pipeline.generate(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
        product="integrated",
        concern="아파트 매매와 이사 시기가 궁금합니다",
    )
    assert r.ok is True
    assert captured["product"] == "integrated"
    assert captured["concern"] == "아파트 매매와 이사 시기가 궁금합니다"


def test_final_render_passes_order_product_and_concern_to_pdf_verify(monkeypatch):
    from sajugen import order_flow
    from sajugen.models.report import BirthInput, CalendarVerification, ReportPlan, UnifiedReport

    captured = {}

    def fake_verify(pdf_path, **kwargs):
        captured.update(kwargs)
        return {"gate_pass": True}

    report = UnifiedReport(
        order_id="ord_test",
        birth=BirthInput(gender="F", input_date="2000-01-01", concern_text="재회 시기"),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        report_plan=ReportPlan(product="integrated"),
        content={
            "sections": [
                {
                    "id": "consult",
                    "title": "상담",
                    "source_keys": ["input"],
                    "rule_text": "본문",
                    "final_text": "본문",
                    "polished": False,
                    "guard_violations": [],
                }
            ],
            "guard": {
                "safe_lint_total": 0,
                "factcheck_total": 0,
                "grounding_ok": True,
                "polished_sections": 0,
                "fallback_sections": 0,
                "clean": True,
            },
            "concern_category": None,
            "allow_tokens": {},
        },
        render_meta={
            "gen_params": {
                "product": "integrated",
                "concern": "재회 시기",
                "brand": "default",
            },
            "input_civil": "2000-01-01 12:00",
        },
    )
    monkeypatch.setattr(order_flow.render_pdf, "render_pdf", lambda *a, **k: "final.pdf")
    monkeypatch.setattr(order_flow.render_verify, "verify", fake_verify)

    assert order_flow.final_render_fn(report) == "final.pdf"
    assert captured["product"] == "integrated"
    assert captured["concern"] == "재회 시기"
