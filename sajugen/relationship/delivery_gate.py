# -*- coding: utf-8 -*-
"""관계/궁합 납품 전용 사전 게이트.

이 모듈의 실패 사유는 summary 에 그대로 실어도 PII 가 섞이지 않도록
원문 match 를 보존하지 않고 rule/field/count 중심으로 정규화한다.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from sajugen.content import client_tone_lint, quality_lint, safe_lint


@dataclass(frozen=True)
class GateResult:
    ok: bool
    failures: list[dict]


class DeliveryGateError(RuntimeError):
    """LLM/API 호출 전 관계 게이트 실패."""

    def __init__(self, failures: list[dict]):
        self.failures = normalize_failures(failures)
        super().__init__("relationship delivery gate failed: " + _brief(self.failures))


_RAW_LABEL_RX = [
    re.compile(r"고객\s*질문"),
    re.compile(r"상담\s*대상"),
    re.compile(r"이\s*장\s*에서"),
    re.compile(r"고객\s*질문"),
    re.compile(r"상담\s*대상"),
    re.compile(r"근거\s*자료"),
    re.compile(r"원문\s*라벨"),
    re.compile(r"이\s*장\s*에서"),
    re.compile(r"두\s*사람\s*사이에서\s*실제로\s*맞물리는\s*부분"),
    re.compile(r"십성\s*으로"),
    re.compile(r"일지\s*삼합"),
    re.compile(r"명궁은\s*명궁\s*[,，]\s*신궁은\s*명궁"),
    re.compile(r"자미두수로는\s*사람과\s*관계,\s*돈과\s*생활,\s*일의\s*자리"),
    re.compile(r"시기\s*흐름은\s*다음처럼"),
    re.compile(r"오행\s*(?:의)?\s*분포"),
    re.compile(r"십성축"),
    re.compile(r"신강약"),
    re.compile(r"사주팔자"),
]
_PROMPT_BIRTH_RX = re.compile(
    r"(?:19|20)\d{2}[-./년]\s*\d{1,2}[-./월]\s*\d{1,2}|"
    r"\b\d{4}\s*-\s*\d{1,2}\s*-\s*\d{1,2}\b|"
    r"\b\d{1,2}\s*:\s*\d{2}\b"
)
_HANGUL_REPEAT_RX = re.compile(
    r"(?<![가-힣])(?P<word>[가-힣]{2,8})(?:\s+(?P=word)){2,}(?![가-힣])"
)
_REPEAT_TERMS = ("흐름", "관계", "확인", "안정", "상대", "기준")


def normalize_failures(failures: list[dict]) -> list[dict]:
    out: list[dict] = []
    for f in failures:
        item = {
            "field": f.get("field"),
            "rule": f.get("rule") or f.get("type"),
        }
        for key in ("count", "term", "limit"):
            if key in f:
                item[key] = f[key]
        out.append({k: v for k, v in item.items() if v is not None})
    return out


def check(
    *,
    prompt_text: str | None = None,
    fallback_text: str | None = None,
    final_section_text: str | None = None,
    names: list[str] | None = None,
) -> GateResult:
    failures: list[dict] = []
    fields = {
        "prompt": prompt_text,
        "fallback": fallback_text,
        "final": final_section_text,
    }
    for field, text in fields.items():
        if text is None:
            continue
        failures.extend(_field_failures(field, text, names or []))
    return GateResult(ok=not failures, failures=normalize_failures(failures))


def assert_clean(**kwargs) -> None:
    result = check(**kwargs)
    if not result.ok:
        raise DeliveryGateError(result.failures)


def _field_failures(field: str, text: str, names: list[str]) -> list[dict]:
    text = text or ""
    out: list[dict] = []
    for hit in safe_lint.lint(text):
        out.append({"field": field, "rule": f"safe_{hit.get('type', 'violation')}"})
    for hit in quality_lint.lint(text, names if field != "prompt" else None):
        out.append({"field": field, "rule": hit.get("type", "quality_violation")})
    for hit in client_tone_lint.loanword_lint(text):
        out.append({"field": field, "rule": "loanword", "term": hit.get("match")})
    for hit in client_tone_lint.raw_calc_lint(text):
        out.append({"field": field, "rule": hit.get("type", "raw_calc")})
    for rx in _RAW_LABEL_RX:
        count = len(rx.findall(text))
        if count:
            out.append({"field": field, "rule": "raw_or_internal_label", "count": count})
    if field == "prompt":
        out.extend(_prompt_pii_failures(text, names))
    else:
        if re.search(r"\b\S+\s*님\b", text) and re.search(r"\b\S+\s*씨\b", text):
            out.append({"field": field, "rule": "honorific_mix"})
    for m in _HANGUL_REPEAT_RX.finditer(text):
        out.append({"field": field, "rule": "excessive_adjacent_repeat", "term": m.group("word")})
    scale = max(1, len(text) // 1200)
    for term in _REPEAT_TERMS:
        count = text.count(term)
        limit = 18 * scale
        if count > limit:
            out.append(
                {"field": field, "rule": "excessive_domain_repeat", "term": term, "count": count, "limit": limit}
            )
    return out


def _prompt_pii_failures(text: str, names: list[str]) -> list[dict]:
    out: list[dict] = []
    aliases: set[str] = set()
    for name in names:
        if not name:
            continue
        aliases.update(
            {
                name,
                client_tone_lint.given_name(name),
                client_tone_lint.honor(name),
                client_tone_lint.intro(name),
            }
        )
    for alias in sorted((a for a in aliases if a), key=len, reverse=True):
        if alias and alias in text:
            out.append({"field": "prompt", "rule": "prompt_name_exposure"})
            break
    if _PROMPT_BIRTH_RX.search(text):
        out.append({"field": "prompt", "rule": "prompt_birth_exposure"})
    return out


def _brief(failures: list[dict]) -> str:
    if not failures:
        return "unknown"
    rules = []
    for f in failures[:5]:
        label = f"{f.get('field', '?')}.{f.get('rule', '?')}"
        if label not in rules:
            rules.append(label)
    return ", ".join(rules)
