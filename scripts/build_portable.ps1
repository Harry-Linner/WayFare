param(
  [string]$Version = "0.1.0"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "wayfare_backend"
$AIBackendDir = Join-Path $Root "wayfare_ai_backend"
$ReleaseRoot = Join-Path $Root "release"
$BundleDir = Join-Path $ReleaseRoot "WayFare-MVP-Portable"
$ZipPath = Join-Path $ReleaseRoot ("WayFare-MVP-Portable-v{0}.zip" -f $Version)

New-Item -ItemType Directory -Force $ReleaseRoot | Out-Null
if (Test-Path $BundleDir) {
  Remove-Item $BundleDir -Recurse -Force
}
New-Item -ItemType Directory -Force $BundleDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleDir "data") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleDir "logs") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BundleDir "uploads") | Out-Null
Set-Content -Path (Join-Path $BundleDir "data\.keep") -Value "" -Encoding UTF8
Set-Content -Path (Join-Path $BundleDir "logs\.keep") -Value "" -Encoding UTF8
Set-Content -Path (Join-Path $BundleDir "uploads\.keep") -Value "" -Encoding UTF8

$env:GOCACHE = Join-Path $BackendDir ".gocache"
$env:GOMODCACHE = Join-Path $BackendDir ".gomodcache"
New-Item -ItemType Directory -Force $env:GOCACHE, $env:GOMODCACHE | Out-Null

Push-Location $BackendDir
try {
  & go build -o (Join-Path $BundleDir "WayFare.exe") .
}
finally {
  Pop-Location
}

$AIBackendBundleDir = Join-Path $BundleDir "wayfare_ai_backend"
New-Item -ItemType Directory -Force $AIBackendBundleDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $AIBackendBundleDir "data") | Out-Null

$AIArtifacts = @(
  '.venv',
  'ipc_main.py',
  'config.py',
  'context_builder.py',
  'database.py',
  'document_parser.py',
  'embedding_provider.py',
  'llm_provider.py',
  'services.py',
  'requirements.txt',
  '.env'
)

foreach ($artifact in $AIArtifacts) {
  $source = Join-Path $AIBackendDir $artifact
  if (Test-Path $source) {
    Copy-Item $source (Join-Path $AIBackendBundleDir $artifact) -Recurse -Force
  }
}

$bat = @"
@echo off
setlocal
set "WAYFARE_BASE_DIR=%~dp0"
set "WAYFARE_OPEN_BROWSER=1"
start "" "%~dp0WayFare.exe"
endlocal
"@
Set-Content -Path (Join-Path $BundleDir "Start WayFare.bat") -Value $bat -Encoding ASCII

Copy-Item (Join-Path $Root "README_QUICKSTART.txt") (Join-Path $BundleDir "README_QUICKSTART.txt") -Force
Copy-Item (Join-Path $Root "MVP_TEST_CHECKLIST.md") (Join-Path $BundleDir "MVP_TEST_CHECKLIST.md") -Force

if (Test-Path $ZipPath) {
  Remove-Item $ZipPath -Force
}

Compress-Archive -Path (Join-Path $BundleDir "*") -DestinationPath $ZipPath -Force

Write-Host "Portable bundle ready:" $BundleDir
Write-Host "Portable zip ready:" $ZipPath
