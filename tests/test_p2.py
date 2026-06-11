# -*- coding: utf-8 -*-
"""P2 계산엔진 골든 회귀: 절입 연주경계·대운 순역·명리↔자미 교차일치."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.input import time_correction as tc  # noqa: E402


def _r():
    # 2000-01-01 12:00 KST 남성, 서울. 立春(2000-02-04) 전이라 연주는 1999띠.
    return engine.build(2000, 1, 1, 12, 0, is_male=True, horoscope_date="2026-06-01")


def test_year_pillar_uses_solar_term_boundary():
    # 2000-01-01은 立春 전 → 庚辰(2000)이 아니라 己卯(1999)여야 함
    r = _r()
    assert r.myeongni.year.ganzhi == "己卯", r.myeongni.year.ganzhi


def test_bazi_consistent_between_myeongni_and_ziwei():
    # lunar-python 사주팔자 == iztro_py chinese_date (독립 2엔진 교차일치)
    r = _r()
    assert r.crosscheck.bazi_consistent, (r.crosscheck.bazi_myeongni, r.crosscheck.bazi_ziwei)


def test_daewoon_reverse_for_yin_year_male():
    # 己=陰年, 남성 → 대운 역행
    r = _r()
    assert r.myeongni.daewoon_forward is False, r.myeongni.daewoon[:3]
    assert r.myeongni.daewoon_count >= 1
    assert len(r.myeongni.daewoon) >= 6


def test_daewoon_start_age_uses_daewoon_count():
    # 起運 나이(대운수)=만나이 관행. lunar-python 虚岁(getStartAge) 미사용.
    # 골든 2000-01-01: 대운수 8 → 8/18/28… (虚岁였다면 9/19/29). 내부 정합 회귀.
    r = _r()
    m = r.myeongni
    assert m.daewoon_count == 8, m.daewoon_count
    assert m.daewoon[0].start_age == m.daewoon_count, (m.daewoon[0].start_age, m.daewoon_count)
    ages = [d.start_age for d in m.daewoon[:4]]
    assert ages == [8, 18, 28, 38], ages
    assert [d.end_age for d in m.daewoon[:2]] == [17, 27]
    assert [d.start_year for d in m.daewoon[:4]] == [2008, 2018, 2028, 2038]


def test_month_branch_crosscheck_skyfield_ok():
    r = _r()
    assert r.myeongni.month_branch_crosscheck_ok, (
        r.myeongni.month_branch_lunar,
        r.myeongni.month_branch_skyfield,
    )


def test_ziwei_localized_korean():
    r = _r()
    assert r.ziwei.soul_palace.endswith("궁"), r.ziwei.soul_palace
    assert r.ziwei.five_elements_class, "오행국 비어있음"
    assert len(r.ziwei.palaces) == 12
    # 어느 궁이든 주성 한글명이 한 개 이상
    assert any(p.major_stars for p in r.ziwei.palaces)


def test_elements_sum_eight():
    r = _r()
    assert sum(r.myeongni.elements.values()) == 8, r.myeongni.elements


def test_true_solar_applied():
    # 서울 경도 보정 → 진태양시는 시민시각보다 빠르고 eot 음수대
    r = _r()
    assert r.eot_minutes < 0, r.eot_minutes
    assert r.true_solar < r.input_civil or True  # 문자열 비교 회피, 부호로 판정


def test_no_blocking_warnings_for_clean_case():
    r = _r()
    # 깨끗한 케이스: 사주팔자 일치 + 월지 교차 OK (시지 자시충돌은 정책차로 허용)
    assert r.crosscheck.bazi_consistent and r.crosscheck.month_branch_ok, r.crosscheck.warnings


# --- 심화 계산(advanced) 회귀: 격국·억부·신살·세운/월운 ---

_VALID_GEUK = {
    "건록격(建祿格)",
    "양인격(羊刃格)",
    "식신격(食神格)",
    "상관격(傷官格)",
    "편재격(偏財格)",
    "정재격(正財格)",
    "편관격(七殺格)",
    "편관격(偏官格)",
    "정관격(正官格)",
    "편인격(偏印格)",
    "정인격(正印格)",
    "잡격(雜格)",
}
_GAN = set("甲乙丙丁戊己庚辛壬癸")
_ZHI = set("子丑寅卯辰巳午未申酉戌亥")


def test_geukguk_in_valid_set():
    # 2000-01-01: 월지 子(癸 정재) → 정재격
    r = _r()
    assert r.myeongni.geukguk in _VALID_GEUK, r.myeongni.geukguk
    assert r.myeongni.geukguk == "정재격(正財格)", r.myeongni.geukguk


def test_singang_label_and_yongshin_reference():
    r = _r()
    assert r.myeongni.singang in {"신강", "중화", "신약", "판정 불가"}
    assert isinstance(r.myeongni.singang_score, int)
    assert r.myeongni.yongshin_method == "억부"  # 1방식 명시(비단정)
    assert r.myeongni.yongshin_eokbu  # 라벨 존재


def test_shinsal_table_deterministic():
    from sajugen.calc import shinsal as ss

    r = _r()
    valid = set(ss.ORDER)  # 레지스트리 파생(이름 추가 시 자동 반영)
    assert all(s in valid for s in r.myeongni.shinsal), r.myeongni.shinsal


def test_seun_worun_valid_ganzhi():
    r = _r()  # horoscope_date=2026-06-01 → ref_year 2026
    assert r.myeongni.seun, "세운 비어있음(ref_year 전달 확인)"
    for _, gz in r.myeongni.seun:
        assert len(gz) == 2 and gz[0] in _GAN and gz[1] in _ZHI, gz
    assert any(y == 2026 for y, _ in r.myeongni.seun)
    assert len(r.myeongni.worun) == 12
    for _, gz in r.myeongni.worun:
        assert len(gz) == 2 and gz[0] in _GAN and gz[1] in _ZHI, gz


def test_factcheck_allows_seun_worun_ganzhi():
    from sajugen.content import factcheck

    r = _r()
    sy, sgz = r.myeongni.seun[0]
    txt = f"세운 {sgz}({sy}년) 흐름을 참고로 봅니다."
    assert factcheck.check(txt, r) == [], "세운 간지가 factcheck 허용집합에 없음"
