# -*- coding: utf-8 -*-
"""P2 명리(사주) 풀세트 — P1 보정시각(진태양시) 기반 lunar-python EightChar.

사실값은 lunar-python에서만 산출(추정 금지). 절입 기준 연·월주 경계는
Skyfield(solarterms)와 교차검증해 분 단위 불일치를 플래그한다.
자시 정책은 P1 enum을 권위로 두고 lunar-python 시지와 다르면 충돌을 '표면화'(단정 금지).
"""

from __future__ import annotations

from datetime import timezone
from typing import Optional

from lunar_python import Solar
from pydantic import BaseModel, Field

from ..input.time_correction import CorrectedTime
from ..config import myeongni_shinsal
from . import advanced, shinsal as shinsal_mod, solarterms

_ELEM = {  # 천간/지지 → 오행
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
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
    "申": "金",
    "酉": "金",
    "子": "水",
    "亥": "水",
}


class Pillar(BaseModel):
    gan: str
    zhi: str
    ganzhi: str
    hide_gan: list[str] = Field(default_factory=list)  # 지장간
    shishen_gan: str = ""  # 천간 십성
    shishen_zhi: list[str] = Field(default_factory=list)  # 지지 십성
    dishi: str = ""  # 십이운성
    nayin: str = ""  # 납음


class DaYunItem(BaseModel):
    start_age: int
    end_age: int
    start_year: int
    ganzhi: str


class ShinsalHit(BaseModel):
    name: str  # 신살 한국어명
    pillar: str  # year|month|day|hour
    basis: str = ""  # 검수·trace 근거 라벨


class Myeongni(BaseModel):
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar
    day_master: str  # 일간(日主)
    elements: dict[str, int]  # 오행 분포(8자 기준)
    daewoon_count: int  # 대운수
    daewoon_forward: bool  # 순행 여부
    daewoon: list[DaYunItem]
    ming_gong_nayin: str = ""
    shen_gong_nayin: str = ""
    # 심화 계산(advanced): 격국·억부용신·전통신살·세운/월운
    geukguk: str = ""  # 격국 라벨
    geukguk_note: str = ""
    singang: str = ""  # 신강|중화|신약|판정 불가
    singang_score: int = 0
    yongshin_eokbu: str = ""  # 억부 방식 참고 용신(라벨)
    yongshin_axis: str = ""
    yongshin_method: str = "억부"
    shinsal: list[str] = Field(default_factory=list)  # 전통 신살 한국어명(detail 파생, 하위호환)
    shinsal_detail: list[ShinsalHit] = Field(default_factory=list)  # 기둥별 신살(근거 포함)
    twelve_shinsal: dict[str, str] = Field(default_factory=dict)  # 기둥→12신살명(Phase B)
    gongmang: dict[str, list[str]] = Field(default_factory=dict)  # 기둥→공망 지지(Phase B)
    shinsal_profile: str = ""  # 적용 신살 학파 프로파일(감사 라벨)
    seun: list[tuple[int, str]] = Field(default_factory=list)  # (연, 간지)
    worun: list[tuple[str, str]] = Field(default_factory=list)  # (월, 간지)
    # 검증·정직성 플래그
    month_branch_crosscheck_ok: bool
    month_branch_lunar: str
    month_branch_skyfield: str
    hour_branch_p1_policy: str  # P1 진태양시·자시정책 시지
    hour_branch_conflict: bool  # lunar-python 시지와 불일치 여부
    note: str = ""


def _pillar(ec, who: str) -> Pillar:
    g = getattr(ec, f"get{who}")()
    return Pillar(
        gan=g[0],
        zhi=g[1],
        ganzhi=g,
        hide_gan=list(getattr(ec, f"get{who}HideGan")()),
        shishen_gan=getattr(ec, f"get{who}ShiShenGan")(),
        shishen_zhi=list(getattr(ec, f"get{who}ShiShenZhi")()),
        dishi=getattr(ec, f"get{who}DiShi")(),
        nayin=getattr(ec, f"get{who}NaYin")(),
    )


def build(ct: CorrectedTime, *, is_male: bool, ref_year: int | None = None) -> Myeongni:
    ts = ct.true_solar  # 진태양시(보정 완료)
    solar = Solar.fromYmdHms(
        ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second if ts.second else 0
    )
    ec = solar.getLunar().getEightChar()

    pillars = {w: _pillar(ec, w) for w in ("Year", "Month", "Day", "Time")}

    elements: dict[str, int] = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for p in pillars.values():
        for ch in (p.gan, p.zhi):
            if ch in _ELEM:
                elements[_ELEM[ch]] += 1

    # 대운 (남=1, 여=0; sect=1 기본 流派) — 방향은 시퀀스로 판정(단정 회피)
    yun = ec.getYun(1 if is_male else 0, 1)
    dy = yun.getDaYun()
    # 起運 나이(대운수) = getStartYear(). 한국 관행은 대운수=만나이 시작(레퍼런스 만세력 일치).
    # lunar-python d.getStartAge()는 起運 캘린더연도의 중국식 세는나이(虚岁)라 대운수와 +1~2 어긋남
    #   → 사용 금지. start_age = 대운수 + 10*순번 으로 도출(daewoon_count 와 내부 정합).
    qiyun = yun.getStartYear()
    _dy_items = [d for d in dy[1:9] if d.getGanZhi()]
    daewoon = [
        DaYunItem(
            start_age=qiyun + 10 * i,
            end_age=qiyun + 10 * i + 9,
            start_year=d.getStartYear(),
            ganzhi=d.getGanZhi(),
        )
        for i, d in enumerate(_dy_items)
    ]
    # 순행/역행: 60갑자 인덱스 증감으로 판정
    SX = "甲乙丙丁戊己庚辛壬癸"

    def gz_idx(gz: str) -> int:
        return SX.index(gz[0])

    forward = True
    if len(daewoon) >= 2:
        diff = (gz_idx(daewoon[1].ganzhi) - gz_idx(daewoon[0].ganzhi)) % 10
        forward = diff == 1

    # 절입 기준 월지 교차검증 (lunar-python vs Skyfield)
    utc = ct.utc.replace(tzinfo=None)
    sky_branch, _, _ = solarterms.month_pillar_branch(utc)
    lunar_month_zhi = pillars["Month"].zhi
    xcheck_ok = sky_branch == lunar_month_zhi

    hour_conflict = ct.hour_branch != pillars["Time"].zhi

    # 심화 계산 (결정론; 세운/월운은 lunar-python 출력 노출)
    dm = ec.getDayGan()
    ge, ge_note = advanced.geukguk(pillars["Month"], dm)
    eb = advanced.eokbu(pillars, dm)
    sal_profile = myeongni_shinsal()
    sal_hits = shinsal_mod.evaluate(pillars, dm, sal_profile)
    sal = shinsal_mod.flat_names(sal_hits)
    sal_detail = [ShinsalHit(name=h.name, pillar=h.pillar, basis=h.basis) for h in sal_hits]
    twelve = shinsal_mod.twelve_shinsal(pillars, sal_profile)
    gong = shinsal_mod.gongmang(pillars["Year"].ganzhi, pillars["Day"].ganzhi, sal_profile)
    seun, worun = advanced.seun_worun(yun, ref_year)

    return Myeongni(
        year=pillars["Year"],
        month=pillars["Month"],
        day=pillars["Day"],
        hour=pillars["Time"],
        day_master=ec.getDayGan(),
        elements=elements,
        daewoon_count=yun.getStartYear(),
        daewoon_forward=forward,
        daewoon=daewoon,
        ming_gong_nayin=ec.getMingGongNaYin(),
        shen_gong_nayin=ec.getShenGongNaYin(),
        geukguk=ge,
        geukguk_note=ge_note,
        singang=eb["label"],
        singang_score=eb["score"],
        yongshin_eokbu=eb["yongshin"],
        yongshin_axis=eb["axis"],
        shinsal=sal,
        shinsal_detail=sal_detail,
        twelve_shinsal=twelve,
        gongmang=gong,
        shinsal_profile=str(sal_profile.get("profile", "default")),
        seun=seun,
        worun=worun,
        month_branch_crosscheck_ok=xcheck_ok,
        month_branch_lunar=lunar_month_zhi,
        month_branch_skyfield=sky_branch,
        hour_branch_p1_policy=ct.hour_branch,
        hour_branch_conflict=hour_conflict,
        note=("월지 lunar↔Skyfield 불일치 — 절입 경계 재검토 필요" if not xcheck_ok else ""),
    )
