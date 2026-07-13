# -*- coding: utf-8 -*-
"""생시 미상 삼주 콘텐츠·LLM·렌더·최종 게이트 양방 계약."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import sys
from types import SimpleNamespace

import pytest

from sajugen import config as cfg
from sajugen import integrated
from sajugen.calc import engine
from sajugen.content import (
    builder,
    client_tone_lint,
    customer_meta_lint,
    delivery_quality,
    factcheck,
    llm_sections,
    quality_lint,
    report_context,
    rules,
    style_lint,
    unknown_time_policy as policy,
)
from sajugen.render import charts, pdf as render_pdf, verify as verify_pdf


def _result():
    return engine.build(
        2000,
        1,
        15,
        None,
        None,
        is_male=False,
        birth_time_mode="three_pillar",
        horoscope_date="2026-07-12",
    )


def _provenance() -> dict:
    return policy.serialize_provenance(_result().provenance)


def _report_context(birth_time_mode: str):
    return report_context.build_report_context(
        selected_modules=("love", "job", "wealth", "health"),
        question_category="전반",
        active_section_ids=("intro", "wonguk", "nature", "frame", "flow", "consult"),
        birth_time_mode=birth_time_mode,
    )


def _capture_compose_request(monkeypatch, context):
    """네트워크 없이 Anthropic SDK 경계에서 최종 system/user 요청을 캡처한다."""

    captured = {}

    class _Messages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="합성 응답")],
                usage=SimpleNamespace(
                    input_tokens=1,
                    output_tokens=1,
                    cache_creation_input_tokens=1,
                    cache_read_input_tokens=0,
                ),
                stop_reason="end_turn",
                model="claude-sonnet-4-6",
            )

    fake_anthropic = SimpleNamespace(
        Anthropic=lambda **_kwargs: SimpleNamespace(messages=_Messages())
    )
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)
    backend = llm_sections.AnthropicBackend()
    monkeypatch.setattr(backend, "available", lambda: True)
    result = backend.compose(
        section_id="wonguk",
        title="원국",
        category="전반",
        base_text="연주와 월주와 일주의 합성 근거입니다.",
        ref_year=2026,
        ref_date="2026-07-13",
        report_context=context,
    )
    assert result == "합성 응답"
    return captured


def test_provenance_contract_accepts_calc_result_and_rejects_schema_edges():
    valid = _provenance()
    assert policy.provenance_contract_lint(
        valid,
        birth_time_mode="three_pillar",
    ) == []

    cases = []
    for candidate_count in (0, 11, 13):
        bad = deepcopy(valid)
        bad["candidate_count"] = candidate_count
        cases.append((bad, "candidate_count"))
    bad = deepcopy(valid)
    bad["three_pillar_schema_version"] = 2
    cases.append((bad, "schema_version"))
    bad = deepcopy(valid)
    bad["stable_fact_ids"] = "day_pillar"
    cases.append((bad, "stable_fact_ids"))
    bad = deepcopy(valid)
    bad["stable_fact_ids"] = ["day_pillar", "day_pillar"]
    cases.append((bad, "stable_fact_ids_duplicate"))
    bad = deepcopy(valid)
    bad["suppressed_fact_ids"] = [valid["stable_fact_ids"][0]]
    cases.append((bad, "fact_id_overlap"))

    for provenance, expected_rule in cases:
        rules = {
            hit["rule"]
            for hit in policy.provenance_contract_lint(
                provenance,
                birth_time_mode="three_pillar",
            )
        }
        assert expected_rule in rules


@pytest.mark.parametrize(
    ("text", "expected_rule"),
    [
        ("출생 시간은 12:00으로 적혀 있습니다.", "birth_time_value"),
        ("생시는 정오 기준으로 두었습니다.", "noon_estimate"),
        ("진태양시와 경도 보정을 적용했습니다.", "solar_time_correction"),
        ("시주는 갑자시로 읽습니다.", "hour_pillar"),
        ("네 기둥을 합쳐 사주팔자를 봅니다.", "four_pillar_claim"),
        ("자미두수 명반의 명궁 주성을 봅니다.", "ziwei_fact"),
        ("생시가 확인되면 다시 살펴보세요.", "birth_time_upsell"),
        ("출생 시각이 확인되면 다시 살펴보세요.", "birth_time_upsell"),
    ],
)
def test_public_lint_blocks_forbidden_customer_facts_without_raw_text(text, expected_rule):
    hits = policy.unknown_time_provenance_lint(
        text,
        birth_time_mode="three_pillar",
        provenance=_provenance(),
        page=2,
        source="admin_edit",
    )
    assert expected_rule in {hit["rule"] for hit in hits}
    assert all(set(hit) == {"rule", "token", "count", "page", "source"} for hit in hits)
    assert all(text not in str(hit) and "12:00" not in str(hit) for hit in hits)


@pytest.mark.parametrize(
    "text",
    [
        policy.THREE_PILLAR_NOTICE,
        "오후 3시에 산책하고 저녁에는 쉬어 보세요.",
        "임신 시 건강 변화는 의료진과 상의하세요.",
        "사주를 생활의 방향을 살피는 참고로만 씁니다.",
        "세 기둥에서 확인되는 내용만 풀이했습니다.",
    ],
)
def test_public_lint_allows_notice_daily_time_and_general_saju_word(text):
    assert policy.unknown_time_provenance_lint(
        text,
        birth_time_mode="three_pillar",
        provenance=_provenance(),
    ) == []


def test_three_pillar_builder_uses_only_allowed_sources_and_fact_tokens():
    saju = _result()
    report = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        birth_time_mode="three_pillar",
        product="integrated_full",
    )
    ids = {section.id for section in report.sections}
    assert "ziwei" not in ids and "together" not in ids
    assert report.guard.clean is True
    assert report.birth_time_mode == "three_pillar"
    assert "추정" not in "\n".join(section.final_text for section in report.sections)
    assert all("{" not in section.final_text and "}" not in section.final_text for section in report.sections)
    assert tuple(report.fact_source_ids) == policy.ALLOWED_FACT_SOURCES
    assert all(
        set(section.source_keys) <= set(policy.ALLOWED_FACT_SOURCES)
        for section in report.sections
        if section.id not in {"toc", "appendix_terms", "colophon"}
    )
    allow = factcheck.allowed_tokens(saju)
    assert allow["ziwei_majors_in_chart"] == set()
    assert allow["fact_source_ids"] == set(policy.ALLOWED_FACT_SOURCES)
    assert len({saju.three_pillar.year.ganzhi, saju.three_pillar.month.ganzhi, saju.three_pillar.day.ganzhi} & allow["ganzhi"]) == 3


def test_three_pillar_rule_skeletons_do_not_conflict_with_final_text_lints():
    """라운드19에서 드러난 삼주 골격×문서 메타 패턴 충돌의 재발을 막는다.

    실제 삼주 계산으로 만든 모든 룰 골격이 최종 PDF 단계의 문서 메타·외래어·
    날것 계산어 lint와 충돌하지 않는지만 검증한다. LLM 후보 문안과 PDF 조판은 이
    비-Playwright 단위 테스트의 검증 범위가 아니다.
    """

    skeletons = rules.build_all(
        _result(),
        ref_year=2026,
        birth_time_mode="three_pillar",
    )
    assert skeletons

    for section_id, text in skeletons.items():
        assert customer_meta_lint.lint(text) == [], section_id
        assert client_tone_lint.loanword_lint(text) == [], section_id
        assert client_tone_lint.raw_calc_lint(text) == [], section_id

    blocked = "세 자리는 따로 떼어 보지 않고 서로 어떤 방향을 보태는지 함께 읽습니다."
    assert customer_meta_lint.lint(blocked) == [
        {
            "type": "ai_meta",
            "rule": "guided_structure_walkthrough",
            "count": 1,
        }
    ]


def test_three_pillar_final_text_and_chart_do_not_conflict_with_verify_lints():
    """라운드20에서 놓친 빌더 최종 문안·차트와 verify lint 충돌을 고정한다.

    raw 골격은 표시 직전 정규화 전 단계이므로 기존 3종 lint 계약이 담당한다. 이 테스트는
    no-LLM 빌더의 전 섹션 ``final_text``를 quality/style lint와 대조하고 삼주 차트의 고객
    표기만 확인한다. LLM 후보, PDF 조판·페이지 분량, render 단계 주입 문안은 검증하지 않는다.
    분량은 delivery 양방 테스트와 E2E가 담당한다.
    """

    saju = _result()
    report = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        birth_time_mode="three_pillar",
        product="integrated_full",
    )
    assert report.sections

    for section in report.sections:
        assert quality_lint.lint(section.final_text) == [], section.id
        assert style_lint.lint(section.final_text) == [], section.id

    blocked_quality = quality_lint.lint("순위와 시작점은 이 장에서 말하지 않습니다.")
    assert [hit["type"] for hit in blocked_quality] == ["internal_meta_label"]

    blocked_style = style_lint.lint("세운·월운")
    assert [hit["why"] for hit in blocked_style] == ["가운뎃점 난발"]

    # known용 manse_table은 건드리지 않고, 삼주 3열 표에만 가운뎃점이 없음을 고정한다.
    assert "·" not in charts.three_pillar_table(saju.three_pillar)


def test_three_pillar_prompt_context_has_narrow_fact_sources_and_no_forbidden_owners():
    context = report_context.build_report_context(
        selected_modules=("love", "job", "wealth", "health"),
        question_category="전반",
        active_section_ids=("intro", "wonguk", "nature", "frame", "flow", "consult"),
        birth_time_mode="three_pillar",
    )
    payload = context.as_dict()
    prompt = context.to_prompt()
    assert payload["fact_source_ids"] == list(policy.ALLOWED_FACT_SOURCES)
    assert payload["birth_time_mode"] == "three_pillar"
    assert "four_pillars" not in prompt
    assert "spouse_palace" not in prompt
    assert "current_daewoon_single_owner" not in prompt
    assert "ziwei_core" not in prompt


def test_three_pillar_compose_request_has_neutral_system_and_narrow_user_evidence(
    monkeypatch,
):
    context = _report_context("three_pillar")
    captured = _capture_compose_request(monkeypatch, context)
    system = captured["system"]
    user = captured["messages"][0]["content"]

    # 첫 공통 블록은 삼주에서 허용되지 않는 내용을 먼저 권한 뒤 뒤에서 취소하지 않는다.
    assert system[0] == {
        "type": "text",
        "text": llm_sections._THREE_PILLAR_COMPOSE_SYSTEM,
    }
    assert system[1] == {
        "type": "text",
        "text": llm_sections._THREE_PILLAR_SYSTEM_OVERRIDE,
    }
    assert system[2] == {
        "type": "text",
        "text": context.to_prompt(),
        "cache_control": {"type": "ephemeral", "ttl": "5m"},
    }
    assert all("cache_control" not in block for block in system[:-1])
    positive_system = system[0]["text"]
    for forbidden_positive_instruction in (
        "사주·자미두수 상담가",
        "신살·별·궁",
        "자미두수 궁 이야기를",
        "네 기둥(연·월·일·시)",
    ):
        assert forbidden_positive_instruction not in positive_system
    assert "계약 JSON의 허용 출처" in user
    assert "신살·별·궁·연도" not in user
    assert llm_sections._THREE_PILLAR_COMPOSE_GUIDE["wonguk"] in user
    assert "연주와 월주와 일주의 합성 근거입니다." in user
    assert "시주" not in user and "자미두수" not in user and "후보" not in user


def test_known_time_compose_request_preserves_original_system_and_user_bytes(
    monkeypatch,
):
    context = _report_context("known")
    captured = _capture_compose_request(monkeypatch, context)
    system = captured["system"]
    user = captured["messages"][0]["content"]

    # known-time 프롬프트는 삼주 분기 도입 전 승인 문자열을 byte-for-byte로 고정한다.
    assert hashlib.sha256(llm_sections._COMPOSE_SYSTEM.encode("utf-8")).hexdigest() == (
        "a17f90fb0aa09ebf86adbac0efe6e1b2fc406ea7a7de46c2757fa626c7c4380a"
    )
    assert system == [
        {"type": "text", "text": llm_sections._COMPOSE_SYSTEM},
        {
            "type": "text",
            "text": context.to_prompt(),
            "cache_control": {"type": "ephemeral", "ttl": "5m"},
        },
    ]
    assert all("cache_control" not in block for block in system[:-1])
    assert llm_sections._THREE_PILLAR_SYSTEM_OVERRIDE not in str(system)
    assert (
        "[근거 자료 — 이 안의 사실(한글 간지·오행·십성·신살·별·궁·연도)만 쓰고, "
        "표기·문체·안전 규칙을 지켜 이야기로 풀어라]"
    ) in user
    assert llm_sections._compose_system_blocks(None) == llm_sections._COMPOSE_SYSTEM


def test_three_pillar_html_has_one_notice_and_three_column_chart_only():
    saju = _result()
    report = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        birth_time_mode="three_pillar",
        product="integrated_full",
    )
    html = render_pdf.render_html(
        report,
        saju,
        name="합성인",
        brand=cfg.brand("sajudoryeong"),
        birth_time_mode="three_pillar",
        three_pillar_provenance=report.three_pillar_provenance,
    )
    assert html.count(policy.THREE_PILLAR_NOTICE) == 1
    assert "年柱" in html and "月柱" in html and "日柱" in html
    assert "時柱" not in html
    assert "생시 미상" not in html
    assert "진태양시" not in html
    assert "사주팔자" not in html
    assert "자미두수" not in html
    assert charts.three_pillar_table(saju.three_pillar) in html


def test_integrated_three_pillar_metadata_has_three_ganzhi_and_date_only():
    result = integrated.build_integrated_full(
        [("합성인", (2000, 1, 15, None, None), False)],
        receiver_name="합성인",
        situation="",
        render=False,
        use_llm=False,
        modules=("love", "job", "wealth", "health"),
        birth_time_mode="three_pillar",
    )
    assert result["bazi"].split() == [
        result["report"].three_pillar.year.ganzhi,
        result["report"].three_pillar.month.ganzhi,
        result["report"].three_pillar.day.ganzhi,
    ]
    assert result["input_civil"] == result["input_civil_date"]
    assert ":" not in result["input_civil"]
    assert "12:00" not in result["input_civil"]


def test_integrated_live_build_consumes_three_pillar_chart_after_sparse_merge():
    result = integrated.build_integrated_full(
        [("합성인", (2000, 1, 15, None, None), False)],
        receiver_name="합성인",
        situation="",
        render=False,
        use_llm=False,
        modules=("love", "job", "wealth", "health"),
        birth_time_mode="three_pillar",
    )
    report = result["report"]
    assert "personal_wonguk" in result["premerge_section_ids"]
    assert any(section.id.startswith("personal_") for section in report.sections)

    html = render_pdf.render_html(
        report,
        report,
        name="",
        brand=cfg.brand("sajudoryeong"),
        birth_time_mode="three_pillar",
        three_pillar_provenance=report.three_pillar_provenance,
    )
    expected_chart = charts.three_pillar_table(report.three_pillar)
    assert html.count(policy.THREE_PILLAR_NOTICE) == 1
    assert html.count('aria-label="연주 월주 일주 세 기둥 명식표"') == 1
    assert expected_chart in html
    assert "時柱" not in html


def test_integrated_content_roundtrip_restores_chart_for_personal_wonguk(
    monkeypatch,
    tmp_path,
):
    result = integrated.build_integrated_full(
        [("합성인", (2000, 1, 15, None, None), False)],
        receiver_name="합성인",
        situation="",
        render=False,
        use_llm=False,
        modules=("love", "job", "wealth", "health"),
        birth_time_mode="three_pillar",
    )
    content_path = integrated._save_integrated_content(
        result,
        situation="",
        ref_year=2026,
        ref_date="2026-07-13",
        brand="sajudoryeong",
        out_name="synthetic.pdf",
        out_dir=tmp_path,
        model="rule",
    )
    captured = {}

    def _fake_render_pdf(report, saju, out_name, **kwargs):
        captured["section_ids"] = [section.id for section in report.sections]
        captured["three_pillar"] = saju.three_pillar
        captured["birth_time_mode"] = kwargs["birth_time_mode"]
        captured["provenance"] = kwargs["three_pillar_provenance"]
        captured["html"] = render_pdf.render_html(
            report,
            saju,
            name=kwargs["name"],
            brand=kwargs["brand"],
            chapter_breaks=kwargs["chapter_breaks"],
            body_font_size=kwargs["body_font_size"],
            body_line_height=kwargs["body_line_height"],
            birth_time_mode=kwargs["birth_time_mode"],
            three_pillar_provenance=kwargs["three_pillar_provenance"],
        )
        return str(tmp_path / out_name)

    monkeypatch.setattr(integrated.render_pdf, "render_pdf", _fake_render_pdf)
    monkeypatch.setattr(
        integrated.render_verify,
        "verify",
        lambda *_args, **_kwargs: {"gate_pass": True},
    )

    rerendered = integrated.render_integrated_from_content(
        content_path,
        out_dir=tmp_path,
    )
    assert rerendered["verify"]["gate_pass"] is True
    assert "personal_wonguk" in result["premerge_section_ids"]
    assert captured["section_ids"] == [
        section.id for section in result["report"].sections
    ]
    assert captured["birth_time_mode"] == "three_pillar"
    assert captured["provenance"] == result["three_pillar_provenance"]
    assert captured["three_pillar"].day.ganzhi == result["report"].three_pillar.day.ganzhi
    assert captured["html"].count(policy.THREE_PILLAR_NOTICE) == 1
    assert captured["html"].count('aria-label="연주 월주 일주 세 기둥 명식표"') == 1
    assert charts.three_pillar_table(captured["three_pillar"]) in captured["html"]
    assert "時柱" not in captured["html"]


def test_known_integrated_personal_wonguk_has_no_three_pillar_chart():
    result = integrated.build_integrated_full(
        [("합성인", (2000, 1, 15, 12, 0), False)],
        receiver_name="합성인",
        situation="",
        render=False,
        use_llm=False,
        modules=("love", "job", "wealth", "health"),
        birth_time_mode="known",
    )
    report = result["report"]
    assert "personal_wonguk" in result["premerge_section_ids"]

    html = render_pdf.render_html(
        report,
        SimpleNamespace(input_civil="2000-01-15 12:00"),
        name="",
        brand=cfg.brand("sajudoryeong"),
        birth_time_mode="known",
    )
    assert 'aria-label="연주 월주 일주 세 기둥 명식표"' not in html
    assert policy.THREE_PILLAR_NOTICE not in html


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def get_text(self):
        return self._text

    def get_fonts(self, full=True):
        return [(0, "ttf", "Type0", "EmbeddedSubset", "F1")]


class _FakeDoc:
    def __init__(self, pages: list[str]):
        self._pages = pages
        self.page_count = len(pages)

    def load_page(self, index: int):
        return _FakePage(self._pages[index])

    def get_toc(self):
        return []

    def pdf_catalog(self):
        return 1

    def xref_object(self, _xref):
        return "<< /StructTreeRoot 1 0 R /MarkInfo << /Marked true >> >>"

    def close(self):
        return None


_CLEAN = (
    "세 기둥에서 확인된 바탕을 생활의 속도와 관계의 방향에 연결해 봅니다. "
    "서두르지 않고 작은 행동 뒤의 반응을 살피면 선택의 부담을 줄일 수 있습니다. "
)


def _verify(monkeypatch, pages: list[str], *, mode="three_pillar", provenance=None):
    monkeypatch.setattr(verify_pdf.fitz, "open", lambda _path: _FakeDoc(pages))
    monkeypatch.setattr(
        verify_pdf,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )
    return verify_pdf.verify(
        "synthetic.pdf",
        birth_time_mode=mode,
        three_pillar_provenance=_provenance() if provenance is None else provenance,
    )


def test_verify_forwards_normalized_birth_time_mode_to_delivery_quality(monkeypatch):
    """verify가 이미 정규화한 삼주 모드를 delivery 소비처까지 전달하는지 고정한다."""

    captured: dict[str, object] = {}
    original_analyze = delivery_quality.analyze

    def _capture_analyze(*args, **kwargs):
        captured["birth_time_mode"] = kwargs.get("birth_time_mode")
        return original_analyze(*args, **kwargs)

    monkeypatch.setattr(delivery_quality, "analyze", _capture_analyze)
    _verify(
        monkeypatch,
        ["날짜\n" + policy.THREE_PILLAR_NOTICE, "목차", _CLEAN * 30, "용어 풀이"],
    )

    assert captured["birth_time_mode"] == "three_pillar"


@pytest.mark.parametrize(
    ("page_index", "injection"),
    [
        (0, "출생 시간은 12:00입니다."),
        (2, "시주는 갑자시로 읽습니다."),
        (3, "자미두수 명반의 명궁을 봅니다."),
    ],
)
def test_cover_body_appendix_injection_fails_final_gate(monkeypatch, page_index, injection):
    pages = [
        "날짜\n" + policy.THREE_PILLAR_NOTICE,
        "목차",
        _CLEAN * 25,
        "용어 풀이 " + _CLEAN * 8,
    ]
    pages[page_index] += " " + injection
    result = _verify(monkeypatch, pages)
    assert result["unknown_time_provenance_clean"] is False
    assert result["unknown_time_provenance_hits"]
    assert result["gate_pass"] is False
    assert all(
        set(hit) == {"rule", "token", "count", "page", "source"}
        for hit in result["unknown_time_provenance_hits"]
    )


def test_clean_three_pillar_and_known_paths_do_not_false_positive(monkeypatch):
    pages = ["날짜\n" + policy.THREE_PILLAR_NOTICE, "목차", _CLEAN * 30, "용어 풀이 " + _CLEAN * 8]
    result = _verify(monkeypatch, pages)
    assert result["unknown_time_provenance_clean"] is True
    assert result["gate_pass"] is True, result

    known = _verify(
        monkeypatch,
        ["표지", (_CLEAN + " 네 기둥과 사주팔자를 설명합니다. ") * 25, "맺음"],
        mode="known",
        provenance={},
    )
    assert known["unknown_time_provenance_clean"] is True


def test_missing_mode_cannot_bypass_present_or_missing_provenance(monkeypatch):
    pages = ["날짜\n" + policy.THREE_PILLAR_NOTICE, "목차", _CLEAN * 30, "용어 풀이"]
    inferred = _verify(monkeypatch, pages, mode=None, provenance=_provenance())
    assert inferred["unknown_time_provenance_clean"] is True

    blocked = _verify(monkeypatch, pages, mode=None, provenance={})
    assert blocked["unknown_time_provenance_clean"] is False
    assert blocked["gate_pass"] is False
