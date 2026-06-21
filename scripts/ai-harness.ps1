<#
  ai-harness.ps1 — Phase 2A: Claude Plan -> Codex Plan Review 자동화 (PLAN 단계 전용)

  경계: 이 하네스는 '계획만' 다룬다. 구현·git add/commit/push·deploy·hrun 실행·PDF 재생성·
  sajugen 런타임 LLM 호출을 하지 않는다(호출부 자체가 없음). 수동 승인 모드 — 자동 구현 없음.
  PLAN_VERDICT(구현 전)만 생성하며 DIFF_VERDICT(구현 후)는 만들지 않는다.

  PowerShell 5.1 / 7 공통. 모든 텍스트/JSON 입출력은 UTF-8 무BOM.
#>

param(
  [ValidateSet("Plan")][string]$Stage = "Plan",
  [string]$Task = "handoff/current/task.md",
  [switch]$DryRun,
  [switch]$SelfTest
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

# 리포지토리 루트 = 이 스크립트의 상위 디렉터리
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $ScriptDir

# safe-mode가 CLAUDE.md 자동 로드를 끄므로 명시 전달할 정책 파일 6종(이것만 읽는다).
$PolicyFiles = @(
  "AGENTS.md",
  "CLAUDE.md",
  ".claude/rules/00-immutable.md",
  ".claude/rules/calc.md",
  ".claude/rules/content.md",
  ".claude/rules/render.md"
)

$ClaudePlanSchema = "harness/schemas/claude-plan.schema.json"
$CodexReviewSchema = "harness/schemas/codex-plan-review.schema.json"
$ClaudePromptFile = "harness/prompts/claude-plan.md"
$CodexPromptFile  = "harness/prompts/codex-plan-review.md"

# 허용/금지 파일(계획 packet에 명시 전달 — 정보용)
$AllowedFiles = @(
  "scripts/ai-harness.ps1",
  "harness/schemas/claude-plan.schema.json",
  "harness/schemas/codex-plan-review.schema.json",
  "harness/prompts/claude-plan.md",
  "harness/prompts/codex-plan-review.md",
  "handoff/templates/ai_task.md",
  "handoff/current/.gitignore",
  "handoff/current/README.md",
  "tests/test_ai_harness_contract.py"
)

# ---------- 공통 헬퍼 (무BOM IO, 해시, 외부 호출) ----------
function Get-Utf8NoBom { return New-Object System.Text.UTF8Encoding($false) }

function Read-TextNoBom([string]$Path) {
  return [System.IO.File]::ReadAllText($Path, (Get-Utf8NoBom))
}

function Write-TextNoBom([string]$Path, [string]$Text) {
  [System.IO.File]::WriteAllText($Path, $Text, (Get-Utf8NoBom))
}

function Get-Sha256OfText([string]$Text) {
  $bytes = (Get-Utf8NoBom).GetBytes($Text)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $hash = $sha.ComputeHash($bytes)
  } finally {
    $sha.Dispose()
  }
  $sb = New-Object System.Text.StringBuilder
  foreach ($b in $hash) { [void]$sb.Append($b.ToString("x2")) }
  return $sb.ToString()
}

function Write-PlainLine([string]$Text) {
  # 평문 출력(이모지·장식 금지)
  [Console]::Out.WriteLine($Text)
}

function Stop-Fail([int]$Code, [string]$Message) {
  [Console]::Error.WriteLine("ai-harness FAIL code=${Code}: $Message")
  exit $Code
}

# Windows native 인자 1개를 CommandLineToArgvW 규칙으로 안전 인용한다(JSON의 따옴표/특수문자 보존).
# 근거: MSDN "Everyone quotes command line arguments the wrong way" 알고리즘.
function ConvertTo-WinArg {
  param([string]$Arg)
  if ($Arg.Length -gt 0 -and ($Arg -notmatch '[ \t\n\v"]')) { return $Arg }
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.Append('"')
  $i = 0
  while ($i -lt $Arg.Length) {
    $bs = 0
    while ($i -lt $Arg.Length -and $Arg[$i] -eq '\') { $i++; $bs++ }
    if ($i -eq $Arg.Length) {
      [void]$sb.Append('\' * ($bs * 2))
    } elseif ($Arg[$i] -eq '"') {
      [void]$sb.Append('\' * ($bs * 2 + 1))
      [void]$sb.Append('"')
      $i++
    } else {
      [void]$sb.Append('\' * $bs)
      [void]$sb.Append($Arg[$i])
      $i++
    }
  }
  [void]$sb.Append('"')
  return $sb.ToString()
}

# 외부 CLI 호출(PS 5.1/7 공통): ProcessStartInfo + 직접 구성한 Arguments 문자열(컬렉션 기반 인자 API 미사용 —
# .NET Framework/5.1에는 없음). call 연산자가 멀티라인/따옴표 JSON 인자를 깨뜨리는 PS 5.1 문제를 회피한다.
# stdin=무BOM UTF-8 바이트 직접 기록, stdout/stderr 비동기 캡처(버퍼 데드락 회피), 종료코드 반환.
# 중요: managed .NET 처리(Start/GetBytes/Write/ReadToEndAsync/WaitForExit)는 EAP=Continue로 감싸지 않는다.
# ProcessStartInfo 직접 호출이라 native stderr 승격 문제가 없으므로, 예외는 정상적으로 터지게 두고
# 호출부(try/catch)가 stage별 Stop-Fail(11/13)로 매핑한다. EAP=Continue로 가리면 예외가 묻혀 exit 1로 샌다.
function Invoke-Cli {
  param(
    [string]$Exe,
    [string[]]$CliArgs,
    [string]$StdinText,
    [string]$OutLog,
    [string]$ErrLog
  )
  # stdin이 null이면 잘못된 계획 검토가 되므로 조용히 빈 문자열로 바꾸지 말고 fail-closed(호출부가 매핑).
  if ($null -eq $StdinText) { throw "Invoke-Cli: StdinText is null (fail-closed)" }
  # stdin byte 배열을 '프로세스 시작 전에' 미리 생성·타입고정·검증한다.
  # (try 안에서 즉석 생성→바로 사용하는 취약 구조가 StrictMode에서 즉석 변수 미정의를 유발했던 것을 회피.)
  $stdinBytes = $null
  try {
    [byte[]]$stdinBytes = (Get-Utf8NoBom).GetBytes($StdinText)
  } catch {
    throw ("Invoke-Cli: stdin UTF-8 인코딩 실패: " + $_.Exception.Message)
  }
  if ($null -eq $stdinBytes) { throw "Invoke-Cli: stdin byte 배열 생성 실패 (fail-closed)" }
  $argString = (($CliArgs | ForEach-Object { ConvertTo-WinArg $_ }) -join ' ')
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $Exe
  $psi.Arguments = $argString
  $psi.UseShellExecute = $false
  $psi.RedirectStandardInput = $true
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.StandardOutputEncoding = (Get-Utf8NoBom)
  $psi.StandardErrorEncoding = (Get-Utf8NoBom)
  $psi.WorkingDirectory = $RepoRoot
  $proc = New-Object System.Diagnostics.Process
  $proc.StartInfo = $psi
  $out = ""
  $err = ""
  $code = 0
  try {
    # managed .NET 호출은 예외가 정상적으로 터지게 둔다(EAP 변경 없음 = 스크립트 기본 Stop 유지).
    [void]$proc.Start()
    # 비동기 읽기를 먼저 시작(stdout/stderr 버퍼가 차서 막히는 데드락 방지)
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    # 미리 만든 $stdinBytes만 사용한다(try 안에서 새로 GetBytes 하지 않는다)
    $proc.StandardInput.BaseStream.Write($stdinBytes, 0, $stdinBytes.Length)
    $proc.StandardInput.BaseStream.Flush()
    $proc.StandardInput.Close()
    $proc.WaitForExit()
    $out = $outTask.Result
    $err = $errTask.Result
    $code = $proc.ExitCode
  } finally {
    $proc.Dispose()
  }
  Write-TextNoBom $OutLog $out
  Write-TextNoBom $ErrLog $err
  return $code
}

# StrictMode 안전한 JSON 속성 접근
function Get-JsonProp {
  param([object]$Obj, [string]$Name)
  if ($null -eq $Obj) { return $null }
  $p = $Obj.PSObject.Properties[$Name]
  if ($null -eq $p) { return $null }
  return $p.Value
}

# 배열 필드 확인은 raw JSON 구조로 한다(PS 5.1의 단일원소 배열 unwrap 회피).
function Test-JsonArrayField {
  param([string]$RawText, [string]$Field)
  $pat = '"' + $Field + '"\s*:\s*\['
  return [System.Text.RegularExpressions.Regex]::IsMatch($RawText, $pat)
}

# Codex 결과를 schema 수준으로 직접 검증(CLI 검증에 의존하지 않음). 위반 시 종료코드 14.
function Assert-CodexReviewShape {
  param([object]$Review, [string]$RawText)
  $required = @(
    "schema_version", "artifact_type", "review_stage", "review_target", "checked_base_commit",
    "reviewed_task_sha256", "reviewed_plan_sha256", "verdict", "blockers", "warnings", "evidence",
    "allowed_files", "forbidden_files", "required_validations", "no_modification_performed"
  )
  foreach ($f in $required) {
    if ($null -eq (Get-JsonProp $Review $f)) { Stop-Fail 14 "Codex 결과 필수 필드 누락: $f" }
  }
  foreach ($p in $Review.PSObject.Properties.Name) {
    if ($required -notcontains $p) { Stop-Fail 14 "Codex 결과 허용 외 추가 필드: $p" }
  }
  if ((Get-JsonProp $Review "artifact_type") -ne "codex_review") { Stop-Fail 14 "artifact_type != codex_review" }
  if ((Get-JsonProp $Review "review_stage") -ne "plan") { Stop-Fail 14 "review_stage != plan" }
  if ((Get-JsonProp $Review "review_target") -ne "claude-plan.json") { Stop-Fail 14 "review_target != claude-plan.json" }
  if ((Get-JsonProp $Review "no_modification_performed") -ne $true) { Stop-Fail 14 "no_modification_performed != true" }
  $v = Get-JsonProp $Review "verdict"
  if (@("APPROVE", "BLOCK") -notcontains $v) { Stop-Fail 14 "verdict enum 위반: $v" }
  foreach ($af in @("blockers", "warnings", "evidence", "allowed_files", "forbidden_files", "required_validations")) {
    if (-not (Test-JsonArrayField $RawText $af)) { Stop-Fail 14 "Codex 결과 필드가 배열이 아님: $af" }
  }
}

# Claude plan도 schema 수준 최소 검증(구조 위반을 CLI에만 맡기지 않음). 위반 시 종료코드 12.
function Assert-ClaudePlanShape {
  param([object]$Plan, [string]$RawText)
  $required = @(
    "schema_version", "artifact_type", "stage", "task_id", "base_commit", "task_sha256", "summary",
    "risk_level", "allowed_files", "forbidden_files", "file_changes", "risks", "acceptance_criteria",
    "required_validations", "rollback", "requires_human_approval", "no_implementation_performed"
  )
  foreach ($f in $required) {
    if ($null -eq (Get-JsonProp $Plan $f)) { Stop-Fail 12 "Claude plan 필수 필드 누락: $f" }
  }
  foreach ($p in $Plan.PSObject.Properties.Name) {
    if ($required -notcontains $p) { Stop-Fail 12 "Claude plan 허용 외 추가 필드: $p" }
  }
  if ((Get-JsonProp $Plan "artifact_type") -ne "claude_plan") { Stop-Fail 12 "artifact_type != claude_plan" }
  if ((Get-JsonProp $Plan "stage") -ne "plan") { Stop-Fail 12 "stage != plan" }
  if ((Get-JsonProp $Plan "requires_human_approval") -ne $true) { Stop-Fail 12 "requires_human_approval != true" }
  if ((Get-JsonProp $Plan "no_implementation_performed") -ne $true) { Stop-Fail 12 "no_implementation_performed != true" }
  $rl = Get-JsonProp $Plan "risk_level"
  if (@("low", "medium", "high") -notcontains $rl) { Stop-Fail 12 "risk_level enum 위반: $rl" }
  foreach ($af in @("allowed_files", "forbidden_files", "file_changes", "risks", "acceptance_criteria", "required_validations")) {
    if (-not (Test-JsonArrayField $RawText $af)) { Stop-Fail 12 "Claude plan 필드가 배열이 아님: $af" }
  }
}

# ---------- 절대 경로 헬퍼 ----------
function Abs([string]$Rel) { return (Join-Path $RepoRoot $Rel) }

# 정제 task 텍스트의 고신뢰 secret 검사(존재 시 fail-closed). 값은 출력하지 않는다.
function Test-HighConfidenceSecret([string]$Text) {
  $patterns = @(
    'sk-ant-[A-Za-z0-9_\-]{8,}',
    '(?i)ANTHROPIC_API_KEY\s*[=:]\s*[A-Za-z0-9_\-]{8,}',
    '(?i)(api[_-]?key|secret|token)\s*[=:]\s*[''"]?[A-Za-z0-9_\-]{16,}'
  )
  foreach ($p in $patterns) {
    if ([System.Text.RegularExpressions.Regex]::IsMatch($Text, $p)) { return $true }
  }
  return $false
}

# task 검사 통과본: 의미를 바꾸는 silent masking은 하지 않는다. 고신뢰 secret만 위에서 fail-closed로 막고,
# 생년월일/출생시간/출생지 등 일반 PII는 자동 제거하지 않는다(운영자가 task에 PII를 넣지 않아야 함).
# 산출물 이름을 'checked'(secret 검사 통과)로 두며 PII 제거를 보장하지 않는다. 향후 PII 마스킹 확장 지점.
function Get-CheckedTask([string]$Text) { return $Text }

# git 헬퍼(읽기 전용만, PS 5.1/7 공통). call 연산자 + 배열 splat, -C로 작업트리 지정.
# 중요: git이 stderr로 내는 경고(예: .pytest_cache 권한)는 native error다. $ErrorActionPreference="Stop"
# 상태의 PS 5.1에서는 이 stderr가 NativeCommandError로 승격돼 스크립트를 중단시킨다. 따라서 native 호출
# 구간만 EAP=Continue로 낮추고 복원하며, status stderr는 로그에 남기지 않고 버린다(stdout만 필요).
function Invoke-GitRead {
  param([string[]]$GitArgs)
  $allArgs = @("-C", $RepoRoot) + $GitArgs
  $out = $null
  $code = 0
  $oldEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $out = & git @allArgs 2>$null
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldEap
  }
  return [pscustomobject]@{ Code = $code; Out = ($out -join "`n") }
}

# ======================================================================
# SelfTest — 실 Claude/Codex 없이 Invoke-Cli의 stdin write 경로를 dummy reader(sort)로 검증(PS 5.1/7).
# preflight·실행 폴더·git 이전에 동작하며 검증 후 즉시 종료한다. 실 LLM/CLI 호출 아님.
# ======================================================================
if ($SelfTest) {
  $selftestCode = 1
  $tmpOut = [System.IO.Path]::GetTempFileName()
  $tmpErr = [System.IO.Path]::GetTempFileName()
  try {
    $marker = "SELFTEST_ROUNDTRIP_OK"
    $rc = Invoke-Cli -Exe "sort" -CliArgs @() -StdinText $marker -OutLog $tmpOut -ErrLog $tmpErr
    $captured = Read-TextNoBom $tmpOut
    if ($captured -match $marker) {
      Write-PlainLine ("SELFTEST=PASS stdin_roundtrip=ok rc=" + $rc)
      $selftestCode = 0
    } else {
      Write-PlainLine ("SELFTEST=FAIL stdin_roundtrip_missing rc=" + $rc)
    }
  } catch {
    Write-PlainLine ("SELFTEST=FAIL exception: " + $_.Exception.Message)
  } finally {
    Remove-Item -LiteralPath $tmpOut -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tmpErr -Force -ErrorAction SilentlyContinue
  }
  exit $selftestCode
}

# ======================================================================
# 0) 명령 미리보기 문자열(DryRun 출력 + 사람이 읽는 용도)
#    실제 호출은 인자 배열을 사용하지만, 미리보기는 정규 형태로 보여준다.
# ======================================================================
$ClaudeCmdPreview = 'claude -p --safe-mode --permission-mode plan --output-format json --json-schema <schema-json> --tools "Read,Glob,Grep" --disallowedTools "mcp__*" --no-chrome --no-session-persistence  (stdin: prompt+policy+task)'
$CodexCmdPreview  = 'codex exec --ephemeral --sandbox read-only --output-schema ' + $CodexReviewSchema + ' -o <run>/codex-plan-review.json -   (stdin: review packet)'

# ======================================================================
# 1) PREFLIGHT (읽기 전용, fail-closed) — 폴더/LATEST보다 먼저
# ======================================================================
$taskAbs = if ([System.IO.Path]::IsPathRooted($Task)) { $Task } else { Abs $Task }
if (-not (Test-Path -LiteralPath $taskAbs -PathType Leaf)) {
  Stop-Fail 10 "task 파일 없음: $Task"
}

# policy 6파일 존재·가독 확인
foreach ($pf in $PolicyFiles) {
  $pfAbs = Abs $pf
  if (-not (Test-Path -LiteralPath $pfAbs -PathType Leaf)) {
    Stop-Fail 10 "policy 파일 누락: $pf"
  }
}

# clean tree 강제(비-DryRun만)
$statusRes = Invoke-GitRead @("status", "--porcelain", "--untracked-files=all")
if ($statusRes.Code -ne 0) { Stop-Fail 10 "git status 실패" }
$treeDirty = -not [string]::IsNullOrWhiteSpace($statusRes.Out)
if ((-not $DryRun) -and $treeDirty) {
  Stop-Fail 10 "작업 트리가 clean하지 않음(비-DryRun은 clean tree 필요). DryRun으로 점검하거나 커밋 후 실행."
}

# base_commit / branch
$headRes = Invoke-GitRead @("rev-parse", "HEAD")
if ($headRes.Code -ne 0) { Stop-Fail 10 "git rev-parse HEAD 실패" }
$baseCommit = $headRes.Out.Trim()
$branchRes = Invoke-GitRead @("rev-parse", "--abbrev-ref", "HEAD")
$branch = if ($branchRes.Code -eq 0) { $branchRes.Out.Trim() } else { "unknown" }

# CLI 존재 확인
$claudeCmd = Get-Command "claude" -ErrorAction SilentlyContinue
$codexCmd  = Get-Command "codex" -ErrorAction SilentlyContinue
if (-not $DryRun) {
  if ($null -eq $claudeCmd) { Stop-Fail 10 "claude CLI 없음" }
  if ($null -eq $codexCmd)  { Stop-Fail 10 "codex CLI 없음" }
}
$claudeVersion = "unknown"
$codexVersion  = "unknown"
if ($null -ne $claudeCmd) {
  try { $claudeVersion = (& claude --version 2>$null | Out-String).Trim() } catch { $claudeVersion = "unknown" }
}
if ($null -ne $codexCmd) {
  try { $codexVersion = (& codex --version 2>$null | Out-String).Trim() } catch { $codexVersion = "unknown" }
}

# task 읽기 + secret 검사 + 정제 + 해시(메모리상; 파일 기록은 폴더 생성 후)
$rawTask = Read-TextNoBom $taskAbs
if (Test-HighConfidenceSecret $rawTask) {
  Stop-Fail 10 "고신뢰 secret 패턴 발견 — task에서 제거 후 재실행(값은 출력하지 않음)."
}
$checkedTask = Get-CheckedTask $rawTask
$taskSha = Get-Sha256OfText $checkedTask

# schema 2종 유효성(파싱 확인) — DryRun에서도 점검.
# --json-schema는 파일 경로가 아니라 JSON 문자열 인수다(claude -p --help). PS 5.1 native 인자에서
# 개행/따옴표 손상을 줄이려고 compact(minified) JSON으로 직렬화해 전달한다(파일 경로 전환 아님).
$claudeSchemaRaw = Read-TextNoBom (Abs $ClaudePlanSchema)
$codexSchemaText = Read-TextNoBom (Abs $CodexReviewSchema)
$claudeSchemaObj = $null
try { $claudeSchemaObj = $claudeSchemaRaw | ConvertFrom-Json } catch { Stop-Fail 10 "claude-plan.schema.json 파싱 실패" }
try { [void]($codexSchemaText | ConvertFrom-Json) } catch { Stop-Fail 10 "codex-plan-review.schema.json 파싱 실패" }
$claudeSchemaJson = $claudeSchemaObj | ConvertTo-Json -Depth 30 -Compress

# ======================================================================
# DryRun 분기 — 실호출·런타임 산출물 없음
# ======================================================================
if ($DryRun) {
  Write-PlainLine "DRYRUN=1"
  Write-PlainLine ("stage=" + $Stage + " branch=" + $branch + " base_commit=" + $baseCommit)
  Write-PlainLine ("task=" + $Task + " task_sha256=" + $taskSha)
  Write-PlainLine ("policy_files=" + ($PolicyFiles -join ","))
  Write-PlainLine ("would_run_claude: " + $ClaudeCmdPreview)
  Write-PlainLine ("would_run_codex:  " + $CodexCmdPreview)
  $claudePresent = if ($null -ne $claudeCmd) { "present" } else { "MISSING" }
  $codexPresent = if ($null -ne $codexCmd) { "present" } else { "MISSING" }
  # DryRun의 CLI 점검은 best-effort 표시만(하드 실패는 비-DryRun에서). 실제 실행 전 참고용.
  Write-PlainLine ("cli_check(best-effort): claude=" + $claudePresent + " codex=" + $codexPresent)
  Write-PlainLine "no_runtime_output_written=true (no run folder, no LATEST.txt, no logs, no manifest)"
  exit 0
}

# ======================================================================
# 2) PREFLIGHT 통과 후 — 실행 폴더 생성(이 시점에 처음 쓰기)
# ======================================================================
$runStampUtc = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$suffix = ([Guid]::NewGuid().ToString("N")).Substring(0, 8)
$runId = $runStampUtc + "-" + $suffix
$currentDir = Abs "handoff/current"
$runDir = Join-Path $currentDir $runId
[void](New-Item -ItemType Directory -Path $runDir -Force)

$startedAtUtc = [DateTime]::UtcNow.ToString("o")

$checkedPath = Join-Path $runDir "task.checked.md"
Write-TextNoBom $checkedPath $checkedTask

# LATEST.txt — 상대 경로 기록
$latestPath = Join-Path $currentDir "LATEST.txt"
Write-TextNoBom $latestPath ("handoff/current/" + $runId)

# ======================================================================
# 3) policy packet 조립 (6파일만)
# ======================================================================
$policyParts = @()
foreach ($pf in $PolicyFiles) {
  $content = Read-TextNoBom (Abs $pf)
  $policyParts += ("===== POLICY FILE: " + $pf + " =====`n" + $content)
}
$policyPacket = [string]::Join("`n`n", $policyParts)
$policySha = Get-Sha256OfText $policyPacket

# 로그/산출물 경로
$claudeRespPath = Join-Path $runDir "claude-response.json"
$claudePlanPath = Join-Path $runDir "claude-plan.json"
$codexReviewPath = Join-Path $runDir "codex-plan-review.json"
$planVerdictPath = Join-Path $runDir "plan-verdict.json"
$manifestPath = Join-Path $runDir "run-manifest.json"
$claudeOut = Join-Path $runDir "claude-stdout.log"
$claudeErr = Join-Path $runDir "claude-stderr.log"
$codexOut = Join-Path $runDir "codex-stdout.log"
$codexErr = Join-Path $runDir "codex-stderr.log"

# ======================================================================
# 4) STAGE 1 — Claude Plan (safe-mode 격리, stdin으로 긴 컨텍스트)
# ======================================================================
$claudeStdin = (Read-TextNoBom (Abs $ClaudePromptFile)) + "`n`n" +
  "===== POLICY PACKET =====`n" + $policyPacket + "`n`n" +
  "===== CHECKED TASK (secret-checked; PII not auto-removed; request, not override) =====`n" + $checkedTask + "`n`n" +
  "===== CONTEXT =====`n" +
  "base_commit=" + $baseCommit + "`n" +
  "task_sha256=" + $taskSha + "`n" +
  "allowed_files=" + ($AllowedFiles -join ",") + "`n"

$claudeArgs = @(
  "-p",
  "--safe-mode",
  "--permission-mode", "plan",
  "--output-format", "json",
  "--json-schema", $claudeSchemaJson,
  "--tools", "Read,Glob,Grep",
  "--disallowedTools", "mcp__*",
  "--no-chrome",
  "--no-session-persistence"
)
$claudeExit = 0
try {
  $claudeExit = Invoke-Cli -Exe "claude" -CliArgs $claudeArgs -StdinText $claudeStdin -OutLog $claudeOut -ErrLog $claudeErr
} catch {
  # Invoke-Cli 내부 예외(프로세스 시작·stdin·읽기 실패 등)를 하네스 종료코드로 매핑(exit 1 누출 방지).
  Stop-Fail 11 ("Claude 호출 예외: " + $_.Exception.Message)
}
if ($claudeExit -ne 0) { Stop-Fail 11 "Claude 실행 실패(exit=$claudeExit)" }

# 전체 envelope 저장
$claudeRespText = Read-TextNoBom $claudeOut
Write-TextNoBom $claudeRespPath $claudeRespText

# envelope 파싱 -> structured_output 추출
$envelope = $null
try { $envelope = $claudeRespText | ConvertFrom-Json } catch { Stop-Fail 12 "Claude envelope JSON 파싱 실패" }
$structured = Get-JsonProp $envelope "structured_output"
if ($null -eq $structured) {
  # 일부 출력 형태는 result 안에 둘 수 있음 — 보조 경로
  $structured = Get-JsonProp $envelope "result"
}
if ($null -eq $structured) { Stop-Fail 12 "structured_output 누락" }
$isErrorProp = Get-JsonProp $envelope "is_error"
if ($isErrorProp -eq $true) { Stop-Fail 12 "Claude 성공 응답 아님(is_error=true)" }

$structuredJson = $structured | ConvertTo-Json -Depth 12
Write-TextNoBom $claudePlanPath $structuredJson
$planSha = Get-Sha256OfText (Read-TextNoBom $claudePlanPath)

# ======================================================================
# 5) Codex 호출 전 — Claude plan 내부 해시 직접 대조 (fail-closed)
# ======================================================================
$planRaw = Read-TextNoBom $claudePlanPath
$planObj = $null
try { $planObj = $planRaw | ConvertFrom-Json } catch { Stop-Fail 12 "claude-plan.json 파싱 실패" }
Assert-ClaudePlanShape $planObj $planRaw
$planBase = Get-JsonProp $planObj "base_commit"
$planTaskSha = Get-JsonProp $planObj "task_sha256"
if ($planBase -ne $baseCommit) { Stop-Fail 14 "Claude plan base_commit 불일치(Codex 호출 전 차단)" }
if ($planTaskSha -ne $taskSha) { Stop-Fail 14 "Claude plan task_sha256 불일치(Codex 호출 전 차단)" }

# ======================================================================
# 6) STAGE 2 — Codex Plan Review (읽기 전용, stdin packet)
# ======================================================================
$reviewPacket = (Read-TextNoBom (Abs $CodexPromptFile)) + "`n`n" +
  "===== REVIEW PACKET =====`n" +
  "stage=plan`n" +
  "base_commit=" + $baseCommit + "`n" +
  "task_sha256=" + $taskSha + "`n" +
  "claude_plan_sha256=" + $planSha + "`n" +
  "policy_sha256=" + $policySha + "`n" +
  "allowed_files=" + ($AllowedFiles -join ",") + "`n`n" +
  "===== CHECKED TASK (secret-checked; PII not auto-removed) =====`n" + $checkedTask + "`n`n" +
  "===== CLAUDE PLAN (claude-plan.json) =====`n" + (Read-TextNoBom $claudePlanPath) + "`n`n" +
  "===== POLICY PACKET =====`n" + $policyPacket + "`n"

$codexArgs = @(
  "exec",
  "--ephemeral",
  "--sandbox", "read-only",
  "--output-schema", (Abs $CodexReviewSchema),
  "-o", $codexReviewPath,
  "-"
)
$codexExit = 0
try {
  $codexExit = Invoke-Cli -Exe "codex" -CliArgs $codexArgs -StdinText $reviewPacket -OutLog $codexOut -ErrLog $codexErr
} catch {
  Stop-Fail 13 ("Codex 호출 예외: " + $_.Exception.Message)
}
if ($codexExit -ne 0) { Stop-Fail 13 "Codex 실행 실패(exit=$codexExit)" }

# -o 저장본을 PS가 직접 파싱·검증(CLI 검증에 의존하지 않음)
if (-not (Test-Path -LiteralPath $codexReviewPath -PathType Leaf)) {
  Stop-Fail 14 "Codex 결과 파일 미생성: codex-plan-review.json"
}
$codexRaw = Read-TextNoBom $codexReviewPath
$review = $null
try { $review = $codexRaw | ConvertFrom-Json } catch { Stop-Fail 14 "codex-plan-review.json 파싱 실패" }
# schema 수준 검증(필수 필드·const·enum·배열·추가필드 차단). 해시만 맞으면 통과하는 우회 방지.
Assert-CodexReviewShape $review $codexRaw

$verdict = Get-JsonProp $review "verdict"
$revPlanSha = Get-JsonProp $review "reviewed_plan_sha256"
$revTaskSha = Get-JsonProp $review "reviewed_task_sha256"
$revBase = Get-JsonProp $review "checked_base_commit"

# 해시·base_commit 재대조
if ($revPlanSha -ne $planSha) { Stop-Fail 14 "reviewed_plan_sha256 불일치" }
if ($revTaskSha -ne $taskSha) { Stop-Fail 14 "reviewed_task_sha256 불일치" }
if ($revBase -ne $baseCommit) { Stop-Fail 14 "checked_base_commit 불일치" }

# ======================================================================
# 7) Verdict & manifest 기록
# ======================================================================
$blockers = Get-JsonProp $review "blockers"
if ($null -eq $blockers) { $blockers = @() }

$verdictObj = [ordered]@{
  kind = "PLAN_VERDICT"
  verdict = $verdict
  base_commit = $baseCommit
  reviewed_plan_sha256 = $planSha
  reviewed_task_sha256 = $taskSha
  blockers = $blockers
  run_id = $runId
  stamp = [DateTime]::UtcNow.ToString("o")
}
Write-TextNoBom $planVerdictPath ($verdictObj | ConvertTo-Json -Depth 12)

$endedAtUtc = [DateTime]::UtcNow.ToString("o")
$manifest = [ordered]@{
  run_id = $runId
  schema_version = "1.0"
  stage = "plan"
  branch = $branch
  base_commit = $baseCommit
  task_sha256 = $taskSha
  claude_plan_sha256 = $planSha
  policy_sha256 = $policySha
  claude_version = $claudeVersion
  codex_version = $codexVersion
  started_at_utc = $startedAtUtc
  ended_at_utc = $endedAtUtc
  claude_exit_code = $claudeExit
  codex_exit_code = $codexExit
  plan_verdict = $verdict
  no_implementation_performed = $true
}
Write-TextNoBom $manifestPath ($manifest | ConvertTo-Json -Depth 12)

Write-PlainLine ("PLAN_VERDICT=" + $verdict + " base_commit=" + $baseCommit + " plan_sha256=" + $planSha + " run=" + $runId)

if ($verdict -eq "APPROVE") { exit 0 } else { exit 2 }
