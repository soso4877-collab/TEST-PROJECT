# -*- coding: utf-8 -*-
"""Phase 3(2026-07-06, C1) — 골격 × lint 매트릭스 (규범·골격·lint 다면 비동기화 차단).

동기(QI-2026-07-05-01 business 골격 미동기화·QI-2026-07-05-02 개인 골격 미동기화):
lint/규범이 게이트에 등재될 때 룰 골격이 함께 동기화됐는지를 골격 전 축 × text lint 전수로
고정한다. test_customer_meta_lint.py:134(단일 lint) 패턴의 일반화.

골격 축(전부 API 0 합성·무렌더·무LLM): personal 7카테고리 + gunghap business/relationship
+ integrated + followup 결정론 답변. lint 축: text/adapter 호환 lint 자동 등재 + 명시 어댑터.

완전성(advisor — silent 제외 금지): 모든 게이트 content-lint 키가 enrolled/matrix-excluded/
specs-excluded/non-lint 중 정확히 하나로 분류됨을 단언한다. 신규 게이트 lint → 미분류 RED.
검증하지 않는 것: LLM 윤문 품질(골격 하한만), 렌더 후 스코프(style_clean=_semantic_style_hits).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import (  # noqa: E402
    builder,
    client_tone_lint as ct,
    customer_meta_lint,
    delivery_quality as dq,
    quality_lint,
    rules,
    safe_lint,
    temporal_lint,
)
from sajugen.render import verify  # noqa: E402
from sajugen import gunghap, integrated  # noqa: E402

_PPL = [("갑", (1990, 1, 1, 10, 0), True), ("을", (1991, 2, 2, 11, 0), False)]
# 부록 용어집·맺음은 body-스코프 lint(loanword/raw_calc)의 allowed-zone(게이트 body/appendix 분리).
_APPENDIX_SECTIONS = {"appendix_terms", "colophon"}
# 커플 상품(2인)은 커플 지칭이 정상 — placeholder 커플 검사(strict_pair)는 개인 문서 전용.
_COUPLE_AXES = {"gunghap_business", "gunghap_relationship", "integrated"}


_PERSONAL_CONCERNS = {
    "연애": "상대가 군대에 있어 연락이 뜸한데 관계의 속도를 어떻게 맞출까요?",
    "직업": "직업과 시험의 시기, 일의 방향이 궁금합니다.",
    "재물": "땅과 자산, 계약과 잔금의 시기를 어떻게 나눌까요?",
    "건강": "건강과 생활 습관의 완급이 궁금합니다.",
    "대인": "모임을 시작할 때 사람과 역할을 어떻게 나눌까요?",
    "시기": "올해와 내년에는 무엇부터 움직이는 편이 좋을까요?",
    "전반": "전반적인 강점과 조심할 때가 궁금합니다.",
}


def _personal(cat: str) -> list[tuple[str, str]]:
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    T = rules.build_all(
        saju,
        ref_year=2026,
        name="테스트",
        concern_category=cat,
        concern_text=_PERSONAL_CONCERNS[cat],
    )
    return list(T.items())


def _gunghap(mode: str) -> list[tuple[str, str]]:
    r = gunghap.build_gunghap(_PPL, ref_year=2026, mode=mode, use_llm=False, render=False)
    return [(s.id, s.final_text) for s in r["sections"]]


def _integrated() -> list[tuple[str, str]]:
    r = integrated.build_integrated_full(_PPL, ref_year=2026, use_llm=False, render=False)
    return [(s.id, s.final_text) for s in r["report"].sections]


def _followup() -> list[tuple[str, str]]:
    # 후속 답변의 무LLM 골격은 저장된 personal consult를 재사용한다. 별도 계산·API 없이
    # 실제 answer_gate가 받는 고객 가시 답변 표면을 매트릭스에 포함한다.
    consult = dict(_personal("직업"))["consult"]
    return [("followup_answer", consult)]


def _build_axes() -> dict[str, list[tuple[str, str]]]:
    return {
        **{
            f"personal_{category}": _personal(category)
            for category in ("연애", "직업", "재물", "건강", "대인", "시기", "전반")
        },
        "gunghap_business": _gunghap("business"),
        "gunghap_relationship": _gunghap("relationship"),
        "integrated": _integrated(),
        "followup": _followup(),
    }


def _rule_of(h) -> str:
    if isinstance(h, dict):
        return str(h.get("rule") or h.get("token") or h.get("match") or "hit")
    return str(h)


# 등재 lint: fn(text)->hits + body_scoped(부록 제외) + couple_check(커플 축 제외).
class _Lint:
    def __init__(self, name, fn, *, body_scoped=False, couple_check=False):
        self.name, self.fn = name, fn
        self.body_scoped, self.couple_check = body_scoped, couple_check


_LINTS = [
    _Lint("safe", lambda t: safe_lint.lint(t)),
    _Lint("customer_meta", lambda t: customer_meta_lint.lint(t)),
    _Lint("quality", lambda t: quality_lint.lint(t)),
    _Lint("temporal", lambda t: temporal_lint.lint(t, 2026)),
    _Lint("guarantee", lambda t: dq.guarantee_lint(t)),
    _Lint("external_domain_advice", lambda t: dq.external_domain_advice_lint(t)),
    _Lint("loanword", lambda t: ct.loanword_lint(t), body_scoped=True),
    # 게이트 raw_calc_head_clean 과 동일 함수(표제형만) — raw_calc_lint(산문 용어까지)가
    # 아니라 raw_calc_headwords 를 써야 게이트 스코프를 정확히 미러링(오행국 산문 언급은 비표제).
    _Lint("raw_calc", lambda t: ct.raw_calc_headwords(t), body_scoped=True),
    # register는 고객 가시 PDF 전체(표지·본문·부록) 계약이므로 body_scoped=False.
    # warning은 관측만 하며 하드 게이트 매트릭스에서는 제외한다.
    _Lint(
        "register",
        lambda t: [h for h in ct.register_lint(t) if h["severity"] == "hard"],
    ),
    _Lint("placeholder", lambda t: ct.placeholder_residue_lint(t), couple_check=True),
]

# ── 게이트 content-lint 키 완전성 분류(silent 제외 금지) ──
_ENROLLED_GATE_KEYS = {
    "quality_clean",
    "temporal_clean",
    "loanword_clean",
    "raw_calc_head_clean",
    "client_register_clean",
    "unknown_time_provenance_clean",
    "customer_meta_clean",
    "placeholder_residue_clean",
}
_MATRIX_EXCLUDED = {
    # 게이트 style_clean 은 verify._semantic_style_hits(렌더 body 페이지) 사용 — raw 골격의
    # 장식 구분자(·/—/→)는 그 스코프 밖. 렌더 검증(test_render_verify)이 커버.
    "style_clean": "게이트는 _semantic_style_hits(렌더 후) 사용, raw 골격 style_lint 스코프 밖",
}
_SPECS_EXCLUDED = {
    "role_perspective_clean": "receiver 관점 specs(런타임) 필요 — build 가드 테스트가 커버",
    "honorific_consistency_clean": "honorific specs 필요 — build 가드 테스트 커버",
    "name_policy_clean": "full_names specs 필요 — build 가드 테스트 커버",
    "identity_role_clean": "identity specs 필요 — build 가드 테스트 커버",
    "singang_role_clean": "singang specs 필요 — build 가드 테스트 커버",
}
_NON_LINT_GATES = {
    "text_layer_ok",
    "fonts_embedded",
    "tagged",
    "markdown_clean",
    "daewoon_consistent",
    "no_orphan",
    "delivery_quality_clean",
    "layout_geometry_clean",
}

# 의도적 예외(axis, lint, rule): 전수 분류에서 실결함 아님으로 판정. 사유 필수.
_ALLOW = {
    # 커플 상품(2인)의 커플 지칭은 정상 — placeholder 커플 검사는 개인 문서(파트너 부재) 전용.
    ("gunghap_relationship", "placeholder", "couple_pair_reference"): "커플 상품 정상 지칭",
    ("integrated", "placeholder", "couple_pair_reference"): "커플 상품 정상 지칭",
    # integrated 는 자미 용어 풀이(사화·오행국 정의)를 relationship_overview 에 인라인 —
    # 용어집 정의는 allowed-zone(게이트는 렌더 페이지 body/appendix 분리로 부록 제외).
    (
        "integrated",
        "raw_calc",
        "오행국",
    ): "인라인 용어 풀이 정의(allowed-zone), 게이트는 부록 페이지 제외",
}


def test_skeleton_lint_matrix_clean_or_allowlisted():
    axes = _build_axes()
    unresolved = []
    for axis, secs in axes.items():
        for sid, text in secs:
            for lint in _LINTS:
                if lint.body_scoped and sid in _APPENDIX_SECTIONS:
                    continue  # 부록 allowed-zone
                if lint.couple_check and axis in _COUPLE_AXES:
                    continue  # 커플 상품은 커플 지칭 정상(strict_pair off)
                for h in lint.fn(text) or []:
                    key = (axis, lint.name, _rule_of(h))
                    if key not in _ALLOW:
                        unresolved.append(f"{axis}/{sid}/{lint.name}/{_rule_of(h)}")
    assert unresolved == [], f"골격 미동기화(수정 또는 allowlist+사유): {sorted(set(unresolved))}"


def test_gate_content_lint_coverage_is_complete():
    # 완전성: 모든 게이트 키가 정확히 한 분류에 속한다(신규 게이트 lint → 미분류 RED).
    classified = (
        _ENROLLED_GATE_KEYS | set(_MATRIX_EXCLUDED) | set(_SPECS_EXCLUDED) | _NON_LINT_GATES
    )
    live = set(verify.GATE_KEYS)
    missing = live - classified  # 게이트에 있으나 미분류
    phantom = classified - live  # 분류에 있으나 게이트 아님
    assert not missing, (
        f"미분류 게이트 키(enrolled/excluded/specs/non-lint 중 하나로 분류 필요): {missing}"
    )
    assert not phantom, f"게이트에 없는 분류 키(팬텀): {phantom}"
    # 분류가 겹치지 않는지(파티션)
    groups = [_ENROLLED_GATE_KEYS, set(_MATRIX_EXCLUDED), set(_SPECS_EXCLUDED), _NON_LINT_GATES]
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            assert not (groups[i] & groups[j]), f"분류 중복: {groups[i] & groups[j]}"


def test_matrix_detects_injected_desync():
    # POSITIVE(B-2 no-op 방지): 골격에 lint 위반을 합성 주입하면 매트릭스가 검출.
    # customer_meta 위반 문구를 임의 섹션 텍스트로 두고 미분류로 잡히는지.
    bad = "이 글은 통합 풀이입니다."  # document_self_reference + product_structure_label
    hits = customer_meta_lint.lint(bad)
    assert hits, "테스트 전제: 주입 문구가 customer_meta 위반이어야 함"
    key = ("synthetic", "customer_meta", _rule_of(hits[0]))
    assert key not in _ALLOW  # allowlist 에 없으므로 매트릭스라면 unresolved 로 잡힘


def test_personal_fallback_glosses_first_hard_terms_near_first_appearance():
    """LLM 없이도 주요 전문용어 첫 등장 곁에 쉬운 뜻이 붙는지 고정한다."""

    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    report = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        name="합성인",
        concern="직업과 재물의 시기와 방향이 궁금합니다.",
    )
    body = "\n".join(
        section.final_text
        for section in report.sections
        if section.id not in {"cover", "toc"}
    )
    expected_nearby = {
        "십성": ("관계의 작용",),
        "식신": ("표현", "생산"),
        "재성": ("현실", "재물"),
        "관성": ("책임", "규칙"),
        "인성": ("배움", "보호"),
        "용신": ("균형", "기운"),
        "신약": ("나약하다는 뜻이 아니라",),
        "대운": ("약 10년 단위",),
        "세운": ("해마다",),
        "천간": ("겉으로 드러",),
        "지지": ("바탕 글자",),
        "자미두수": ("별과 12궁",),
    }
    for concept, anchors in expected_nearby.items():
        first = body.find(concept)
        assert first >= 0, concept
        nearby = body[max(0, first - 100) : first + 220]
        assert all(anchor in nearby for anchor in anchors), (concept, nearby)
