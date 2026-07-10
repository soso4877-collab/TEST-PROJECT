# -*- coding: utf-8 -*-
"""integrated_full 질문 영역 모듈의 결정론 레지스트리와 공통 계산.

조립기와 납품 게이트가 같은 모듈 순서·소유권·분량 공식을 공유하도록 이 파일을
단일 소스로 둔다. 이 레이어는 계산 결과를 만들지 않고 이미 생성된 섹션의 선택 범위만
정하므로 ``calc`` 또는 ``input`` 모듈을 참조하지 않는다.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


MODULE_SCHEMA_VERSION = 1
# content.json 공개 키와 문서 표현이 같은 이름을 사용할 수 있도록 읽기 전용 별칭을 둔다.
module_schema_version = MODULE_SCHEMA_VERSION

# 운영자가 선택하는 영역 모듈의 정규 순서다. 입력 순서와 무관하게 이 순서로 정규화해
# 같은 집합은 항상 같은 문서와 같은 게이트 하한을 만든다.
SELECTABLE_MODULES = ("love", "job", "wealth", "health", "gunghap")
ALWAYS_INCLUDED_MODULES = ("core", "tail")
ALL_MODULES = ALWAYS_INCLUDED_MODULES[:1] + SELECTABLE_MODULES + ALWAYS_INCLUDED_MODULES[1:]

# 레지스트리는 조립 전 개인 섹션 ID를 기준으로 소유권을 선언한다. ``work``는 기존
# 5모듈 출력의 단일 섹션 ID를 보존하면서 job/wealth 제공자를 선택적으로 합치는 호환 슬롯이다.
# 관계 섹션은 개수가 가변이므로 고정 ID 대신 prefix 계약을 사용한다.
MODULE_REGISTRY: dict[str, dict[str, object]] = {
    "core": {
        "personal_section_ids": (
            "intro",
            "wonguk",
            "nature",
            "frame",
            "flow",
            "ziwei",
            "together",
        ),
        "always": True,
    },
    "love": {"personal_section_ids": ("love",), "always": False},
    "job": {
        "personal_section_ids": ("work",),
        "provider_id": "work_job",
        "always": False,
    },
    "wealth": {
        "personal_section_ids": ("work",),
        "provider_id": "work_wealth",
        "always": False,
    },
    "health": {"personal_section_ids": ("health",), "always": False},
    "gunghap": {"section_prefix": "relationship_", "always": False},
    "tail": {
        "personal_section_ids": ("consult", "closing", "appendix_terms", "colophon"),
        "always": True,
    },
}

PERSONAL_SECTION_IDS = frozenset(
    section_id
    for module_id, spec in MODULE_REGISTRY.items()
    if module_id != "gunghap"
    for section_id in spec["personal_section_ids"]
)

_PERSONAL_SECTION_MODULE: dict[str, str] = {
    section_id: module_id
    for module_id in ("core", "love", "health", "tail")
    for section_id in MODULE_REGISTRY[module_id]["personal_section_ids"]
}


def normalize_modules(modules: Iterable[str] | None) -> tuple[str, ...]:
    """선택 모듈을 검증하고 레지스트리 정규 순서의 튜플로 반환한다.

    ``None``은 레거시 integrated_full과 같은 5모듈 전체다. 빈 목록·중복·미등록 ID는
    조용히 보정하지 않고 실패시켜 잘못된 주문 메타가 다른 문서로 변하는 일을 막는다.
    """

    if modules is None:
        return SELECTABLE_MODULES
    raw = [str(module_id).strip().lower() for module_id in modules]
    if not raw:
        raise ValueError("integrated_full modules must select at least one module")
    unknown = sorted(set(raw) - set(SELECTABLE_MODULES))
    if unknown:
        raise ValueError(f"unknown integrated_full modules: {unknown}")
    if len(raw) != len(set(raw)):
        raise ValueError("integrated_full modules must not contain duplicates")
    return tuple(module_id for module_id in SELECTABLE_MODULES if module_id in raw)


def work_provider_modules(selected_modules: Iterable[str] | None) -> tuple[str, ...]:
    """현재 선택에서 기존 ``work`` 슬롯에 넣을 job/wealth 제공자 순서를 반환한다."""

    selected = normalize_modules(selected_modules)
    return tuple(module_id for module_id in ("job", "wealth") if module_id in selected)


def included_personal_sections(selected_modules: Iterable[str] | None) -> frozenset[str]:
    """선택 조합에서 개인 빌더가 실제 작성·가드할 원본 섹션 ID 집합을 반환한다."""

    selected = normalize_modules(selected_modules)
    included = set(MODULE_REGISTRY["core"]["personal_section_ids"])
    included.update(MODULE_REGISTRY["tail"]["personal_section_ids"])
    for module_id in selected:
        if module_id == "gunghap":
            continue
        included.update(MODULE_REGISTRY[module_id]["personal_section_ids"])
    return frozenset(included)


def personal_section_modules(
    section_id: str, selected_modules: Iterable[str] | None
) -> tuple[str, ...]:
    """개인 섹션 하나가 이번 조립에서 속하는 모듈 ID를 반환한다.

    ``work``는 job과 wealth를 모두 고른 경우 같은 물리 섹션 하나가 두 모듈을 충족한다.
    그 외 미등록 섹션은 빈 튜플로 반환해 조립기가 fail-closed 예외를 만들 수 있게 한다.
    """

    selected = normalize_modules(selected_modules)
    if section_id == "work":
        return tuple(module_id for module_id in ("job", "wealth") if module_id in selected)
    module_id = _PERSONAL_SECTION_MODULE.get(section_id)
    if module_id in ALWAYS_INCLUDED_MODULES:
        return (module_id,)
    if module_id and module_id in selected:
        return (module_id,)
    return ()


def empty_module_sections() -> dict[str, list[str]]:
    """병합 전 커버리지 기록용 빈 모듈→섹션 ID 맵을 만든다."""

    return {module_id: [] for module_id in ALL_MODULES}


def legacy_full_module_sections() -> dict[str, list[str]]:
    """모듈 메타가 없던 구 integrated_full 번들의 5모듈 커버리지를 복원한다.

    구 번들은 선택 기능 자체가 없어서 항상 5모듈 전체였다. 따라서 이 기본값은 검사를
    건너뛰는 ``skipped``가 아니라, 당시 조립 전 섹션 계약을 명시적으로 재구성한 값이다.
    """

    sections = empty_module_sections()
    sections["core"] = ["personal_intro"]
    sections["love"] = ["personal_love"]
    sections["job"] = ["personal_work"]
    sections["wealth"] = ["personal_work"]
    sections["health"] = ["personal_health"]
    sections["gunghap"] = ["relationship_overview"]
    sections["tail"] = ["personal_consult"]
    return sections


def normalize_module_sections(
    module_sections: Mapping[str, Iterable[str]] | None,
) -> dict[str, list[str]]:
    """게이트 입력을 JSON 안전한 모듈→고유 섹션 ID 맵으로 정규화한다."""

    source = legacy_full_module_sections() if module_sections is None else module_sections
    normalized = empty_module_sections()
    for module_id, section_ids in source.items():
        key = str(module_id).strip().lower()
        normalized.setdefault(key, [])
        normalized[key] = list(
            dict.fromkeys(str(section_id).strip() for section_id in section_ids if str(section_id).strip())
        )
    return normalized


def _modules_for_unmapped_section(section_id: str) -> tuple[str, ...]:
    """raw/personal_ ID 하나의 정당한 모듈 소유권을 레지스트리에서 복원한다."""

    if section_id.startswith("relationship_"):
        return ("gunghap",)
    raw_id = section_id.removeprefix("personal_")
    if raw_id == "work":
        # work는 물리 ID만으로 job/wealth 제공자를 구분할 수 없다. 정상 조립은 구조화 맵을
        # 함께 넘기므로, 맵 없이 주입된 work는 두 후보를 모두 표시해 조용한 통과를 막는다.
        return ("job", "wealth")
    module_id = _PERSONAL_SECTION_MODULE.get(raw_id)
    if module_id:
        return (module_id,)
    return ()


def module_coverage(
    selected_modules: Iterable[str] | None,
    module_sections: Mapping[str, Iterable[str]] | None,
    premerge_section_ids: Iterable[str] | None = None,
) -> dict[str, object]:
    """병합 전 섹션 맵에서 선택 모듈의 누락과 비선택 모듈 유입을 판정한다."""

    selected = normalize_modules(selected_modules)
    sections = normalize_module_sections(module_sections)
    if premerge_section_ids is None:
        # 구 호출은 구조화 맵 자체가 병합 전 증거다. 이를 평면화해 동일한 교차검증 경로를 탄다.
        premerge_ids = list(
            dict.fromkeys(section_id for values in sections.values() for section_id in values)
        )
    else:
        premerge_ids = list(
            dict.fromkeys(
                str(section_id).strip()
                for section_id in premerge_section_ids
                if str(section_id).strip()
            )
        )
    actual_ids = set(premerge_ids)

    # R9-1 불변식: 실제 평면 목록에 존재하는 것만으로는 충분하지 않다. 구조화 맵의
    # (주장 모듈, 섹션 ID) 쌍도 레지스트리 소유권과 일치해야 커버리지로 인정한다.
    # 불일치 쌍은 여기서 버린 뒤 아래의 기존 미배정 복원 경로로 정확히 한 번만 보낸다.
    effective_sections = {module_id: [] for module_id in sections}
    misattributed_section_ids: list[dict[str, object]] = []
    for claimed_module, section_ids in sections.items():
        for section_id in section_ids:
            if section_id not in actual_ids:
                continue
            owner_modules = _modules_for_unmapped_section(section_id)
            if claimed_module in owner_modules:
                effective_sections[claimed_module].append(section_id)
                continue
            misattributed_section_ids.append(
                {
                    "claimed_module": claimed_module,
                    "section_id": section_id,
                    "owner_modules": list(owner_modules),
                }
            )

    # 평면 목록에만 있던 ID와 위에서 소유권 불일치로 거부된 ID를 같은 단일 경로로
    # 처리한다. 실소유자가 있으면 그쪽으로 귀속하고, 없으면 unknown 관측으로 남긴다.
    mapped_ids = {
        section_id for section_ids in effective_sections.values() for section_id in section_ids
    }
    unmapped_ids = [section_id for section_id in premerge_ids if section_id not in mapped_ids]
    unknown_section_ids: list[str] = []
    for section_id in unmapped_ids:
        owners = _modules_for_unmapped_section(section_id)
        if not owners:
            unknown_section_ids.append(section_id)
            continue
        for module_id in owners:
            effective_sections.setdefault(module_id, []).append(section_id)

    present = {
        module_id
        for module_id, section_ids in effective_sections.items()
        if section_ids and module_id not in ALWAYS_INCLUDED_MODULES
    }
    expected = set(selected)
    return {
        "selected_modules": list(selected),
        "module_sections": effective_sections,
        "premerge_section_ids": premerge_ids,
        "missing_modules": sorted(expected - present, key=SELECTABLE_MODULES.index),
        "unexpected_modules": sorted(
            present - expected,
            key=lambda module_id: (
                SELECTABLE_MODULES.index(module_id)
                if module_id in SELECTABLE_MODULES
                else len(SELECTABLE_MODULES),
                module_id,
            ),
        ),
        "unknown_section_ids": unknown_section_ids,
        "misattributed_section_ids": misattributed_section_ids,
        "checked_before_sparse_merge": True,
        "skipped": False,
    }


def module_minimums(selected_modules: Iterable[str] | None) -> tuple[int, int]:
    """승인 공식으로 선택 수 N의 (최소 페이지, 최소 본문 글자 수)를 계산한다."""

    module_count = len(normalize_modules(selected_modules))
    pages = min(30, 12 + 4 * module_count)
    text_chars = min(10_000, 1_000 + 2_000 * module_count)
    return pages, text_chars
