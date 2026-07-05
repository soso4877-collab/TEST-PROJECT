# -*- coding: utf-8 -*-
"""P5(2026-07-05) 날것 계산어·연성 외래어 소멸 — v7 실격 후속(운영자: "분포"·"(대운수6)").

커밋 순서 규율(골격 스윕 → lint 등재)의 결과를 양방으로 고정한다:
(a) 신규 lint(대운수·오행국·bare 분포·리듬)가 결함 문안을 차단,
(b) 전 골격(개인·궁합 폴백·integrated depth)이 신규 lint 를 통과(동기화 앵커),
(c) 필러 정규식 카운터('결' 단독·'의 색')가 부분문자열 오탐 없이 계수. PII 0.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import client_tone_lint as ct  # noqa: E402
from sajugen.content import delivery_quality as dq  # noqa: E402
from sajugen.content import rules  # noqa: E402


def test_new_raw_calc_heads_flag_defects():
    # 차단 측: v7 실사고 표현 그대로.
    assert ct.raw_calc_lint("대운 순행(대운수 6)입니다.")
    assert ct.raw_calc_lint("오행국은 화육국입니다.")
    assert ct.raw_calc_lint("금 기운은 옅은 분포라 채워 가면 좋습니다.")
    assert ct.loanword_lint("시간의 리듬을 타면 좋습니다.")


def test_new_raw_calc_heads_pass_normal_prose():
    # 통과 측: 합성어·정상 서술 오탐 0.
    assert ct.raw_calc_lint("큰 운의 방향은 6세부터 10년 단위로 바뀝니다.") == []
    assert ct.raw_calc_lint("명반의 바탕은 해석의 토대입니다.") == []
    assert ct.raw_calc_lint("역할을 재분포하는 이야기") == []  # 합성어(앞 한글) 미매칭
    assert ct.loanword_lint("호흡과 박자를 맞추면 됩니다.") == []


def test_all_personal_skeleton_sections_pass_new_lints():
    # 골격-게이트 동기화 앵커: 스윕(P5-1) 후 전 섹션이 신규 lint 0(부록 제외 — 허용구역).
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    T = rules.build_all(
        saju, ref_year=2026, name="테스트", concern_category="재물", concern_text="합성 고민."
    )
    for sid, text in T.items():
        if sid in ("appendix_terms", "cover", "toc"):
            continue
        assert ct.loanword_lint(text) == [], (sid, "loanword")
        heads = ct.raw_calc_headwords(text)
        assert heads == [], (sid, heads)


def test_gunghap_and_integrated_skeletons_pass_loanword():
    # 이웃 소스(궁합 폴백 가이드·integrated depth 골격)도 '리듬' 스윕 완료 앵커.
    from sajugen import gunghap as g
    from sajugen import integrated as itg
    from sajugen.relationship import context as rc
    from sajugen.relationship import fallback as rf

    blobs = []
    blobs += [v for v in rc.GUIDE.values()] if hasattr(rc, "GUIDE") else []
    blobs += [str(getattr(itg, n, "")) for n in dir(itg) if n.startswith("_DEPTH")]
    import inspect

    blobs.append(inspect.getsource(rf))
    blobs.append(inspect.getsource(rc))
    joined = "\n".join(str(b) for b in blobs)
    assert "리듬" not in joined


def test_filler_regex_counter_no_substring_false_positive():
    # '결' 단독 카운터: 결혼·결론·결정은 세지 않는다(부분문자열 오탐 차단).
    text = "결혼과 결론과 결정을 이야기합니다. " * 30
    hits = dq._repetition_hits(text)
    assert not [h for h in hits if h["term"] == "결(단독)"]
    # 단독 '결'+조사 남발은 계수 — cap 12 초과 시 warning 항목으로 잡힘.
    filler = "이 결이 좋고, 그 결은 곱고, 저 결도 맑습니다. " * 10
    hits2 = dq._repetition_hits(filler)
    assert [h for h in hits2 if h["term"] == "결(단독)"]
    # '의 색' 은유 계수
    color = "마음의 색이 곱고, 기운의 색이 맑고, 영역의 색이 짙고, 삶의 색이 깊고, 말의 색이 밝다."
    hits3 = dq._repetition_hits(color)
    assert [h for h in hits3 if h["term"] == "의 색"]


def test_keywords_line_has_no_raw_daewoon_label():
    # v7 실사고 지점(1장 keywords ④·⑤): 표제 소멸 + 나이·바탕 자연문 유지.
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    T = rules.build_all(saju, ref_year=2026, name="테스트")
    intro = T["intro"]
    assert "대운수" not in intro and "오행국" not in intro and "분포" not in intro
    assert "세부터 10년 단위" in intro  # 계산 사실(대운수)은 자연문으로 보존
    assert "명반의 바탕" in intro
