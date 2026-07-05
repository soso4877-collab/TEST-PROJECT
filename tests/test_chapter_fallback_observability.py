# -*- coding: utf-8 -*-
"""P0(2026-07-05) 챕터별 윤문/폴백 관측 배선 — QI-2026-07-05-03 재발 구조 차단.

배경: v7 발송 후보에서 consult 챕터가 골격으로 폴백(-61%)됐는데 GuardReport 가
카운트만 보고해 발송 리포트에 "전 챕터 LLM 재작성"으로 오기재됐다(관측 갭).
이 스위트는 (a) builder 의 id 수집, (b) CLI stdout 줄, (c) hrun 파싱,
(d) hsummary 화이트리스트를 양방으로 고정한다. PII 0(합성 입력만).
"""

import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, llm_polish, llm_sections  # noqa: E402
from sajugen.content.question_router import QuestionCategory  # noqa: E402


def _saju():
    return engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")


def test_guard_reports_fallback_ids_when_guard_fails(monkeypatch):
    # 가드에 걸리는 후보를 내는 스텁 → 해당 챕터 id 가 fallback 목록에 잡힌다.
    class _Stub:
        name = "anthropic"

        def classify(self, concern):
            return QuestionCategory.WEALTH

        def compose(self, *, base_text, section_id, **kw):
            if section_id == "consult":
                return base_text + " 반드시 성공합니다."  # §12 위반 → 폴백 유도
            return base_text + " 흐름을 차분히 살피면 좋습니다."

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _Stub())
    monkeypatch.setattr(llm_polish, "polish", lambda text, title, **kw: text)
    r = builder.build_report(
        _saju(), use_llm=True, ref_year=2026, name="테스트", concern="합성 재물 고민입니다."
    )
    g = r.guard
    assert "consult" in g.fallback_section_ids
    assert "consult" not in g.polished_section_ids
    # 카운트와 id 목록 정합
    assert len(g.fallback_section_ids) == g.fallback_sections
    assert len(g.polished_section_ids) == g.polished_sections
    # 섹션 plished 플래그와도 정합
    assert r.section("consult").polished is False


def test_guard_ids_empty_without_llm(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = builder.build_report(_saju(), use_llm=False, ref_year=2026, name="테스트")
    assert r.guard.polished_section_ids == []
    assert r.guard.fallback_section_ids == []


def test_hrun_parses_fallback_chapters_line(monkeypatch):
    # hrun 이 cli 의 chapters 줄을 파싱해 regen_fallback_chapters 로 올린다(양방).
    import hrun

    def _run_with(stdout):
        monkeypatch.setattr(
            hrun.subprocess,
            "run",
            lambda cmd, **kw: types.SimpleNamespace(returncode=0, stdout=stdout, stderr=""),
        )
        profile = {
            "type": "personal",
            "pdf": "sajugen/render/out/__nonexistent__.pdf",
            "birth": "1990-01-01 10:00",
            "name": "합성갑",
            "ref_year": 2026,
        }
        return hrun._regen_pdf(profile, "python")

    r = _run_with("PDF: x.pdf\nchapters: polished=intro,wonguk fallback=consult,frame\n")
    assert r["fallback_chapters"] == ["consult", "frame"]
    r2 = _run_with("PDF: x.pdf\nchapters: polished=intro fallback=-\n")
    assert r2["fallback_chapters"] == []
    r3 = _run_with("PDF: x.pdf\n")  # 구 빌드(줄 없음) = None
    assert r3["fallback_chapters"] is None


def test_hsummary_whitelists_fallback_chapters():
    import hsummary

    p = {
        "type": "personal",
        "pdf": "x.pdf",
        "status": "verified",
        "regen": "done",
        "regen_fallback_chapters": ["consult"],
    }
    out = hsummary._redact_pdf(p)
    assert out["regen_fallback_chapters"] == ["consult"]
    out2 = hsummary._redact_pdf({"type": "personal", "pdf": "y.pdf", "status": "verified"})
    assert "regen_fallback_chapters" not in out2
