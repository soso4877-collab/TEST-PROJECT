# -*- coding: utf-8 -*-
"""Delivery-level quality checks for paid/custom PDF readings.

This module intentionally checks the final customer-facing text, not the
underlying deterministic calculation.  It is used as an additional gate for
premium/custom deliveries where the PDF must be long enough, answer the actual
question, include a usable ziwei perspective, and avoid repetitive AI-like
phrasing.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

MIN_PREMIUM_PAGES = 20
MIN_GUNGHAP_PAGES = 30
MIN_INTEGRATED_FULL_PAGES = 30
MIN_PREMIUM_TEXT_CHARS = 10_000

_GUNGHAP_PRODUCTS = {"gunghap", "gunghap_relationship", "relationship_gunghap"}
_INTEGRATED_FULL_PRODUCTS = {"integrated_full"}
_PREMIUM_PRODUCTS = (
    {"premium", "integrated", "premium_integrated", "custom"}
    | _GUNGHAP_PRODUCTS
    | _INTEGRATED_FULL_PRODUCTS
)
# 고객 질문(고민)이 반드시 있어야 하는 상품 — integrated_full·궁합 계열은 '고객 질문에
# 답하는' 맞춤 납품이라 concern 부재는 질문축 검사를 통째로 no-op 시킨다(2026-07-01 P1).
# 이 집합의 상품은 context_required 로 표시해, concern 부재 시 조용히 통과하지 않고
# missing_customer_context 로 드러낸다. (계산·게이트 완화가 아니라 누락 신호 강화.)
CONTEXT_REQUIRED_PRODUCTS = frozenset(_INTEGRATED_FULL_PRODUCTS | _GUNGHAP_PRODUCTS)


def context_required_for(product: str | None) -> bool:
    """product 가 고객 질문이 필수인 상품(integrated_full·궁합 계열)인지."""
    return (product or "").strip().lower() in CONTEXT_REQUIRED_PRODUCTS


_REPEAT_CAPS = {
    "또렷": 0,
    "흐름": 8,
    "기운": 10,
    "구조": 8,
    "자리": 12,
    "정리": 8,
    "중심": 8,
}
_FAIL_REPEAT_TERMS = {"또렷"}
_REPEAT_BASE_LEN = 10_000
_FRONTLOAD_CHARS = 1_800

_GUARANTEE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"100\s*%"), "absolute percentage"),
    (re.compile(r"무조건"), "absolute guarantee"),
    (re.compile(r"반드시\s*(?:성공|재회|결혼|된다|됩니다)"), "absolute guarantee"),
    (re.compile(r"확실히\s*(?:성공|재회|결혼|된다|됩니다)"), "absolute guarantee"),
    (re.compile(r"(?:재회|결혼)합니다"), "hard outcome statement"),
]

_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "move_house": {
        "triggers": (
            "이사",
            "집",
            "아파트",
            "매매",
            "김포",
            "계양",
            "부동산",
            "거처",
            "땅",
            "토지",
        ),
        "evidence": (
            "이사",
            "집",
            "아파트",
            "매매",
            "계약",
            "김포",
            "계양",
            "부동산",
            "거처",
            "터전",
            "땅",
            "토지",
        ),
    },
    "club_group": {
        "triggers": ("로타리", "클럽", "창립", "모임", "단체", "봉사"),
        "evidence": ("로타리", "클럽", "창립", "모임", "단체", "봉사", "사람", "역할"),
    },
    "helper_people": {
        "triggers": ("도와", "도움", "협조", "귀인", "사람", "장재화", "배우자", "조력"),
        "evidence": ("도움", "협조", "사람", "배우자", "조력", "맡기", "확인", "거리"),
    },
    "money_contract": {
        "triggers": (
            "돈",
            "재물",
            "재산",
            "자산",
            "계약",
            "매매",
            "가격",
            "손해",
            "대출",
            "부동산",
            "땅",
            "토지",
            "땅값",
        ),
        "evidence": (
            "돈",
            "재물",
            "재산",
            "자산",
            "계약",
            "매매",
            "가격",
            "손해",
            "서류",
            "명의",
            "잔금",
            "땅",
            "토지",
            "세금",
            "현금화",
        ),
    },
    "children_family": {
        "triggers": ("자식복", "자식", "자녀", "아이"),
        "evidence": ("자식복", "자식", "자녀", "아이", "의지", "간섭", "거리"),
    },
    "danger_period": {
        "triggers": ("위험", "조심", "주의", "손실", "크게 잃", "무너"),
        "evidence": ("위험", "조심", "주의", "손실", "보증", "명의", "무리한 확장", "큰돈"),
    },
    "love_reunion": {
        "triggers": (
            "재회",
            "연애",
            "결혼",
            "전남친",
            "전여친",
            "헤어진",
            "소개팅",
            "만남",
        ),
        "evidence": (
            "재회",
            "연애",
            "결혼",
            "만남",
            "상대",
            "연락",
            "대화",
            "판단",
            "소개팅",
            "현재 만나는 사람",
            "생활 기준",
            "돈 관리",
            "배우자 기준",
        ),
    },
    "relationship_intent": {
        "triggers": ("썸", "호감", "진심", "상대방", "마음"),
        "evidence": ("썸", "호감", "진심", "상대", "마음", "표현", "속도"),
    },
    "relationship_conflict": {
        "triggers": ("대화", "갈등", "생각하는 방식", "차이"),
        "evidence": ("대화", "갈등", "생각", "차이", "말", "속도", "조율"),
    },
    "relationship_values": {
        "triggers": ("성격", "가치관", "연애관"),
        "evidence": ("성격", "가치관", "연애관", "생활 기준", "관계 기준", "맞추"),
    },
    "relationship_stability": {
        "triggers": ("안정", "좋은 영향", "이어갈", "관계"),
        "evidence": ("안정", "좋은 영향", "이어갈", "관계", "신뢰", "지속"),
    },
    "relationship_compatibility": {
        "triggers": ("궁합", "잘 맞", "맞는지"),
        "evidence": ("궁합", "맞는", "맞추", "보완", "끌림", "관계"),
    },
    "timing": {
        "triggers": ("언제", "시기", "올해", "내년", "1년", "일년", "상반기", "하반기"),
        "evidence": (
            "1년",
            "일년",
            "올해",
            "내년",
            "상반기",
            "하반기",
            "봄",
            "여름",
            "가을",
            "겨울",
            "월",
            "시기",
            "판단 지점",
        ),
    },
    "action": {
        "triggers": ("어떻게", "방법", "해야", "다가", "주의", "조심", "확인"),
        "evidence": (
            "먼저",
            "확인",
            "주의",
            "조심",
            "기다",
            "다가",
            "말",
            "정하",
            "피하",
            "서두르",
        ),
    },
}

_ZIWEI_MARKERS = ("자미두수", "자미", "천부", "천량", "천이", "전택", "재백", "관록")
_ZIWEI_DOMAIN_TERMS = {
    "home": ("집", "터전", "이사", "부동산", "거처"),
    "money": ("돈", "재물", "재산", "자산", "계약", "매매", "가격", "땅", "토지"),
    "work": ("일", "직업", "역할", "창립", "운영"),
    "people": ("사람", "관계", "배우자", "도움", "협조"),
    "move": ("이동", "밖", "김포", "계양", "나가", "옮"),
}

_NEAR_TERM_TIMING_TERMS = (
    "1년",
    "일년",
    "올해",
    "내년",
    "상반기",
    "하반기",
    "봄",
    "여름",
    "가을",
    "겨울",
    "월",
)

_LOVE_ACTION_TERMS = (
    "연락",
    "안부",
    "소개팅",
    "첫 만남",
    "현재 만나는 사람",
    "생활 기준",
    "돈 관리",
    "가족",
    "다가",
    "접점",
    "약속",
)

_LOVE_CAUTION_TERMS = (
    "조심",
    "주의",
    "멈추",
    "물러서",
    "서두르",
    "답이 짧",
    "늦어지",
    "무리",
    "반복",
)

_MYEONGNI_MARKERS = ("명리", "사주")

_FRONTLOAD_TERMS = {
    "decision": ("결론", "핵심", "먼저", "한마디", "정리하면", "말씀드리면"),
    "timing": _NEAR_TERM_TIMING_TERMS + ("시기", "판단 지점"),
    "action": ("먼저", "확인", "주의", "조심", "기다", "다가", "말", "정하", "피하", "서두르"),
}

# Customer-specific context that is easy to hallucinate and must be grounded in
# the order concern or explicit expected_context_terms.
_PROVENANCE_CONTEXT_TERMS = ("청마",)


def _is_premium(product: str | None, premium: bool) -> bool:
    return bool(premium or (product or "").strip().lower() in _PREMIUM_PRODUCTS)


def _min_pages(product: str | None) -> int:
    product_key = (product or "").strip().lower()
    if product_key in _GUNGHAP_PRODUCTS:
        return MIN_GUNGHAP_PAGES
    if product_key in _INTEGRATED_FULL_PRODUCTS:
        return MIN_INTEGRATED_FULL_PAGES
    return MIN_PREMIUM_PAGES


def _hit_terms(text: str, terms: Iterable[str]) -> list[str]:
    return [t for t in terms if t and t in text]


def _required_axes(concern: str | None) -> set[str]:
    text = concern or ""
    axes = {axis for axis, spec in _AXES.items() if _hit_terms(text, spec["triggers"])}
    if axes:
        axes.add("timing")
        axes.add("action")
    if "love_reunion" in axes:
        axes.update({"timing", "action"})
    return axes


def _repetition_hits(text: str) -> list[dict]:
    scale = max(1.0, len(text) / _REPEAT_BASE_LEN)
    hits: list[dict] = []
    for word, cap in _REPEAT_CAPS.items():
        count = text.count(word)
        allowed = int(math.ceil(cap * scale))
        if count > allowed:
            hits.append({"term": word, "count": count, "allowed": allowed})
    return hits


def _frontloaded_result(text: str, required_axes: set[str]) -> dict:
    """Check that a paid answer gives the customer a usable answer early."""

    if not required_axes:
        return {"ok": True, "missing": [], "window_chars": _FRONTLOAD_CHARS}

    early = text[:_FRONTLOAD_CHARS]
    missing: list[str] = []
    if not _hit_terms(early, _FRONTLOAD_TERMS["decision"]):
        missing.append("decision")
    if "timing" in required_axes and not _hit_terms(early, _FRONTLOAD_TERMS["timing"]):
        missing.append("timing")
    if "action" in required_axes and not _hit_terms(early, _FRONTLOAD_TERMS["action"]):
        missing.append("action")

    topic_axes = sorted(a for a in required_axes if a not in {"timing", "action"})
    covered_topic_axes = [axis for axis in topic_axes if _hit_terms(early, _AXES[axis]["evidence"])]
    if topic_axes and not covered_topic_axes:
        missing.append("question_topic")

    return {
        "ok": not missing,
        "missing": missing,
        "window_chars": _FRONTLOAD_CHARS,
        "covered_topic_axes": covered_topic_axes,
    }


_PHYSICAL_FRONTLOAD_PAGES = 3  # 고객이 체감하는 '초반' = 물리 첫 3페이지


def _page_has_direct_answer(page_text: str, required_axes: set[str]) -> bool:
    """물리 한 페이지가 직접 답변(결론 표지 + 질문 주제/시기 근거)을 담는지."""
    if not _hit_terms(page_text, _FRONTLOAD_TERMS["decision"]):
        return False
    topic_axes = [a for a in required_axes if a not in {"timing", "action"}]
    if any(_hit_terms(page_text, _AXES[axis]["evidence"]) for axis in topic_axes):
        return True
    if "timing" in required_axes and _hit_terms(page_text, _FRONTLOAD_TERMS["timing"]):
        return True
    # 주제/시기 축이 없으면 결론 표지만으로도 초반 답변으로 인정(과탐 방지).
    return not topic_axes and "timing" not in required_axes


def _physical_frontloaded_result(
    page_texts: list[str] | None,
    required_axes: set[str],
    first_pages: int = _PHYSICAL_FRONTLOAD_PAGES,
) -> dict:
    """물리 페이지 기준 초반 답변 보조지표(보고용). char 기반 frontloaded_answer 와 별개.

    표지/목차가 물리 p1~p3을 차지해 고객 체감 '초반'에 답변이 없을 때를 드러낸다.
    concern/required_axes 가 있을 때만 평가하며, 게이트(clean/gate_pass)는 바꾸지 않고
    warning 으로만 보고한다(false-pass 가시화 — 게이트 완화·과차단 아님).
    """
    if not required_axes or not page_texts:
        return {"required": False, "ok": True, "first_pages": first_pages, "answer_page": None}
    answer_page = None
    for idx, page_text in enumerate(page_texts, start=1):
        if _page_has_direct_answer(page_text or "", required_axes):
            answer_page = idx
            break
    return {
        "required": True,
        "ok": answer_page is not None and answer_page <= first_pages,
        "first_pages": first_pages,
        "answer_page": answer_page,
    }


def _near_term_timing_result(text: str, required_axes: set[str]) -> dict:
    """Love/reunion customers usually ask for a near-term usable window."""

    if "love_reunion" not in required_axes:
        return {"required": False, "ok": True, "hits": []}
    hits = _hit_terms(text, _NEAR_TERM_TIMING_TERMS)
    return {"required": True, "ok": bool(hits), "hits": hits}


def _love_action_result(text: str, required_axes: set[str]) -> dict:
    """Paid love/reunion/marriage answers need usable action and caution."""

    if "love_reunion" not in required_axes:
        return {"required": False, "ok": True, "action_hits": [], "caution_hits": []}
    action_hits = _hit_terms(text, _LOVE_ACTION_TERMS)
    caution_hits = _hit_terms(text, _LOVE_CAUTION_TERMS)
    return {
        "required": True,
        "ok": bool(action_hits) and bool(caution_hits),
        "action_hits": action_hits,
        "caution_hits": caution_hits,
    }


def _love_myeongni_result(text: str, required_axes: set[str]) -> dict:
    """Love-axis paid answers should not lean on ziwei alone."""

    if "love_reunion" not in required_axes:
        return {"required": False, "ok": True, "hits": []}
    hits = _hit_terms(text, _MYEONGNI_MARKERS)
    return {"required": True, "ok": bool(hits), "hits": hits}


def _guarantee_hits(text: str) -> list[dict]:
    hits: list[dict] = []
    for rx, why in _GUARANTEE_PATTERNS:
        for m in rx.finditer(text):
            hits.append({"match": m.group(0), "why": why, "pos": m.start()})
            break
    return hits


def guarantee_lint(text: str) -> list[dict]:
    """compose 단계용 보장형 가드 헬퍼(builder/gunghap 가 cand/retry 에 붙임).

    결과 보장처럼 읽히는 표현(absolute_guarantee 계열)을 최종 납품 게이트 전에
    compose 단계에서 잡아 재작성/폴백시키기 위한 public 헬퍼. 기준은 analyze() 가
    쓰는 _GUARANTEE_PATTERNS / _guarantee_hits 와 **동일**하다(같은 내부 함수에 위임 —
    룰 완화·중복정의·analyze 동작 변경 없음). 배경: safe_lint 와 delivery_quality 의
    보장형 탐지 범위가 달라, LLM 후보가 compose 가드는 통과하고 최종 PDF delivery
    게이트에서만 BLOCKED 되던 갭(2026-06-30, Tier2 retry3)을 차단한다.
    반환은 hit dict 리스트(빈 리스트=clean). dict 의 match 원문은 테스트에서만 쓰고
    운영 보고에는 출력하지 않는다.
    """
    return _guarantee_hits(text or "")


def _ziwei_result(text: str) -> dict:
    markers = _hit_terms(text, _ZIWEI_MARKERS)
    domains = {
        name: _hit_terms(text, terms)
        for name, terms in _ZIWEI_DOMAIN_TERMS.items()
        if _hit_terms(text, terms)
    }
    cross_domains: dict[str, list[str]] = {}
    for marker in _ZIWEI_MARKERS:
        for match in re.finditer(re.escape(marker), text):
            start = max(0, match.start() - 180)
            end = min(len(text), match.end() + 260)
            window = text[start:end]
            for name, terms in _ZIWEI_DOMAIN_TERMS.items():
                hits = _hit_terms(window, terms)
                if hits:
                    cross_domains.setdefault(name, [])
                    for hit in hits:
                        if hit not in cross_domains[name]:
                            cross_domains[name].append(hit)
    return {
        "markers": markers,
        "domains": domains,
        "cross_domains": cross_domains,
        "ok": bool(markers) and len(cross_domains) >= 2,
    }


def _context_provenance_result(
    text: str,
    concern: str | None,
    expected_context_terms: list[str] | None,
) -> dict:
    concern = concern or ""
    expected = set(expected_context_terms or [])
    unbacked = [
        term
        for term in _PROVENANCE_CONTEXT_TERMS
        if term in text and term not in concern and term not in expected
    ]
    return {"ok": not unbacked, "unbacked_terms": unbacked}


def _finding_message(finding: dict) -> dict:
    rule = finding.get("rule", "unknown")
    messages = {
        "premium_pages": "납품 페이지 수가 상품 기준보다 적습니다.",
        "premium_text_chars": "납품 본문 글자 수가 상품 기준보다 적습니다.",
        "premium_low_density_pages": "본문 밀도가 낮은 페이지가 있습니다.",
        "missing_customer_context": "고객 질문(고민)이 이 상품의 품질 검사까지 전달되지 않았습니다.",
        "missing_question_axes": "질문 축에 대한 답변 근거가 부족합니다.",
        "missing_frontloaded_answer": "초반부에 결론, 시기, 행동 기준이 충분히 앞서 나오지 않았습니다.",
        "physical_frontloaded_answer": "물리 첫 3페이지(표지/목차 포함) 안에 직접 답변이 보이지 않습니다(검수 확인).",
        "missing_near_term_timing": "연애/재회 질문에 필요한 가까운 시기 기준이 부족합니다.",
        "missing_love_reunion_action": "연애/재회 질문에 필요한 행동 기준과 주의 기준이 부족합니다.",
        "repetitive_phrasing": "반복 표현이 기준을 넘었습니다.",
        "domain_term_repetition": "영역 단어 반복이 많습니다.",
        "absolute_guarantee": "결과 보장처럼 읽히는 표현이 있습니다.",
        "missing_usable_ziwei": "자미두수 관점이 고객 질문과 충분히 연결되지 않았습니다.",
        "missing_love_myeongni": "연애/재회 질문에 필요한 명리 관점이 부족합니다.",
        "unbacked_context_terms": "입력 근거 없는 맥락 단어가 본문에 들어갔습니다.",
        "missing_expected_context": "요청된 맥락 단어가 본문에 반영되지 않았습니다.",
        "overused_expected_context": "요청된 맥락 단어가 과도하게 반복됩니다.",
    }
    out = {"rule": rule, "message": messages.get(rule, "납품 품질 기준을 충족하지 못했습니다.")}
    for key in ("value", "minimum", "axes"):
        if key in finding:
            out[key] = finding[key]
    if "pages" in finding:
        out["pages_count"] = len(finding.get("pages") or [])
    return out


def analyze(
    text: str,
    *,
    pages: int | None = None,
    low_density_pages: list[dict] | None = None,
    product: str | None = None,
    premium: bool = False,
    concern: str | None = None,
    expected_context_terms: list[str] | None = None,
    context_required: bool = False,
    page_texts: list[str] | None = None,
) -> dict:
    """Return customer-delivery quality findings.

    The default non-premium mode reports findings but does not require premium
    length/ziwei/depth thresholds.  Callers that pass premium=True get a hard
    clean=False result when a paid-delivery requirement is missed.

    context_required=True (integrated_full·궁합 계열 실제 납품 경로에서 verify 가 지정)
    이면 고객 질문(concern/expected_context_terms)이 비어 있을 때 조용히 통과하지 않고
    missing_customer_context 로 실패시킨다. 기본 False — 무고객 합성/단위 테스트 경로는
    영향받지 않는다(질문축 검사가 의도적으로 스킵되는 경로 보존).
    """

    text = text or ""
    is_premium = _is_premium(product, premium)
    has_customer_context = bool((concern or "").strip() or expected_context_terms)
    failures: list[dict] = []
    warnings: list[dict] = []

    if context_required and is_premium and not has_customer_context:
        # 고객 질문 필수 상품인데 concern 이 delivery_quality 까지 도달하지 않음 =
        # 질문축 검사가 no-op 된 상태. false-pass 방지(조용한 통과 금지).
        failures.append({"rule": "missing_customer_context", "product": product})

    if is_premium:
        min_pages = _min_pages(product)
        if pages is not None and pages < min_pages:
            failures.append(
                {
                    "rule": "premium_pages",
                    "value": pages,
                    "minimum": min_pages,
                }
            )
        if len(text) < MIN_PREMIUM_TEXT_CHARS:
            failures.append(
                {
                    "rule": "premium_text_chars",
                    "value": len(text),
                    "minimum": MIN_PREMIUM_TEXT_CHARS,
                }
            )
        if low_density_pages:
            finding = {
                "rule": "premium_low_density_pages",
                "pages": low_density_pages[:20],
            }
            if has_customer_context:
                failures.append(finding)
            else:
                warnings.append(finding)

    required_axes = _required_axes(concern)
    coverage_hits = {
        axis: _hit_terms(text, _AXES[axis]["evidence"]) for axis in sorted(required_axes)
    }
    missing_axes = [axis for axis, hits in coverage_hits.items() if not hits]
    if missing_axes:
        failures.append({"rule": "missing_question_axes", "axes": missing_axes})

    frontloaded = _frontloaded_result(text, required_axes)
    if is_premium and not frontloaded["ok"]:
        failures.append({"rule": "missing_frontloaded_answer", "frontloaded": frontloaded})

    # 물리 페이지 기준 초반 답변(보고용 warning — 게이트 미변경). 표지/목차가 물리 p1~p3을
    # 차지해 고객 체감 초반에 답변이 없을 때를 드러낸다(char 기반 frontloaded 와 별개).
    physical_frontloaded = _physical_frontloaded_result(page_texts, required_axes)
    if is_premium and physical_frontloaded["required"] and not physical_frontloaded["ok"]:
        warnings.append(
            {"rule": "physical_frontloaded_answer", "physical_frontloaded": physical_frontloaded}
        )

    near_term_timing = _near_term_timing_result(text, required_axes)
    if is_premium and not near_term_timing["ok"]:
        failures.append({"rule": "missing_near_term_timing", "timing": near_term_timing})

    love_action = _love_action_result(text, required_axes)
    if is_premium and not love_action["ok"]:
        failures.append({"rule": "missing_love_reunion_action", "action": love_action})

    repetition_hits = _repetition_hits(text)
    if repetition_hits:
        fail_hits = [h for h in repetition_hits if h["term"] in _FAIL_REPEAT_TERMS]
        warn_hits = [h for h in repetition_hits if h["term"] not in _FAIL_REPEAT_TERMS]
        if fail_hits:
            finding = {"rule": "repetitive_phrasing", "hits": fail_hits}
            if (is_premium and has_customer_context) or required_axes:
                failures.append(finding)
            else:
                warnings.append(finding)
        if warn_hits:
            warnings.append({"rule": "domain_term_repetition", "hits": warn_hits})

    guarantee_hits = _guarantee_hits(text)
    if guarantee_hits:
        failures.append({"rule": "absolute_guarantee", "hits": guarantee_hits})

    ziwei = _ziwei_result(text)
    if is_premium and not ziwei["ok"]:
        failures.append({"rule": "missing_usable_ziwei", "ziwei": ziwei})

    love_myeongni = _love_myeongni_result(text, required_axes)
    if is_premium and not love_myeongni["ok"]:
        failures.append({"rule": "missing_love_myeongni", "myeongni": love_myeongni})

    context_provenance = _context_provenance_result(text, concern, expected_context_terms)
    if is_premium and not context_provenance["ok"]:
        failures.append({"rule": "unbacked_context_terms", "context": context_provenance})

    context_hits = {term: text.count(term) for term in expected_context_terms or [] if term}
    missing_context = [term for term, count in context_hits.items() if count == 0]
    overused_context = {term: count for term, count in context_hits.items() if count > 3}
    if missing_context:
        failures.append({"rule": "missing_expected_context", "terms": missing_context})
    if overused_context:
        warnings.append({"rule": "overused_expected_context", "terms": overused_context})

    return {
        "clean": not failures,
        "premium": is_premium,
        "product": product,
        "has_customer_context": has_customer_context,
        "pages": pages,
        "text_chars": len(text),
        "min_premium_pages": MIN_PREMIUM_PAGES,
        "min_gunghap_pages": MIN_GUNGHAP_PAGES,
        "min_integrated_full_pages": MIN_INTEGRATED_FULL_PAGES,
        "min_premium_text_chars": MIN_PREMIUM_TEXT_CHARS,
        "failures": failures,
        "warnings": warnings,
        "failure_messages": [_finding_message(f) for f in failures],
        "warning_messages": [_finding_message(w) for w in warnings],
        "required_axes": sorted(required_axes),
        "coverage_hits": coverage_hits,
        "missing_axes": missing_axes,
        "frontloaded_answer": frontloaded,
        "physical_frontloaded_answer": physical_frontloaded,
        "near_term_timing": near_term_timing,
        "love_action": love_action,
        "love_myeongni": love_myeongni,
        "repetition_hits": repetition_hits,
        "guarantee_hits": guarantee_hits,
        "ziwei": ziwei,
        "context_provenance": context_provenance,
        "expected_context_hits": context_hits,
        "missing_context_terms": missing_context,
        "overused_context_terms": overused_context,
    }


def is_clean(text: str, **kwargs) -> bool:
    return bool(analyze(text, **kwargs)["clean"])
