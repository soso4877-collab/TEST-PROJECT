# -*- coding: utf-8 -*-
"""교차챕터 대운 일관성 — '현재 대운'이 리포트 전체에서 단 하나로 일치하는지 검사.

배경(실사고 2026-06-14): 같은 PDF에서 8장은 '정미 대운(현재)', 11장은 '병오 대운 초입'
으로 서술돼 모순. 병오는 그의 36~45 대운(미래)이자 2026 세운이라 factcheck(토큰 멤버십)는
못 막는다. 골격이 '현재 대운=정미'를 단일 사실로 못박지 않아 챕터마다 '현재'를 제각기
추론한 것이 원인. 이 모듈은 본문에서 '현재로 서술된 대운 간지'를 추출해, 결정론 현재
대운과 불일치하거나 2종 이상 섞이면 위반으로 보고한다(단정 표현이 아닌 일관성 검사).
"""

from __future__ import annotations

import re

# 한글 간지(천간+지지)
_GZ = r"[갑을병정무기경신임계][자축인묘진사오미신유술해]"
# A: '현재/지금/올해/이번/막/초입/진입 … {간지} 대운' (현재 맥락이 간지 앞에)
_CUR_BEFORE = re.compile(rf"(?:현재|지금|올해|이번|막|초입|진입)[^.。!?\n]{{0,14}}?({_GZ})\s*대운")
# B: '{간지} 대운 초입/진입/에 들어/시작/들어서/막' (현재 진입 맥락이 간지 뒤에)
_CUR_AFTER = re.compile(rf"({_GZ})\s*대운\s*(?:초입|진입|에\s*들어|에\s*진입|시작|들어서|막)")


def current_framed(text: str) -> set[str]:
    """본문에서 '현재 대운'으로 서술된 간지(한글) 집합. 비어 있으면 현재 대운 단정 없음."""
    found: set[str] = set()
    for rx in (_CUR_BEFORE, _CUR_AFTER):
        for m in rx.finditer(text):
            found.add(m.group(1))
    return found


def check(sections, expected_ko: str | None = None) -> tuple[bool, list[dict]]:
    """섹션들의 '현재 대운' 서술이 일관되는지. (ok, 위반목록).

    expected_ko: 결정론 현재 대운 간지(한글). 주어지면 이와 다른 간지를 '현재'로 쓴
    섹션을 위반으로 표시한다. 또한 전체에서 '현재'로 쓰인 간지가 2종 이상이면 위반.
    """
    bad: list[dict] = []
    all_current: set[str] = set()
    for sec in sections:
        framed = current_framed(getattr(sec, "final_text", "") or "")
        all_current |= framed
        if expected_ko:
            for g in sorted(framed):
                if g != expected_ko:
                    bad.append(
                        {
                            "id": getattr(sec, "id", "?"),
                            "ganzhi": g,
                            "expected": expected_ko,
                            "why": "결정론 현재 대운과 다른 간지를 '현재 대운'으로 서술",
                        }
                    )
    if len(all_current) > 1:
        bad.append(
            {
                "id": "(전체)",
                "ganzhi": sorted(all_current),
                "why": "현재 대운으로 서술된 간지가 2종 이상(교차챕터 모순)",
            }
        )
    return (not bad), bad


def offending_ids(sections, expected_ko: str | None) -> set[str]:
    """현재 대운을 잘못(또는 모순되게) 서술한 섹션 id 집합 — 골격 폴백 대상."""
    if not expected_ko:
        return set()
    ids: set[str] = set()
    for sec in sections:
        framed = current_framed(getattr(sec, "final_text", "") or "")
        if any(g != expected_ko for g in framed):
            ids.add(getattr(sec, "id", "?"))
    return ids
