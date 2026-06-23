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


def test_claude_plan_schema_simplified():
    # 생성용 최소 schema: structured_output 생성을 위해 검증성 키워드 제거(복잡 schema는 CLI가 structured_output을 드롭).
    raw = _read("harness/schemas/claude-plan.schema.json")
    s = json.loads(raw)
    assert s["type"] == "object"
    assert s["additionalProperties"] is False
    # 제거 확인: const/pattern/minLength/$schema/$id/title/description 없음
    assert "const" not in raw
    assert "pattern" not in raw
    assert "minLength" not in raw
    for meta in ("$schema", "$id", "title", "description"):
        assert meta not in s, f"제거 대상 메타 키 잔존: {meta}"
    # 유지 확인: 필수 필드/properties
    for k in (
        "schema_version",
        "artifact_type",
        "stage",
        "base_commit",
        "task_sha256",
        "requires_human_approval",
        "no_implementation_performed",
        "allowed_files",
        "forbidden_files",
        "file_changes",
    ):
        assert k in s["properties"], f"claude schema 필드 누락: {k}"
        assert k in s["required"], f"claude schema required 누락: {k}"
    # risk_level enum은 유지 가능
    assert s["properties"]["risk_level"]["enum"] == ["low", "medium", "high"]
    # canonical 값을 singleton enum으로 강제(claude-plan/Plan 변형 차단)
    assert s["properties"]["artifact_type"]["enum"] == ["claude_plan"]
    assert s["properties"]["stage"]["enum"] == ["plan"]
    assert "DIFF_VERDICT" not in raw


def test_ps_assert_claudeplan_enforces_removed_constraints():
    # schema에서 제거한 엄격 제약을 PS Assert-ClaudePlanShape가 강제하는지 정적 고정.
    t = _ps_text()
    assert "Assert-ClaudePlanShape" in t
    # base_commit/task_sha256 hex(pattern 대체)
    assert "[0-9a-f]{7,40}" in t
    assert "[0-9a-f]{64}" in t
    # const 대체
    assert "claude_plan" in t
    assert "no_implementation_performed" in t
    assert "requires_human_approval" in t
    # 추가필드 금지 + file_changes item(path/change) 검증
    assert "unexpected extra field" in t
    assert "file_changes" in t
    assert "path" in t and "change" in t
    # 비어있지 않은 string 검증(minLength 대체)
    assert "IsNullOrWhiteSpace" in t
    # 배열 필드는 raw JSON 기준으로 '진짜 배열'인지 확인(스칼라 문자열 @() 감싸기 통과 방지)
    assert "Test-JsonArrayField" in t
    assert "field is not an array" in t


def test_codex_review_schema_simplified():
    # 생성용 최소 schema: Codex --output-schema(OpenAI response_format) 호환 위해 검증성 키워드 제거.
    raw = _read("harness/schemas/codex-plan-review.schema.json")
    s = json.loads(raw)
    assert s["type"] == "object"
    assert s["additionalProperties"] is False
    # 제거 확인: const/pattern/minLength/$schema/$id/title/description 없음 (type 없는 const-only 필드 제거)
    assert "const" not in raw
    assert "pattern" not in raw
    assert "minLength" not in raw
    for meta in ("$schema", "$id", "title", "description"):
        assert meta not in s, f"제거 대상 메타 키 잔존: {meta}"
    # 모든 property에 type 키가 있어야 함(Codex가 type 없는 schema를 거부)
    for name, spec in s["properties"].items():
        assert "type" in spec, f"property {name} 에 type 키 없음"
    # 유지 확인: 필수 필드 + verdict enum
    for k in (
        "verdict",
        "reviewed_plan_sha256",
        "reviewed_task_sha256",
        "checked_base_commit",
        "no_modification_performed",
        "blockers",
        "allowed_files",
    ):
        assert k in s["properties"], f"codex schema 필드 누락: {k}"
        assert k in s["required"], f"codex schema required 누락: {k}"
    assert s["properties"]["verdict"]["enum"] == ["APPROVE", "BLOCK"]
    # canonical 값을 singleton enum으로 강제(실제 codex가 codex_plan_review 등 비-canonical 값을 내는 것 차단)
    assert s["properties"]["artifact_type"]["enum"] == ["codex_review"]
    assert s["properties"]["review_stage"]["enum"] == ["plan"]
    assert s["properties"]["review_target"]["enum"] == ["claude-plan.json"]
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


def test_ps_is_ascii_only():
    # PS 5.1는 BOM 없는 스크립트를 시스템 ANSI 코드페이지(cp949 등)로 읽어 비ASCII 문자열을 손상시킨다
    # (한글 선행바이트가 닫는 따옴표를 삼켜 파서가 깨짐). ai-harness.ps1을 ASCII-only로 유지해
    # Windows PowerShell 5.1과 PowerShell 7에서 동일하게 파싱되도록 강제한다.
    data = (ROOT / "scripts" / "ai-harness.ps1").read_bytes()
    non_ascii = [i for i, b in enumerate(data) if b > 0x7F]
    assert not non_ascii, f"ai-harness.ps1 비ASCII 바이트 오프셋(앞 10개): {non_ascii[:10]}"


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


def test_ps_invoke_cli_exceptions_map_to_stage_exit_codes():
    # Invoke-Cli 예외(프로세스 시작·stdin·읽기 실패)가 exit 1로 새지 않고 stage별 Stop-Fail로 매핑돼야 함.
    t = _ps_text()
    # Claude/Codex 호출부가 try/catch로 감싸 각각 11/13으로 매핑
    assert re.search(r"try\s*\{\s*\$claudeExit\s*=\s*Invoke-Cli", t), "Claude 호출 try/catch 필요"
    assert re.search(r"catch\s*\{[^}]*Stop-Fail\s+11", t), "Claude 예외 -> Stop-Fail 11"
    assert re.search(r"try\s*\{\s*\$codexExit\s*=\s*Invoke-Cli", t), "Codex 호출 try/catch 필요"
    assert re.search(r"catch\s*\{[^}]*Stop-Fail\s+13", t), "Codex 예외 -> Stop-Fail 13"
    # StdinText null이면 fail-closed(조용히 빈 문자열로 바꾸지 않음)
    assert re.search(r"\$null\s*-eq\s*\$StdinText", t), "StdinText null fail-closed 필요"
    # Invoke-Cli 내부 managed .NET 처리를 EAP=Continue로 감싸지 않는다(예외가 정상 전파돼야 함).
    # = Invoke-Cli 본문에 ErrorActionPreference 재설정이 없어야 한다(EAP 처리는 Invoke-GitRead에만 존재).
    m = re.search(r"function Invoke-Cli\s*\{.*?\n\}", t, re.DOTALL)
    assert m, "Invoke-Cli 함수 본문을 찾지 못함"
    assert "ErrorActionPreference" not in m.group(0), "Invoke-Cli는 EAP를 변경하지 않아야 함"


def test_ps_stdin_bytes_precomputed():
    # stdin byte 배열은 프로세스 시작 전에 미리 만들고 타입 고정(try 안 즉석 생성→사용하는 취약 구조 회피).
    t = _ps_text()
    assert "[byte[]]$stdinBytes" in t, "stdin byte 사전 생성/타입고정 필요"
    assert "$stdinBytes" in t
    # 회귀 방지: try 안에서 $inBytes를 즉석 생성해 바로 쓰던 취약 패턴 제거
    assert "$inBytes" not in t, "$inBytes 즉석 생성 패턴 잔존(회귀)"


def test_invoke_cli_stdin_roundtrip_selftest():
    # 실 Claude/Codex 없이 dummy reader(sort)로 Invoke-Cli stdin write가 PS 5.1/7에서 성공하는지 검증.
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if not ps:
        return  # PowerShell 없으면 skip(best-effort)
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
            "-SelfTest",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"SelfTest 실패: out={r.stdout} err={r.stderr}"
    assert "SELFTEST=PASS" in r.stdout, f"stdin roundtrip 미확인: {r.stdout}"
    # 응답 처리 케이스도 self-test에서 통과해야 함(순수 JSON / prose BLOCK / structured_output / is_error)
    assert "envelope_pure=ok" in r.stdout
    assert "envelope_prose_blocked=ok" in r.stdout
    assert "structured_output=ok" in r.stdout
    assert "is_error_blocked=ok" in r.stdout
    assert "planshape_valid=ok" in r.stdout
    assert "planshape_bad_rejected=ok" in r.stdout
    # 배열 필드의 raw JSON 기준 검증 회복(스칼라/객체 거부) + 라운드트립 보존
    assert "planshape_scalar_array_rejected=ok" in r.stdout
    assert "planshape_file_changes_object_rejected=ok" in r.stdout
    assert "planshape_roundtrip=ok" in r.stdout
    # Codex review shape 유효/거부 케이스
    assert "codexshape_valid=ok" in r.stdout
    assert "codexshape_bad_artifact_rejected=ok" in r.stdout
    assert "codexshape_bad_hash_rejected=ok" in r.stdout
    assert "codexshape_blockers_scalar_rejected=ok" in r.stdout
    assert "codexshape_nomod_false_rejected=ok" in r.stdout
    # bool 타입 강제: string "true"/number 1 이 boolean true로 통과하지 않아야 함
    assert "planshape_rha_string_rejected=ok" in r.stdout
    assert "planshape_nip_number_rejected=ok" in r.stdout
    assert "codexshape_nomod_string_rejected=ok" in r.stdout
    assert "codexshape_nomod_number_rejected=ok" in r.stdout
    # string const(artifact_type/stage)도 boolean true가 통과하지 않아야 함
    assert "planshape_artifact_bool_rejected=ok" in r.stdout
    assert "planshape_stage_bool_rejected=ok" in r.stdout
    # 실제 codex가 냈던 비-canonical artifact_type("codex_plan_review")도 거부
    assert "codexshape_canonical_artifact_rejected=ok" in r.stdout
    # task.md machine-readable scope is parsed and enforced before Codex review.
    assert "taskscope_valid=ok" in r.stdout
    assert "taskscope_glob=ok" in r.stdout
    assert "taskscope_plan_valid=ok" in r.stdout
    assert "taskscope_plan_bad_rejected=ok" in r.stdout


def test_ps_claude_response_failclosed():
    # Claude 응답 읽기/저장/파싱이 전부 fail-closed(Stop-Fail 12)이고 prose+JSON 혼입을 BLOCK해야 함.
    t = _ps_text()
    # 응답 추출 로직이 self-test 가능한 함수로 분리됨
    assert "Resolve-ClaudePlanJson" in t
    # 단일 JSON 객체만 허용(prose/markdown/펜스 차단)
    assert "StartsWith" in t and "EndsWith" in t
    # 응답 텍스트는 pre-declare 후 try/catch로 읽는다(StrictMode 미정의 크래시 방지)
    assert "$claudeRespText = $null" in t
    # 파일 존재/크기 검사
    assert "claude-stdout.log missing" in t
    assert "-le 0" in t
    # 읽기/저장/파싱 예외가 Stop-Fail 12로 매핑(exit 1 누출 방지)
    assert "Claude response read failed" in t
    assert "claude-response.json write failed" in t
    assert "Claude response processing BLOCK" in t


def test_ps_validates_artifact_shapes():
    t = _ps_text()
    # Codex/Claude 산출물을 schema 수준으로 직접 검증하는 함수가 존재해야 함(해시만 맞으면 통과 방지)
    assert "Assert-CodexReviewShape" in t
    assert "Assert-ClaudePlanShape" in t
    # const·불변 안전 필드 검증 + 추가필드 차단이 포함되어야 함
    assert "no_modification_performed" in t
    assert "no_implementation_performed" in t
    assert "unexpected extra field" in t


def test_ps_assert_codexreview_enforces_removed_constraints():
    # codex schema에서 제거한 엄격 제약을 PS Assert-CodexReviewShape가 강제하는지 정적 고정.
    t = _ps_text()
    assert "Assert-CodexReviewShape" in t
    # const 대체
    assert "codex_review" in t
    assert "claude-plan.json" in t
    assert "review_stage" in t
    # hash/base_commit hex (pattern 대체)
    assert "checked_base_commit" in t
    assert "reviewed_plan_sha256" in t and "reviewed_task_sha256" in t
    # 배열은 raw JSON 기준 검증
    assert "Test-JsonArrayField" in t
    assert "verdict" in t


def test_ps_task_artifact_not_overclaim_pii():
    t = _ps_text()
    # PII 제거를 보장하지 않으므로 'sanitized' 이름을 쓰지 않는다(secret-checked만 보장)
    assert "task.checked.md" in t
    assert "task.sanitized.md" not in t


def test_ai_task_template_has_machine_readable_scope():
    t = _read("handoff/templates/ai_task.md")
    assert "## ALLOWED_FILES" in t
    assert "## FORBIDDEN_FILES" in t
    assert "- handoff/current/README.md" in t
    assert "- sajugen/calc/**" in t


def test_ps_derives_allowed_files_from_task_scope():
    t = _ps_text()
    assert "Get-TaskListSection" in t
    assert 'Get-TaskListSection $checkedTask "ALLOWED_FILES"' in t
    assert 'Get-TaskListSection $checkedTask "FORBIDDEN_FILES"' in t
    assert "Assert-TaskScope" in t
    assert "Assert-PlanScopeWithinTask" in t
    assert '"allowed_files=" + ($taskAllowedFiles -join ",")' in t
    assert '"forbidden_files=" + ($taskForbiddenFiles -join ",")' in t
    assert "$AllowedFiles = @(" not in t


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
