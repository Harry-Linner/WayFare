# WayFare AI学习助手 - 手动启动指南

## 🚨 Docker未安装

系统检测到Docker未安装。请按照以下步骤手动启动服务：

## 📥 第一步：安装Docker

1. **下载Docker Desktop**:
   - 访问: https://www.docker.com/products/docker-desktop
   - 下载并安装Windows版本

2. **验证安装**:
   ```bash
   docker --version
   docker-compose --version
   ```

## 🚀 第二步：手动启动服务

### 方法1：使用Docker Compose（推荐）

1. **打开命令提示符或PowerShell**

2. **创建必要的目录**:
   ```bash
   mkdir uploads
   mkdir logs
   mkdir postgres_data
   mkdir redis_data
   ```

3. **构建服务镜像**:
   ```bash
   # 🎯 推荐：构建所有服务
   docker-compose build
   
   # 🔧 或者只构建后端服务（调试Go后端时）
   docker-compose build go_backend
   
   # 🚨 如果docker-compose失败，直接构建Dockerfile
   cd wayfare_backend
   docker build -t wayfare_go_backend .
   ```

4. **启动所有服务**:
   ```bash
   docker-compose build
   ```

5. **检查服务状态**:
   ```bash
   docker-compose ps
   ```

6. **查看日志**:
   ```bash
   docker-compose logs -f
   ```

### 方法2：逐个启动服务（调试模式）

如果Docker Compose有问题，或者需要单独调试某个服务：

1. **启动基础服务**:
   ```bash
   # 启动PostgreSQL
   docker run -d --name wayfare_postgres -p 5432:5432 -e POSTGRES_DB=wayfare_db -e POSTGRES_USER=luckdd -e POSTGRES_PASSWORD=123456 -v postgres_data:/var/lib/postgresql/data pgvector/pgvector:pg16
   
   # 启动Redis  
   docker run -d --name wayfare_redis -p 6379:6379 redis:7-alpine
   ```

2. **构建并启动Go后端（调试模式）**:
   ```bash
   cd wayfare_backend
   
   # 🔍 首先检查Dockerfile是否完整
   cat Dockerfile
   
   # 🏗️ 构建镜像（带详细输出）
   docker build -t wayfare_go_backend .
   
   # 🚀 启动容器（注意volume映射和环境变量）
   docker run -d --name wayfare_go_backend -p 8080:8080 \
     --link wayfare_postgres:postgres --link wayfare_redis:redis \
     -e DB_HOST=postgres -e DB_PORT=5432 -e DB_NAME=wayfare_db \
     -e DB_USER=luckdd -e DB_PASSWORD=123456 \
     -e REDIS_HOST=redis -e REDIS_PORT=6379 \
     -e PYTHON_EXECUTABLE=/usr/bin/python3 \
     -v %cd%/uploads:/app/uploads \
     -v %cd%/wayfare_ai_backend:/app/wayfare_ai_backend \
     wayfare_go_backend
   ```

3. **构建其他服务**:
   ```bash
   # Python AI服务
   cd wayfare_ai_backend
   docker build -t wayfare_python_ai .
   docker run -d --name wayfare_python_ai -p 8001:8001 wayfare_python_ai
   
   # C++沙箱
   cd WayFare-AI-C
   docker build -t wayfare_cpp_sandbox .
   docker run -d --name wayfare_cpp_sandbox -p 8002:8002 wayfare_cpp_sandbox
   
   # 前端
   docker build -t wayfare_frontend .
   docker run -d --name wayfare_frontend -p 3000:80 wayfare_frontend
   ```

## 🌐 访问服务

服务启动后，可以通过以下地址访问：

- **前端界面**: http://localhost:3000
- **Go后端API**: http://localhost:8080
- **Python AI服务**: http://localhost:8001
- **C++沙箱**: http://localhost:8002
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🧪 测试系统

打开新的终端窗口，运行测试脚本：

```bash
python test_system.py
```

## 🛠️ 常用Docker命令

```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker logs [容器名]

# 停止容器
docker stop [容器名]

# 删除容器
docker rm [容器名]

# 查看镜像
docker images

# 删除镜像
docker rmi [镜像名]

# 进入容器
docker exec -it [容器名] bash
```

## 📋 故障排除

### 端口冲突
如果端口被占用，可以修改`docker-compose.yml`中的端口映射：

```yaml
ports:
  - "新端口:原端口"
```

### 内存不足
Docker Desktop默认内存限制可能不够。在Docker设置中增加内存分配。

### 构建失败

**Go后端Docker构建问题解决方案：**

1. **🔍 检查具体错误**：
   ```bash
   cd wayfare_backend
   docker build -t test_build . 2>&1 | findstr "error"
   ```

2. **🛠️ 常见构建错误修复**：
   ```bash
   # 错误：缺少gcc/musl-dev
   # 确保Dockerfile包含：
   # RUN apk add --no-cache git gcc musl-dev ca-certificates
   
   # 错误：go mod download失败
   # 在Dockerfile中添加：
   # ENV GOPROXY=https://goproxy.cn,direct
   # ENV GOSUMDB=off
   ```

3. **🔄 替代构建方法**：
   ```bash
   # 方法1：使用docker-compose构建
   docker-compose build go_backend
   
   # 方法2：清理缓存后重新构建
   docker system prune -f
   docker-compose build --no-cache go_backend
   
   # 方法3：检查日志
   docker-compose logs go_backend
   ```

4. **📋 确保所有依赖项都已安装，网络连接正常**

## 🆘 需要帮助

如果仍有问题：
1. 检查Docker服务是否正在运行
2. 查看容器日志：`docker-compose logs [服务名]`
3. 确保端口未被其他程序占用
4. 尝试重启Docker服务

---
*安装Docker后，您可以使用`start.bat`或`start-simple.bat`来自动启动整个系统*