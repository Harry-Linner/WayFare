# WayFare AI学习助手 - 部署指南

## 🎯 系统概述

WayFare是一个多语言微服务架构的AI学习助手，集成了：
- **前端**: Astro + TypeScript + Tailwind CSS
- **API网关**: Go + Gin框架
- **AI服务**: Python + FastAPI + PostgreSQL(pgvector)
- **安全沙箱**: C++

## 🚀 快速启动

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ 内存
- 10GB+ 磁盘空间

### 一键启动
```bash
# Linux/Mac
chmod +x start.sh
./start.sh

# Windows
start.bat
```

### 手动部署
```bash
# 1. 克隆项目
git clone <repository-url>
cd WayFare

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 构建并启动服务
docker-compose build
docker-compose up -d

# 4. 验证服务状态
docker-compose ps
```

## 📋 服务端口

| 服务 | 端口 | 描述 |
|------|------|------|
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存服务 |
| Go后端 | 8080 | API网关 |
| Python AI | 8001 | AI处理服务 |
| C++沙箱 | 8002 | 安全沙箱 |
| 前端 | 3000 | Web界面 |

## 🔧 环境配置

### 基础配置
```env
# 数据库
DB_HOST=postgres
DB_PORT=5432
DB_NAME=wayfare_db
DB_USER=wayfare_user
DB_PASSWORD=your_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# 文件上传
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=52428800
```

### 可选配置
```env
# OpenAI API (可选)
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-3.5-turbo

# 日志级别
LOG_LEVEL=INFO
LOG_FILE=logs/wayfare.log

# 安全设置
JWT_SECRET=your_jwt_secret
CORS_ORIGINS=*
```

## 🐳 Docker Compose服务

### 服务依赖关系
```
frontend (3000) → go_backend (8080)
                    ↓
python_ai (8001) ← postgres (5432), redis (6379)
                    ↓
cpp_sandbox (8002)
```

### 数据持久化
- `postgres_data/`: PostgreSQL数据
- `redis_data/`: Redis数据
- `uploads/`: 上传文件
- `logs/`: 应用日志

## 🔍 监控与调试

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f go_backend
docker-compose logs -f python_ai
```

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8080/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### 进入容器
```bash
# Go后端
docker-compose exec go_backend bash

# Python AI服务
docker-compose exec python_ai bash

# PostgreSQL
docker-compose exec postgres psql -U wayfare_user -d wayfare_db
```

## 🛠️ 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
netstat -tuln | grep :8080

# 修改端口映射
# 编辑 docker-compose.yml 中的 ports 部分
```

#### 2. 数据库连接失败
```bash
# 检查PostgreSQL状态
docker-compose logs postgres

# 手动连接测试
docker-compose exec postgres psql -U wayfare_user -d wayfare_db
```

#### 3. Python AI服务无响应
```bash
# 检查IPC连接
docker-compose logs python_ai

# 重启服务
docker-compose restart python_ai
```

#### 4. 文件上传失败
```bash
# 检查上传目录权限
ls -la uploads/

# 检查磁盘空间
df -h
```

### 性能优化

#### 1. 数据库优化
```sql
-- 创建索引
CREATE INDEX idx_documents_project_id ON documents(project_id);
CREATE INDEX idx_chat_messages_project_id ON chat_messages(project_id);
```

#### 2. 内存配置
```yaml
# docker-compose.yml
services:
  python_ai:
    mem_limit: 2g
    mem_reservation: 1g
```

#### 3. 并发设置
```env
# Python AI服务
MAX_WORKERS=4
REQUEST_TIMEOUT=60
```

## 🔒 安全配置

### 生产环境建议
1. **数据库安全**
   - 使用强密码
   - 限制数据库访问
   - 定期备份

2. **网络安全**
   - 配置防火墙
   - 使用HTTPS
   - 设置CORS白名单

3. **容器安全**
   - 使用非root用户
   - 定期更新镜像
   - 扫描漏洞

### 备份策略
```bash
# 数据库备份
docker-compose exec postgres pg_dump -U wayfare_user wayfare_db > backup.sql

# 文件备份
tar -czf uploads_backup.tar.gz uploads/
```

## 📊 系统监控

### 资源使用
```bash
# 容器资源使用
docker stats

# 系统资源
top
htop
```

### 日志分析
```bash
# 错误日志统计
docker-compose logs | grep ERROR | wc -l

# 响应时间分析
docker-compose logs go_backend | grep -o '耗时: [0-9.]*s'
```

## 🔄 更新与维护

### 服务更新
```bash
# 拉取最新代码
git pull origin main

# 重新构建
docker-compose build --no-cache

# 滚动更新
docker-compose up -d --force-recreate
```

### 数据迁移
```bash
# 备份当前数据
docker-compose down
cp -r postgres_data postgres_data_backup
cp -r uploads uploads_backup

# 恢复数据
cp -r postgres_data_backup postgres_data
cp -r uploads_backup uploads
```

## 📞 支持

如遇到问题：
1. 查看日志文件
2. 检查服务状态
3. 验证配置文件
4. 查看GitHub Issues

## 🎯 下一步

系统启动后，请访问 http://localhost:3000 开始使用WayFare AI学习助手！

可以：
- 📁 上传学习文档
- 💬 与AI对话学习
- 🔍 搜索知识点
- 📊 查看学习进度