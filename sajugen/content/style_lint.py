# -*- coding: utf-8 -*-
"""스타일 린터 — AI틱 표현 검증(2026-06-12 신설, 운영자 보고 기반).

배경: 가드 3단(safe_lint/factcheck/trace)은 사실·안전만 검사하고 스타일은
프롬프트 지시뿐 검증이 없었다 → 규칙 누설("한자 표기를 쓰지 않겠습니다"),
시적 비유("시간의 결을 따라 걷고"), em dash 52회·가운뎃점 49회 난발이 통과.
이 린터는 LLM compose 후보에만 적용(룰 골격은 우리가 직접 통제) — builder의
재작성→폴백 루프에 4번째 검사로 들어간다(가드 추가, 완화 아님).
"""

from __future__ import annotations

import re

# (패턴, 사유) — 발견 즉시 위반(재작성 유도)
RULES: list[tuple[str, str]] = [
    # 규칙 누설(메타 발화): 작성 지시를 본문에서 입 밖에 내는 것
    (
        r"(한자|표기|호칭|기호|규칙|존칭)[^.\n!?]{0,24}(않겠습|않을게|쓰지 않|생략하|부르겠|부르기로|하기로 하|지키겠)",
        "규칙 누설(메타 발화)",
    ),
    (r"(라고|이라고|로|으로)\s*부르(겠|기로)", "호칭 선언(메타 발화)"),
    # AI 시그니처 기호
    (r"—|–", "em dash(AI 시그니처)"),
    (r"·", "가운뎃점 난발"),
    (r"[①-⑳]|[➀-➉]|→|⇒|▶|■|◆|●|★|☆", "기호 난발"),
    # 과한 시적 비유(운영자 지적: '시간의 결을 따라 걷고' 류)
    (
        r"결을 따라 걷|길을 걷는 중|물길|항해|여정|등불|수놓|춤추|노래하|날개를 펴|꽃피|"
        r"발걸음을 내딛|새로운 장을 열|페이지를 넘기|캔버스|교향곡|악장",
        "과한 비유(시적 수사)",
    ),
    # 시기·나이 가정어: 명식은 결정론(세운 연도·간지가 정해짐) → 추정형으로 흐리지 않는다.
    # '약 N세'·'N세/년 전후'·'전후라면'·'쯤'·'안팎'·'즈음'만 차단('약 10년 대운' 같은 정당 근사는 통과).
    (
        r"약\s*\d+\s*(세|살)|\d+\s*(세|살|년)\s*전후|전후라면|쯤|안팎|즈음",
        "시기·나이 가정어(확정 명식인데 추정형)",
    ),
]
_COMPILED = [(re.compile(p), why) for p, why in RULES]

# 반복 남발 상한(챕터 단위) — 같은 단어를 버릇처럼 반복 = AI 신호.
# 기준 2,500자 챕터의 상한이며 글 길이에 비례 보정(가족 다인 consult 같은 긴
# 챕터는 자연 언급량이 많음 — 절대 상한이면 정상 밀도도 폴백, 실측 2026-06-12).
_REPEAT_CAPS = {"기운": 12, "의 결": 8, "흐름": 10, "구조": 12}
_REPEAT_BASE_LEN = 2500


def lint(text: str) -> list[dict]:
    """위반 목록. 빈 리스트면 통과."""
    out: list[dict] = []
    for rx, why in _COMPILED:
        m = rx.search(text)
        if m:
            out.append({"match": m.group(0), "why": why, "pos": m.start()})
    scale = max(1.0, len(text) / _REPEAT_BASE_LEN)
    for word, cap in _REPEAT_CAPS.items():
        n = text.count(word)
        eff = int(cap * scale)
        if n > eff:
            out.append({"match": word, "why": f"반복 남발({n}회 > {eff})", "pos": -1})
    return out


def is_clean(text: str) -> bool:
    return not lint(text)
