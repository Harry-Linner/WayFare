#requires -Version 5.1
param(
  [switch]$CheckRuntime
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "wayfare_backend"
$FrontendEnv = Join-Path $Root ".env"
$AIEnv = Join-Path $Root "wayfare_ai_backend\.env"
$PythonExe = Join-Path $Root "wayfare_ai_backend\.venv\Scripts\python.exe"
$BackendHealth = "http://127.0.0.1:8080/healthz"
$ProfileUrl = "http://127.0.0.1:8080/profiles/global"
$FrontendUrl = "http://127.0.0.1:4321/dashboard"

$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
  param(
    [string]$Name,
    [string]$Status,
    [string]$Detail
  )

  $results.Add([pscustomobject]@{
    Name   = $Name
    Status = $Status
    Detail = $Detail
  }) | Out-Null
}

function Test-CommandExists {
  param([string]$CommandName)
  try {
    $resolved = Get-Command $CommandName -ErrorAction Stop
    return $resolved.Source
  } catch {
    return $null
  }
}

$goPath = Test-CommandExists "go"
if ($goPath) {
  Add-Result "Go" "OK" $goPath
} else {
  Add-Result "Go" "FAIL" "go 命令不可用"
}

$npmPath = Test-CommandExists "npm.cmd"
if ($npmPath) {
  Add-Result "npm" "OK" $npmPath
} else {
  Add-Result "npm" "FAIL" "npm.cmd 不可用"
}

if (Test-Path $PythonExe) {
  Add-Result "Python Sidecar" "OK" $PythonExe
} else {
  Add-Result "Python Sidecar" "FAIL" "wayfare_ai_backend/.venv/Scripts/python.exe 不存在"
}

if (Test-Path $FrontendEnv) {
  Add-Result "Frontend .env" "OK" $FrontendEnv
} else {
  Add-Result "Frontend .env" "WARN" ".env 不存在"
}

if (Test-Path $AIEnv) {
  Add-Result "AI .env" "OK" $AIEnv
} else {
  Add-Result "AI .env" "WARN" "wayfare_ai_backend/.env 不存在"
}

if ($CheckRuntime) {
  try {
    $health = Invoke-RestMethod -Uri $BackendHealth -TimeoutSec 5
    if ($health.status -eq "ok") {
      Add-Result "Backend Health" "OK" ($health | ConvertTo-Json -Compress)
    } else {
      Add-Result "Backend Health" "FAIL" "healthz 返回非 ok"
    }
  } catch {
    Add-Result "Backend Health" "FAIL" "无法访问 $BackendHealth"
  }

  try {
    $frontend = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -TimeoutSec 5
    if ($frontend.StatusCode -ge 200 -and $frontend.StatusCode -lt 400) {
      Add-Result "Frontend Runtime" "OK" $FrontendUrl
    } else {
      Add-Result "Frontend Runtime" "FAIL" "前端返回状态码 $($frontend.StatusCode)"
    }
  } catch {
    Add-Result "Frontend Runtime" "FAIL" "无法访问 $FrontendUrl"
  }

  try {
    $profile = Invoke-RestMethod -Uri $ProfileUrl -TimeoutSec 5
    if ($profile.profile.scope -eq "global") {
      Add-Result "Profile API" "OK" $ProfileUrl
    } else {
      Add-Result "Profile API" "FAIL" "profiles/global returned an unexpected payload"
    }
  } catch {
    Add-Result "Profile API" "FAIL" "unable to reach $ProfileUrl"
  }
}

$results | Format-Table -AutoSize

$hasFailure = $results | Where-Object { $_.Status -eq "FAIL" }
if ($hasFailure) {
  exit 1
}

exit 0
