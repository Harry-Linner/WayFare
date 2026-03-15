# WayFare 学习助手 - 完整系统联通指南

## 🎯 系统架构概览

WayFare 是一个基于多语言微服务架构的智能学习助手系统，由三个核心团队（ABC）开发：

- **A队（前端&网关）**: Astro + TypeScript + Go
- **B队（AI&业务逻辑）**: Python + FastAPI + PostgreSQL
- **C队（安全沙箱）**: C++ + WebAssembly + Linux容器

## 🚀 快速启动

### 前提条件
- Docker 和 Docker Compose
- 至少 8GB RAM
- 10GB 可用磁盘空间

### 一键启动
```bash
# 1. 克隆项目
git clone <repository-url>
cd WayFare

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置你的 API 密钥

# 3. 启动所有服务
docker-compose up -d

# 4. 检查服务状态
docker-compose ps
```

### 服务端口
- 🌐 前端界面: http://localhost:3000
- 🔌 Go网关: http://localhost:8080
- 🤖 AI服务: http://localhost:8001
- 🔒 沙箱服务: http://localhost:8002
- 🗄️ PostgreSQL: localhost:5432
- ⚡ Redis: localhost:6379

## 📋 功能特性

### 1. 智能文档处理
- 📄 PDF文档自动解析和向量化
- 🎯 基于知识点的智能批注
- 🔍 语义搜索和问答
- 📊 考频统计和重点标记

### 2. 个性化学习
- 👤 用户画像和学习偏好
- 📚 知识库专属配置
- 🎯 基于目标的学习路径
- ⏰ 智能干预和提醒

### 3. 三栏交互界面
- 📁 左侧：文件夹管理和配置
- 📖 中间：文档阅读和批注
- 💬 右侧：AI对话和问答

### 4. 安全沙箱
- 🔒 代码执行环境隔离
- 🛡️ 系统资源限制
- 📋 权限最小化原则

## 🔧 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Astro + TS | 高性能静态渲染 |
| 网关 | Go + Gin | API网关和WebSocket |
| AI服务 | Python + FastAPI | LLM集成和业务逻辑 |
| 沙箱 | C++ + WASM | 安全代码执行 |
| 数据层 | PostgreSQL + pgvector | 向量存储和查询 |
| 缓存 | Redis | 会话和状态管理 |

## 📁 项目结构

```
WayFare/
├── src/                          # 前端代码 (A队)
│   ├── components/              # UI组件
│   ├── pages/                   # 页面路由
│   ├── store/                   # 状态管理
│   └── types/                   # TypeScript类型定义
├── wayfare_backend/             # Go后端 (A队)
│   ├── main.go                  # 主入口
│   ├── models.go                # 数据模型
│   ├── ipc.go                   # Python进程通信
│   └── api_*.go                 # API接口
├── wayfare_ai_backend/          # Python AI服务 (B队)
│   ├── services.py              # 核心业务逻辑
│   ├── llm_provider.py          # LLM接口
│   ├── embedding_provider.py    # 向量嵌入
│   ├── document_parser.py       # 文档解析
│   └── database.py              # 数据库操作
├── WayFare-AI-C/                # C++沙箱 (C队)
│   └── wayfare-cpp/
│       ├── src/main.cpp         # 主程序
│       └── src/document_engine.cpp # 文档处理引擎
└── docker-compose.yml           # 容器编排
```

## 🔗 服务间通信

### 1. 前端 ↔ Go网关
- REST API: `/upload`, `/chat`
- WebSocket: 实时通信
- 文件上传：拖拽或选择文件

### 2. Go网关 ↔ Python AI
- IPC管道：标准输入输出
- JSON-RPC协议：结构化通信
- 异步处理：非阻塞调用

### 3. Python ↔ 数据库
- PostgreSQL：业务数据存储
- pgvector：向量相似度搜索
- 连接池：高效数据库访问

### 4. C++沙箱 ↔ 其他服务
- gRPC：高性能RPC调用
- 资源限制：CPU、内存、文件系统
- 安全隔离：容器化部署

## 🎯 核心功能流程

### 文档上传流程
1. 📤 用户拖拽文件到界面
2. 🔄 前端调用Go网关 `/upload` API
3. 📁 Go网关保存文件并更新数据库
4. 🐍 Go网关通过IPC通知Python处理
5. 🤖 Python解析文档并生成向量嵌入
6. 🗄️ 向量数据存储到PostgreSQL
7. ✅ 处理完成通知前端

### 智能批注流程
1. 📖 用户选择文本或点击气泡
2. 💬 前端发送批注请求到Go网关
3. 🔄 Go网关转发请求到Python AI
4. 🤖 Python进行语义搜索获取上下文
5. 🧠 LLM生成智能批注内容
6. 📊 返回带优先级和权重的批注
7. 🎨 前端根据优先级显示不同颜色

### 学习干预流程
1. ⏱️ Python后台监控页面停留时间
2. 📊 超过阈值触发干预机制
3. 💡 生成个性化学习建议
4. 🔔 通过WebSocket推送通知
5. 💬 用户可以选择接受建议或忽略

## 🔐 安全配置

### 数据库安全
- 连接池和连接超时
- SQL注入防护
- 数据加密存储

### API安全
- JWT身份验证
- CORS跨域控制
- 请求频率限制

### 沙箱安全
- 容器资源限制
- 系统调用拦截
- 文件系统隔离

## 📊 监控和日志

### 日志系统
- 📝 结构化日志输出
- 🔄 自动日志轮转
- 📊 错误追踪和报警

### 性能监控
- ⏱️ API响应时间
- 💾 数据库查询性能
- 🔄 服务健康检查

## 🚀 部署指南

### 开发环境
```bash
# 启动开发服务器
npm run dev          # 前端
go run main.go       # Go网关
python ipc_main.py   # Python AI
```

### 生产环境
```bash
# 使用Docker部署
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔧 故障排查

### 常见问题
1. **数据库连接失败**
   - 检查PostgreSQL服务状态
   - 验证连接字符串配置
   - 确认网络连通性

2. **Python IPC通信失败**
   - 检查Python进程状态
   - 验证IPC管道配置
   - 查看错误日志

3. **前端构建失败**
   - 检查Node.js版本
   - 清理node_modules
   - 重新安装依赖

### 调试工具
```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f [service-name]

# 进入容器调试
docker-compose exec [service-name] bash
```

## 🤝 团队协作

### 开发流程
1. **接口先行**: 定义Protobuf接口
2. **并行开发**: 各队独立开发
3. **集成测试**: 联调测试
4. **文档更新**: 同步文档

### 代码规范
- 📏 统一代码风格
- 📝 完善注释文档
- 🧪 单元测试覆盖
- 🔍 代码审查流程

## 📞 支持

如有问题，请通过以下方式联系：
- 📧 邮箱: support@wayfare.com
- 💬 Discord: WayFare社区
- 📚 文档: docs.wayfare.com

---

**WayFare** - 让学习更智能，让知识更易掌握 🎓