@echo off
setlocal

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

set "UPLOAD_DIR=%ROOT%\uploads"
set "LOG_DIR=%ROOT%\logs"
set "START_DOCKER=1"
set "CHECK_ONLY=0"

if /I "%~1"=="nodocker" set "START_DOCKER=0"
if /I "%~1"=="check" (
    set "CHECK_ONLY=1"
    set "START_DOCKER=0"
)

echo.
echo ============================================
echo WayFare quick start
echo ============================================
echo Root: %ROOT%
echo.

if not exist "%UPLOAD_DIR%" mkdir "%UPLOAD_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

call :check_cmd python "Python"
if errorlevel 1 exit /b 1

call :check_cmd go "Go"
if errorlevel 1 exit /b 1

call :check_cmd npm.cmd "Node.js / npm"
if errorlevel 1 exit /b 1

if not exist "%PS_EXE%" (
    echo [ERROR] Windows PowerShell executable not found: %PS_EXE%
    exit /b 1
)
echo [OK] Windows PowerShell detected

if "%START_DOCKER%"=="1" (
    where docker >nul 2>nul
    if errorlevel 1 (
        echo [WARN] Docker not found. Skipping postgres/redis startup.
        echo [WARN] Please make sure PostgreSQL on localhost:5432 is already running.
        echo.
    ) else (
        docker info >nul 2>nul
        if errorlevel 1 (
            echo [WARN] Docker is installed, but Docker Desktop daemon is not running.
            echo [WARN] Skipping postgres/redis startup.
            echo [WARN] You can either:
            echo        1. Start Docker Desktop and rerun quick-start.bat
            echo        2. Or run quick-start.bat nodocker
            echo.
        ) else (
            echo [INFO] Starting postgres and redis with docker compose...
            pushd "%ROOT%"
            docker compose up -d postgres redis
            if errorlevel 1 (
                echo [WARN] docker compose failed. Please check your DB manually.
            ) else (
                echo [OK] postgres/redis startup command sent.
                timeout /t 5 /nobreak >nul
            )
            popd
            echo.
        )
    )
)

echo [INFO] Local URLs:
echo   Go API         http://localhost:8080
echo   Python AI      http://localhost:8001
echo   Astro Frontend http://localhost:3000
echo   Upload dir     %UPLOAD_DIR%
echo.

if "%CHECK_ONLY%"=="1" (
    echo [OK] Environment check finished.
    echo Usage:
    echo   quick-start.bat          Start postgres/redis + Python + Go + Astro
    echo   quick-start.bat nodocker Start Python + Go + Astro only
    echo   quick-start.bat check    Only validate environment
    exit /b 0
)

echo [INFO] Starting Python AI...
start "WayFare Python AI" "%PS_EXE%" -NoExit -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%\wayfare_ai_backend'; $env:DB_DSN='postgresql://luckdd:123456@localhost:5432/wayfare_db'; $env:GO_BACKEND_CALLBACK_URL='http://localhost:8080/api/internal/parse-status'; python http_server.py"
timeout /t 2 /nobreak >nul

echo [INFO] Starting Go backend...
start "WayFare Go Backend" "%PS_EXE%" -NoExit -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%\wayfare_backend'; $env:DB_HOST='localhost'; $env:DB_PORT='5432'; $env:DB_NAME='wayfare_db'; $env:DB_USER='luckdd'; $env:DB_PASSWORD='123456'; $env:PYTHON_AI_URL='http://localhost:8001'; $env:UPLOAD_DIR='%UPLOAD_DIR%'; go run ."
timeout /t 3 /nobreak >nul

echo [INFO] Starting Astro frontend...
start "WayFare Astro Frontend" "%PS_EXE%" -NoExit -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%'; $env:GO_BACKEND_URL='http://localhost:8080'; npm.cmd run dev"

echo.
echo [OK] Startup commands sent.
echo.
echo Open these pages:
echo   Frontend   http://localhost:3000
echo   Dashboard  http://localhost:3000/dashboard
echo   Debug      http://localhost:3000/debug
echo   API Test   http://localhost:3000/api-test
echo.
echo Health checks:
echo   Go         http://localhost:8080/health
echo   Python     http://localhost:8001/health
echo.
exit /b 0

:check_cmd
where %~1 >nul 2>nul
if errorlevel 1 (
    echo [ERROR] %~2 not found in PATH.
    exit /b 1
)
echo [OK] %~2 detected
exit /b 0
