# 通知系统部署检查清单

## 开发环境验证

### 步骤 1: 数据库初始化
- [ ] 运行数据库初始化脚本
  ```bash
  python -c "import asyncio, sys; sys.path.insert(0, 'wayfare'); from init_notification_db import init_notification_tables; asyncio.run(init_notification_tables('.wayfare/wayfare.db'))"
  ```
- [ ] 验证数据库文件已创建：`.wayfare/wayfare.db`
- [ ] 运行数据库测试：`python test_notification_system.py`

### 步骤 2: Python 后端验证
- [ ] 安装 Python 依赖：`pip install -r requirements.txt`
- [ ] 设置环境变量：
  ```bash
  # Windows PowerShell
  $env:ENABLE_TEST_NOTIFICATIONS="true"
  $env:DATABASE_PATH=".wayfare/wayfare.db"
  $env:BACKEND_PORT="3001"
  
  # Linux/Mac
  export ENABLE_TEST_NOTIFICATIONS=true
  export DATABASE_PATH=.wayfare/wayfare.db
  export BACKEND_PORT=3001
  ```
- [ ] 启动后端：`python start_notification_backend.py --enable-test`
- [ ] 验证健康检查：`curl http://localhost:3001/health`
- [ ] 运行 API 测试：`python test_notification_api.py`

### 步骤 3: Tauri 应用验证
- [ ] 安装 Node.js 依赖：`npm install`
- [ ] 添加 Rust 依赖：`cd src-tauri && cargo build`
- [ ] 验证编译无错误
- [ ] 启动开发模式：`npm run tauri dev`

### 步骤 4: 前端集成测试
- [ ] 打开浏览器开发者工具
- [ ] 测试发送测试通知：
  ```javascript
  await window.__TAURI__.core.invoke('send_test_notification', {
    userId: 'test_user',
    notificationType: 'learning_progress'
  });
  ```
- [ ] 测试获取通知：
  ```javascript
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
- [ ] 验证通知显示在前端界面
- [ ] 测试标记已读功能
- [ ] 测试关闭通知功能
- [ ] 测试偏好设置界面

## 生产环境部署

### 环境配置
- [ ] 设置生产环境变量：
  ```bash
  BACKEND_URL=https://your-backend-domain.com
  DATABASE_PATH=/var/lib/wayfare/wayfare.db
  BACKEND_PORT=3001
  ENABLE_TEST_NOTIFICATIONS=false
  LOG_LEVEL=INFO
  ```
- [ ] 配置 HTTPS（使用 nginx 或 Caddy）
- [ ] 配置防火墙规则

### 数据库
- [ ] 初始化生产数据库
- [ ] 配置数据库备份
- [ ] 设置定期清理任务（cron）：
  ```bash
  # 每天凌晨 2 点清理
  0 2 * * * cd /path/to/wayfare && python wayfare/notification_cleanup.py
  ```

### 后端服务
- [ ] 使用 gunicorn 或 uwsgi 运行 Flask：
  ```bash
  gunicorn -w 4 -b 0.0.0.0:3001 wayfare.notification_api:app
  ```
- [ ] 配置进程管理器（systemd 或 supervisor）
- [ ] 配置日志轮转
- [ ] 设置监控和告警

### Tauri 应用
- [ ] 构建生产版本：`npm run tauri build`
- [ ] 测试打包后的应用
- [ ] 配置自动更新（可选）

## 监控指标

### 性能指标
- [ ] API 响应时间 < 100ms
- [ ] 数据库查询时间 < 50ms
- [ ] 通知获取延迟 < 200ms

### 业务指标
- [ ] 通知发送成功率 > 99%
- [ ] 通知阅读率
- [ ] 通知关闭率
- [ ] 用户偏好设置使用率

### 系统指标
- [ ] 数据库大小增长趋势
- [ ] API 错误率 < 1%
- [ ] 服务器 CPU/内存使用率

## 故障排查

### 常见问题

**问题**: 前端无法获取通知
- 检查后端是否运行
- 检查 BACKEND_URL 配置
- 查看浏览器控制台错误
- 查看 Tauri 日志

**问题**: 数据库错误
- 确认数据库已初始化
- 检查文件权限
- 查看 Python 日志

**问题**: Rust 编译失败
- 运行 `cargo clean`
- 重新构建：`cargo build`
- 检查 Cargo.toml 依赖版本

**问题**: 测试通知返回 403
- 设置 `ENABLE_TEST_NOTIFICATIONS=true`
- 重启后端服务

## 回滚计划

如果部署出现问题：

1. **停止新服务**
   ```bash
   # 停止 Flask 服务
   pkill -f notification_api.py
   ```

2. **恢复数据库**
   ```bash
   # 从备份恢复
   cp /backup/wayfare.db.backup .wayfare/wayfare.db
   ```

3. **回滚代码**
   ```bash
   git checkout previous-stable-branch
   ```

## 完成标准

- ✅ 所有核心功能已实现
- ✅ 数据库测试通过
- ✅ API 测试通过
- ✅ Rust 编译无错误
- ✅ 前端可以调用所有 Tauri 命令
- ✅ 文档完整
- ✅ 测试脚本可用

## 签署

- 开发完成日期: ___________
- 测试负责人: ___________
- 部署负责人: ___________
- 上线日期: ___________
