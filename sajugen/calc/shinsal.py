# -*- coding: utf-8 -*-
"""신살(神煞) 산출 — 표 기반 결정론 레지스트리 + 기둥별(per-pillar) 평가.

설계(docs/12 조사·docs/03 §1 결정표):
- 신살은 보조 색채. 길흉·시기 단정 근거 아님(절대규칙 9·11·12). 문안 계층에서 비단정.
- 표 데이터 = 코드 상수(검증 대상). 학파 분기 스위치만 config(rule_profile.yaml myeongni_shinsal).
- lunar-python getDayJiShen/XiongSha(택일 신살)는 사주 신살과 다른 체계 → 사용 금지(calc.md).
- 공망은 lunar-python EightChar API(sect=2 고정, 야자시가 JST_2300과 어긋남) 대신 자체 산술.
  입력을 파이프라인 확정 간지 문자열로 받아 자시정책과 무조건 정합(docs/03 §1 공망 행).

산출 단위: Hit(name, pillar, basis). myeongni 가 pydantic ShinsalHit 로 매핑하고,
평탄 shinsal 리스트(하위호환)는 ORDER 순서로 detail 에서 파생한다.
"""

from __future__ import annotations

from dataclasses import dataclass

# 기둥 키: lunar-python who → 모델 필드명(소문자)
PILLAR_KO = {"Year": "year", "Month": "month", "Day": "day", "Time": "hour"}
_PILLAR_LABEL = {"year": "년", "month": "월", "day": "일", "hour": "시"}

# 평탄 출력 안정 순서(하위호환: 기존 7종 우선, 신규는 뒤에 추가)
ORDER = [
    "천을귀인",
    "도화살",
    "역마살",
    "화개살",
    "양인",
    "괴강",
    "백호",
    # --- Phase B 확장(docs/12 §3-1 채택분) ---
    "문창귀인",
    "학당귀인",
    "금여",
    "암록",
    "태극귀인",
    "천문성",
    "고신살",
    "과숙살",
]

# 정책 기본값(docs/03 §1, config 부재 시 폴백과 동일)
DEFAULT_PROFILE = {
    "profile": "default",
    "goegang_scope": "day_only",  # day_only(현행) | all_pillars
    "samhap_axis": "both",  # day_zhi | year_zhi | both — 도화·역마·화개·12신살 공유
    "twelve_axis": "both",  # year_zhi | day_zhi | both
    "gongmang_display": "year_day",  # year_day | day_only
}

# --- 일간 기준 길신 표 (지지 집합) ---
_CHEONEUL = {  # 천을귀인: 일간 → 지지(주류 표, 辰戌 제외)
    "甲": {"丑", "未"},
    "戊": {"丑", "未"},
    "庚": {"丑", "未"},
    "乙": {"子", "申"},
    "己": {"子", "申"},
    "丙": {"亥", "酉"},
    "丁": {"亥", "酉"},
    "壬": {"卯", "巳"},
    "癸": {"卯", "巳"},
    "辛": {"寅", "午"},
}
_YANGIN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}  # 양간 양인(본령)

# --- 삼합국 → (도화=왕지, 역마=충지, 화개=묘지) 대상 지지 ---
_SAMHAP = {
    frozenset({"申", "子", "辰"}): ("酉", "寅", "辰"),
    frozenset({"寅", "午", "戌"}): ("卯", "申", "戌"),
    frozenset({"巳", "酉", "丑"}): ("午", "亥", "丑"),
    frozenset({"亥", "卯", "未"}): ("子", "巳", "未"),
}

# --- 일주/간지 기준 ---
# 괴강: 현대 통용형 4종(docs/03 §1). 고전 4주설(戊戌 포함·壬戌 제외)과 차이는 note.
_GOEGANG = {"庚辰", "庚戌", "壬辰", "壬戌"}
_BAEKHO = {"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"}  # 백호 7종


@dataclass
class Hit:
    name: str
    pillar: str  # year|month|day|hour
    basis: str  # 검수·trace 근거 라벨


def _group_targets(zhi: str):
    """지지가 속한 삼합국의 (도화, 역마, 화개) 대상. 없으면 None."""
    for grp, targets in _SAMHAP.items():
        if zhi in grp:
            return targets
    return None


def _samhap_axes(year_zhi: str, day_zhi: str, axis: str) -> list[tuple[str, str]]:
    """삼합 기준 축 → [(축라벨, 기준지지)] 목록(중복 그룹 제거)."""
    refs: list[tuple[str, str]] = []
    if axis in ("day_zhi", "both"):
        refs.append(("일지", day_zhi))
    if axis in ("year_zhi", "both"):
        refs.append(("년지", year_zhi))
    # 같은 삼합국이면 한 번만(년지·일지가 동일 국이면 중복 산출 방지)
    seen: set = set()
    out: list[tuple[str, str]] = []
    for label, z in refs:
        grp = next((g for g in _SAMHAP if z in g), None)
        if grp is None or grp in seen:
            continue
        seen.add(grp)
        out.append((label, z))
    return out


def evaluate(pillars: dict, day_master: str, profile: dict | None = None) -> list[Hit]:
    """기둥별 신살 산출. pillars = {"Year"/"Month"/"Day"/"Time": Pillar}."""
    p = {**DEFAULT_PROFILE, **(profile or {})}
    items = [(PILLAR_KO[w], pillars[w]) for w in ("Year", "Month", "Day", "Time")]
    day_zhi = pillars["Day"].zhi
    year_zhi = pillars["Year"].zhi
    hits: list[Hit] = []

    # 천을귀인 — 일간 기준, 4기둥 지지
    target = _CHEONEUL.get(day_master, set())
    for ko, pil in items:
        if pil.zhi in target:
            hits.append(Hit("천을귀인", ko, f"일간 {day_master} → {_PILLAR_LABEL[ko]}지 {pil.zhi}"))

    # 도화·역마·화개 — 삼합 기준(축 정책)
    for label, ref in _samhap_axes(year_zhi, day_zhi, p["samhap_axis"]):
        targets = _group_targets(ref)
        if not targets:
            continue
        do, yeok, hwa = targets
        for nm, tz in (("도화살", do), ("역마살", yeok), ("화개살", hwa)):
            for ko, pil in items:
                if pil.zhi == tz:
                    hits.append(Hit(nm, ko, f"{label} {ref} 삼합 → {_PILLAR_LABEL[ko]}지 {tz}"))

    # 양인 — 일간(양간) 기준
    yi = _YANGIN.get(day_master)
    if yi:
        for ko, pil in items:
            if pil.zhi == yi:
                hits.append(Hit("양인", ko, f"일간 {day_master} → {_PILLAR_LABEL[ko]}지 {yi}"))

    # 괴강 — 일주(또는 전 기둥) 간지
    if p["goegang_scope"] == "all_pillars":
        for ko, pil in items:
            if pil.ganzhi in _GOEGANG:
                hits.append(Hit("괴강", ko, f"{_PILLAR_LABEL[ko]}주 {pil.ganzhi}"))
    else:
        if pillars["Day"].ganzhi in _GOEGANG:
            hits.append(Hit("괴강", "day", f"일주 {pillars['Day'].ganzhi}"))

    # 백호 — 전 기둥 간지
    for ko, pil in items:
        if pil.ganzhi in _BAEKHO:
            hits.append(Hit("백호", ko, f"{_PILLAR_LABEL[ko]}주 {pil.ganzhi}"))

    return _dedup(hits)


def _dedup(hits: list[Hit]) -> list[Hit]:
    """(name, pillar) 중복 제거 + 이름 ORDER·기둥 순서 안정 정렬."""
    seen: set = set()
    uniq: list[Hit] = []
    for h in hits:
        key = (h.name, h.pillar)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    pil_order = {"year": 0, "month": 1, "day": 2, "hour": 3}
    name_order = {n: i for i, n in enumerate(ORDER)}
    uniq.sort(key=lambda h: (name_order.get(h.name, 999), pil_order.get(h.pillar, 9)))
    return uniq


def flat_names(hits: list[Hit]) -> list[str]:
    """하위호환 평탄 리스트 — ORDER 순서, 이름 중복 제거."""
    present = {h.name for h in hits}
    return [n for n in ORDER if n in present]
