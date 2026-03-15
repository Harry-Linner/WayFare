# WayFare AI学习助手 - Astro与Go后端联调指南

## 🎯 概述

本文档指导如何在开发环境中将Astro前端与Go后端进行联调，确保前后端通信正常。

## 🏗️ 架构概览

```
Astro前端 (3000)  ←→  Go后端 (8080)  ←→  Python AI (8001)  ←→  PostgreSQL (5432)
     ↓                    ↓                    ↓
   用户界面            API网关              AI处理服务
```

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Node.js (≥18.0.0)
- Go (≥1.23)
- Python (≥3.8)
- PostgreSQL
- Redis (可选，但推荐)

### 2. 启动服务

#### 方法1：使用一键启动脚本
```bash
# Windows
dev-start.bat

# 或使用Docker
docker-compose up -d
```

#### 方法2：手动启动
```bash
# 1. 启动Go后端
cd wayfare_backend
go run .

# 2. 启动Python AI服务（新终端）
cd wayfare_ai_backend
python http_server.py

# 3. 启动Astro前端（新终端）
npm run dev
```

### 3. 验证联调

#### 检查服务状态
```bash
# 使用状态检查脚本
check-status.bat

# 或手动检查
curl http://localhost:8080/health
curl http://localhost:8001/health
```

#### 访问测试页面
- **联调测试页**: http://localhost:3000/debug
- **API测试页**: http://localhost:3000/api-test
- **文件上传**: http://localhost:3000/create-knowledge-base

## 🔧 配置说明

### 环境变量

主要配置项（`.env`文件）：

```env
# API配置
PUBLIC_API_URL=http://localhost:8080

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=wayfare_db
DB_USER=luckdd
DB_PASSWORD=123456

# CORS配置
CORS_ORIGIN=http://localhost:3000
```

### Astro配置

`astro.config.mjs`中的代理配置：

```javascript
vite: {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false
      }
    }
  }
}
```

## 🧪 联调测试

### 1. 基础连接测试

访问 http://localhost:3000/debug，点击：
- **测试连接**: 检查前后端连接状态
- **完整测试**: 运行完整的API测试流程

### 2. API功能测试

#### 健康检查
```javascript
// 浏览器控制台
WayFareDebug.testConnection()
```

#### 聊天功能测试
```javascript
// 浏览器控制台
WayFareDebug.testChat("你好，请介绍一下WayFare系统")
```

#### 文件上传测试
```javascript
// 选择文件后上传
const file = document.querySelector('input[type="file"]').files[0]
WayFareDebug.api.uploadDocument(file)
```

### 3. 手动API测试

#### 获取文档列表
```bash
curl http://localhost:8080/api/documents
```

#### 发送聊天消息
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好",
    "context": "测试消息",
    "docHash": "optional_doc_hash"
  }'
```

## 🔍 常见问题排查

### 1. 前端无法连接后端

**症状**: 浏览器控制台显示 `net::ERR_CONNECTION_REFUSED`

**解决方案**:
1. 检查Go后端是否启动：`check-status.bat`
2. 检查端口是否被占用：`netstat -ano | findstr :8080`
3. 检查防火墙设置
4. 确认环境变量 `PUBLIC_API_URL` 设置正确

### 2. CORS错误

**症状**: 浏览器显示 CORS policy 错误

**解决方案**:
1. 检查Go后端CORS配置
2. 确认 `CORS_ORIGIN` 环境变量包含前端地址
3. 检查 `astro.config.mjs` 中的代理配置

### 3. 文件上传失败

**症状**: 文件上传无响应或报错

**解决方案**:
1. 检查上传目录权限：`uploads/` 目录可写
2. 检查文件大小限制（默认50MB）
3. 检查磁盘空间
4. 查看Go后端日志获取详细错误信息

### 4. 数据库连接失败

**症状**: Go后端启动时报数据库连接错误

**解决方案**:
1. 检查PostgreSQL服务状态
2. 确认数据库配置正确
3. 检查数据库用户权限
4. 手动测试连接：`psql -h localhost -U luckdd -d wayfare_db`

## 📊 监控与日志

### 日志文件位置
- **Go后端**: `wayfare_backend/logs/`
- **Python AI**: `wayfare_ai_backend/logs/`
- **Astro前端**: 浏览器控制台

### 实时监控
```bash
# 查看Go后端日志
tail -f wayfare_backend/logs/*.log

# 查看Python AI日志  
tail -f wayfare_ai_backend/logs/*.log

# 查看所有服务状态
docker-compose logs -f
```

## 🎯 最佳实践

### 1. 开发流程
1. 先启动后端服务，确保API正常
2. 再启动前端服务，进行界面开发
3. 使用联调测试页验证功能
4. 查看日志排查问题

### 2. 调试技巧
- 使用浏览器开发者工具查看网络请求
- 在控制台中使用 `WayFareDebug` 对象进行快速测试
- 查看各个服务的日志文件获取详细信息
- 使用代理配置避免CORS问题

### 3. 性能优化
- 使用开发模式的热重载功能
- 合理设置API超时时间
- 启用适当的缓存策略
- 监控服务资源使用情况

## 📚 相关资源

- **API文档**: 查看 `src/lib/api/client.ts`
- **测试页面**: http://localhost:3000/debug
- **状态检查**: `check-status.bat`
- **Docker部署**: `docker-compose.yml`

## 🆘 获取帮助

如果问题无法解决：
1. 检查所有服务的日志文件
2. 确认所有依赖服务都已启动
3. 验证网络连接和端口状态
4. 查看GitHub Issues或联系开发团队

---

**Happy Coding! 🚀**