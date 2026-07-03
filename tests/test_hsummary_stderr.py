# -*- coding: utf-8 -*-
"""T5.2/E-5: hsummary 가 regen_stderr_tail(재생성 실패 진단)을 PII 레닥션 후 화이트리스트에
포함(그동안 드롭되던 관측 갭). 생년월일·시각형 토큰은 [redacted]."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hsummary  # noqa: E402


def test_stderr_tail_included_and_redacted():
    p = {
        "type": "integrated",
        "regen_stderr_tail": "Traceback: bad birth 1989-01-02 07:40 실패 코드 19890102",
    }
    out = hsummary._redact_pdf(p)
    assert "regen_stderr_tail" in out
    tail = out["regen_stderr_tail"]
    assert "1989-01-02" not in tail and "07:40" not in tail and "19890102" not in tail
    assert "[redacted]" in tail


def test_stderr_tail_absent_when_field_missing():
    out = hsummary._redact_pdf({"type": "integrated"})
    assert "regen_stderr_tail" not in out


def test_redact_stderr_tail_helper():
    assert hsummary._redact_stderr_tail(None) is None
    assert hsummary._redact_stderr_tail("") is None
    r = hsummary._redact_stderr_tail("date 2000-01-01 time 14:30 num 20000101 ok")
    assert "2000-01-01" not in r and "14:30" not in r and "20000101" not in r
    assert "ok" in r  # 비-PII 텍스트는 보존
