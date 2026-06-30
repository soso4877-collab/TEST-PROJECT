# -*- coding: utf-8 -*-
"""LLM 출력 공통 후처리 — 마크다운/메타 누출 제거 + 한자 제거·기호 산문화.

개인 리포트(builder.py)와 다인 궁합(gunghap.py)이 **같은 함수**를 호출하도록
단일 소스로 분리한다(복붙 시 경로별 드리프트 방지 — 궁합 PDF '---'·'**' 누출
실사고 2026-06-14 재발 차단). builder._strip_artifacts/_hanja_clean 의 로직을
그대로 이전(동작 보존)했다.
"""

from __future__ import annotations

import re

_HR_RX = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,}|={3,})\s*$")  # 마크다운 수평선('---' 누출)
_LIST_MARK_RX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")  # 줄머리 불릿/번호 마커
_GENERIC_ADDRESS_RX = re.compile(r"(고객님|당신)(은|는|이|가|을|를|의|에게|께|도|만)?")
_DOC_SELF_SUBJECT_RX = re.compile(r"이\s*(?:글|문서|리포트)\s*(?:은|는)\s*")
_DOC_META_RX = re.compile(
    r"고객용\s*문서(?:로서|에서는|에서|은|는)?\s*|"
    r"수신자(?:에게|께|는|은|의)?\s*|"
    r"한\s*분께\s*드리는\s*"
)
_FORMULAIC_CONCLUSION_LINE_RX = re.compile(
    # 문두 라벨 + 선택 조사(은/는) + 선택 쉼표까지 함께 제거(선행 조사 잔존 차단).
    r"(?m)^[ \t]*(?:종합하면|결론적으로)(?:은|는)?\s*[,，]?\s*"
)
_FORMULAIC_CORE_RX = re.compile(
    # '핵심은 다음과 같습니다' + 뒤 문장부호(.,:,：,。,!,?,！,？) 함께 제거(부호 잔존 차단).
    r"핵심은\s*다음과\s*같습니다\s*[.。:：!?！？]*\s*"
)


def strip_artifacts(text: str) -> str:
    """LLM 출력의 메타 누출 제거 — 섹션 표시·마크다운(제목/굵게/수평선/리스트/
    인용) 등 AI틱 표식을 걷어낸다. '---' 본문 인쇄 실사고(2026-06-12) 재발 방지."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("[섹션:") or s.startswith("[섹션 "):
            continue
        if s.startswith("#"):  # 마크다운 제목(# 일과 직업…) 누출 제거
            continue
        if _HR_RX.match(ln):  # 수평선 구분선 라인 통째 드롭
            continue
        ln = _LIST_MARK_RX.sub("", ln)  # 줄머리 리스트 마커만 제거(내용 보존)
        ln = ln.replace("**", "").replace("##", "").replace("`", "")  # 굵게/코드 잔재
        if ln.lstrip().startswith("> "):  # 인용 머리
            ln = ln.lstrip()[2:]
        out.append(ln)
    return "\n".join(out).strip()


def _default_honorific() -> str:
    try:
        from . import rules

        return rules.call_name(None) or "그대"
    except Exception:
        return "그대"


def replace_generic_address(text: str, honorific: str | None = None) -> str:
    """Replace generic customer addresses while preserving attached Korean particles."""

    honorific = (honorific or "").strip() or _default_honorific()

    def repl(match: re.Match) -> str:
        particle = match.group(2) or ""
        return f"{honorific}{particle}"

    return _GENERIC_ADDRESS_RX.sub(repl, text or "")


def strip_document_self_reference(text: str) -> str:
    """Remove document-meta subjects without dropping the customer-facing sentence body."""

    text = _DOC_SELF_SUBJECT_RX.sub("", text or "")
    text = _DOC_META_RX.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s*,\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_formulaic_conclusion(text: str) -> str:
    """Remove formulaic conclusion lead-ins while preserving the sentence body."""

    text = _FORMULAIC_CONCLUSION_LINE_RX.sub("", text or "")
    text = _FORMULAIC_CORE_RX.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s*[,，.:：]\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# CJK 한자(확장A U+3400-4DBF·통합 U+4E00-9FFF·호환 U+F900-FAFF) — 본문은 한글 전용이라
# 표시 직전 제거. 범위를 \u 코드포인트로 명시 = 한글(U+AC00-D7A3) 비포함 보장
# (리터럴 한자 입력이 U+8C48 등으로 오기되어 한글까지 삭제된 회귀 2026-06-14 차단).
# factcheck(환각 간지 차단)는 이 제거 이전에 수행되므로 그라운딩은 유지된다.
_CJK_RX = re.compile("[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")

_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"  # ①~⑩

_ADJACENT_HANGUL_DUP_RX = re.compile(
    r"(?<![\uac00-\ud7a3])(?P<word>[\uac00-\ud7a3]{2,8})(?:\s+(?P=word))+(?![\uac00-\ud7a3])"
)


def collapse_adjacent_duplicates(text: str) -> str:
    """Collapse accidental adjacent Korean word duplication, e.g. '반복되는 반복되는'."""
    return _ADJACENT_HANGUL_DUP_RX.sub(lambda m: m.group("word"), text)


def hanja_clean(text: str) -> str:
    # 한자 제거 + 기호 산문화. '수면·식사'(무간격) 보존, 불릿용 ' · '(양옆 공백)만 환원.
    t = _CJK_RX.sub("", text)
    t = t.replace("[원국]", "").replace("[기운 분포]", "")
    t = t.replace("[자미 구조]", "").replace("[읽는 방향]", "")
    t = re.sub(rf"^\s*[{_CIRCLED}]\s*", "", t, flags=re.M)  # 줄머리 원문자
    t = re.sub(r"^\s*·\s*", "", t, flags=re.M)  # 줄머리 불릿
    # '첫째→먼저' 류 치환은 폐기(2026-06-12 운영자 지적 — '먼저/그리고/끝으로'
    # 나열 잔재 자체가 AI틱). 나열은 룰 골격·프롬프트에서 원천 제거.
    t = re.sub(r"\s*→\s*", ", ", t)  # 화살표 → 쉼표(서사화)
    t = re.sub(r"\s*[—–]\s*", ", ", t)  # em/en dash(AI 시그니처) → 쉼표(이중 방어)
    t = re.sub(r"\s*·\s*", ", ", t)  # 가운뎃점 전부 → 쉼표(기호 난발 금지 2026-06-12)
    t = re.sub(r" · ", ", ", t)  # 불릿 구분(양옆 공백) → 쉼표
    # 중복 괄호 축약: '술(술)'·'명궁(명궁)'처럼 앞말과 괄호 안이 똑같으면 괄호 제거
    # (LLM 한자병기→한글변환 부작용·자미 골격 라벨 중복). 정확 반복만 — '묘(매우 밝음)' 보존.
    t = re.sub(r"([가-힣]{1,4})\(\1\)", r"\1", t)
    # 괄호 안 잔재 정리(H1.5.1): 한자 제거 부작용. 설명 괄호('묘(매우 밝음)')는 보존.
    t = re.sub(r"\(([가-힣]{1,4})\s*,\s*\1\)", r"(\1)", t)  # (술, 술)→(술)·(진, 진)→(진)
    t = re.sub(r"\(([^),]*?)\s*,\s*\)", r"(\1)", t)  # (화, )→(화) 괄호 안 trailing comma
    t = re.sub(r"\(\s*\)", "", t)  # 빈 괄호
    # 구두점 깨짐 정규화(H1.5): '기준,, 년주 기준,.' 류. 자연 구두점(요.)은 불변.
    t = re.sub(r"(?:\s*,\s*){2,}", ", ", t)  # ',,'·', ,' → ', '
    t = re.sub(r"\s*,\s*\.", ".", t)  # ',.'·', .' → '.'
    t = re.sub(r"\.{2,}", ".", t)  # '..'(연속 마침표) → '.'
    t = collapse_adjacent_duplicates(t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" +([,.)])", r"\1", t)  # 구두점 앞 공백 정리
    return t.strip()
