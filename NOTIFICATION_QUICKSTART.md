# 通知系统快速启动指南

## 前置条件

- Python 3.8+
- Node.js 18+
- Rust 1.77+
- 已安装项目依赖

## 快速启动（3 步）

### 1. 初始化数据库

```bash
python -c "import asyncio, sys; sys.path.insert(0, 'wayfare'); from init_notification_db import init_notification_tables; asyncio.run(init_notification_tables('.wayfare/wayfare.db'))"
```

### 2. 启动 Python 后端

```bash
# Windows (PowerShell)
$env:ENABLE_TEST_NOTIFICATIONS="true"
python start_notification_backend.py

# Linux/Mac
export ENABLE_TEST_NOTIFICATIONS=true
python start_notification_backend.py
```

后端将在 http://localhost:3001 启动

### 3. 启动 Tauri 应用

```bash
npm install
npm run tauri dev
```

## 测试通知系统

### 方法 1: 使用测试脚本

```bash
python test_notification_system.py
```

### 方法 2: 使用 curl 测试 API

```bash
# 健康检查
curl http://localhost:3001/health

# 发送测试通知
curl -X POST http://localhost:3001/api/notifications/test \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "notification_type": "learning_progress"}'

# 获取通知列表
curl -X POST http://localhost:3001/api/notifications/fetch \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "limit": 20, "offset": 0, "types": [], "unread_only": false, "sort_by": "recent"}'
```

### 方法 3: 在前端测试

打开浏览器开发者工具，在控制台执行：

```javascript
// 发送测试通知
await window.__TAURI__.core.invoke('send_test_notification', {
  userId: 'test_user',
  notificationType: 'learning_progress'
});

// 获取通知
const batch = await window.__TAURI__.core.invoke('fetch_notifications', {
  userId: 'test_user',
  limit: 20,
  offset: 0,
  types: [],
  unreadOnly: false,
  sortBy: 'recent'
});
console.log(batch);
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `BACKEND_URL` | `http://localhost:3001` | Python 后端地址（Tauri 使用） |
| `BACKEND_PORT` | `3001` | Flask 服务器端口 |
| `DATABASE_PATH` | `.wayfare/wayfare.db` | 数据库文件路径 |
| `ENABLE_TEST_NOTIFICATIONS` | `false` | 启用测试通知（开发环境） |

## 故障排查

### 问题 1: 数据库未初始化
**症状**: API 返回数据库错误

**解决**: 运行数据库初始化命令（见步骤 1）

### 问题 2: 后端无法连接
**症状**: Tauri 命令返回 NETWORK_ERROR

**解决**: 
1. 确认 Python 后端正在运行
2. 检查端口 3001 是否被占用
3. 验证 BACKEND_URL 环境变量

### 问题 3: 测试通知返回 403
**症状**: send_test_notification 返回 FORBIDDEN

**解决**: 设置环境变量 `ENABLE_TEST_NOTIFICATIONS=true` 并重启后端

### 问题 4: Rust 编译错误
**症状**: cargo build 失败

**解决**: 
```bash
cd src-tauri
cargo clean
cargo build
```

## 下一步

- 查看 [通知系统文档](wayfare/README_NOTIFICATION.md) 了解详细 API
- 查看 [使用示例](examples/notification_usage_example.py) 学习如何使用
- 查看 [通知协议](NOTIFICATION_PROTOCOL.md) 了解数据格式

## 开发模式

启动后端时添加 `--enable-test` 参数：

```bash
python start_notification_backend.py --enable-test
```

这将启用测试通知功能，方便开发调试。
