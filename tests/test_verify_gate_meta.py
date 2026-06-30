# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hsemantic_review  # noqa: E402
from sajugen.render import verify as verify_pdf  # noqa: E402


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def get_text(self):
        return self._text

    def get_fonts(self, full=True):
        return [(0, "ttf", "Type0", "EmbeddedSubset", "F1")]


class _FakeDoc:
    def __init__(self, pages: list[str]):
        self._pages = pages
        self.page_count = len(pages)

    def load_page(self, index: int):
        return _FakePage(self._pages[index])

    def get_toc(self):
        return []

    def pdf_catalog(self):
        return 1

    def xref_object(self, _xref):
        return "<< /StructTreeRoot 1 0 R /MarkInfo << /Marked true >> >>"

    def close(self):
        return None


_CLEAN_SENTENCE = (
    "이 사람은 생활의 속도를 고르게 잡고, 말과 행동을 맞추며 안정적으로 이어 갑니다. "
    "서두르지 않고 확인할수록 선택이 차분해집니다. "
)


def _verify_text(monkeypatch, body: str) -> dict:
    pages = ["표지", body, body]
    monkeypatch.setattr(verify_pdf.fitz, "open", lambda _path: _FakeDoc(pages))
    monkeypatch.setattr(
        verify_pdf,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )
    return verify_pdf.verify("synthetic.pdf")


def test_hand_edited_semantic_leak_fails_gate(monkeypatch):
    leak = (
        "이 글은 통합 풀이입니다. "
        "일반론이 아니라 실제 글자 하나하나를 먼저 이어서 살펴보겠습니다. "
        "첫 번째 분에게 고객님이라고 적힌 자리가 남았습니다. "
        "또렷합니다. "
    )
    result = _verify_text(monkeypatch, leak + (_CLEAN_SENTENCE * 20))

    assert result["gate_pass"] is False
    assert result["customer_meta_clean"] is False
    assert result["placeholder_residue_clean"] is False
    assert result["style_clean"] is False
    assert result["ai_meta_hits"]
    assert result["placeholder_residue_hits"]
    assert result["semantic_style_hits"]


def test_normal_customer_copy_keeps_new_gates_clean(monkeypatch):
    result = _verify_text(monkeypatch, _CLEAN_SENTENCE * 24)
    assert result["customer_meta_clean"] is True, result["ai_meta_hits"]
    assert result["placeholder_residue_clean"] is True, result["placeholder_residue_hits"]
    assert result["style_clean"] is True, result["semantic_style_hits"]
    assert result["gate_pass"] is True, result


def test_toc_customer_framing_is_not_body_quality_failure(monkeypatch):
    body = _CLEAN_SENTENCE * 24
    pages = [
        "표지",
        "목차\n이 풀이는 큰 그림에서 현실 적용 순서로 이어집니다.",
        body,
        body,
    ]
    monkeypatch.setattr(verify_pdf.fitz, "open", lambda _path: _FakeDoc(pages))
    monkeypatch.setattr(
        verify_pdf,
        "_verapdf_ua1",
        lambda _path: {"available": False, "note": "test"},
    )

    result = verify_pdf.verify("synthetic.pdf")

    assert result["quality_clean"] is True, result["quality_hits"]
    assert result["gate_pass"] is True, result


def test_hsemantic_review_never_outputs_ready():
    result = hsemantic_review.review_text(_CLEAN_SENTENCE * 4)
    assert result["semantic_review_status"] == "REVIEW_REQUIRED"
    assert result["operator_full_text_reading_required"] is True
    assert result["release_allowed"] is False
    assert "READY" not in str(result)


def test_verify_semantic_hits_are_pii_free(monkeypatch):
    result = _verify_text(monkeypatch, "이 글은 통합 풀이입니다. 고객님. " + (_CLEAN_SENTENCE * 24))
    hit_payload = {
        "ai_meta_hits": result["ai_meta_hits"],
        "placeholder_residue_hits": result["placeholder_residue_hits"],
        "semantic_style_hits": result["semantic_style_hits"],
    }
    assert "match" not in str(hit_payload)
    assert "이 글은" not in str(hit_payload)
    assert "고객님" not in str(hit_payload)
