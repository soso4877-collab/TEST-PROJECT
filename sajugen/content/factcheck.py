# -*- coding: utf-8 -*-
"""사실일치 린터 — 생성 텍스트의 명리·자미 사실 토큰이 계산 객체에 존재하는지 대조.

원리(메모리 feedback-verify-no-overclaim): 사실은 엔진만 산출. 텍스트에 등장한
干支·자미 별/궁이 이 사주의 계산 집합에 없으면 = 할루시네이션 → 차단.
보수적으로 '특정 사실 토큰'만 검사(일반 한국어 산문은 오탐 없음).
"""

from __future__ import annotations

import re

_GAN = set("甲乙丙丁戊己庚辛壬癸")
_ZHI = set("子丑寅卯辰巳午未申酉戌亥")
_GANZHI_RX = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")

# 자미두수 14주성(한글) — 텍스트에 별 언급 시 차트 보유 별과 대조
_ZIWEI_MAJORS = {
    "자미",
    "천기",
    "태양",
    "무곡",
    "천동",
    "염정",
    "천부",
    "태음",
    "탐랑",
    "거문",
    "천상",
    "천량",
    "칠살",
    "파군",
}


def allowed_tokens(saju) -> dict:
    """SajuResult → 허용 사실 토큰 집합."""
    m = saju.myeongni
    gz = {m.year.ganzhi, m.month.ganzhi, m.day.ganzhi, m.hour.ganzhi}
    gz |= {d.ganzhi for d in m.daewoon}
    # 세운·월운 간지(lunar-python 산출 실재값) — 본문 언급 시 허용
    gz |= {g for _, g in getattr(m, "seun", [])}
    gz |= {g for _, g in getattr(m, "worun", [])}
    star_ko = set()
    for p in saju.ziwei.palaces:
        for s in (*p.major_stars, *p.minor_stars, *p.adjective_stars):
            star_ko.add(s.name)
    return {
        "ganzhi": gz,
        "ziwei_majors_in_chart": {s for s in star_ko if s in _ZIWEI_MAJORS},
        "all_star_ko": star_ko,
    }


def check(text: str, saju) -> list[dict]:
    """위반 목록. 빈 리스트면 통과."""
    allow = allowed_tokens(saju)
    out: list[dict] = []

    # 1) 干支 토큰: 텍스트의 모든 간지쌍이 이 사주 허용 집합에 있어야 함
    for m in _GANZHI_RX.finditer(text):
        tok = m.group(0)
        if tok not in allow["ganzhi"]:
            out.append(
                {
                    "type": "ganzhi",
                    "token": tok,
                    "why": "이 사주의 사주팔자/대운에 없는 간지",
                    "pos": m.start(),
                }
            )

    # 2) 자미 14주성: 텍스트에 언급된 주성은 이 명반에 실재해야 함
    chart_majors = allow["ziwei_majors_in_chart"]
    for star in _ZIWEI_MAJORS:
        if star in text and star not in chart_majors:
            out.append(
                {"type": "ziwei_star", "token": star, "why": "이 명반에 없는 자미 주성 언급"}
            )
    return out


def is_consistent(text: str, saju) -> bool:
    return not check(text, saju)
