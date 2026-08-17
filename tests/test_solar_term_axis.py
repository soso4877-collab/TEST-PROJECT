# -*- coding: utf-8 -*-
"""절입 판정 시각축 회귀 — 연·월·대운=절대축(CST) / 일·시=국지축(진태양시).

무엇을 검증하는가
-----------------
- 연주·월주 전환이 실제 절기 시각과 분 단위로 일치한다(구 결함: 13~14분 이르게 전환).
- 두 결함(lunar-python 절기표 CST −60분 · 진태양시 투입 +46분)의 **상쇄**가 풀렸는지.
  한쪽만 고치면(시민 KST 투입) −60분으로 악화되므로 양쪽 케이스를 함께 둔다.
- 축 분리가 절입 경계 **밖**의 기존 산출을 바꾸지 않는다(비회귀).
- 십성·지세가 국지축 일간 기준으로 계산된다(축 혼입 차단).

무엇을 검증하지 않는가
----------------------
- 자미두수(iztro) 절입 해상도 결함(원인이 다름 — 별도 패킷).
- `three_pillar.py`·`partner.py` 의 시각축(이 패킷 범위 밖 — 인접 사각으로 보고).
- 대운수 관례(만나이 vs 세는나이) — 이 패킷에서 바꾸지 않는다.

기준값 출처
-----------
§표 5행은 KASI 절기 원본(`handoff/evidence/20260817-postteller-chart-survey/kasi-terms-2000.json`,
Skyfield 와 분 단위 일치 확인)에서 도출한 값이다. 2000 입춘 = KST 21:40:22, 2000 망종 = KST 17:59:00.
"""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from lunar_python import Solar  # noqa: E402
from lunar_python.util import LunarUtil  # noqa: E402

from sajugen.calc import myeongni as mod_my, solarterms  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402

ULLEUNG_LON = 130.9057  # 울릉도 — 서울 대비 경도차 약 +3.93° (진태양시 +15.7분)


def _build(y, mo, d, h, mi, *, is_male=True, longitude=tc.SEOUL_LON, policy=None):
    kwargs = {"longitude": longitude}
    if policy is not None:
        kwargs["policy"] = policy
    ct = tc.correct(y, mo, d, h, mi, **kwargs)
    return ct, mod_my.build(ct, is_male=is_male)


def _absolute_frame_eight_char(ct):
    """제품과 독립적으로 CST 프레임 EightChar 를 다시 만든다(오라클용)."""
    cst = ct.utc + timedelta(hours=mod_my.LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS)
    return (
        Solar.fromYmdHms(cst.year, cst.month, cst.day, cst.hour, cst.minute, 0)
        .getLunar()
        .getEightChar()
    )


# ---------------------------------------------------------------------------
# 3. 절입 정확도 — KASI 기준 대조(패킷 §6 표)
# ---------------------------------------------------------------------------

# (출생 시민시각, 연주, 월주). 21:39 과 17:58 은 **교정 전 코드가 틀리는** 앵커다.
_TERM_TABLE = [
    ((2000, 2, 4, 20, 41), "己卯", "丁丑"),  # 입춘 전 — 시민 KST 투입 시 틀림(-60분 재발 감지)
    ((2000, 2, 4, 21, 39), "己卯", "丁丑"),  # 입춘 1분 전 — 교정 전 틀림
    ((2000, 2, 4, 21, 41), "庚辰", "戊寅"),  # 입춘 직후
    ((2000, 6, 5, 17, 58), "庚辰", "辛巳"),  # 망종 1분 전 — 교정 전 틀림
    ((2000, 6, 5, 17, 59), "庚辰", "壬午"),  # 망종 정각
]


@pytest.mark.parametrize("birth,year_gz,month_gz", _TERM_TABLE)
def test_year_month_pillar_matches_actual_solar_term(birth, year_gz, month_gz):
    """연·월주가 실제 절기 시각(KASI) 기준으로 전환된다."""
    _, m = _build(*birth)
    assert (m.year.ganzhi, m.month.ganzhi) == (year_gz, month_gz), birth


def test_partial_fix_regression_anchor_ipchun_before_kst_boundary():
    """부분 수정(결함 B만) 차단 앵커 — 시민 KST 를 넘기면 이 케이스가 틀린다.

    2000-02-04 20:41 KST 는 입춘(21:40:22 KST) **전**이라 정답이 己卯 丁丑 이다.
    lunar-python 절기표는 CST 라, 시민 KST 를 그대로 넘기면 20:40:22 에 전환해
    庚辰 戊寅 으로 뒤집힌다(−60분 결함). 교정 전 코드는 진태양시 보정이 이를 우연히
    상쇄해 이 케이스를 통과했으므로, 이 테스트 하나만으로는 결함을 못 잡는다 —
    위 표의 21:39·17:58 과 **함께** 있어야 양방이 성립한다(작업 규율 3).
    """
    ct, m = _build(2000, 2, 4, 20, 41)
    assert (m.year.ganzhi, m.month.ganzhi) == ("己卯", "丁丑")

    civil_frame = (
        Solar.fromYmdHms(2000, 2, 4, 20, 41, 0).getLunar().getEightChar()
    )
    assert (civil_frame.getYear(), civil_frame.getMonth()) == ("庚辰", "戊寅"), (
        "시민 KST 투입이 여전히 −60분으로 틀린다는 전제가 깨졌다 — 테스트 의미 재검토"
    )
    assert m.year.ganzhi != civil_frame.getYear()  # 제품이 그 경로를 쓰지 않음을 실증


# ---------------------------------------------------------------------------
# 5. 축 분리 불변식 — 절입은 절대 시각, 시지는 국지 시각
# ---------------------------------------------------------------------------


def test_year_month_longitude_invariant_but_hour_branch_is_not():
    """같은 절대 순간이면 경도가 달라도 연·월주는 같고, 시지는 달라질 수 있다.

    검증: 경도가 연·월주로 새지 않는다(교정 전에는 진태양시 경유로 샜다) + 시지는
    국지축이라 경도에 반응한다(축이 하나로 뭉개지지 않았다는 반대 방향 증거).
    검증하지 않음: 어느 경도가 '옳은' 시지인가(유파·정책 문제).
    """
    _, seoul = _build(2000, 2, 4, 21, 35, longitude=tc.SEOUL_LON)
    _, ulleung = _build(2000, 2, 4, 21, 35, longitude=ULLEUNG_LON)

    assert (seoul.year.ganzhi, seoul.month.ganzhi) == ("己卯", "丁丑")
    assert (seoul.year.ganzhi, seoul.month.ganzhi) == (ulleung.year.ganzhi, ulleung.month.ganzhi)
    assert seoul.hour.zhi != ulleung.hour.zhi, (seoul.hour.zhi, ulleung.hour.zhi)


# ---------------------------------------------------------------------------
# 6·7. 교차검증 정합 + 절입 창 폭 0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("birth", [b for b, _, _ in _TERM_TABLE] + [(2000, 2, 4, 21, 35)])
def test_crosscheck_flags_true_on_boundary_cases(birth):
    """경계 케이스 전부에서 lunar↔Skyfield 월지·연지 교차검증이 통과한다."""
    _, m = _build(*birth)
    assert m.month_branch_crosscheck_ok is True, (birth, m.month_branch_lunar, m.month_branch_skyfield)
    assert m.year_branch_crosscheck_ok is True, (birth, m.year_branch_lunar, m.year_branch_skyfield)


_SCAN_TERMS = [(2000, 315), (1990, 75), (2010, 225)]  # 입춘 · 망종 · 한로


@pytest.mark.parametrize("year,lon", _SCAN_TERMS)
def test_no_crosscheck_mismatch_window_around_solar_term(year, lon):
    """절입 ±40분을 1분 간격으로 훑어 교차검증 False 가 0건.

    랜덤 표본은 경계 폭이 좁아(연 0.063%) 이 결함을 못 잡았다 — 경계를 직접 겨냥한다.
    """
    kst = solarterms.solar_term_time(year, lon).replace(tzinfo=None) + timedelta(hours=9)
    bad = []
    for off in range(-40, 41):
        t = kst + timedelta(minutes=off)
        _, m = _build(t.year, t.month, t.day, t.hour, t.minute)
        if not (m.month_branch_crosscheck_ok and m.year_branch_crosscheck_ok):
            bad.append(off)
    assert bad == [], (year, lon, bad)


@pytest.mark.parametrize("year,lon", _SCAN_TERMS)
def test_month_pillar_transition_minute_matches_solar_term(year, lon):
    """월주가 실제로 바뀌는 '분'이 절기 시각과 일치한다(하드코딩 없는 오라클).

    허용 ±1분: lunar-python 절기표↔Skyfield 는 0.02~0.21분 차가 있고(calc.md) 입력이
    분 해상도라 절상 경계에서 1분 어긋날 수 있다. 구 결함(13~14분)·부분수정(60분)은
    이 허용치 밖이므로 감지력을 잃지 않는다.
    """
    kst = solarterms.solar_term_time(year, lon).replace(tzinfo=None) + timedelta(hours=9)
    base = kst.replace(second=0, microsecond=0) - timedelta(minutes=40)
    prev = None
    transition = None
    for off in range(0, 81):
        t = base + timedelta(minutes=off)
        _, m = _build(t.year, t.month, t.day, t.hour, t.minute)
        if prev is not None and m.month.ganzhi != prev:
            transition = t
            break
        prev = m.month.ganzhi
    assert transition is not None, (year, lon, "±40분 안에서 월주 전환을 찾지 못함")
    delta_min = abs((transition - kst).total_seconds()) / 60.0
    assert delta_min <= 1.0, (year, lon, transition.isoformat(), kst.isoformat(), delta_min)


# ---------------------------------------------------------------------------
# 8. 대운 축 정합 — 起運도 절대축에서 나온다
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("birth", [(2000, 2, 4, 21, 39), (2000, 2, 4, 21, 41), (2000, 6, 5, 17, 58)])
@pytest.mark.parametrize("is_male", [True, False])
def test_daewoon_start_follows_absolute_axis(birth, is_male):
    """대운수(起運)가 절대축(CST 프레임)에서 독립 재도출한 값과 일치한다.

    起運은 절입까지의 거리라 절입과 같은 축이어야 한다. 국지축(진태양시)에서 세면
    절입 축과 어긋난다. 오라클 = 제품 경로를 타지 않는 별도 EightChar.
    """
    ct, m = _build(*birth, is_male=is_male)
    expected = _absolute_frame_eight_char(ct).getYun(1 if is_male else 0, 1).getStartYear()
    assert m.daewoon_count == expected, (birth, is_male, m.daewoon_count, expected)


# ---------------------------------------------------------------------------
# 9. 자시 정책 불변 — 국지축은 손대지 않았다
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "policy,expected_day",
    [(tc.ZasiPolicy.JST_2300, "乙巳"), (tc.ZasiPolicy.YAJASI_SPLIT, "甲辰")],
)
def test_zasi_policy_day_pillar_unchanged(policy, expected_day):
    """외부 대조로 확인된 자시 정책 거동(results-measured.md §13)이 축 분리 후에도 그대로."""
    _, m = _build(2000, 6, 15, 23, 33, policy=policy)
    assert m.day.ganzhi == expected_day, (policy, m.day.ganzhi)


# ---------------------------------------------------------------------------
# 축 혼입 차단 — 십성·지세는 국지축 일간 기준이어야 한다
# ---------------------------------------------------------------------------


def test_year_month_shishen_use_local_axis_day_master():
    """연·월주 십성·지세가 **국지축 일간** 기준으로 계산된다.

    연·월주만 다른 EightChar 인스턴스에서 골라 담으면 그 인스턴스의 일간으로 십성이
    계산돼 일간과 어긋난 십성이 조용히 섞인다. 2000-06-15 23:33 은 자시 정책으로
    국지축 일간(乙)과 절대축 일간(甲)이 갈리는 케이스라 두 값이 실제로 다르다
    (正官 vs 七杀 / 正印 vs 偏印 / 冠带 vs 衰) — 비-no-op.
    """
    ct, m = _build(2000, 6, 15, 23, 33)
    ec_abs = _absolute_frame_eight_char(ct)
    assert m.day_master != ec_abs.getDayGan(), "판별력 전제(두 축의 일간이 갈림)가 깨졌다"

    # 일주 천간 십성은 lunar-python 이 '日主' 로 고정 표기하므로 천간은 제외하고,
    # 일간 자체가 국지축에서 왔는지는 별도로 못박는다.
    assert m.day.gan == m.day_master
    for pillar in (m.year, m.month, m.hour):
        assert pillar.shishen_gan == LunarUtil.SHI_SHEN.get(m.day_master + pillar.gan), pillar
    for pillar in (m.year, m.month, m.day, m.hour):
        assert pillar.shishen_zhi == [
            LunarUtil.SHI_SHEN.get(m.day_master + g) for g in pillar.hide_gan
        ], pillar

    # 절대축 일간으로 계산했다면 나왔을 값과 실제로 다르다(축 혼입이면 여기서 실패)
    assert m.year.shishen_gan != LunarUtil.SHI_SHEN.get(ec_abs.getDayGan() + m.year.gan)
    assert m.year.dishi != ec_abs.getYearDiShi()


# ---------------------------------------------------------------------------
# 비회귀 — 절입 경계 밖에서는 축 분리가 기존 산출을 바꾸지 않는다
# ---------------------------------------------------------------------------


def _legacy_eight_char(ct):
    """교정 전 방식(국지축 단일 EightChar) 재현 — 비회귀 대조용."""
    ts = ct.true_solar
    ec = (
        Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second or 0)
        .getLunar()
        .getEightChar()
    )
    if ct.day_offset:
        ec.setSect(1)
    return ec


def _nonboundary_grid():
    grid = []
    for year in (1956, 1975, 1990, 2003, 2016):
        for mo, d in ((1, 11), (4, 22), (8, 3), (11, 27)):
            for h, mi in ((3, 15), (12, 0), (23, 33)):
                grid.append((year, mo, d, h, mi))
    return grid


@pytest.mark.parametrize("birth", _nonboundary_grid())
def test_axis_split_is_noop_outside_term_boundaries(birth):
    """절입 경계 밖 출생은 4기둥·십성·지세·납음·명궁/신궁이 교정 전과 완전히 동일하다.

    검증: 축 분리가 '경계에서만' 작동한다(광범위 회귀 0).
    검증하지 않음: 대운수 — 起運 축이 의도적으로 바뀌었다(0.57% 변동, 별도 테스트).
    """
    ct, m = _build(*birth)
    legacy = _legacy_eight_char(ct)
    if (legacy.getYear(), legacy.getMonth()) != (m.year.ganzhi, m.month.ganzhi):
        pytest.skip("절입 경계 케이스 — 이 테스트의 대상이 아니다")

    for who, pillar in (("Year", m.year), ("Month", m.month), ("Day", m.day), ("Time", m.hour)):
        assert pillar.ganzhi == getattr(legacy, f"get{who}")(), who
        assert pillar.shishen_gan == getattr(legacy, f"get{who}ShiShenGan")(), who
        assert pillar.shishen_zhi == list(getattr(legacy, f"get{who}ShiShenZhi")()), who
        assert pillar.dishi == getattr(legacy, f"get{who}DiShi")(), who
        assert pillar.nayin == getattr(legacy, f"get{who}NaYin")(), who
    assert m.ming_gong_nayin == legacy.getMingGongNaYin()
    assert m.shen_gong_nayin == legacy.getShenGongNaYin()


def test_noop_grid_actually_covers_cases():
    """위 비회귀 격자가 전부 skip 되지 않았음을 보장(no-op 테스트 방지)."""
    covered = 0
    for birth in _nonboundary_grid():
        ct, m = _build(*birth)
        legacy = _legacy_eight_char(ct)
        if (legacy.getYear(), legacy.getMonth()) == (m.year.ganzhi, m.month.ganzhi):
            covered += 1
    assert covered >= len(_nonboundary_grid()) - 2, covered


# ---------------------------------------------------------------------------
# 프록시 계약 — 축 배정은 명시적이고 fail-closed 다
# ---------------------------------------------------------------------------


def test_split_axis_proxy_routes_and_fails_closed():
    ct = tc.correct(2000, 2, 4, 21, 39)
    absolute = _absolute_frame_eight_char(ct).getLunar()
    ts = ct.true_solar
    local = Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute, 0).getLunar()
    proxy = mod_my._SplitAxisLunar(absolute, local)

    assert proxy.getYearInGanZhiExact() == absolute.getYearInGanZhiExact()
    assert proxy.getMonthInGanZhiExact() == absolute.getMonthInGanZhiExact()
    assert proxy.getSolar().toYmdHms() == absolute.getSolar().toYmdHms()
    assert proxy.getDayInGanZhiExact() == local.getDayInGanZhiExact()
    assert proxy.getTimeInGanZhi() == local.getTimeInGanZhi()
    # 두 축이 실제로 다른 Lunar 라는 전제(프록시가 우연히 같은 값을 내는 게 아님)
    assert absolute.getSolar().toYmdHms() != local.getSolar().toYmdHms()

    with pytest.raises(RuntimeError):
        proxy.getSomethingUnclassified()


def test_split_axis_routing_covers_every_lunar_method_lunar_python_calls():
    """lunar-python 1.4.8 이 Lunar 에 실제로 호출하는 이름 전체가 축 배정 표에 있다.

    버전 드리프트로 새 메서드가 생기면 조용히 한쪽 축으로 새지 않고 여기서 잡힌다.
    """
    import re

    import lunar_python

    root = Path(lunar_python.__file__).resolve().parent
    sources = [root / "EightChar.py"] + sorted((root / "eightchar").glob("*.py"))
    names = set()
    for path in sources:
        names |= set(re.findall(r"__lunar\.([A-Za-z0-9_]+)", path.read_text(encoding="utf-8")))
    assert names, "lunar-python 소스에서 Lunar 호출을 찾지 못했다(스캔 실패)"

    unclassified = sorted(
        n
        for n in names
        if not (
            n in mod_my._ABSOLUTE_AXIS_NAMES
            or n.startswith(mod_my._ABSOLUTE_AXIS_PREFIXES)
            or n.startswith(mod_my._LOCAL_AXIS_PREFIXES)
        )
    )
    assert unclassified == [], unclassified
