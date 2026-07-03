# -*- coding: utf-8 -*-
"""T5.3/B-6·B-7: content.json 스키마에 재현성/이력 메타(ref_date·premium·model·layout_variant)
추가 + 읽기 측 하위호환 기본값(구 파일에 필드 없어도 로드)."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import integrated  # noqa: E402


def _result():
    return {
        "receiver": "DOC_A",
        "people": [{"name": "DOC_A"}, {"name": "DOC_B"}],
        "role_perspective": [{"given": "DOC_A"}],
        "identity": ({"임"}, {"임수"}, [(["DOC_A"], "임수")]),
        "singang": [],
        "sections": [SimpleNamespace(id="s1", title="t", source_keys=["m"], final_text="본문")],
    }


def test_save_writes_provenance_meta(tmp_path):
    path = integrated._save_integrated_content(
        _result(),
        situation="ctx",
        ref_year=2026,
        brand="seodam",
        out_name="x.pdf",
        out_dir=tmp_path,
        ref_date="2026-06-13",
        premium=True,
        model="claude-sonnet-4-6",
        layout_variant={"body_font_size": "14.5pt", "body_line_height": 1.8},
    )
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["ref_date"] == "2026-06-13"
    assert data["premium"] is True
    assert data["model"] == "claude-sonnet-4-6"
    assert data["layout_variant"]["body_font_size"] == "14.5pt"


def test_save_defaults_when_meta_omitted(tmp_path):
    path = integrated._save_integrated_content(
        _result(),
        situation="ctx",
        ref_year=2026,
        brand="seodam",
        out_name="y.pdf",
        out_dir=tmp_path,
    )
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["ref_date"] == "2026-06-13"  # ref_year 파생 기본
    assert data["premium"] is True
    assert data["model"] == "rule"  # 무LLM 기본
    assert data["layout_variant"] is None


def test_read_backcompat_old_bundle(tmp_path, monkeypatch):
    # 구 content.json(메타 필드 없음) → render_integrated_from_content 하위호환 기본값.
    old = {
        "product": "integrated_full",
        "receiver": "DOC_A",
        "names": ["DOC_A", "DOC_B"],
        "ref_year": 2026,
        "situation": "",
        "brand": "seodam",
        "role_perspective": [{"given": "DOC_A"}],
        "identity": [["임"], ["임수"], [[["DOC_A"], "임수"]]],
        "singang": [],
        "sections": [{"id": "s1", "title": "t", "source_keys": ["m"], "final_text": "본문"}],
    }
    p = tmp_path / "old.content.json"
    p.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        integrated,
        "_render_integrated",
        lambda *a, **k: ("fake.pdf", {"gate_pass": True}, [{"gate_pass": True}]),
    )
    out = integrated.render_integrated_from_content(p)
    assert out["ref_date"] == "2026-06-13"  # ref_year 파생
    assert out["premium"] is True
    assert out["model"] == "rule"
    assert out["layout_variant"] is None
