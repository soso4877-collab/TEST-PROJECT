# -*- coding: utf-8 -*-
"""관계/재회/궁합 LLM용 안전 context 생성."""

from __future__ import annotations

import re

from sajugen.content import client_tone_lint

from . import delivery_gate


SYSTEM = (
    "너는 오래 상담해 온 사주 상담가다. 두 사람의 명식과 질문 축을 보고, 고객에게 직접 답한다. "
    "명리 판단은 분명하게 말하되 결과를 보장하지 않는다.\n\n"
    "[말투] '~예요/~해요' 중심의 자연스러운 존댓말. '~편이다/~한다/~이다' 보고서체를 피한다.\n"
    "[질문] 상대의 진심, 대화와 갈등, 성격·가치관·연애관, 좋은 영향, 안정성, 앞으로 1년의 판단 기준을 빠뜨리지 않는다.\n"
    "[행동] 고백보다 반복 태도, 약속 이행, 갈등 뒤 회복, 주변 관계에 자연스럽게 놓는지를 구체 기준으로 쓴다.\n"
    "[금지] 홍보 문구, 링크 안내, 장식 이모지, AI/도구 고지, 사주도령 서명 반복 금지. "
    "'당신', '고객님', '이 글은', '이 문서는', '이 리포트는' 같은 호명/문서 자기소개 표현 금지.\n"
    "[결론 표지 금지] '종합하면', '결론적으로', '핵심은 다음과 같습니다' 같은 공식적 결론 표지 금지.\n"
    "[문서 진행/섹션 예고 금지] '이야기가(도) 이어집니다', '다음 장에서는', '다음으로 …을 살펴보겠습니다', "
    "'이어서 …을 보겠습니다', '이 풀이는 다음 순서로', '자미두수 명궁 이야기도 바로 이어집니다' 같은 "
    "섹션 예고·다음 파트 안내·작성자 진행 표현 금지. 각 대목은 다음 파트 예고가 아니라 그 자체로 완결된 풀이여야 한다.\n"
    "[분량] 각 장은 짧은 표어로 끝내지 않고 최소 세 문장 이상으로 판단 기준과 실제 행동을 함께 쓴다.\n"
)

SECTIONS = [
    ("overview", "두 사람의 큰 흐름"),
    ("intent", "상대의 진심과 표현 방식"),
    ("conflict", "대화와 갈등이 생길 때"),
    ("values", "성격과 가치관, 연애관"),
    ("ziwei_relation", "자미두수로 보는 관계의 자리"),
    ("chemistry", "끌림과 맞물림"),
    ("daily", "일상에서 맞는 부분과 다른 부분"),
    ("social", "주변 사람과 관계를 놓는 방식"),
    ("pace", "관계 속도와 확인 방식"),
    ("risk", "주의해야 할 장면"),
    ("stability", "안정적으로 이어갈 수 있는가"),
    ("action", "지금 다가가는 방식"),
    ("timing", "앞으로 1년의 흐름"),
    ("decision", "지금 확인해야 할 기준"),
]

GUIDE = {
    "overview": "두 사람의 큰 결을 먼저 말하고, 지금 질문의 핵심을 정리한다.",
    "intent": "상대의 마음을 말이 아니라 반복 태도와 약속 이행으로 확인하는 기준을 적는다.",
    "conflict": "대화 속도와 갈등 회복 방식의 차이를 설명하고, 부딪힐 때의 실제 대응을 제안한다.",
    "values": "성격, 생활 기준, 가치관, 연애관이 맞는 지점과 조심할 지점을 분명히 나눈다.",
    "ziwei_relation": "자미두수의 관계·돈·일·생활 축을 고객이 이해할 수 있는 말로 연결한다.",
    "chemistry": "끌림이 생기는 이유와 실제로 맞물리는 지점을 명리와 관계 행동으로 설명한다.",
    "daily": "연락, 약속, 생활 리듬, 말투처럼 일상에서 맞거나 어긋날 부분을 쓴다.",
    "social": "학교, 전공, 겹지인, 주변에 관계를 자연스럽게 놓는 방식이 왜 중요한지 쓴다.",
    "pace": "한쪽은 확인이 빠르고 한쪽은 살피는 속도가 느릴 때 어떻게 맞추는지 쓴다.",
    "risk": "관계가 흔들릴 수 있는 장면과 미리 조심할 기준을 쓴다.",
    "stability": "서로에게 좋은 영향이 되는 조건과 안정 관계로 가는 조건을 쓴다.",
    "action": "지금 먼저 보낼 말, 만남을 여는 방식, 부담을 줄이는 접근 순서를 제안한다.",
    "timing": "앞으로 1년을 중심으로 성급히 밀어붙일 때와 확인할 때를 나누어 말한다.",
    "decision": "고백이나 확답보다 먼저 볼 기준, 물러설 기준, 다음 연락 방식을 제시한다.",
}

_FOCUS = {
    "overview": "먼저 두 사람의 전체 궁합과 현재 질문의 핵심을 답합니다.",
    "intent": "상대의 진심은 말보다 약속 이행, 대화 회복, 주변 관계에 자연스럽게 놓는지로 봅니다.",
    "conflict": "갈등은 마음의 크기보다 표현 속도와 회복 방식의 차이로 봅니다.",
    "values": "성격, 가치관, 연애관은 생활 기준과 관계 기준이 맞는지로 풉니다.",
    "ziwei_relation": "자미두수에서는 사람과 관계, 돈, 일, 생활의 자리가 어떻게 관계 안정에 이어지는지 봅니다.",
    "chemistry": "서로 끌리는 지점과 실제로 맞물리는 지점은 따로 봅니다.",
    "daily": "일상에서는 연락, 약속, 생활 리듬, 말의 속도를 봅니다.",
    "social": "겹지인, 학교, 전공처럼 주변에 관계가 놓이는 방식도 안정성을 봅니다.",
    "pace": "관계 속도와 확인 방식이 다르면 마음이 있어도 오해가 생길 수 있습니다.",
    "risk": "주의할 장면은 말이 끊길 때, 약속이 밀릴 때, 갈등 뒤 회복이 늦을 때입니다.",
    "stability": "서로에게 좋은 영향이 되는 조건과 안정적으로 이어갈 조건을 봅니다.",
    "action": "지금 다가가는 방식은 부담을 줄이고 확인할 기준을 세우는 쪽으로 봅니다.",
    "timing": "앞으로 1년 안에서 서두를 때와 확인할 때를 나누어 봅니다.",
    "decision": "지금 다가가는 방식, 확인해야 할 기준, 물러설 기준을 제시합니다.",
}

_AXIS_KEYWORDS = {
    "상대의 진심": ("진심", "마음", "호감", "상대방"),
    "대화와 갈등": ("대화", "갈등", "차이", "생각하는 방식"),
    "성격과 가치관": ("성격", "가치관", "연애관", "생활 기준"),
    "안정성과 좋은 영향": ("안정", "좋은 영향", "이어갈", "관계"),
    "궁합과 끌림": ("궁합", "잘 맞", "끌림", "맞는지"),
    "앞으로 1년의 흐름": ("언제", "시기", "올해", "내년", "1년", "일년"),
    "다가가는 방식": ("어떻게", "방법", "해야", "다가", "확인"),
}
_LABELS = ("첫 번째 분", "두 번째 분", "세 번째 분", "네 번째 분")
_RAW_REPLACEMENTS = (
    ("사주팔자", "타고난 전체 흐름"),
    ("일주", "중심 자리"),
    ("일간", "중심 기운"),
    ("십성으로", "관계 역할로"),
    ("일지 삼합 반합", "생활 자리에서 같은 방향으로 모이는 결"),
    ("일지", "생활 자리"),
    ("천간합", "서로 묶이는 결"),
    ("오행", "다섯 기운"),
    ("신강약", "힘의 균형"),
    ("용신", "보완 방향"),
    ("세운", "해마다의 흐름"),
    ("식신생재", "만들고 표현한 것이 재물로 이어지는"),
    ("재고", "모으고 쌓는 창고의 결"),
)
_BRACKET_RX = re.compile(r"\[[^\]]+\]")


def build_context(
    section_id: str,
    people: list[dict],
    persons_txt: str,
    pairs_txt: str,
    timing_txt: str,
    situation: str,
) -> str:
    unknown_note = (
        "출생시각은 미상인 사람이 있어 세부 기질은 단정하지 않고 큰 성향과 관계 흐름 위주로 봅니다."
        if any(p.get("unknown_time") for p in people)
        else "두 사람의 출생시각을 기준으로 큰 흐름과 세부 기질을 함께 봅니다."
    )
    axes = _question_axes(situation)
    body = (
        f"{_FOCUS.get(section_id, '')}\n\n"
        f"질문 축: {', '.join(axes)}.\n\n"
        f"{unknown_note}\n\n"
        "두 사람의 타고난 결, 서로 맞물리는 방식, 가까운 시기 판단을 아래처럼 요약합니다.\n"
        f"{persons_txt}\n\n{pairs_txt}\n\n{_ziwei_context(people)}\n\n{timing_txt}"
    )
    body = _sanitize_for_prompt(body, people)
    delivery_gate.assert_clean(prompt_text=body, names=[p["name"] for p in people])
    return body


def layout_variants(llm_active: bool) -> list[tuple[str, str]]:
    if not llm_active:
        return [("14.5pt", "1.8")]
    return [
        ("13.8pt", "1.68"),
        ("13.6pt", "1.64"),
        ("13.4pt", "1.60"),
        ("13.2pt", "1.56"),
        ("13.0pt", "1.52"),
        ("12.8pt", "1.48"),
    ]


def only_low_density_failure(v: dict) -> bool:
    dq = v.get("delivery_quality") or {}
    failures = dq.get("failures") or []
    if not failures or any(f.get("rule") != "premium_low_density_pages" for f in failures):
        return False
    return all(
        bool(v.get(k, True))
        for k in (
            "text_layer_ok",
            "fonts_embedded",
            "tagged",
            "markdown_clean",
            "daewoon_consistent",
            "quality_clean",
            "temporal_clean",
            "loanword_clean",
            "raw_calc_head_clean",
            "name_policy_clean",
            "identity_role_clean",
            "singang_role_clean",
        )
    )


def _question_axes(situation: str) -> list[str]:
    text = situation or ""
    axes = [label for label, terms in _AXIS_KEYWORDS.items() if any(t in text for t in terms)]
    return axes or ["전체 궁합", "관계 안정성", "다가가는 방식"]


def _sanitize_for_prompt(text: str, people: list[dict]) -> str:
    text = _BRACKET_RX.sub("", text)
    replacements: dict[str, str] = {}
    for idx, person in enumerate(people):
        label = _LABELS[idx] if idx < len(_LABELS) else f"{idx + 1}번째 분"
        name = person.get("name", "")
        if not name:
            continue
        replacements[name] = label
        replacements[client_tone_lint.given_name(name)] = label
        replacements[client_tone_lint.honor(name)] = label
        replacements[client_tone_lint.intro(name)] = label
    for old in sorted(replacements, key=len, reverse=True):
        text = text.replace(old, replacements[old])
    for old, new in _RAW_REPLACEMENTS:
        text = text.replace(old, new)
    text = text.replace("같은 방향으로 모이는 협업의 결", "같은 방향으로 모이는 관계의 결")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _ziwei_context(people: list[dict]) -> str:
    lines = [
        "자미두수 관점은 두 사람이 밖에서 관계를 드러내는 방식, 돈과 생활을 다루는 방식, 일과 역할의 부담을 함께 봅니다."
    ]
    for idx, person in enumerate(people):
        label = _LABELS[idx] if idx < len(_LABELS) else f"{idx + 1}번째 분"
        lines.append(
            f"{label}은 가까운 관계에서 말보다 태도와 생활의 반복이 중요하고, "
            "돈과 역할을 다루는 방식도 관계 안정감에 영향을 줍니다."
        )
    return "\n".join(lines)
