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
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hpreflight  # noqa: E402
import hrun  # noqa: E402
import hstate  # noqa: E402
import hverify_pdf  # noqa: E402
from playwright_guard import require_playwright_subprocess  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIX_P = "harness/profiles/fixtures/personal_synthetic.yml"


def _args(**kw):
    base = dict(regen=False, allow_llm=False, no_tests=True, stamp="pytest-harness", profile=[])
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_profile_concern_normalizes_situation():
    # P1: integrated/궁합 프로파일은 고민을 situation 으로 담는다 → concern 정규화(질문축 no-op 차단).
    assert hrun._profile_concern({"concern": "직접 concern"}) == "직접 concern"
    assert hrun._profile_concern({"situation": "상황 고민"}) == "상황 고민"
    assert hrun._profile_concern({"concern": "", "situation": "상황"}) == "상황"
    assert hrun._profile_concern({"concern": None, "situation": "상황"}) == "상황"
    assert hrun._profile_concern({}) is None


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
    assert s["retry_blocked"] is True
    assert s["current_stage"] == "COMPLETE"
    assert isinstance(s["input_sha"], str) and len(s["input_sha"]) == 12
    assert isinstance(s["output_sha"], str) and len(s["output_sha"]) == 12
    assert s["api_calls"] == 0
    assert s["pdf_rendered"] is False
    assert s["final_status"] == "BLOCKED"
    run_state = json.loads(Path(s["report"]["run_state"]).read_text(encoding="utf-8"))
    assert run_state["retry_blocked"] is True
    assert run_state["final_status"] == "BLOCKED"


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
    assert Path(s["report"]["run_state"]).is_file()
    assert "PII" in Path(s["report"]["md"]).read_text(encoding="utf-8")
    archived = json.loads(Path(s["report"]["json"]).read_text(encoding="utf-8"))
    assert archived["report"]["run_state"]["path"] == s["report"]["run_state"]
    assert len(archived["report"]["run_state"]["sha12"]) == 12
    assert "run_state" not in archived


def test_retry_blocked_after_failed_regen_blocks_later_regen(monkeypatch):
    monkeypatch.setenv("SAJUGEN_HARNESS_ALLOW_REGEN", "1")
    regen_calls = []

    def fake_regen(profile, python):
        regen_calls.append(profile["type"])
        return {"returncode": 1}

    monkeypatch.setattr(hrun, "_regen_pdf", fake_regen)
    s = hrun.run([FIX_P, FIX_P], _args(regen=True, allow_llm=True, stamp="pytest-retry-block"))
    assert regen_calls == ["personal"]
    assert s["retry_blocked"] is True
    assert "pdf_regen_failed" in s["retry_reasons"]
    assert s["pdfs"][0]["retry_blocked"] is True
    assert s["pdfs"][1]["regen"] == "blocked_after_failure"
    assert s["pdf_rendered"] is False
    assert s["api_calls"] == 0
    assert s["final_status"] == "BLOCKED"


def test_summary_redacts_pdf_name_and_hit_text():
    summary = hrun.hsummary.build_summary(
        {"branch": "x", "preflight_ok": True},
        {"returncode": 0, "passed": 1},
        [
            {
                "type": "gunghap",
                "pdf": "sajugen/render/out/real_name_19900101.pdf",
                "status": "verified",
                "gate_pass": False,
                "meta": {"sha256": "abc", "pages": 1, "size": 10},
                "quality_hits": [{"type": "internal_meta_label", "match": "고객 질문: 실제 원문"}],
                "quality_hits_count": 1,
                "customer_meta_clean": False,
                "placeholder_residue_clean": False,
                "style_clean": False,
                "semantic_style_hits": [
                    {"type": "semantic_style", "rule": "ai_like_repetition", "count": 1, "page": 2}
                ],
                "semantic_style_hits_count": 1,
                "ai_meta_hits": [
                    {"type": "ai_meta", "rule": "document_self_reference", "count": 1, "page": 2}
                ],
                "ai_meta_hits_count": 1,
                "placeholder_residue_hits": [
                    {
                        "type": "placeholder_residue",
                        "rule": "generic_customer_address",
                        "severity": "hard",
                        "count": 1,
                        "page": 2,
                        "match": "고객님",
                    }
                ],
                "placeholder_residue_hits_count": 1,
                "role_perspective_hits": [],
                "role_perspective_hits_count": 0,
                "role_perspective_clean": True,
                "honorific_consistency_clean": False,
                "honorific_consistency_hits": [
                    {
                        "type": "honorific_consistency",
                        "rule": "unexpected_honorific",
                        "role": "receiver",
                        "expected": "님",
                        "actual": "씨",
                        "count": 1,
                        "match": "실제 호칭 원문",
                    }
                ],
                "honorific_consistency_hits_count": 1,
                "semantic_review_status": "FAILED",
                "delivery_quality": {
                    "clean": False,
                    "failures": [
                        {"rule": "missing_question_axes", "axes": ["relationship_intent"]}
                    ],
                    "failure_messages": [
                        {
                            "rule": "missing_question_axes",
                            "message": "질문 축에 대한 답변 근거가 부족합니다.",
                        }
                    ],
                    "warnings": [],
                    "warning_messages": [],
                },
            }
        ],
    )
    pdf = summary["pdfs"][0]
    assert pdf["pdf"] == "[redacted].pdf"
    assert "실제 원문" not in str(pdf)
    assert "고객님" not in str(pdf)
    assert pdf["quality_hits"] == [{"type": "internal_meta_label"}]
    assert pdf["semantic_review_status"] == "FAILED"
    assert pdf["ai_meta_hits"] == [
        {"type": "ai_meta", "rule": "document_self_reference", "page": 2, "count": 1}
    ]
    assert pdf["placeholder_residue_hits"] == [
        {
            "type": "placeholder_residue",
            "rule": "generic_customer_address",
            "page": 2,
            "count": 1,
            "severity": "hard",
        }
    ]
    assert pdf["honorific_consistency_clean"] is False
    assert "실제 호칭 원문" not in str(pdf)
    assert pdf["honorific_consistency_hits"] == [
        {
            "type": "honorific_consistency",
            "rule": "unexpected_honorific",
            "role": "receiver",
            "expected": "님",
            "actual": "씨",
            "count": 1,
        }
    ]


def test_run_state_schema_requires_phase1_fields():
    state = hstate.default_state(current_stage="VERIFY", final_status="REVIEW_REQUIRED")
    assert hstate.validate_run_state(state)["valid"] is True

    invalid = hstate.validate_run_state({"current_stage": "VERIFY"})
    assert invalid["valid"] is False
    for field in (
        "input_sha",
        "output_sha",
        "api_calls",
        "pdf_rendered",
        "retry_blocked",
        "final_status",
    ):
        assert field in invalid["missing"]


def test_hverify_semantic_hits_forwarded_without_render(monkeypatch):
    import fitz
    from sajugen.render import verify as verify_mod

    class FakePage:
        def get_text(self):
            return "synthetic extracted text"

    class FakeDoc:
        page_count = 1

        def load_page(self, index):
            assert index == 0
            return FakePage()

        def close(self):
            return None

    monkeypatch.setattr(hverify_pdf.os.path, "isfile", lambda path: True)
    monkeypatch.setattr(
        hverify_pdf,
        "_build_specs",
        lambda profile: {
            "ref_year": 2026,
            "names": ["DOC_A"],
            "name_full": None,
            "identity": None,
            "singang": None,
        },
    )
    monkeypatch.setattr(
        hverify_pdf,
        "_file_meta",
        lambda path: {"sha256": "0" * 64, "pages": 1, "size": 10, "mtime": "2026-01-01 00:00:00"},
    )
    monkeypatch.setattr(fitz, "open", lambda path: FakeDoc())
    monkeypatch.setattr(verify_mod, "_split_body_appendix", lambda pages: ("", ""))
    monkeypatch.setattr(
        verify_mod,
        "verify",
        lambda *args, **kwargs: {
            "gate_pass": False,
            "customer_meta_clean": False,
            "placeholder_residue_clean": False,
            "style_clean": False,
            "semantic_style_hits": [
                {"type": "semantic_style", "rule": "ai_like_repetition", "count": 1, "page": 1}
            ],
            "ai_meta_hits": [
                {
                    "type": "ai_meta",
                    "rule": "document_self_reference",
                    "count": 1,
                    "page": 1,
                    "match": "raw text must not forward",
                }
            ],
            "placeholder_residue_hits": [
                {
                    "type": "placeholder_residue",
                    "rule": "generic_customer_address",
                    "severity": "hard",
                    "count": 1,
                    "page": 1,
                    "match": "raw text must not forward",
                }
            ],
            "role_perspective_hits": [],
        },
    )

    r = hverify_pdf.verify_profile({"type": "personal", "pdf": "synthetic.pdf"})
    assert r["status"] == "verified"
    assert r["customer_meta_clean"] is False
    assert r["placeholder_residue_clean"] is False
    assert r["style_clean"] is False
    assert r["semantic_style_hits_count"] == 1
    assert r["ai_meta_hits_count"] == 1
    assert r["placeholder_residue_hits_count"] == 1
    assert r["role_perspective_hits_count"] == 0
    assert "match" not in r["ai_meta_hits"][0]
    assert "match" not in r["placeholder_residue_hits"][0]
    forbidden_legacy_key = "placeholder_" + "honorific_hits"
    assert forbidden_legacy_key not in r


def test_integrated_hrun_regen_uses_integrated_module(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(hrun.subprocess, "run", fake_run)
    profile = {
        "type": "integrated_full",
        "pdf": "sajugen/render/out/__nonexistent_synthetic_integrated_full__.pdf",
        "ref_year": 2026,
        "receiver": "합성갑",
        "brand": "sajudoryeong",
        "concern": "합성 관계와 생활 기준을 함께 확인합니다.",
        "people": [
            {"name": "합성갑", "birth": "1990-01-01 10:00", "gender": "남"},
            {"name": "합성을", "birth": "1991-02-02 11:00", "gender": "여"},
        ],
    }

    result = hrun._regen_pdf(profile, "python")
    cmd = calls[0]
    assert result["returncode"] == 0
    assert cmd[:4] == ["python", "-m", "sajugen.integrated", "--llm"]
    assert "--receiver" in cmd and "합성갑" in cmd
    assert "--person" in cmd
    assert "--out" in cmd and "__nonexistent_synthetic_integrated_full__.pdf" in cmd


def test_regen_parses_llm_usage_line_from_stdout(monkeypatch):
    # 사용량 관측 배선(2026-07-05): 빌드 CLI 의 "LLM usage:" 줄이 regen 결과로 파싱되고,
    # 줄이 없으면 None(구 빌드/무LLM — 양방).
    def fake_run(cmd, **kwargs):
        return types.SimpleNamespace(
            returncode=0,
            stdout="PDF: x.pdf (2인)\nLLM usage: calls=7 input_tokens=1200 output_tokens=340\n",
            stderr="",
        )

    monkeypatch.setattr(hrun.subprocess, "run", fake_run)
    profile = {
        "type": "personal",
        "pdf": "sajugen/render/out/__nonexistent__.pdf",
        "birth": "1990-01-01 10:00",
        "name": "합성갑",
        "ref_year": 2026,
    }
    r = hrun._regen_pdf(profile, "python")
    assert r["llm_usage"] == {"calls": 7, "input_tokens": 1200, "output_tokens": 340}

    monkeypatch.setattr(
        hrun.subprocess,
        "run",
        lambda cmd, **kw: types.SimpleNamespace(returncode=0, stdout="PDF: x.pdf\n", stderr=""),
    )
    assert hrun._regen_pdf(profile, "python")["llm_usage"] is None


def test_hsummary_whitelists_regen_usage_and_returncode():
    # summary 화이트리스트 배선 — regen_returncode 는 그동안 드롭돼 성패가 안 보였다
    # (QI-2026-07-05-01 관측 갭의 이웃). PII 0 필드만 추가.
    import hsummary

    p = {
        "type": "gunghap",
        "pdf": "x.pdf",
        "status": "verified",
        "regen": "done",
        "regen_returncode": 0,
        "regen_llm_usage": {"calls": 7, "input_tokens": 1200, "output_tokens": 340},
    }
    out = hsummary._redact_pdf(p)
    assert out["regen_returncode"] == 0
    assert out["regen_llm_usage"] == {"calls": 7, "input_tokens": 1200, "output_tokens": 340}
    # 필드 부재 시 키 미출현(None 오염 방지)
    out2 = hsummary._redact_pdf({"type": "personal", "pdf": "y.pdf", "status": "verified"})
    assert "regen_llm_usage" not in out2 and "regen_returncode" not in out2


def test_failed_regen_is_reported_as_failed_not_done(monkeypatch):
    # 관측 갭(2026-07-05 h153 실측): 재생성 CLI rc!=0 인데 summary 의 regen 이 "done" 으로
    # 표기돼 실패가 가려졌다. 실패한 프로파일 자신은 "failed" 로 드러난다(fail-closed 관측).
    monkeypatch.setenv("SAJUGEN_HARNESS_ALLOW_REGEN", "1")
    monkeypatch.setattr(hrun, "_regen_pdf", lambda profile, python: {"returncode": 1})
    s = hrun.run([FIX_P], _args(regen=True, allow_llm=True, stamp="pytest-regen-failed"))
    assert s["pdfs"][0]["regen"] == "failed"
    assert "pdf_regen_failed" in s["retry_reasons"]


def test_hrun_regen_injects_today_ref_date_when_absent(monkeypatch):
    # Phase 0(2026-07-06, 의도 변경 — 구 동작 '미지정 시 미전달'을 폐기): 운영자 대면
    # regen 은 프로파일 ref_date 부재 시 '오늘'을 명시 주입한다(관측성 — CLI 내부 기본에
    # 맡기지 않고 실행 명령에 날짜 기록). 양방: 명시→전달값 / 부재→오늘(고정값 주입).
    # date.today() 자정 경계 flakiness 회피 위해 헬퍼 monkeypatch(고정값).
    monkeypatch.setattr(hrun, "default_ref_date_iso", lambda: "2026-07-06")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(hrun.subprocess, "run", fake_run)
    base = {
        "pdf": "sajugen/render/out/__nonexistent_synthetic__.pdf",
        "ref_year": 2026,
        "people": [
            {"name": "합성갑", "birth": "1990-01-01 10:00", "gender": "남"},
            {"name": "합성을", "birth": "1991-02-02 11:00", "gender": "여"},
        ],
    }
    for ptype in ("integrated_full", "gunghap"):
        calls.clear()
        hrun._regen_pdf({**base, "type": ptype, "ref_date": "2026-07-05"}, "python")
        cmd = calls[0]
        assert "--ref-date" in cmd and "2026-07-05" in cmd, ptype  # 명시→전달
        calls.clear()
        hrun._regen_pdf({**base, "type": ptype}, "python")
        cmd = calls[0]
        assert "--ref-date" in cmd and "2026-07-06" in cmd, ptype  # 부재→오늘 주입


def test_integrated_cli_gen_forwards_ref_date(monkeypatch):
    # integrated CLI 진입점 배선: --ref-date 가 build_integrated_full 로 전달된다
    # (함수만 배선되고 CLI 가 못 넘기는 팬텀 파라미터 방지, 방법론 A-5).
    from typer.testing import CliRunner

    from sajugen import integrated

    captured = {}

    def fake_build(people, **kwargs):
        captured.update(kwargs)
        return {"pdf_path": "fake.pdf", "people": [{"name": "합성갑"}]}

    monkeypatch.setattr(integrated, "build_integrated_full", fake_build)
    r = CliRunner().invoke(
        integrated.app,
        [
            "gen",
            "--person",
            "합성갑,1990-01-01,10:00,남",
            "--person",
            "합성을,1991-02-02,11:00,여",
            "--ref-date",
            "2026-07-05",
        ],
    )
    assert r.exit_code == 0, r.output
    assert captured["ref_date"] == "2026-07-05"


def test_integrated_cli_gen_defaults_ref_date_to_today_when_absent(monkeypatch):
    # Phase 0: --ref-date 미지정 시 CLI 가 '오늘'을 주입(운영자 기억 의존 제거).
    # 헬퍼 monkeypatch 로 고정값(자정 경계 flakiness 회피).
    from typer.testing import CliRunner

    from sajugen import integrated

    monkeypatch.setattr(integrated, "default_ref_date_iso", lambda: "2026-07-06")
    captured = {}

    def fake_build(people, **kwargs):
        captured.update(kwargs)
        return {"pdf_path": "fake.pdf", "people": [{"name": "합성갑"}]}

    monkeypatch.setattr(integrated, "build_integrated_full", fake_build)
    r = CliRunner().invoke(
        integrated.app,
        ["gen", "--person", "합성갑,1990-01-01,10:00,남", "--person", "합성을,1991-02-02,11:00,여"],
    )
    assert r.exit_code == 0, r.output
    assert captured["ref_date"] == "2026-07-06"  # 미지정→오늘


def test_gunghap_cli_gen_defaults_ref_date_to_today_and_forwards_explicit(monkeypatch):
    # Phase 0 양방: gunghap CLI 도 미지정→오늘 / 명시→전달값.
    from typer.testing import CliRunner

    from sajugen import gunghap

    monkeypatch.setattr(gunghap, "default_ref_date_iso", lambda: "2026-07-06")
    captured = {}

    def fake_build(people_in, **kwargs):
        captured.clear()
        captured.update(kwargs)
        return {"pdf_path": "fake.pdf", "people": [{"name": "합성갑"}, {"name": "합성을"}]}

    monkeypatch.setattr(gunghap, "build_gunghap", fake_build)
    # gunghap.app 은 단일 커맨드(gen 하나) — Typer 가 서브커맨드명을 요구하지 않는다.
    persons = ["--person", "합성갑,1990-01-01,10:00,남", "--person", "합성을,1991-02-02,11:00,여"]
    r1 = CliRunner().invoke(gunghap.app, [*persons])
    assert r1.exit_code == 0, r1.output
    assert captured["ref_date"] == "2026-07-06"  # 미지정→오늘
    r2 = CliRunner().invoke(gunghap.app, [*persons, "--ref-date", "2026-07-05"])
    assert r2.exit_code == 0, r2.output
    assert captured["ref_date"] == "2026-07-05"  # 명시→전달


def test_integrated_hverify_profile_forwards_receiver_specs(monkeypatch):
    import fitz
    from sajugen.render import verify as verify_mod

    captured = {}

    class FakePage:
        def get_text(self):
            return "synthetic extracted text"

    class FakeDoc:
        page_count = 1

        def load_page(self, index):
            assert index == 0
            return FakePage()

        def close(self):
            return None

    monkeypatch.setattr(hverify_pdf.os.path, "isfile", lambda path: True)
    monkeypatch.setattr(
        hverify_pdf,
        "_file_meta",
        lambda path: {"sha256": "0" * 64, "pages": 1, "size": 10, "mtime": "2026-01-01 00:00:00"},
    )
    monkeypatch.setattr(fitz, "open", lambda path: FakeDoc())
    monkeypatch.setattr(verify_mod, "_split_body_appendix", lambda pages: ("", ""))

    def fake_verify(*args, **kwargs):
        captured.update(kwargs)
        return {
            "gate_pass": False,
            "customer_meta_clean": True,
            "placeholder_residue_clean": True,
            "style_clean": True,
            "role_perspective_clean": False,
            "honorific_consistency_clean": False,
            "role_perspective_hits": [
                {
                    "type": "role_perspective",
                    "rule": "receiver_third_person_honorific",
                    "role": "receiver",
                    "expected": "님",
                    "actual": "씨",
                    "count": 1,
                }
            ],
            "honorific_consistency_hits": [
                {
                    "type": "honorific_consistency",
                    "rule": "unexpected_honorific",
                    "role": "receiver",
                    "expected": "님",
                    "actual": "씨",
                    "count": 1,
                }
            ],
            "semantic_style_hits": [],
            "ai_meta_hits": [],
            "placeholder_residue_hits": [],
        }

    monkeypatch.setattr(verify_mod, "verify", fake_verify)
    profile = {
        "type": "integrated_full",
        "product": "integrated_full",
        "pdf": "synthetic.pdf",
        "ref_year": 2026,
        "receiver": "합성갑",
        "people": [
            {"name": "합성갑", "birth": "1990-01-01 10:00", "gender": "남"},
            {"name": "합성을", "birth": "1991-02-02 11:00", "gender": "여"},
        ],
    }

    result = hverify_pdf.verify_profile(profile)
    assert captured["product"] == "integrated_full"
    assert captured["premium"] is True
    assert captured["role_perspective"]
    assert captured["honorific"] == captured["role_perspective"]
    assert captured["identity"] is not None
    assert captured["singang"] is not None
    assert result["role_perspective_clean"] is False
    assert result["honorific_consistency_clean"] is False
    assert result["role_perspective_hits_count"] == 1
    assert result["honorific_consistency_hits_count"] == 1
    assert "합성갑" not in str(result["role_perspective_hits"])


def test_hverify_calls_verify_on_rendered_pdf(tmp_path, monkeypatch):
    from types import SimpleNamespace

    require_playwright_subprocess()
    from sajugen import config as cfg
    from sajugen.render import pdf as render_pdf

    body = "민준 씨는 차분한 사람입니다. 흐름을 봅니다. " * 30
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
