@echo off
REM WayFare AI学习助手 - Windows启动脚本

echo Starting WayFare AI Learning Assistant...
echo ========================================

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker not found. Please install Docker first.
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose not found. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create directories
echo Creating directories...
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs
if not exist "postgres_data" mkdir postgres_data
if not exist "redis_data" mkdir redis_data

REM Build and start services
echo Building services...
docker-compose build
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo Starting services...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: Start failed
    pause
    exit /b 1
)

echo Waiting for services to start...
timeout /t 15 /nobreak >nul

echo.
echo Services started successfully!
echo ========================================
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8080
echo Python AI: http://localhost:8001
echo PostgreSQL: localhost:5432
echo Redis: localhost:6379
echo.
echo Use 'docker-compose logs -f' to view logs
echo Use 'docker-compose down' to stop services
echo.
pause