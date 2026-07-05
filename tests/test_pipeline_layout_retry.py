# -*- coding: utf-8 -*-
"""개인 경로 저밀도 무과금 재렌더 재시도(2026-07-04, integrated 패턴 이식) 양방 회귀.

배경: 개인(pipeline) 경로엔 integrated 의 _LAYOUT_VARIANTS 재시도가 없어 저밀도 1건에도
재compose(API 과금)가 강제됐다(실측: CUSTOMER_3 윤문 재시도 2회 소모). 재시도는 compose
이후의 레이아웃 변형(폰트 14.5->13.8pt)만 반복하므로 API 0 이며, 저밀도 '단독' 실패에만
발동한다(다른 게이트 실패 = 즉시 반환, 완화 0).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import integrated, pipeline  # noqa: E402


def _fail_low_density_only() -> dict:
    # gate_pass=False 이지만 실패가 premium_low_density_pages 뿐 + 나머지 플래그 clean
    v = {flag: True for flag in integrated._LOW_DENSITY_ONLY_CLEAN_FLAGS}
    v["gate_pass"] = False
    v["text_chars"] = 9000
    v["delivery_quality"] = {"failures": [{"rule": "premium_low_density_pages"}]}
    return v


def _fail_other() -> dict:
    v = _fail_low_density_only()
    v["delivery_quality"] = {"failures": [{"rule": "missing_customer_context"}]}
    return v


def _run(monkeypatch, verify_seq):
    renders = []
    verifies = iter(verify_seq)

    def fake_render(report, saju, out_name, **kw):
        renders.append(kw.get("body_font_size"))
        return "out/fake.pdf"

    monkeypatch.setattr(pipeline.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(pipeline.render_verify, "verify", lambda *a, **k: next(verifies))
    r = pipeline.generate(
        1989,
        1,
        2,
        7,
        40,
        is_male=False,
        horoscope_date="2026-06-01",
        use_llm=False,
        name="테스트",
        out_name="fake.pdf",
    )
    return renders, r


def test_low_density_only_failure_triggers_free_rerender(monkeypatch):
    ok = {"gate_pass": True, "text_chars": 9000, "tagged": True, "fonts_embedded": True}
    renders, r = _run(monkeypatch, [_fail_low_density_only(), ok])
    assert renders == ["14.5pt", "13.8pt"]  # 변형 순서(하한 13.8pt)
    assert r.verify["gate_pass"] is True


def test_other_failure_does_not_retry(monkeypatch):
    renders, r = _run(monkeypatch, [_fail_other()])
    assert renders == ["14.5pt"]  # 저밀도 단독이 아니면 재시도 없음(우회 금지)
    assert r.verify["gate_pass"] is False


def test_low_density_at_floor_reports_fail(monkeypatch):
    # 13.8pt 하한도 실패 = 그대로 FAIL 보고(열화 발급·완화 없음)
    renders, r = _run(monkeypatch, [_fail_low_density_only(), _fail_low_density_only()])
    assert renders == ["14.5pt", "13.8pt"]
    assert r.verify["gate_pass"] is False


# ---- P6(2026-07-05): 조판 부류(orphan 스필) 무과금 재렌더 확대 양방 ----


def _clean_flags(**overrides):
    from sajugen import integrated as itg

    base = {f: True for f in itg._LOW_DENSITY_ONLY_CLEAN_FLAGS}
    base["delivery_quality"] = {"failures": []}
    base["gate_pass"] = False
    base.update(overrides)
    return base


def test_layout_only_failure_two_way():
    from sajugen import integrated as itg

    # orphan 단독 실패(v8 실측: 13자 스필 1쪽) = 재렌더 대상
    assert itg._layout_only_failure(_clean_flags(no_orphan=False)) is True
    # 저밀도 dq 단독 = 재렌더 대상(기존 동작 포함)
    assert itg._layout_only_failure(
        _clean_flags(delivery_quality={"failures": [{"rule": "premium_low_density_pages"}]})
    ) is True
    # 저밀도+orphan 동시 = 재렌더 대상
    assert itg._layout_only_failure(
        _clean_flags(
            no_orphan=False,
            delivery_quality={"failures": [{"rule": "premium_low_density_pages"}]},
        )
    ) is True
    # 내용 결함 동반(예: 시맨틱 스타일) = 재렌더 아님(하드 실패 유지 — 완화 0)
    assert itg._layout_only_failure(_clean_flags(no_orphan=False, style_clean=False)) is False
    # 다른 dq 실패 동반 = 재렌더 아님
    assert itg._layout_only_failure(
        _clean_flags(delivery_quality={"failures": [{"rule": "missing_near_term_timing"}]})
    ) is False
    # 조판 실패 자체가 없으면(다른 원인 gate FAIL) 재렌더 아님
    assert itg._layout_only_failure(_clean_flags()) is False
