# -*- coding: utf-8 -*-
"""생시 미상용 삼주(연·월·일) 계산과 12시지 민감도 축약.

삼주의 기준 날짜는 신고된 민간 날짜다. 시각 후보는 기존 값을 고르는 용도가 아니라
시간 의존 사실을 찾아 억제하는 용도로만 계산하며, 후보 원문은 결과에 남기지 않는다.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from lunar_python import Solar
from pydantic import BaseModel, Field

from ..config import myeongni_shinsal
from . import advanced, kasi, shinsal as shinsal_mod, solarterms
from .myeongni import Pillar, ShinsalHit, _pillar

THREE_PILLAR_SCHEMA_VERSION = 1
_KST = ZoneInfo("Asia/Seoul")
_CANDIDATE_HOURS = tuple(range(0, 24, 2))
_EXPECTED_BRANCHES = tuple("子丑寅卯辰巳午未申酉戌亥")


class NeedsInfoTimeBoundary(ValueError):
    """신고 날짜 안에 절입이 있어 시각 없이 연·월주를 확정할 수 없음."""

    code = "NEEDS_INFO_TIME_BOUNDARY"

    def __init__(self) -> None:
        # 예외가 로그에 남아도 생년월일이 노출되지 않도록 날짜를 넣지 않는다.
        super().__init__("신고 날짜 안에 절입 경계가 있어 출생시각 확인이 필요합니다")


class FactProvenance(str, Enum):
    """고객 문안과 LLM에 전달할 수 있는 사실 출처."""

    THREE_PILLAR = "three_pillar"
    TIME_INVARIANT = "time_invariant"
    CALENDAR_FLOW = "calendar_flow"


class ThreePillarProvenance(BaseModel):
    """후보 원문 없이 남기는 결정론 민감도 증거."""

    three_pillar_schema_version: int = THREE_PILLAR_SCHEMA_VERSION
    candidate_count: int = 12
    candidate_digest: str
    stable_fact_ids: list[str] = Field(default_factory=list)
    suppressed_fact_ids: list[str] = Field(default_factory=list)


class ThreePillarMyeongni(BaseModel):
    """시주가 구조적으로 존재하지 않는 삼주 결과.

    `hour`, `elements`, `singang`, `yongshin`, `daewoon` 필드를 일부러 만들지 않는다.
    소비자가 알려진 시각용 `Myeongni`처럼 사용하면 즉시 실패하도록 하는 계약이다.
    """

    year: Pillar
    month: Pillar
    day: Pillar
    day_master: str
    geukguk: str
    geukguk_note: str
    known_pillar_shinsal: list[ShinsalHit] = Field(default_factory=list)
    seun: list[tuple[int, str]] = Field(default_factory=list)
    worun: list[tuple[str, str]] = Field(default_factory=list)
    stable_facts: dict[str, Any] = Field(default_factory=dict)
    fact_sources: dict[str, FactProvenance] = Field(default_factory=dict)


class ThreePillarCrossCheck(BaseModel):
    """시각·자미 값 없이 유지하는 공통 계산 교차검증."""

    month_branch_ok: bool
    year_branch_ok: bool
    near_term_boundary: bool = False
    kasi_consistent: bool = True
    kasi_out_of_range: bool = False
    warnings: list[str] = Field(default_factory=list)


class ThreePillarCalculation(BaseModel):
    """엔진이 `ThreePillarSajuResult`로 감싸는 계산 전용 결과."""

    input_civil_date: str
    ref_year: int | None = None
    three_pillar: ThreePillarMyeongni
    crosscheck: ThreePillarCrossCheck
    provenance: ThreePillarProvenance


def _canonical(value: Any) -> str:
    """구조 전체를 비교하는 결정론 JSON 표현."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def reduce_candidate_facts(
    candidates: Sequence[dict[str, Any]],
    *,
    expected_count: int = 12,
) -> tuple[dict[str, Any], list[str], str]:
    """모든 후보에서 구조 전체가 같은 사실만 승격한다.

    한 후보에서 키가 빠지거나 값의 일부만 달라도 해당 fact ID 전체를 억제한다.
    반환값은 `(stable, suppressed_ids, digest)`이며 후보 원문은 반환하지 않는다.
    """

    if len(candidates) != expected_count:
        raise ValueError(f"candidate_count must be {expected_count}")

    keys = sorted({key for candidate in candidates for key in candidate})
    stable: dict[str, Any] = {}
    suppressed: list[str] = []
    for key in keys:
        if any(key not in candidate for candidate in candidates):
            suppressed.append(key)
            continue
        encoded = [_canonical(candidate[key]) for candidate in candidates]
        if len(set(encoded)) == 1:
            stable[key] = candidates[0][key]
        else:
            suppressed.append(key)

    # 후보 순서는 사실 의미가 없으므로, 동일 후보 집합이면 입력 순서가 달라도 digest가 같다.
    canonical_candidates = sorted(_canonical(candidate) for candidate in candidates)
    digest = hashlib.sha256(_canonical(canonical_candidates).encode("utf-8")).hexdigest()
    return stable, suppressed, digest


def _utc_bounds_of_civil_date(year: int, month: int, day: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, day, tzinfo=_KST)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return (
        start.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
        end.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
    )


def ensure_unambiguous_civil_date(year: int, month: int, day: int) -> None:
    """민간 날짜 안에서 월건(입춘 포함)이 바뀌면 fail-closed 한다."""

    start_utc, end_utc = _utc_bounds_of_civil_date(year, month, day)
    start_branch, _, _ = solarterms.month_pillar_branch(start_utc)
    end_branch, _, _ = solarterms.month_pillar_branch(end_utc)
    if start_branch != end_branch:
        raise NeedsInfoTimeBoundary()


def _base_eight_char(year: int, month: int, day: int):
    """경계가 제거된 신고 민간 날짜의 연·월·일주를 얻는다.

    정오는 날짜 안의 대표 계산점일 뿐 결과에 시각·시주로 저장되지 않는다.
    """

    return Solar.fromYmdHms(year, month, day, 12, 0, 0).getLunar().getEightChar()


def _candidate_hour_pillar(year: int, month: int, day: int, hour: int) -> Pillar:
    ec = Solar.fromYmdHms(year, month, day, hour, 0, 0).getLunar().getEightChar()
    return _pillar(ec, "Time")


def _calendar_flow(ref_year: int | None) -> tuple[list[tuple[int, str]], list[tuple[str, str]]]:
    """출생시각과 무관한 연·월 간지 흐름만 산출한다."""

    if ref_year is None:
        return [], []
    seun = [
        (year, Solar.fromYmd(year, 7, 1).getLunar().getYearInGanZhiByLiChun())
        for year in range(ref_year - 1, ref_year + 4)
    ]
    worun = [
        (
            f"{month}월",
            Solar.fromYmd(ref_year, month, 15).getLunar().getMonthInGanZhiExact(),
        )
        for month in range(1, 13)
    ]
    return seun, worun


def build(
    year: int,
    month: int,
    day: int,
    *,
    ref_year: int | None = None,
) -> ThreePillarCalculation:
    """신고 민간 날짜 기준 삼주와 12시지 민감도 메타를 계산한다."""

    ensure_unambiguous_civil_date(year, month, day)
    ec = _base_eight_char(year, month, day)
    base_pillars = {who: _pillar(ec, who) for who in ("Year", "Month", "Day")}
    day_master = ec.getDayGan()
    geukguk, geukguk_note = advanced.geukguk(base_pillars["Month"])
    sal_profile = myeongni_shinsal()

    candidates: list[dict[str, Any]] = []
    known_shinsal: list[ShinsalHit] | None = None
    for expected_branch, hour in zip(_EXPECTED_BRANCHES, _CANDIDATE_HOURS):
        hour_pillar = _candidate_hour_pillar(year, month, day, hour)
        if hour_pillar.zhi != expected_branch:
            raise RuntimeError("12시지 후보 생성 순서가 결정론 계약과 일치하지 않습니다")
        pillars = {**base_pillars, "Time": hour_pillar}

        elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        from .myeongni import _ELEM  # 기존 오행 정본을 재사용해 표 이중화를 막는다.

        for pillar in pillars.values():
            for char in (pillar.gan, pillar.zhi):
                if char in _ELEM:
                    elements[_ELEM[char]] += 1

        eokbu = advanced.eokbu(pillars, day_master)
        hits = shinsal_mod.evaluate(pillars, day_master, sal_profile)
        if known_shinsal is None:
            known_shinsal = [
                ShinsalHit(name=hit.name, pillar=hit.pillar, basis=hit.basis)
                for hit in hits
                if hit.pillar != "hour"
            ]

        candidates.append(
            {
                "elements": elements,
                "singang_yongshin": eokbu,
                "shinsal_detail": [
                    {"name": hit.name, "pillar": hit.pillar, "basis": hit.basis}
                    for hit in hits
                ],
                "twelve_shinsal": shinsal_mod.twelve_shinsal(pillars, sal_profile),
                "gongmang": shinsal_mod.gongmang(
                    base_pillars["Year"].ganzhi,
                    base_pillars["Day"].ganzhi,
                    sal_profile,
                ),
            }
        )

    candidate_stable, candidate_suppressed, candidate_digest = reduce_candidate_facts(candidates)
    seun, worun = _calendar_flow(ref_year)

    stable_facts: dict[str, Any] = {
        "pillar.year": base_pillars["Year"].model_dump(mode="json"),
        "pillar.month": base_pillars["Month"].model_dump(mode="json"),
        "pillar.day": base_pillars["Day"].model_dump(mode="json"),
        "day_master": day_master,
        "geukguk": {"label": geukguk, "note": geukguk_note},
        "known_pillar_shinsal": [item.model_dump(mode="json") for item in known_shinsal or []],
        "calendar_flow.seun": seun,
        "calendar_flow.worun": worun,
    }
    fact_sources = {
        fact_id: (
            FactProvenance.CALENDAR_FLOW
            if fact_id.startswith("calendar_flow.")
            else FactProvenance.THREE_PILLAR
        )
        for fact_id in stable_facts
    }
    for fact_id, value in candidate_stable.items():
        stable_id = f"candidate.{fact_id}"
        stable_facts[stable_id] = value
        fact_sources[stable_id] = FactProvenance.TIME_INVARIANT

    always_suppressed = {
        "hour_pillar",
        "ziwei",
        "daewoon",
        "current_daewoon",
        "elements_ranking",
        "singang",
        "yongshin",
    }
    suppressed_fact_ids = sorted(
        always_suppressed | {f"candidate.{fact_id}" for fact_id in candidate_suppressed}
    )
    stable_fact_ids = sorted(stable_facts)

    start_utc, _ = _utc_bounds_of_civil_date(year, month, day)
    noon_utc = start_utc + timedelta(hours=12)
    month_branch, _, _ = solarterms.month_pillar_branch(noon_utc)
    month_ok = month_branch == base_pillars["Month"].zhi
    ipchun = solarterms.solar_term_time(noon_utc.year, 315)
    sky_year = noon_utc.year if noon_utc >= ipchun else noon_utc.year - 1
    sky_year_zhi = "子丑寅卯辰巳午未申酉戌亥"[(sky_year - 4) % 12]
    year_ok = sky_year_zhi == base_pillars["Year"].zhi
    kasi_consistent, kasi_out_of_range = kasi.year_kasi_check(year)
    warnings: list[str] = []
    if not month_ok:
        warnings.append("월지 lunar↔Skyfield 불일치 — 계산 차단 필요")
    if not year_ok:
        warnings.append("연지 lunar↔Skyfield 불일치 — 계산 차단 필요")
    if not kasi_consistent:
        warnings.append("KASI 3원 교차 미지 불일치 — 계산 차단 필요")
    elif kasi_out_of_range:
        warnings.append("KASI 절기 캐시 범위 밖 — 2원 검증")

    return ThreePillarCalculation(
        input_civil_date=f"{year:04d}-{month:02d}-{day:02d}",
        ref_year=ref_year,
        three_pillar=ThreePillarMyeongni(
            year=base_pillars["Year"],
            month=base_pillars["Month"],
            day=base_pillars["Day"],
            day_master=day_master,
            geukguk=geukguk,
            geukguk_note=geukguk_note,
            known_pillar_shinsal=known_shinsal or [],
            seun=seun,
            worun=worun,
            stable_facts=stable_facts,
            fact_sources=fact_sources,
        ),
        crosscheck=ThreePillarCrossCheck(
            month_branch_ok=month_ok,
            year_branch_ok=year_ok,
            near_term_boundary=False,
            kasi_consistent=kasi_consistent,
            kasi_out_of_range=kasi_out_of_range,
            warnings=warnings,
        ),
        provenance=ThreePillarProvenance(
            candidate_digest=candidate_digest,
            stable_fact_ids=stable_fact_ids,
            suppressed_fact_ids=suppressed_fact_ids,
        ),
    )
