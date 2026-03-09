# 实现计划：前后端通知系统对接

## 概述

本实现计划将前后端通知系统对接分解为可执行的编码任务。实现顺序遵循自底向上的原则：先实现数据库层，再实现 Python 后端业务逻辑和 API，然后实现 Tauri 命令处理器，最后实现通知调度器和测试功能。

技术栈：
- 数据库：SQLite (通过 wayfare/db.py)
- 后端：Python (Flask/FastAPI)
- 中枢：Rust (Tauri)
- 前端：TypeScript (React) - 已实现

## 任务

- [x] 1. 实现数据库层和数据模型
  - [x] 1.1 创建数据库初始化脚本
    - 在 wayfare/init_notification_db.py 中实现数据库表创建
    - 创建 notifications 表（包含所有必需字段）
    - 创建 notification_preferences 表
    - 创建必要的索引（user_id, created_at, is_read/is_dismissed 复合索引）
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 1.2 编写数据库 schema 验证测试
    - 验证 notifications 表存在且包含所有字段
    - 验证 notification_preferences 表存在且包含所有字段
    - 验证索引已正确创建
    - _需求：4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 1.3 扩展 wayfare/db.py 添加通知相关方法
    - 实现 save_notification() 方法
    - 实现 get_notification() 方法
    - 实现 query_notifications() 方法（支持过滤、分页、排序）
    - 实现 count_notifications() 方法
    - 实现 update_notification() 方法
    - 实现 batch_update_notifications() 方法
    - 实现 get_notification_preferences() 方法
    - 实现 save_notification_preferences() 方法
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 1.4 编写数据库操作单元测试
    - 测试通知的创建、查询、更新操作
    - 测试批量更新操作
    - 测试偏好设置的读写操作
    - 测试过滤和分页功能
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. 实现通知管理器（NotificationManager）
  - [x] 2.1 创建 NotificationManager 类和核心方法
    - 在 wayfare/notification_manager.py 中创建 NotificationManager 类
    - 实现 create_notification() 方法（生成 UUID、设置时间戳、设置过期时间）
    - 实现 get_notifications() 方法（支持过滤、分页、统计）
    - 实现 mark_as_read() 方法（更新 is_read 和 read_at）
    - 实现 dismiss_notification() 方法（更新 is_dismissed 和 dismissed_at）
    - 实现 batch_dismiss() 方法（批量更新）
    - _需求：5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 2.2 编写属性测试：通知 CRUD Round-Trip
    - **属性 5：通知 CRUD Round-Trip**
    - **验证需求：5.1, 5.2, 5.3, 5.4**
    - 对于任意有效的通知对象，执行创建→查询→标记已读→再次查询→关闭→查询未关闭通知的完整流程
    - 验证每个步骤的数据一致性

  - [ ]* 2.3 编写属性测试：批量操作一致性
    - **属性 6：批量操作一致性**
    - **验证需求：5.5**
    - 对于任意通知 ID 列表，验证批量关闭操作等价于单独关闭每个通知

  - [ ]* 2.4 编写属性测试：通知过滤正确性
    - **属性 7：通知过滤正确性**
    - **验证需求：5.2, 5.6**
    - 对于任意通知集合和过滤条件，验证查询结果只包含满足条件的通知且不包含已过期通知

  - [ ]* 2.5 编写属性测试：分页元数据正确性
    - **属性 8：分页元数据正确性**
    - **验证需求：5.7, 12.5**
    - 对于任意分页参数，验证 totalCount、unreadCount、hasMore 的正确性

  - [x] 2.6 实现偏好设置管理方法
    - 实现 get_preferences() 方法（返回默认偏好如果不存在）
    - 实现 update_preferences() 方法（验证输入、更新时间戳）
    - _需求：6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 2.7 编写属性测试：偏好设置 Round-Trip
    - **属性 9：偏好设置 Round-Trip**
    - **验证需求：6.1, 6.2, 6.6**
    - 对于任意有效的 NotificationPreferences 对象，验证保存后读取得到等价对象

  - [ ]* 2.8 编写单元测试：默认偏好设置和输入验证
    - 测试首次访问返回默认偏好设置
    - 测试无效通知类型被拒绝
    - 测试无效优先级被拒绝
    - _需求：6.3, 6.4, 6.5_

- [x] 3. 检查点 - 确保数据库和管理器层测试通过
  - 运行所有数据库和 NotificationManager 测试
  - 确认所有测试通过，如有问题请询问用户

- [x] 4. 实现 Python 后端 API 端点
  - [x] 4.1 创建 Flask/FastAPI 应用和路由
    - 在 wayfare/notification_api.py 中创建 Flask 应用
    - 初始化 SQLiteDB 和 NotificationManager
    - 实现 POST /api/notifications/fetch 端点
    - 实现 POST /api/notifications/:id/read 端点
    - 实现 DELETE /api/notifications/:id 端点
    - 实现 POST /api/notifications/batch-dismiss 端点
    - 实现 GET /api/notifications/preferences 端点
    - 实现 PUT /api/notifications/preferences 端点
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 4.2 实现错误处理和输入验证
    - 验证必需参数（user_id, notification_id 等）
    - 返回 HTTP 400 对于无效输入
    - 返回 HTTP 404 对于不存在的资源
    - 返回 HTTP 500 对于服务器错误
    - 实现统一的错误处理器
    - _需求：3.7, 3.8, 3.9, 10.3, 10.4, 10.5, 10.6_

  - [ ]* 4.3 编写属性测试：HTTP 请求格式正确性
    - **属性 3：HTTP 请求格式正确性**
    - **验证需求：2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8**
    - 验证所有端点的 HTTP 方法、路径、Content-Type 头正确

  - [ ]* 4.4 编写属性测试：API 端点输入验证
    - **属性 4：API 端点输入验证**
    - **验证需求：3.7, 6.4, 6.5**
    - 对于任意缺失必需参数或包含无效值的请求，验证返回 HTTP 400 和描述性错误

  - [ ]* 4.5 编写单元测试：API 端点功能
    - 测试每个端点的正常流程
    - 测试资源不存在返回 404
    - 测试参数验证
    - _需求：3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x] 4.6 实现健康检查和日志配置
    - 实现 GET /health 端点
    - 配置结构化日志（JSON 格式）
    - 配置日志轮转
    - _需求：10.4, 10.5_

- [x] 5. 实现 Tauri 命令处理器（Rust）
  - [x] 5.1 创建 Rust 数据结构和命令模块
    - 在 src-tauri/src/commands/notifications.rs 中定义数据结构
    - 定义 Notification、NotificationBatch、NotificationPreferences 结构体
    - 实现 Serialize 和 Deserialize trait
    - 创建 AppState 结构体（包含 HTTP 客户端和后端 URL）
    - _需求：11.1, 11.2_

  - [ ]* 5.2 编写属性测试：数据序列化 Round-Trip
    - **属性 13：数据序列化 Round-Trip**
    - **验证需求：11.1, 11.2, 11.3, 11.4, 11.5, 11.6**
    - 对于任意 Notification 或 NotificationPreferences 对象，验证序列化后反序列化得到等价对象

  - [ ]* 5.3 编写属性测试：反序列化错误处理
    - **属性 14：反序列化错误处理**
    - **验证需求：11.7**
    - 对于任意无效 JSON，验证反序列化返回明确错误而不是 panic

  - [x] 5.4 实现 8 个 Tauri 命令处理器
    - 实现 fetch_notifications 命令（调用 POST /api/notifications/fetch）
    - 实现 mark_notification_as_read 命令（调用 POST /api/notifications/:id/read）
    - 实现 dismiss_notification 命令（调用 DELETE /api/notifications/:id）
    - 实现 batch_dismiss_notifications 命令（调用 POST /api/notifications/batch-dismiss）
    - 实现 get_notification_preferences 命令（调用 GET /api/notifications/preferences）
    - 实现 update_notification_preferences 命令（调用 PUT /api/notifications/preferences）
    - 实现 refresh_notification_stream 命令（调用 POST /api/notifications/fetch）
    - 实现 send_test_notification 命令（调用 POST /api/notifications/test）
    - _需求：1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 5.5 实现错误处理和日志记录
    - 实现统一的错误响应格式（ErrorResponse 结构体）
    - 处理网络错误（NETWORK_ERROR）
    - 处理服务器错误（SERVER_ERROR）
    - 处理反序列化错误（INVALID_RESPONSE）
    - 记录错误日志
    - _需求：1.9, 2.7, 10.1, 10.2_

  - [ ]* 5.6 编写属性测试：Tauri 命令处理器完整性
    - **属性 1：Tauri 命令处理器完整性**
    - **验证需求：1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8**
    - 对于任意有效命令名称，验证调用返回成功响应或明确错误而不是崩溃

  - [ ]* 5.7 编写属性测试：命令错误处理
    - **属性 2：命令错误处理**
    - **验证需求：1.9, 2.7**
    - 对于任意导致错误的输入，验证返回 Result::Err 而不是 panic

  - [x] 5.8 在 main.rs 中注册命令
    - 在 src-tauri/src/main.rs 中导入 notifications 模块
    - 初始化 AppState（HTTP 客户端和后端 URL）
    - 使用 tauri::generate_handler! 注册所有 8 个命令
    - _需求：1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

- [x] 6. 检查点 - 确保 API 和 Tauri 命令测试通过
  - 运行所有 Python API 测试
  - 运行所有 Rust 命令处理器测试
  - 确认所有测试通过，如有问题请询问用户

- [x] 7. 实现通知调度器（NotificationScheduler）
  - [x] 7.1 创建 NotificationScheduler 类
    - 在 wayfare/notification_scheduler.py 中创建 NotificationScheduler 类
    - 实现事件监听机制（学习进度、任务完成、卡顿检测）
    - 实现通知生成逻辑（调用 NotificationManager.create_notification）
    - _需求：7.1, 7.2, 7.3_

  - [x] 7.2 实现偏好过滤和静默时段逻辑
    - 检查用户偏好设置（enabled_types, min_priority_level）
    - 实现静默时段检查（quiet_hours）
    - 延迟非紧急通知到静默时段结束后
    - 设置通知过期时间（默认 24 小时）
    - _需求：7.4, 7.5, 7.6, 7.7_

  - [ ]* 7.3 编写属性测试：通知调度器偏好过滤
    - **属性 10：通知调度器偏好过滤**
    - **验证需求：7.4, 7.5**
    - 验证禁用的通知类型或低于最低优先级的通知不会被生成

  - [ ]* 7.4 编写属性测试：静默时段延迟
    - **属性 11：静默时段延迟**
    - **验证需求：7.6**
    - 验证静默时段内的非紧急通知被延迟到静默时段结束后

  - [ ]* 7.5 编写属性测试：通知过期时间设置
    - **属性 12：通知过期时间设置**
    - **验证需求：7.7**
    - 验证新创建的通知的 expires_at 是未来时间且默认为 24 小时后

  - [ ]* 7.6 编写单元测试：调度器功能
    - 测试学习进度事件触发通知
    - 测试任务完成事件触发通知
    - 测试卡顿检测事件触发通知
    - 测试偏好过滤逻辑
    - _需求：7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. 实现测试通知功能
  - [x] 8.1 实现测试通知 API 端点
    - 在 wayfare/notification_api.py 中实现 POST /api/notifications/test 端点
    - 检查环境变量 ENABLE_TEST_NOTIFICATIONS
    - 生成测试通知（添加 [TEST] 前缀）
    - 返回 HTTP 403 如果测试功能未启用
    - _需求：9.1, 9.2, 9.3, 9.4_

  - [x] 8.2 在 NotificationManager 中添加测试通知方法
    - 实现 create_test_notification() 方法
    - 根据 notification_type 生成不同类型的测试通知
    - 为测试通知添加 [TEST] 前缀
    - _需求：9.2, 9.3_

  - [ ]* 8.3 编写单元测试：测试通知功能
    - 测试启用时可以发送测试通知
    - 测试未启用时返回 403
    - 测试通知包含 [TEST] 前缀
    - _需求：9.1, 9.2, 9.3, 9.4_

- [x] 9. 实现性能优化和清理任务
  - [x] 9.1 实现数据库连接池（如需要）
    - 评估是否需要连接池
    - 如需要，配置 aiosqlite 连接池
    - _需求：12.3_

  - [x] 9.2 实现查询限制和优化
    - 在 get_notifications 中限制最大返回数量为 100
    - 优化 SQL 查询（使用索引）
    - _需求：12.4, 12.1_

  - [x] 9.3 实现定期清理任务
    - 创建 cleanup_expired_notifications() 函数
    - 删除 30 天前的已关闭通知
    - 实现定期执行机制（每天一次）
    - _需求：12.6_

  - [ ]* 9.4 编写性能测试
    - 测试查询 10000 条通知时响应时间 < 100ms
    - 测试批量操作使用单个 SQL 语句
    - _需求：12.1, 12.2_

- [x] 10. 集成测试和端到端验证
  - [ ]* 10.1 编写集成测试：完整通知生命周期
    - 测试从事件触发到通知创建到前端获取的完整流程
    - 测试标记已读和关闭通知的完整流程
    - 测试偏好设置更新影响通知生成
    - _需求：所有需求_

  - [ ]* 10.2 编写集成测试：Tauri 与 Python 后端通信
    - 测试所有 8 个 Tauri 命令与后端 API 的通信
    - 测试错误处理和重试机制
    - _需求：1.1-1.9, 2.1-2.8, 3.1-3.9_

  - [ ]* 10.3 编写集成测试：数据一致性
    - 测试并发操作的数据一致性
    - 测试批量操作的原子性
    - _需求：5.5, 12.2_

- [x] 11. 最终检查点 - 确保所有测试通过
  - 运行所有单元测试
  - 运行所有属性测试
  - 运行所有集成测试
  - 运行所有性能测试
  - 确认所有测试通过，如有问题请询问用户

- [x] 12. 文档和配置
  - [x] 12.1 创建 README 文档
    - 在 wayfare/README_NOTIFICATION.md 中记录通知系统架构
    - 记录 API 端点和参数
    - 记录 Tauri 命令和参数
    - 记录环境变量配置
    - _需求：所有需求_

  - [x] 12.2 创建使用示例
    - 在 examples/notification_usage_example.py 中创建 Python 使用示例
    - 展示如何创建通知、查询通知、更新偏好设置
    - _需求：所有需求_

  - [x] 12.3 更新配置文件
    - 在 config.example.yaml 中添加通知系统配置项
    - 记录所有环境变量和默认值
    - _需求：所有需求_

## 注意事项

- 标记为 `*` 的任务是可选的测试任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号，确保可追溯性
- 检查点任务确保增量验证，及时发现问题
- 属性测试验证通用正确性属性，单元测试验证特定示例和边界情况
- 实现顺序遵循依赖关系：数据库 → 管理器 → API → Tauri 命令 → 调度器

## 技术细节

### 数据库操作
- 使用 wayfare/db.py 中的 SQLiteDB 类
- 所有数据库操作使用 aiosqlite 异步接口
- JSON 字段（action_payload, metadata, enabled_types, quiet_hours）使用 json.dumps/loads 序列化

### HTTP 通信
- Tauri 使用 reqwest 库发送 HTTP 请求
- Python 使用 Flask 或 FastAPI 处理 HTTP 请求
- 所有请求和响应使用 JSON 格式

### 错误处理
- Tauri 命令返回 Result<T, String>
- Python API 使用 HTTP 状态码表示错误类型
- 所有错误记录到日志文件

### 测试策略
- 单元测试：pytest + pytest-asyncio
- 属性测试：hypothesis (Python) + quickcheck (Rust)
- 集成测试：pytest + mock HTTP 服务器
- 性能测试：pytest + time 测量

### 环境变量
- ENABLE_TEST_NOTIFICATIONS: 启用测试通知功能（开发环境）
- BACKEND_URL: Python 后端 URL（默认 http://localhost:3001）
- DATABASE_PATH: SQLite 数据库路径（默认 .wayfare/wayfare.db）
- LOG_LEVEL: 日志级别（默认 INFO）
