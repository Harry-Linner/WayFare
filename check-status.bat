@echo off
REM WayFare AI学习助手 - 服务状态检查脚本
echo.
echo 🔍 WayFare服务状态检查
echo =========================
echo.

REM 检查Go后端
echo 📡 检查Go后端服务 (localhost:8080)...
curl -s -o nul -w "%%{http_code}" http://localhost:8080/health > temp_status.txt
set /p GO_STATUS=<temp_status.txt
if "%GO_STATUS%"=="200" (
    echo ✅ Go后端运行正常
) else (
    echo ❌ Go后端异常 (状态码: %GO_STATUS%)
)

REM 检查Python AI服务
echo.
echo 🧠 检查Python AI服务 (localhost:8001)...
curl -s -o nul -w "%%{http_code}" http://localhost:8001/health > temp_status.txt
set /p PYTHON_STATUS=<temp_status.txt
if "%PYTHON_STATUS%"=="200" (
    echo ✅ Python AI服务运行正常
) else (
    echo ❌ Python AI服务异常 (状态码: %PYTHON_STATUS%)
)

REM 检查Astro前端
echo.
echo 🌟 检查Astro前端 (localhost:3000)...
curl -s -o nul -w "%%{http_code}" http://localhost:3000 > temp_status.txt
set /p ASTRO_STATUS=<temp_status.txt
if "%ASTRO_STATUS%"=="200" (
    echo ✅ Astro前端运行正常
) else (
    echo ❌ Astro前端异常 (状态码: %ASTRO_STATUS%)
)

REM 检查数据库连接（通过Go后端）
echo.
echo 🗄️  检查数据库连接...
curl -s http://localhost:8080/api/status > temp_db.json 2>nul
if exist temp_db.json (
    findstr /C:"database" temp_db.json > nul
    if !errorlevel! equ 0 (
        echo ✅ 数据库连接正常
    ) else (
        echo ⚠️  数据库连接状态未知
    )
) else (
    echo ❌ 无法检查数据库状态
)

REM 清理临时文件
del temp_status.txt 2>nul
del temp_db.json 2>nul

echo.
echo 📋 服务端口状态:
echo   Go后端API:    http://localhost:8080/health
echo   Python AI:     http://localhost:8001/health
echo   Astro前端:     http://localhost:3000
echo   联调测试页:    http://localhost:3000/debug
echo.
echo 🚀 快速测试命令:
echo   完整测试: curl -X GET http://localhost:8080/health
echo   聊天测试: curl -X POST http://localhost:8080/api/chat -H "Content-Type: application/json" -d "{\"message\":\"hello\",\"context\":\"test\"}"
echo.
pause