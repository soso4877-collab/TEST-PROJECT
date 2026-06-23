<#
  ai-harness.ps1 - Phase 2A: Claude Plan -> Codex Plan Review automation (PLAN stage only)

  Boundary: this harness deals with 'plans only'. It does not implement, does not run
  git add/commit/push, deploy, hrun, or regenerate PDFs, and does not call the sajugen
  runtime LLM (no such call sites exist). Manual approval mode - no automatic implementation.
  It produces only PLAN_VERDICT (pre-implementation); it does not produce DIFF_VERDICT (post-implementation).

  Windows PowerShell 5.1 / 7 compatible. All text/JSON IO is UTF-8 without BOM.
  Note: keep this script strictly ASCII so PS 5.1 (which reads BOM-less scripts as the ANSI code page) parses it correctly.
#>

param(
  [ValidateSet("Plan")][string]$Stage = "Plan",
  [string]$Task = "handoff/current/task.md",
  [switch]$DryRun,
  [switch]$SelfTest
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

# Repository root = parent directory of this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Split-Path -Parent $ScriptDir

# safe-mode disables CLAUDE.md auto-load, so pass these 6 policy files explicitly (only these are read).
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

# Allowed/forbidden files (passed in the plan packet - informational)
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

# ---------- common helpers (no-BOM IO, hash, external call) ----------
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
  # plain output (no emoji/decoration)
  [Console]::Out.WriteLine($Text)
}

function Stop-Fail([int]$Code, [string]$Message) {
  [Console]::Error.WriteLine("ai-harness FAIL code=${Code}: $Message")
  exit $Code
}

# Quote one Windows native argument per the CommandLineToArgvW rules (preserve JSON quotes/special chars).
# Basis: MSDN "Everyone quotes command line arguments the wrong way" algorithm.
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

# External CLI call (PS 5.1/7 common): ProcessStartInfo + a manually built Arguments string (no collection-based
# arg API - absent in .NET Framework/5.1). Avoids the PS 5.1 issue where the call operator breaks multiline/quoted JSON args.
# stdin = no-BOM UTF-8 bytes written directly; stdout/stderr captured async (avoid buffer deadlock); returns exit code.
# Important: managed .NET work (Start/GetBytes/Write/ReadToEndAsync/WaitForExit) is NOT wrapped with EAP=Continue.
# Since ProcessStartInfo is called directly there is no native-stderr promotion issue, so let exceptions throw normally and
# the caller (try/catch) maps them to a per-stage Stop-Fail (11/13). Masking with EAP=Continue would bury exceptions and leak as exit 1.
function Invoke-Cli {
  param(
    [string]$Exe,
    [string[]]$CliArgs,
    [string]$StdinText,
    [string]$OutLog,
    [string]$ErrLog
  )
  # If stdin is null it would mean reviewing the wrong plan, so do not silently substitute an empty string - fail-closed (caller maps).
  if ($null -eq $StdinText) { throw "Invoke-Cli: StdinText is null (fail-closed)" }
  # Build/type-fix/validate the stdin byte array BEFORE starting the process.
  # (Avoids the fragile pattern of creating it inline inside try then using immediately, which triggered StrictMode undefined-variable.)
  $stdinBytes = $null
  try {
    [byte[]]$stdinBytes = (Get-Utf8NoBom).GetBytes($StdinText)
  } catch {
    throw ("Invoke-Cli: stdin UTF-8 encoding failed: " + $_.Exception.Message)
  }
  if ($null -eq $stdinBytes) { throw "Invoke-Cli: stdin byte array build failed (fail-closed)" }
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
    # let managed .NET calls throw normally (no EAP change = script default Stop preserved).
    [void]$proc.Start()
    # start async reads first (prevent deadlock when stdout/stderr buffers fill)
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    # use only the pre-built $stdinBytes (do not call GetBytes again inside try)
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

# StrictMode-safe JSON property access
function Get-JsonProp {
  param([object]$Obj, [string]$Name)
  if ($null -eq $Obj) { return $null }
  $p = $Obj.PSObject.Properties[$Name]
  if ($null -eq $p) { return $null }
  return $p.Value
}

# Array-field check via raw JSON structure (avoid PS 5.1 single-element array unwrap).
function Test-JsonArrayField {
  param([string]$RawText, [string]$Field)
  $pat = '"' + $Field + '"\s*:\s*\['
  return [System.Text.RegularExpressions.Regex]::IsMatch($RawText, $pat)
}

# Safely extract the plan JSON 'text' from the Claude envelope. Prefer the structured_output object; otherwise use
# result only when it is a 'single JSON object string'. prose/markdown/explanation mixed in is not extracted but throws (BLOCK) - caller does Stop-Fail 12.
# To avoid single-element array unwrap, the result-string path returns the raw text as-is.
function Resolve-ClaudePlanJson {
  param([object]$Envelope)
  if ($null -eq $Envelope) { throw "envelope null" }
  $isErr = Get-JsonProp $Envelope "is_error"
  if ($isErr -eq $true) { throw "is_error=true (not a Claude success response)" }
  $structured = Get-JsonProp $Envelope "structured_output"
  if ($null -ne $structured -and ($structured -is [System.Management.Automation.PSCustomObject])) {
    return ($structured | ConvertTo-Json -Depth 30)
  }
  $result = Get-JsonProp $Envelope "result"
  if ($null -eq $result) { throw "structured_output/result missing" }
  if ($result -is [System.Management.Automation.PSCustomObject]) {
    return ($result | ConvertTo-Json -Depth 30)
  }
  if ($result -is [string]) {
    $rs = $result.Trim()
    # Accept only a pure single JSON object: must start with '{' and end with '}' (block prose/markdown-fence/surrounding text).
    if (-not ($rs.StartsWith("{") -and $rs.EndsWith("}"))) {
      throw "result is not a single JSON object (prose/markdown mixed in) - BLOCK"
    }
    $probe = $null
    try { $probe = $rs | ConvertFrom-Json } catch { throw "result JSON parse failed - BLOCK" }
    if (-not ($probe -is [System.Management.Automation.PSCustomObject])) { throw "result is not a JSON object - BLOCK" }
    return $rs
  }
  throw "result type unknown - BLOCK"
}

# Validate the Codex result at schema level. The generation schema is simplified for Codex --output-schema compatibility,
# so enforce all the removed strict constraints (hex/const/array-ness/element type) here. On violation throw -> caller Stop-Fail 14.
function Assert-CodexReviewShape {
  param([object]$Review, [string]$RawText)
  $required = @(
    "schema_version", "artifact_type", "review_stage", "review_target", "checked_base_commit",
    "reviewed_task_sha256", "reviewed_plan_sha256", "verdict", "blockers", "warnings", "evidence",
    "allowed_files", "forbidden_files", "required_validations", "no_modification_performed"
  )
  # all required fields present (property exists even if an empty array arrives as null)
  foreach ($f in $required) {
    if ($null -eq $Review.PSObject.Properties[$f]) { throw "missing required field: $f" }
  }
  # forbid fields outside the allowed set
  foreach ($p in $Review.PSObject.Properties.Name) {
    if ($required -notcontains $p) { throw "unexpected extra field: $p" }
  }
  # const replacement (validate type+value together - defensive)
  $artifact = Get-JsonProp $Review "artifact_type"
  if (-not ($artifact -is [string]) -or $artifact -ne "codex_review") { throw "artifact_type != codex_review" }
  $rstage = Get-JsonProp $Review "review_stage"
  if (-not ($rstage -is [string]) -or $rstage -ne "plan") { throw "review_stage != plan" }
  $rtarget = Get-JsonProp $Review "review_target"
  if (-not ($rtarget -is [string]) -or $rtarget -ne "claude-plan.json") { throw "review_target != claude-plan.json" }
  # enforce bool type (block "true"/1 passing via PS comparison coercion)
  $nomod = Get-JsonProp $Review "no_modification_performed"
  if (-not ($nomod -is [bool]) -or $nomod -ne $true) { throw "no_modification_performed != boolean true" }
  # verdict enum
  if (@("APPROVE", "BLOCK") -notcontains (Get-JsonProp $Review "verdict")) { throw "verdict enum violation" }
  # schema_version non-empty string
  $sv = Get-JsonProp $Review "schema_version"
  if (-not ($sv -is [string]) -or [string]::IsNullOrWhiteSpace($sv)) { throw "schema_version is not a non-empty string" }
  # hex (pattern replacement)
  $cb = Get-JsonProp $Review "checked_base_commit"
  if (-not ($cb -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($cb, '^[0-9a-f]{7,40}$')) { throw "checked_base_commit format violation (7-40 hex)" }
  foreach ($hf in @("reviewed_task_sha256", "reviewed_plan_sha256")) {
    $hv = Get-JsonProp $Review $hf
    if (-not ($hv -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($hv, '^[0-9a-f]{64}$')) { throw "$hf format violation (64 hex)" }
  }
  # arrays: confirm 'real array' by raw JSON (block scalar @() wrapping) then each element string
  foreach ($af in @("blockers", "warnings", "evidence", "allowed_files", "forbidden_files", "required_validations")) {
    if (-not (Test-JsonArrayField $RawText $af)) { throw "$af field is not an array" }
    $val = (Get-JsonProp $Review $af)
    foreach ($el in @($val)) {
      if ($null -eq $el) { continue }
      if (-not ($el -is [string])) { throw "$af element is not a string" }
    }
  }
}

# Validate the Claude plan at schema level. The generation schema is simplified to allow structured_output generation,
# so enforce all the removed strict constraints (hex/const/non-empty string/array element type/file_changes item) here.
# On violation throw -> caller try/catch maps to Stop-Fail 12 (do not call Stop-Fail directly so self-test works).
function Assert-ClaudePlanShape {
  param([object]$Plan, [string]$RawText)
  $required = @(
    "schema_version", "artifact_type", "stage", "task_id", "base_commit", "task_sha256", "summary",
    "risk_level", "allowed_files", "forbidden_files", "file_changes", "risks", "acceptance_criteria",
    "required_validations", "rollback", "requires_human_approval", "no_implementation_performed"
  )
  # all required fields present (property exists even if an empty array arrives as null)
  foreach ($f in $required) {
    if ($null -eq $Plan.PSObject.Properties[$f]) { throw "missing required field: $f" }
  }
  # forbid fields outside the allowed set
  foreach ($p in $Plan.PSObject.Properties.Name) {
    if ($required -notcontains $p) { throw "unexpected extra field: $p" }
  }
  # const replacement
  # Inline calls since the variable is unused (avoid StrictMode undefined-variable). Do not keep a $stage variable as it collides with the param.
  $planArtifact = Get-JsonProp $Plan "artifact_type"
  if (-not ($planArtifact -is [string]) -or $planArtifact -ne "claude_plan") { throw "artifact_type != claude_plan" }
  $planStage = Get-JsonProp $Plan "stage"
  if (-not ($planStage -is [string]) -or $planStage -ne "plan") { throw "stage != plan" }
  # enforce bool type (block "true"/1 passing via PS comparison coercion)
  $rha = Get-JsonProp $Plan "requires_human_approval"
  if (-not ($rha -is [bool]) -or $rha -ne $true) { throw "requires_human_approval != boolean true" }
  $nip = Get-JsonProp $Plan "no_implementation_performed"
  if (-not ($nip -is [bool]) -or $nip -ne $true) { throw "no_implementation_performed != boolean true" }
  # risk_level enum
  if (@("low", "medium", "high") -notcontains (Get-JsonProp $Plan "risk_level")) { throw "risk_level enum violation" }
  # non-empty string (minLength replacement)
  foreach ($sf in @("schema_version", "task_id", "summary", "rollback")) {
    $v = Get-JsonProp $Plan $sf
    if (-not ($v -is [string]) -or [string]::IsNullOrWhiteSpace($v)) { throw "$sf is not a non-empty string" }
  }
  # base_commit / task_sha256 hex (pattern replacement)
  $bc = Get-JsonProp $Plan "base_commit"
  if (-not ($bc -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($bc, '^[0-9a-f]{7,40}$')) { throw "base_commit format violation (7-40 hex)" }
  $ts = Get-JsonProp $Plan "task_sha256"
  if (-not ($ts -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($ts, '^[0-9a-f]{64}$')) { throw "task_sha256 format violation (64 hex)" }
  # string arrays: first confirm 'real array' by raw JSON (block a scalar string wrapped by @()) then each element string.
  foreach ($af in @("allowed_files", "forbidden_files", "risks", "acceptance_criteria", "required_validations")) {
    if (-not (Test-JsonArrayField $RawText $af)) { throw "$af field is not an array" }
    $val = (Get-JsonProp $Plan $af)
    foreach ($el in @($val)) {
      if ($null -eq $el) { continue }
      if (-not ($el -is [string])) { throw "$af element is not a string" }
    }
  }
  # file_changes: first confirm array by raw JSON then validate each item (reject a single object as not-an-array).
  if (-not (Test-JsonArrayField $RawText "file_changes")) { throw "file_changes field is not an array" }
  $fcVal = (Get-JsonProp $Plan "file_changes")
  foreach ($item in @($fcVal)) {
    if ($null -eq $item) { continue }
    if (-not ($item -is [System.Management.Automation.PSCustomObject])) { throw "file_changes item is not an object" }
    foreach ($n in $item.PSObject.Properties.Name) {
      if (@("path", "change") -notcontains $n) { throw "file_changes item has unexpected field: $n" }
    }
    $pp = Get-JsonProp $item "path"
    $cc = Get-JsonProp $item "change"
    if (-not ($pp -is [string]) -or [string]::IsNullOrWhiteSpace($pp)) { throw "file_changes.path is not a non-empty string" }
    if (-not ($cc -is [string]) -or [string]::IsNullOrWhiteSpace($cc)) { throw "file_changes.change is not a non-empty string" }
  }
}

# ---------- absolute path helper ----------
function Abs([string]$Rel) { return (Join-Path $RepoRoot $Rel) }

# High-confidence secret check on the checked task text (fail-closed if present). Values are not printed.
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

# Checked task: no semantic-changing silent masking. Only high-confidence secrets are fail-closed above;
# general PII like birth date/birth time/birthplace is not auto-removed (the operator must not put PII in the task).
# The artifact is named 'checked' (passed secret check) and does not guarantee PII removal. Future PII-masking extension point.
function Get-CheckedTask([string]$Text) { return $Text }

# git helper (read-only only, PS 5.1/7 common). call operator + array splat, -C to set the work tree.
# Important: git warnings on stderr (e.g. .pytest_cache permission) are native errors. With $ErrorActionPreference="Stop"
# on PS 5.1 this stderr gets promoted to NativeCommandError and aborts the script. So lower EAP=Continue only around the native
# call and restore it, and discard status stderr instead of logging it (only stdout is needed).
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
# SelfTest - without real Claude/Codex, verify Invoke-Cli's stdin write path via a dummy reader (sort) (PS 5.1/7).
# Runs before preflight/run-folder/git and exits immediately after. Not a real LLM/CLI call.
# ======================================================================
if ($SelfTest) {
  $selftestCode = 1
  $tmpOut = [System.IO.Path]::GetTempFileName()
  $tmpErr = [System.IO.Path]::GetTempFileName()
  try {
    # (a) stdin write path (dummy reader sort)
    $marker = "SELFTEST_ROUNDTRIP_OK"
    $rc = Invoke-Cli -Exe "sort" -CliArgs @() -StdinText $marker -OutLog $tmpOut -ErrLog $tmpErr
    $stdinOk = ((Read-TextNoBom $tmpOut) -match $marker)

    # Build sample envelopes with [pscustomobject] directly instead of inline JSON string + ConvertFrom-Json
    # (which is affected by PS5.1/StrictMode escaping). (Real envelope handling uses the main-flow ConvertFrom-Json path.)
    # (b) result is a pure single JSON object string -> pass
    $env1 = [pscustomobject]@{ is_error = $false; result = '{"a":1}' }
    $j1 = Resolve-ClaudePlanJson $env1
    $pureOk = ($j1 -match '"a"')

    # (c) prose+JSON mixed in result -> not extracted, BLOCK
    $env2 = [pscustomobject]@{ is_error = $false; result = 'Here is the plan: {"a":1} thanks' }
    $proseBlocked = $false
    try { [void](Resolve-ClaudePlanJson $env2) } catch { $proseBlocked = $true }

    # (d) structured_output object -> pass
    $env3 = [pscustomobject]@{ is_error = $false; structured_output = [pscustomobject]@{ b = 2 } }
    $j3 = Resolve-ClaudePlanJson $env3
    $soOk = ($j3 -match '"b"')

    # (e) is_error=true -> BLOCK
    $env4 = [pscustomobject]@{ is_error = $true; result = '{"a":1}' }
    $errBlocked = $false
    try { [void](Resolve-ClaudePlanJson $env4) } catch { $errBlocked = $true }

    # (f) Assert-ClaudePlanShape: restore raw-JSON array validation. Pass real JSON as RawText (clean JSON string).
    $zeros = ("0" * 64)
    $validRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":true}'
    $validObj = $validRaw | ConvertFrom-Json
    $validOk = $true
    try { Assert-ClaudePlanShape $validObj $validRaw } catch { $validOk = $false }

    # base_commit not hex -> reject
    $badRaw = $validRaw.Replace('"base_commit":"0000000"', '"base_commit":"NOTHEX"')
    $badObj = $badRaw | ConvertFrom-Json
    $badRejected = $false
    try { Assert-ClaudePlanShape $badObj $badRaw } catch { $badRejected = $true }

    # allowed_files is a scalar string, not an array -> reject (the core regression of this BLOCK)
    $scalarRaw = $validRaw.Replace('"allowed_files":["a"]', '"allowed_files":"a"')
    $scalarObj = $scalarRaw | ConvertFrom-Json
    $scalarRejected = $false
    try { Assert-ClaudePlanShape $scalarObj $scalarRaw } catch { $scalarRejected = $true }

    # file_changes is a single object, not an array -> reject
    $fcObjRaw = $validRaw.Replace('"file_changes":[{"path":"a","change":"edit"}]', '"file_changes":{"path":"a","change":"edit"}')
    $fcObjObj = $fcObjRaw | ConvertFrom-Json
    $fcObjRejected = $false
    try { Assert-ClaudePlanShape $fcObjObj $fcObjRaw } catch { $fcObjRejected = $true }

    # Verify that in the real path roundtrip (structured_output -> ConvertTo-Json -> file -> ConvertFrom-Json)
    # a single-element/empty array is preserved as an 'array' and passes Test-JsonArrayField (must pass so a valid plan is not broken).
    $rtJson = ($validRaw | ConvertFrom-Json) | ConvertTo-Json -Depth 30
    $rtObj = $rtJson | ConvertFrom-Json
    $roundtripOk = $true
    try { Assert-ClaudePlanShape $rtObj $rtJson } catch { $roundtripOk = $false }

    # enforce bool type: requires_human_approval as string "true" -> reject
    $rhaStrRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":"true","no_implementation_performed":true}'
    $rhaStrRejected = $false
    try { Assert-ClaudePlanShape ($rhaStrRaw | ConvertFrom-Json) $rhaStrRaw } catch { $rhaStrRejected = $true }

    # no_implementation_performed as number 1 -> reject
    $nipNumRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":1}'
    $nipNumRejected = $false
    try { Assert-ClaudePlanShape ($nipNumRaw | ConvertFrom-Json) $nipNumRaw } catch { $nipNumRejected = $true }

    # artifact_type as boolean true -> reject (string const type+value enforced)
    $artBoolRaw = '{"schema_version":"1.0","artifact_type":true,"stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":true}'
    $artBoolRejected = $false
    try { Assert-ClaudePlanShape ($artBoolRaw | ConvertFrom-Json) $artBoolRaw } catch { $artBoolRejected = $true }

    # stage as boolean true -> reject
    $stageBoolRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":true,"task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":true}'
    $stageBoolRejected = $false
    try { Assert-ClaudePlanShape ($stageBoolRaw | ConvertFrom-Json) $stageBoolRaw } catch { $stageBoolRejected = $true }

    # (g) Assert-CodexReviewShape: write each case as an independent raw JSON fixture (no Replace-derived fixtures)
    $cz = ("0" * 64)
    # valid review -> pass
    $cxValidRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $codexValidOk = $true
    try { Assert-CodexReviewShape ($cxValidRaw | ConvertFrom-Json) $cxValidRaw } catch { $codexValidOk = $false }

    # artifact_type "wrong" -> reject
    $cxBadArtRaw = '{"schema_version":"1.0","artifact_type":"wrong","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxBadArtRejected = $false
    try { Assert-CodexReviewShape ($cxBadArtRaw | ConvertFrom-Json) $cxBadArtRaw } catch { $cxBadArtRejected = $true }

    # artifact_type "codex_plan_review" (the non-canonical value codex actually emitted) -> reject (regression)
    $cxCanonRaw = '{"schema_version":"1.0","artifact_type":"codex_plan_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxCanonRejected = $false
    try { Assert-CodexReviewShape ($cxCanonRaw | ConvertFrom-Json) $cxCanonRaw } catch { $cxCanonRejected = $true }

    # reviewed_plan_sha256 bad format -> reject
    $cxBadHashRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"NOTHEX","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxBadHashRejected = $false
    try { Assert-CodexReviewShape ($cxBadHashRaw | ConvertFrom-Json) $cxBadHashRaw } catch { $cxBadHashRejected = $true }

    # blockers is a scalar string, not an array -> reject
    $cxBlkScalarRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":"x","warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxBlkScalarRejected = $false
    try { Assert-CodexReviewShape ($cxBlkScalarRaw | ConvertFrom-Json) $cxBlkScalarRaw } catch { $cxBlkScalarRejected = $true }

    # no_modification_performed false -> reject
    $cxNomodRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":false}'
    $cxNomodRejected = $false
    try { Assert-CodexReviewShape ($cxNomodRaw | ConvertFrom-Json) $cxNomodRaw } catch { $cxNomodRejected = $true }

    # no_modification_performed string "true" -> reject (bool type enforced)
    $cxNomodStrRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":"true"}'
    $cxNomodStrRejected = $false
    try { Assert-CodexReviewShape ($cxNomodStrRaw | ConvertFrom-Json) $cxNomodStrRaw } catch { $cxNomodStrRejected = $true }

    # no_modification_performed number 1 -> reject (bool type enforced)
    $cxNomodNumRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":1}'
    $cxNomodNumRejected = $false
    try { Assert-CodexReviewShape ($cxNomodNumRaw | ConvertFrom-Json) $cxNomodNumRaw } catch { $cxNomodNumRejected = $true }

    if ($stdinOk -and $pureOk -and $proseBlocked -and $soOk -and $errBlocked -and $validOk -and $badRejected -and $scalarRejected -and $fcObjRejected -and $roundtripOk -and $rhaStrRejected -and $nipNumRejected -and $artBoolRejected -and $stageBoolRejected -and $codexValidOk -and $cxBadArtRejected -and $cxCanonRejected -and $cxBadHashRejected -and $cxBlkScalarRejected -and $cxNomodRejected -and $cxNomodStrRejected -and $cxNomodNumRejected) {
      Write-PlainLine "SELFTEST=PASS stdin_roundtrip=ok envelope_pure=ok envelope_prose_blocked=ok structured_output=ok is_error_blocked=ok planshape_valid=ok planshape_bad_rejected=ok planshape_scalar_array_rejected=ok planshape_file_changes_object_rejected=ok planshape_roundtrip=ok planshape_rha_string_rejected=ok planshape_nip_number_rejected=ok planshape_artifact_bool_rejected=ok planshape_stage_bool_rejected=ok codexshape_valid=ok codexshape_bad_artifact_rejected=ok codexshape_canonical_artifact_rejected=ok codexshape_bad_hash_rejected=ok codexshape_blockers_scalar_rejected=ok codexshape_nomod_false_rejected=ok codexshape_nomod_string_rejected=ok codexshape_nomod_number_rejected=ok"
      $selftestCode = 0
    } else {
      Write-PlainLine ("SELFTEST=FAIL stdin=" + $stdinOk + " pure=" + $pureOk + " prose=" + $proseBlocked + " so=" + $soOk + " err=" + $errBlocked + " valid=" + $validOk + " bad=" + $badRejected + " scalar=" + $scalarRejected + " fcobj=" + $fcObjRejected + " rt=" + $roundtripOk + " rhastr=" + $rhaStrRejected + " nipnum=" + $nipNumRejected + " artbool=" + $artBoolRejected + " stagebool=" + $stageBoolRejected + " cxvalid=" + $codexValidOk + " cxart=" + $cxBadArtRejected + " cxcanon=" + $cxCanonRejected + " cxhash=" + $cxBadHashRejected + " cxblk=" + $cxBlkScalarRejected + " cxnomod=" + $cxNomodRejected + " cxnomodstr=" + $cxNomodStrRejected + " cxnomodnum=" + $cxNomodNumRejected)
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
# 0) command preview strings (DryRun output + human readable)
#    actual calls use the arg array, but the preview shows the canonical form.
# ======================================================================
$ClaudeCmdPreview = 'claude -p --safe-mode --permission-mode plan --output-format json --json-schema <schema-json> --tools "Read,Glob,Grep" --disallowedTools "mcp__*" --no-chrome --no-session-persistence  (stdin: prompt+policy+task)'
$CodexCmdPreview  = 'codex exec --ephemeral --sandbox read-only --output-schema ' + $CodexReviewSchema + ' -o <run>/codex-plan-review.json -   (stdin: review packet)'

# ======================================================================
# 1) PREFLIGHT (read-only, fail-closed) - before folder/LATEST
# ======================================================================
$taskAbs = if ([System.IO.Path]::IsPathRooted($Task)) { $Task } else { Abs $Task }
if (-not (Test-Path -LiteralPath $taskAbs -PathType Leaf)) {
  Stop-Fail 10 "task file missing: $Task"
}

# check existence/readability of the 6 policy files
foreach ($pf in $PolicyFiles) {
  $pfAbs = Abs $pf
  if (-not (Test-Path -LiteralPath $pfAbs -PathType Leaf)) {
    Stop-Fail 10 "policy file missing: $pf"
  }
}

# enforce clean tree (non-DryRun only)
$statusRes = Invoke-GitRead @("status", "--porcelain", "--untracked-files=all")
if ($statusRes.Code -ne 0) { Stop-Fail 10 "git status failed" }
$treeDirty = -not [string]::IsNullOrWhiteSpace($statusRes.Out)
if ((-not $DryRun) -and $treeDirty) {
  Stop-Fail 10 "work tree not clean (non-DryRun needs a clean tree). Check with DryRun or run after committing."
}

# base_commit / branch
$headRes = Invoke-GitRead @("rev-parse", "HEAD")
if ($headRes.Code -ne 0) { Stop-Fail 10 "git rev-parse HEAD failed" }
$baseCommit = $headRes.Out.Trim()
$branchRes = Invoke-GitRead @("rev-parse", "--abbrev-ref", "HEAD")
$branch = if ($branchRes.Code -eq 0) { $branchRes.Out.Trim() } else { "unknown" }

# check CLI presence
$claudeCmd = Get-Command "claude" -ErrorAction SilentlyContinue
$codexCmd  = Get-Command "codex" -ErrorAction SilentlyContinue
if (-not $DryRun) {
  if ($null -eq $claudeCmd) { Stop-Fail 10 "claude CLI missing" }
  if ($null -eq $codexCmd)  { Stop-Fail 10 "codex CLI missing" }
}
$claudeVersion = "unknown"
$codexVersion  = "unknown"
if ($null -ne $claudeCmd) {
  try { $claudeVersion = (& claude --version 2>$null | Out-String).Trim() } catch { $claudeVersion = "unknown" }
}
if ($null -ne $codexCmd) {
  try { $codexVersion = (& codex --version 2>$null | Out-String).Trim() } catch { $codexVersion = "unknown" }
}

# read task + secret check + checked + hash (in memory; file write after folder creation)
$rawTask = Read-TextNoBom $taskAbs
if (Test-HighConfidenceSecret $rawTask) {
  Stop-Fail 10 "high-confidence secret pattern found - remove from task and re-run (value not printed)."
}
$checkedTask = Get-CheckedTask $rawTask
$taskSha = Get-Sha256OfText $checkedTask

# schema validity for both (parse check) - also checked in DryRun.
# --json-schema is a JSON string argument, not a file path (claude -p --help). To reduce newline/quote
# damage in PS 5.1 native args, serialize to compact (minified) JSON to pass (not a switch to file path).
$claudeSchemaRaw = Read-TextNoBom (Abs $ClaudePlanSchema)
$codexSchemaText = Read-TextNoBom (Abs $CodexReviewSchema)
$claudeSchemaObj = $null
try { $claudeSchemaObj = $claudeSchemaRaw | ConvertFrom-Json } catch { Stop-Fail 10 "claude-plan.schema.json parse failed" }
try { [void]($codexSchemaText | ConvertFrom-Json) } catch { Stop-Fail 10 "codex-plan-review.schema.json parse failed" }
$claudeSchemaJson = $claudeSchemaObj | ConvertTo-Json -Depth 30 -Compress

# ======================================================================
# DryRun branch - no real call, no runtime artifacts
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
  # DryRun CLI check is a best-effort display only (hard failure is in non-DryRun). For reference before a real run.
  Write-PlainLine ("cli_check(best-effort): claude=" + $claudePresent + " codex=" + $codexPresent)
  Write-PlainLine "no_runtime_output_written=true (no run folder, no LATEST.txt, no logs, no manifest)"
  exit 0
}

# ======================================================================
# 2) After PREFLIGHT passes - create the run folder (first write happens here)
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

# LATEST.txt - record relative path
$latestPath = Join-Path $currentDir "LATEST.txt"
Write-TextNoBom $latestPath ("handoff/current/" + $runId)

# ======================================================================
# 3) assemble policy packet (6 files only)
# ======================================================================
$policyParts = @()
foreach ($pf in $PolicyFiles) {
  $content = Read-TextNoBom (Abs $pf)
  $policyParts += ("===== POLICY FILE: " + $pf + " =====`n" + $content)
}
$policyPacket = [string]::Join("`n`n", $policyParts)
$policySha = Get-Sha256OfText $policyPacket

# log/artifact paths
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
# 4) STAGE 1 - Claude Plan (safe-mode isolation, long context via stdin)
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
  # Map Invoke-Cli internal exceptions (process start/stdin/read failure etc.) to a harness exit code (prevent exit 1 leak).
  Stop-Fail 11 ("Claude call exception: " + $_.Exception.Message)
}
if ($claudeExit -ne 0) { Stop-Fail 11 "Claude execution failed(exit=$claudeExit)" }

# Claude response: handle read/save/parse all fail-closed (no PowerShell exception leaks as exit 1; use Stop-Fail 12).
if (-not (Test-Path -LiteralPath $claudeOut -PathType Leaf)) { Stop-Fail 12 "claude-stdout.log missing" }
$claudeOutLen = (Get-Item -LiteralPath $claudeOut).Length
if ($claudeOutLen -le 0) { Stop-Fail 12 "claude-stdout.log empty (Claude no output)" }

# pre-declare then read in try/catch (prevent StrictMode undefined-variable crash).
$claudeRespText = $null
try { $claudeRespText = Read-TextNoBom $claudeOut } catch { Stop-Fail 12 ("Claude response read failed: " + $_.Exception.Message) }
if ([string]::IsNullOrEmpty($claudeRespText)) { Stop-Fail 12 "Claude response text empty" }
try { Write-TextNoBom $claudeRespPath $claudeRespText } catch { Stop-Fail 12 ("claude-response.json write failed: " + $_.Exception.Message) }

$envelope = $null
try { $envelope = $claudeRespText | ConvertFrom-Json } catch { Stop-Fail 12 ("Claude envelope JSON parse failed: " + $_.Exception.Message) }
if ($null -eq $envelope) { Stop-Fail 12 "Claude envelope empty" }

# Prefer structured_output; otherwise use result only when it is a 'single JSON object' (prose/markdown mixed in = BLOCK). No arbitrary substring extraction.
$planJson = $null
try { $planJson = Resolve-ClaudePlanJson $envelope } catch { Stop-Fail 12 ("Claude response processing BLOCK: " + $_.Exception.Message) }
try { Write-TextNoBom $claudePlanPath $planJson } catch { Stop-Fail 12 ("claude-plan.json write failed: " + $_.Exception.Message) }
$planSha = Get-Sha256OfText (Read-TextNoBom $claudePlanPath)

# ======================================================================
# 5) Before Codex call - directly compare hashes inside the Claude plan (fail-closed)
# ======================================================================
$planRaw = Read-TextNoBom $claudePlanPath
$planObj = $null
try { $planObj = $planRaw | ConvertFrom-Json } catch { Stop-Fail 12 "claude-plan.json parse failed" }
try { Assert-ClaudePlanShape $planObj $planRaw } catch { Stop-Fail 12 ("Claude plan validation failed: " + $_.Exception.Message) }
$planBase = Get-JsonProp $planObj "base_commit"
$planTaskSha = Get-JsonProp $planObj "task_sha256"
if ($planBase -ne $baseCommit) { Stop-Fail 14 "Claude plan base_commit mismatch (blocked before Codex call)" }
if ($planTaskSha -ne $taskSha) { Stop-Fail 14 "Claude plan task_sha256 mismatch (blocked before Codex call)" }

# ======================================================================
# 6) STAGE 2 - Codex Plan Review (read-only, stdin packet)
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
  Stop-Fail 13 ("Codex call exception: " + $_.Exception.Message)
}
if ($codexExit -ne 0) { Stop-Fail 13 "Codex execution failed(exit=$codexExit)" }

# PS parses/validates the -o output directly (does not rely on CLI validation)
if (-not (Test-Path -LiteralPath $codexReviewPath -PathType Leaf)) {
  Stop-Fail 14 "Codex result file not created: codex-plan-review.json"
}
$codexRaw = Read-TextNoBom $codexReviewPath
$review = $null
try { $review = $codexRaw | ConvertFrom-Json } catch { Stop-Fail 14 "codex-plan-review.json parse failed" }
# schema-level validation (required fields/const/enum/hex/array/extra-field block). Prevent a bypass where only hashes match.
try { Assert-CodexReviewShape $review $codexRaw } catch { Stop-Fail 14 ("Codex result validation failed: " + $_.Exception.Message) }

$verdict = Get-JsonProp $review "verdict"
$revPlanSha = Get-JsonProp $review "reviewed_plan_sha256"
$revTaskSha = Get-JsonProp $review "reviewed_task_sha256"
$revBase = Get-JsonProp $review "checked_base_commit"

# re-compare hash/base_commit
if ($revPlanSha -ne $planSha) { Stop-Fail 14 "reviewed_plan_sha256 mismatch" }
if ($revTaskSha -ne $taskSha) { Stop-Fail 14 "reviewed_task_sha256 mismatch" }
if ($revBase -ne $baseCommit) { Stop-Fail 14 "checked_base_commit mismatch" }

# ======================================================================
# 7) Verdict & manifest
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
