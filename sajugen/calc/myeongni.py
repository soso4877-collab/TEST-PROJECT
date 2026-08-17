# -*- coding: utf-8 -*-
"""P2 명리(사주) 풀세트 — 두 시각축(절대축·국지축)을 분리한 lunar-python EightChar.

사실값은 lunar-python에서만 산출(추정 금지). 절입 기준 연·월주 경계는
Skyfield(solarterms)와 교차검증해 분 단위 불일치를 플래그한다.
자시 정책은 P1 enum을 권위로 두고 lunar-python 시지와 다르면 충돌을 '표면화'(단정 금지).

★ 불변식 — 시각축은 둘이고 산출마다 소속이 다르다 (2026-08-17 교정, docs/03 결정표):
  - **절대축**(연주·월주·대운·세운): 절기는 태양 황경이 특정 각도가 되는 '절대 시각'이라
    관측지 경도·균시차와 무관하다. 서울에서 나든 뉴욕에서 나든 입춘 순간은 같다.
  - **국지축**(일주·시주·자시 정책): 시지는 그 자리에서의 태양 시각각 문제라 진태양시가 맞다.
  이 둘을 한 축으로 뭉개면 절입 판정이 진태양시 보정량만큼 밀린다(구 결함).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from lunar_python import EightChar, Solar
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


# lunar-python 1.4.8 의 절기표(JieQiTable)는 **중국 표준시(UTC+8)** 로 적혀 있다. 시민 KST(UTC+9)나
# 진태양시를 그대로 넘기면 라이브러리가 절입을 60분 이르게 판정한다.
#   실측(2026-08-17): 2000 입춘 = KST 21:40:22 / CST 20:40:22 인데
#   Solar.fromYmdHms(2000,2,4,20,41)(=KST 20:41 로 읽힘)에서 이미 연주가 己卯→庚辰 로 넘어간다.
# 그래서 절입에 걸리는 산출(연주·월주·대운)만 UTC+8 프레임으로 환산해 넘긴다.
# ★ 이 상수를 지우면 다음 사람이 -60분 결함을 다시 만든다. 매직넘버로 두지 말 것.
LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS = 8

# _SplitAxisLunar 위임 규칙 — lunar-python 1.4.8 의 EightChar·Yun·DaYun·LiuNian·XiaoYun 이
# Lunar 에 실제로 호출하는 메서드 전체를 축별로 분류한 표(라이브러리 소스 전수 스캔, 버전 고정).
# 미분류 이름은 조용히 한쪽으로 새지 않도록 fail loud 한다(방법론 B-2 fail-closed).
_ABSOLUTE_AXIS_PREFIXES = ("getYear", "getMonth")  # 연·월주와 그 순공/납음
_ABSOLUTE_AXIS_NAMES = frozenset(
    {
        "getJieQiTable",  # 세운(입춘 기준 유년) 기준표
        "getNextJie",  # 대운 起運 = 다음 절입까지의 거리
        "getPrevJie",  # 대운 起運(역행) = 직전 절입까지의 거리
        "getSolar",  # 起運 거리 계산의 출생 기준점 · 대운 시작 연도
    }
)
_LOCAL_AXIS_PREFIXES = ("getDay", "getTime")  # 일주·시주(자시 정책 포함)


class _SplitAxisLunar:
    """연·월·절입은 절대축 Lunar 로, 일·시는 국지축 Lunar 로 위임하는 프록시.

    두 개의 EightChar 에서 기둥을 골라 담지 않고 **하나의 EightChar** 를 만드는 이유:
    십성(十神)·지세(十二運星)·명궁은 전부 '일간 기준' 파생값이라, 연·월주만 다른 인스턴스에서
    가져오면 그 인스턴스의 일간(자시 정책·날짜 경계로 달라질 수 있다)으로 십성이 계산돼
    일간과 어긋난 십성이 조용히 섞인다. 축을 Lunar 층에서 합치면 EightChar 가 언제나
    국지축 일간으로 파생값을 계산하므로 이 사각이 구조적으로 닫힌다.
    """

    __slots__ = ("_absolute", "_local")

    def __init__(self, absolute, local) -> None:
        self._absolute = absolute
        self._local = local

    def __getattr__(self, name: str):
        if name.startswith("_"):  # 슬롯·던더는 프록시 대상 아님
            raise AttributeError(name)
        if name in _ABSOLUTE_AXIS_NAMES or name.startswith(_ABSOLUTE_AXIS_PREFIXES):
            return getattr(self._absolute, name)
        if name.startswith(_LOCAL_AXIS_PREFIXES):
            return getattr(self._local, name)
        raise RuntimeError(
            f"_SplitAxisLunar: 축 미분류 Lunar 메서드 '{name}' — 절대축/국지축 배정을 "
            "먼저 결정해야 한다(조용한 축 혼입 차단)"
        )


def _split_axis_eight_char(ct: CorrectedTime) -> EightChar:
    """CorrectedTime 하나에서 절대축·국지축을 함께 물린 EightChar 를 만든다."""
    ts = ct.true_solar  # 국지축: 진태양시(경도차+균시차 보정 완료)
    # 절대축: 출생의 절대 순간(UTC)을 lunar-python 절기표 프레임(CST)으로 환산.
    cst = ct.utc.replace(tzinfo=None) + timedelta(
        hours=LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS
    )
    local_lunar = Solar.fromYmdHms(
        ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second if ts.second else 0
    ).getLunar()
    absolute_lunar = Solar.fromYmdHms(
        cst.year, cst.month, cst.day, cst.hour, cst.minute, cst.second if cst.second else 0
    ).getLunar()
    return EightChar(_SplitAxisLunar(absolute_lunar, local_lunar))


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
    year_branch_crosscheck_ok: bool = True  # 입춘 기준 연지 lunar↔Skyfield (F-2)
    year_branch_lunar: str = ""
    year_branch_skyfield: str = ""
    hour_branch_p1_policy: str  # P1 진태양시·자시정책 시지
    hour_branch_conflict: bool  # lunar-python 시지와 불일치 여부
    note: str = ""


def current_daewoon(m: "Myeongni", ref_year: int | None) -> Optional[DaYunItem]:
    """기준 연도(ref_year)에 해당하는 '현재 대운' 하나를 결정론으로 반환.

    현재 대운 = start_year <= ref_year 인 마지막(가장 늦게 시작한) 대운.
    ref_year 가 첫 대운 시작 이전(起運 전)이거나 미지정이면 None.
    리포트의 모든 챕터가 '현재 대운'을 이 단일 값으로만 서술하도록 단일 사실원을 제공한다
    (대운 모순 = 정미/병오 혼서 실사고 2026-06-14 근원 수정).
    """
    if not ref_year or not m.daewoon:
        return None
    cur: Optional[DaYunItem] = None
    for d in m.daewoon:
        if d.start_year <= ref_year:
            cur = d
        else:
            break
    return cur


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
    # 축 분리(2026-08-17): 연주·월주·대운은 절대축(UTC+8 프레임), 일주·시주는 국지축(진태양시).
    # 근거·불변식은 모듈 도크스트링과 LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS 주석 참조.
    ec = _split_axis_eight_char(ct)
    # 자시 정책(ZasiPolicy) 반영(T2.1/P0-1): ct.day_offset=1 (JST_2300 = 진태양시 23시부터 子시
    # → 일주 익일)이면 setSect(1) 로 일주만 익일 전환한다. lunar-python setSect(1) 은 일주만
    # 바꾸고 시/월/연주·대운(getYun)은 보존한다(실측 2026-08-17 재확인: 4케이스×남녀에서
    # getYun 起運·대운 간지 전부 불변). 자시는 국지 시각 축의 정책이라 국지축 일간에만 걸린다.
    # day_offset 이 이미 정책값이라(JST=23시+ →1, YAJASI=조자시만 1) 이 분기가 정책을 정확히
    # 수행 — 하드코딩 아님(calc.md·절대규칙6).
    if ct.day_offset:
        ec.setSect(1)

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

    # 절입 기준 월지 교차검증 (lunar-python vs Skyfield). 축 분리 후에는 양쪽이 같은 절대축을
    # 보므로 절입 경계에서도 일치해야 한다(교정 전에는 36/36 절입에서 불일치했다).
    # 이 검사는 결함을 잡아낸 유일한 장치다 — 완화·삭제 금지, '통과하게 만드는' 방향만 허용.
    utc = ct.utc.replace(tzinfo=None)
    sky_branch, _, _ = solarterms.month_pillar_branch(utc)
    lunar_month_zhi = pillars["Month"].zhi
    xcheck_ok = sky_branch == lunar_month_zhi

    # 입춘(315°) 기준 연지 교차검증 (F-2) — 연주 경계(입춘 ±) 사각 해소. 기존엔 연주가
    # lunar-python 단독 판정(#26 절기시각 이슈 미커버)이었다. 출생이 그 해 입춘 이후면 명리
    # 연도=그레고리 utc.year, 전이면 year-1. 연지는 60갑자 순환((명리연도-4)%12).
    ipchun = solarterms.solar_term_time(utc.year, 315)
    sky_year = utc.year if utc >= ipchun else utc.year - 1
    sky_year_zhi = "子丑寅卯辰巳午未申酉戌亥"[(sky_year - 4) % 12]
    lunar_year_zhi = pillars["Year"].zhi
    year_xcheck_ok = sky_year_zhi == lunar_year_zhi

    hour_conflict = ct.hour_branch != pillars["Time"].zhi

    # 심화 계산 (결정론; 세운/월운은 lunar-python 출력 노출)
    dm = ec.getDayGan()
    ge, ge_note = advanced.geukguk(pillars["Month"])
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
        year_branch_crosscheck_ok=year_xcheck_ok,
        year_branch_lunar=lunar_year_zhi,
        year_branch_skyfield=sky_year_zhi,
        hour_branch_p1_policy=ct.hour_branch,
        hour_branch_conflict=hour_conflict,
        note=("월지 lunar↔Skyfield 불일치 — 절입 경계 재검토 필요" if not xcheck_ok else ""),
    )
