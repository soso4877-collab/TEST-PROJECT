# -*- coding: utf-8 -*-
"""개인 PDF 12개 LLM 챕터가 공유하는 결정론적·PII-free 문맥.

이 모듈은 고객 원문이나 계산 결과를 요약하지 않는다. 선택 모듈, 질문 분류, 챕터별
책임, 승인된 설명·조언·반복 규칙의 **고정 ID**만 조립한다. 따라서 이름·생년월일·
질문 원문·이전 LLM 산문을 실수로 공통 프롬프트에 넣을 수 없고, 같은 입력이면 항상
같은 직렬화 결과가 나온다.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

from sajugen import modules as integrated_modules

from .question_router import QuestionCategory


_DEFAULT_PERSONAL_MODULES = ("love", "job", "wealth", "health")

# 공통 논지는 고객별 산문이 아니라 보고서 전체가 지켜야 할 이야기 순서다.
_BASE_NARRATIVE_IDS = (
    "strength_before_task",
    "evidence_before_advice",
    "future_without_guarantee",
)
_CATEGORY_NARRATIVE_ID = {
    QuestionCategory.LOVE.value: "question_love",
    QuestionCategory.JOB.value: "question_job",
    QuestionCategory.WEALTH.value: "question_wealth",
    QuestionCategory.HEALTH.value: "question_health",
    QuestionCategory.RELATION.value: "question_relation",
    QuestionCategory.TIMING.value: "question_timing",
    QuestionCategory.GENERAL.value: "question_general",
}

# 각 챕터가 맡는 주제를 한 곳에서 고정해, 서로의 결론을 반복하는 일을 줄인다.
_SECTION_OWNERSHIP: dict[str, tuple[str, ...]] = {
    "intro": ("report_entry", "identity_overview"),
    "wonguk": ("four_pillars", "day_pillar_intro"),
    "nature": ("temperament", "strength_and_task"),
    "frame": ("gyeokguk", "sinsal"),
    "love": ("love_relationship", "spouse_palace"),
    "work": ("work_style", "wealth_style"),
    "health": ("daily_rhythm", "health_caution"),
    "flow": ("daewoon", "seun_timing"),
    "ziwei": ("ziwei_core", "palace_structure"),
    "together": ("cross_system_synthesis",),
    "consult": ("question_direct_answer", "allowed_action"),
    "closing": ("strength_recap", "small_next_step"),
}

# 삼주 모드에서는 소유권 ID 자체도 허용 출처만 가리킨다. 프롬프트에 ``four_pillars``·
# ``spouse_palace``·``daewoon`` 같은 ID만 남아도 모델이 금지 사실을 복원할 수 있으므로
# 고객 산문과 별개로 공통 문맥 계약부터 좁힌다.
_THREE_PILLAR_SECTION_OWNERSHIP: dict[str, tuple[str, ...]] = {
    "intro": ("reading_scope", "identity_overview"),
    "wonguk": ("three_pillars", "day_pillar_intro"),
    "nature": ("day_master", "known_pillar_roles"),
    "frame": ("month_order_geukguk", "time_invariant"),
    "love": ("relationship_pacing", "day_pillar_relation"),
    "work": ("work_style", "wealth_pacing"),
    "health": ("daily_rhythm", "health_caution"),
    "flow": ("calendar_flow", "seun_timing"),
    "consult": ("question_direct_answer", "allowed_action"),
    "closing": ("scope_recap", "small_next_step"),
}

# docs/14 tone-contract-v1의 12개 개념군과 같은 순서로 유지한다. 영어 내부 ID만
# 전달하면 모델이 승인된 개념 범위를 알 수 없으므로, 고객에게 바로 쓸 수 있는 한국어
# 설명까지 공통 prefix에 넣는다. 이 상수는 문서↔런타임 양방 계약 테스트의 공개 표면이다.
GLOSSARY_EXPLANATIONS: dict[str, str] = {
    "십성": "일간을 기준으로 표현·재물·책임·배움 같은 역할을 나눈 이름",
    "식신": "생각과 재능을 말이나 결과물로 밖에 내놓는 힘",
    "재성": "돈·성과·현실 자원을 다루는 방식",
    "관성": "규칙·책임·직업 역할을 받아들이는 방식",
    "인성": "배움·보호·생각을 받아들이고 쌓는 힘",
    "용신": "명식 전체의 균형을 돕는 데 유용하게 쓰이는 기운",
    "신약": "나약하다는 뜻이 아니라 중심 기운이 도움과 균형을 더 필요로 하는 상태",
    "대운": "약 10년 단위로 바뀌는 큰 흐름",
    "세운·월운": "해와 달 단위로 달라지는 비교적 짧은 흐름",
    "천간·지지": "겉으로 드러난 기운과 그 기운을 받치는 바탕",
    "역마·화개": "움직임·변화와 몰입·내면 성향을 읽는 신살 이름",
    "자미 계열 별 이름": "자미두수에서 성향과 삶의 영역을 설명하는 상징 이름",
}
_GLOSSARY_EXPLANATION_IDS = tuple(GLOSSARY_EXPLANATIONS)
_THREE_PILLAR_GLOSSARY_EXPLANATION_IDS = (
    "십성",
    "식신",
    "재성",
    "관성",
    "인성",
    "세운·월운",
    "천간·지지",
)
GLOSSARY_OWNER_BY_CONCEPT: dict[str, str] = {
    "십성": "nature",
    "식신": "nature",
    "재성": "nature",
    "관성": "nature",
    "인성": "nature",
    "용신": "frame",
    "신약": "nature",
    "대운": "flow",
    "세운·월운": "flow",
    "천간·지지": "wonguk",
    "역마·화개": "frame",
    "자미 계열 별 이름": "ziwei",
}
_GLOSSARY_OWNER_ITEMS = tuple(GLOSSARY_OWNER_BY_CONCEPT.items())

# 선호 소유 장이 상품 토글로 빠질 때 사용할 의미상 가까운 대체 장 순서다. 마지막에는
# 실제 활성 장의 정규 순서를 덧붙이므로, 최소 한 장이 활성인 모든 상품에서 소유권이
# 존재하는 장을 가리킨다. 고객 텍스트를 보고 정하는 규칙이 아니어서 결과는 결정론적이다.
_GLOSSARY_FALLBACK_OWNER_CANDIDATES: dict[str, tuple[str, ...]] = {
    "십성": ("work", "love", "health", "consult", "intro", "ziwei", "closing"),
    "식신": ("work", "love", "health", "consult", "intro", "ziwei", "closing"),
    "재성": ("work", "love", "consult", "intro", "ziwei", "closing"),
    "관성": ("work", "love", "consult", "intro", "ziwei", "closing"),
    "인성": ("work", "health", "consult", "intro", "ziwei", "closing"),
    "용신": ("wonguk", "nature", "consult", "intro", "ziwei", "closing"),
    "신약": ("wonguk", "nature", "health", "consult", "intro", "ziwei", "closing"),
    "대운": ("consult", "work", "love", "health", "intro", "ziwei", "closing"),
    "세운·월운": ("consult", "work", "love", "health", "intro", "ziwei", "closing"),
    "천간·지지": ("nature", "frame", "consult", "intro", "ziwei", "closing"),
    "역마·화개": ("nature", "consult", "intro", "ziwei", "closing"),
    "자미 계열 별 이름": ("ziwei", "intro", "consult", "closing"),
}


def resolve_glossary_owner_by_concept(
    active_section_ids: Iterable[str],
    *,
    concepts: Iterable[str] | None = None,
) -> tuple[tuple[str, str], ...]:
    """이번 상품에 실제 존재하는 장만 가리키도록 용어 설명 소유권을 확정한다.

    docs/14의 맵은 통합 상품 기준 선호 소유 장이다. ``myeongni``·``ziwei`` 상품이나
    부분 모듈에서 그 장이 빠지면 의미상 가까운 활성 장으로 옮긴다. 활성 장이 없거나
    알 수 없는 장이 섞이면 조용히 잘못된 계약을 만들지 않고 실패한다.
    """

    requested = {str(section_id) for section_id in active_section_ids}
    unknown = requested - set(_SECTION_OWNERSHIP)
    if unknown:
        raise ValueError(f"unknown report context sections: {sorted(unknown)}")
    active = tuple(section_id for section_id in _SECTION_OWNERSHIP if section_id in requested)
    if not active:
        raise ValueError("report context must own at least one active section")
    active_set = set(active)

    resolved: list[tuple[str, str]] = []
    requested_concepts = tuple(GLOSSARY_OWNER_BY_CONCEPT if concepts is None else concepts)
    unknown_concepts = set(requested_concepts) - set(GLOSSARY_OWNER_BY_CONCEPT)
    if unknown_concepts:
        raise ValueError(f"unknown report context glossary concepts: {sorted(unknown_concepts)}")
    for concept in requested_concepts:
        preferred = GLOSSARY_OWNER_BY_CONCEPT[concept]
        if preferred in active_set:
            owner = preferred
        else:
            candidates = (*_GLOSSARY_FALLBACK_OWNER_CANDIDATES[concept], *active)
            owner = next(section_id for section_id in candidates if section_id in active_set)
        resolved.append((concept, owner))
    return tuple(resolved)

_ADVICE_BOUNDARY_IDS = (
    "allow_timing_choice",
    "allow_pacing",
    "allow_direction",
    "allow_priority",
    "allow_people_role",
    "allow_relationship_coordination",
    "deny_external_domain_fact",
    "deny_external_procedure",
)

_REPETITION_GUARD_IDS = (
    "day_pillar_intro_owner_wonguk",
    "current_daewoon_single_owner",
    "question_answer_owner_consult",
    "avoid_cross_chapter_rephrase",
)
_THREE_PILLAR_REPETITION_GUARD_IDS = (
    "day_pillar_intro_owner_wonguk",
    "question_answer_owner_consult",
    "avoid_cross_chapter_rephrase",
)

_THREE_PILLAR_FACT_SOURCE_IDS = (
    "three_pillar",
    "time_invariant",
    "calendar_flow",
)

# 장별 근거 슬롯의 단일 소스. 공통 fact_source_ids 전체는 보고서가 사용할 수 있는
# 출처 집합일 뿐이고, 실제 compose는 현재 장에 보이는 이 부분집합만 받는다.
_THREE_PILLAR_SECTION_FACT_SOURCE_IDS: dict[str, tuple[str, ...]] = {
    "cover": ("three_pillar",),
    "intro": ("three_pillar", "time_invariant"),
    "wonguk": ("three_pillar",),
    "nature": ("three_pillar", "time_invariant"),
    "frame": ("three_pillar", "time_invariant"),
    "love": ("three_pillar",),
    "work": ("three_pillar",),
    "health": ("three_pillar",),
    "flow": ("calendar_flow",),
    "consult": ("three_pillar", "time_invariant", "calendar_flow"),
    "closing": ("three_pillar",),
}


def three_pillar_section_fact_source_ids(section_id: str) -> tuple[str, ...]:
    """삼주 장에 실제 공급되는 근거 출처 ID를 결정론적으로 반환한다."""

    return _THREE_PILLAR_SECTION_FACT_SOURCE_IDS.get(str(section_id), ())

_NARRATIVE_TEXT = {
    "strength_before_task": "강점을 먼저 충분히 짚고 보완 과제를 잇는다.",
    "evidence_before_advice": "간지·십성·신살·궁·운의 근거를 제시한 뒤 조언한다.",
    "future_without_guarantee": "시기와 방향은 분명히 말하되 미래 결과는 보장하지 않는다.",
    "question_love": "연애 질문의 답과 판단 신호는 consult 장이 맡는다.",
    "question_job": "직업 질문의 답과 일 방향은 consult 장이 맡는다.",
    "question_wealth": "재물 질문의 답과 완급 조절은 consult 장이 맡는다.",
    "question_health": "건강 질문은 진단 없이 생활 박자와 관찰 방향으로 답한다.",
    "question_relation": "대인 질문은 사람·역할·관계 조율 방향으로 답한다.",
    "question_timing": "시기 질문은 계산 근거가 있는 때와 완급만 말한다.",
    "question_general": "전반 질문은 각 장의 책임을 지키며 같은 결론을 반복하지 않는다.",
}

_ADVICE_TEXT = {
    "allow_timing_choice": "허용: 사주 근거의 시기 선택",
    "allow_pacing": "허용: 속도와 완급 조절",
    "allow_direction": "허용: 방향 선택",
    "allow_priority": "허용: 우선순위 조정",
    "allow_people_role": "허용: 사람과 역할 선택",
    "allow_relationship_coordination": "허용: 관계 조율",
    "deny_external_domain_fact": "금지: 시험·직업·법·제도의 외부 사실 단정",
    "deny_external_procedure": "금지: 원서·서류·행정 절차의 구체 지시",
}

_REPETITION_TEXT = {
    "day_pillar_intro_owner_wonguk": "일주 자기소개는 wonguk 장에서만 한다.",
    "current_daewoon_single_owner": "현재 대운은 보고서 전체에서 하나의 사실로 유지한다.",
    "question_answer_owner_consult": "신청 질문의 직접 답은 consult 장이 맡는다.",
    "avoid_cross_chapter_rephrase": "다른 장의 결론을 표현만 바꾸어 반복하지 않는다.",
}


@dataclass(frozen=True)
class ReportContext:
    """허용 목록의 ID만 보유하는 공유 문맥 값 객체."""

    selected_modules: tuple[str, ...]
    question_category: str
    narrative_anchor_ids: tuple[str, ...]
    section_ownership: tuple[tuple[str, tuple[str, ...]], ...]
    glossary_explanation_ids: tuple[str, ...]
    advice_boundary_ids: tuple[str, ...]
    repetition_guard_ids: tuple[str, ...]
    glossary_owner_by_concept: tuple[tuple[str, str], ...] = _GLOSSARY_OWNER_ITEMS
    schema_version: str = "report-context-v1"
    birth_time_mode: str = "known"
    fact_source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """임의 문자열 주입을 fail-closed로 거부해 PII-free 계약을 타입 경계에서 지킨다."""
        if self.birth_time_mode not in {"known", "three_pillar"}:
            raise ValueError("unsupported report context birth-time mode")
        expected_schema = (
            "report-context-v2-three-pillar"
            if self.birth_time_mode == "three_pillar"
            else "report-context-v1"
        )
        if self.schema_version != expected_schema:
            raise ValueError("unsupported report context schema")
        if self.birth_time_mode == "three_pillar":
            if self.fact_source_ids != _THREE_PILLAR_FACT_SOURCE_IDS:
                raise ValueError("three-pillar report context fact sources are noncanonical")
            ownership_contract = _THREE_PILLAR_SECTION_OWNERSHIP
            expected_glossary_ids = _THREE_PILLAR_GLOSSARY_EXPLANATION_IDS
            expected_repetition_ids = _THREE_PILLAR_REPETITION_GUARD_IDS
        else:
            if self.fact_source_ids:
                raise ValueError("known report context must not override fact sources")
            ownership_contract = _SECTION_OWNERSHIP
            expected_glossary_ids = _GLOSSARY_EXPLANATION_IDS
            expected_repetition_ids = _REPETITION_GUARD_IDS
        try:
            normalized_modules = integrated_modules.normalize_modules(self.selected_modules)
        except (TypeError, ValueError) as exc:
            raise ValueError("report context contains invalid module ids") from exc
        if self.selected_modules != normalized_modules:
            raise ValueError("report context modules are not canonical")
        if self.question_category not in _CATEGORY_NARRATIVE_ID:
            raise ValueError("report context contains unknown question category")
        expected_narrative = (
            *_BASE_NARRATIVE_IDS,
            _CATEGORY_NARRATIVE_ID[self.question_category],
        )
        if self.narrative_anchor_ids != expected_narrative:
            raise ValueError("report context narrative policy is incomplete or noncanonical")
        if not self.section_ownership:
            raise ValueError("report context must own at least one active section")
        seen_sections: set[str] = set()
        for section_id, ownership_ids in self.section_ownership:
            if section_id not in ownership_contract:
                raise ValueError("report context contains unknown section id")
            if section_id in seen_sections:
                raise ValueError("report context contains duplicate section ownership")
            seen_sections.add(section_id)
            if tuple(ownership_ids) != ownership_contract[section_id]:
                raise ValueError("report context contains unknown ownership id")
        canonical_sections = tuple(
            (section_id, ownership_contract[section_id])
            for section_id in ownership_contract
            if section_id in seen_sections
        )
        if self.section_ownership != canonical_sections:
            raise ValueError("report context section ownership is not canonical")
        if self.glossary_explanation_ids != expected_glossary_ids:
            raise ValueError("report context glossary policy is incomplete or noncanonical")
        expected_glossary_owners = resolve_glossary_owner_by_concept(
            seen_sections,
            concepts=self.glossary_explanation_ids,
        )
        if self.glossary_owner_by_concept != expected_glossary_owners:
            raise ValueError("report context glossary ownership is incomplete or noncanonical")
        if self.advice_boundary_ids != _ADVICE_BOUNDARY_IDS:
            raise ValueError("report context advice policy is incomplete or noncanonical")
        if self.repetition_guard_ids != expected_repetition_ids:
            raise ValueError("report context repetition policy is incomplete or noncanonical")

    def as_dict(self) -> dict[str, object]:
        """테스트·감사에 쓰는 결정론적 JSON-safe 표현. 고객 입력 필드는 존재하지 않는다."""
        result = {
            "schema_version": self.schema_version,
            "selected_modules": list(self.selected_modules),
            "question_category": self.question_category,
            "narrative_anchor_ids": list(self.narrative_anchor_ids),
            "section_ownership": {
                section_id: list(ownership_ids)
                for section_id, ownership_ids in self.section_ownership
            },
            "glossary_explanation_ids": list(self.glossary_explanation_ids),
            "glossary_owner_by_concept": dict(self.glossary_owner_by_concept),
            "advice_boundary_ids": list(self.advice_boundary_ids),
            "repetition_guard_ids": list(self.repetition_guard_ids),
        }
        if self.birth_time_mode == "three_pillar":
            result["birth_time_mode"] = self.birth_time_mode
            result["fact_source_ids"] = list(self.fact_source_ids)
        return result

    def to_prompt(self) -> str:
        """모든 compose 호출에 같은 바이트로 전달할 공통 프롬프트 블록을 만든다."""
        payload = json.dumps(
            self.as_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        narratives = "\n".join(
            f"- {anchor_id}: "
            + (
                "연·월·일과 출생 시간에 따라 달라지지 않는 사실을 먼저 제시한 뒤 조언한다."
                if self.birth_time_mode == "three_pillar"
                and anchor_id == "evidence_before_advice"
                else _NARRATIVE_TEXT[anchor_id]
            )
            for anchor_id in self.narrative_anchor_ids
        )
        ownership = "\n".join(
            f"- {section_id}: {', '.join(ownership_ids)}"
            for section_id, ownership_ids in self.section_ownership
        )
        advice = "\n".join(
            f"- {boundary_id}: {_ADVICE_TEXT[boundary_id]}"
            for boundary_id in self.advice_boundary_ids
        )
        repetition = "\n".join(
            f"- {guard_id}: {_REPETITION_TEXT[guard_id]}"
            for guard_id in self.repetition_guard_ids
        )
        glossary_owners = dict(self.glossary_owner_by_concept)
        glossary = "\n".join(
            f"- {concept} (이번 상품 설명 소유 장: {glossary_owners[concept]}): "
            f"{GLOSSARY_EXPLANATIONS[concept]}"
            for concept in self.glossary_explanation_ids
        )
        # 삼주 출처 ID는 사실 생성 권한이 아니라 현재 장 근거의 provenance 표지다.
        # known-time은 빈 문자열을 사용해 승인된 prompt bytes를 그대로 보존한다.
        source_scope = (
            "출처 계약: fact_source_ids는 현재 근거 블록 안에 실제 있는 사실의 출처만 "
            "표시한다. 근거 블록에 없는 사실을 만들 권한이 아니다.\n"
            if self.birth_time_mode == "three_pillar"
            else ""
        )
        return (
            "[리포트 공통 문맥 — 모든 장에서 동일, 고객 원문 없음]\n"
            f"계약 JSON: {payload}\n"
            f"{source_scope}"
            f"공통 논지:\n{narratives}\n"
            f"장별 책임:\n{ownership}\n"
            "용어 계약: 아래 개념은 처음 나오는 같은 문장이나 바로 다음 문장에서 승인된 "
            "쉬운 뜻을 바탕으로 짧게 풀어 쓴다. 표시된 설명 소유 장만 뜻을 풀고, 다른 "
            f"장은 같은 정의를 반복하지 않는다.\n{glossary}\n"
            f"조언 경계:\n{advice}\n"
            f"반복 금지:\n{repetition}"
        )


def build_report_context(
    *,
    selected_modules: Iterable[str] | None,
    question_category: str,
    active_section_ids: Iterable[str],
    birth_time_mode: str = "known",
) -> ReportContext:
    """허용된 런타임 메타만으로 공유 문맥을 한 번 조립한다.

    ``None``은 기존 개인 상품의 love/job/wealth/health 구성을 뜻한다. integrated_full은
    호출측이 실제 선택 모듈을 명시해 gunghap 포함 여부까지 정확히 전달한다.
    """
    modules = integrated_modules.normalize_modules(
        _DEFAULT_PERSONAL_MODULES if selected_modules is None else selected_modules
    )
    category = str(question_category or "").strip()
    if category not in _CATEGORY_NARRATIVE_ID:
        raise ValueError("unknown report context question category")
    if birth_time_mode not in {"known", "three_pillar"}:
        raise ValueError("unsupported report context birth-time mode")
    ownership_contract = (
        _THREE_PILLAR_SECTION_OWNERSHIP
        if birth_time_mode == "three_pillar"
        else _SECTION_OWNERSHIP
    )
    requested_sections = set(str(section_id) for section_id in active_section_ids)
    unknown_sections = requested_sections - set(ownership_contract)
    if unknown_sections:
        raise ValueError(f"unknown report context sections: {sorted(unknown_sections)}")
    ownership = tuple(
        (section_id, ownership_ids)
        for section_id, ownership_ids in ownership_contract.items()
        if section_id in requested_sections
    )
    glossary_ids = (
        _THREE_PILLAR_GLOSSARY_EXPLANATION_IDS
        if birth_time_mode == "three_pillar"
        else _GLOSSARY_EXPLANATION_IDS
    )
    return ReportContext(
        selected_modules=modules,
        question_category=category,
        narrative_anchor_ids=(*_BASE_NARRATIVE_IDS, _CATEGORY_NARRATIVE_ID[category]),
        section_ownership=ownership,
        glossary_explanation_ids=glossary_ids,
        advice_boundary_ids=_ADVICE_BOUNDARY_IDS,
        repetition_guard_ids=(
            _THREE_PILLAR_REPETITION_GUARD_IDS
            if birth_time_mode == "three_pillar"
            else _REPETITION_GUARD_IDS
        ),
        glossary_owner_by_concept=resolve_glossary_owner_by_concept(
            requested_sections,
            concepts=glossary_ids,
        ),
        schema_version=(
            "report-context-v2-three-pillar"
            if birth_time_mode == "three_pillar"
            else "report-context-v1"
        ),
        birth_time_mode=birth_time_mode,
        fact_source_ids=(
            _THREE_PILLAR_FACT_SOURCE_IDS if birth_time_mode == "three_pillar" else ()
        ),
    )
