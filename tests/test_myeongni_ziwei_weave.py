# -*- coding: utf-8 -*-
"""P4(2026-07-05) 명리-자미 통합(B안) — v7 실격 후속(운영자: 두 체계 병렬 나열 단절).

고정하는 것: (a) _palace_para myeongni_hint 통합 꼬리 + hint 미전달 결정론 보존,
(b) '명리는 흐름/자미는 구조' 역할분담 정형 소거(9장 개관 외), (c) 10장 교차 요약이
방법론 일반론이 아니라 이 사람의 실사실(십성·궁·별)을 참조, (d) 시진 불명이면 궁
실명 미노출(절대규칙 8), (e) 통합 문장 factcheck 0(실재 별·궁만). PII 0(합성 입력).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import factcheck, rules  # noqa: E402


def _saju():
    return engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")


def _T(**kw):
    return rules.build_all(_saju(), ref_year=2026, name="테스트", **kw)


def test_palace_para_hint_adds_weave_and_keeps_determinism():
    saju = _saju()
    p = rules._palace(saju.ziwei, "부처궁")
    plain1 = rules._palace_para(p, "가까운 관계")
    plain2 = rules._palace_para(p, "가까운 관계")
    assert plain1 == plain2  # 결정론
    hinted = rules._palace_para(p, "가까운 관계", myeongni_hint="일주에서 본 정관의 결")
    assert hinted != plain1
    assert "일주에서 본 정관의 결" in hinted  # 명리 참조 통합 꼬리
    # hint 미전달 출력은 기존 seed 그대로(스냅샷 동치 — 통합 꼬리 문구 미포함)
    assert "겹쳐 읽으면" not in plain1 or "같은 자리를 가리키고" not in plain1


def test_role_split_formula_removed_outside_ziwei_overview():
    # '명리는 시간의 흐름/자미두수는 인생의 구조' 정형은 전 챕터에서 소거(9장 개관 허용도
    # 현행 골격에는 없음 — 재유입 시 이 앵커가 잡는다).
    T = _T(concern_category="재물", concern_text="돈 흐름이 궁금합니다.")
    joined = "\n".join(T.values())
    assert "명리는 시간의 '흐름'을" not in joined
    assert "인생의 '구조'를 보는 역할" not in joined
    assert "명리는 시기의 흐름을 보고" not in joined


def test_cross_weaves_actual_facts_not_methodology():
    # 10장(cross)이 이 사람의 실사실(부처궁·관록궁·재백궁 + 별)을 참조한다.
    saju = _saju()
    T = rules.build_all(saju, ref_year=2026, name="테스트")
    cross = T["together"]
    assert "부처궁" in cross and "관록궁" in cross and "재백궁" in cross
    assert "겹쳐 읽었습니다" in cross
    # 층위 원칙(상충 = 틀림 아님) 유지
    assert "틀린 것이 아니라" in cross
    # factcheck: 언급된 별·궁은 전부 이 명반 실재 토큰(환각 0)
    assert factcheck.check(cross, saju, frozenset()) == []


def test_cross_omits_palace_names_when_unknown_time():
    # 절대규칙 8: 시진 불명 = 자미 궁 실명 미노출(층위 원칙 문단만).
    T = _T(unknown_time=True)
    cross = T["together"]
    assert "부처궁" not in cross and "재백궁" not in cross
    assert "안정적이라는 근거" in cross
    assert "참고" not in cross


def test_key_palace_paragraphs_reference_myeongni_anchor():
    # 9장 핵심 궁 문단이 명리 앵커(일간/월간 십성 등)를 참조한다(사일로 해소).
    saju = _saju()
    T = rules.build_all(saju, ref_year=2026, name="테스트")
    zp = T["ziwei"]
    dm_ko = rules._GAN_KO.get(saju.myeongni.day_master, "")
    assert f"일간 {dm_ko}의 중심축" in zp  # 명궁 힌트
    assert "월간" in zp  # 관록궁 힌트
    # 통합 꼬리 문형이 실제로 실렸는지(자립 카드 3부 정형만으로 끝나지 않음)
    assert ("겹쳐 읽으면" in zp) or ("안과 밖에서 본 것" in zp) or ("하나로 모입니다" in zp)
