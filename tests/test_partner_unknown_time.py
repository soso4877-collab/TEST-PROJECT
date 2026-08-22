# -*- coding: utf-8 -*-
"""시각 미상 상대 x 절입 경계일 — 연·월주 비단정(절대규칙 8-1) 회귀.

무엇을 검증하는가
-----------------
- 사연에서 감지한 상대의 출생 시각이 미상이고, 신고 민간 날짜 안에서 월건(입춘 포함)이
  바뀌면 상대의 연주·월주가 **고객 가시 문안**과 **factcheck 허용 토큰** 양쪽에서 사라지고
  확정 가능한 일주 중심 서술 + 고지로 대체된다.
- 판정 술어는 본인 경로와 같은 `three_pillar.ensure_unambiguous_civil_date` 단일 소스다
  (partner 에 월건 비교를 복제하면 이 파일의 경계 표가 조용히 갈린다).
- allow-set 축소가 **실제 방어**로 작동한다 — 억제된 간지를 주입한 합성 텍스트가 차단된다.

무엇을 검증하지 않는가
----------------------
- 접수 단계 차단·되묻기(운영자 미채택, 패킷 §3-1). 일주 억제(절대규칙 8과 동일 계약 유지).
- 사연 파서의 날짜 감지 정확도(별건 — `tests/test_partner.py`).
- 인물별 allow-set 분리. 허용 토큰은 주문 단위·토큰 수준이라 두 사람의 간지가 실제로
  겹치면 원리적으로 분리 불가하다(패킷 §12-4 미결). T8 은 겹치지 않는 쌍만 다룬다.
- factcheck 일상어 동형 예외(계신·임신·기사·무사·병사·정사·기미)는 이 패킷이 고치지 않는
  기존 구조다(패킷 §12-3). 결함 주입 케이스는 그 집합 **밖** 간지로 고른다.

PII: 입력 날짜·라벨·이름은 전부 합성이다. 실명·실고객 생년월일 0.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.calc import partner as calc_partner  # noqa: E402
from sajugen.content import builder, client_tone_lint, factcheck, rules  # noqa: E402

# 본인 명식(합성) — 기존 회귀 파일과 같은 앵커. 아래 상대 간지가 이 명식의 허용 집합
# (사주팔자·대운·세운·월운)과 겹치지 않는 날짜만 골랐다. 겹치면 부재 단언이 무의미해진다.
_SAJU = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
# 관계 계산용 고정 '본인' 인자 — 연·월주 판정과 무관하다(test_partner_axis.py 와 같은 관례).
_ME: dict = {
    "my_day_gan": "庚",
    "my_day_zhi": "午",
    "my_elements": {"木": 1, "火": 2, "土": 2, "金": 2, "水": 1},
    "my_yongshin": "",
}

# 경계일(민간 날짜 안에서 월건 전환) — 시각 미상 기준 산출값은 아래 주석의 간지.
_BOUNDARY_A = (2011, 4, 5)  # 辛卯년 辛卯월 庚寅일 (연·월주가 같은 간지)
_BOUNDARY_B = (1986, 2, 4)  # 乙丑년 己丑월 己卯일 (입춘 경계)
_PLAIN = (1999, 1, 18)  # 비경계일 — 戊寅년 乙丑월 庚午일 (기존 골든)

_NOTICE = "절기가 바뀌는 날"  # 고지 문장 앵커(문구 전문은 rules.py 단일 소스)


def _facts(ymd, hour=None, minute=0):
    return calc_partner.partner_pillars(ymd[0], ymd[1], ymd[2], hour, minute, **_ME)


# ---------------------------------------------------------------------------
# 1. 차단 방향 — 경계일 + 시각 미상이면 연·월주가 문안에서 사라진다
# ---------------------------------------------------------------------------


def test_boundary_unknown_hour_drops_year_month_from_text():
    """경계일 시각 미상: 연·월주 한글 간지 부재 / 일주 서술 존재 / 고지 존재."""
    blk_a = rules.partner_block(_facts(_BOUNDARY_A), _SAJU, label="합성상대")
    assert "신묘" not in blk_a  # 辛卯 = 연주이자 월주
    assert "경인일주" in blk_a  # 庚寅 일주는 확정 가능 — 억제하지 않는다
    assert _NOTICE in blk_a
    assert "시주는 제외" in blk_a  # 기존 시각 미상 고지 유지(별도 문단 신설 아님)

    blk_b = rules.partner_block(_facts(_BOUNDARY_B), _SAJU, label="합성상대")
    assert "을축" not in blk_b and "기축" not in blk_b  # 乙丑 연주 · 己丑 월주
    assert "기묘일주" in blk_b
    assert _NOTICE in blk_b

    # 상담가 문체 유지(외래어 린트) — 고지 확장이 문체를 깨지 않아야 한다.
    for blk in (blk_a, blk_b):
        assert client_tone_lint.loanword_lint(blk) == []


# ---------------------------------------------------------------------------
# 2. 정상 통과 방향(완화 감지) — 비경계일은 현행과 동일한 3기둥 표기
# ---------------------------------------------------------------------------


def test_non_boundary_unknown_hour_keeps_three_pillars():
    """비경계일 + 시각 미상: 연·월·일주 3기둥 표기 유지, 고지 없음."""
    blk = rules.partner_block(_facts(_PLAIN), _SAJU, label="합성상대")
    assert "무인" in blk and "을축" in blk and "경오일주" in blk
    assert _NOTICE not in blk
    assert "시주는 제외" in blk  # 시각 미상 고지 자체는 그대로


# ---------------------------------------------------------------------------
# 3. 과탐 감지 — 경계일이라도 시각이 알려지면 억제하지 않는다
# ---------------------------------------------------------------------------


def test_boundary_with_known_hour_is_not_suppressed():
    """경계일 + 시각 기지: 4기둥 현행 유지, 고지·시각 미상 문구 모두 없음."""
    blk = rules.partner_block(_facts(_BOUNDARY_A, hour=7), _SAJU, label="합성상대")
    assert "신묘" in blk  # 시각이 있으면 연·월주는 확정 사실
    assert _NOTICE not in blk
    assert "시주는 제외" not in blk


# ---------------------------------------------------------------------------
# 4. 플래그 경계 3행 — 술어가 hour is None 일 때만 발화한다
# ---------------------------------------------------------------------------


def test_ym_time_dependent_flag_boundary_table():
    assert _facts(_BOUNDARY_A).ym_time_dependent is True
    assert _facts(_BOUNDARY_B).ym_time_dependent is True
    assert _facts(_BOUNDARY_A, hour=7).ym_time_dependent is False
    assert _facts(_PLAIN).ym_time_dependent is False


def test_partner_block_requires_ym_time_dependent_flag():
    """고객 가시 억제 플래그가 없는 객체는 기본값으로 통과시키지 않는다."""
    attrs = vars(_facts(_PLAIN)).copy()
    attrs.pop("ym_time_dependent")
    missing_flag = SimpleNamespace(**attrs)

    with pytest.raises(AttributeError, match="ym_time_dependent"):
        rules.partner_block(missing_flag, _SAJU, label="합성상대")


def test_predicate_is_reused_not_reimplemented():
    """술어 단일 소스 — partner 가 three_pillar 판정을 그대로 쓴다(방법론 B-1).

    `ensure_unambiguous_civil_date` 가 raise 하는 날짜 집합과 플래그 True 집합이
    같은지 표본으로 대조한다. partner 가 월건 비교를 복제하면 두 집합이 갈린다.
    """
    from sajugen.calc.three_pillar import (
        NeedsInfoTimeBoundary,
        ensure_unambiguous_civil_date,
    )

    for ymd in (_BOUNDARY_A, _BOUNDARY_B, _PLAIN, (1990, 6, 6), (1990, 3, 15)):
        try:
            ensure_unambiguous_civil_date(*ymd)
            expected = False
        except NeedsInfoTimeBoundary:
            expected = True
        assert _facts(ymd).ym_time_dependent is expected, ymd


# ---------------------------------------------------------------------------
# 5. 허용 토큰 — allow-set 에서도 연·월주가 빠진다 (가장 중요한 배선)
# ---------------------------------------------------------------------------

_CONCERN_ONE = "여자친구 1986-02-04 인데 저랑 잘 맞을지 궁금합니다."


def _report_for(concern):
    return builder.build_report(_SAJU, use_llm=False, ref_year=2026, concern=concern)


def test_allowed_tokens_exclude_suppressed_year_month():
    r = _report_for(_CONCERN_ONE)
    consult = next(s for s in r.sections if s.id == "consult")
    # fail-closed 전제: 상대 블록이 실제로 주입됐을 때만 부재 단언이 의미를 갖는다.
    assert "의 명식" in consult.rule_text
    assert r.partner_present is True

    gz = set(r.allow_tokens["ganzhi"])
    gz_ko = set(r.allow_tokens["ganzhi_ko"])
    assert "己卯" in gz and "기묘" in gz_ko  # 일주는 허용(양성 대조)
    assert "乙丑" not in gz and "을축" not in gz_ko  # 연주 억제
    assert "己丑" not in gz and "기축" not in gz_ko  # 월주 억제
    assert r.guard.clean is True


# ---------------------------------------------------------------------------
# 6. 결함 주입 — 억제된 간지를 되살린 텍스트가 실제로 차단된다
# ---------------------------------------------------------------------------


def test_suppressed_ganzhi_injection_is_blocked():
    """allow-set 축소가 방어로 작동함을 증명. 문안에서만 빼면 여기서 통과해버린다.

    주입 간지 `乙丑`(을축)·`己丑`(기축)은 factcheck 일상어 동형 집합
    (계신·임신·기사·무사·병사·정사·기미) **밖**이라 검사가 실제로 발화한다.
    """
    r = _report_for(_CONCERN_ONE)
    allow = r.allow_tokens

    assert factcheck.check_with_allow("그분은 을축년 기축월생이에요.", allow)
    assert factcheck.check_with_allow("그분의 명식은 乙丑 己丑 입니다.", allow)
    # 양성 대조 — 억제하지 않은 일주는 통과해야 한다(과차단 감지).
    assert factcheck.check_with_allow("그분은 기묘일주예요.", allow) == []


# ---------------------------------------------------------------------------
# 7. 파생 축소 — 보완 오행이 일주 기준으로 좁아진다
# ---------------------------------------------------------------------------


def test_complements_narrowed_to_day_pillar_on_boundary():
    """경계일 시각 미상: 연·월주에만 있던 오행은 보완 목록에서 빠진다.

    합성 케이스 1990-06-06(경계일) = 庚午년 壬午월 壬寅일.
    연·월주에만 있는 오행 = 火(午)·金(庚), 일주 오행 = 水(壬)·木(寅).
    본인 부족 오행을 火·水로 두면 교정 전에는 '화·수', 교정 후에는 '수'만 남는다.
    `matches_my_yongshin` 은 이미 일간 기준이라 이 패킷의 축소 대상이 아니다.
    """
    weak_fire_water = {"木": 1, "火": 0, "土": 1, "金": 1, "水": 0}
    pf = calc_partner.partner_pillars(
        1990, 6, 6, None, my_day_gan="甲", my_day_zhi="子", my_elements=weak_fire_water
    )
    assert pf.ym_time_dependent is True
    assert pf.complements_elems_ko == ["수"]  # '화'(월지 午)는 빠진다

    # 비경계일 대조 — 축소가 상시 발화하지 않는다(과탐 감지).
    pf_plain = calc_partner.partner_pillars(
        1999, 1, 18, None, my_day_gan="甲", my_day_zhi="子", my_elements=weak_fire_water
    )
    assert pf_plain.ym_time_dependent is False
    assert "화" in pf_plain.complements_elems_ko


def test_matches_my_yongshin_unchanged_on_boundary():
    """용신 일치 판정은 일간 기준이라 경계일에도 계산 근거가 달라지지 않는다."""
    pf = calc_partner.partner_pillars(  # 일간 壬 = 수
        1990,
        6,
        6,
        None,
        my_day_gan="甲",
        my_day_zhi="子",
        my_elements={"木": 1, "火": 1, "土": 1, "金": 1, "水": 1},
        my_yongshin="수",
    )
    assert pf.day_gan_elem_ko == "수"
    assert pf.matches_my_yongshin is True


# ---------------------------------------------------------------------------
# 8. 다인 케이스 — 다른 상대 때문에 억제 간지가 되살아나지 않는다
# ---------------------------------------------------------------------------

# A = 1986-02-04(경계일, 乙丑·己丑 억제 / 己卯 유지), B = 1993-02-14(비경계일, 癸酉·甲寅·丙寅).
# 두 사람의 간지가 겹치지 않는 쌍만 고른다 — 겹치면 토큰 수준 허용이라 분리 불가(§12-4).
_CONCERN_TWO = "여자친구 1986-02-04 이고 남사친 1993-02-14 인데 둘 다 궁금합니다."


def test_multi_partner_allow_set_does_not_revive_suppressed():
    r = _report_for(_CONCERN_TWO)
    consult = next(s for s in r.sections if s.id == "consult")
    assert consult.rule_text.count("의 명식") >= 2  # 두 사람 모두 주입됐을 때만 유효

    gz = set(r.allow_tokens["ganzhi"])
    assert {"癸酉", "甲寅", "丙寅"} <= gz  # 비경계일 상대는 현행 유지
    assert "己卯" in gz  # 경계일 상대의 일주는 유지
    assert "乙丑" not in gz and "己丑" not in gz  # 경계일 상대의 연·월주는 여전히 부재


# ---------------------------------------------------------------------------
# 9. PII 0 — 생년월일 원본이 문안에 남지 않는다
# ---------------------------------------------------------------------------


def test_no_birth_digits_in_partner_blocks():
    for ymd in (_BOUNDARY_A, _BOUNDARY_B, _PLAIN):
        blk = rules.partner_block(_facts(ymd), _SAJU, label="합성상대")
        assert str(ymd[0]) not in blk
        assert f"{ymd[1]:02d}{ymd[2]:02d}" not in blk
