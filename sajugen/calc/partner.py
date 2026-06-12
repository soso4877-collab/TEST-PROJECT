# -*- coding: utf-8 -*-
"""상대방 명식 계산 — 결정론 엔진 전용(LLM 위임 금지, 절대규칙 1).

신청 고민에 적힌 상대 생년월일로 연·월·일주를 계산하고, 본인 명식과의 관계
(십성·천간합·일지 합충·반합·부족 오행 보완)를 사실 슬롯으로 산출한다.
시각 미상(질문에 사실상 없음) = 정오로 계산하되 시주는 결과에서 제외(절대규칙 8 정신).
성별 미상이라 대운은 계산하지 않는다(양남음녀 방향 결정 불가).
"""

from __future__ import annotations

from lunar_python import Solar
from lunar_python.util import LunarUtil
from pydantic import BaseModel, Field

from ..input import time_correction as tc

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
    year: PartnerPillar
    month: PartnerPillar
    day: PartnerPillar
    hour: PartnerPillar | None = None  # hour_known=False면 None(시주 제외)
    day_gan_elem_ko: str  # 상대 일간 오행(한글: 목화토금수)
    shishen_to_me: str  # 나의 일간 기준 상대 일간의 십성(한자 — 표시 계층에서 한글化)
    gan_hap: str = ""  # 천간합(있을 때)
    ilji_relation: str = ""  # 일지 육합/충(있을 때)
    ilji_banhap: str = ""  # 일지 삼합 반합(있을 때, 살아나는 오행)
    complements_elems_ko: list[str] = Field(default_factory=list)  # 보완하는 나의 부족 오행(한글)
    matches_my_yongshin: bool = False
    note: str = "상대 명식은 신청 글의 생년월일 기준, 시간 미상으로 시주 제외·대운 미산출"


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
    """상대 명식 계산 + 본인과의 관계 사실. calc/myeongni.build 와 동일 경로
    (진태양시 보정 → lunar-python EightChar), 자시정책 동일(JST_2300)."""
    hour_known = hour is not None
    ct = tc.correct(year, month, day, hour if hour_known else 12, minute if hour_known else 0)
    ts = ct.true_solar
    ec = (
        Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute, 0).getLunar().getEightChar()
    )

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
    banhap = ""
    if my_day_zhi != pd.zhi:
        for group, elem_ko in _SAMHAP:
            if my_day_zhi in group and pd.zhi in group:
                banhap = elem_ko
                break

    # 상대 명식(시 미상이면 3주)이 품은 오행 — 나의 부족 오행(0~최소치) 보완 여부
    partner_elems: set[str] = set()
    for p in (py, pm, pd) + ((ph,) if ph else ()):
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
        year=py,
        month=pm,
        day=pd,
        hour=ph,
        day_gan_elem_ko=d_elem_ko,
        shishen_to_me=shishen,
        gan_hap=gan_hap,
        ilji_relation=ilji,
        ilji_banhap=banhap,
        complements_elems_ko=complements,
        matches_my_yongshin=matches,
    )
