# -*- coding: utf-8 -*-
"""Phase 3(2026-07-06, 보너스) — lint 속성 테스트(hypothesis).

임의 한글/유니코드 입력에 대해 전 text-호환 lint 가 (1) 크래시하지 않고 (2) 결정론적임
(같은 입력=같은 출력)을 property 로 고정한다. lint 는 룰·LLM·관리자 수정분 전수에 적용되므로
크래시·비결정은 파이프라인 전체를 흔든다. max_examples 제한(무크래시가 핵심, 결정론은 저비용).
"""

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import (  # noqa: E402
    client_tone_lint as ct,
    customer_meta_lint,
    delivery_quality as dq,
    quality_lint,
    safe_lint,
    style_lint,
    temporal_lint,
)

# text 호환 lint(고정 인자 어댑터 포함). specs 기반(name_policy/identity/singang 등)은 런타임
# specs 필요라 제외(build 가드 테스트가 커버 — test_skeleton_lint_matrix 완전성 분류와 일치).
_LINTS = {
    "safe": lambda t: safe_lint.lint(t),
    "style": lambda t: style_lint.lint(t),
    "customer_meta": lambda t: customer_meta_lint.lint(t),
    "quality": lambda t: quality_lint.lint(t),
    "temporal": lambda t: temporal_lint.lint(t, 2026),
    "temporal_dated": lambda t: temporal_lint.lint(t, 2026, ref_date="2026-07-06"),
    "loanword": lambda t: ct.loanword_lint(t),
    "raw_calc": lambda t: ct.raw_calc_lint(t),
    "raw_calc_head": lambda t: ct.raw_calc_headwords(t),
    "placeholder": lambda t: ct.placeholder_residue_lint(t),
    "guarantee": lambda t: dq.guarantee_lint(t),
}

# 한글 음절 위주 + 임의 유니코드 혼합(경계·조사·특수문자 엣지 노출).
_korean = st.text(alphabet=st.characters(min_codepoint=0xAC00, max_codepoint=0xD7A3), max_size=120)
_mixed = st.text(max_size=120)
_text = st.one_of(_korean, _mixed, st.builds(lambda a, b: a + b, _korean, _mixed))


@settings(max_examples=200, deadline=None)
@given(text=_text)
def test_all_text_lints_no_crash_and_deterministic(text):
    for name, fn in _LINTS.items():
        try:
            a = fn(text)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(
                f"{name} lint 가 입력 {text!r} 에서 크래시: {type(e).__name__}: {e}"
            )
        b = fn(text)
        assert a == b, f"{name} lint 비결정(같은 입력 다른 출력): {text!r}"
        assert isinstance(a, list), f"{name} lint 반환이 list 아님: {type(a)}"
