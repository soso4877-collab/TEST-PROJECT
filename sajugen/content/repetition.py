# -*- coding: utf-8 -*-
"""크로스챕터 반복 억제 — 결정론 후처리(2026-06-14 운영자 베타 지적).

배경: compose 가 해석 챕터를 병렬·독립 생성해 일주 자기소개("○○님은 ◇◇일주예요")가
원국 장과 기질 장에 중복됐다. 프롬프트 지시·골격 근원 수정으로도 LLM 비결정성으로 잔존
(연구 합의: 병렬 독립 생성은 크로스챕터 일관성을 보장 못 함). 따라서 조립 후 결정론
후처리로 '소유 챕터' 1곳에만 남긴다.

안전 원칙: 내용 손상 방지를 위해 **짧은 '자기소개 줄'만** 제거한다(한 줄이 곧 도입 문장인
경우). 내용을 담은 긴 문장은 건드리지 않는다(일주를 풀이에 활용한 문장은 보존).
"""

from __future__ import annotations

import re

# 일주 자기소개: "○○님은 ◇◇(간지 2자, 공백 허용) 일주[종결어미]" 형태.
_ILJU_INTRO = re.compile(
    r"[가-힣]{1,6}님은\s*[가-힣]\s?[가-힣]\s*일주"
    r"(입니다|이에요|예요|이고요?|이라(서|고)?|라서|라|네요|군요)?"
)
_INTRO_LINE_MAX = 40  # 이보다 짧고 도입 패턴이면 '자기소개 줄'로 보고 제거


def dedup_ilju_intro(sections, owner_id: str = "wonguk", max_len: int = _INTRO_LINE_MAX) -> int:
    """일주 자기소개 줄을 owner 챕터에만 남기고 다른 챕터에서 제거. 제거 줄 수 반환.

    sections: .id 와 .final_text(가변) 를 가진 Section 리스트.
    """
    removed = 0
    for s in sections:
        if getattr(s, "id", None) == owner_id:
            continue  # 소유 챕터는 보존
        text = getattr(s, "final_text", "") or ""
        out_lines = []
        for line in text.split("\n"):
            core = line.strip()
            if core and len(core) <= max_len and _ILJU_INTRO.search(core):
                removed += 1
                continue  # 짧은 일주 자기소개 줄 → 제거(내용 없는 도입)
            out_lines.append(line)
        new = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()
        if new != text:
            s.final_text = new
    return removed
