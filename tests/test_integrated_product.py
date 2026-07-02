# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hsemantic_review  # noqa: E402
from sajugen import integrated  # noqa: E402
from sajugen.content import client_tone_lint, delivery_quality, quality_lint, style_lint  # noqa: E402
from sajugen.render import verify as render_verify  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "synthetic_integrated"


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


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _expanded_pages(data: dict, *, body_pages: int = 31) -> list[str]:
    page = " ".join([data["body"]] * 3)
    return ["표지"] + [page for _ in range(body_pages)] + ["글을 맺으며"]


def _verify_fixture(monkeypatch, name: str) -> dict:
    data = _load(name)
    specs = client_tone_lint.role_perspective_specs(data["people"], receiver=data["receiver"])
    monkeypatch.setattr(render_verify.fitz, "open", lambda _path: _FakeDoc(_expanded_pages(data)))
    monkeypatch.setattr(
        render_verify,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )
    return render_verify.verify(
        "synthetic-integrated.pdf",
        ref_year=2026,
        names=data["people"],
        product="integrated_full",
        premium=True,
        # context_required 상품(integrated_full)이므로 고객 질문이 있어야 통과 — 트리거 없는
        # 합성 맥락으로 context 만 충족(질문축 커버 검사는 비활성, P1 회귀 보존).
        concern="합성 상담 맥락 참고",
        role_perspective=specs,
        honorific=specs,
    )


def _patch_integrated_sources(monkeypatch):
    captured = {}
    monkeypatch.setattr(integrated.engine, "build", lambda *a, **k: SimpleNamespace(ref_year=2026))

    def fake_personal_report(*args, **kwargs):
        captured["personal_product"] = kwargs["product"]
        return SimpleNamespace(
            sections=[
                SimpleNamespace(id="cover", title="표지", source_keys=[], final_text=""),
                SimpleNamespace(
                    id="nature",
                    title="개인 합성",
                    source_keys=["m"],
                    final_text="DOC_A 님 개인 문안",
                ),
                SimpleNamespace(
                    id="closing", title="마무리", source_keys=["m"], final_text="마무리"
                ),
                SimpleNamespace(
                    id="colophon", title="글을 맺으며", source_keys=[], final_text="끝"
                ),
            ]
        )

    def fake_gunghap(*args, **kwargs):
        captured["gunghap"] = kwargs
        return {
            "people": [
                {"name": "DOC_A", "saju": None, "m": None},
                {"name": "DOC_B", "saju": None, "m": None},
            ],
            "sections": [
                SimpleNamespace(
                    id="overview",
                    title="관계 합성",
                    source_keys=["gunghap"],
                    final_text="DOC_A 님과 DOC_B 씨 관계 문안",
                )
            ],
        }

    monkeypatch.setattr(integrated.builder, "build_report", fake_personal_report)
    monkeypatch.setattr(integrated.gunghap, "build_gunghap", fake_gunghap)
    monkeypatch.setattr(
        integrated.gunghap,
        "_identity_spec",
        lambda people: (set(), set(), []),
    )
    monkeypatch.setattr(integrated.gunghap, "_singang_specs", lambda people: [])
    return captured


def _people():
    return [
        ("DOC_A", (1990, 1, 1, 10, 0), True),
        ("DOC_B", (1991, 2, 2, 11, 0), False),
    ]


def _verify_result(*, gate_pass: bool, failures: list[dict]) -> dict:
    return {
        "gate_pass": gate_pass,
        "text_layer_ok": True,
        "fonts_embedded": True,
        "tagged": True,
        "markdown_clean": True,
        "daewoon_consistent": True,
        "quality_clean": True,
        "temporal_clean": True,
        "no_orphan": True,
        "loanword_clean": True,
        "raw_calc_head_clean": True,
        "customer_meta_clean": True,
        "placeholder_residue_clean": True,
        "style_clean": True,
        "role_perspective_clean": True,
        "honorific_consistency_clean": True,
        "name_policy_clean": True,
        "identity_role_clean": True,
        "singang_role_clean": True,
        "delivery_quality_clean": gate_pass,
        "delivery_quality": {"failures": failures},
    }


def test_integrated_full_delivery_page_floor_is_30():
    assert delivery_quality._min_pages("integrated") == delivery_quality.MIN_PREMIUM_PAGES
    assert delivery_quality._min_pages("integrated_full") == 30
    result = delivery_quality.analyze(
        "자미두수로 집과 일, 사람과 관계, 돈과 재물을 함께 봅니다. " * 220,
        pages=29,
        product="integrated_full",
        premium=False,
    )
    assert result["premium"] is True
    assert any(f["rule"] == "premium_pages" and f["minimum"] == 30 for f in result["failures"])


def test_role_and_honorific_lints_are_pii_free():
    specs = client_tone_lint.role_perspective_specs(["DOC_A", "DOC_B"], receiver="DOC_A")
    clean = "DOC_A 님은 차분히 확인하고 DOC_B 씨는 속도를 맞춥니다."
    residue = "DOC_A 님은 확인합니다. DOC_A 씨는 다시 설명합니다. DOC_B 님도 남아 있습니다."

    assert client_tone_lint.role_perspective_lint(clean, specs) == []
    assert client_tone_lint.honorific_consistency_lint(clean, specs) == []
    role_hits = client_tone_lint.role_perspective_lint(residue, specs)
    honor_hits = client_tone_lint.honorific_consistency_lint(residue, specs)
    assert role_hits
    assert honor_hits
    assert "DOC_A" not in str(role_hits)
    assert "DOC_B" not in str(honor_hits)


def test_integrated_full_clean_fixture_passes_gate(monkeypatch):
    result = _verify_fixture(monkeypatch, "clean.json")
    assert result["gate_pass"] is True, result
    assert result["role_perspective_clean"] is True
    assert result["honorific_consistency_clean"] is True
    review = hsemantic_review.review_verify_result(result)
    assert review["semantic_review_status"] == "REVIEW_REQUIRED"
    assert review["release_allowed"] is False
    assert "READY" not in str(review)
    assert "APPROVED" not in str(review)


def test_integrated_full_residue_fixture_fails_gate(monkeypatch):
    result = _verify_fixture(monkeypatch, "residue.json")
    assert result["gate_pass"] is False
    assert result["placeholder_residue_clean"] is False
    assert result["role_perspective_clean"] is False
    assert result["honorific_consistency_clean"] is False
    assert result["placeholder_residue_hits"]
    assert result["role_perspective_hits"]
    assert result["honorific_consistency_hits"]
    review = hsemantic_review.review_verify_result(result)
    assert review["semantic_review_status"] == "FAILED"
    assert review["release_allowed"] is False
    assert "READY" not in str(review)
    assert "APPROVED" not in str(review)


def _verify_integrated(monkeypatch, name: str, **verify_kwargs) -> dict:
    data = _load(name)
    monkeypatch.setattr(render_verify.fitz, "open", lambda _p: _FakeDoc(_expanded_pages(data)))
    monkeypatch.setattr(
        render_verify, "_verapdf_ua1", lambda _p: {"available": False, "note": "test"}
    )
    return render_verify.verify(
        "synthetic-integrated.pdf",
        ref_year=2026,
        names=data["people"],
        product="integrated_full",
        premium=True,
        **verify_kwargs,
    )


def test_integrated_full_without_concern_fails_missing_customer_context(monkeypatch):
    # P1: integrated_full 인데 concern 미전달이면 조용히 통과하지 말고 실패로 드러나야 함.
    r = _verify_integrated(monkeypatch, "clean.json")  # concern 없음
    assert r["delivery_quality_clean"] is False
    assert "missing_customer_context" in {f["rule"] for f in r["delivery_quality"]["failures"]}
    assert r["delivery_quality"]["has_customer_context"] is False
    assert r["gate_pass"] is False


def test_integrated_full_with_concern_populates_axes_and_stores_fields(monkeypatch):
    # P1: concern 이 delivery_quality 까지 도달하면 질문축이 산출되고 summary 필드가 저장됨.
    concern = "도와주는 사람과 시기가 궁금하고 어떻게 준비할지 알고 싶습니다"
    r = _verify_integrated(monkeypatch, "clean.json", concern=concern)
    dq = r["delivery_quality"]
    assert dq["has_customer_context"] is True
    assert dq["required_axes"] != []
    assert "missing_customer_context" not in {f["rule"] for f in dq["failures"]}
    # 저장 회귀: 원인 추적용 필드가 delivery_quality 에 남는다(null 아님).
    for key in (
        "required_axes",
        "has_customer_context",
        "missing_axes",
        "frontloaded_answer",
        "near_term_timing",
        "love_action",
        "ziwei",
    ):
        assert key in dq, key
    assert dq["frontloaded_answer"].get("ok") is not None
    assert dq["ziwei"].get("ok") is not None


def test_integrated_full_assembler_uses_native_sections_without_render(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    captured = _patch_integrated_sources(monkeypatch)

    result = integrated.build_integrated_full(
        _people(),
        receiver_name="DOC_A",
        situation="synthetic context",
        render=False,
    )

    assert result["product"] == "integrated_full"
    assert captured["personal_product"] == "integrated_full"
    assert captured["gunghap"]["render"] is False
    assert captured["gunghap"]["receiver_perspective"] is True
    assert captured["gunghap"]["product"] == "integrated_full"
    assert [s.id for s in result["sections"]] == [
        "personal_nature",
        "integrated_full_depth",
        "relationship_overview",
    ]
    assert "마무리" in result["sections"][-1].final_text
    assert "글을 맺으며" in result["sections"][-1].final_text


def test_integrated_full_receiver_perspective_unmasks_llm_placeholders(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_personal_report(*args, **kwargs):
        return SimpleNamespace(
            sections=[
                SimpleNamespace(id="cover", title="표지", source_keys=[], final_text=""),
                SimpleNamespace(
                    id="nature",
                    title="개인 합성",
                    source_keys=["m"],
                    final_text="성갑 님은 생활 기준을 차분히 확인합니다.",
                ),
            ]
        )

    def fake_compose(*args, **kwargs):
        return (
            "첫 번째 분은 대화를 먼저 확인하고, 두 번째 분은 약속의 속도를 맞춥니다. "
            "상대 분도 필요한 내용을 짧게 설명하면 관계가 안정됩니다."
        )

    monkeypatch.setattr(integrated.builder, "build_report", fake_personal_report)
    monkeypatch.setattr(integrated.gunghap, "_compose", fake_compose)

    result = integrated.build_integrated_full(
        [
            ("합성갑", (1990, 1, 1, 10, 0), True),
            ("합성을", (1991, 2, 2, 11, 0), False),
        ],
        receiver_name="합성갑",
        situation="",
        render=False,
        use_llm=True,
    )
    text = "\n\n".join(s.final_text for s in result["sections"])

    assert "첫 번째 분" not in text
    assert "두 번째 분" not in text
    assert "상대 분" not in text
    assert "성갑 님" in text
    assert "성을 씨" in text
    hard_placeholder_hits = [
        h for h in client_tone_lint.placeholder_residue_lint(text) if h.get("severity") == "hard"
    ]
    assert hard_placeholder_hits == []
    assert client_tone_lint.role_perspective_lint(text, result["role_perspective"]) == []
    assert client_tone_lint.honorific_consistency_lint(text, result["honorific"]) == []


def test_integrated_full_style_safety_normalizes_known_triggers():
    raw = "새 흐름이 또렷이 보이고, 시간의 결을 따라 걷고 있습니다."
    text = integrated._integrated_style_safe_text(raw)
    assert style_lint.is_clean(text), style_lint.lint(text)
    assert "또렷" not in text
    assert "결을 따라 걷" not in text
    assert "시간의 흐름을 차분히 살피고 있습니다." in text


def test_integrated_full_style_safety_preserves_normal_words():
    text = integrated._integrated_style_safe_text(
        "선택의 결과를 봅니다. 오늘의 결정은 중요합니다. 처음의 결론입니다."
    )
    assert style_lint.is_clean(text), style_lint.lint(text)
    assert "선택의 결과를 봅니다." in text
    assert "오늘의 결정은 중요합니다." in text
    assert "처음의 결론입니다." in text


def test_integrated_full_quality_safety_normalizes_internal_ziwei_label():
    text = integrated._integrated_style_safe_text(
        "명궁은 명궁, 신궁은 명궁에 놓입니다. 다음 문장입니다."
    )
    assert "명궁은 명궁" not in text
    assert quality_lint.lint(text) == []


def test_integrated_full_sparse_relationship_sections_merge_within_group():
    sections = [
        SimpleNamespace(
            id="personal_nature",
            title="개인 합성",
            source_keys=["m"],
            final_text="개인 문안 " * 120,
        ),
        SimpleNamespace(
            id="relationship_overview",
            title="관계 개요",
            source_keys=["gunghap"],
            final_text="관계 문안",
        ),
        SimpleNamespace(
            id="relationship_timing",
            title="관계 시기",
            source_keys=["gunghap"],
            final_text="시기 문안",
        ),
    ]

    compacted = integrated._compact_sparse_sections(sections)

    assert [s.id for s in compacted] == ["personal_nature", "relationship_overview"]
    assert "관계 시기" in compacted[-1].final_text
    assert "시기 문안" in compacted[-1].final_text
    assert compacted[-1].source_keys == ["gunghap"]


def test_integrated_full_no_llm_depth_section_supports_page_floor(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_integrated_sources(monkeypatch)

    result = integrated.build_integrated_full(
        _people(),
        receiver_name="DOC_A",
        situation="synthetic context",
        render=False,
        use_llm=False,
    )
    depth = next(s for s in result["sections"] if s.id == "integrated_full_depth")

    assert len(depth.final_text) >= 5000
    assert style_lint.is_clean(depth.final_text), style_lint.lint(depth.final_text)
    assert "고객님" not in depth.final_text
    assert "당신" not in depth.final_text
    assert "신청자" not in depth.final_text
    assert "상담 대상" not in depth.final_text


def test_integrated_full_no_render_synthetic_body_quality_clean(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = integrated.build_integrated_full(
        [
            ("합성갑", (1990, 1, 1, 10, 0), True),
            ("합성을", (1991, 2, 2, 11, 0), False),
        ],
        receiver_name="합성갑",
        situation="",
        render=False,
        use_llm=False,
    )
    text = "\n\n".join(s.final_text for s in result["sections"])

    assert quality_lint.lint(text) == []
    assert style_lint.lint(text) == []


def test_integrated_full_low_density_only_requires_clean_integrated_flags():
    low_density = [{"rule": "premium_low_density_pages"}]
    clean = _verify_result(gate_pass=False, failures=low_density)
    assert integrated._integrated_only_low_density_failure(clean) is True

    style_failure = _verify_result(gate_pass=False, failures=low_density)
    style_failure["style_clean"] = False
    assert integrated._integrated_only_low_density_failure(style_failure) is False

    meta_failure = _verify_result(gate_pass=False, failures=low_density)
    meta_failure["customer_meta_clean"] = False
    assert integrated._integrated_only_low_density_failure(meta_failure) is False

    placeholder_failure = _verify_result(gate_pass=False, failures=low_density)
    placeholder_failure["placeholder_residue_clean"] = False
    assert integrated._integrated_only_low_density_failure(placeholder_failure) is False

    other_delivery_failure = _verify_result(
        gate_pass=False,
        failures=[{"rule": "premium_low_density_pages"}, {"rule": "missing_question_axes"}],
    )
    assert integrated._integrated_only_low_density_failure(other_delivery_failure) is False


def test_integrated_full_low_density_only_retries_layout_then_passes(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_integrated_sources(monkeypatch)
    render_calls = []
    verify_results = [
        _verify_result(gate_pass=False, failures=[{"rule": "premium_low_density_pages"}]),
        _verify_result(gate_pass=True, failures=[]),
    ]

    def fake_render_pdf(*args, **kwargs):
        render_calls.append(kwargs)
        return f"synthetic-{len(render_calls)}.pdf"

    def fake_verify(*args, **kwargs):
        return verify_results.pop(0)

    monkeypatch.setattr(integrated.render_pdf, "render_pdf", fake_render_pdf)
    monkeypatch.setattr(integrated.render_verify, "verify", fake_verify)

    result = integrated.build_integrated_full(
        _people(),
        receiver_name="DOC_A",
        situation="synthetic context",
        render=True,
        out_dir="synthetic-tmp",
    )

    assert result["pdf_path"] == "synthetic-2.pdf"
    assert len(render_calls) == 2
    assert render_calls[0]["body_font_size"] == "14.5pt"
    assert render_calls[1]["body_font_size"] != render_calls[0]["body_font_size"]
    assert all(call["chapter_breaks"] is False for call in render_calls)
    assert all(call["out_dir"] == "synthetic-tmp" for call in render_calls)
    assert result["layout_attempts"] == [
        {
            "body_font_size": "14.5pt",
            "body_line_height": "1.8",
            "gate_pass": False,
            "low_density_only": True,
        },
        {
            "body_font_size": "13.8pt",
            "body_line_height": "1.68",
            "gate_pass": True,
            "low_density_only": False,
        },
    ]


def test_integrated_full_style_failure_does_not_retry_as_low_density(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_integrated_sources(monkeypatch)
    render_calls = []
    verify_result = _verify_result(
        gate_pass=False,
        failures=[{"rule": "premium_low_density_pages"}],
    )
    verify_result["style_clean"] = False

    monkeypatch.setattr(
        integrated.render_pdf,
        "render_pdf",
        lambda *args, **kwargs: render_calls.append(kwargs) or "synthetic-1.pdf",
    )
    monkeypatch.setattr(
        integrated.render_verify,
        "verify",
        lambda *args, **kwargs: verify_result,
    )

    try:
        integrated.build_integrated_full(
            _people(),
            receiver_name="DOC_A",
            situation="synthetic context",
            render=True,
            out_dir="synthetic-tmp",
        )
    except RuntimeError as exc:
        assert "integrated_full PDF 하드 게이트 실패" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    assert len(render_calls) == 1


def test_integrated_full_non_low_density_failure_does_not_retry(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_integrated_sources(monkeypatch)
    render_calls = []

    monkeypatch.setattr(
        integrated.render_pdf,
        "render_pdf",
        lambda *args, **kwargs: render_calls.append(kwargs) or "synthetic-1.pdf",
    )
    monkeypatch.setattr(
        integrated.render_verify,
        "verify",
        lambda *args, **kwargs: _verify_result(
            gate_pass=False, failures=[{"rule": "missing_question_axes"}]
        ),
    )

    try:
        integrated.build_integrated_full(
            _people(),
            receiver_name="DOC_A",
            situation="synthetic context",
            render=True,
            out_dir="synthetic-tmp",
        )
    except RuntimeError as exc:
        assert "integrated_full PDF 하드 게이트 실패" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    assert len(render_calls) == 1


def test_verify_stores_physical_frontloaded_field(monkeypatch):
    # P5: verify 가 물리 페이지 기준 초반 답변 보조지표를 delivery_quality 에 저장(보고 보존).
    concern = "도와주는 사람과 시기가 궁금하고 어떻게 준비할지 알고 싶습니다"
    r = _verify_integrated(monkeypatch, "clean.json", concern=concern)
    dq = r["delivery_quality"]
    assert "physical_frontloaded_answer" in dq
    pf = dq["physical_frontloaded_answer"]
    assert pf["required"] is True
    assert "first_pages" in pf and "answer_page" in pf
    # 게이트 미변경: 이 보조지표는 warning 경로이며 gate_pass 를 좌우하지 않는다.
    assert "physical_frontloaded_answer" not in {f["rule"] for f in dq["failures"]}


def test_toc_lead_has_no_transition_meta(monkeypatch):
    # P4: 목차 리드가 문서 진행/섹션 예고 메타("…다음 순서로 이어집니다")가 아니라 중립 헤딩이어야 함.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder, customer_meta_lint

    saju = engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(saju, use_llm=False)
    toc = next((s for s in rep.sections if s.id == "toc"), None)
    assert toc is not None, "toc section missing"
    assert "다음 순서로 이어집니다" not in toc.final_text
    assert customer_meta_lint.is_clean(toc.final_text), customer_meta_lint.lint(toc.final_text)
    assert "차례" in toc.final_text


def test_build_integrated_full_saves_reusable_content(monkeypatch, tmp_path):
    # compose 결과가 .content.json 으로 영속돼, 이후 재compose 없이 재렌더 가능해야 함(2026-07-02).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _patch_integrated_sources(monkeypatch)  # build_report/build_gunghap mock(=compose 대체)
    monkeypatch.setattr(integrated, "_render_integrated", lambda report, **k: ("x.pdf", {"gate_pass": True}, []))

    res = integrated.build_integrated_full(
        _people(), receiver_name="DOC_A", situation="합성 맥락",
        out_name="save_rt.pdf", out_dir=str(tmp_path), render=True,
    )
    cpath = Path(res["content_path"])
    assert cpath.is_file()
    data = json.loads(cpath.read_text(encoding="utf-8"))
    assert data["product"] == "integrated_full"
    assert data["names"] == ["DOC_A", "DOC_B"]
    assert [s["id"] for s in data["sections"]] == [s.id for s in res["sections"]]
    assert all(s.get("final_text") is not None for s in data["sections"])


def test_render_only_from_content_does_not_recompose(monkeypatch, tmp_path):
    # 재렌더는 저장 본문만 쓰고 build_report/build_gunghap(=compose)를 절대 다시 부르지 않는다(LLM/API 0).
    monkeypatch.setattr(
        integrated.builder, "build_report",
        lambda *a, **k: pytest.fail("re-render must NOT compose (build_report called)"),
    )
    monkeypatch.setattr(
        integrated.gunghap, "build_gunghap",
        lambda *a, **k: pytest.fail("re-render must NOT compose (build_gunghap called)"),
    )
    seen = {}
    monkeypatch.setattr(
        integrated, "_render_integrated",
        lambda report, **k: (
            seen.update(sections=[s.final_text for s in report.sections], names=k["names"],
                        identity=k["identity"], role=k["role_specs"])
            or ("relayout.pdf", {"gate_pass": True}, [])
        ),
    )
    content = {
        "product": "integrated_full", "receiver": "DOC_A", "names": ["DOC_A", "DOC_B"],
        "ref_year": 2026, "situation": "맥락", "brand": "sajudoryeong",
        "role_perspective": [{"given": "DOC_A"}], "identity": [["임"], ["임수"], []], "singang": [],
        "sections": [
            {"id": "nature", "title": "성향", "source_keys": ["m"], "final_text": "DOC_A 님 본문"},
            {"id": "overview", "title": "관계", "source_keys": ["gunghap"], "final_text": "관계 본문"},
        ],
    }
    p = tmp_path / "rt.content.json"
    p.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")

    res = integrated.render_integrated_from_content(str(p), out_name="relayout.pdf", out_dir=str(tmp_path))
    assert res["pdf_path"] == "relayout.pdf"
    assert seen["sections"] == ["DOC_A 님 본문", "관계 본문"]  # 저장 본문 그대로 재렌더로 흐름
    assert seen["names"] == ["DOC_A", "DOC_B"]
    assert seen["identity"] == (["임"], ["임수"], [])  # 저장 스펙 복원
    assert seen["role"] == [{"given": "DOC_A"}]
