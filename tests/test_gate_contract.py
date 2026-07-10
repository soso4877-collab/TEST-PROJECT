# -*- coding: utf-8 -*-
"""Phase 1(2026-07-06) — 게이트 키 SSOT + 요약↔원천 정합 계약 (C4 관측 갭 자동화).

배경(실결함): verify.gate_pass AND-체인에 layout_geometry_clean(+text_layer_ok·
fonts_embedded·tagged)이 있는데 scripts/hsummary._PDF_GATE·scripts/hrun._retry_reason
에는 없어, 그 키 단독 실패 시 summary 에서 이유 불명(pdf_gate_failed)·필드 드롭.
이 파일은 (a) 그 갭을 RED 로 고정하고 (b) GATE_KEYS SSOT 파생으로 닫는다.

PII 0(합성 dict 만). *_clean·*_hits_count 는 bool/int 라 PII-safe, *_hits(문구)는
curated _summarize_hits 경로 유지 — 원문 노출 금지(가드 테스트로 고정).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hrun  # noqa: E402
import hsummary  # noqa: E402

# 20키 동결 앵커(verify.py gate_pass AND-체인 630-649 순서 그대로). GATE_KEYS 도입 후
# 이 튜플과 verify.GATE_KEYS 가 정확히 일치(멤버십+순서)함을 test_gate_keys_frozen 이 고정.
_EXPECTED_GATE_KEYS = (
    "text_layer_ok",
    "fonts_embedded",
    "tagged",
    "markdown_clean",
    "daewoon_consistent",
    "quality_clean",
    "temporal_clean",
    "no_orphan",
    "loanword_clean",
    "raw_calc_head_clean",
    "customer_meta_clean",
    "placeholder_residue_clean",
    "style_clean",
    "role_perspective_clean",
    "honorific_consistency_clean",
    "name_policy_clean",
    "identity_role_clean",
    "singang_role_clean",
    "delivery_quality_clean",
    "layout_geometry_clean",
)


def _synthetic_verified(**overrides) -> dict:
    """전 게이트 통과 합성 verify 결과 + overrides 로 특정 키만 결함 주입."""
    r = {k: True for k in _EXPECTED_GATE_KEYS}
    r.update({"type": "personal", "pdf": "x.pdf", "status": "verified"})
    r.update(overrides)
    r["gate_pass"] = all(r[k] for k in _EXPECTED_GATE_KEYS)
    return r


def test_layout_geometry_failure_surfaces_in_summary():
    # RED(수정 전): layout_geometry_clean 이 _redact_pdf 화이트리스트에서 드롭 → 이유 불명.
    r = _synthetic_verified(layout_geometry_clean=False)
    out = hsummary._redact_pdf(r)
    assert out["gate_pass"] is False
    assert "layout_geometry_clean" in out, "기하 실패가 summary 에서 관측돼야 한다(C4)"
    assert out["layout_geometry_clean"] is False


def test_layout_geometry_failure_gives_specific_retry_reason():
    # RED(수정 전): _retry_reason 하드코딩 목록에 layout_geometry_clean 부재 → pdf_gate_failed.
    r = _synthetic_verified(layout_geometry_clean=False)
    assert hrun._retry_reason(r) == "layout_geometry_clean"


def test_structural_key_failure_surfaces_and_reasons():
    # 사각 인접: text_layer_ok/fonts_embedded/tagged 도 동일 드롭 갭(단독 실패 시).
    for key in ("text_layer_ok", "fonts_embedded", "tagged"):
        r = _synthetic_verified(**{key: False})
        out = hsummary._redact_pdf(r)
        assert key in out and out[key] is False, key
        assert hrun._retry_reason(r) == key, key


def test_gate_keys_frozen():
    # 20키 동결(멤버십+순서). verify.GATE_KEYS 변경 = 게이트 의미 변경 → 별도 결정·양방 필수.
    # 이 테스트가 RED 면 순수 리팩터가 아니라 게이트 집합이 바뀐 것(의도했는지 확인).
    from sajugen.render import verify

    assert verify.GATE_KEYS == _EXPECTED_GATE_KEYS
    assert len(verify.GATE_KEYS) == 20
    assert len(set(verify.GATE_KEYS)) == 20  # 중복 없음


def test_gate_pass_is_pure_all_of_gate_keys():
    # 순수 리팩터 증명: gate_pass = all(GATE_KEYS). 전부 참=True, 하나라도 거짓=False.
    from sajugen.render import verify

    r_pass = _synthetic_verified()
    assert r_pass["gate_pass"] is True
    for key in verify.GATE_KEYS:
        r = _synthetic_verified(**{key: False})
        assert r["gate_pass"] is False, key


def test_summary_superset_of_gate_keys():
    # 요약 ⊇ GATE_KEYS: 모든 게이트 키가 redact 요약에 표면화(수동 목록 드롭 방지).
    from sajugen.render import verify

    out = hsummary._redact_pdf(_synthetic_verified())
    for key in verify.GATE_KEYS:
        assert key in out, key
    assert "gate_pass" in out


def test_every_gate_key_yields_its_own_retry_reason():
    # 키별 계약: GATE_KEYS 각각 단독 False → _retry_reason 이 그 키를 정확히 반환.
    from sajugen.render import verify

    for key in verify.GATE_KEYS:
        r = _synthetic_verified(**{key: False})
        assert hrun._retry_reason(r) == key, key


def test_redact_surfaces_unknown_clean_and_count_fields():
    # 일반 계약(미래 관측 필드 자동 표면화): 목록에 없던 *_clean(bool)·*_hits_count(int) 도
    # redact 출력에 존재해야 한다(수동 화이트리스트가 곧 다음 드롭 원천 — C4 재발 차단).
    r = _synthetic_verified(future_lens_clean=False, novel_defect_hits_count=7)
    out = hsummary._redact_pdf(r)
    assert out.get("future_lens_clean") is False
    assert out.get("novel_defect_hits_count") == 7


def test_redact_never_leaks_hits_text_or_nonbool_clean():
    # PII 가드(관측 확대 ↔ PII-0 동반): suffix 확장이 문구 보유 *_hits 필드나 문자열형
    # *_clean 을 원문 노출하면 안 된다. *_hits 는 curated _summarize_hits 경로만.
    pii = "김민준 1997-10-27"
    r = _synthetic_verified(
        exotic_hits=[pii],  # 비-curated *_hits(문구) — suffix 확장 대상 아님
        weird_clean=pii,  # 문자열형 _clean — isinstance(bool/int) 가드로 제외
    )
    import json as _json

    dumped = _json.dumps(hsummary._redact_pdf(r), ensure_ascii=False)
    assert pii not in dumped, "비-curated *_hits/문자열 _clean 원문이 요약에 새면 안 된다"
    assert "exotic_hits" not in dumped
    assert "weird_clean" not in dumped
