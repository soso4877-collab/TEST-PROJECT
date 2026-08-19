# -*- coding: utf-8 -*-
"""상대방 명식 계산 — 결정론 엔진 전용(LLM 위임 금지, 절대규칙 1).

신청 고민에 적힌 상대 생년월일로 연·월·일주를 계산하고, 본인 명식과의 관계
(십성·천간합·일지 합충·반합·부족 오행 보완)를 사실 슬롯으로 산출한다.
시각 미상(질문에 사실상 없음) = 정오로 계산하되 시주는 결과에서 제외(절대규칙 8 정신).
시각 미상 + 신고 날짜 안 월건 전환 = `ym_time_dependent` 로 표시하고 연·월주를 확정 사실로
쓰지 않는다(절대규칙 8-1). 판정은 `three_pillar.ensure_unambiguous_civil_date` 재사용.
성별 미상이라 대운은 계산하지 않는다(양남음녀 방향 결정 불가).
"""

from __future__ import annotations

from lunar_python.util import LunarUtil
from pydantic import BaseModel, Field

from ..input import time_correction as tc
from .myeongni import split_axis_eight_char
from .three_pillar import NeedsInfoTimeBoundary, ensure_unambiguous_civil_date

_ELEM = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}
# 천간합(五合) — 나의 일간과 상대 일간
_GAN_HAP = {
    frozenset("甲己"): "갑기합(토)",
    frozenset("乙庚"): "을경합(금)",
    frozenset("丙辛"): "병신합(수)",
    frozenset("丁壬"): "정임합(목)",
    frozenset("戊癸"): "무계합(화)",
}
# 일지 육합·충 (calc/shinsal.py 표 스타일)
_ZHI_LIUHE = {
    frozenset("子丑"),
    frozenset("寅亥"),
    frozenset("卯戌"),
    frozenset("辰酉"),
    frozenset("巳申"),
    frozenset("午未"),
}
_ZHI_CHONG = {
    frozenset("子午"),
    frozenset("丑未"),
    frozenset("寅申"),
    frozenset("卯酉"),
    frozenset("辰戌"),
    frozenset("巳亥"),
}
# 일지 긴장 관계(docs/03 §1-1) — pairwise 완결 관계만 산출한다.
# 삼형(寅巳申·丑戌未)은 두 지지만으로 맥락이 완결되지 않아 이번 범위에서 제외한다.
_ZHI_HAI = {
    frozenset("子未"),
    frozenset("丑午"),
    frozenset("寅巳"),
    frozenset("卯辰"),
    frozenset("申亥"),
    frozenset("酉戌"),
}
_ZHI_PO = {
    frozenset("子酉"),
    frozenset("卯午"),
    frozenset("巳申"),
    frozenset("寅亥"),
    frozenset("丑辰"),
    frozenset("戌未"),
}
_ZHI_WONJIN = {
    frozenset("子未"),
    frozenset("丑午"),
    frozenset("寅酉"),
    frozenset("卯申"),
    frozenset("辰亥"),
    frozenset("巳戌"),
}
_ZHI_SELF_XING = set("辰午酉亥")
_ZHI_XING_MUTUAL = {frozenset("子卯")}
# 삼합국 — 두 지지가 같은 국이면 반합(기운이 살아나는 구조, 샘플 '화의 기운이 더 살아나는')
_SAMHAP = [
    (set("申子辰"), "수"),
    (set("寅午戌"), "화"),
    (set("巳酉丑"), "금"),
    (set("亥卯未"), "목"),
]


class PartnerPillar(BaseModel):
    gan: str
    zhi: str
    ganzhi: str


class PartnerFacts(BaseModel):
    """상대방 명식 사실 슬롯 — LLM에는 파생값만 전달(생년월일 원본 비전달, 절대규칙 17)."""

    hour_known: bool = False
    # 시각 미상 + 신고 날짜 안에서 월건 전환 = 연·월주가 시각에 따라 갈린다(절대규칙 8-1).
    # True 면 표시 계층과 factcheck 허용 토큰 양쪽에서 연·월주를 뺀다(필드 값 자체는 담는다).
    ym_time_dependent: bool = False
    year: PartnerPillar
    month: PartnerPillar
    day: PartnerPillar
    hour: PartnerPillar | None = None  # hour_known=False면 None(시주 제외)
    day_gan_elem_ko: str  # 상대 일간 오행(한글: 목화토금수)
    shishen_to_me: str  # 나의 일간 기준 상대 일간의 십성(한자 — 표시 계층에서 한글化)
    gan_hap: str = ""  # 천간합(있을 때)
    ilji_relation: str = ""  # 일지 육합/충(있을 때)
    ilji_hai: str = ""  # 일지 해(있을 때)
    ilji_po: str = ""  # 일지 파(있을 때)
    ilji_wonjin: str = ""  # 일지 원진(있을 때)
    ilji_xing: str = ""  # 일지 형(자형/상형, pairwise 한정)
    ilji_banhap: str = ""  # 일지 삼합 반합(있을 때, 살아나는 오행)
    complements_elems_ko: list[str] = Field(default_factory=list)  # 보완하는 나의 부족 오행(한글)
    matches_my_yongshin: bool = False
    note: str = (
        "상대 명식은 신청 글의 생년월일 기준, 시간 미상으로 시주 제외·대운 미산출. "
        "일지 형은 자형·子卯 상형만 산출하고 삼형 완전판은 범위 밖으로 둔다"
    )


_ELEM_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def partner_pillars(
    year: int,
    month: int,
    day: int,
    hour: int | None,
    minute: int = 0,
    *,
    my_day_gan: str,
    my_day_zhi: str,
    my_elements: dict[str, int],
    my_yongshin: str = "",
) -> PartnerFacts:
    """상대 명식 계산 + 본인과의 관계 사실. calc/myeongni.build 와 **같은 헬퍼**로 축을 만든다.

    시각축(2026-08-17 교정, docs/03 결정표): 연주·월주 = 절대축(lunar-python 절기표 프레임 CST),
    일주·시주·자시정책 = 국지축(진태양시). 자시정책 기본 JST_2300 고정(policy 인자 없음),
    대운은 성별 미상으로 산출하지 않는다.
    축 프레임 상수·분류표는 `calc/myeongni` 단일 소스이며 여기서 재계산하지 않는다.
    시각 미상이고 신고 날짜 안에서 월건이 바뀌면 `ym_time_dependent=True` 로 표시한다
    (절대규칙 8-1 — 판정 술어는 `three_pillar.ensure_unambiguous_civil_date` 단일 소스).
    """
    hour_known = hour is not None
    # 시각 미상일 때만 판정한다(시각을 알면 연·월주는 확정 사실이다). 판정 술어는 본인 경로가
    # 쓰는 three_pillar 단일 소스를 재사용한다 — 월건 비교를 여기 복제하면 불변식이 2곳이 된다.
    # 이 함수는 술어가 아니라 fail-closed 함수라, 예외를 True 로 매핑해서 플래그를 얻는다.
    ym_time_dependent = False
    if not hour_known:
        try:
            ensure_unambiguous_civil_date(year, month, day)
        except NeedsInfoTimeBoundary:
            ym_time_dependent = True
    ct = tc.correct(year, month, day, hour if hour_known else 12, minute if hour_known else 0)
    ec = split_axis_eight_char(ct)
    # 자시 정책 반영(T2.1/P0-1, myeongni 와 동일): day_offset=1 이면 일주만 익일 전환.
    if ct.day_offset:
        ec.setSect(1)

    def _p(who: str) -> PartnerPillar:
        g = getattr(ec, f"get{who}")()
        return PartnerPillar(gan=g[0], zhi=g[1], ganzhi=g)

    py, pm, pd = _p("Year"), _p("Month"), _p("Day")
    ph = _p("Time") if hour_known else None

    # 나의 일간 기준 상대 일간 십성 — lunar-python 검증 표 재사용
    shishen = LunarUtil.SHI_SHEN.get(my_day_gan + pd.gan, "")

    gan_hap = _GAN_HAP.get(frozenset(my_day_gan + pd.gan), "") if my_day_gan != pd.gan else ""

    pair = frozenset(my_day_zhi + pd.zhi)
    if my_day_zhi == pd.zhi:
        ilji = ""
    elif pair in _ZHI_LIUHE:
        ilji = "육합"
    elif pair in _ZHI_CHONG:
        ilji = "충"
    else:
        ilji = ""
    ilji_hai = "해" if pair in _ZHI_HAI else ""
    ilji_po = "파" if pair in _ZHI_PO else ""
    ilji_wonjin = "원진" if pair in _ZHI_WONJIN else ""
    if my_day_zhi == pd.zhi and my_day_zhi in _ZHI_SELF_XING:
        ilji_xing = "자형"
    elif pair in _ZHI_XING_MUTUAL:
        ilji_xing = "상형"
    else:
        ilji_xing = ""
    banhap = ""
    if my_day_zhi != pd.zhi:
        for group, elem_ko in _SAMHAP:
            if my_day_zhi in group and pd.zhi in group:
                banhap = elem_ko
                break

    # 상대 명식(시 미상이면 3주)이 품은 오행 — 나의 부족 오행(0~최소치) 보완 여부.
    # 연·월주가 비단정이면 그 오행을 근거로 쓸 수 없으므로 일주(간+지)만으로 산출한다.
    elem_pillars = (pd,) if ym_time_dependent else (py, pm, pd) + ((ph,) if ph else ())
    partner_elems: set[str] = set()
    for p in elem_pillars:
        partner_elems.add(_ELEM[p.gan])
        partner_elems.add(_ELEM[p.zhi])
    weak = [e for e, n in my_elements.items() if n == 0]
    if not weak:
        mn = min(my_elements.values())
        weak = [e for e, n in my_elements.items() if n == mn]
    complements = [_ELEM_KO[e] for e in weak if e in partner_elems]

    d_elem_ko = _ELEM_KO[_ELEM[pd.gan]]
    matches = bool(my_yongshin) and my_yongshin.strip().startswith(d_elem_ko)

    return PartnerFacts(
        hour_known=hour_known,
        ym_time_dependent=ym_time_dependent,
        year=py,
        month=pm,
        day=pd,
        hour=ph,
        day_gan_elem_ko=d_elem_ko,
        shishen_to_me=shishen,
        gan_hap=gan_hap,
        ilji_relation=ilji,
        ilji_hai=ilji_hai,
        ilji_po=ilji_po,
        ilji_wonjin=ilji_wonjin,
        ilji_xing=ilji_xing,
        ilji_banhap=banhap,
        complements_elems_ko=complements,
        matches_my_yongshin=matches,
    )
