# -*- coding: utf-8 -*-
"""P1(2026-07-05) 직답 골격 재작성 — v7 실격 후속(운영자: 직답 맥빠짐·유보 프레임).

골격 consult/concern_snapshot 이 [방향 단정]→[근거 겹침(궁 실명)]→[시기]→[첫 행동]
구조로, 전 가드(안전·메타·보장·날것 계산어·외래어)를 통과하면서 충분한 밀도를
가짐을 카테고리 전수 실빌드로 고정한다. PII 0(합성 입력만).
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


def test_snapshot_is_decisive_not_hedging():
    # 스냅샷(인트로 직답 리드)이 유보 프레임 대신 성향 근거+시기+첫 행동을 담는다.
    saju = _saju()
    T = rules.build_all(
        saju, ref_year=2026, name="테스트", concern_category="재물", concern_text="돈 고민입니다."
    )
    intro = T["intro"]
    assert "신청 질문부터 먼저 답하면" in intro  # frontload 가드 앵커 유지
    assert "늦지 않습니다" not in intro  # 구 유보 꼬리 부재
    assert "첫걸음" in intro or "지켜보십시오" in intro  # 행동 지시 존재
