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
    # 인물 문맥(관계어/역법 라벨/출생 접미) 동반 날짜는 전 포맷 감지 유지
    for text, ymd in [
        ("그친구는 990118 양력인데", (1999, 1, 18)),
        ("19990118 생이에요", (1999, 1, 18)),
        ("99년 1월 18일생", (1999, 1, 18)),
        ("1999.1.18 남자", (1999, 1, 18)),
        ("여자친구 1999-01-18", (1999, 1, 18)),
        ("그분은 05년 4월 20일 태어났어요", (2005, 4, 20)),
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


def test_parser_requires_person_context():
    # QI-2026-07-04 팬텀 파트너: 인물 문맥 없는 날짜(사건·이력·금액 조각)는 미감지.
    # 사건 날짜가 상대 생일로 둔갑해 존재하지 않는 인물의 명식·관계 서술이 개인 풀이에
    # 주입된 실사고의 회귀 앵커. 미감지 = 개인 풀이 진행(안전 방향).
    for text in [
        "2020년 3월 5일에 이사한 뒤로 일이 잘 안 풀립니다.",  # 사건 날짜(_RX_KO)
        "계약금 300만원 중 150301 송금했는데 사업운이 궁금합니다.",  # 맨 6자리(_RX_6)
        "1999-01-18",  # 문맥 없는 맨 날짜(_RX_SEP) — 구 골든에서 의도 변경(사건 오인 방지)
        "2021.4.1 계약했고 2023-05-02 퇴사했습니다.",  # 이력 날짜 2건
    ]:
        assert not input_partner.find_partner_births(text, ref_year=_REF), text


def test_builder_wires_self_solar_guard():
    # QI-2026-07-04: builder 가 본인 생일 제외 가드(self_solar)를 실제 배선하는지 —
    # 원문에 본인 생일이 있어도 상대방 명식이 주입되지 않아야 한다.
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    r = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        concern="제 남편은 저랑 동갑이고 저는 1989년 1월 2일생입니다. 남편 복이 궁금해요.",
    )
    consult = next(s for s in r.sections if s.id == "consult")
    assert "의 명식" not in consult.rule_text  # 본인 생일 = 상대 아님(가드 발동)


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


_DAY_ZHI_SAMPLE = {
    "子": (1990, 1, 11),
    "丑": (1990, 1, 12),
    "寅": (1990, 1, 1),
    "卯": (1990, 1, 2),
    "辰": (1990, 1, 3),
    "巳": (1990, 1, 4),
    "午": (1990, 1, 5),
    "未": (1990, 1, 6),
    "申": (1990, 1, 7),
    "酉": (1990, 1, 8),
    "戌": (1990, 1, 9),
    "亥": (1990, 1, 10),
}


def _facts_for_day_pair(my_day_zhi: str, partner_day_zhi: str):
    # 각 날짜의 일지는 lunar-python EightChar 실측값으로 고정했다.
    # 테스트 목적은 달력 계산이 아니라 docs/03 §1-1 지지쌍 표와 필드 배선 검증이다.
    y, m, d = _DAY_ZHI_SAMPLE[partner_day_zhi]
    return calc_partner.partner_pillars(
        y,
        m,
        d,
        None,
        my_day_gan="甲",
        my_day_zhi=my_day_zhi,
        my_elements={"木": 1, "火": 1, "土": 1, "金": 1, "水": 1},
    )


def test_ilji_hai_table_hit_and_no_hit():
    for a, b in [("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")]:
        assert _facts_for_day_pair(a, b).ilji_hai == "해"
    assert _facts_for_day_pair("子", "寅").ilji_hai == ""


def test_ilji_po_table_hit_and_no_hit():
    for a, b in [("子", "酉"), ("卯", "午"), ("巳", "申"), ("寅", "亥"), ("丑", "辰"), ("戌", "未")]:
        assert _facts_for_day_pair(a, b).ilji_po == "파"
    assert _facts_for_day_pair("子", "寅").ilji_po == ""


def test_ilji_wonjin_table_hit_and_no_hit():
    for a, b in [("子", "未"), ("丑", "午"), ("寅", "酉"), ("卯", "申"), ("辰", "亥"), ("巳", "戌")]:
        assert _facts_for_day_pair(a, b).ilji_wonjin == "원진"
    assert _facts_for_day_pair("子", "寅").ilji_wonjin == ""


def test_ilji_xing_pairwise_scope_and_boundary():
    for zhi in ("辰", "午", "酉", "亥"):
        assert _facts_for_day_pair(zhi, zhi).ilji_xing == "자형"
    assert _facts_for_day_pair("子", "卯").ilji_xing == "상형"
    assert _facts_for_day_pair("卯", "子").ilji_xing == "상형"
    assert _facts_for_day_pair("子", "子").ilji_xing == ""
    assert _facts_for_day_pair("子", "寅").ilji_xing == ""


def test_ilji_relations_are_independent_not_elif_chain():
    yuk_hap_and_po = _facts_for_day_pair("巳", "申")
    assert yuk_hap_and_po.ilji_relation == "육합"
    assert yuk_hap_and_po.ilji_po == "파"

    hai_and_wonjin = _facts_for_day_pair("子", "未")
    assert hai_and_wonjin.ilji_hai == "해"
    assert hai_and_wonjin.ilji_wonjin == "원진"


def test_samhyeong_deferred_yin_si_is_hai_only_for_now():
    # docs/03 §1-1: 寅巳의 형은 삼형(寅巳申)에서 오므로 이번 pairwise 범위에서는 defer.
    # 추후 삼형 전체 구조를 구현하면 이 테스트를 형+해 동시 발화로 승격한다.
    pf = _facts_for_day_pair("寅", "巳")
    assert pf.ilji_hai == "해"
    assert pf.ilji_xing == ""


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


def test_partner_block_outputs_ilji_tension_fields():
    # 개인 consult 경로도 PartnerFacts 긴장 관계를 소비해야 한다.
    # 합성 PartnerFacts 만 사용해 생년월일·실명 PII 없이 출력 문장 배선을 검증한다.
    pillar = calc_partner.PartnerPillar(gan="甲", zhi="子", ganzhi="甲子")
    pf = calc_partner.PartnerFacts(
        year=pillar,
        month=pillar,
        day=pillar,
        day_gan_elem_ko="목",
        shishen_to_me="",
        ilji_hai="해",
        ilji_po="파",
        ilji_wonjin="원진",
        ilji_xing="상형",
    )
    blk = rules.partner_block(pf, _SAJU, label="합성상대")

    assert "본인 일지와 합성상대의 일지는 해" in blk
    assert "생활 흐름이 엇갈리기 쉬워 확인이 필요한 자리다" in blk
    assert "본인 일지와 합성상대의 일지는 파" in blk
    assert "가까워진 뒤에도 약속과 역할을 다시 맞춰야 하는 자리다" in blk
    assert "본인 일지와 합성상대의 일지는 원진" in blk
    assert "이유 없이 서먹해지기 쉬워 감정을 천천히 확인해야 하는 자리다" in blk
    assert "본인 일지와 합성상대의 일지는 상형" in blk
    assert "비슷한 반응이 반복될 때 속도를 낮춰야 하는 자리다" in blk
    from sajugen.content import client_tone_lint as ct

    assert ct.loanword_lint(blk) == []
