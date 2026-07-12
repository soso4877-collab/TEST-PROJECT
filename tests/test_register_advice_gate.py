# -*- coding: utf-8 -*-
"""문체 register·외부 도메인 조언 게이트 양방 회귀(합성 텍스트만, PII 0)."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import client_tone_lint as ct  # noqa: E402
from sajugen.content import builder, llm_sections, rules  # noqa: E402
from sajugen.content import delivery_quality as dq  # noqa: E402
from sajugen.calc import engine  # noqa: E402
from sajugen import gunghap  # noqa: E402
from sajugen.followup import answer_gate  # noqa: E402
from sajugen.relationship import delivery_gate as relationship_delivery_gate  # noqa: E402
from sajugen.render import verify as verify_pdf  # noqa: E402


def test_register_contract_hard_warning_allow_and_exact_shape():
    text = (
        "결과지 참고 준비 구간 구간 정보 수집 커트라인 "
        "큰 그림 그림을 잡다 그림을 잡아 두다 "
        "항목 자료 검토 점검 활용 전략 스트레스"
    )
    hits = ct.register_lint(text, page=7)

    assert all(set(hit) == {"rule", "token", "count", "page", "severity"} for hit in hits)
    assert all(hit["page"] == 7 for hit in hits)
    hard = {(hit["rule"], hit["token"]) for hit in hits if hit["severity"] == "hard"}
    warning = {(hit["rule"], hit["token"]) for hit in hits if hit["severity"] == "warning"}
    assert hard == {
        ("result_sheet", "결과지"),
        ("reference_register", "참고"),
        ("time_interval", "준비 구간"),
        ("time_interval", "구간"),
        ("information_collection", "정보 수집"),
        ("cutline", "커트라인"),
        ("big_picture", "큰 그림"),
        ("big_picture", "그림을 잡다"),
        ("big_picture", "그림을 잡아 두다"),
    }
    assert warning == {
        ("document_noun", "항목"),
        ("document_noun", "자료"),
        ("document_noun", "검토"),
        ("document_noun", "점검"),
        ("document_noun", "활용"),
        ("document_noun", "전략"),
    }
    assert all(hit["token"] != "스트레스" for hit in hits)
    assert ct.is_register_clean(text) is False


def test_register_longest_first_dedupes_preparation_interval():
    hits = ct.register_lint("준비 구간을 두 번 말하지 않습니다.")
    interval_hits = [hit for hit in hits if hit["rule"] == "time_interval"]
    assert interval_hits == [
        {
            "rule": "time_interval",
            "token": "준비 구간",
            "count": 1,
            "page": None,
            "severity": "hard",
        }
    ]


def test_register_warning_only_and_stress_do_not_block():
    hits = ct.register_lint("자료를 검토하고 활용 전략을 점검합니다. 스트레스도 살핍니다.")
    assert hits
    assert {hit["severity"] for hit in hits} == {"warning"}
    assert ct.is_register_clean("자료를 검토하고 활용 전략을 점검합니다. 스트레스도 살핍니다.")
    assert ct.register_lint("스트레스를 천천히 살핍니다.") == []


@pytest.mark.parametrize(
    ("text", "expected_rule"),
    [
        ("필요한 정보를 수집하세요.", "information_collection"),
        ("지원 커트 라인을 살펴봅니다.", "cutline"),
        ("전체 그림을 잡으세요.", "big_picture"),
        ("전체 그림을 잡으십시오.", "big_picture"),
    ],
)
def test_register_inflected_and_spaced_variants_are_blocked(text, expected_rule):
    hits = ct.register_lint(text)
    assert expected_rule in {hit["rule"] for hit in hits if hit["severity"] == "hard"}


def test_register_replacements_remain_allowed():
    text = "필요한 내용을 알아보고 지원 기준을 살피며 전체 흐름을 정합니다."
    assert ct.register_lint(text) == []


@pytest.mark.parametrize(
    "text",
    [
        "시험 일정과 마감일은 반드시 확인하세요.",
        "영어 점수 요건과 응시 자격은 이 기준을 따라야 합니다.",
        "직업 지원에는 나이 조건과 비용 규정이 있습니다.",
        "원서 접수 절차와 제출 서류를 먼저 준비하세요.",
        "자격증 발급 신청에는 행정 절차가 필요합니다.",
    ],
)
def test_external_domain_advice_blocks_fact_and_procedure_pairs(text):
    hits = dq.external_domain_advice_lint(text)
    assert hits
    assert all(hit["rule"] == "external_domain_advice" for hit in hits)
    assert text not in str(hits)  # 고객 문장 원문은 finding에 싣지 않는다.


@pytest.mark.parametrize(
    "text",
    [
        "시험이 걱정된다는 질문으로 이해했습니다.",
        "직업에서는 속도를 늦추고 방향과 우선순위를 조율하세요.",
        "시험은 2027년 세운을 바탕으로 준비 속도를 조절하세요.",
        "2027년 대운과 2028년 세운의 완급을 함께 봅니다.",
        "영어 공부가 걱정된다면 사람과 역할의 균형부터 살핍니다.",
        "행정이 걱정된다는 질문으로 이해했습니다.",
        "신청해 주신 고민은 직업 영역으로 이해했습니다.",
        "시험 일정이 걱정된다는 질문으로 이해했습니다.",
        "시험 응시 자격이 걱정된다는 질문이 마음에 남으셨을 거예요.",
        "직업 자격 요건이 걱정된다고 적어 주셨습니다.",
        "직업에서 중요한 조건은 역할과 사람의 균형입니다.",
        "직업에서 나이는 경험의 폭을 보여주는 생활 맥락입니다.",
        "직업\n관계에서는 나이 차이를 천천히 살핍니다.",
    ],
)
def test_external_domain_advice_allows_topic_and_saju_grounded_action(text):
    assert dq.external_domain_advice_lint(text) == []


def test_external_domain_advice_is_independent_delivery_failure_reason():
    result = dq.analyze("시험 일정과 영어 점수 요건을 확인하세요.")
    assert result["clean"] is False
    assert result["external_domain_advice_hits"]
    assert "external_domain_advice" in {failure["rule"] for failure in result["failures"]}


def test_question_mirror_exception_does_not_hide_trailing_advice():
    text = (
        "시험 일정이 걱정된다는 질문으로 이해했으니 "
        "공식 일정은 확인해 두는 편이 좋습니다."
    )
    assert dq.external_domain_advice_lint(text)


def _consult_text(core: str) -> str:
    return (core + " 사주 흐름의 근거를 차분히 설명합니다. ") * 12


def test_consult_first_and_check_alone_no_longer_satisfy_action():
    text = _consult_text("결론은 직업을 올해 살펴보는 것입니다. 먼저 확인합니다.")
    result = dq.consult_direct_result(text, "직업 시험은 언제 어떻게 준비할까요?")
    assert result["ok"] is False
    assert "action" in result["missing"]


def test_consult_generic_speech_does_not_satisfy_action():
    text = _consult_text("결론을 말씀드리면 올해 직업을 살펴봅니다.")
    result = dq.consult_direct_result(text, "직업 시험은 언제 어떻게 준비할까요?")
    assert result["ok"] is False
    assert "action" in result["missing"]


def test_consult_saju_action_terms_satisfy_action():
    text = _consult_text("결론은 직업을 올해 살펴보되 완급과 방향, 우선순위를 조율하는 것입니다.")
    result = dq.consult_direct_result(text, "직업 시험은 언제 어떻게 준비할까요?")
    assert result["ok"] is True, result


def test_work_career_axis_requires_topic_evidence_beyond_timing_and_action():
    bad = _consult_text("결론은 올해 속도와 방향을 조율하는 것입니다.")
    bad_result = dq.consult_direct_result(bad, "직업과 시험이 궁금합니다.")
    assert bad_result["ok"] is False
    assert "work_career" in bad_result["missing_topic_axes"]

    good = _consult_text("결론은 직업의 역할을 올해 살피며 속도와 방향을 조율하는 것입니다.")
    good_result = dq.consult_direct_result(good, "직업과 시험이 궁금합니다.")
    assert good_result["ok"] is True, good_result
    assert "work_career" in good_result["required_topic_axes"]


def test_work_career_axis_rejects_generic_task_word():
    text = _consult_text("결론은 올해 해야 할 일을 정하고 관계 방향과 속도를 조율하는 것입니다.")
    result = dq.consult_direct_result(text, "직업과 시험이 궁금합니다.")
    assert result["ok"] is False
    assert "work_career" in result["missing_topic_axes"]


def test_work_career_axis_rejects_relationship_role_without_career_evidence():
    text = _consult_text("결론은 올해 관계에서 역할과 속도, 방향을 조율하는 것입니다.")
    result = dq.consult_direct_result(text, "직업과 시험이 궁금합니다.")
    assert result["ok"] is False
    assert "work_career" in result["missing_topic_axes"]


def test_timing_requires_real_calendar_month_not_month_substring():
    bad = _consult_text("결론은 직업에서 월급과 역할, 방향을 조율하는 것입니다.")
    bad_result = dq.consult_direct_result(bad, "직업과 시험은 언제가 좋을까요?")
    assert bad_result["ok"] is False
    assert "timing" in bad_result["missing"]

    good = _consult_text("결론은 직업 방향을 7월에 맞추고 속도와 우선순위를 조율합니다.")
    good_result = dq.consult_direct_result(good, "직업과 시험은 언제가 좋을까요?")
    assert good_result["ok"] is True, good_result


def test_external_advice_pdf_block_joins_visual_wrap_without_crossing_blocks():
    wrapped = dq.analyze(
        "시험은 공식 일정과 마감을 확인하세요.",
        external_advice_segments=[(2, 3, "시험은 공식\n일정과 마감을\n확인하세요.")],
    )
    assert wrapped["external_domain_advice_hits"]
    assert wrapped["external_domain_advice_hits"][0]["page"] == 2
    assert wrapped["external_domain_advice_hits"][0]["block"] == 3

    separated = dq.analyze(
        "직업 관계에서는 나이 차이를 천천히 살핍니다.",
        external_advice_segments=[
            (1, 1, "직업"),
            (1, 2, "관계에서는 나이 차이를 천천히 살핍니다."),
        ],
    )
    assert separated["external_domain_advice_hits"] == []


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
    "이 사람은 생활의 속도를 고르게 맞추고, 말과 행동의 방향을 차분히 조율합니다. "
    "사주 흐름은 사람과 역할의 균형을 살피는 기준이 됩니다. "
)


@pytest.mark.parametrize(
    ("page_index", "injection", "expected_token"),
    [
        (0, "결과지", "결과지"),  # cover
        (1, "구간", "구간"),  # toc
        (2, "큰 그림", "큰 그림"),  # body
        (3, "참고", "참고"),  # appendix
    ],
)
def test_register_hard_hit_on_every_customer_visible_region_fails_gate(
    monkeypatch, page_index, injection, expected_token
):
    pages = ["표지", "차례 " + (_CLEAN * 2), _CLEAN * 18, "본문에 나온 용어 풀이 " + (_CLEAN * 4)]
    pages[page_index] += " " + injection
    monkeypatch.setattr(verify_pdf.fitz, "open", lambda _path: _FakeDoc(pages))
    monkeypatch.setattr(
        verify_pdf,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )

    result = verify_pdf.verify("synthetic.pdf")

    assert result["client_register_clean"] is False
    assert result["gate_pass"] is False
    assert any(
        hit["page"] == page_index + 1
        and hit["token"] == expected_token
        and hit["severity"] == "hard"
        for hit in result["register_hits"]
    )
    assert all(set(hit) == {"rule", "token", "count", "page", "severity"} for hit in result["register_hits"])


def test_register_warning_is_observed_without_failing_register_gate(monkeypatch):
    pages = ["표지", (_CLEAN * 18) + " 자료를 검토하고 전략을 점검합니다.", "맺음"]
    monkeypatch.setattr(verify_pdf.fitz, "open", lambda _path: _FakeDoc(pages))
    monkeypatch.setattr(
        verify_pdf,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )

    result = verify_pdf.verify("synthetic.pdf")

    assert result["client_register_clean"] is True
    assert result["register_warning_hits_count"] >= 1
    assert all(hit["severity"] == "warning" for hit in result["register_hits"])


def test_external_domain_advice_reaches_final_delivery_gate(monkeypatch):
    bad_advice = "시험 일정과 영어 점수 요건을 확인한 뒤 원서 접수 절차를 따르세요. "
    pages = ["표지", (_CLEAN * 18) + bad_advice, "맺음"]
    monkeypatch.setattr(verify_pdf.fitz, "open", lambda _path: _FakeDoc(pages))
    monkeypatch.setattr(
        verify_pdf,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )

    result = verify_pdf.verify("synthetic.pdf")
    failures = {failure["rule"] for failure in result["delivery_quality"]["failures"]}

    assert result["delivery_quality_clean"] is False
    assert result["delivery_external_domain_advice_hits_count"] == 1
    assert "external_domain_advice" in failures
    assert result["gate_pass"] is False


@pytest.mark.parametrize("bad_candidate", ["결과지입니다.", "시험 일정과 마감일을 확인하세요."])
def test_builder_rejects_policy_candidate_then_accepts_clean_retry(monkeypatch, bad_candidate):
    """개인 builder의 최초 후보·재작성 양쪽 배선을 경로 수준으로 고정한다."""

    calls = 0

    class _Backend:
        name = "anthropic"

        def classify(self, _concern):
            raise AssertionError("concern 없는 합성 테스트에서는 classify를 부르면 안 됩니다")

        def compose(self, *, base_text, section_id, **_kwargs):
            nonlocal calls
            assert section_id == "nature"
            calls += 1
            if calls == 1:
                text = base_text + "\n" + bad_candidate
            else:
                text = base_text + "\n생활의 속도와 방향을 차분히 조율합니다."
            return llm_sections.ComposeResult(
                text,
                cache_observed=True,
                api_succeeded=True,
            )

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _Backend())
    monkeypatch.setattr(builder, "_COMPOSE_SECTIONS", {"nature"})
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-07-12")

    report = builder.build_report(saju, use_llm=True, ref_year=2026, name="합성인")

    assert calls == 2
    assert report.section("nature").polished is True
    assert bad_candidate not in report.section("nature").final_text
    assert "nature" not in report.guard.fallback_section_ids


def test_builder_falls_back_when_policy_violation_persists(monkeypatch):
    """재작성도 hard register를 내면 승인된 결정론 골격으로 닫힌다."""

    calls = 0

    class _Backend:
        name = "anthropic"

        def classify(self, _concern):
            raise AssertionError("classify 호출 금지")

        def compose(self, *, base_text, section_id, **_kwargs):
            nonlocal calls
            calls += 1
            return llm_sections.ComposeResult(
                base_text + "\n결과지입니다.",
                cache_observed=True,
                api_succeeded=True,
            )

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _Backend())
    monkeypatch.setattr(builder, "_COMPOSE_SECTIONS", {"nature"})
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-07-12")

    report = builder.build_report(saju, use_llm=True, ref_year=2026, name="합성인")

    assert calls == 2
    assert report.section("nature").polished is False
    assert "결과지" not in report.section("nature").final_text
    assert "nature" in report.guard.fallback_section_ids


@pytest.mark.parametrize(
    "injection",
    ("결과지입니다.", "시험 일정과 영어 점수 요건을 확인하세요."),
)
def test_builder_rule_skeleton_policy_violation_marks_aggregate_unclean(
    monkeypatch, injection
):
    """룰 골격 위반도 최종 PDF 이전 aggregate guard에서 false-PASS하지 않는다."""

    original_build_all = rules.build_all

    def injected_build_all(*args, **kwargs):
        skeletons = original_build_all(*args, **kwargs)
        skeletons["nature"] += "\n" + injection
        return skeletons

    monkeypatch.setattr(rules, "build_all", injected_build_all)
    saju = engine.build(2000, 1, 2, 7, 40, is_male=False, horoscope_date="2026-07-12")

    report = builder.build_report(saju, use_llm=False, ref_year=2026, name="DOC_A")

    assert report.guard.customer_policy_lint_total >= 1
    assert report.guard.clean is False
    assert report.section("nature").guard_violations


@pytest.mark.parametrize("bad_candidate", ["큰 그림을 잡습니다.", "시험 일정과 마감일을 확인하세요."])
def test_gunghap_compose_rejects_customer_policy_candidate(monkeypatch, bad_candidate):
    """궁합 LLM 후보도 공통 고객 정책을 지우면 깨지는 회귀를 잡는다."""

    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *_args, **_kwargs):
            return types.SimpleNamespace(content=[types.SimpleNamespace(text=bad_candidate)])

    class _Anthropic:
        def __init__(self, *_args, **_kwargs):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-test-key")
    monkeypatch.setitem(sys.modules, "anthropic", fake)

    result = gunghap._compose(
        "each",
        "두 사람은 속도와 방향을 차분히 맞춥니다.",
        {"ganzhi": [], "ganzhi_ko": []},
        "",
        ["합성갑", "합성을"],
        2026,
        use_llm=True,
    )

    assert result == "두 사람은 속도와 방향을 차분히 맞춥니다."
    assert bad_candidate not in result


@pytest.mark.parametrize(
    ("consumer", "bad_text", "expected_rule"),
    [
        ("relationship", "이 결과지는 두 사람의 방향을 말합니다.", "result_sheet"),
        ("relationship", "시험 일정과 마감일을 확인하세요.", "external_domain_advice"),
        ("followup", "큰 그림을 잡습니다.", "big_picture"),
        ("followup", "원서 접수 절차를 따르세요.", "external_domain_advice"),
    ],
)
def test_relationship_and_followup_consumers_reject_policy_defects(
    consumer, bad_text, expected_rule
):
    """관계 최종 섹션과 후속 답변의 독립 소비자 배선을 고정한다."""

    if consumer == "relationship":
        result = relationship_delivery_gate.check(final_section_text=bad_text, names=[])
        assert result.ok is False
        rules = {failure["rule"] for failure in result.failures}
    else:
        result = answer_gate.check(
            bad_text,
            concern=None,
            allow_tokens={},
            ref_year=2026,
            ref_date="2026-07-12",
        )
        assert result["ok"] is False
        rules = {failure["rule"] for failure in result["failures"]}

    assert expected_rule in rules
