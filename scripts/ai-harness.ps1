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

# Claude envelope에서 계획 JSON '텍스트'를 안전 추출한다. structured_output 객체 우선, 없으면 result가
# '단일 JSON 객체 문자열'일 때만 사용. prose/markdown/설명 혼입은 추출하지 않고 throw(BLOCK) — 호출부가 Stop-Fail 12.
# 단일원소 배열 unwrap을 피하려고 result-string 경로는 원문 텍스트를 그대로 반환한다.
function Resolve-ClaudePlanJson {
  param([object]$Envelope)
  if ($null -eq $Envelope) { throw "envelope null" }
  $isErr = Get-JsonProp $Envelope "is_error"
  if ($isErr -eq $true) { throw "is_error=true (Claude 성공 응답 아님)" }
  $structured = Get-JsonProp $Envelope "structured_output"
  if ($null -ne $structured -and ($structured -is [System.Management.Automation.PSCustomObject])) {
    return ($structured | ConvertTo-Json -Depth 30)
  }
  $result = Get-JsonProp $Envelope "result"
  if ($null -eq $result) { throw "structured_output/result 없음" }
  if ($result -is [System.Management.Automation.PSCustomObject]) {
    return ($result | ConvertTo-Json -Depth 30)
  }
  if ($result -is [string]) {
    $rs = $result.Trim()
    # 순수 단일 JSON 객체만 허용: 반드시 '{'로 시작·'}'로 끝나야 함(prose/마크다운펜스/앞뒤텍스트 차단).
    if (-not ($rs.StartsWith("{") -and $rs.EndsWith("}"))) {
      throw "result가 단일 JSON 객체가 아님(prose/markdown 혼입) — BLOCK"
    }
    $probe = $null
    try { $probe = $rs | ConvertFrom-Json } catch { throw "result JSON 파싱 실패 — BLOCK" }
    if (-not ($probe -is [System.Management.Automation.PSCustomObject])) { throw "result가 JSON 객체 아님 — BLOCK" }
    return $rs
  }
  throw "result 형식 불명 — BLOCK"
}

# Codex 결과를 schema 수준으로 검증한다. 생성용 schema는 Codex --output-schema 호환을 위해 단순화했으므로
# 제거한 엄격 제약(hex·const·배열성·요소 타입)을 전부 여기서 강제한다. 위반 시 throw -> 호출부 Stop-Fail 14.
function Assert-CodexReviewShape {
  param([object]$Review, [string]$RawText)
  $required = @(
    "schema_version", "artifact_type", "review_stage", "review_target", "checked_base_commit",
    "reviewed_task_sha256", "reviewed_plan_sha256", "verdict", "blockers", "warnings", "evidence",
    "allowed_files", "forbidden_files", "required_validations", "no_modification_performed"
  )
  # 필수 필드 전체 존재(빈 배열이 null로 와도 property 존재로 판정)
  foreach ($f in $required) {
    if ($null -eq $Review.PSObject.Properties[$f]) { throw "필수 필드 누락: $f" }
  }
  # 허용 외 추가 필드 금지
  foreach ($p in $Review.PSObject.Properties.Name) {
    if ($required -notcontains $p) { throw "허용 외 추가 필드: $p" }
  }
  # const 대체(type+value를 함께 검증 — 방어적)
  $artifact = Get-JsonProp $Review "artifact_type"
  if (-not ($artifact -is [string]) -or $artifact -ne "codex_review") { throw "artifact_type != codex_review" }
  $rstage = Get-JsonProp $Review "review_stage"
  if (-not ($rstage -is [string]) -or $rstage -ne "plan") { throw "review_stage != plan" }
  $rtarget = Get-JsonProp $Review "review_target"
  if (-not ($rtarget -is [string]) -or $rtarget -ne "claude-plan.json") { throw "review_target != claude-plan.json" }
  # bool 타입 강제(PS 비교 변환으로 "true"/1 이 통과하는 것 차단)
  $nomod = Get-JsonProp $Review "no_modification_performed"
  if (-not ($nomod -is [bool]) -or $nomod -ne $true) { throw "no_modification_performed != boolean true" }
  # verdict enum
  if (@("APPROVE", "BLOCK") -notcontains (Get-JsonProp $Review "verdict")) { throw "verdict enum 위반" }
  # schema_version 비어있지 않은 string
  $sv = Get-JsonProp $Review "schema_version"
  if (-not ($sv -is [string]) -or [string]::IsNullOrWhiteSpace($sv)) { throw "schema_version 비어있지 않은 문자열 아님" }
  # hex (pattern 대체)
  $cb = Get-JsonProp $Review "checked_base_commit"
  if (-not ($cb -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($cb, '^[0-9a-f]{7,40}$')) { throw "checked_base_commit 형식 위반(7~40 hex)" }
  foreach ($hf in @("reviewed_task_sha256", "reviewed_plan_sha256")) {
    $hv = Get-JsonProp $Review $hf
    if (-not ($hv -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($hv, '^[0-9a-f]{64}$')) { throw "$hf 형식 위반(64 hex)" }
  }
  # 배열들: raw JSON 기준 '진짜 배열' 확인(스칼라 @() 감싸기 차단) 후 각 요소 string
  foreach ($af in @("blockers", "warnings", "evidence", "allowed_files", "forbidden_files", "required_validations")) {
    if (-not (Test-JsonArrayField $RawText $af)) { throw "$af 필드가 배열이 아님" }
    $val = (Get-JsonProp $Review $af)
    foreach ($el in @($val)) {
      if ($null -eq $el) { continue }
      if (-not ($el -is [string])) { throw "$af 요소가 문자열이 아님" }
    }
  }
}

# Claude plan을 schema 수준으로 검증한다. 생성용 schema는 structured_output 생성을 위해 단순화했으므로
# 제거한 엄격 제약(hex·const·비어있지 않은 string·배열 요소 타입·file_changes item)을 전부 여기서 강제한다.
# 위반 시 throw -> 호출부 try/catch가 Stop-Fail 12로 매핑(self-test 가능하도록 Stop-Fail 직접 호출하지 않음).
function Assert-ClaudePlanShape {
  param([object]$Plan, [string]$RawText)
  $required = @(
    "schema_version", "artifact_type", "stage", "task_id", "base_commit", "task_sha256", "summary",
    "risk_level", "allowed_files", "forbidden_files", "file_changes", "risks", "acceptance_criteria",
    "required_validations", "rollback", "requires_human_approval", "no_implementation_performed"
  )
  # 필수 필드 전체 존재(빈 배열이 null로 와도 property 존재로 판정)
  foreach ($f in $required) {
    if ($null -eq $Plan.PSObject.Properties[$f]) { throw "필수 필드 누락: $f" }
  }
  # 허용 외 추가 필드 금지
  foreach ($p in $Plan.PSObject.Properties.Name) {
    if ($required -notcontains $p) { throw "허용 외 추가 필드: $p" }
  }
  # const 대체
  # 변수 미사용으로 인라인 호출(StrictMode 즉석 변수 미정의 회피). $stage 등은 param과 충돌하므로 변수 자체를 두지 않음.
  $planArtifact = Get-JsonProp $Plan "artifact_type"
  if (-not ($planArtifact -is [string]) -or $planArtifact -ne "claude_plan") { throw "artifact_type != claude_plan" }
  $planStage = Get-JsonProp $Plan "stage"
  if (-not ($planStage -is [string]) -or $planStage -ne "plan") { throw "stage != plan" }
  # bool 타입 강제(PS 비교 변환으로 "true"/1 이 통과하는 것 차단)
  $rha = Get-JsonProp $Plan "requires_human_approval"
  if (-not ($rha -is [bool]) -or $rha -ne $true) { throw "requires_human_approval != boolean true" }
  $nip = Get-JsonProp $Plan "no_implementation_performed"
  if (-not ($nip -is [bool]) -or $nip -ne $true) { throw "no_implementation_performed != boolean true" }
  # risk_level enum
  if (@("low", "medium", "high") -notcontains (Get-JsonProp $Plan "risk_level")) { throw "risk_level enum 위반" }
  # 비어 있지 않은 string (minLength 대체)
  foreach ($sf in @("schema_version", "task_id", "summary", "rollback")) {
    $v = Get-JsonProp $Plan $sf
    if (-not ($v -is [string]) -or [string]::IsNullOrWhiteSpace($v)) { throw "$sf 가 비어있지 않은 문자열이 아님" }
  }
  # base_commit / task_sha256 hex (pattern 대체)
  $bc = Get-JsonProp $Plan "base_commit"
  if (-not ($bc -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($bc, '^[0-9a-f]{7,40}$')) { throw "base_commit 형식 위반(7~40 hex)" }
  $ts = Get-JsonProp $Plan "task_sha256"
  if (-not ($ts -is [string]) -or -not [System.Text.RegularExpressions.Regex]::IsMatch($ts, '^[0-9a-f]{64}$')) { throw "task_sha256 형식 위반(64 hex)" }
  # string 배열들: raw JSON 기준 '진짜 배열'인지 먼저 확인(스칼라 문자열이 @()로 감싸져 통과하는 것 차단) 후 각 요소 string.
  foreach ($af in @("allowed_files", "forbidden_files", "risks", "acceptance_criteria", "required_validations")) {
    if (-not (Test-JsonArrayField $RawText $af)) { throw "$af 필드가 배열이 아님" }
    $val = (Get-JsonProp $Plan $af)
    foreach ($el in @($val)) {
      if ($null -eq $el) { continue }
      if (-not ($el -is [string])) { throw "$af 요소가 문자열이 아님" }
    }
  }
  # file_changes: raw JSON 기준 배열인지 먼저 확인한 뒤 각 item 검증(객체 하나만 와도 배열 아님으로 거부).
  if (-not (Test-JsonArrayField $RawText "file_changes")) { throw "file_changes 필드가 배열이 아님" }
  $fcVal = (Get-JsonProp $Plan "file_changes")
  foreach ($item in @($fcVal)) {
    if ($null -eq $item) { continue }
    if (-not ($item -is [System.Management.Automation.PSCustomObject])) { throw "file_changes item이 객체가 아님" }
    foreach ($n in $item.PSObject.Properties.Name) {
      if (@("path", "change") -notcontains $n) { throw "file_changes item 허용 외 필드: $n" }
    }
    $pp = Get-JsonProp $item "path"
    $cc = Get-JsonProp $item "change"
    if (-not ($pp -is [string]) -or [string]::IsNullOrWhiteSpace($pp)) { throw "file_changes.path 비어있지 않은 문자열 아님" }
    if (-not ($cc -is [string]) -or [string]::IsNullOrWhiteSpace($cc)) { throw "file_changes.change 비어있지 않은 문자열 아님" }
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
    # (a) stdin write 경로(dummy reader sort)
    $marker = "SELFTEST_ROUNDTRIP_OK"
    $rc = Invoke-Cli -Exe "sort" -CliArgs @() -StdinText $marker -OutLog $tmpOut -ErrLog $tmpErr
    $stdinOk = ((Read-TextNoBom $tmpOut) -match $marker)

    # 샘플 envelope은 inline JSON string+ConvertFrom-Json(PS5.1/StrictMode escaping 영향) 대신
    # [pscustomobject]로 직접 구성한다. (실 envelope 처리는 메인 흐름의 ConvertFrom-Json 경로로 동작)
    # (b) result가 순수 단일 JSON 객체 문자열 -> 통과
    $env1 = [pscustomobject]@{ is_error = $false; result = '{"a":1}' }
    $j1 = Resolve-ClaudePlanJson $env1
    $pureOk = ($j1 -match '"a"')

    # (c) result에 prose+JSON 혼입 -> 추출하지 않고 BLOCK
    $env2 = [pscustomobject]@{ is_error = $false; result = 'Here is the plan: {"a":1} thanks' }
    $proseBlocked = $false
    try { [void](Resolve-ClaudePlanJson $env2) } catch { $proseBlocked = $true }

    # (d) structured_output 객체 -> 통과
    $env3 = [pscustomobject]@{ is_error = $false; structured_output = [pscustomobject]@{ b = 2 } }
    $j3 = Resolve-ClaudePlanJson $env3
    $soOk = ($j3 -match '"b"')

    # (e) is_error=true -> BLOCK
    $env4 = [pscustomobject]@{ is_error = $true; result = '{"a":1}' }
    $errBlocked = $false
    try { [void](Resolve-ClaudePlanJson $env4) } catch { $errBlocked = $true }

    # (f) Assert-ClaudePlanShape: raw JSON 기준 배열 검증 회복. RawText로 실제 JSON을 넘긴다(clean JSON string).
    $zeros = ("0" * 64)
    $validRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":true}'
    $validObj = $validRaw | ConvertFrom-Json
    $validOk = $true
    try { Assert-ClaudePlanShape $validObj $validRaw } catch { $validOk = $false }

    # base_commit가 hex 아님 -> 거부
    $badRaw = $validRaw.Replace('"base_commit":"0000000"', '"base_commit":"NOTHEX"')
    $badObj = $badRaw | ConvertFrom-Json
    $badRejected = $false
    try { Assert-ClaudePlanShape $badObj $badRaw } catch { $badRejected = $true }

    # allowed_files가 배열이 아니라 스칼라 문자열 -> 거부(이번 BLOCK의 핵심 회귀)
    $scalarRaw = $validRaw.Replace('"allowed_files":["a"]', '"allowed_files":"a"')
    $scalarObj = $scalarRaw | ConvertFrom-Json
    $scalarRejected = $false
    try { Assert-ClaudePlanShape $scalarObj $scalarRaw } catch { $scalarRejected = $true }

    # file_changes가 배열이 아니라 객체 하나 -> 거부
    $fcObjRaw = $validRaw.Replace('"file_changes":[{"path":"a","change":"edit"}]', '"file_changes":{"path":"a","change":"edit"}')
    $fcObjObj = $fcObjRaw | ConvertFrom-Json
    $fcObjRejected = $false
    try { Assert-ClaudePlanShape $fcObjObj $fcObjRaw } catch { $fcObjRejected = $true }

    # 실제 경로 라운드트립(structured_output -> ConvertTo-Json -> 파일 -> ConvertFrom-Json)에서
    # 단일원소/빈 배열이 '배열'로 보존되어 Test-JsonArrayField를 통과하는지 실측(통과해야 정상 plan을 안 깬다).
    $rtJson = ($validRaw | ConvertFrom-Json) | ConvertTo-Json -Depth 30
    $rtObj = $rtJson | ConvertFrom-Json
    $roundtripOk = $true
    try { Assert-ClaudePlanShape $rtObj $rtJson } catch { $roundtripOk = $false }

    # bool 타입 강제: requires_human_approval가 string "true" -> 거부
    $rhaStrRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":"true","no_implementation_performed":true}'
    $rhaStrRejected = $false
    try { Assert-ClaudePlanShape ($rhaStrRaw | ConvertFrom-Json) $rhaStrRaw } catch { $rhaStrRejected = $true }

    # no_implementation_performed가 number 1 -> 거부
    $nipNumRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":1}'
    $nipNumRejected = $false
    try { Assert-ClaudePlanShape ($nipNumRaw | ConvertFrom-Json) $nipNumRaw } catch { $nipNumRejected = $true }

    # artifact_type 가 boolean true -> 거부(string const 타입+값 강제)
    $artBoolRaw = '{"schema_version":"1.0","artifact_type":true,"stage":"plan","task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":true}'
    $artBoolRejected = $false
    try { Assert-ClaudePlanShape ($artBoolRaw | ConvertFrom-Json) $artBoolRaw } catch { $artBoolRejected = $true }

    # stage 가 boolean true -> 거부
    $stageBoolRaw = '{"schema_version":"1.0","artifact_type":"claude_plan","stage":true,"task_id":"t1","base_commit":"0000000","task_sha256":"' + $zeros + '","summary":"s","risk_level":"low","allowed_files":["a"],"forbidden_files":["b"],"file_changes":[{"path":"a","change":"edit"}],"risks":[],"acceptance_criteria":["ok"],"required_validations":["test"],"rollback":"revert","requires_human_approval":true,"no_implementation_performed":true}'
    $stageBoolRejected = $false
    try { Assert-ClaudePlanShape ($stageBoolRaw | ConvertFrom-Json) $stageBoolRaw } catch { $stageBoolRejected = $true }

    # (g) Assert-CodexReviewShape: 각 케이스를 독립 raw JSON fixture로 명시 작성(Replace 파생 금지)
    $cz = ("0" * 64)
    # 정상 review -> 통과
    $cxValidRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $codexValidOk = $true
    try { Assert-CodexReviewShape ($cxValidRaw | ConvertFrom-Json) $cxValidRaw } catch { $codexValidOk = $false }

    # artifact_type 가 "wrong" -> 거부
    $cxBadArtRaw = '{"schema_version":"1.0","artifact_type":"wrong","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxBadArtRejected = $false
    try { Assert-CodexReviewShape ($cxBadArtRaw | ConvertFrom-Json) $cxBadArtRaw } catch { $cxBadArtRejected = $true }

    # reviewed_plan_sha256 형식 불량 -> 거부
    $cxBadHashRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"NOTHEX","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxBadHashRejected = $false
    try { Assert-CodexReviewShape ($cxBadHashRaw | ConvertFrom-Json) $cxBadHashRaw } catch { $cxBadHashRejected = $true }

    # blockers 가 배열이 아니라 스칼라 문자열 -> 거부
    $cxBlkScalarRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":"x","warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":true}'
    $cxBlkScalarRejected = $false
    try { Assert-CodexReviewShape ($cxBlkScalarRaw | ConvertFrom-Json) $cxBlkScalarRaw } catch { $cxBlkScalarRejected = $true }

    # no_modification_performed 가 false -> 거부
    $cxNomodRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":false}'
    $cxNomodRejected = $false
    try { Assert-CodexReviewShape ($cxNomodRaw | ConvertFrom-Json) $cxNomodRaw } catch { $cxNomodRejected = $true }

    # no_modification_performed 가 string "true" -> 거부(bool 타입 강제)
    $cxNomodStrRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":"true"}'
    $cxNomodStrRejected = $false
    try { Assert-CodexReviewShape ($cxNomodStrRaw | ConvertFrom-Json) $cxNomodStrRaw } catch { $cxNomodStrRejected = $true }

    # no_modification_performed 가 number 1 -> 거부(bool 타입 강제)
    $cxNomodNumRaw = '{"schema_version":"1.0","artifact_type":"codex_review","review_stage":"plan","review_target":"claude-plan.json","checked_base_commit":"0000000","reviewed_task_sha256":"' + $cz + '","reviewed_plan_sha256":"' + $cz + '","verdict":"APPROVE","blockers":[],"warnings":[],"evidence":["ok"],"allowed_files":["a"],"forbidden_files":["b"],"required_validations":["test"],"no_modification_performed":1}'
    $cxNomodNumRejected = $false
    try { Assert-CodexReviewShape ($cxNomodNumRaw | ConvertFrom-Json) $cxNomodNumRaw } catch { $cxNomodNumRejected = $true }

    if ($stdinOk -and $pureOk -and $proseBlocked -and $soOk -and $errBlocked -and $validOk -and $badRejected -and $scalarRejected -and $fcObjRejected -and $roundtripOk -and $rhaStrRejected -and $nipNumRejected -and $artBoolRejected -and $stageBoolRejected -and $codexValidOk -and $cxBadArtRejected -and $cxBadHashRejected -and $cxBlkScalarRejected -and $cxNomodRejected -and $cxNomodStrRejected -and $cxNomodNumRejected) {
      Write-PlainLine "SELFTEST=PASS stdin_roundtrip=ok envelope_pure=ok envelope_prose_blocked=ok structured_output=ok is_error_blocked=ok planshape_valid=ok planshape_bad_rejected=ok planshape_scalar_array_rejected=ok planshape_file_changes_object_rejected=ok planshape_roundtrip=ok planshape_rha_string_rejected=ok planshape_nip_number_rejected=ok planshape_artifact_bool_rejected=ok planshape_stage_bool_rejected=ok codexshape_valid=ok codexshape_bad_artifact_rejected=ok codexshape_bad_hash_rejected=ok codexshape_blockers_scalar_rejected=ok codexshape_nomod_false_rejected=ok codexshape_nomod_string_rejected=ok codexshape_nomod_number_rejected=ok"
      $selftestCode = 0
    } else {
      Write-PlainLine ("SELFTEST=FAIL stdin=" + $stdinOk + " pure=" + $pureOk + " prose=" + $proseBlocked + " so=" + $soOk + " err=" + $errBlocked + " valid=" + $validOk + " bad=" + $badRejected + " scalar=" + $scalarRejected + " fcobj=" + $fcObjRejected + " rt=" + $roundtripOk + " rhastr=" + $rhaStrRejected + " nipnum=" + $nipNumRejected + " artbool=" + $artBoolRejected + " stagebool=" + $stageBoolRejected + " cxvalid=" + $codexValidOk + " cxart=" + $cxBadArtRejected + " cxhash=" + $cxBadHashRejected + " cxblk=" + $cxBlkScalarRejected + " cxnomod=" + $cxNomodRejected + " cxnomodstr=" + $cxNomodStrRejected + " cxnomodnum=" + $cxNomodNumRejected)
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

# Claude 응답: 읽기/저장/파싱을 전부 fail-closed로 처리(어떤 PowerShell 예외도 exit 1로 새지 않고 Stop-Fail 12).
if (-not (Test-Path -LiteralPath $claudeOut -PathType Leaf)) { Stop-Fail 12 "claude-stdout.log 없음" }
$claudeOutLen = (Get-Item -LiteralPath $claudeOut).Length
if ($claudeOutLen -le 0) { Stop-Fail 12 "claude-stdout.log 비어 있음(Claude 무출력)" }

# pre-declare 후 try/catch로 읽는다(StrictMode 즉석 변수 미정의 크래시 방지).
$claudeRespText = $null
try { $claudeRespText = Read-TextNoBom $claudeOut } catch { Stop-Fail 12 ("Claude 응답 읽기 실패: " + $_.Exception.Message) }
if ([string]::IsNullOrEmpty($claudeRespText)) { Stop-Fail 12 "Claude 응답 텍스트 비어 있음" }
try { Write-TextNoBom $claudeRespPath $claudeRespText } catch { Stop-Fail 12 ("claude-response.json 저장 실패: " + $_.Exception.Message) }

$envelope = $null
try { $envelope = $claudeRespText | ConvertFrom-Json } catch { Stop-Fail 12 ("Claude envelope JSON 파싱 실패: " + $_.Exception.Message) }
if ($null -eq $envelope) { Stop-Fail 12 "Claude envelope 비어 있음" }

# structured_output 우선, 없으면 result가 '단일 JSON 객체'일 때만 사용(prose/markdown 혼입은 BLOCK). 임의 substring 추출 금지.
$planJson = $null
try { $planJson = Resolve-ClaudePlanJson $envelope } catch { Stop-Fail 12 ("Claude 응답 처리 BLOCK: " + $_.Exception.Message) }
try { Write-TextNoBom $claudePlanPath $planJson } catch { Stop-Fail 12 ("claude-plan.json 저장 실패: " + $_.Exception.Message) }
$planSha = Get-Sha256OfText (Read-TextNoBom $claudePlanPath)

# ======================================================================
# 5) Codex 호출 전 — Claude plan 내부 해시 직접 대조 (fail-closed)
# ======================================================================
$planRaw = Read-TextNoBom $claudePlanPath
$planObj = $null
try { $planObj = $planRaw | ConvertFrom-Json } catch { Stop-Fail 12 "claude-plan.json 파싱 실패" }
try { Assert-ClaudePlanShape $planObj $planRaw } catch { Stop-Fail 12 ("Claude plan 검증 실패: " + $_.Exception.Message) }
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
# schema 수준 검증(필수 필드·const·enum·hex·배열·추가필드 차단). 해시만 맞으면 통과하는 우회 방지.
try { Assert-CodexReviewShape $review $codexRaw } catch { Stop-Fail 14 ("Codex 결과 검증 실패: " + $_.Exception.Message) }

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
