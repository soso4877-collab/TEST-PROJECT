# -*- coding: utf-8 -*-
"""서양 점성술 off-domain 하드 가드.

이 상품의 계산·해석 권위는 명리와 자미두수에 한정된다. 황도 12궁이나
별자리 해석은 근거 슬롯 밖 사실이므로, 결과 보장 여부와 무관하게 고객 문안에서
결정론적으로 차단한다.

오탐을 막기 위해 ``자리``·``별``·``사자`` 같은 단독어는 잡지 않는다. 황도 12궁
이름은 ``사자자리``처럼 붙여 쓴 컴파운드만 차단하며, ``관록궁 자리``와 자미의
``주성``·``별``은 정상 표현으로 남긴다.
"""

from __future__ import annotations

import re
from collections import Counter

# 황도 12궁의 한국어 이름. 사수자리는 궁수자리라는 별칭도 함께 차단하므로
# 12개 별자리 의미에 대응하는 표기는 13개다.
WESTERN_ZODIAC_SIGN_NAMES = (
    "양자리",
    "황소자리",
    "쌍둥이자리",
    "게자리",
    "사자자리",
    "처녀자리",
    "천칭자리",
    "전갈자리",
    "사수자리",
    "궁수자리",
    "염소자리",
    "물병자리",
    "물고기자리",
)

# ``점성술``보다 ``점성``을 먼저 매치하면 같은 표현을 짧게 잘라 보고하므로,
# 긴 토큰 우선 정렬한 단일 정규식으로 전체 고정 토큰을 검사한다.
WESTERN_ASTROLOGY_TERMS = ("별자리", "황도", "점성술", "점성")
_BLOCKED_TOKENS = tuple(
    sorted(
        {*WESTERN_ZODIAC_SIGN_NAMES, *WESTERN_ASTROLOGY_TERMS},
        key=lambda token: (-len(token), token),
    )
)
_BLOCKED_RX = re.compile("|".join(re.escape(token) for token in _BLOCKED_TOKENS))


def lint(text: str) -> list[dict]:
    """고정 토큰별 PII-free 위반 집계를 반환한다. 빈 목록이면 통과다."""

    counts = Counter(match.group(0) for match in _BLOCKED_RX.finditer(text))
    return [
        {
            "type": "off_domain",
            "rule": "western_astrology",
            "token": token,
            "count": count,
            "severity": "hard",
        }
        for token, count in sorted(counts.items())
    ]


def is_clean(text: str) -> bool:
    """서양 점성술 고정 토큰이 하나도 없으면 True다."""

    return not lint(text)
