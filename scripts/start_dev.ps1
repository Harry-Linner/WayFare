#requires -Version 5.1
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "wayfare_backend"

$backendCommand = @"
Set-Location '$BackendDir'
`$env:GOCACHE = Join-Path (Get-Location) '.gocache'
`$env:GOMODCACHE = Join-Path (Get-Location) '.gomodcache'
`$env:WAYFARE_OPEN_BROWSER = '0'
go run .
"@

$frontendCommand = @"
Set-Location '$Root'
npm.cmd run dev
"@

Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", $backendCommand
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoProfile", "-NoExit", "-Command", $frontendCommand

Write-Host "WayFare dev stack starting..."
Write-Host "Backend target: http://127.0.0.1:8080/healthz"
Write-Host "Frontend target: http://127.0.0.1:4321/dashboard"
Write-Host "After both windows are ready, run:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\check_env.ps1 -CheckRuntime"
