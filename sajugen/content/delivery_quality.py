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
from collections.abc import Iterable, Mapping

from .. import modules as integrated_modules
from . import safe_lint

MIN_PREMIUM_PAGES = 20
MIN_GUNGHAP_PAGES = 16
MIN_INTEGRATED_FULL_PAGES = 30
MIN_FOLLOWUP_PAGES = 10
MIN_PREMIUM_TEXT_CHARS = 10_000
MIN_GUNGHAP_TEXT_CHARS = 3_000
MIN_FOLLOWUP_TEXT_CHARS = 2_000

_GUNGHAP_PRODUCTS = {"gunghap", "gunghap_relationship", "relationship_gunghap"}
_INTEGRATED_FULL_PRODUCTS = {"integrated_full"}
_FOLLOWUP_PRODUCTS = {"followup"}
_PREMIUM_PRODUCTS = (
    {"premium", "integrated", "premium_integrated", "custom"}
    | _GUNGHAP_PRODUCTS
    | _INTEGRATED_FULL_PRODUCTS
    | _FOLLOWUP_PRODUCTS
)
# 고객 질문(고민)이 반드시 있어야 하는 상품 — integrated_full·궁합·후속 PDF는 '고객 질문에
# 답하는' 맞춤 납품이라 concern 부재는 질문축 검사를 통째로 no-op 시킨다(2026-07-01 P1).
# 이 집합의 상품은 context_required 로 표시해, concern 부재 시 조용히 통과하지 않고
# missing_customer_context 로 드러낸다. (계산·게이트 완화가 아니라 누락 신호 강화.)
CONTEXT_REQUIRED_PRODUCTS = frozenset(
    _INTEGRATED_FULL_PRODUCTS | _GUNGHAP_PRODUCTS | _FOLLOWUP_PRODUCTS
)


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
# P5-3(2026-07-05, 운영자 지적 '결' 77회·'색' 은유): 상투 필러 정규식 카운터 —
# text.count 는 부분문자열이라 '결'을 세면 결혼/결론/결정을 전부 오탐(설계 검증 실측).
# 단독 명사 '결(+조사)'과 '~의 색' 은유만 센다. FAIL 승격은 v8 실측 후 운영자 결정 —
# 지금은 warning(domain_term_repetition) 보고 전용.
_REPEAT_CAP_PATTERNS: dict[str, tuple[re.Pattern[str], int]] = {
    "결(단독)": (
        re.compile(r"(?<![가-힣])결(?:이|을|은|의|과|와|로|도|입니다|이에요)?(?![가-힣])"),
        12,
    ),
    "의 색": (re.compile(r"의\s*색(?:이|을|은|과|와|으로|도)?(?![가-힣])"), 4),
}
_REPEAT_BASE_LEN = 10_000

# P3(2026-07-05, 운영자 승인 — 절대규칙 12 '사각 축소 방향' 정밀화):
# '무조건' 단독 금지가 정당한 행동·시기 단정("무조건 미룰 일은 아닙니다")까지 차단해
# 재작성/폴백을 유발하던 것을, safe_lint §12(2026-06-12 완화 원칙: 부사 단독 허용,
# 부사+결과동사 결합만 차단)와 동기화. 동시에 결과동사 어간을 OUTCOME_VERBS 재사용으로
# 확대(승진/창업/취업류 — 기존 성공|재회|결혼|된다 5종만 보던 사각 흡수 = 강화).
# 100%·"(재회|결혼)합니다" 는 불변.
_GUARANTEE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"100\s*%"), "absolute percentage"),
    # '잘 맞' = 궁합 단정 보장(retry3 갭 앵커 "무조건 잘 맞습니다" 비악화 보존).
    (
        re.compile(rf"무조건\s*[^.\n!?]{{0,14}}(?:{safe_lint.OUTCOME_VERBS}|성공|재회|잘\s*맞)"),
        "absolute guarantee",
    ),
    (
        re.compile(rf"반드시\s*[^.\n!?]{{0,14}}(?:{safe_lint.OUTCOME_VERBS}|성공|재회|잘\s*맞)"),
        "absolute guarantee",
    ),
    (
        re.compile(rf"확실히\s*[^.\n!?]{{0,14}}(?:{safe_lint.OUTCOME_VERBS}|성공|재회|잘\s*맞)"),
        "absolute guarantee",
    ),
    (re.compile(r"(?:재회|결혼)합니다"), "hard outcome statement"),
]

_AXES: dict[str, dict[str, tuple[str, ...]]] = {
    "move_house": {
        "triggers": (
            "이사",
            "집",
            "아파트",
            "매매",
            "지역",
            "거주지",
            "생활권",
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
            "지역",
            "거주지",
            "생활권",
            "동선",
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
        "triggers": ("도와", "도움", "협조", "귀인", "사람", "배우자", "조력"),
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
    "parental_approval": {
        "triggers": ("부모", "어머니", "엄마", "아버지", "가족", "반대", "허락"),
        # '시간·신뢰' 같은 일반 연애어만으로는 부모 반대 직답으로 인정하지 않는다.
        "evidence": ("부모", "어머니", "엄마", "아버지", "가족", "반대", "설득", "인사", "허락"),
    },
    "marriage_commitment": {
        "triggers": ("결혼", "혼인", "배우자", "상견례"),
        "evidence": ("결혼", "혼인", "배우자", "상견례", "결혼 준비"),
    },
    "longterm_relationship": {
        "triggers": ("3년", "몇 년", "오래 만난", "장기", "오랜 연애"),
        # 단독 '반복'은 모든 관계 글에 흔하므로 장기 관계의 직접 근거로 쓰지 않는다.
        "evidence": ("3년", "몇 년", "오래", "장기", "권태", "다음 단계", "관계를 유지", "이어 온 시간"),
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
    "move": ("이동", "밖", "지역", "거주지", "생활권", "동선", "나가", "옮"),
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

# 고객별 고유명은 전역 상수로 축적하지 않는다. 필요한 이름은 호출자가
# expected_context_terms 로 전달해 주문별로 존재·반복 횟수를 검사한다.
# 빈 튜플이 기본이면 provenance 검사는 의도적으로 비활성이고, 합성 주입 회귀로 차단 경로를 보존한다.
_PROVENANCE_CONTEXT_TERMS: tuple[str, ...] = ()


def _is_premium(product: str | None, premium: bool) -> bool:
    return bool(premium or (product or "").strip().lower() in _PREMIUM_PRODUCTS)


def _min_pages(
    product: str | None, selected_modules: Iterable[str] | None = None
) -> int:
    product_key = (product or "").strip().lower()
    if product_key in _GUNGHAP_PRODUCTS:
        return MIN_GUNGHAP_PAGES
    if product_key in _INTEGRATED_FULL_PRODUCTS:
        return integrated_modules.module_minimums(selected_modules)[0]
    if product_key in _FOLLOWUP_PRODUCTS:
        return MIN_FOLLOWUP_PAGES
    return MIN_PREMIUM_PAGES


def _min_text_chars(
    product: str | None, selected_modules: Iterable[str] | None = None
) -> int:
    product_key = (product or "").strip().lower()
    if product_key in _GUNGHAP_PRODUCTS:
        return MIN_GUNGHAP_TEXT_CHARS
    if product_key in _FOLLOWUP_PRODUCTS:
        return MIN_FOLLOWUP_TEXT_CHARS
    if product_key in _INTEGRATED_FULL_PRODUCTS:
        return integrated_modules.module_minimums(selected_modules)[1]
    return MIN_PREMIUM_TEXT_CHARS


def _hit_terms(text: str, terms: Iterable[str]) -> list[str]:
    return [t for t in terms if t and t in text]


def _required_axes(concern: str | None) -> set[str]:
    text = concern or ""
    axes = {axis for axis, spec in _AXES.items() if _hit_terms(text, spec["triggers"])}
    if axes:
        # 부모 반대·결혼 이행·장기 관계를 포함한 모든 인식 질문은 설명만으로 끝내지
        # 않고 언제 무엇을 할지까지 답해야 한다. 기존 축과 같은 timing/action 규칙 유지.
        axes.add("timing")
        axes.add("action")
    if "love_reunion" in axes:
        axes.update({"timing", "action"})
    return axes


def _repetition_hits(text: str) -> list[dict]:
    scale = max(1.0, len(text) / _REPEAT_BASE_LEN)
    hits: list[dict] = []
    # P5-3: 정규식 카운터(단독 '결'·'의 색') — _FAIL_REPEAT_TERMS 미포함 = warning 전용.
    for term, (rx, cap) in _REPEAT_CAP_PATTERNS.items():
        count = len(rx.findall(text))
        allowed = int(math.ceil(cap * scale))
        if count > allowed:
            hits.append({"term": term, "count": count, "allowed": allowed})
    for word, cap in _REPEAT_CAPS.items():
        count = text.count(word)
        allowed = int(math.ceil(cap * scale))
        if count > allowed:
            hits.append({"term": word, "count": count, "allowed": allowed})
    return hits


# P2(2026-07-05, QI-2026-07-05-03): consult 최소 밀도 하한. v7 실사고 = generic 골격
# 388자(공백 제외)로 붕괴했는데 frontload 게이트는 intro 초반 1800자만 봐 false-PASS.
# 하한은 골격 최소(연애 분기 약 560자)보다 낮게 잡아 골격 폴백은 항상 통과(fail-closed 가
# 아니라 '붕괴 감지'가 목적 — 골격 자체의 밀도 하한은 test_consult_skeleton 이 별도 고정).
MIN_CONSULT_CHARS = 450


def consult_direct_result(text: str, concern: str | None) -> dict:
    """consult(신청 질문 답변) 챕터의 직답성 검사 — builder compose 가드·pipeline 게이트 공용.

    concern 부재는 조용한 통과가 아니라 skipped 로 구분 보고(B-2 fail-closed 관측 원칙).
    검사: 최소 밀도 + 결론/시기/행동 표지 + 질문축 evidence(축이 잡힌 concern 만).
    """
    if not (concern or "").strip():
        return {"ok": True, "skipped": True, "missing": []}
    body = text or ""
    dense = len(body.replace(" ", "").replace("\n", ""))
    missing: list[str] = []
    if dense < MIN_CONSULT_CHARS:
        missing.append(f"min_chars({dense}<{MIN_CONSULT_CHARS})")
    if not _hit_terms(body, _FRONTLOAD_TERMS["decision"]):
        missing.append("decision")
    if not _hit_terms(body, _FRONTLOAD_TERMS["timing"]):
        missing.append("timing")
    if not _hit_terms(body, _FRONTLOAD_TERMS["action"]):
        missing.append("action")
    topic_axes = sorted(a for a in _required_axes(concern) if a not in {"timing", "action"})
    missing_topic_axes = [
        axis for axis in topic_axes if not _hit_terms(body, _AXES[axis]["evidence"])
    ]
    if missing_topic_axes:
        missing.append("question_topic")
    return {
        "ok": not missing,
        "skipped": False,
        "missing": missing,
        "dense_chars": dense,
        "required_topic_axes": topic_axes,
        "missing_topic_axes": missing_topic_axes,
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
        "missing_module_sections": "선택한 질문 영역 모듈의 본문 섹션이 누락되었습니다.",
        "unexpected_module_sections": "선택하지 않은 질문 영역 모듈의 본문 섹션이 유입되었습니다.",
        "missing_question_axes": "질문 축에 대한 답변 근거가 부족합니다.",
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
    for key in ("value", "minimum", "axes", "modules", "section_ids"):
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
    selected_modules: Iterable[str] | None = None,
    module_sections: Mapping[str, Iterable[str]] | None = None,
    premerge_section_ids: Iterable[str] | None = None,
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

    product_key = (product or "").strip().lower()
    module_coverage: dict[str, object]
    if product_key in _INTEGRATED_FULL_PRODUCTS:
        # v3: 커버리지는 sparse 병합 뒤의 PDF 제목이 아니라 조립기가 넘긴 병합 전 ID 맵으로
        # 판정한다. 모듈 인자가 없는 레거시는 5모듈 전체 계약으로 복원하며 skipped가 아니다.
        module_coverage = integrated_modules.module_coverage(
            selected_modules, module_sections, premerge_section_ids
        )
        missing_modules = list(module_coverage["missing_modules"])
        unexpected_modules = list(module_coverage["unexpected_modules"])
        unknown_section_ids = list(module_coverage["unknown_section_ids"])
        if missing_modules:
            failures.append({"rule": "missing_module_sections", "modules": missing_modules})
        if unexpected_modules or unknown_section_ids:
            failures.append(
                {
                    "rule": "unexpected_module_sections",
                    "modules": unexpected_modules,
                    "section_ids": unknown_section_ids,
                }
            )
    else:
        module_coverage = {
            "selected_modules": [],
            "module_sections": {},
            "missing_modules": [],
            "unexpected_modules": [],
            "unknown_section_ids": [],
            "premerge_section_ids": [],
            "checked_before_sparse_merge": False,
            "skipped": True,
        }
    effective_selected_modules = module_coverage["selected_modules"] or selected_modules

    if context_required and is_premium and not has_customer_context:
        # 고객 질문 필수 상품인데 concern 이 delivery_quality 까지 도달하지 않음 =
        # 질문축 검사가 no-op 된 상태. false-pass 방지(조용한 통과 금지).
        failures.append({"rule": "missing_customer_context", "product": product})

    if is_premium:
        min_pages = _min_pages(product, effective_selected_modules)
        min_text_chars = _min_text_chars(product, effective_selected_modules)
        if pages is not None and pages < min_pages:
            failures.append(
                {
                    "rule": "premium_pages",
                    "value": pages,
                    "minimum": min_pages,
                }
            )
        if len(text) < min_text_chars:
            failures.append(
                {
                    "rule": "premium_text_chars",
                    "value": len(text),
                    "minimum": min_text_chars,
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
        "min_followup_pages": MIN_FOLLOWUP_PAGES,
        "min_premium_text_chars": MIN_PREMIUM_TEXT_CHARS,
        "min_gunghap_text_chars": MIN_GUNGHAP_TEXT_CHARS,
        "min_integrated_full_text_chars": MIN_PREMIUM_TEXT_CHARS,
        "min_followup_text_chars": MIN_FOLLOWUP_TEXT_CHARS,
        "minimum_pages": (
            _min_pages(product, effective_selected_modules) if is_premium else None
        ),
        "minimum_text_chars": (
            _min_text_chars(product, effective_selected_modules) if is_premium else None
        ),
        "selected_modules": module_coverage["selected_modules"],
        "module_schema_version": integrated_modules.MODULE_SCHEMA_VERSION,
        "module_sections": module_coverage["module_sections"],
        "module_coverage": module_coverage,
        "failures": failures,
        "warnings": warnings,
        "failure_messages": [_finding_message(f) for f in failures],
        "warning_messages": [_finding_message(w) for w in warnings],
        "required_axes": sorted(required_axes),
        "coverage_hits": coverage_hits,
        "missing_axes": missing_axes,
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
