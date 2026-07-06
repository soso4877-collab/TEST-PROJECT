# -*- coding: utf-8 -*-
"""T3.3(B-1+G-5) 최종 발급 게이트 완전화 회귀.

final_render_fn 이:
  (a) safe/fact 재검증 벨트로 위반 본문의 발급을 렌더 전에 차단하고,
  (b) verify 에 이름·일간 스펙(names/identity)·ref_year/ref_date 를 복원 전달(그동안 no-op)하며,
  (c) verify 게이트 미통과 시 예외로 발급을 막는지 검증한다.

렌더/verify/엔진은 대체(Playwright·엔진 무실행) — 배선과 벨트만 결정론 검증.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import order_flow  # noqa: E402
from sajugen.content.sections_schema import GuardReport, Report23, Section  # noqa: E402
from sajugen.models.report import (  # noqa: E402
    BirthInput,
    CalendarVerification,
    UnifiedReport,
)

_ALLOW = {
    "ganzhi": ["庚午"],
    "ganzhi_ko": ["경오"],
    "ziwei_majors_in_chart": [],
    "all_star_ko": [],
}


def _report(final_text: str) -> UnifiedReport:
    r23 = Report23(
        sections=[
            Section(
                id="intro",
                title="t",
                source_keys=["myeongni"],
                rule_text="룰 골격",
                final_text=final_text,
                polished=True,
            )
        ],
        guard=GuardReport(
            safe_lint_total=0,
            factcheck_total=0,
            grounding_ok=True,
            polished_sections=1,
            fallback_sections=0,
            clean=True,
        ),
        allow_tokens=_ALLOW,
    )
    return UnifiedReport(
        order_id="ord_t33",
        birth=BirthInput(gender="M", input_date="1990-05-20", birth_time="14:30"),
        calendar_verification=CalendarVerification(solar_date="1990-05-20"),
        content=r23.model_dump(),
        render_meta={
            "input_civil": "1990-05-20 14:30",
            "gen_params": {
                "year": 1990,
                "month": 5,
                "day": 20,
                "hour": 14,
                "minute": 30,
                "is_male": True,
                "name": "홍길동",
                "product": "integrated",
                "brand": "default",
                "horoscope": "2026-06-01",
                "unknown_time": False,
            },
        },
    )


def _patch_render(monkeypatch, capture: dict, *, gate_pass: bool = True) -> None:
    # 엔진: personal_identity_spec 이 saju.myeongni.day_master 만 읽으므로 최소 fake.
    monkeypatch.setattr(
        order_flow.engine,
        "build",
        lambda *a, **k: SimpleNamespace(myeongni=SimpleNamespace(day_master="庚")),
    )
    monkeypatch.setattr(order_flow.render_pdf, "render_pdf", lambda *a, **k: "final_ord_t33.pdf")

    def _fake_verify(_path, **kw):
        capture.update(kw)
        return {
            "gate_pass": gate_pass,
            "text_chars": 1000,
            "tagged": True,
            "fonts_embedded": True,
            "name_policy_clean": True,
            "identity_role_clean": True,
        }

    monkeypatch.setattr(order_flow.render_verify, "verify", _fake_verify)


def test_final_gate_restores_name_identity_specs(monkeypatch):
    # no-op 해소: draft 와 동일하게 identity 3-튜플·names·ref_year/ref_date 가 verify 로 전달.
    cap: dict = {}
    _patch_render(monkeypatch, cap)
    path = order_flow.final_render_fn(_report("순한 흐름이 이어지는 해입니다."))
    assert path == "final_ord_t33.pdf"
    assert cap["names"] == ["홍길동"]
    assert cap["identity"] is not None and len(cap["identity"]) == 3
    assert cap["ref_year"] == 2026
    assert cap["ref_date"] == "2026-06-01"


def test_final_gate_belt_blocks_safe_violation(monkeypatch):
    # 안전(§12) 위반 본문 → 렌더 전에 벨트가 차단(verify 미도달).
    cap: dict = {}
    _patch_render(monkeypatch, cap)
    with pytest.raises(RuntimeError) as e:
        order_flow.final_render_fn(_report("100% 적중합니다. 100% 적중합니다."))
    assert "safe_lint" in str(e.value)
    assert cap == {}  # 렌더/verify 도달 전 차단


def test_final_gate_belt_blocks_fact_violation(monkeypatch):
    # 사실(factcheck) 위반(allow_tokens 밖 간지) → 벨트 차단.
    cap: dict = {}
    _patch_render(monkeypatch, cap)
    with pytest.raises(RuntimeError) as e:
        order_flow.final_render_fn(_report("당신의 일주는 무술(戊戌)입니다."))
    assert "factcheck" in str(e.value)
    assert cap == {}


def test_final_gate_belt_message_is_pii_free(monkeypatch):
    # 벨트 예외 메시지는 카운트만 — 위반 본문 조각(match) 미노출.
    cap: dict = {}
    _patch_render(monkeypatch, cap)
    with pytest.raises(RuntimeError) as e:
        order_flow.final_render_fn(_report("당신의 일주는 무술(戊戌)입니다."))
    msg = str(e.value)
    assert "무술" not in msg and "戊戌" not in msg and "일주" not in msg


def test_final_gate_blocks_when_verify_fails(monkeypatch):
    # verify 게이트 미통과 → 예외(발급 차단, 절대규칙 16 비우회).
    cap: dict = {}
    _patch_render(monkeypatch, cap, gate_pass=False)
    with pytest.raises(RuntimeError) as e:
        order_flow.final_render_fn(_report("순한 흐름이 이어지는 해입니다."))
    assert "게이트 실패" in str(e.value)
