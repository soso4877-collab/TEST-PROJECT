# -*- coding: utf-8 -*-
"""검증 하네스 자체 테스트 — 안전 동작 고정.

- no-regen 기본값에서 cli/gunghap(재생성) 미호출.
- 재생성/LLM 3중 잠금(--regen + --allow-llm + env) 전부일 때만 허용.
- missing PDF 시 재생성 안 하고 missing_pdf 보고.
- local 프로파일이 gitignore 대상.
- summary 리포트 생성.
- synthetic 렌더본으로 hverify_pdf 가 verify 를 호출(결과 게이트 필드 존재).
- secrets scan 이 값 출력 없이 redacted/count 만.
"""

import subprocess
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hpreflight  # noqa: E402
import hrun  # noqa: E402
import hverify_pdf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIX_P = "harness/profiles/fixtures/personal_synthetic.yml"


def _args(**kw):
    base = dict(regen=False, allow_llm=False, no_tests=True, stamp="pytest-harness", profile=[])
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_regen_triple_lock(monkeypatch):
    monkeypatch.delenv("SAJUGEN_HARNESS_ALLOW_REGEN", raising=False)
    assert hrun._regen_allowed(_args(regen=False, allow_llm=False)) is False
    assert hrun._regen_allowed(_args(regen=True, allow_llm=False)) is False
    assert hrun._regen_allowed(_args(regen=True, allow_llm=True)) is False  # env 없음
    monkeypatch.setenv("SAJUGEN_HARNESS_ALLOW_REGEN", "1")
    assert hrun._regen_allowed(_args(regen=True, allow_llm=True)) is True
    assert hrun._regen_allowed(_args(regen=False, allow_llm=True)) is False  # 플래그 없음


def test_no_regen_does_not_call_cli(monkeypatch):
    monkeypatch.delenv("SAJUGEN_HARNESS_ALLOW_REGEN", raising=False)
    called = []
    monkeypatch.setattr(hrun, "_regen_pdf", lambda *a, **k: called.append(1))
    s = hrun.run([FIX_P], _args())  # regen False, no_tests True
    assert called == []  # 재생성 함수 호출 0
    assert s["regen_allowed"] is False
    assert s["pdfs"][0]["regen"].startswith("skipped")


def test_missing_pdf_no_regen():
    # 합성 픽스처 pdf 경로는 존재하지 않음 → 재생성하지 말고 missing_pdf
    r = hverify_pdf.verify_profile(hverify_pdf.load_profile(FIX_P))
    assert r["status"] == "missing_pdf"
    assert r["gate_pass"] is False


def test_local_profile_gitignored():
    r = subprocess.run(
        ["git", "check-ignore", "harness/profiles/local/x.yml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0  # ignored
    r2 = subprocess.run(
        ["git", "check-ignore", "harness/profiles/personal.example.yml"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 1  # example 은 커밋 가능


def test_summary_written(monkeypatch):
    monkeypatch.delenv("SAJUGEN_HARNESS_ALLOW_REGEN", raising=False)
    s = hrun.run([FIX_P], _args(stamp="pytest-harness-summary"))
    assert Path(s["report"]["json"]).is_file()
    assert Path(s["report"]["md"]).is_file()
    assert "PII" in Path(s["report"]["md"]).read_text(encoding="utf-8")


def test_hverify_calls_verify_on_rendered_pdf(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from sajugen import config as cfg
    from sajugen.render import pdf as render_pdf

    body = "태수 씨는 차분한 사람입니다. 흐름을 봅니다. " * 30
    secs = [SimpleNamespace(id="a", title="결", source_keys=["m"], final_text=body)]
    bp = dict(cfg.brand("seodam"))
    path = render_pdf.render_pdf(
        SimpleNamespace(sections=secs),
        SimpleNamespace(input_civil="테스트"),
        "test_harness_render.pdf",
        name="",
        brand=bp,
    )
    prof = {
        "type": "personal",
        "name": "합성갑",
        "gender": "남",
        "birth": "1990-05-20 14:30",
        "horoscope": "2026-06-01",
        "ref_year": 2026,
        "pdf": path,
    }
    r = hverify_pdf.verify_profile(prof, pdf_override=path)
    assert r["status"] == "verified"
    assert "gate_pass" in r and "meta" in r and r["meta"]["sha256"]
    assert "name_policy_hits_count" in r


def test_secret_scan_redacted(monkeypatch):
    fake_key = "sk-ant-FAKEFAKE1234567890abcdef"
    fake_diff = f"+++ b/x.txt\n+ANTHROPIC_API_KEY={fake_key}\n+ normal line\n"
    monkeypatch.setattr(hpreflight, "_git", lambda *a, **k: fake_diff if a[0] == "diff" else "")
    hits = hpreflight._secret_scan()
    assert len(hits) >= 1
    # 값 비노출: 어떤 필드에도 실제 키 문자열이 없어야 함
    for h in hits:
        assert set(h.keys()) <= {"path", "rule", "count", "redacted_preview"}
        assert fake_key not in str(h)
        assert h["redacted_preview"] == "[REDACTED]"
