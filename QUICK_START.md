# 🚀 WayFare 快速启动指南

## 前置条件

确保已安装：
- Python 3.8+
- Node.js 18+
- Rust 和 Cargo

## 快速启动（3 步）

### 步骤 1：初始化数据库
```bash
python init_db_simple.py
```

### 步骤 2：启动后端（新终端窗口）
```bash
# Windows PowerShell
$env:ENABLE_TEST_NOTIFICATIONS="true"
python start_notification_backend.py --enable-test

# Linux/Mac
export ENABLE_TEST_NOTIFICATIONS=true
python start_notification_backend.py --enable-test
```

看到 "Running on http://127.0.0.1:3001" 就成功了。
**保持这个终端窗口运行。**

### 步骤 3：启动前端（另一个新终端窗口）
```bash
npm install
npm run tauri:dev
```

应用会自动打开。

## 常见问题

### 问题：ModuleNotFoundError
**原因**：Python 模块导入冲突（wayfare/logging.py 与标准库冲突）

**解决方案**：使用提供的简化脚本：
- 数据库初始化：`python init_db_simple.py`
- 后端启动：`python start_notification_backend.py`

### 问题：端口 3001 被占用
```bash
# Windows
netstat -ano | findstr :3001
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -ti:3001 | xargs kill -9
```

### 问题：前端无法连接后端
1. 确认后端正在运行：`curl http://localhost:3001/health`
2. 检查防火墙设置
3. 确认环境变量已设置

## 下一步

- 📖 完整文档：`START_HERE.md`
- 🔧 配置选项：`config.example.yaml`
- 📝 使用示例：`examples/notification_usage_example.py`
- ✅ 部署清单：`NOTIFICATION_DEPLOYMENT_CHECKLIST.md`

## 测试命令

```bash
# 测试数据库
python test_notification_system.py

# 测试 API（需要先启动后端）
python test_notification_api.py

# 健康检查
curl http://localhost:3001/health
```

就这么简单！🎉
