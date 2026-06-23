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
MIN_PREMIUM_TEXT_CHARS = 10_000

_PREMIUM_PRODUCTS = {"premium", "integrated", "premium_integrated", "custom"}

_REPEAT_CAPS = {
    "또렷": 0,
    "흐름": 8,
    "기운": 10,
    "구조": 8,
    "자리": 12,
    "정리": 8,
    "중심": 8,
}
_REPEAT_BASE_LEN = 10_000

_GUARANTEE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"100\s*%"), "absolute percentage"),
    (re.compile(r"무조건"), "absolute guarantee"),
    (re.compile(r"반드시\s*(?:성공|재회|결혼|된다|됩니다)"), "absolute guarantee"),
    (re.compile(r"확실히\s*(?:성공|재회|결혼|된다|됩니다)"), "absolute guarantee"),
    (re.compile(r"(?:재회|결혼)합니다"), "hard outcome statement"),
]

_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "move_house": {
        "triggers": ("이사", "집", "아파트", "매매", "김포", "계양", "부동산", "거처"),
        "evidence": ("이사", "집", "아파트", "매매", "계약", "김포", "계양", "부동산", "거처", "터전"),
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
        "triggers": ("돈", "재물", "계약", "매매", "가격", "손해", "대출", "부동산"),
        "evidence": ("돈", "재물", "계약", "매매", "가격", "손해", "서류", "명의", "잔금"),
    },
    "love_reunion": {
        "triggers": ("재회", "연애", "결혼", "전남친", "전여친", "헤어진", "소개팅", "만남"),
        "evidence": ("재회", "연애", "결혼", "만남", "상대", "연락", "대화", "판단"),
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
        "evidence": ("먼저", "확인", "주의", "조심", "기다", "다가", "말", "정하", "피하", "서두르"),
    },
}

_ZIWEI_MARKERS = ("자미두수", "자미", "천부", "천량", "천이", "전택", "재백", "관록")
_ZIWEI_DOMAIN_TERMS = {
    "home": ("집", "터전", "이사", "부동산", "거처"),
    "money": ("돈", "재물", "계약", "매매", "가격"),
    "work": ("일", "직업", "역할", "창립", "운영"),
    "people": ("사람", "관계", "배우자", "도움", "협조"),
    "move": ("이동", "밖", "김포", "계양", "나가", "옮"),
}


def _is_premium(product: str | None, premium: bool) -> bool:
    return bool(premium or (product or "").strip().lower() in _PREMIUM_PRODUCTS)


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


def _guarantee_hits(text: str) -> list[dict]:
    hits: list[dict] = []
    for rx, why in _GUARANTEE_PATTERNS:
        for m in rx.finditer(text):
            hits.append({"match": m.group(0), "why": why, "pos": m.start()})
            break
    return hits


def _ziwei_result(text: str) -> dict:
    markers = _hit_terms(text, _ZIWEI_MARKERS)
    domains = {
        name: _hit_terms(text, terms)
        for name, terms in _ZIWEI_DOMAIN_TERMS.items()
        if _hit_terms(text, terms)
    }
    return {
        "markers": markers,
        "domains": domains,
        "ok": bool(markers) and len(domains) >= 2,
    }


def analyze(
    text: str,
    *,
    pages: int | None = None,
    low_density_pages: list[dict] | None = None,
    product: str | None = None,
    premium: bool = False,
    concern: str | None = None,
    expected_context_terms: list[str] | None = None,
) -> dict:
    """Return customer-delivery quality findings.

    The default non-premium mode reports findings but does not require premium
    length/ziwei/depth thresholds.  Callers that pass premium=True get a hard
    clean=False result when a paid-delivery requirement is missed.
    """

    text = text or ""
    is_premium = _is_premium(product, premium)
    failures: list[dict] = []
    warnings: list[dict] = []

    if is_premium:
        if pages is not None and pages < MIN_PREMIUM_PAGES:
            failures.append(
                {
                    "rule": "premium_pages",
                    "value": pages,
                    "minimum": MIN_PREMIUM_PAGES,
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
            failures.append(
                {
                    "rule": "premium_low_density_pages",
                    "pages": low_density_pages[:20],
                }
            )

    required_axes = _required_axes(concern)
    coverage_hits = {
        axis: _hit_terms(text, _AXES[axis]["evidence"])
        for axis in sorted(required_axes)
    }
    missing_axes = [axis for axis, hits in coverage_hits.items() if not hits]
    if missing_axes:
        failures.append({"rule": "missing_question_axes", "axes": missing_axes})

    repetition_hits = _repetition_hits(text)
    if repetition_hits:
        failures.append({"rule": "repetitive_phrasing", "hits": repetition_hits})

    guarantee_hits = _guarantee_hits(text)
    if guarantee_hits:
        failures.append({"rule": "absolute_guarantee", "hits": guarantee_hits})

    ziwei = _ziwei_result(text)
    if is_premium and not ziwei["ok"]:
        failures.append({"rule": "missing_usable_ziwei", "ziwei": ziwei})

    context_hits = {
        term: text.count(term)
        for term in expected_context_terms or []
        if term
    }
    missing_context = [term for term, count in context_hits.items() if count == 0]
    overused_context = {
        term: count
        for term, count in context_hits.items()
        if count > 3
    }
    if missing_context:
        failures.append({"rule": "missing_expected_context", "terms": missing_context})
    if overused_context:
        warnings.append({"rule": "overused_expected_context", "terms": overused_context})

    return {
        "clean": not failures,
        "premium": is_premium,
        "product": product,
        "pages": pages,
        "text_chars": len(text),
        "min_premium_pages": MIN_PREMIUM_PAGES,
        "min_premium_text_chars": MIN_PREMIUM_TEXT_CHARS,
        "failures": failures,
        "warnings": warnings,
        "required_axes": sorted(required_axes),
        "coverage_hits": coverage_hits,
        "missing_axes": missing_axes,
        "repetition_hits": repetition_hits,
        "guarantee_hits": guarantee_hits,
        "ziwei": ziwei,
        "expected_context_hits": context_hits,
        "missing_context_terms": missing_context,
        "overused_context_terms": overused_context,
    }


def is_clean(text: str, **kwargs) -> bool:
    return bool(analyze(text, **kwargs)["clean"])
