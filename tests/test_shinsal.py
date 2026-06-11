# -*- coding: utf-8 -*-
"""신살 레지스트리 회귀 — Phase A 구조 리팩토링(표 불변) 보존 검증.

골든(2000-01-01 12:00 KST 남 서울 = 己卯 丙子 戊午 戊午):
- 평탄 shinsal = ["도화살", "양인"] (리팩토링 전후 동일).
- shinsal_detail 은 평탄 리스트와 이름 집합 일치(하위호환 불변식).
학파 스위치(samhap_axis·goegang_scope)는 profile dict 직접 주입으로 검증
(config lru_cache 비의존).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine, shinsal as ss  # noqa: E402


def _r():
    return engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")


def _pil(gz: str):
    return SimpleNamespace(gan=gz[0], zhi=gz[1], ganzhi=gz)


def _pillars(year, month, day, hour):
    return {"Year": _pil(year), "Month": _pil(month), "Day": _pil(day), "Time": _pil(hour)}


# --- 골든 스냅샷(리팩토링 전 현행값 고정) ---


def test_golden_flat_shinsal():
    # 戊 일간, 일지 午(寅午戌) → 도화 卯(년주). 양인 午(일·시). 천문성 卯(년지).
    # Phase A 기존 7종 = [도화살, 양인]. Phase B 확장으로 천문성(년지 卯) 추가.
    r = _r()
    assert r.myeongni.shinsal == ["도화살", "양인", "천문성"], r.myeongni.shinsal


def test_detail_matches_flat():
    # 하위호환 불변식: 평탄 리스트 == detail 이름 ORDER 중복제거 파생
    r = _r()
    derived = ss.flat_names([ss.Hit(h.name, h.pillar, h.basis) for h in r.myeongni.shinsal_detail])
    assert derived == r.myeongni.shinsal, (derived, r.myeongni.shinsal)


def test_detail_has_pillar_and_basis():
    r = _r()
    assert r.myeongni.shinsal_detail, "detail 비어있음"
    for h in r.myeongni.shinsal_detail:
        assert h.pillar in ("year", "month", "day", "hour"), h.pillar
        assert h.basis, h
    # 양인은 일·시 두 기둥 午에서 잡힌다(both 무관)
    yangin_pillars = {h.pillar for h in r.myeongni.shinsal_detail if h.name == "양인"}
    assert yangin_pillars == {"day", "hour"}, yangin_pillars


def test_profile_label_recorded():
    r = _r()
    assert r.myeongni.shinsal_profile == "default", r.myeongni.shinsal_profile


# --- 학파 스위치(profile 직접 주입) ---


def test_samhap_axis_both_vs_day_zhi():
    # 2000 케이스 동일 간지로 축 스위치 효과 검증
    P = _pillars("己卯", "丙子", "戊午", "戊午")
    both = ss.evaluate(P, "戊", {"samhap_axis": "both"})
    day = ss.evaluate(P, "戊", {"samhap_axis": "day_zhi"})
    # both: 일지 午(도화卯=년주) + 년지 卯(도화子=월주) → 도화 2기둥
    both_do = {h.pillar for h in both if h.name == "도화살"}
    day_do = {h.pillar for h in day if h.name == "도화살"}
    assert both_do == {"year", "month"}, both_do
    assert day_do == {"year"}, day_do
    # 평탄 이름은 축 무관 동일(도화살·양인 + 천문성 년지 卯)
    assert ss.flat_names(both) == ss.flat_names(day) == ["도화살", "양인", "천문성"]


def test_goegang_scope_switch():
    # 월주가 庚戌(괴강)인 합성 케이스: day_only 면 미산출, all_pillars 면 월주 산출
    P = _pillars("甲子", "庚戌", "丙寅", "戊子")  # 일주 丙寅=괴강 아님
    day_only = ss.evaluate(P, "丙", {"goegang_scope": "day_only"})
    all_p = ss.evaluate(P, "丙", {"goegang_scope": "all_pillars"})
    assert "괴강" not in ss.flat_names(day_only)
    goe = [h for h in all_p if h.name == "괴강"]
    assert len(goe) == 1 and goe[0].pillar == "month", goe


def test_cheoneul_and_baekho_tables():
    # 壬 일간 → 천을 {卯,巳}: 시지 巳. 백호: 년주 丁丑.
    P = _pillars("丁丑", "丙午", "壬寅", "乙巳")
    hits = ss.evaluate(P, "壬", {})
    names = ss.flat_names(hits)
    assert "천을귀인" in names, names  # 시지 巳
    assert "백호" in names, names  # 년주 丁丑
    cheoneul = [h for h in hits if h.name == "천을귀인"]
    assert cheoneul[0].pillar == "hour", cheoneul


def test_order_stable_and_deduped():
    # 동일 신살이 같은 기둥에 중복 산출되지 않음
    r = _r()
    keys = [(h.name, h.pillar) for h in r.myeongni.shinsal_detail]
    assert len(keys) == len(set(keys)), keys


# --- Phase B: 공망·12신살·확장 길신 ---


def test_gongmang_xunkong_six_xun():
    # 60갑자 6개 旬首의 공망 전수
    assert ss._xunkong("甲子") == ["戌", "亥"]
    assert ss._xunkong("甲戌") == ["申", "酉"]
    assert ss._xunkong("甲申") == ["午", "未"]
    assert ss._xunkong("甲午") == ["辰", "巳"]
    assert ss._xunkong("甲辰") == ["寅", "卯"]
    assert ss._xunkong("甲寅") == ["子", "丑"]


def _case1():
    # 1997-10-27 09:46 서울 남 = 乙巳(시)/壬寅(일)/庚戌(월)/丁丑(년), 일간 壬
    return engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")


def test_case1_pillars_guard():
    m = _case1().myeongni
    assert (m.year.ganzhi, m.month.ganzhi, m.day.ganzhi, m.hour.ganzhi) == (
        "丁丑",
        "庚戌",
        "壬寅",
        "乙巳",
    ), (m.year.ganzhi, m.month.ganzhi, m.day.ganzhi, m.hour.ganzhi)


def test_case1_gongmang():
    # 일주 壬寅(甲午旬)→辰巳, 년주 丁丑(甲戌旬)→申酉. docs/11 레퍼런스 일치.
    g = _case1().myeongni.gongmang
    assert g["day"] == ["辰", "巳"], g
    assert g["year"] == ["申", "酉"], g


def test_case1_per_pillar_golden():
    # 포스텔러 대조 — 엔진이 재현하는 항목(docs/12 §3-1 채택분)
    m = _case1().myeongni
    got = {(h.name, h.pillar) for h in m.shinsal_detail}
    expected = {
        ("천을귀인", "hour"),  # 壬→巳(시지)
        ("태극귀인", "hour"),  # 壬→巳
        ("문창귀인", "day"),  # 壬→寅(일지)
        ("암록", "day"),  # 壬→寅
        ("고신살", "day"),  # 년지 丑 방국 → 寅
        ("금여", "year"),  # 壬→丑(년지)
        ("백호", "year"),  # 丁丑 년주
        ("화개살", "year"),  # 년지 丑 삼합 → 丑
        ("화개살", "month"),  # 일지 寅 삼합 → 戌
        ("천문성", "month"),  # 戌(월지)
        ("과숙살", "month"),  # 년지 丑 방국 → 戌
    }
    assert expected <= got, sorted(expected - got)
    # known-diff(미채택): 천주귀인 미구현, 역마 사생지 느슨표기 미채택
    assert not any(h.name == "천주귀인" for h in m.shinsal_detail)


def test_case1_daewoon_start_age():
    # 레퍼런스(포스텔러·전문가용) 6 己酉 / 16 戊申 / 26 丁未 와 일치.
    # 버그 수정 전엔 8/18/28(lunar 虚岁)이었음.
    m = _case1().myeongni
    assert m.daewoon_count == 6, m.daewoon_count
    got = [(d.start_age, d.ganzhi) for d in m.daewoon[:4]]
    assert got == [(6, "己酉"), (16, "戊申"), (26, "丁未"), (36, "丙午")], got


def test_case1_twelve_shinsal():
    # 일지 기준(寅午戌국, 일지 寅): 년丑=천살 월戌=화개 일寅=지살 시巳=망신
    tw = _case1().myeongni.twelve_shinsal
    assert tw == {"year": "천살", "month": "화개살", "day": "지살", "hour": "망신살"}, tw


def test_extended_gilsin_tables():
    # 문창 壬→寅, 금여 壬→丑, 암록 壬→寅 표 점검
    P = _pillars("壬丑", "甲寅", "壬寅", "丙午")
    hits = ss.evaluate(P, "壬", {})
    by_name = {h.name for h in hits}
    assert "문창귀인" in by_name  # 寅(월·일)
    assert "금여" in by_name  # 丑(년)
    assert "암록" in by_name  # 寅
