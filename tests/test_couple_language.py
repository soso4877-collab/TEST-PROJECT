# -*- coding: utf-8 -*-
"""QI-2026-07-04 팬텀 파트너 — 커플 지칭 게이트 양방 회귀.

증상: 궁합 없는 개인 풀이에 궁합·관계 문구 혼입. 원인 2층 = (1) 팬텀 파트너 배선 버그
(test_partner.py 에 회귀 있음) + (2) 커플 언어 게이트 부재(product dead parameter).
이 파일은 (2)의 회귀: 1인 문서(파트너 부재)에서 커플 지칭 = FAIL, 파트너 있는 개인 풀이·
다인 상품에서는 정상 통과(오탐 0)를 고정한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, client_tone_lint as ct  # noqa: E402
from sajugen.render import verify as V  # noqa: E402

_SAJU = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")


# ---- lint 단위: 커플 지칭 검출(candidate) ----
def test_couple_pair_rule_detects_pair_language():
    hits = ct.placeholder_residue_lint("두 사람의 인연은 깊고, 두 분이 함께 갑니다.")
    rules_found = {h["rule"] for h in hits}
    assert "couple_pair_reference" in rules_found
    assert all(h["severity"] == "candidate" for h in hits if h["rule"] == "couple_pair_reference")


def test_strict_helper_escalates_only_when_pairless():
    text = "두 사람의 결이 잘 맞습니다."
    assert ct.placeholder_residue_strict_violations(text, strict_pair=True)  # 1인 문서 = 위반
    assert not ct.placeholder_residue_strict_violations(text, strict_pair=False)  # 파트너 有 = 정상
    # hard 룰은 strict 여부와 무관하게 항상 위반
    assert ct.placeholder_residue_strict_violations("상대 분의 명식", strict_pair=False)


# ---- verify 판정: product + partner_present 승격 ----
_CAND = [{"severity": "candidate", "rule": "couple_pair_reference", "count": 1}]


def test_verify_clean_escalates_personal_without_partner():
    assert (
        V._placeholder_residue_hits_clean(_CAND, product="integrated", partner_present=False)
        is False
    )


def test_verify_clean_allows_partner_and_multi_products():
    # 파트너 있는 개인 풀이 = 정상(상대방 사주 포함 기능)
    assert (
        V._placeholder_residue_hits_clean(_CAND, product="integrated", partner_present=True) is True
    )
    # 다인 상품 = 정상 표현(오탐 0)
    for prod in ("gunghap", "relationship", "integrated_full"):
        assert V._placeholder_residue_hits_clean(_CAND, product=prod, partner_present=False) is True
    # 레거시 호출(partner_present 미상) = 기존 동작 유지(back-compat)
    assert (
        V._placeholder_residue_hits_clean(_CAND, product="integrated", partner_present=None) is True
    )
    # hard 는 어디서나 실패(비완화 앵커)
    hard = [{"severity": "hard", "rule": "generic_customer_address", "count": 1}]
    assert V._placeholder_residue_hits_clean(hard, product="gunghap", partner_present=True) is False


# ---- 골격 위생: 파트너 없는 개인 풀이 본문에 커플 지칭 0 ----
def test_personal_skeleton_has_no_couple_language():
    r = builder.build_report(
        _SAJU,
        use_llm=False,
        ref_year=2026,
        name="테스트",
        concern="결혼운이 궁금합니다. 좋은 사람을 만날 수 있을까요?",
    )
    assert r.partner_present is False
    for s in r.sections:
        viol = ct.placeholder_residue_strict_violations(s.final_text, strict_pair=True)
        assert not viol, (s.id, viol)


def test_partner_present_flag_true_with_partner_block():
    r = builder.build_report(
        _SAJU,
        use_llm=False,
        ref_year=2026,
        name="테스트",
        concern="그친구는 990118 양력인데 왜 끌리는지 궁금해요.",
    )
    assert r.partner_present is True
    consult = next(s for s in r.sections if s.id == "consult")
    # 파트너 명식의 커플 서술은 정상 — strict_pair=False 기준으로 위반 아님
    assert not ct.placeholder_residue_strict_violations(consult.final_text, strict_pair=False)


# ---- F2: 재회 전제 문구는 원문에 재회 토큰이 있을 때만 ----
def test_love_consult_without_reunion_token_has_no_reunion_phrases():
    r = builder.build_report(
        _SAJU,
        use_llm=False,
        ref_year=2026,
        name="테스트",
        concern="결혼운이 궁금합니다. 좋은 사람을 만날 수 있을까요?",
    )
    consult = next(s for s in r.sections if s.id == "consult")
    for phrase in ("재회", "붙잡는", "예전 문제"):
        assert phrase not in consult.final_text, phrase


def test_love_consult_with_reunion_token_keeps_reunion_guidance():
    r = builder.build_report(
        _SAJU,
        use_llm=False,
        ref_year=2026,
        name="테스트",
        concern="헤어진 남자친구와 재회할 수 있을까요?",
    )
    consult = next(s for s in r.sections if s.id == "consult")
    assert "재회" in consult.final_text  # 재회 질문에 재회 답변은 정당(과수정 금지 앵커)
