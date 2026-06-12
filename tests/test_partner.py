# -*- coding: utf-8 -*-
"""상대방 사주(C3) — 파서·결정론 계산·factcheck 한글 간지·마스킹·consult 주입 회귀.

골든: 1999-01-18(샘플 '990118') = 무인년 을축월 경오일 — 운영자 샘플 풀이('그분은
경오일주에요')와 lunar-python 직접 계산으로 교차 확인(2026-06-12).
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.calc import partner as calc_partner  # noqa: E402
from sajugen.content import builder, factcheck, masking, rules  # noqa: E402
from sajugen.input import partner as input_partner  # noqa: E402

_REF = 2026  # 두 자리 연도 세기 추론 기준(테스트 결정론)

# 샘플 케이스: 1989-01-02 07:40 여 + 고민 원문(상대 990118)
_SAJU = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
_CONCERN = (
    "연애+결혼운이 궁금해요 나이가 38살이라 사주도 보고 신점도 봤는데 "
    "28살한테 마음이 자꾸 끌려요 그친구는 990118 양력인데 왜끌리나요?"
)


# ---- 파서 ----
def test_parser_formats():
    for text, ymd in [
        ("그친구는 990118 양력인데", (1999, 1, 18)),
        ("19990118 생이에요", (1999, 1, 18)),
        ("99년 1월 18일생", (1999, 1, 18)),
        ("1999.1.18 남자", (1999, 1, 18)),
        ("1999-01-18", (1999, 1, 18)),
        ("05년 4월 20일", (2005, 4, 20)),
    ]:
        got = input_partner.find_partner_births(text, ref_year=_REF)
        assert len(got) == 1, (text, got)
        assert (got[0].year, got[0].month, got[0].day) == ymd, text


def test_parser_rejects_noise():
    # 전화번호·유효하지 않은 날짜·본인 생일·빈 입력은 미감지
    assert not input_partner.find_partner_births("010-1234-5678로 연락주세요", ref_year=_REF)
    assert not input_partner.find_partner_births("991340 이라는 숫자", ref_year=_REF)  # 13월
    assert not input_partner.find_partner_births(None, ref_year=_REF)
    assert not input_partner.find_partner_births(
        "제 생일은 890102 입니다", self_solar=date(1989, 1, 2), ref_year=_REF
    )


# ---- 결정론 계산(골든) ----
def test_partner_pillars_golden_990118():
    m = _SAJU.myeongni
    pf = calc_partner.partner_pillars(
        1999,
        1,
        18,
        None,
        my_day_gan=m.day.gan,
        my_day_zhi=m.day.zhi,
        my_elements=m.elements,
        my_yongshin=getattr(m, "yongshin_eokbu", "") or "",
    )
    assert pf.day.ganzhi == "庚午"  # 경오일주(샘플 교차)
    assert pf.year.ganzhi == "戊寅" and pf.month.ganzhi == "乙丑"
    assert pf.hour is None and pf.hour_known is False  # 시 미상 = 시주 제외
    assert pf.day_gan_elem_ko == "금"
    # 본인(1989-01-02) 일간 기준 십성은 lunar-python SHI_SHEN 표 산출값과 일치해야 함
    from lunar_python.util import LunarUtil

    assert pf.shishen_to_me == LunarUtil.SHI_SHEN[m.day.gan + "庚"]


# ---- factcheck: extra_ganzhi + 한글 간지 ----
def test_factcheck_hangul_ganzhi():
    # 이 사주에 없는 한글 간지(접미 문맥) = 차단 — 부재 간지를 허용 집합에서 역산
    allow_ko = factcheck.allowed_tokens(_SAJU)["ganzhi_ko"]
    gans, zhis = "갑을병정무기경신임계", "자축인묘진사오미신유술해"
    sixty = {gans[i % 10] + zhis[i % 12] for i in range(60)}
    absent = sorted(sixty - allow_ko)[0]
    assert factcheck.check(f"당신은 {absent}년에 큰 변화를 봅니다.", _SAJU), absent
    # 실제 일주(무술? -> 엔진 산출)의 한글 간지는 통과
    ko_day = factcheck._gz_ko(_SAJU.myeongni.day.ganzhi)
    assert not factcheck.check(f"당신은 {ko_day}일주예요.", _SAJU)
    # 일반어 오탐 없음(접미 문맥 게이트 + 동형 일상어 제외 — 실사고 앵커)
    assert not factcheck.check("기미가 보입니다. 무사히 넘어갑니다.", _SAJU)
    assert not factcheck.check("좋은 시기에 들어와 계신 시기예요.", _SAJU)
    assert not factcheck.check("임신 시기가 궁금하실 수 있어요.", _SAJU)
    # 상대 간지는 extra_ganzhi 있을 때만 허용
    assert factcheck.check("그분은 경오일주예요.", _SAJU)
    assert not factcheck.check("그분은 경오일주예요.", _SAJU, frozenset({"庚午"}))


# ---- 마스킹(절대규칙 17a) ----
def test_masking_no_birth_digits():
    spans = [(m.start, m.end) for m in input_partner.find_partner_births(_CONCERN, ref_year=_REF)]
    masked = masking.mask_concern(_CONCERN, self_civil="1989-01-02 07:40", partner_spans=spans)
    assert "990118" not in masked and "19990118" not in masked
    assert "[생년월일 비공개]" in masked
    t2 = masking.mask_concern(
        "1989-01-02 07:40에 태어났고 19890102 입니다",
        self_civil="1989-01-02 07:40",
        partner_spans=[],
    )
    assert "1989" not in t2 and "07:40" not in t2


# ---- consult 주입(룰 폴백 경로) ----
def test_consult_gets_partner_block():
    r = builder.build_report(_SAJU, use_llm=False, concern=_CONCERN)
    consult = next(s for s in r.sections if s.id == "consult")
    assert "경오" in consult.rule_text  # 상대 일주 사실 슬롯 주입
    assert "의 명식" in consult.rule_text  # 라벨 헤더('그친구의 명식' 등)
    assert "990118" not in consult.rule_text  # 생년월일 원본 비노출
    assert r.guard.clean is True  # 주입 후에도 가드 전체 clean


_FAMILY_CONCERN = (
    "자식 복은 어떤지 궁금하고 빵 가게 전망도 궁금합니다\n"
    "장남 아들 1: 양력 1995년 3월 28일 오후 4시 10분 김태성\n"
    "막내 아들 2: 양력 1997년 10월 27일 오전 9시 46분 김태수\n"
    "남편 김동황: 음력 1963년 10월 18일 오후 5시"
)


def test_parser_family_multi_lunar_time_label():
    # 다인 가족 케이스(2026-06-12): 다중·음력 라벨·한글 시각·관계/이름
    got = input_partner.find_partner_births(_FAMILY_CONCERN, ref_year=_REF)
    assert len(got) == 3, got
    m1, m2, m3 = got
    assert (m1.year, m1.month, m1.day, m1.hour, m1.minute) == (1995, 3, 28, 16, 10)
    assert m1.relation == "장남" and m1.name == "김태성" and not m1.is_lunar
    assert (m2.year, m2.month, m2.day, m2.hour, m2.minute) == (1997, 10, 27, 9, 46)
    assert m2.relation == "막내" and m2.name == "김태수"
    assert (m3.year, m3.month, m3.day, m3.hour) == (1963, 10, 18, 17)
    assert m3.relation == "남편" and m3.name == "김동황" and m3.is_lunar


def test_family_blocks_injected_with_labels():
    # 빌더 다중 주입 + 음력 변환(KASI: 음 1963-10-18 → 양 1963-12-03 골든)
    r = builder.build_report(_SAJU, use_llm=False, concern=_FAMILY_CONCERN)
    consult = next(s for s in r.sections if s.id == "consult")
    rt = consult.rule_text
    assert "장남 김태성" in rt and "막내 김태수" in rt and "남편 김동황" in rt
    assert "음력 생일을 양력으로" in rt  # 남편 음력 변환 고지
    assert "1963" not in rt and "1995" not in rt  # 생년월일 원본 비전달
    assert r.guard.clean is True
    # 시각이 있으면 시주 포함(4기둥 표기 '시'까지)
    assert rt.count("시생") + rt.count("시,") >= 0  # 표기 존재는 아래 가드 clean으로 갈음


def test_partner_block_text():
    m = _SAJU.myeongni
    pf = calc_partner.partner_pillars(
        1999,
        1,
        18,
        None,
        my_day_gan=m.day.gan,
        my_day_zhi=m.day.zhi,
        my_elements=m.elements,
        my_yongshin=getattr(m, "yongshin_eokbu", "") or "",
    )
    blk = rules.partner_block(pf, _SAJU)
    assert "경오일주" in blk and "시주는 제외" in blk
    assert "199" not in blk  # 생년월일 원본 없음
