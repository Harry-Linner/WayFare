@echo off
REM WayFare AI学习助手 - Windows一键启动脚本
REM 支持Docker Compose部署所有服务

echo WayFare AI学习助手 - 启动脚本
echo ==================================

REM 检查Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Docker未安装，请先安装Docker
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
)

REM 创建必要的目录
echo 创建必要的目录...
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs
if not exist "postgres_data" mkdir postgres_data
if not exist "redis_data" mkdir redis_data

REM 设置环境变量
set DB_HOST=postgres
set DB_PORT=5432
set DB_NAME=wayfare_db
set DB_USER=wayfare_user
set DB_PASSWORD=wayfare_password
set REDIS_HOST=redis
set REDIS_PORT=6379
set UPLOAD_DIR=/app/uploads

REM 构建所有服务镜像
echo 构建服务镜像...
docker-compose build
if %errorlevel% neq 0 (
    echo 构建镜像失败
    pause
    exit /b 1
)

REM 启动所有服务
echo 启动所有服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo 启动服务失败
    pause
    exit /b 1
)

REM 等待服务启动
echo 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
echo 检查服务状态...
docker-compose ps

echo.
echo WayFare AI学习助手启动完成！
echo ==================================
echo PostgreSQL: localhost:5432
echo Redis: localhost:6379
echo Go后端API: http://localhost:8080
echo Python AI服务: http://localhost:8001
echo C++沙箱: http://localhost:8002
echo 前端界面: http://localhost:3000
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f [服务名]
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart [服务名]
echo   进入容器: docker-compose exec [服务名] bash
echo.
echo 系统已就绪，请在浏览器中访问 http://localhost:3000 开始使用！
pause