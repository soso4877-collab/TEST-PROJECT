# -*- coding: utf-8 -*-
"""T4.4/G-8: 윤달 15일 분할법 산입 기준 고지 자동 삽입(절대규칙 5).

자미두수 윤달 = 15일 분할법(1~15일 본월, 16일~ 익월). 자미가 표시되는 리포트
(integrated/ziwei)에서 is_leap 일 때만 고지되고, 명리 단독(자미 미표시)·비윤달엔 없다.
E2E 실측(감사 전 현 경로에 고지 부재 확인 후 신설): e2e_p8_leap 렌더에 '15일 분할' 없었음.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder  # noqa: E402

_DISC = "15일 분할법"


def _build(product: str, is_leap: bool):
    saju = engine.build(2012, 4, 21, 10, 0, is_male=True, horoscope_date="2026-06-01")
    rep = builder.build_report(
        saju, use_llm=False, ref_year=2026, name="홍길동", product=product, is_leap=is_leap
    )
    return " ".join(s.final_text or "" for s in rep.sections), rep.guard.clean


def test_leap_disclosure_present_integrated():
    txt, clean = _build("integrated", True)
    assert _DISC in txt
    assert clean is True  # 고지 문안은 3단 가드 통과(간지·연도·결과 토큰 없음)


def test_leap_disclosure_absent_when_not_leap():
    txt, _ = _build("integrated", False)
    assert _DISC not in txt  # 비윤달엔 고지 없음(오삽입 0)


def test_leap_disclosure_absent_for_myeongni():
    # 명리 단독은 자미 미표시 → 15일 분할(자미 개념) 고지 없음(관련 리포트에만).
    txt, _ = _build("myeongni", True)
    assert _DISC not in txt


def test_leap_disclosure_present_ziwei():
    txt, clean = _build("ziwei", True)
    assert _DISC in txt
    assert clean is True
