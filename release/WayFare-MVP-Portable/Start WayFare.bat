@echo off
setlocal
set "WAYFARE_BASE_DIR=%~dp0"
set "WAYFARE_OPEN_BROWSER=1"
start "" "%~dp0WayFare.exe"
endlocal
