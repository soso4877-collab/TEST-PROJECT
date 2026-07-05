# -*- coding: utf-8 -*-
"""P1(2026-07-05) 직답 골격 재작성 — v7 실격 후속(운영자: 직답 맥빠짐·유보 프레임).

골격 consult 가 [방향 단정]→[근거 겹침(궁 실명)]→[시기]→[첫 행동] 구조로, 전 가드
(안전·메타·보장·날것 계산어·외래어)를 통과하면서 충분한 밀도를 가짐을 카테고리
전수 실빌드로 고정한다. PII 0(합성 입력만).
2026-07-05 운영자 지시 개정: 1장(intro) 직답 문단(concern_snapshot)·frontload 게이트는
폐기 — 신청 질문 직답은 consult 장 전담(아래 역방향 앵커 테스트로 고정).
검증하지 않는 것: LLM 윤문 품질(골격 하한만 고정).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import client_tone_lint as ct  # noqa: E402
from sajugen.content import (  # noqa: E402
    customer_meta_lint,
    delivery_quality,
    rules,
    safe_lint,
)

_CATS = ["연애", "직업", "재물", "건강", "대인", "시기", "전반"]
_CONCERNS = [None, "합성 고민 텍스트입니다. 방향이 궁금합니다."]


def _saju(unknown_time=False):
    return engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")


def _guards(text: str) -> list:
    return (
        safe_lint.lint(text)
        + customer_meta_lint.lint(text)
        + delivery_quality.guarantee_lint(text)
        + ct.raw_calc_lint(text)
        + ct.loanword_lint(text)
    )


def test_consult_skeleton_all_categories_pass_guards_with_density():
    # 카테고리 7종 x concern 유/무 = 14케이스 전수: 가드 0 + generic 밀도 하한.
    saju = _saju()
    for cat in _CATS:
        for concern in _CONCERNS:
            T = rules.build_all(
                saju, ref_year=2026, name="테스트", concern_category=cat, concern_text=concern
            )
            for sid in ("consult", "intro"):
                hits = _guards(T[sid])
                assert hits == [], (cat, concern, sid, hits[:4])
            dense = len(T["consult"].replace(" ", "").replace("\n", ""))
            # 연애는 F2 분기(전용 본문), 그 외 골격은 800자 이상(v7 실측 388자 재발 차단).
            floor = 550 if cat == "연애" else 800
            assert dense >= floor, (cat, concern, dense)


def test_consult_generic_else_has_direction_timing_action():
    # generic-else 가 [방향 단정]+[시기]+[첫 행동]을 실제로 담는다(유보 체크리스트 재발 차단).
    saju = _saju()
    T = rules.build_all(
        saju,
        ref_year=2026,
        name="테스트",
        concern_category="전반",
        concern_text="흐름이 궁금합니다.",
    )
    consult = T["consult"]
    assert "결론부터 말하면" in consult  # 방향 단정 리드
    assert "2026년 하반기부터 2027년 상반기까지" in consult  # 시기 실명
    assert "첫걸음" in consult  # 첫 행동
    assert "하나씩 짚은 뒤에 정하셔도" not in consult  # 구 유보 프레임 부재
    # 자미 궁 실명 근거(시진 확정 케이스): 궁 이름이 등장한다.
    assert "궁" in consult


def test_consult_palace_line_absent_when_unknown_time():
    # 절대규칙 8: 시진 불명이면 자미 궁 문장 생략(명리 단독 강등) — 궁 실명 미노출.
    saju = _saju()
    T = rules.build_all(
        saju,
        ref_year=2026,
        name="테스트",
        unknown_time=True,
        concern_category="재물",
        concern_text="돈 흐름이 궁금합니다.",
    )
    assert "자미두수에서 같은 영역을 비추는 자리는" not in T["consult"]


def test_intro_no_direct_answer_answer_lives_in_consult():
    # 2026-07-05 운영자 지시 개정(역방향 앵커): 1장(intro) 직답 문단 제거 — 도입은
    # '사주를 펼쳐 놓고 보면…' 요약 카드로 시작하고, 신청 질문 직답은 consult 장이 전담한다.
    # (구 test_snapshot_is_decisive_not_hedging 을 반대 방향으로 재정의)
    saju = _saju()
    T = rules.build_all(
        saju, ref_year=2026, name="테스트", concern_category="재물", concern_text="돈 고민입니다."
    )
    intro = T["intro"]
    assert "신청 질문부터 먼저 답하면" not in intro  # 직답 문단 소멸
    assert "사주를 펼쳐 놓고 보면" in intro[:30]  # 요약 카드로 시작(nm_pfx 접두 뒤)
    consult = T["consult"]
    # 직답은 consult 장 전담 — 직답 리드가 여기에 있다.
    assert "먼저 핵심부터 말하면" in consult or "결론부터" in consult


def test_intro_frontload_gate_removed_two_way():
    # frontload 게이트 철거 회귀(2026-07-05 운영자 지시 개정). 양방:
    #  (a) intro 초반에 decision/timing 표지가 없어도 missing_frontloaded_answer 미발생
    #      (게이트·산출 필드 소멸 — 직답은 consult 장 전담).
    #  (b) 골격 실빌드 intro 는 전 가드 clean(제거로 인한 회귀 0) + 직답 문단 소멸.
    # (a) 초반 1800자에 결론/시기 표지가 없는 본문 — 구 게이트라면 FAIL 대상
    body = "배경을 천천히 살펴보겠습니다. " * 300
    r = delivery_quality.analyze(
        body,
        pages=27,
        product="integrated",
        premium=True,
        concern="아파트 매매 시기가 궁금합니다",
    )
    assert "missing_frontloaded_answer" not in {f["rule"] for f in r["failures"]}
    assert "frontloaded_answer" not in r  # 산출 필드 소멸
    assert "physical_frontloaded_answer" not in r
    # (b) 골격 intro: 전 가드 clean + 직답 문단 소멸
    saju = _saju()
    T = rules.build_all(
        saju,
        ref_year=2026,
        name="테스트",
        concern_category="재물",
        concern_text="합성 고민 텍스트입니다.",
    )
    assert _guards(T["intro"]) == []
    assert "신청 질문부터 먼저 답하면" not in T["intro"]
