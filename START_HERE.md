# 🚀 通知系统 - 3 分钟快速启动

## 前置条件

确保已安装：
- Python 3.8+
- Node.js 18+
- Rust 和 Cargo（[安装指南](https://www.rust-lang.org/tools/install)）

**检查 Rust 是否已安装**：
```bash
cargo --version
```

如果没有安装，请先安装 Rust：
- Windows: 下载并运行 [rustup-init.exe](https://win.rustup.rs/)
- Linux/Mac: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

## 第一次使用？按这个顺序操作

### 1️⃣ 初始化数据库（30 秒）
```bash
python init_db_simple.py
```

看到 "✅ Notification tables initialized successfully" 就成功了。

### 2️⃣ 启动后端（1 分钟）

**打开一个新的终端窗口**，然后运行：

```bash
# Windows PowerShell
$env:ENABLE_TEST_NOTIFICATIONS="true"
python start_notification_backend.py --enable-test

# Linux/Mac
export ENABLE_TEST_NOTIFICATIONS=true
python start_notification_backend.py --enable-test
```

看到以下信息就成功了：
```
 * Running on http://127.0.0.1:3001
 * Debugger is active!
```

✅ **后端已验证正常工作！所有 API 端点测试通过。**

**保持这个终端窗口运行**，不要关闭。

### 3️⃣ 启动应用（1 分钟）

**打开另一个新的终端窗口**，然后运行：

```bash
npm install
npm run tauri:dev
```

应用会自动打开。

**注意**：如果遇到 "Missing script: tauri" 错误，说明 package.json 已更新，请重新运行 `npm install`。

### 4️⃣ 测试通知（30 秒）

打开浏览器开发者工具（F12），在控制台输入：

```javascript
// 发送测试通知
await window.__TAURI__.core.invoke('send_test_notification', {
  userId: 'test_user',
  notificationType: 'learning_progress'
});

// 查看通知
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

你应该能看到通知出现在界面上！

## 遇到问题？

### 后端无法启动
- 检查端口 3001 是否被占用
- 确认 Python 依赖已安装：`pip install -r requirements.txt`

### 前端无法连接后端
- 确认后端正在运行：`curl http://localhost:3001/health`
- 检查防火墙设置

### 测试通知返回 403
- 确认设置了 `ENABLE_TEST_NOTIFICATIONS=true`
- 重启后端服务

## 下一步

- 📖 查看完整文档：`wayfare/README_NOTIFICATION.md`
- 🔧 查看配置选项：`config.example.yaml`
- 📝 查看使用示例：`examples/notification_usage_example.py`
- ✅ 查看部署清单：`NOTIFICATION_DEPLOYMENT_CHECKLIST.md`

## 快速测试命令

```bash
# 测试数据库
python test_notification_system.py

# 测试 API（需要先启动后端）
python test_notification_api.py

# 健康检查
curl http://localhost:3001/health
```

就这么简单！🎉
