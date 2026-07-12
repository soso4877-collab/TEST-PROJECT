# -*- coding: utf-8 -*-
"""docs/14 tone-contract-v1과 런타임 register 규칙의 양방 정합.

문서에만 있는 팬텀 규칙과 코드에만 있는 미문서 규칙을 모두 막는다. 대체 문구는
사람이 고르는 작성 지침이므로 런타임 regex와 비교하지 않고, rule/token/severity만
기계 계약으로 고정한다.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from sajugen.content import client_tone_lint, delivery_quality, report_context


ROOT = Path(__file__).resolve().parents[1]


def _tone_contract() -> dict:
    text = (ROOT / "docs" / "14-tone-spec.md").read_text(encoding="utf-8")
    block = re.search(
        r"<!-- tone-contract-v1:start -->\s*```json\s*(\{.*?\})\s*```\s*"
        r"<!-- tone-contract-v1:end -->",
        text,
        re.DOTALL,
    )
    assert block, "docs/14 tone-contract-v1 JSON block missing"
    return json.loads(block.group(1))


def test_register_rules_match_docs_bidirectionally():
    contract = _tone_contract()
    documented: dict[tuple[str, str], set[str]] = {}
    for rule in contract["register_rules"]:
        documented[(rule["id"], rule["severity"])] = set(rule["tokens"])

    runtime: dict[tuple[str, str], set[str]] = defaultdict(set)
    for rule in client_tone_lint.REGISTER_RULES:
        runtime[(str(rule["rule"]), str(rule["severity"]))].add(str(rule["token"]))

    assert dict(runtime) == documented


def test_allowed_everyday_term_is_not_a_register_rule():
    contract = _tone_contract()
    runtime_tokens = {str(rule["token"]) for rule in client_tone_lint.REGISTER_RULES}
    assert set(contract["allowed_everyday_terms"]).isdisjoint(runtime_tokens)


def test_external_advice_rule_and_fixed_terms_match_docs_bidirectionally():
    contract = _tone_contract()
    external = contract["external_advice"]
    hits = delivery_quality.external_domain_advice_lint("시험 원서 접수 일정을 확인하세요.")
    assert hits
    assert {hit["rule"] for hit in hits} == {external["rule_id"]}

    runtime = {
        "domain_terms": [token for token, _pattern in delivery_quality._EXTERNAL_DOMAIN_PATTERNS],
        "fact_terms": [token for token, _pattern in delivery_quality._EXTERNAL_FACT_PATTERNS],
        "procedure_terms": [
            *(
                token
                for token, _pattern in delivery_quality._EXTERNAL_PROCEDURE_PATTERNS
            ),
            delivery_quality._EXTERNAL_ARTIFACT_PREPARE_TOKEN,
        ],
    }
    assert runtime == {
        "domain_terms": external["domain_terms"],
        "fact_terms": external["fact_terms"],
        "procedure_terms": external["procedure_terms"],
    }


def test_glossary_concepts_explanations_and_owner_map_match_runtime():
    from sajugen.content import report_context

    contract = _tone_contract()
    assert list(report_context.GLOSSARY_EXPLANATIONS) == contract["glossary_concepts"]
    assert report_context.GLOSSARY_EXPLANATIONS == contract["glossary_explanations"]
    assert report_context.GLOSSARY_OWNER_BY_CONCEPT == contract["glossary_owner_by_concept"]


def test_glossary_concepts_and_easy_explanations_match_report_context_bidirectionally():
    contract = _tone_contract()
    documented_concepts = contract["glossary_concepts"]
    documented_explanations = contract["glossary_explanations"]

    assert documented_concepts == list(documented_explanations)
    assert documented_explanations == report_context.GLOSSARY_EXPLANATIONS
