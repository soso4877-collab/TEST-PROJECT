# -*- coding: utf-8 -*-
"""생시 미상 삼주 결과의 고객 노출·출처 계약.

계산기는 삼주와 12개 시지 후보의 공통 사실을 만들고, 이 모듈은 그 결과가 고객 문안으로
나갈 때 금지 사실이 다시 섞이지 않도록 막는다. 생성 후보, 관리자 편집, 렌더 직전,
최종 PDF 검증이 모두 같은 공개 함수를 사용한다.

finding에는 승인된 규칙 ID와 고정 토큰만 담는다. 실제 문장, 시각값, 이름 같은 고객
정보는 저장하거나 반환하지 않는다.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import re
from typing import Any, Iterable, Mapping


THREE_PILLAR_MODE = "three_pillar"
KNOWN_MODE = "known"
THREE_PILLAR_SCHEMA_VERSION = 1
THREE_PILLAR_CANDIDATE_COUNT = 12
THREE_PILLAR_NOTICE = (
    "출생시각이 확인되지 않아 연·월·일 세 기둥을 기준으로 풀이했습니다. "
    "시간에 따라 달라지는 세부 해석은 제외했습니다."
)
ALLOWED_FACT_SOURCES = ("three_pillar", "time_invariant", "calendar_flow")
PROVENANCE_RULE_IDS = frozenset(
    {
        "schema_version",
        "candidate_count",
        "candidate_digest",
        "stable_fact_ids",
        "stable_fact_ids_duplicate",
        "suppressed_fact_ids",
        "suppressed_fact_ids_duplicate",
        "fact_id_overlap",
    }
)


def normalize_mode(
    birth_time_mode: object | None = None,
    *,
    unknown_time: bool | None = None,
) -> str:
    """공개 birth-time enum을 문자열로 정규화한다.

    계산 축의 정규화 함수가 로드된 런타임에서는 그 함수를 단일 정본으로 사용한다.
    순환 import나 구 저장본을 검사하는 도구에서도 안전하게 동작하도록 값 표면만 보수적으로
    읽는다. 알 수 없는 값은 조용히 known으로 취급하지 않고 예외를 낸다.
    """

    # 콘텐츠/렌더 API의 역사적 기본은 known이다. 계산 입력 정규화와 달리 이 계층에는
    # hour 인자가 없으므로 ``mode=None``을 시각 미상으로 추론하면 모든 기존 문서가 삼주로
    # 뒤집힌다. 레거시 ``unknown_time=True``만 명시적 삼주로 승격한다.
    if birth_time_mode is None and unknown_time is not True:
        birth_time_mode = KNOWN_MODE
    try:
        from ..input.birth_time import normalize_birth_time_mode

        normalized = normalize_birth_time_mode(
            birth_time_mode,
            # 콘텐츠 API의 legacy 기본 False는 "명시 known"이 아니라 과거 함수 기본값이다.
            # True만 호환 신호로 전달하고, 신규 mode와 기본 False가 충돌하지 않게 한다.
            unknown_time=True if unknown_time is True else None,
        )
        return str(getattr(normalized, "value", normalized))
    except ImportError:
        # 단계별 구현 중 구 모듈을 읽는 도구의 하위호환 경로다. 최종 제품 런타임에서는
        # input.birth_time이 존재하므로 이 분기가 정본을 대체하지 않는다.
        value = getattr(birth_time_mode, "value", birth_time_mode)
        if value is None:
            return THREE_PILLAR_MODE if unknown_time else KNOWN_MODE
        value = str(value)
        if value not in {KNOWN_MODE, THREE_PILLAR_MODE}:
            raise ValueError(f"unsupported birth_time_mode: {value}")
        return value


def is_three_pillar_mode(
    birth_time_mode: object | None = None,
    *,
    unknown_time: bool | None = None,
) -> bool:
    return normalize_mode(birth_time_mode, unknown_time=unknown_time) == THREE_PILLAR_MODE


def provenance_from_result(saju: object) -> object | None:
    """계산 결과의 공개 provenance 필드를 그대로 돌려준다."""

    return getattr(saju, "provenance", None)


def _as_mapping(value: object | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    if is_dataclass(value):
        return {str(k): v for k, v in asdict(value).items()}
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return {str(k): v for k, v in dumped.items()} if isinstance(dumped, Mapping) else {}
    keys = (
        "three_pillar_schema_version",
        "schema_version",
        "candidate_count",
        "candidate_digest",
        "stable_fact_ids",
        "suppressed_fact_ids",
    )
    return {key: getattr(value, key) for key in keys if hasattr(value, key)}


def serialize_provenance(value: object | None) -> dict[str, Any]:
    """저장·검증 소비처가 공유하는 JSON-safe provenance 표현."""

    raw = _as_mapping(value)
    schema = raw.get("three_pillar_schema_version", raw.get("schema_version"))
    stable_raw = raw.get("stable_fact_ids")
    suppressed_raw = raw.get("suppressed_fact_ids")
    return {
        "three_pillar_schema_version": schema,
        "candidate_count": raw.get("candidate_count"),
        "candidate_digest": raw.get("candidate_digest"),
        "stable_fact_ids": (
            list(stable_raw) if isinstance(stable_raw, (list, tuple)) else []
        ),
        "suppressed_fact_ids": (
            list(suppressed_raw) if isinstance(suppressed_raw, (list, tuple)) else []
        ),
    }


def _finding(
    rule: str,
    token: str,
    *,
    count: int = 1,
    page: int | None = None,
    source: str,
) -> dict[str, object]:
    """원문을 보유하지 않는 고정 스키마 finding."""

    return {
        "rule": rule,
        "token": token,
        "count": int(count),
        "page": page,
        "source": source,
    }


def provenance_contract_lint(
    provenance: object | None,
    *,
    birth_time_mode: object | None,
    source: str = "provenance",
) -> list[dict[str, object]]:
    """삼주 출처 메타의 스키마·완전성을 fail-closed 검사한다."""

    if not is_three_pillar_mode(birth_time_mode):
        return []
    raw = _as_mapping(provenance)
    data = serialize_provenance(provenance)
    out: list[dict[str, object]] = []
    if data["three_pillar_schema_version"] != THREE_PILLAR_SCHEMA_VERSION:
        out.append(_finding("schema_version", "three_pillar_schema_version", source=source))
    if data["candidate_count"] != THREE_PILLAR_CANDIDATE_COUNT:
        out.append(_finding("candidate_count", "candidate_count", source=source))
    digest = data["candidate_digest"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        out.append(_finding("candidate_digest", "candidate_digest", source=source))
    stable_raw = raw.get("stable_fact_ids")
    stable_ids = data["stable_fact_ids"]
    if (
        not isinstance(stable_raw, (list, tuple))
        or not stable_ids
        or any(not isinstance(v, str) or not v.strip() for v in stable_ids)
    ):
        out.append(_finding("stable_fact_ids", "stable_fact_ids", source=source))
    elif len(stable_ids) != len(set(stable_ids)):
        out.append(
            _finding("stable_fact_ids_duplicate", "stable_fact_ids", source=source)
        )
    suppressed_raw = raw.get("suppressed_fact_ids")
    suppressed_ids = data["suppressed_fact_ids"]
    if not isinstance(suppressed_raw, (list, tuple)) or any(
        not isinstance(v, str) or not v.strip() for v in suppressed_ids
    ):
        out.append(_finding("suppressed_fact_ids", "suppressed_fact_ids", source=source))
    elif len(suppressed_ids) != len(set(suppressed_ids)):
        out.append(
            _finding("suppressed_fact_ids_duplicate", "suppressed_fact_ids", source=source)
        )
    if set(stable_ids) & set(suppressed_ids):
        out.append(_finding("fact_id_overlap", "fact_ids", source=source))
    return out


# 정규식 매치값을 finding에 싣지 않기 위해 token은 항상 아래 고정 라벨을 사용한다.
_FORBIDDEN_TEXT_RULES: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "birth_time_value",
        "출생 시각값",
        re.compile(
            r"(?:출생\s*(?:시각|시간)?|태어난\s*(?:시각|시간)?|생시).{0,16}"
            r"(?:(?:오전|오후)\s*\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?|(?<!\d)\d{1,2}:\d{2}(?!\d)|\d{1,2}\s*시)"
            r"|(?:(?:오전|오후)\s*\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?|(?<!\d)\d{1,2}:\d{2}(?!\d))"
            r".{0,8}(?:출생|태어)"
        ),
    ),
    (
        "noon_estimate",
        "정오 추정",
        re.compile(r"(?:출생|생시).{0,12}정오|정오\s*(?:로|기준|출생|추정|대입)|생시\s*(?:미상|추정)"),
    ),
    (
        "solar_time_correction",
        "진태양시 보정",
        re.compile(r"진태양시|경도\s*보정|보정\s*분수|균시차"),
    ),
    (
        "hour_pillar",
        "시주",
        re.compile(
            r"시주|[갑을병정무기경신임계][자축인묘진사오미신유술해]\s*시"
            r"(?:주|간지|에|는|가|를|로|(?=\s*(?:태어|출생|기운|입니다|$)))"
        ),
    ),
    ("four_pillar_claim", "네 기둥", re.compile(r"네\s*기둥|사주팔자")),
    (
        "ziwei_fact",
        "자미두수 사실",
        re.compile(
            r"자미두수|명반|(?:명|신|부처|관록|재백|질액|천이)궁|(?:12|십이)궁|주성|별\s*이름"
        ),
    ),
    (
        "birth_time_upsell",
        "생시 재검토 문구",
        re.compile(r"생시.{0,24}(?:다시|재검토|살펴)|출생\s*시각.{0,24}(?:다시|재검토|살펴)"),
    ),
)


def unknown_time_provenance_lint(
    text: str,
    *,
    birth_time_mode: object | None,
    provenance: object | None,
    page: int | None = None,
    source: str = "content",
) -> list[dict[str, object]]:
    """고객 가시 문자열과 출처 메타를 함께 검사한다.

    known-time 문안은 이 게이트 때문에 바뀌지 않는다. three-pillar에서는 정확 고지 자체를
    허용하되, 고지 밖의 시각·시주·자미·네 기둥 사실은 전부 차단한다.
    """

    if not is_three_pillar_mode(birth_time_mode):
        return []
    out = provenance_contract_lint(
        provenance,
        birth_time_mode=birth_time_mode,
        source=source,
    )
    # 정확 고지 안의 '출생시각'은 정책 설명이지 실제 시각값이 아니다. 나머지 텍스트만
    # 금지 패턴으로 검사해 고지 자체가 게이트에 걸리는 항진을 막는다.
    scan_text = str(text or "").replace(THREE_PILLAR_NOTICE, "")
    for rule, token, pattern in _FORBIDDEN_TEXT_RULES:
        count = len(pattern.findall(scan_text))
        if count:
            out.append(_finding(rule, token, count=count, page=page, source=source))
    return out


def report_unknown_time_provenance_lint(
    sections: Iterable[object],
    *,
    birth_time_mode: object | None,
    provenance: object | None,
    source: str = "render_preflight",
) -> list[dict[str, object]]:
    """Report23/SimpleNamespace 섹션 전부를 같은 정책으로 검사한다."""

    if not is_three_pillar_mode(birth_time_mode):
        return []
    # provenance 오류는 섹션마다 중복하지 않고 한 번만 반환한다.
    out = provenance_contract_lint(
        provenance,
        birth_time_mode=birth_time_mode,
        source=source,
    )
    for section in sections:
        text = getattr(section, "final_text", "") or ""
        # 섹션 단위 사전검사는 실제 PDF page를 알 수 없으므로 page=None을 유지한다.
        section_hits = unknown_time_provenance_lint(
            text,
            birth_time_mode=birth_time_mode,
            provenance=None,
            source=f"{source}:{getattr(section, 'id', 'unknown')}",
        )
        # 위 호출은 provenance=None 오류를 포함하므로 텍스트 규칙만 합친다.
        out.extend(hit for hit in section_hits if hit["rule"] not in PROVENANCE_RULE_IDS)
    return out


def assert_unknown_time_provenance_clean(
    sections: Iterable[object],
    *,
    birth_time_mode: object | None,
    provenance: object | None,
    source: str = "render_preflight",
) -> None:
    hits = report_unknown_time_provenance_lint(
        sections,
        birth_time_mode=birth_time_mode,
        provenance=provenance,
        source=source,
    )
    if hits:
        rules = ",".join(sorted({str(hit["rule"]) for hit in hits}))
        raise ValueError(f"unknown-time provenance gate failed: {rules}")
