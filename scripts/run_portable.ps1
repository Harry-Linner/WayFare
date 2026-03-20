$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BundleDir = Join-Path $Root "release\\WayFare-MVP-Portable"
$ExePath = Join-Path $BundleDir "WayFare.exe"

if (-not (Test-Path $ExePath)) {
  throw "WayFare.exe not found. Run scripts/build_portable.ps1 first."
}

$env:WAYFARE_BASE_DIR = $BundleDir
$env:WAYFARE_OPEN_BROWSER = "1"

Start-Process -FilePath $ExePath -WorkingDirectory $BundleDir
