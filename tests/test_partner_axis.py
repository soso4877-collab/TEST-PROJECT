# -*- coding: utf-8 -*-
"""상대 명식(궁합) 시각축 회귀 — 본인과 동일 축을 쓰는지.

무엇을 검증하는가
-----------------
- `partner_pillars` 의 연·월주 전환이 실제 절기 시각(KASI 기준)과 분 단위로 일치한다.
  구 결함: `ct.true_solar` 단일축이라 −14분 이르게 전환(경계 5건 중 2건 오답).
- 두 결함(lunar-python 절기표 CST −60분 · 진태양시 투입 +46분)의 **상쇄**가 풀렸는지.
  한쪽만 고치면(시민 KST 투입) −60분으로 악화되므로 양쪽 케이스를 함께 둔다(작업 규율 3).
- 본인(`myeongni.build`)과 상대(`partner_pillars`)가 **같은 축**을 쓴다. 궁합 리포트는 두 명식을
  나란히 놓고 관계를 계산하므로, 한 리포트 안에서 축이 갈리면 안 된다.
- 축 분리 프록시(`_SplitAxisLunar`)가 partner 호출 경로 전체를 분류하고 있다(미분류 = RuntimeError).
- 기존 계약(시각 미상 3주·자시 정책 반영·docstring 사실성) 불변.

무엇을 검증하지 않는가
----------------------
- 자시 정책 **분기**(partner_pillars 는 policy 인자를 받지 않는다 — 기본 JST_2300 고정이 계약).
  정책별 양방 핀은 `tests/test_solar_term_axis.py`(본인 경로)가 담당한다.
- 상대 대운·세운(성별 미상으로 산출하지 않는다) → 이월 F-1(대운 start_year 앵커)과 무관.
- `three_pillar.py`·`ziwei.py` 의 시각축(원인이 다름 — 별도 패킷).

기준값 출처
-----------
경계 5행은 `solar-term-axis-fix-20260817` 패킷 §6 표(KASI 절기 원본
`kasi-terms-2000.json`, Skyfield 와 분 단위 일치 확인)를 그대로 재사용한다.
2000 입춘 = KST 21:40:22 / 2000 망종 = KST 17:59:00.
"""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from lunar_python import Solar  # noqa: E402

from sajugen.calc import myeongni as mod_my  # noqa: E402
from sajugen.calc import partner as mod_partner  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402

# 관계 계산용 고정 '본인' — 연·월주 판정과 무관한 인자(관계 필드에만 쓰인다).
_ME = {
    "my_day_gan": "庚",
    "my_day_zhi": "午",
    "my_elements": {"木": 1, "火": 2, "土": 2, "金": 2, "水": 1},
    "my_yongshin": "",
}

# (출생 시민시각, 연주, 월주). 21:39 과 17:58 은 **교정 전 partner 가 틀리는** 앵커다.
_TERM_TABLE = [
    ((2000, 2, 4, 20, 41), "己卯", "丁丑"),  # 입춘 전 — 시민 KST 투입 시 틀림(-60분 재발 감지)
    ((2000, 2, 4, 21, 39), "己卯", "丁丑"),  # 입춘 1분 전 — 교정 전 틀림
    ((2000, 2, 4, 21, 41), "庚辰", "戊寅"),  # 입춘 직후
    ((2000, 6, 5, 17, 58), "庚辰", "辛巳"),  # 망종 1분 전 — 교정 전 틀림
    ((2000, 6, 5, 17, 59), "庚辰", "壬午"),  # 망종 정각
]


def _partner(birth):
    y, mo, d, h, mi = birth
    return mod_partner.partner_pillars(y, mo, d, h, mi, **_ME)


# ---------------------------------------------------------------------------
# 4. 절입 정확도 — KASI 기준 대조(패킷 §6 표를 partner 경로로 실행)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("birth,year_gz,month_gz", _TERM_TABLE)
def test_partner_year_month_matches_actual_solar_term(birth, year_gz, month_gz):
    """상대 연·월주가 실제 절기 시각(KASI) 기준으로 전환된다."""
    pf = _partner(birth)
    assert (pf.year.ganzhi, pf.month.ganzhi) == (year_gz, month_gz), birth


# ---------------------------------------------------------------------------
# 5. 부분수정 차단 — 시민 KST 투입(−60분) 재발 방지
# ---------------------------------------------------------------------------


def test_partner_partial_fix_regression_anchor():
    """진태양시만 걷어내고 시민 KST 를 넘기면 이 케이스가 틀린다(−60분 결함).

    2000-02-04 20:41 KST 는 입춘(21:40:22 KST) **전**이라 정답이 己卯 丁丑 이다.
    교정 전 코드도 (상쇄 덕에) 이 행은 통과하므로 이 테스트 하나로는 결함을 못 잡는다 —
    위 표의 21:39·17:58 과 **함께** 있어야 양방(결함 검출 + 부분수정 차단)이 성립한다.
    """
    pf = _partner((2000, 2, 4, 20, 41))
    assert (pf.year.ganzhi, pf.month.ganzhi) == ("己卯", "丁丑")

    civil_frame = Solar.fromYmdHms(2000, 2, 4, 20, 41, 0).getLunar().getEightChar()
    assert (civil_frame.getYear(), civil_frame.getMonth()) == ("庚辰", "戊寅"), (
        "시민 KST 투입이 여전히 −60분으로 틀린다는 전제가 깨졌다 — 테스트 의미 재검토"
    )
    assert pf.year.ganzhi != civil_frame.getYear()  # 제품이 그 경로를 쓰지 않음을 실증


# ---------------------------------------------------------------------------
# 6. 본인↔상대 축 일치 불변식 (재발방지 상시 회귀 — 패킷 §9)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("birth,_year_gz,_month_gz", _TERM_TABLE)
def test_partner_and_self_share_same_axis(birth, _year_gz, _month_gz):
    """같은 출생을 본인 경로와 상대 경로에 넣으면 연·월·일주 간지가 같다.

    검증: 두 경로가 같은 헬퍼(같은 축)를 쓴다는 코드 증명. 축이 갈리면 궁합 리포트 안에서
    본인은 교정축·상대는 미교정축으로 판정된다(F-2 의 실제 피해 형태).
    검증하지 않음: 시주(상대는 시각 미상 계약이 별도로 있어 이 테스트에서 비교하지 않는다).
    """
    y, mo, d, h, mi = birth
    ct = tc.correct(y, mo, d, h, mi)
    me = mod_my.build(ct, is_male=True)
    pf = _partner(birth)

    assert (pf.year.ganzhi, pf.month.ganzhi, pf.day.ganzhi) == (
        me.year.ganzhi,
        me.month.ganzhi,
        me.day.ganzhi,
    ), birth


def test_partner_uses_absolute_frame_oracle():
    """제품과 독립적으로 만든 CST 프레임 EightChar 와 연·월주가 일치한다(오라클 대조).

    비-no-op 전제: 같은 출생의 진태양시 프레임은 **다른 값**을 낸다는 것을 함께 단언한다.
    (전제가 깨지면 이 케이스는 판별력이 없으므로 테스트가 스스로 알려야 한다.)
    """
    birth = (2000, 2, 4, 21, 39)
    y, mo, d, h, mi = birth
    ct = tc.correct(y, mo, d, h, mi)

    cst = ct.utc + timedelta(hours=mod_my.LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS)
    oracle = (
        Solar.fromYmdHms(cst.year, cst.month, cst.day, cst.hour, cst.minute, 0)
        .getLunar()
        .getEightChar()
    )
    ts = ct.true_solar
    legacy = (
        Solar.fromYmdHms(ts.year, ts.month, ts.day, ts.hour, ts.minute, 0)
        .getLunar()
        .getEightChar()
    )
    assert (oracle.getYear(), oracle.getMonth()) != (legacy.getYear(), legacy.getMonth()), (
        "이 출생에서 두 프레임이 같은 값을 내면 판별력이 없다 — 경계 표본 재선정 필요"
    )

    pf = _partner(birth)
    assert (pf.year.ganzhi, pf.month.ganzhi) == (oracle.getYear(), oracle.getMonth())


# ---------------------------------------------------------------------------
# 7. 프록시 축 배정 완전성 — partner 호출 경로 전용 스윕
# ---------------------------------------------------------------------------

# partner 가 실제로 호출하는 Lunar 메서드 집합은 대운·세운·명궁 경로와 다른 부분집합이라
# (getYear/getMonth/getDay/getTime + LunarUtil.SHI_SHEN) 별도로 훑는다.
# 미분류 이름이 있으면 `_SplitAxisLunar` 가 RuntimeError 를 던진다(fail loud).
_SWEEP_BIRTHS = [
    (2000, 2, 4, 20, 41),
    (2000, 2, 4, 21, 39),
    (2000, 2, 4, 21, 41),
    (2000, 6, 5, 17, 58),
    (2000, 6, 5, 17, 59),
    (2000, 6, 15, 23, 33),  # 자시대 — day_offset=1 경로
    (2000, 6, 16, 0, 30),  # 조자시
    (1999, 1, 18, 12, 0),  # 기존 골든 상대 케이스(무인년 을축월 경오일)
    (1990, 5, 20, 14, 30),  # CLI 표준 표본
    (2026, 1, 1, 6, 5),
]


@pytest.mark.parametrize("birth", _SWEEP_BIRTHS)
def test_partner_path_has_no_unclassified_axis_method(birth):
    """partner 경로 전 표본에서 RuntimeError(축 미분류) 0건 + 산출이 비지 않는다."""
    pf = _partner(birth)
    assert pf.year.ganzhi and pf.month.ganzhi and pf.day.ganzhi
    assert len(pf.year.ganzhi) == 2 and len(pf.month.ganzhi) == 2


def test_partner_hour_unknown_path_has_no_unclassified_axis_method():
    """시각 미상(hour=None → 정오) 경로도 축 분류 누락 0."""
    pf = mod_partner.partner_pillars(1999, 1, 18, None, **_ME)
    assert pf.day.ganzhi == "庚午"  # 기존 골든(운영자 샘플 '990118') 불변


# ---------------------------------------------------------------------------
# 7-b. 인접 사각 — 시각 미상 x 절입 경계 교집합 (작업 규율 4)
# ---------------------------------------------------------------------------

# 시각 미상은 12:00 KST 를 대입한다. 절입이 그 직후(12:00~12:35 KST)인 날에 태어난 상대는
# 교정 전(진태양시 ~11:14 을 시민시각처럼 투입)과 교정 후(12:00 KST = 11:00 CST)의 판정이 갈린다.
# 1960~2030 절입 1704건 전수 스캔 = 갈리는 날 **18건**(scratchpad 프로브, 제품 무변경).
# 기대값 근거: 절입 시각(Skyfield `solarterms`) 이 12:00 보다 **뒤**이므로 정오 출생은 절입 **전**이고,
# 따라서 직전 연주·월주가 정답이다. 교정 전은 이를 이미 넘어간 것으로 판정했다(오답).
_HOUR_UNKNOWN_TERM_TABLE = [
    # (출생일, 기대 연주, 기대 월주, 절입명, 절입 KST, 교정 전 오답)
    ((1986, 2, 4), "乙丑", "己丑", "立春 12:07:41", ("丙寅", "庚寅")),  # 연주까지 갈림
    ((2011, 4, 5), "辛卯", "辛卯", "淸明 12:11:58", ("辛卯", "壬辰")),  # 월주만 갈림
]


@pytest.mark.parametrize("birth,year_gz,month_gz,term,legacy", _HOUR_UNKNOWN_TERM_TABLE)
def test_partner_hour_unknown_on_term_day(birth, year_gz, month_gz, term, legacy):
    """시각 미상 상대가 절입일에 태어나도 정오 대입이 절입 '전'으로 판정된다.

    검증: 정오 대입 경로도 절대축을 탄다(교정 전에는 진태양시 경유라 절입을 넘겨 판정).
    비-no-op 전제: 교정 전 값(legacy)과 기대값이 실제로 다르다는 것을 함께 단언한다.
    검증하지 않음: 정오 대입 자체의 정당성(절대규칙 8·three_pillar 계약 — 별건).
    """
    y, mo, d = birth
    pf = mod_partner.partner_pillars(y, mo, d, None, **_ME)
    assert (pf.year.ganzhi, pf.month.ganzhi) == (year_gz, month_gz), (birth, term)
    assert (year_gz, month_gz) != legacy, "판별력 없는 표본 — 경계 재선정 필요"


# ---------------------------------------------------------------------------
# 8~9. 기존 계약 불변 — 자시 정책 반영·시각 미상 3주
# ---------------------------------------------------------------------------


def test_partner_zasi_policy_day_transition_preserved():
    """자시대 상대 출생에서 일주 익일 전환(기본 JST_2300)이 유지된다.

    `partner_pillars` 는 policy 인자를 받지 않으므로 기본 정책만 검증 대상이다(계약).
    같은 정책의 본인 경로와 일주가 일치하는지로 고정한다 — 값 하드코딩이 아니라
    두 경로가 같은 정책·같은 축을 쓴다는 단언.
    """
    birth = (2000, 6, 15, 23, 33)
    y, mo, d, h, mi = birth
    ct = tc.correct(y, mo, d, h, mi, policy=tc.ZasiPolicy.JST_2300)
    assert ct.day_offset == 1  # 전제: 이 표본이 실제로 자시 전환 구간이다

    pf = _partner(birth)
    me = mod_my.build(ct, is_male=True)
    assert pf.day.ganzhi == me.day.ganzhi == "乙巳"  # 외부 대조값(results-measured.md §13)


def test_partner_hour_unknown_contract_unchanged():
    """시각 미상이면 hour_known=False · hour=None (3주 계약 불변)."""
    pf = mod_partner.partner_pillars(1999, 1, 18, None, **_ME)
    assert pf.hour_known is False
    assert pf.hour is None

    pf_known = mod_partner.partner_pillars(1999, 1, 18, 7, 40, **_ME)
    assert pf_known.hour_known is True
    assert pf_known.hour is not None


# ---------------------------------------------------------------------------
# 10. docstring 정합 — 문서-코드 정합(방법론 A-5)
# ---------------------------------------------------------------------------


def test_partner_docstring_states_split_axis_not_single_axis():
    """docstring 이 축 분리 사실을 말하고, 단일축 서술(거짓)이 남아 있지 않다.

    F-2 후반부: `fae34f7` 이후 "진태양시 보정 → lunar-python EightChar" 는 거짓이 됐다.
    문구만 고치는 것을 막기 위해 실제 헬퍼 공유(위 테스트 6)와 함께 둔다.
    """
    doc = mod_partner.partner_pillars.__doc__ or ""
    assert "절대축" in doc and "국지축" in doc, doc
    assert "진태양시 보정 → lunar-python EightChar" not in doc, doc
