# -*- coding: utf-8 -*-
"""Phase 2A AI 하네스 계약 테스트 — 실호출 0(Claude/Codex 미호출).

검증 대상:
- 허용 9개 파일 존재.
- 두 JSON Schema 구조(draft 2020-12·required·additionalProperties:false·필수 필드·enum·DIFF_VERDICT 부재).
- ai-harness.ps1 정적 계약(플래그 토큰 포함·--bare 부재·정책 6파일·제외 5경로 미열람·Preflight 선행·금지 호출 부재).
- handoff/current/.gitignore 격리(git check-ignore).
- DryRun(best-effort): 실호출 없이 종료코드 0 + 런타임 산출물 미생성.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED = [
    "scripts/ai-harness.ps1",
    "harness/schemas/claude-plan.schema.json",
    "harness/schemas/codex-plan-review.schema.json",
    "harness/prompts/claude-plan.md",
    "harness/prompts/codex-plan-review.md",
    "handoff/templates/ai_task.md",
    "handoff/current/.gitignore",
    "handoff/current/README.md",
    "tests/test_ai_harness_contract.py",
]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _ps_text() -> str:
    return _read("scripts/ai-harness.ps1")


def test_allowed_files_exist():
    for rel in ALLOWED:
        assert (ROOT / rel).is_file(), f"누락: {rel}"


def test_claude_plan_schema():
    s = json.loads(_read("harness/schemas/claude-plan.schema.json"))
    assert "2020-12" in s["$schema"]
    assert s["additionalProperties"] is False
    assert s["type"] == "object"
    for k in (
        "base_commit",
        "task_sha256",
        "requires_human_approval",
        "no_implementation_performed",
        "allowed_files",
        "forbidden_files",
    ):
        assert k in s["properties"], f"claude schema 필드 누락: {k}"
        assert k in s["required"], f"claude schema required 누락: {k}"
    assert s["properties"]["artifact_type"]["const"] == "claude_plan"
    assert s["properties"]["stage"]["const"] == "plan"
    assert s["properties"]["requires_human_approval"]["const"] is True
    assert s["properties"]["no_implementation_performed"]["const"] is True
    assert "DIFF_VERDICT" not in _read("harness/schemas/claude-plan.schema.json")


def test_codex_review_schema():
    raw = _read("harness/schemas/codex-plan-review.schema.json")
    s = json.loads(raw)
    assert "2020-12" in s["$schema"]
    assert s["additionalProperties"] is False
    for k in (
        "verdict",
        "reviewed_plan_sha256",
        "reviewed_task_sha256",
        "checked_base_commit",
        "no_modification_performed",
    ):
        assert k in s["properties"], f"codex schema 필드 누락: {k}"
        assert k in s["required"], f"codex schema required 누락: {k}"
    assert s["properties"]["verdict"]["enum"] == ["APPROVE", "BLOCK"]
    assert s["properties"]["artifact_type"]["const"] == "codex_review"
    assert s["properties"]["review_stage"]["const"] == "plan"
    assert s["properties"]["no_modification_performed"]["const"] is True
    # DIFF_VERDICT 키/문자열은 정의 자체를 두지 않음
    assert "DIFF_VERDICT" not in raw


def test_ps_contains_required_flag_tokens():
    t = _ps_text()
    required_tokens = [
        "claude -p",
        "--safe-mode",
        "--permission-mode plan",
        "--output-format json",
        "--json-schema",
        "--no-session-persistence",
        "--disallowedTools",
        "codex exec",
        "--ephemeral",
        "--sandbox read-only",
        "--output-schema",
        "-o",
        '[ValidateSet("Plan")]',
    ]
    for tok in required_tokens:
        assert tok in t, f"ps 정적 계약 토큰 누락: {tok}"
    # Codex stdin 표식 '-'(인자 배열 끝)
    assert re.search(r'"-"\s*\)', t), "codex stdin '-' 인자 누락"


def test_ps_forbids_bare_mode():
    assert "--bare" not in _ps_text(), "--bare는 어떤 형태로도 금지"


def test_ps_passes_json_schema_safely():
    # --json-schema는 파일 경로가 아니라 JSON 문자열 인수. PS 5.1 native 인자 손상(개행/따옴표)을
    # 피하려고 (1) compact JSON 직렬화 + (2) Windows 인자 인용 + ProcessStartInfo로 전달해야 한다.
    t = _ps_text()
    assert "--json-schema" in t
    assert "-Compress" in t, "schema를 compact JSON으로 직렬화해야 함"
    assert "ConvertTo-WinArg" in t, "Windows 인자 인용 함수 필요"
    assert "ProcessStartInfo" in t, "call 연산자 대신 ProcessStartInfo로 인자 직접 구성"
    assert "ArgumentList" not in t, ".NET Framework/5.1 부재 — ArgumentList 사용 금지"
    # 파일 경로가 아니라 JSON 문자열 변수를 인자로 넘긴다(claudeArgs 안에서)
    assert '"--json-schema", $claudeSchemaJson' in t
    # --json-schema 인자 바로 뒤에 .schema.json 파일 경로 리터럴을 넘기지 않는다
    assert not re.search(r'--json-schema"?\s*,\s*"[^"]*\.schema\.json"', t)


def test_ps_reads_only_policy_six_files():
    t = _ps_text()
    for pf in (
        "AGENTS.md",
        "CLAUDE.md",
        ".claude/rules/00-immutable.md",
        ".claude/rules/calc.md",
        ".claude/rules/content.md",
        ".claude/rules/render.md",
    ):
        assert pf in t, f"정책 파일 경로 누락: {pf}"
    # 제외 5경로는 스크립트에 등장하지 않는다(열람 코드 부재)
    for excluded in (".env", "data/", "profiles/local", "render/out", "handoff/reports"):
        assert excluded not in t, f"제외 경로가 스크립트에 등장: {excluded}"


def test_ps_git_stderr_does_not_terminate():
    # git이 stderr 경고(.pytest_cache 권한 등)를 내도 EAP=Stop로 승격돼 DryRun을 깨뜨리면 안 됨.
    # native 호출 구간만 EAP=Continue로 낮추고 stderr는 버린다(stdout만 필요).
    t = _ps_text()
    assert "ErrorActionPreference" in t and "Continue" in t
    assert "2>$null" in t  # Invoke-GitRead가 git stderr를 버림


def test_ps_preflight_before_run_folder():
    t = _ps_text()
    assert "--porcelain" in t and "New-Item" in t
    assert t.index("--porcelain") < t.index("New-Item"), "Preflight가 실행 폴더 생성보다 앞서야 함"


def test_ps_no_forbidden_call_patterns():
    t = _ps_text()
    # bare substring이 아니라 '호출 패턴' 정규식(설명 주석 오탐 회피)
    forbidden = [
        r"&\s*git[^\n]*\bcommit\b",
        r"\bgit\s+push\b",
        r"\bhrun\.py\b",
        r"\bhrun\.ps1\b",
        r"(&|Start-Process|Invoke-Expression)[^\n]*\bdeploy\b",
    ]
    for pat in forbidden:
        assert not re.search(pat, t), f"금지 호출 패턴 발견: {pat}"


def test_ps_validates_artifact_shapes():
    t = _ps_text()
    # Codex/Claude 산출물을 schema 수준으로 직접 검증하는 함수가 존재해야 함(해시만 맞으면 통과 방지)
    assert "Assert-CodexReviewShape" in t
    assert "Assert-ClaudePlanShape" in t
    # const·불변 안전 필드 검증 + 추가필드 차단이 포함되어야 함
    assert "no_modification_performed" in t
    assert "no_implementation_performed" in t
    assert "허용 외 추가 필드" in t


def test_ps_task_artifact_not_overclaim_pii():
    t = _ps_text()
    # PII 제거를 보장하지 않으므로 'sanitized' 이름을 쓰지 않는다(secret-checked만 보장)
    assert "task.checked.md" in t
    assert "task.sanitized.md" not in t


def test_gitignore_isolation():
    r = subprocess.run(
        ["git", "check-ignore", "handoff/current/RUN_EXAMPLE/plan-verdict.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, "런타임 산출물은 ignored여야 함"
    r2 = subprocess.run(
        ["git", "check-ignore", "handoff/current/README.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 1, "README.md는 추적 가능해야 함"


def test_dryrun_best_effort():
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return  # PowerShell 없으면 skip(best-effort)
    latest = ROOT / "handoff" / "current" / "LATEST.txt"
    latest_before = latest.exists()
    r = subprocess.run(
        [
            ps,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "ai-harness.ps1"),
            "-Stage",
            "Plan",
            "-Task",
            "handoff/templates/ai_task.md",
            "-DryRun",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"DryRun 종료코드 0 기대, got {r.returncode}: {r.stderr}"
    assert "DRYRUN=1" in r.stdout
    assert "no_runtime_output_written=true" in r.stdout
    # DryRun은 LATEST.txt를 새로 만들지 않는다
    if not latest_before:
        assert not latest.exists(), "DryRun이 LATEST.txt를 생성하면 안 됨"
