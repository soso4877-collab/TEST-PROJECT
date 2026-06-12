# -*- coding: utf-8 -*-
"""style_lint(2026-06-12 신설) — AI틱 표현 차단/허용 회귀.

운영자 보고 실사례 앵커: 규칙 누설("한자 표기를 쓰지 않겠습니다"),
시적 비유("시간의 결을 따라 걷고"), em dash 52회·가운뎃점 49회 난발.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import style_lint  # noqa: E402

BLOCKED = [
    # 규칙 누설(운영자 보고 원문 패턴)
    "임수는, 아 참고로 한자 표기를 쓰지 않겠습니다.",
    "이제부터 호칭은 태수님으로 부르겠습니다.",
    "기호는 생략하기로 합니다.",
    # 시적 비유(운영자 보고 원문)
    "시간의 결을 따라 걷고 있는 셈이에요.",
    "인생이라는 항해에서 태수님은 지금 큰 바다에 있어요.",
    "삶의 여정에 작은 등불이 되기를 바랍니다.",
    # AI 시그니처 기호
    "겉으로 드러나는 색은 편인 — 독창적인 사고와 통찰이에요.",
    "수면·식사·운동을 같이 챙기세요.",
    "① 먼저 휴식부터 챙기세요.",
]

ALLOWED = [
    "태수님은 임인일주예요.",
    "임수는 작은 물이 아니라 큰 물이에요.",  # 일간 오행 자연물 비유는 허용
    "2026년은 병오년입니다.",
    "겉으로 드러나는 색은 편인, 독창적인 사고와 통찰이에요.",
    "괴강살, 백호대살, 양인살까지 함께 있어서 분위기가 가볍지 않습니다.",
    "몸의 신호가 이어지면 병원에서 확인해 보세요.",
]


def test_blocked():
    for s in BLOCKED:
        assert style_lint.lint(s), f"차단되어야 함: {s}"


def test_allowed():
    for s in ALLOWED:
        v = style_lint.lint(s)
        assert not v, f"허용되어야 함: {s} -> {v}"


def test_repeat_cap():
    ok = "기운이라는 말을 적당히 쓰면 괜찮아요. " * 3
    assert not style_lint.lint(ok)
    spam = "이 기운은 좋은 기운이고 저 기운은 강한 기운이라 " * 4  # 16회
    assert any("반복 남발" in v["why"] for v in style_lint.lint(spam))
