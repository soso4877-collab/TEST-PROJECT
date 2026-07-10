# -*- coding: utf-8 -*-
"""Q7 모듈 레지스트리·조립·게이트와 CLI 배선의 양방 계약.

실 PDF나 LLM을 만들지 않고 합성 섹션으로 조립 경계를 검증한다. 특히 v3의 핵심인
"필터링 → 병합 전 커버리지 기록 → 현행 sparse 병합" 순서를 결과 메타로 고정한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from sajugen import integrated
from sajugen import modules as integrated_modules
from sajugen.calc import engine
from sajugen.content import delivery_quality, rules


def _section(section_id: str, text: str) -> SimpleNamespace:
    """조립 테스트가 본문 생성 세부와 결합되지 않게 만드는 최소 합성 섹션."""

    return SimpleNamespace(
        id=section_id,
        title=f"{section_id} 합성 제목",
        source_keys=[section_id],
        final_text=text,
    )


def _people(count: int = 2) -> list[tuple]:
    people = [
        ("DOC_A", (1990, 1, 1, 10, 0), True),
        ("DOC_B", (1991, 2, 2, 11, 0), False),
    ]
    return people[:count]


def _cli_person_args(count: int = 2) -> list[str]:
    """PII 없는 합성 인원을 반복 ``--person`` 인자 형태로 펼친다."""

    people = (
        "DOC_A,1990-01-01,10:00,남",
        "DOC_B,1991-02-02,11:00,여",
    )
    return [part for person in people[:count] for part in ("--person", person)]


def _patch_cli_build_without_render(monkeypatch) -> list[dict]:
    """CLI kwargs를 관측하면서 실제 레지스트리 검증을 타고 렌더만 끈다."""

    original_build = integrated.build_integrated_full
    calls: list[dict] = []

    def fake_build(people, **kwargs):
        call = {"people": people, "kwargs": dict(kwargs)}
        calls.append(call)
        result = original_build(people, **{**kwargs, "render": False})
        result["pdf_path"] = "fake.pdf"
        call["result_modules"] = result["modules"]
        return result

    monkeypatch.setattr(integrated, "build_integrated_full", fake_build)
    return calls


def _patch_sources(monkeypatch) -> dict:
    """계산·LLM·렌더 없이 모듈별 제공자와 관계 호출 여부만 관측한다."""

    captured: dict[str, object] = {
        "personal_calls": [],
        "included_section_calls": [],
        "gunghap_calls": 0,
    }
    fake_saju = SimpleNamespace(
        ref_year=2026,
        myeongni=SimpleNamespace(day_master="甲", singang="신강"),
    )
    monkeypatch.setattr(integrated.engine, "build", lambda *args, **kwargs: fake_saju)

    def fake_personal_report(*args, **kwargs):
        work_modules = tuple(kwargs["work_modules"])
        captured["personal_calls"].append(work_modules)
        captured["included_section_calls"].append(frozenset(kwargs["include_section_ids"]))
        work_parts = {
            "job": "직업 제공자 문단",
            "wealth": "재물 제공자 문단",
        }
        work_text = "\n\n".join(work_parts[module_id] for module_id in work_modules)
        return SimpleNamespace(
            sections=[
                _section("cover", "표지"),
                _section("intro", "핵심 도입 문단"),
                _section("love", "연애 제공자 문단"),
                _section("work", work_text),
                _section("health", "건강 제공자 문단"),
                _section("consult", "질문 답변 문단"),
                _section("closing", "마무리 문단"),
                _section("colophon", "맺음 문단"),
            ]
        )

    def fake_gunghap(*args, **kwargs):
        captured["gunghap_calls"] += 1
        return {
            "people": [
                {"name": "DOC_A", "day_master": "甲", "singang": "신강"},
                {"name": "DOC_B", "day_master": "乙", "singang": "신약"},
            ],
            "sections": [_section("overview", "관계 제공자 문단")],
        }

    monkeypatch.setattr(integrated.builder, "build_report", fake_personal_report)
    monkeypatch.setattr(integrated.gunghap, "build_gunghap", fake_gunghap)
    monkeypatch.setattr(integrated.gunghap, "_identity_spec", lambda people: (set(), set(), []))
    monkeypatch.setattr(integrated.gunghap, "_singang_specs", lambda people: [])
    return captured


def _module_sections_for(selected_modules: list[str]) -> dict[str, list[str]]:
    """게이트 경계표에 쓰는 정상 병합 전 섹션 맵."""

    sections = integrated_modules.empty_module_sections()
    sections["core"] = ["personal_intro"]
    sections["tail"] = ["personal_consult"]
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


def _premerge_ids(module_sections: dict[str, list[str]]) -> list[str]:
    """구조화 맵의 ID를 실제 병합 전 목록 형태로 한 번씩 펼친다."""

    return list(
        dict.fromkeys(
            section_id for section_ids in module_sections.values() for section_id in section_ids
        )
    )


def _analyze_module_map(
    module_sections: dict[str, list[str]], premerge_section_ids: list[str]
) -> dict:
    """R9-1 합성 맵이 최종 delivery_quality failure까지 도달하는지 확인한다."""

    return delivery_quality.analyze(
        "자미두수와 명리 관점을 함께 살핍니다. " * 600,
        pages=16,
        product="integrated_full",
        selected_modules=["love"],
        module_sections=module_sections,
        premerge_section_ids=premerge_section_ids,
    )


def test_cli_gen_without_module_passes_none_and_preserves_legacy_call(monkeypatch):
    # 미지정은 빈 목록이 아니라 None이어야 기존 5모듈 기본값과 같은 단일 경로를 탄다.
    _patch_sources(monkeypatch)
    calls = _patch_cli_build_without_render(monkeypatch)

    result = CliRunner().invoke(integrated.app, ["gen", *_cli_person_args()])

    assert result.exit_code == 0, result.output
    assert calls[0]["kwargs"]["modules"] is None
    assert calls[0]["kwargs"]["render"] is True
    assert calls[0]["result_modules"] == list(integrated_modules.SELECTABLE_MODULES)
    assert "PDF: fake.pdf (2인)" in result.output
    assert "modules: love,job,wealth,health,gunghap (schema v1)" in result.output


def test_cli_gen_forwards_repeated_modules_and_prints_result_metadata(monkeypatch):
    # CLI는 반복값을 보정하지 않고 그대로 넘기며, 출력은 빌더가 정규화한 결과 메타만 쓴다.
    _patch_sources(monkeypatch)
    calls = _patch_cli_build_without_render(monkeypatch)

    result = CliRunner().invoke(
        integrated.app,
        [
            "gen",
            *_cli_person_args(),
            "--module",
            "love",
            "--module",
            "job",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["kwargs"]["modules"] == ["love", "job"]
    assert calls[0]["result_modules"] == ["love", "job"]
    assert "modules: love,job (schema v1)" in result.output


@pytest.mark.parametrize(
    ("module_args", "person_count", "cause"),
    [
        (["--module", "fake"], 2, "unknown"),
        (["--module", "love", "--module", "love"], 2, "duplicates"),
        (["--module", "gunghap"], 1, "at least two"),
    ],
)
def test_cli_gen_blocks_invalid_module_requests_without_pdf(
    monkeypatch, module_args, person_count, cause
):
    # 미등록·중복·관계 인원 부족은 빌더 원인을 보존한 exit 1이며 성공 라인을 남기지 않는다.
    calls = _patch_cli_build_without_render(monkeypatch)

    result = CliRunner().invoke(
        integrated.app,
        ["gen", *_cli_person_args(person_count), *module_args],
    )

    assert result.exit_code == 1
    assert cause in result.output.lower()
    assert "PDF:" not in result.output
    assert len(calls) == 1


def test_module_selection_normalizes_to_one_deterministic_order():
    # 입력 순서가 달라도 같은 집합은 같은 문서를 만들어야 한다. 잘못된 메타는 fail-closed다.
    assert integrated_modules.normalize_modules(None) == integrated_modules.SELECTABLE_MODULES
    assert integrated_modules.normalize_modules(
        ["gunghap", "health", "wealth", "job", "love"]
    ) == integrated_modules.SELECTABLE_MODULES
    with pytest.raises(ValueError, match="at least one"):
        integrated_modules.normalize_modules([])
    with pytest.raises(ValueError, match="unknown"):
        integrated_modules.normalize_modules(["unknown"])
    with pytest.raises(ValueError, match="duplicates"):
        integrated_modules.normalize_modules(["love", "love"])


def test_rules_expose_job_and_wealth_providers_without_changing_full_work_bytes():
    # 실제 결정론 룰에서 기본/명시 2제공자 문자열이 완전히 같고, 각 단독 제공자가 갈라지는지 본다.
    saju = engine.build(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
    )
    base = rules.build_all(saju, ref_year=2026, name="DOC_A")
    explicit = rules.build_all(
        saju, ref_year=2026, name="DOC_A", work_modules=["job", "wealth"]
    )
    job = rules.build_all(saju, ref_year=2026, name="DOC_A", work_modules=["job"])
    wealth = rules.build_all(saju, ref_year=2026, name="DOC_A", work_modules=["wealth"])

    assert base["work"] == explicit["work"]
    assert base["work"] == base["work_job"] + "\n\n" + base["work_wealth"]
    assert job["work"] == job["work_job"]
    assert wealth["work"] == wealth["work_wealth"]
    assert job["work"] != wealth["work"]


def test_default_and_explicit_five_modules_are_byte_identical(monkeypatch):
    # None과 명시적 5모듈은 같은 단일 레짐을 타며 섹션 ID·본문이 완전히 같아야 한다.
    _patch_sources(monkeypatch)
    legacy = integrated.build_integrated_full(
        _people(), receiver_name="DOC_A", situation="합성 맥락", render=False
    )
    explicit = integrated.build_integrated_full(
        _people(),
        receiver_name="DOC_A",
        situation="합성 맥락",
        modules=list(integrated_modules.SELECTABLE_MODULES),
        render=False,
    )

    legacy_snapshot = [(section.id, section.final_text) for section in legacy["sections"]]
    explicit_snapshot = [(section.id, section.final_text) for section in explicit["sections"]]
    assert legacy_snapshot == explicit_snapshot
    assert [section.id for section in legacy["sections"]] == [
        "personal_intro",
        "integrated_full_depth",
        "relationship_overview",
    ]
    assert legacy["modules"] == list(integrated_modules.SELECTABLE_MODULES)


def test_five_module_assembly_matches_pre_q7_legacy_algorithm():
    # 새 조립기를 자기 자신과 비교하지 않고, Q7 이전 알고리즘을 독립 오라클로 재현해 바이트를 고정한다.
    personal = SimpleNamespace(
        sections=[
            _section("cover", "표지"),
            _section("intro", "도입 문단"),
            _section("love", "연애 문단"),
            _section("work", "직업 문단\n\n재물 문단"),
            _section("health", "건강 문단"),
            _section("consult", "질문 답변"),
            _section("closing", "마무리"),
            _section("appendix_terms", "용어 풀이"),
            _section("colophon", "맺음"),
        ]
    )
    relationship = [_section("overview", "관계 문단")]

    # 아래 블록은 HEAD 0b3134f의 기존 조립 순서·drop·tail 처리 그대로다. 새 레지스트리
    # 분기와 독립시켜 default 동작이 과거 알고리즘과 달라질 때만 실패하게 한다.
    closing = []
    body = []
    for section in personal.sections:
        if section.id in {"cover", "toc", "appendix_terms", "colophon"}:
            if section.id in {"appendix_terms", "colophon"}:
                closing.append(integrated._copy_section(section))
            continue
        if section.id == "closing":
            closing.insert(0, integrated._copy_section(section))
            continue
        body.append(integrated._copy_section(section, prefix="personal"))
    legacy_sections = body + [
        integrated._copy_section(section, prefix="relationship") for section in relationship
    ] + closing
    for section in legacy_sections:
        section.final_text = integrated._integrated_style_safe_text(section.final_text)
    legacy_sections = integrated._compact_sparse_sections(legacy_sections)

    assembly = integrated._assemble_sections(personal, relationship, None)
    assert isinstance(assembly, list)
    current = assembly.sections
    assert [(section.id, section.final_text) for section in current] == [
        (section.id, section.final_text) for section in legacy_sections
    ]


def test_love_only_filters_before_sparse_merge_and_skips_gunghap(monkeypatch):
    # 1인 love 조합은 관계 compose를 부르지 않고, 선택 밖 제공자 텍스트도 병합 입력에 없다.
    captured = _patch_sources(monkeypatch)
    result = integrated.build_integrated_full(
        _people(1),
        receiver_name="DOC_A",
        situation="합성 맥락",
        modules=["love"],
        render=False,
    )
    text = "\n".join(section.final_text for section in result["sections"])

    assert captured["gunghap_calls"] == 0
    assert "love" in captured["included_section_calls"][0]
    assert "work" not in captured["included_section_calls"][0]
    assert "health" not in captured["included_section_calls"][0]
    assert "연애 제공자 문단" in text
    assert "직업 제공자 문단" not in text
    assert "재물 제공자 문단" not in text
    assert "건강 제공자 문단" not in text
    assert "관계 제공자 문단" not in text
    assert result["module_sections"]["love"] == ["personal_love"]
    assert result["module_sections"]["gunghap"] == []


def test_job_and_wealth_modules_consume_different_work_providers(monkeypatch):
    # 같은 personal_work 슬롯을 유지하되 제공자 본문은 선택에 따라 실제로 달라져야 한다.
    captured = _patch_sources(monkeypatch)
    job = integrated.build_integrated_full(
        _people(1), receiver_name="DOC_A", modules=["job"], render=False
    )
    wealth = integrated.build_integrated_full(
        _people(1), receiver_name="DOC_A", modules=["wealth"], render=False
    )
    job_text = "\n".join(section.final_text for section in job["sections"])
    wealth_text = "\n".join(section.final_text for section in wealth["sections"])

    assert captured["personal_calls"] == [("job",), ("wealth",)]
    assert "직업 제공자 문단" in job_text and "재물 제공자 문단" not in job_text
    assert "재물 제공자 문단" in wealth_text and "직업 제공자 문단" not in wealth_text
    assert job["module_sections"]["job"] == ["personal_work"]
    assert wealth["module_sections"]["wealth"] == ["personal_work"]


def test_gunghap_requires_two_people_but_two_people_pass(monkeypatch):
    # 경계값 1인은 조립 전 차단하고, 2인은 관계 제공자까지 정상 조립한다.
    captured = _patch_sources(monkeypatch)
    with pytest.raises(ValueError, match="at least two"):
        integrated.build_integrated_full(
            _people(1), receiver_name="DOC_A", modules=["gunghap"], render=False
        )

    result = integrated.build_integrated_full(
        _people(2), receiver_name="DOC_A", modules=["gunghap"], render=False
    )
    assert captured["gunghap_calls"] == 1
    assert result["module_sections"]["gunghap"] == ["relationship_overview"]


def test_duplicate_premerge_section_ids_fail_assembly():
    # sparse 병합이 중복 ID를 숨기기 전에 조립기가 명시적으로 실패해야 한다.
    personal = SimpleNamespace(
        sections=[_section("love", "첫 문단"), _section("love", "둘째 문단")]
    )
    with pytest.raises(ValueError, match="duplicate"):
        integrated._assemble_sections(personal, [], ["love"])


def test_module_coverage_uses_premerge_ids_not_compacted_ids(monkeypatch):
    # 최종 sparse 결과에서 love/work/health ID가 사라져도 병합 전 맵은 모두 존재해 오탐이 없다.
    _patch_sources(monkeypatch)
    result = integrated.build_integrated_full(
        _people(), receiver_name="DOC_A", situation="합성 맥락", render=False
    )
    final_ids = {section.id for section in result["sections"]}
    assert "personal_love" not in final_ids
    assert "personal_work" not in final_ids
    assert "personal_health" not in final_ids

    checked = delivery_quality.analyze(
        "자미두수와 명리 관점을 함께 살핍니다. " * 600,
        pages=30,
        product="integrated_full",
        selected_modules=result["modules"],
        module_sections=result["module_sections"],
    )
    rules_found = {failure["rule"] for failure in checked["failures"]}
    assert "missing_module_sections" not in rules_found
    assert "unexpected_module_sections" not in rules_found
    assert checked["module_coverage"]["checked_before_sparse_merge"] is True
    assert checked["module_coverage"]["skipped"] is False


def test_module_coverage_blocks_missing_and_unexpected_sections():
    # 정상 love 맵에서 love를 지우면 missing, health를 주입하면 unexpected가 각각 하드 실패다.
    missing_sections = _module_sections_for(["love"])
    missing_sections["love"] = []
    missing = delivery_quality.analyze(
        "자미두수와 명리 관점을 함께 살핍니다. " * 600,
        pages=16,
        product="integrated_full",
        selected_modules=["love"],
        module_sections=missing_sections,
    )
    assert "missing_module_sections" in {failure["rule"] for failure in missing["failures"]}

    unexpected_sections = _module_sections_for(["love"])
    unexpected = delivery_quality.analyze(
        "자미두수와 명리 관점을 함께 살핍니다. " * 600,
        pages=16,
        product="integrated_full",
        selected_modules=["love"],
        module_sections=unexpected_sections,
        # 구조화 맵을 조작하지 않고 실제 병합 전 목록에만 health를 합성 주입한다.
        premerge_section_ids=[
            "personal_intro",
            "personal_love",
            "personal_health",
            "personal_consult",
        ],
    )
    assert "unexpected_module_sections" in {
        failure["rule"] for failure in unexpected["failures"]
    }


def test_module_coverage_rejects_misattributed_known_section_like_unmapped_control():
    # R9-1 P1: love가 health를 선점 주장해도 거부한 뒤 health 실소유로 귀속해야 한다.
    forged = _module_sections_for(["love"])
    forged["love"].append("personal_health")
    premerge_ids = _premerge_ids(forged)
    forged_result = integrated_modules.module_coverage(["love"], forged, premerge_ids)

    assert forged_result["missing_modules"] == []
    assert forged_result["unexpected_modules"] == ["health"]
    assert forged_result["unknown_section_ids"] == []
    assert forged_result["module_sections"]["love"] == ["personal_love"]
    assert forged_result["module_sections"]["health"] == ["personal_health"]
    assert forged_result["misattributed_section_ids"] == [
        {
            "claimed_module": "love",
            "section_id": "personal_health",
            "owner_modules": ["health"],
        }
    ]

    # R9-1 P2 대조군: 같은 평면 목록에서 health를 미배정해도 동일하게 health 유입을 잡는다.
    honest = _module_sections_for(["love"])
    honest_result = integrated_modules.module_coverage(["love"], honest, premerge_ids)
    assert honest_result["unexpected_modules"] == ["health"]
    assert honest_result["misattributed_section_ids"] == []


@pytest.mark.parametrize(
    ("injected_id", "expected_unexpected", "expected_unknown", "expected_owner"),
    [
        ("fake_zone", [], ["fake_zone"], []),
        ("relationship_overview", ["gunghap"], [], ["gunghap"]),
    ],
)
def test_module_coverage_rejects_claimed_unknown_and_relationship_sections(
    injected_id, expected_unexpected, expected_unknown, expected_owner
):
    # R9-1 P3/P4: 미등록 ID와 관계 전속 ID 모두 love 주장으로 세탁되지 않아야 한다.
    forged = _module_sections_for(["love"])
    forged["love"].append(injected_id)
    premerge_ids = _premerge_ids(forged)
    coverage = integrated_modules.module_coverage(["love"], forged, premerge_ids)

    assert coverage["unexpected_modules"] == expected_unexpected
    assert coverage["unknown_section_ids"] == expected_unknown
    assert coverage["misattributed_section_ids"][-1] == {
        "claimed_module": "love",
        "section_id": injected_id,
        "owner_modules": expected_owner,
    }
    analyzed = _analyze_module_map(forged, premerge_ids)
    assert "unexpected_module_sections" in {
        failure["rule"] for failure in analyzed["failures"]
    }


def test_fake_section_cannot_bypass_missing_selected_module():
    # R9-1 missing 우회: 가짜 ID 하나로 love 커버리지를 채우려 하면 missing+unknown이 함께 실패한다.
    forged = _module_sections_for(["love"])
    forged["love"] = ["fake_zone"]
    premerge_ids = _premerge_ids(forged)
    coverage = integrated_modules.module_coverage(["love"], forged, premerge_ids)

    assert coverage["missing_modules"] == ["love"]
    assert coverage["unknown_section_ids"] == ["fake_zone"]
    analyzed = _analyze_module_map(forged, premerge_ids)
    failure_rules = {failure["rule"] for failure in analyzed["failures"]}
    assert {"missing_module_sections", "unexpected_module_sections"} <= failure_rules


def test_delivery_quality_blocks_p1_misattributed_health_claim():
    # 모듈 단위 함수만이 아니라 실제 delivery_quality failures에도 P1 차단이 나타나야 한다.
    forged = _module_sections_for(["love"])
    forged["love"].append("personal_health")
    analyzed = _analyze_module_map(forged, _premerge_ids(forged))
    assert "unexpected_module_sections" in {
        failure["rule"] for failure in analyzed["failures"]
    }
    assert analyzed["module_coverage"]["unexpected_modules"] == ["health"]


def test_registry_owned_legacy_work_core_and_tail_claims_remain_clean():
    # 통과측: legacy 대표맵과 work 이중 소유, core/tail 자기 소유는 R9-1에서 오탐하면 안 된다.
    legacy = integrated_modules.module_coverage(None, None, None)
    assert legacy["missing_modules"] == []
    assert legacy["unexpected_modules"] == []
    assert legacy["unknown_section_ids"] == []
    assert legacy["misattributed_section_ids"] == []

    work = _module_sections_for(["job", "wealth"])
    work_result = integrated_modules.module_coverage(
        ["job", "wealth"], work, _premerge_ids(work)
    )
    assert work_result["missing_modules"] == []
    assert work_result["unexpected_modules"] == []
    assert work_result["unknown_section_ids"] == []
    assert work_result["misattributed_section_ids"] == []
    assert work_result["module_sections"]["job"] == ["personal_work"]
    assert work_result["module_sections"]["wealth"] == ["personal_work"]


@pytest.mark.parametrize("love_section_id", ["love", "personal_love"])
def test_registry_ownership_accepts_raw_and_personal_prefixed_ids(love_section_id):
    # A-4 이웃: raw ID와 personal_ ID가 같은 소유권 정규화 경로를 타야 한다.
    sections = {"love": [love_section_id]}
    coverage = integrated_modules.module_coverage(["love"], sections, [love_section_id])
    assert coverage["missing_modules"] == []
    assert coverage["unexpected_modules"] == []
    assert coverage["unknown_section_ids"] == []
    assert coverage["misattributed_section_ids"] == []


@pytest.mark.parametrize(
    ("selected_modules", "minimum_pages", "minimum_chars"),
    [
        (["love"], 16, 3_000),
        (["love", "job"], 20, 5_000),
        (["love", "job", "wealth"], 24, 7_000),
        (["love", "job", "wealth", "health"], 28, 9_000),
        (["love", "job", "wealth", "health", "gunghap"], 30, 10_000),
    ],
)
def test_module_count_boundary_table_blocks_minus_one_and_accepts_floor(
    selected_modules, minimum_pages, minimum_chars
):
    # 승인 공식 N=1..5의 두 경계를 같은 표에서 검증해 자릿수·상한 인접 사각을 막는다.
    module_sections = _module_sections_for(selected_modules)
    below = delivery_quality.analyze(
        "가" * (minimum_chars - 1),
        pages=minimum_pages - 1,
        product="integrated_full",
        selected_modules=selected_modules,
        module_sections=module_sections,
    )
    below_rules = {failure["rule"] for failure in below["failures"]}
    assert {"premium_pages", "premium_text_chars"} <= below_rules

    floor = delivery_quality.analyze(
        "가" * minimum_chars,
        pages=minimum_pages,
        product="integrated_full",
        selected_modules=selected_modules,
        module_sections=module_sections,
    )
    floor_rules = {failure["rule"] for failure in floor["failures"]}
    assert "premium_pages" not in floor_rules
    assert "premium_text_chars" not in floor_rules
    assert floor["minimum_pages"] == minimum_pages
    assert floor["minimum_text_chars"] == minimum_chars


def test_render_bridge_forwards_selected_modules_and_premerge_coverage(monkeypatch):
    # verify 소비처까지 파라미터가 관통해야 팬텀 메타가 아니다. PDF 생성기는 합성 경로로 대체한다.
    captured: dict[str, object] = {}
    monkeypatch.setattr(integrated.render_pdf, "render_pdf", lambda *args, **kwargs: "fake.pdf")

    def fake_verify(*args, **kwargs):
        captured.update(kwargs)
        return {"gate_pass": True}

    monkeypatch.setattr(integrated.render_verify, "verify", fake_verify)
    module_sections = _module_sections_for(["love"])
    integrated._render_integrated(
        SimpleNamespace(sections=[]),
        names=["DOC_A"],
        ref_year=2026,
        situation="합성 맥락",
        identity=(set(), set(), []),
        singang=[],
        role_specs=[],
        brand="sajudoryeong",
        out_name="fake.pdf",
        out_dir=None,
        selected_modules=["love"],
        module_sections=module_sections,
        premerge_section_ids=["personal_intro", "personal_love", "personal_consult"],
    )

    assert captured["selected_modules"] == ["love"]
    assert captured["module_sections"] == module_sections
    assert captured["premerge_section_ids"] == [
        "personal_intro",
        "personal_love",
        "personal_consult",
    ]


def test_partial_modules_persist_and_restore_for_rerender(monkeypatch, tmp_path):
    # compose 시점의 선택·병합 전 맵이 content.json을 거쳐 재렌더 verify까지 동일하게 복원된다.
    _patch_sources(monkeypatch)
    result = integrated.build_integrated_full(
        _people(1), receiver_name="DOC_A", modules=["love", "job"], render=False
    )
    content_path = integrated._save_integrated_content(
        result,
        situation="합성 맥락",
        ref_year=2026,
        brand="sajudoryeong",
        out_name="partial.pdf",
        out_dir=tmp_path,
    )
    saved = json.loads(Path(content_path).read_text(encoding="utf-8"))
    assert saved["modules"] == ["love", "job"]
    assert saved["module_schema_version"] == integrated.MODULE_SCHEMA_VERSION
    assert saved["module_sections"] == result["module_sections"]

    captured: dict[str, object] = {}

    def fake_render(report, **kwargs):
        captured.update(kwargs)
        return "fake.pdf", {"gate_pass": True}, []

    monkeypatch.setattr(integrated, "_render_integrated", fake_render)
    restored = integrated.render_integrated_from_content(content_path)
    assert captured["selected_modules"] == ("love", "job")
    assert captured["module_sections"] == result["module_sections"]
    assert captured["premerge_section_ids"] == result["premerge_section_ids"]
    assert restored["modules"] == ["love", "job"]
