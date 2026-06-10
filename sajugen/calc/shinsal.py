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
    "samhap_axis": "both",  # day_zhi | year_zhi | both — 도화·역마·화개
    "twelve_axis": "day_zhi",  # day_zhi(현대 대세) | year_zhi — 12신살 기준 축
    "gongmang_display": "year_day",  # year_day | day_only
}

# 60갑자 산술용 인덱스 문자열
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"

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

# --- 일간 기준 길신 확장 표(docs/12 §2-1 채택분) ---
_MUNCHANG = {  # 문창귀인(식신 위치). A등급
    "甲": "巳",
    "乙": "午",
    "丙": "申",
    "丁": "酉",
    "戊": "申",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "寅",
    "癸": "卯",
}
_HAKDANG = {  # 학당귀인(장생지설). B등급 — note 동반
    "甲": "亥",
    "乙": "午",
    "丙": "寅",
    "丁": "酉",
    "戊": "寅",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "申",
    "癸": "卯",
}
_GEUMYEO = {  # 금여(건록+2). A등급
    "甲": "辰",
    "乙": "巳",
    "丙": "未",
    "丁": "申",
    "戊": "未",
    "己": "申",
    "庚": "戌",
    "辛": "亥",
    "壬": "丑",
    "癸": "寅",
}
_AMNOK = {  # 암록(건록의 육합). A등급
    "甲": "亥",
    "乙": "戌",
    "丙": "申",
    "丁": "未",
    "戊": "申",
    "己": "未",
    "庚": "巳",
    "辛": "辰",
    "壬": "寅",
    "癸": "丑",
}
_TAEGEUK = {  # 태극귀인(일간→지지 집합). B등급
    "甲": {"子", "午"},
    "乙": {"子", "午"},
    "丙": {"卯", "酉"},
    "丁": {"卯", "酉"},
    "戊": {"辰", "戌", "丑", "未"},
    "己": {"辰", "戌", "丑", "未"},
    "庚": {"寅", "亥"},
    "辛": {"寅", "亥"},
    "壬": {"巳", "申"},
    "癸": {"巳", "申"},
}

# 천문성(지지 자체, 강 그룹만 채택해 노이즈 억제). B등급
_CHEONMUN = {"卯", "戌", "亥", "未"}

# 고신살·과숙살: 년지 방국 기준(docs/12 §2-2). B등급
_GOSIN = {  # 년지 → 고신 지지
    "亥": "寅",
    "子": "寅",
    "丑": "寅",
    "寅": "巳",
    "卯": "巳",
    "辰": "巳",
    "巳": "申",
    "午": "申",
    "未": "申",
    "申": "亥",
    "酉": "亥",
    "戌": "亥",
}
_GWASUK = {  # 년지 → 과숙 지지
    "亥": "戌",
    "子": "戌",
    "丑": "戌",
    "寅": "丑",
    "卯": "丑",
    "辰": "丑",
    "巳": "辰",
    "午": "辰",
    "未": "辰",
    "申": "未",
    "酉": "未",
    "戌": "未",
}

# 12신살: 寅午戌국 기준 12지지 순서(겁살→화개). 다른 국은 회전.
_TWELVE_NAMES = [
    "겁살",
    "재살",
    "천살",
    "지살",
    "연살",
    "월살",
    "망신살",
    "장성살",
    "반안살",
    "역마살",
    "육해살",
    "화개살",
]
# 각 삼합국의 겁살 시작 지지(생지의 직전=절지)
_TWELVE_START = {
    frozenset({"寅", "午", "戌"}): "亥",
    frozenset({"申", "子", "辰"}): "巳",
    frozenset({"巳", "酉", "丑"}): "寅",
    frozenset({"亥", "卯", "未"}): "申",
}


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

    # --- 확장 길신(일간 기준 단일 지지) ---
    for nm, table in (
        ("문창귀인", _MUNCHANG),
        ("학당귀인", _HAKDANG),
        ("금여", _GEUMYEO),
        ("암록", _AMNOK),
    ):
        tz = table.get(day_master)
        if not tz:
            continue
        for ko, pil in items:
            if pil.zhi == tz:
                hits.append(Hit(nm, ko, f"일간 {day_master} → {_PILLAR_LABEL[ko]}지 {tz}"))

    # 태극귀인 — 일간 기준 지지 집합
    taegeuk = _TAEGEUK.get(day_master, set())
    for ko, pil in items:
        if pil.zhi in taegeuk:
            hits.append(Hit("태극귀인", ko, f"일간 {day_master} → {_PILLAR_LABEL[ko]}지 {pil.zhi}"))

    # 천문성 — 지지 자체(강 그룹)
    for ko, pil in items:
        if pil.zhi in _CHEONMUN:
            hits.append(Hit("천문성", ko, f"{_PILLAR_LABEL[ko]}지 {pil.zhi}(천문 지지)"))

    # 고신살·과숙살 — 년지 방국 기준
    gosin = _GOSIN.get(year_zhi)
    gwasuk = _GWASUK.get(year_zhi)
    for ko, pil in items:
        if gosin and pil.zhi == gosin:
            hits.append(Hit("고신살", ko, f"년지 {year_zhi} 방국 → {_PILLAR_LABEL[ko]}지 {gosin}"))
        if gwasuk and pil.zhi == gwasuk:
            hits.append(Hit("과숙살", ko, f"년지 {year_zhi} 방국 → {_PILLAR_LABEL[ko]}지 {gwasuk}"))

    return _dedup(hits)


def twelve_shinsal(pillars: dict, profile: dict | None = None) -> dict[str, str]:
    """12신살 — 기둥당 1개. 기준 축(일지/년지)의 삼합국으로 12지지를 순환 배정."""
    p = {**DEFAULT_PROFILE, **(profile or {})}
    ref = pillars["Day"].zhi if p["twelve_axis"] == "day_zhi" else pillars["Year"].zhi
    start = next((s for g, s in _TWELVE_START.items() if ref in g), None)
    if start is None:
        return {}
    base = _ZHI.index(start)
    pos = {_ZHI[(base + i) % 12]: _TWELVE_NAMES[i] for i in range(12)}
    return {PILLAR_KO[w]: pos[pillars[w].zhi] for w in ("Year", "Month", "Day", "Time")}


def _xunkong(ganzhi: str) -> list[str]:
    """순중공망(旬空) 산술 — 간지의 공망 2지지. lunar-python API 비의존."""
    g = _GAN.index(ganzhi[0])
    z = _ZHI.index(ganzhi[1])
    return [_ZHI[(z - g + 10) % 12], _ZHI[(z - g + 11) % 12]]


def gongmang(
    year_ganzhi: str, day_ganzhi: str, profile: dict | None = None
) -> dict[str, list[str]]:
    """공망 — 일주 기준 본령(+ 년주 병기). 입력=파이프라인 확정 간지(자시정책 정합)."""
    p = {**DEFAULT_PROFILE, **(profile or {})}
    out = {"day": _xunkong(day_ganzhi)}
    if p["gongmang_display"] == "year_day":
        out["year"] = _xunkong(year_ganzhi)
    return out


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
