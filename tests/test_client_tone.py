# -*- coding: utf-8 -*-
"""고객 본문 톤 — 외래어 hard-ban·날것 계산표현·전문용어 + 결정론 자연화 검증(H1.5)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import client_tone_lint as ct  # noqa: E402


def _lw(t):
    return [x["match"] for x in ct.loanword_lint(t)]


def test_loanword_43_and_drive_separate():
    assert len(ct.LOANWORDS) == 43
    assert _lw("한 지붕 아래 두 드라이버") == ["드라이버"]
    assert _lw("강한 드라이브가 필요해요") == ["드라이브"]
    for w in [
        "포지션",
        "리스크",
        "시스템",
        "브레이크",
        "에너지",
        "아이디어",
        "콘텐츠",
        "컨디션",
        "패턴",
        "타입",
        "파트너",
        "팀",
    ]:
        assert w in _lw(f"이건 {w}예요"), w


def test_loanword_no_false_positive():
    assert _lw("남자다운 모습과 사람다운 태도") == []  # '-다운' 접미사 오탐 0
    assert _lw("스스로 버티는 힘이 강한 사주입니다") == []
    assert _lw("이 팀이 함께 일한다") == ["팀"]  # 조사 뒤는 잡힘


def test_loanword_lint_compounds_not_flagged():
    # 합성어·접미사는 오탐하지 않아야 함(전부 [])
    for s in ["남자다운 사람", "사람다운 선택", "메인팀", "운영팀", "팀장", "스스로 버티는 힘"]:
        assert _lw(s) == [], f"오탐: {s} → {_lw(s)}"


def test_loanword_lint_real_hits_detected():
    # 조사/어미 뒤 외래어는 반드시 검출
    assert _lw("이 팀이 움직인다") == ["팀"]
    assert _lw("좋은 타이밍이다") == ["타이밍"]
    assert _lw("포지션을 잡는다") == ["포지션"]
    assert _lw("리스크가 있다") == ["리스크"]
    assert _lw("드라이버가 둘이다") == ["드라이버"]
    assert _lw("에너지를 많이 쓴다") == ["에너지"]


def test_raw_calc_head_vs_count():
    assert ct.raw_calc_headwords("오행 분포를 보면")
    assert ct.raw_calc_headwords("신강약은 신약입니다")
    assert ct.raw_calc_headwords("십성축이 재성")
    assert ct.raw_calc_lint("목 2, 화 2, 토 2")  # 카운트열
    assert not ct.raw_calc_headwords("목 2, 화 2, 토 2")  # 카운트는 표제형 아님
    assert ct.raw_calc_lint("사주 안의 다섯 기운을 보면") == []  # 자연어 허용


def test_raw_calc_ohaeng_ui_bunpo():
    # H1.5.2: '오행의 분포' 변형도 표제형으로 검출(개인 PDF p8 잔존 잡기)
    assert ct.raw_calc_lint("오행의 분포를 보면 목의 힘이 또렷합니다")
    assert ct.raw_calc_headwords("오행의 분포를 보면 목의 힘이 또렷합니다")
    assert ct.raw_calc_lint("오행의 분포")
    assert ct.raw_calc_headwords("오행의 분포")
    assert ct.raw_calc_lint("오행 분포")  # 기존도 유지
    # 자연어 대체 표현은 미매칭(허용)
    assert ct.raw_calc_lint("사주 안의 다섯 기운을 보면 목의 힘이 또렷합니다") == []
    assert ct.raw_calc_lint("다섯 기운을 보면") == []
    assert ct.raw_calc_lint("목의 힘이 또렷하고 금의 힘이 옅습니다") == []


def test_normalize_loanwords_josa():
    # H1.5.1: 외래어 치환 + 대체어 받침에 맞춘 조사 보정(문법 오류 방지)
    cases = {
        "아이디어가 떠올랐다": "생각이 떠올랐다",
        "아이디어를 정리한다": "생각을 정리한다",
        "에너지가 강하다": "기운이 강하다",
        "에너지를 쓴다": "기운을 쓴다",
        "콘텐츠를 만든다": "글을 만든다",
        "파트너가 중요하다": "동업자가 중요하다",
        "팀이 움직인다": "세 사람이 움직인다",
        "타이밍을 본다": "때를 본다",
        "포지션을 잡는다": "역할을 잡는다",
        "리스크가 있다": "위험이 있다",
        "시스템을 만든다": "체계를 만든다",
        "드라이버가 둘이다": "주도하는 사람이 둘이다",
        "드라이브를 건다": "추진력을 건다",
        "브레이크를 건다": "제동을 건다",
        "에너지와 기운": "기운과 기운",  # 와→과(받침)
        "시스템으로 간다": "체계로 간다",  # 으로→로(받침 없음)
    }
    for src, exp in cases.items():
        assert ct.normalize_loanwords(src) == exp, (
            f"{src} → {ct.normalize_loanwords(src)} (기대 {exp})"
        )


def test_normalize_loanwords_endings():
    # H1.5.1: 어미형(이다·입니다·이에요…)도 순화 — loanword_lint 검출 범위와 일치
    cases = {
        "타이밍이다": "때다",
        "포지션입니다": "역할입니다",
        "시스템입니다": "체계입니다",
        "리스크입니다": "위험입니다",
        "팀입니다": "세 사람입니다",
        "에너지예요": "기운이에요",
        "드라이버입니다": "주도하는 사람입니다",
        "콘텐츠입니다": "글입니다",
    }
    for src, exp in cases.items():
        assert ct.normalize_loanwords(src) == exp, (
            f"{src} → {ct.normalize_loanwords(src)} (기대 {exp})"
        )
    # 순화 후 loanword_lint 0건
    for s in [
        "타이밍이다",
        "포지션입니다",
        "시스템이에요",
        "리스크입니다",
        "팀입니다",
        "에너지예요",
    ]:
        assert ct.loanword_lint(ct.normalize_loanwords(s)) == [], s


def test_normalize_loanwords_particles_aligned():
    # H1.5.1: _NORM_TAIL = _JOSA_LA 정렬 — loanword_lint가 잡는 조사/어미는 normalize도 처리
    cases = {
        "포지션에서 맡을 일을 본다": "역할에서 맡을 일을 본다",
        "리스크까지 본다": "위험까지 본다",
        "시스템에 넣는다": "체계에 넣는다",
        "팀들끼리 움직인다": "세 사람끼리 움직인다",
        "타이밍쯤 본다": "때쯤 본다",
        "파트너에게 맡긴다": "동업자에게 맡긴다",
        "콘텐츠마다 다르다": "글마다 다르다",
        "데이터보다 흐름이 중요하다": "자료보다 흐름이 중요하다",
        "케이스도 있다": "경우도 있다",
        "플랜만 세우지 마라": "계획만 세우지 마라",
        "스타일의 차이다": "방식의 차이다",
        "포인트나 이슈가 아니다": "핵심이나 문제가 아니다",
    }
    for src, exp in cases.items():
        got = ct.normalize_loanwords(src)
        assert got == exp, f"{src} → {got} (기대 {exp})"
        assert ct.loanword_lint(got) == [], f"순화 후 잔존: {got}"


def test_normalize_team_plural():
    # H1.5.1: '팀들' → '세 사람들'(어색) 방지 → '세 사람' + 조사
    cases = {
        "팀들끼리 움직인다": "세 사람끼리 움직인다",
        "팀들이 움직인다": "세 사람이 움직인다",
        "팀들은 움직인다": "세 사람은 움직인다",
        "팀들을 본다": "세 사람을 본다",
        "팀들의 차이다": "세 사람의 차이다",
    }
    for src, exp in cases.items():
        got = ct.normalize_loanwords(src)
        assert got == exp, f"{src} → {got} (기대 {exp})"
        assert ct.loanword_lint(got) == [], f"순화 후 잔존: {got}"
    # 다른 외래어 복수는 '들' 유지(정상)
    assert ct.normalize_loanwords("드라이버들이 많다") == "주도하는 사람들이 많다"
    assert ct.normalize_loanwords("파트너들과 간다") == "동업자들과 간다"
    # 기존 단수·합성어 동작 유지
    assert ct.normalize_loanwords("팀이 움직인다") == "세 사람이 움직인다"
    assert ct.normalize_loanwords("팀입니다") == "세 사람입니다"
    for s in ["메인팀", "운영팀", "팀장"]:
        assert ct.normalize_loanwords(s) == s


def test_normalize_endings_no_false_positive():
    for s in ["남자다운 사람", "사람다운 선택", "메인팀", "운영팀", "팀장", "스스로 버티는 힘"]:
        assert ct.normalize_loanwords(s) == s, f"오탐: {s} → {ct.normalize_loanwords(s)}"


def test_normalize_loanwords_no_false_positive():
    for s in ["남자다운 사람", "사람다운 선택", "메인팀", "운영팀", "스스로 버티는 힘이 강한 사주"]:
        assert ct.normalize_loanwords(s) == s, f"오탐: {s} → {ct.normalize_loanwords(s)}"


def test_normalize_then_lint_clean():
    src = "이 팀이 함께 맡을 포지션을 잡고, 좋은 아이디어와 에너지를 쓴다"
    assert ct.loanword_lint(ct.normalize_loanwords(src)) == []


def test_term_hits_report_only():
    assert ct.term_hits("환경과 사람을 잘 만날 때 힘이 나는 사주입니다(신약)")


# ───────────────── H1.5.3: 이름 호칭 정책 ─────────────────
_FULL = ["김태수", "김태성", "장순조"]


def _np(s):
    return [h["match"] for h in ct.name_policy_lint(s, _FULL)]


def test_name_policy_detects_violations():
    # 조사·부호·명사형·단독·쌍·붙은씨 모두 검출(최신 실제 문형 포함)
    for s in [
        "김태수는 임인일주입니다",
        "김태성은 무오일주입니다",
        "장순조는 기미일주입니다",
        "김태수를",
        "김태수의",
        "김태수에게",
        "김태수, 먼저",
        "김태수: 본문",
        "김태수의 자리",
        "김태성의 살아나는 결",
        "김태수 사주",
        "김태수 명식",
        "태수씨는 옵니다",
    ]:
        assert _np(s), f"미검출: {s}"
    # 쌍(본문 전체이름) — 양쪽 다 잡힘
    assert _np("김태수와 김태성")
    assert _np("김태수와 장순조")
    assert _np("김태성과 장순조")


def test_name_policy_standalone_line():
    assert _np("김태수")  # 줄 단독 전체이름


def test_name_policy_allows():
    assert _np("김태수 · 김태성 · 장순조") == []  # 표지 가운뎃점 나열
    assert _np("김태수 씨는 임인일주입니다") == []  # 첫 소개 1회
    assert _np("태수 씨는 임인일주입니다") == []
    assert _np("태수 씨 명식") == []
    assert _np("태수와 태성") == []
    assert _np("태수와 순조") == []
    assert _np("태성과 순조") == []


def test_name_policy_first_intro_once_pdf_wide():
    one = "김태수 씨는 임인일주입니다. 돈의 흐름을 봅니다."
    assert ct.name_policy_lint(one, _FULL) == []  # 1회 허용
    two = "김태수 씨는 임인일주입니다. 그리고 김태수 씨는 돈을 봅니다."
    hits = [h["kind"] for h in ct.name_policy_lint(two, _FULL)]
    assert "중복소개" in hits  # 2회째 위반


def test_normalize_names():
    cases = {
        "김태수는": "태수 씨는",
        "김태수를": "태수 씨를",
        "김태수의": "태수 씨의",
        "김태수에게": "태수 씨에게",
        "김태수, 먼저": "태수 씨, 먼저",
        "김태수:": "태수 씨:",
        "김태수 사주": "태수 씨 사주",
        "김태수 명식": "태수 씨 명식",
        "김태수와 김태성": "태수와 태성",
        "김태수와 장순조": "태수와 순조",
        "김태성과 장순조": "태성과 순조",
        "태수씨는": "태수 씨는",
        "태성씨가": "태성 씨가",
        "순조씨를": "순조 씨를",
        "김태성은": "태성 씨는",
        "김태수 · 김태성 · 장순조": "김태수 · 김태성 · 장순조",  # 표지 보존
    }
    for src, exp in cases.items():
        got = ct.normalize_names(src, _FULL)
        assert got == exp, f"{src} → {got} (기대 {exp})"
    # 순화 후 본문 정책 위반 0(가운뎃점 제외)
    for src in cases:
        if "·" not in src:
            assert ct.name_policy_lint(ct.normalize_names(src, _FULL), _FULL) == [], src
    # 2회째 'FULL 씨'만 호칭화(첫 소개 보존)
    assert (
        ct.normalize_names("김태수 씨는 좋고 김태수 씨는 또", _FULL)
        == "김태수 씨는 좋고 태수 씨는 또"
    )


# ───────────────── H1.5.3: 일간 role 오류 ─────────────────
# 개인(태수) 단일 주체 — expected 임수.
_EG, _ET = {"임"}, {"임수"}
_SPECS = [(["김태수", "태수", "태수님", "태수 씨", "자기 자신", "나 자신", "본인", "자신"], "임수")]


def _ir(s):
    return [h["match"] for h in ct.identity_role_lint(s, _EG, _ET, _SPECS)]


def test_identity_role_detects():
    for s in [
        "일간 계수",
        "계수 일간",
        "일간 무토",
        "무토 일간",
        "일간 갑목",
        "일간 병화",
        "경금 일간",
        "중심 글자는 계수",
        "태수님은 계수",
        "태수 씨는 계수",
        "김태수는 계수",
        "태수님은 무토",
        "자기 자신은 계수",
        "나 자신은 계수",
        "태수 씨 일간은 계수",
        "태수 씨의 일간은 계수",
        "김태수 일간 계수",
        "김태수의 일간은 계수",
        "태수 씨 일간은 무토",
    ]:
        assert _ir(s), f"미검출: {s}"


def test_identity_role_allows():
    for s in [
        "일간 임수",
        "임수 일간",
        "태수님은 임수",
        "태수 씨 일간은 임수",
        "김태수의 일간은 임수",
        "계사 월운",
        "계묘 대운",
        "지장간 계",
        "운에서 계가 들어온다",
        "연주 지장간에 계가 있다",
        "올해는 계수 기운이 들어와",
        "태수 씨는 계수 대운에",
    ]:
        assert _ir(s) == [], f"오탐: {s} → {_ir(s)}"


def test_identity_role_gunghap_subject_specific():
    # 궁합 합집합(임수/무토/기토)에서도 주체별 정확 판정 — 합집합 우회 방지
    eg, et = {"임", "무", "기"}, {"임수", "무토", "기토"}
    specs = [
        (["김태수", "태수", "태수 씨"], "임수"),
        (["김태성", "태성", "태성 씨"], "무토"),
        (["장순조", "순조", "순조 씨"], "기토"),
    ]

    def ir2(s):
        return ct.identity_role_lint(s, eg, et, specs)

    assert ir2("태수 씨 일간은 무토입니다")  # 태수≠무토 → 위반
    assert ir2("태수 씨 일간은 계수입니다")  # 위반
    assert ir2("태성 씨 일간은 무토입니다") == []  # 태성=무토 → 통과
    assert ir2("순조 씨 일간은 기토입니다") == []  # 순조=기토 → 통과
    assert ir2("태수 씨 일간은 임수입니다") == []  # 통과


def test_normalize_names_pdfwide():
    # H1.5.3.1: 섹션 여러 개에 걸친 'FULL 씨' 반복을 PDF 전체 기준 첫 소개 1회만 보존
    texts = [
        "김태수 씨는 임인일주입니다. 김태성 씨는 무오일주입니다.",
        "김태수 씨의 재물 흐름은 좋고, 김태성 씨는 틀을 세웁니다.",
        "김태수와 김태성은 함께 움직입니다. 장순조 씨는 중심입니다.",
        "장순조 씨의 역할은 버팀목입니다.",
    ]
    out = ct.normalize_names_pdfwide(texts, _FULL)
    # 첫 text의 첫 소개는 보존
    assert "김태수 씨는" in out[0] and "김태성 씨는" in out[0]
    # 2회째부터 호칭으로 강등
    assert "태수 씨의" in out[1] and "김태수 씨의" not in out[1]
    assert "태성 씨는" in out[1] and "김태성 씨는" not in out[1]
    assert "태수와 태성" in out[2] and "김태수와 김태성" not in out[2]
    assert "장순조 씨는" in out[2]  # 장순조 첫 소개(여기서 처음)
    assert "순조 씨의" in out[3] and "장순조 씨의" not in out[3]
    # PDF 전체 합치면 name_policy 위반 0
    assert ct.name_policy_lint("\n".join(out), _FULL) == []
    # 가운뎃점 보존 / 붙은씨·명사형 보정
    assert ct.normalize_names_pdfwide(["김태수 · 김태성 · 장순조"], _FULL) == [
        "김태수 · 김태성 · 장순조"
    ]
    assert ct.normalize_names_pdfwide(["태수씨는 옵니다"], _FULL) == ["태수 씨는 옵니다"]
    assert ct.normalize_names_pdfwide(["김태수 사주가 좋다"], _FULL) == ["태수 씨 사주가 좋다"]


# ───────────────── H1.5.3.2: 신강약 group/role ─────────────────
_SG_SPECS = [
    {"full": "김태수", "given": "태수", "honor": "태수 씨", "singang": "신약"},
    {"full": "김태성", "given": "태성", "honor": "태성 씨", "singang": "신약"},
    {"full": "장순조", "given": "순조", "honor": "순조 씨", "singang": "신강"},
]


def _sg(s):
    return ct.singang_role_lint(s, _SG_SPECS)


def test_singang_group_and_role_detects():
    for s in [
        "세 사람 모두 신약입니다",
        "세 사람은 모두 신약입니다",
        "세 사람 다 신약입니다",
        "세 명 모두 신약입니다",
        "세 분 모두 신약입니다",
        "셋 다 신약입니다",
        "전원 신약입니다",
        "이 조합은 모두 신약입니다",
        "이 조합이 모두 신강입니다",
        "세 사람 모두 신약이거나 안정 쪽에 무게가 있습니다",
        "세 사람 모두 신강입니다",
        "전원 신강입니다",
        "순조 씨는 신약입니다",
        "장순조는 신약입니다",
        "태수 씨는 신강입니다",
        "김태수는 신강입니다",
        "태성 씨는 신강입니다",
        "김태성은 신강입니다",
        "순조 씨의 사주는 신약입니다",
        "순조 씨의 명식은 신약입니다",
        "순조 씨의 힘의 강약은 신약입니다",
        "태수 씨의 사주는 신강입니다",
        "김태수의 명식은 신강입니다",
    ]:
        assert _sg(s), f"미검출: {s}"


def test_singang_allows():
    for s in [
        "태수 씨는 신약입니다",
        "태성 씨는 신약입니다",
        "순조 씨는 신강입니다",
        "태수 씨와 태성 씨는 모두 신약이고, 순조 씨는 신강입니다",
        "태수 씨와 태성 씨 모두 신약이고, 순조 씨는 신강입니다",
        "태수 씨와 태성 씨는 신약이고, 순조 씨는 신강입니다",
        "순조 씨의 사주는 신강입니다",
        "태수 씨의 명식은 신약입니다",
        "태수 씨와 태성 씨는 환경을 잘 만날 때 힘이 나고, 순조 씨는 스스로 버티는 힘이 강합니다",
        "세 사람 모두 재고를 갖고 있습니다",
        "세 사람 모두 역할을 나눠야 합니다",
    ]:
        assert _sg(s) == [], f"오탐: {s} → {_sg(s)}"


def test_name_honor_helpers():
    assert ct.given_name("김태수") == "태수"
    assert ct.given_name("장순조") == "순조"
    assert ct.honor("김태수") == "태수 씨"
    assert ct.intro("김태수") == "김태수 씨"
    assert ct.pair_label("김태수", "김태성") == "태수와 태성"
    assert ct.pair_label("김태성", "장순조") == "태성과 순조"
    assert ct.gan_to_term("임") == "임수"


def test_gunghap_person_slot_natural():
    from sajugen import gunghap as g

    p = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    slot = g._person_slot(p)
    for bad in ("오행 분포", "십성축", "포지션", "신강약"):
        assert bad not in slot, f"슬롯 잔존: {bad!r} in {slot}"
    assert ct.loanword_lint(slot) == [], ct.loanword_lint(slot)
    assert ct.raw_calc_headwords(slot) == [], ct.raw_calc_headwords(slot)


def test_personal_rules_body_natural(monkeypatch):
    # 룰경로 본문(해석 산문)에 외래어·표제형 계산표현 0건(부록 제외).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder
    from sajugen.content.sections_schema import _STATIC_OK

    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(saju, use_llm=False, ref_year=2026, name="김태수")
    body = "\n".join(s.final_text for s in rep.sections if s.id not in _STATIC_OK)
    assert ct.loanword_lint(body) == [], ct.loanword_lint(body)
    assert ct.raw_calc_headwords(body) == [], ct.raw_calc_headwords(body)
    assert "신강약" not in body and "오행 분포" not in body and "컨디션" not in body


def test_love_consult_rule_text_tone_clean(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        name="김태수",
        concern="전남친과 재회 시기 언제가 좋을까요",
    )
    text = rep.section("consult").final_text
    assert ct.loanword_lint(text) == [], ct.loanword_lint(text)
    assert ct.raw_calc_headwords(text) == [], ct.raw_calc_headwords(text)


def test_new_love_and_marriage_consult_rule_text_tone_clean(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder
    from sajugen.content import safe_lint

    saju = engine.build(1997, 10, 27, 9, 46, is_male=True, horoscope_date="2026-06-01")
    concerns = [
        "연애를 못한 지 오래됐는데 앞으로 1년 안에 만남이 들어올까요. 소개팅을 받아도 되는지 궁금합니다",
        "나이가 있어서 언제 결혼운이 들어오는지 궁금합니다. 지금 만나는 사람과 결혼까지 봐도 될까요",
    ]
    for concern in concerns:
        rep = builder.build_report(
            saju,
            use_llm=False,
            ref_year=2026,
            name="김태수",
            concern=concern,
        )
        text = rep.section("consult").final_text
        assert ct.loanword_lint(text) == [], ct.loanword_lint(text)
        assert ct.raw_calc_headwords(text) == [], ct.raw_calc_headwords(text)
        assert safe_lint.lint(text) == [], safe_lint.lint(text)
        assert "또렷" not in text
        assert "재회합니다" not in text and "결혼합니다" not in text
