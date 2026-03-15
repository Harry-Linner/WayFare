#!/bin/bash

# WayFare AI学习助手 - 一键启动脚本
# 支持Docker Compose部署所有服务

set -e

echo "🚀 WayFare AI学习助手 - 启动脚本"
echo "=================================="

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查端口占用
check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$1 "; then
        echo "❌ 端口 $1 已被占用"
        return 1
    fi
    return 0
}

echo "🔍 检查端口占用..."
check_port 5432 || exit 1  # PostgreSQL
check_port 6379 || exit 1  # Redis
check_port 8080 || exit 1  # Go后端
check_port 8001 || exit 1  # Python AI服务
check_port 8002 || exit 1  # C++沙箱
check_port 3000 || exit 1  # 前端

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads logs postgres_data redis_data

# 设置环境变量
export DB_HOST=postgres
export DB_PORT=5432
export DB_NAME=wayfare_db
export DB_USER=wayfare_user
export DB_PASSWORD=wayfare_password
export REDIS_HOST=redis
export REDIS_PORT=6379
export UPLOAD_DIR=/app/uploads

# 构建所有服务镜像
echo "🔨 构建服务镜像..."
docker-compose build

# 启动所有服务
echo "🏃 启动所有服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
services=("postgres" "redis" "go_backend" "python_ai" "cpp_sandbox" "frontend")

for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service 服务运行正常"
    else
        echo "❌ $service 服务启动失败"
        echo "查看日志: docker-compose logs $service"
    fi
done

echo ""
echo "🎉 WayFare AI学习助手启动完成！"
echo "=================================="
echo "📊 PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo "🔧 Go后端API: http://localhost:8080"
echo "🤖 Python AI服务: http://localhost:8001"
echo "🔒 C++沙箱: http://localhost:8002"
echo "🌐 前端界面: http://localhost:3000"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f [服务名]"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart [服务名]"
echo "  进入容器: docker-compose exec [服务名] bash"
echo ""
echo "🚀 系统已就绪，请在浏览器中访问 http://localhost:3000 开始使用！"