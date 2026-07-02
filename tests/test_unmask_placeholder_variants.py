# -*- coding: utf-8 -*-
"""회귀: receiver-perspective un-mask 가 placeholder_residue 게이트와 동일한 공백 변형을 모두
덮어야 한다. 과거 _unmask_receiver_placeholders 가 정확 문자열 str.replace 라서 LLM 이 낸 공백
변형("첫번째 분" 등)을 놓치고 게이트(regex)는 잡아 placeholder 누출+게이트 실패가 났다
(2026-06-29 실고객 Tier2 실측: 첫 번째 분 55·두 번째 분 67 누출). 합성 이름만 사용(실고객 PII 없음)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import gunghap  # noqa: E402
from sajugen.content import client_tone_lint  # noqa: E402

NAMES = ["김갑동", "이을순"]  # 합성(synthetic) — 실고객 이름 아님
RECEIVER = "김갑동"

# 게이트 regex(첫\s*번째\s*분 …)가 잡는 공백 변형 전수 — unmask 도 동일하게 치환해야 함
_VARIANTS = [
    "첫 번째 분",
    "첫번째 분",
    "첫 번째분",
    "첫번째분",
    "두 번째 분",
    "두번째분",
    "세 번째 분",
]


def test_unmask_covers_all_lint_whitespace_variants():
    for variant in _VARIANTS:
        text = f"{variant}은 차분히 보고 두번째 분과 속도를 맞춥니다."
        out = gunghap._unmask_receiver_placeholders(text, NAMES, RECEIVER)
        # 핵심 계약: unmask 후 게이트가 잡을 placeholder 가 하나도 남지 않는다.
        assert client_tone_lint.placeholder_residue_clean(out), (variant, out)
        assert "번째" not in out, (variant, out)


def test_unmask_no_residue_for_compact_form():
    out = gunghap._unmask_receiver_placeholders("첫번째분과 두번째분", NAMES, RECEIVER)
    assert client_tone_lint.placeholder_residue_clean(out), out
    assert "번째" not in out, out
