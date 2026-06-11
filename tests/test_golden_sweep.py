# -*- coding: utf-8 -*-
"""골든 회귀 확장 — 독립 오라클·속성기반(invariant) 검증.

방법론(plan partitioned-jingling-sunbeam): 기댓값을 사람이 케이스마다 손대조하지 않는다.
정답 판정을 신뢰된 독립 도구·수학 규칙·1차원리·구조 불변식이 대신한다.

3층:
- 1층 독립 오라클: 공망 = lunar-python LunarUtil.getXunKong(별개 구현), 4기둥 = iztro↔lunar
  (crosscheck.bazi_consistent), 대운 방향 = 양남음녀 규칙.
- 2층 1차원리 재도출: 양인=양간 제왕지, 암록=건록 육합, 금여=건록+2(복붙 오타·정답 가드).
- 3층 표 스냅샷 + 구조 불변식: docs/12 검증값 잠금 + 산출 구조 불변(기댓값 불요).

신살·공망은 우리 표 적용이라 외부 정답이 없다(학파차 — docs/12). 그래서 구체값을 박지 않고
invariant 로 검증한다. 신살 구체값 pin 은 외부 캡처가 있는 1997 케이스(test_shinsal)만 유지.
"""

import sys
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from lunar_python.util import LunarUtil  # noqa: E402

from sajugen.calc import engine, shinsal as ss  # noqa: E402


def _pil(gz):
    return SimpleNamespace(gan=gz[0], zhi=gz[1], ganzhi=gz)


_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"
_YANG_GAN = set("甲丙戊庚壬")


# === 결정론 날짜 격자 (무작위 아님 — 재현성 100%) ===
def _date_grid():
    """연 1956~2016 × 4 조합. 성별은 연·월로 결정(순/역·남/여 골고루)."""
    grid = []
    for k, y in enumerate(range(1956, 2017, 10)):  # 1956,1966,...2016 (7 연도)
        for j, (mo, d, h) in enumerate([(2, 18, 8), (6, 5, 14), (9, 23, 20)]):
            male = (k + j) % 2 == 0
            grid.append((y, mo, d, h, male))
    return grid


_GRID = _date_grid()


@lru_cache(maxsize=None)
def _build(y, mo, d, h, male):
    return engine.build(y, mo, d, h, 0, is_male=male, horoscope_date="2026-06-01")


@lru_cache(maxsize=1)
def _grid_built():
    return [(c, _build(*c)) for c in _GRID]


# ----------------------------------------------------------------------------
# 1층 — 독립 오라클
# ----------------------------------------------------------------------------


def test_gongmang_oracle_all_60_jiazi():
    """공망: 우리 _xunkong(산술) == lunar-python getXunKong(독립 구현). 60갑자 전수."""
    for i in range(60):
        gz = _GAN[i % 10] + _ZHI[i % 12]
        lun = LunarUtil.getXunKong(gz)
        assert set(ss._xunkong(gz)) == {lun[0], lun[1]}, (gz, ss._xunkong(gz), lun)


def test_gongmang_oracle_on_grid():
    """격자 사주의 일주·년주 공망도 lunar 독립 구현과 일치."""
    for c, r in _grid_built():
        m = r.myeongni
        for axis, gz in (("day", m.day.ganzhi), ("year", m.year.ganzhi)):
            lun = LunarUtil.getXunKong(gz)
            assert set(m.gongmang[axis]) == {lun[0], lun[1]}, (c, axis, gz)


def test_bazi_consistent_oracle_on_grid():
    """4기둥: 명리(lunar) ↔ 자미(iztro) 독립 2엔진 교차일치."""
    for c, r in _grid_built():
        assert r.crosscheck.bazi_consistent, (
            c,
            r.crosscheck.bazi_myeongni,
            r.crosscheck.bazi_ziwei,
        )


def test_daewoon_direction_yangnam_eumnyeo():
    """대운 방향 = 양남음녀 규칙(양년==남성 → 순행). 명리 공리 독립 검증."""
    for c, r in _grid_built():
        m = r.myeongni
        yang_year = m.year.ganzhi[0] in _YANG_GAN
        assert m.daewoon_forward == (yang_year == c[4]), (c, m.year.ganzhi, m.daewoon_forward)


# ----------------------------------------------------------------------------
# 2층 — 1차원리 재도출 (표 정답성·복붙 오타 가드)
# ----------------------------------------------------------------------------

_LOK = {  # 천간 건록지(전통)
    "甲": "寅",
    "乙": "卯",
    "丙": "巳",
    "丁": "午",
    "戊": "巳",
    "己": "午",
    "庚": "申",
    "辛": "酉",
    "壬": "亥",
    "癸": "子",
}
_YUKHAP = {  # 지지 육합
    "子": "丑",
    "丑": "子",
    "寅": "亥",
    "亥": "寅",
    "卯": "戌",
    "戌": "卯",
    "辰": "酉",
    "酉": "辰",
    "巳": "申",
    "申": "巳",
    "午": "未",
    "未": "午",
}


def test_yangin_derives_from_jewang():
    """양인 = 양간의 제왕지(건록 +1)."""
    for g in _YANG_GAN:
        jewang = _ZHI[(_ZHI.index(_LOK[g]) + 1) % 12]
        assert ss._YANGIN[g] == jewang, (g, ss._YANGIN[g], jewang)


def test_amnok_derives_from_lok_yukhap():
    """암록 = 건록의 육합 지지."""
    for g in _GAN:
        assert ss._AMNOK[g] == _YUKHAP[_LOK[g]], (g, ss._AMNOK[g], _YUKHAP[_LOK[g]])


def test_geumyeo_derives_from_lok_plus2():
    """금여 = 건록 +2 지지."""
    for g in _GAN:
        expect = _ZHI[(_ZHI.index(_LOK[g]) + 2) % 12]
        assert ss._GEUMYEO[g] == expect, (g, ss._GEUMYEO[g], expect)


# ----------------------------------------------------------------------------
# 3층 — 표 스냅샷 (docs/12 검증값 잠금)
# ----------------------------------------------------------------------------


def test_table_snapshots():
    """docs/12 교차검증 표를 그대로 잠금(향후 실수 편집 즉시 차단)."""
    assert ss._CHEONEUL == {
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
    assert ss._MUNCHANG == {
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
    assert ss._HAKDANG == {
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
    assert ss._TAEGEUK["戊"] == {"辰", "戌", "丑", "未"}
    assert ss._TAEGEUK["甲"] == {"子", "午"} and ss._TAEGEUK["壬"] == {"巳", "申"}
    assert ss._CHEONMUN == {"卯", "戌", "亥", "未"}
    assert ss._GOSIN["亥"] == "寅" and ss._GOSIN["申"] == "亥"
    assert ss._GWASUK["亥"] == "戌" and ss._GWASUK["寅"] == "丑"
    assert ss._GOEGANG == {"庚辰", "庚戌", "壬辰", "壬戌"}
    assert ss._BAEKHO == {"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"}


# ----------------------------------------------------------------------------
# 3층 — 구조 불변식 (격자 전수, 기댓값 불요)
# ----------------------------------------------------------------------------


def test_daewoon_structure_invariants():
    for c, r in _grid_built():
        m = r.myeongni
        dw = m.daewoon
        assert dw[0].start_age == m.daewoon_count, (c, dw[0].start_age, m.daewoon_count)
        for i, d in enumerate(dw):
            assert d.start_age == m.daewoon_count + 10 * i, (c, i)
            assert d.end_age == d.start_age + 9, (c, i)
            assert d.start_year == dw[0].start_year + 10 * i, (c, i)
            assert 0 <= (d.start_year - c[0]) - d.start_age <= 2, (c, i)


def _shinsal_allowed(name, day_master):
    """이름별 표가 허용하는 지지/간지 집합(독립 재계산)."""
    if name == "천을귀인":
        return ("zhi", ss._CHEONEUL.get(day_master, set()))
    if name == "양인":
        return ("zhi", {ss._YANGIN[day_master]} if day_master in ss._YANGIN else set())
    if name in ("문창귀인", "학당귀인", "금여", "암록"):
        tbl = {
            "문창귀인": ss._MUNCHANG,
            "학당귀인": ss._HAKDANG,
            "금여": ss._GEUMYEO,
            "암록": ss._AMNOK,
        }[name]
        return ("zhi", {tbl[day_master]})
    if name == "태극귀인":
        return ("zhi", ss._TAEGEUK.get(day_master, set()))
    if name == "천문성":
        return ("zhi", ss._CHEONMUN)
    if name == "괴강":
        return ("ganzhi", ss._GOEGANG)
    if name == "백호":
        return ("ganzhi", ss._BAEKHO)
    return (None, None)  # 삼합계·고신·과숙·12신살은 위치 의존 — 별도 불변식


def test_shinsal_membership_invariants():
    """각 신살은 표가 허용한 지지/간지에서만 출현(일간 기준 길신·간지살)."""
    for c, r in _grid_built():
        m = r.myeongni
        pmap = {"year": m.year, "month": m.month, "day": m.day, "hour": m.hour}
        for h in m.shinsal_detail:
            kind, allowed = _shinsal_allowed(h.name, m.day_master)
            if kind is None:
                continue
            pil = pmap[h.pillar]
            val = pil.zhi if kind == "zhi" else pil.ganzhi
            assert val in allowed, (c, h.name, h.pillar, val, allowed)


# 12신살 독립 재구현: 생지(寅午戌국 寅=지살)에서 +1씩 지살→…→천살
_FROM_JISAL = [
    "지살",
    "연살",
    "월살",
    "망신살",
    "장성살",
    "반안살",
    "역마살",
    "육해살",
    "화개살",
    "겁살",
    "재살",
    "천살",
]
_SAENGJI = {  # 삼합국의 생지(사생지)
    frozenset({"寅", "午", "戌"}): "寅",
    frozenset({"申", "子", "辰"}): "申",
    frozenset({"巳", "酉", "丑"}): "巳",
    frozenset({"亥", "卯", "未"}): "亥",
}


def _twelve_independent(day_zhi, branch):
    grp = next(g for g in _SAENGJI if day_zhi in g)
    saeng = _SAENGJI[grp]
    off = (_ZHI.index(branch) - _ZHI.index(saeng)) % 12
    return _FROM_JISAL[off]


def test_twelve_shinsal_independent_reimpl():
    """12신살(일지축): 독립 재구현과 일치 + 4개·기둥당 1개."""
    for c, r in _grid_built():
        m = r.myeongni
        tw = m.twelve_shinsal
        assert set(tw.keys()) == {"year", "month", "day", "hour"}, (c, tw)
        pmap = {"year": m.year, "month": m.month, "day": m.day, "hour": m.hour}
        for p, name in tw.items():
            assert name == _twelve_independent(m.day.zhi, pmap[p].zhi), (c, p, name)


def test_flat_derives_from_detail_invariant():
    for c, r in _grid_built():
        m = r.myeongni
        derived = ss.flat_names([ss.Hit(h.name, h.pillar, h.basis) for h in m.shinsal_detail])
        assert derived == m.shinsal, (c, derived, m.shinsal)
        keys = [(h.name, h.pillar) for h in m.shinsal_detail]
        assert len(keys) == len(set(keys)), (c, keys)


def test_ziwei_integration_invariants():
    for c, r in _grid_built():
        assert len(r.ziwei.palaces) == 12, c
        assert r.ziwei.soul_palace.endswith("궁"), (c, r.ziwei.soul_palace)
        assert r.ziwei.five_elements_class, c


# ----------------------------------------------------------------------------
# 명명 커버리지 케이스 (4기둥 pin = iztro 교차로 자동 정답확인. 손대조 아님)
# ----------------------------------------------------------------------------

# (y,mo,d,h,mi,male, 년,월,일,시, forward, 대운수, 라벨)
_NAMED = [
    (1984, 5, 10, 10, 0, True, "甲子", "己巳", "甲辰", "己巳", True, 8, "양남 순행"),
    (1985, 3, 15, 7, 20, False, "乙丑", "己卯", "癸丑", "乙卯", True, 6, "음녀 순행"),
    (1992, 12, 25, 18, 0, True, "壬申", "壬子", "乙亥", "乙酉", True, 3, "양남 순행2"),
    (1986, 8, 20, 15, 30, False, "丙寅", "丙申", "丙申", "乙未", False, 4, "양녀 역행"),
    (1978, 9, 9, 4, 0, False, "戊午", "辛酉", "甲戌", "丙寅", False, 0, "양녀 역행·대운수0 엣지"),
    (1995, 6, 15, 23, 30, True, "乙亥", "壬午", "丁丑", "辛亥", False, 3, "자시경계 23:30"),
    (2000, 2, 4, 12, 0, True, "己卯", "丁丑", "壬辰", "丙午", False, 9, "입춘 당일"),
]


@pytest.mark.parametrize("case", _NAMED, ids=[c[-1] for c in _NAMED])
def test_named_cases(case):
    y, mo, d, h, mi, male, yy, mm, dd, hh, fwd, cnt, _label = case
    m = engine.build(y, mo, d, h, mi, is_male=male, horoscope_date="2026-06-01").myeongni
    # 4기둥 pin(회귀 앵커; bazi_consistent 로 자동 정답확인)
    assert (m.year.ganzhi, m.month.ganzhi, m.day.ganzhi, m.hour.ganzhi) == (yy, mm, dd, hh)
    # 대운 방향·대운수·내부정합
    assert m.daewoon_forward is fwd
    assert m.daewoon_count == cnt
    assert m.daewoon[0].start_age == cnt
    # 양남음녀 규칙 자동 정답확인
    yang = m.year.ganzhi[0] in _YANG_GAN
    assert m.daewoon_forward == (yang == male)
    # 공망 오라클
    for axis, gz in (("day", m.day.ganzhi), ("year", m.year.ganzhi)):
        lun = LunarUtil.getXunKong(gz)
        assert set(m.gongmang[axis]) == {lun[0], lun[1]}


def test_named_leap_month_case():
    """윤달 입력: 음력 2017 윤5월10일 → 양력 2017-07-03(KASI). normalize→build 정합."""
    from sajugen.input import normalize

    n = normalize.normalize_date(2017, 5, 10, is_lunar=True, is_leap=True)
    assert (n.year, n.month, n.day) == (2017, 7, 3), (n.year, n.month, n.day)
    m = engine.build(
        n.year, n.month, n.day, 10, 0, is_male=False, horoscope_date="2026-06-01"
    ).myeongni
    assert (m.year.ganzhi, m.month.ganzhi, m.day.ganzhi, m.hour.ganzhi) == (
        "丁酉",
        "丙午",
        "辛卯",
        "癸巳",
    )
    assert m.daewoon_count == 1 and m.daewoon_forward is True
    assert m.daewoon[0].start_age == 1


# ----------------------------------------------------------------------------
# 학파 스위치 (profile 분기 — goegang_scope)
# ----------------------------------------------------------------------------


def test_goegang_all_pillars_switch():
    """괴강 all_pillars: 월주 庚戌도 산출(day_only면 미산출)."""
    P = {
        "Year": _pil("甲子"),
        "Month": _pil("庚戌"),
        "Day": _pil("丙寅"),
        "Time": _pil("戊子"),
    }
    day_only = ss.evaluate(P, "丙", {"goegang_scope": "day_only"})
    all_p = ss.evaluate(P, "丙", {"goegang_scope": "all_pillars"})
    assert "괴강" not in ss.flat_names(day_only)
    goe = [h for h in all_p if h.name == "괴강"]
    assert len(goe) == 1 and goe[0].pillar == "month"
