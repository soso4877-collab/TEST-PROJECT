# -*- coding: utf-8 -*-
"""문장 품질 린터 — LLM 산문의 의미 모순·알려진 오타를 보수적으로 검출(H1-mini 2026-06-15).

safe_lint(§12 안전)·style_lint(AI틱)·factcheck(사실)가 못 잡는 '말이 안 되는 문장'을
잡는다: (1) 신강/신약 모순, (2) '재무'를 '재수'로 쓴 오타(돈 맥락), (3) 이름 뒤 재수.
위반 시 builder/gunghap 가드에서 룰 골격 폴백(재작성). 과탐 방지를 위해 known bad 중심 —
'재수가 좋다'(운) 같은 정상 표현은 검출하지 않는다.
"""

from __future__ import annotations

import re

# 1) 의미 모순쌍 — 신강과 신약은 동시 성립 불가
_CONTRADICTIONS = [
    re.compile(r"신강한\s*신약"),
    re.compile(r"신약한\s*신강"),
]
# 2) 재무→재수 오타: '재수'가 돈/재물 맥락에 붙은 경우만(운세의 '재수가 좋다'는 미검출)
_TYPO = [
    re.compile(r"재수(?:는|가|를|의)?\s*(?:돈|재물|재정|자금|흐름)"),
]
_ADJACENT_HANGUL_DUP_RX = re.compile(
    r"(?<![\uac00-\ud7a3])(?P<word>[\uac00-\ud7a3]{2,8})(?:\s+(?P=word))+(?![\uac00-\ud7a3])"
)
_CUSTOMER_FRAMING_RX = [
    re.compile(r"이\s*풀이(?:는|에서는|에서)\b"),
    re.compile(r"이\s*자료(?:는|에서는|에서)\b"),
]
_INTERNAL_META_RX = [
    re.compile(r"고객\s*질문\s*:"),
    re.compile(r"상담\s*대상\s*:"),
    re.compile(r"\[(?:각자\s*명식|두\s*사람\s*관계|자미두수|시기)\]"),
    re.compile(r"근거\s*자료"),
    re.compile(r"이\s*장\s*에서"),
    re.compile(r"두\s*사람\s*사이에서\s*실제로\s*맞물리는\s*부분은\s*다음과\s*같습니다"),
    re.compile(r"십성\s*으로"),
    re.compile(r"같은\s*방향으로\s*모이는\s*협업의\s*결"),
    re.compile(r"명궁은\s*명궁"),
    re.compile(r"신궁은\s*명궁"),
    re.compile(r"자미두수로는\s*사람과\s*관계,\s*돈과\s*생활,\s*일의\s*자리"),
    re.compile(r"시기\s*흐름은\s*다음처럼\s*나누어\s*봅니다"),
]
_PROMO_CTA_RX = [
    re.compile(r"(?:사주도령|서담선생)\s*(?:전문\s*)?(?:상담|궁합\s*상담)"),
    re.compile(r"(?:전문\s*상담|궁합\s*상담)"),
    re.compile(r"더\s*깊은\s*(?:궁합|해석|풀이|시기별\s*흐름).*(?:확인|신청|상담)"),
    re.compile(r"(?:아래\s*)?링크"),
]
_DECORATIVE_EMOJI_RX = re.compile(r"[🔮🌙🪄🌿✦★☆]")


def lint(text: str, names: list[str] | None = None) -> list[dict]:
    """위반 목록(빈 리스트면 통과). names = 사람 이름(이름 뒤 재수 오타 앵커용, 선택)."""
    out: list[dict] = []
    for rx in _CONTRADICTIONS:
        for m in rx.finditer(text):
            out.append({"type": "contradiction", "match": m.group(0), "why": "신강/신약 모순"})
    for rx in _TYPO:
        for m in rx.finditer(text):
            out.append({"type": "typo", "match": m.group(0), "why": "재무→재수 오타 의심(돈 맥락)"})
    for m in _ADJACENT_HANGUL_DUP_RX.finditer(text):
        out.append({"type": "adjacent_duplicate", "match": m.group(0), "why": "인접 단어 반복"})
    for rx in _CUSTOMER_FRAMING_RX:
        for m in rx.finditer(text):
            out.append(
                {
                    "type": "customer_framing",
                    "match": m.group(0),
                    "why": "고객 본문에 자료 설명식 표현 사용",
                }
            )
    for rx in _INTERNAL_META_RX:
        for m in rx.finditer(text):
            out.append(
                {
                    "type": "internal_meta_label",
                    "match": m.group(0),
                    "why": "고객 본문에 내부 근거/작업 라벨 누출",
                }
            )
    for rx in _PROMO_CTA_RX:
        for m in rx.finditer(text):
            out.append(
                {
                    "type": "promo_cta",
                    "match": m.group(0),
                    "why": "고객 본문에 홍보성 상담/링크 문구 사용",
                }
            )
    for m in _DECORATIVE_EMOJI_RX.finditer(text):
        out.append(
            {
                "type": "decorative_emoji",
                "match": m.group(0),
                "why": "고객 본문에 장식 이모지 사용",
            }
        )
    for nm in names or []:
        if not nm:
            continue
        for m in re.finditer(re.escape(nm) + r"\s*,?\s*재수", text):
            out.append(
                {"type": "name_typo", "match": m.group(0), "why": f"{nm} 뒤 재수(재무 오타 의심)"}
            )
    return out


def is_clean(text: str, names: list[str] | None = None) -> bool:
    return not lint(text, names)
