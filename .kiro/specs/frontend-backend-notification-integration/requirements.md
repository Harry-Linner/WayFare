# 需求文档 - 前后端通知系统对接

## 介绍

本功能实现前端（Tauri + React + TypeScript）与后端（Python）的通知系统完整对接。前端已实现 NotificationService，调用 8 个 Tauri 命令；现需在 Tauri 中枢（Rust）实现这些命令处理器，并在 Python 后端实现对应的 API 端点、数据库操作和通知生成逻辑。通信协议已在 NOTIFICATION_PROTOCOL.md 中定义。

## 术语表

- **Tauri_Command_Handler**: Tauri 中枢的 Rust 命令处理器，接收前端 IPC 调用
- **Python_Backend**: Python 后端服务，提供 HTTP API 端点
- **Notification_Database**: SQLite 数据库中的通知相关表
- **Frontend_Service**: 前端的 NotificationService (TypeScript)
- **IPC_Communication**: Tauri 进程间通信机制
- **HTTP_Client**: Tauri 中的 HTTP 客户端，用于与 Python 后端通信
- **Notification_Scheduler**: 后端的通知调度器，负责生成和触发通知
- **WebSocket_Connection**: 可选的实时推送连接

## 需求

### 需求 1: Tauri 命令处理器实现

**用户故事**: 作为前端开发者，我希望调用 Tauri 命令时能够成功与后端通信，以便获取和管理通知数据。

#### 验收标准

1. THE Tauri_Command_Handler SHALL 实现 fetch_notifications 命令，接收 user_id、project_id、limit、offset、types、unread_only、sort_by 参数
2. THE Tauri_Command_Handler SHALL 实现 mark_notification_as_read 命令，接收 notification_id 和 user_id 参数
3. THE Tauri_Command_Handler SHALL 实现 dismiss_notification 命令，接收 notification_id 和 user_id 参数
4. THE Tauri_Command_Handler SHALL 实现 batch_dismiss_notifications 命令，接收 notification_ids 数组和 user_id 参数
5. THE Tauri_Command_Handler SHALL 实现 get_notification_preferences 命令，接收 user_id 参数
6. THE Tauri_Command_Handler SHALL 实现 update_notification_preferences 命令，接收 preferences 对象参数
7. THE Tauri_Command_Handler SHALL 实现 refresh_notification_stream 命令，接收 user_id 参数
8. THE Tauri_Command_Handler SHALL 实现 send_test_notification 命令，接收 user_id 和 notification_type 参数
9. WHEN 任何命令执行失败，THE Tauri_Command_Handler SHALL 返回包含错误信息的 Result::Err

### 需求 2: Tauri 与 Python 后端通信

**用户故事**: 作为系统架构师，我希望 Tauri 中枢能够通过 HTTP 与 Python 后端通信，以便实现前后端数据交互。

#### 验收标准

1. THE HTTP_Client SHALL 向 Python_Backend 发送 POST 请求到 /api/notifications/fetch 端点以获取通知列表
2. THE HTTP_Client SHALL 向 Python_Backend 发送 POST 请求到 /api/notifications/:id/read 端点以标记通知为已读
3. THE HTTP_Client SHALL 向 Python_Backend 发送 DELETE 请求到 /api/notifications/:id 端点以关闭通知
4. THE HTTP_Client SHALL 向 Python_Backend 发送 POST 请求到 /api/notifications/batch-dismiss 端点以批量关闭通知
5. THE HTTP_Client SHALL 向 Python_Backend 发送 GET 请求到 /api/notifications/preferences 端点以获取偏好设置
6. THE HTTP_Client SHALL 向 Python_Backend 发送 PUT 请求到 /api/notifications/preferences 端点以更新偏好设置
7. WHEN HTTP 请求失败，THE HTTP_Client SHALL 返回包含错误类型（NETWORK_ERROR、SERVER_ERROR、UNAUTHORIZED）的错误响应
8. THE HTTP_Client SHALL 在请求头中包含 Content-Type: application/json

### 需求 3: Python 后端 API 端点实现

**用户故事**: 作为后端开发者，我希望实现通知相关的 API 端点，以便处理来自 Tauri 的请求。

#### 验收标准

1. THE Python_Backend SHALL 实现 POST /api/notifications/fetch 端点，返回 NotificationBatch 结构
2. THE Python_Backend SHALL 实现 POST /api/notifications/:id/read 端点，返回更新后的 Notification 对象
3. THE Python_Backend SHALL 实现 DELETE /api/notifications/:id 端点，返回 { dismissed: boolean }
4. THE Python_Backend SHALL 实现 POST /api/notifications/batch-dismiss 端点，返回 { status: string }
5. THE Python_Backend SHALL 实现 GET /api/notifications/preferences 端点，返回 NotificationPreferences 对象
6. THE Python_Backend SHALL 实现 PUT /api/notifications/preferences 端点，返回 { status: string }
7. WHEN 请求参数缺失或无效，THE Python_Backend SHALL 返回 HTTP 400 状态码和错误描述
8. WHEN 资源不存在，THE Python_Backend SHALL 返回 HTTP 404 状态码
9. WHEN 服务器内部错误，THE Python_Backend SHALL 返回 HTTP 500 状态码和错误日志

### 需求 4: 通知数据库模型

**用户故事**: 作为数据库管理员，我希望有清晰的数据库表结构来存储通知数据，以便支持通知的 CRUD 操作。

#### 验收标准

1. THE Notification_Database SHALL 包含 notifications 表，字段包括 id、user_id、type、title、message、priority、icon、action_url、action_label、action_type、action_payload、metadata、created_at、scheduled_at、expires_at、is_read、read_at、is_dismissed、dismissed_at
2. THE Notification_Database SHALL 包含 notification_preferences 表，字段包括 user_id、enabled_types、enable_browser_notifications、enable_in_app_notifications、enable_email_notifications、min_priority_level、quiet_hours、max_notifications_per_hour、updated_at
3. THE Notification_Database SHALL 在 notifications 表的 user_id 字段上创建索引以优化查询性能
4. THE Notification_Database SHALL 在 notifications 表的 created_at 字段上创建索引以支持时间排序
5. THE Notification_Database SHALL 在 notifications 表的 is_read 和 is_dismissed 字段上创建复合索引以支持过滤查询

### 需求 5: 通知 CRUD 操作

**用户故事**: 作为后端开发者，我希望实现通知的创建、读取、更新、删除操作，以便管理通知生命周期。

#### 验收标准

1. THE Python_Backend SHALL 提供 create_notification 方法，接收通知属性并返回新创建的通知 ID
2. THE Python_Backend SHALL 提供 get_notifications 方法，支持按 user_id、project_id、types、unread_only、limit、offset、sort_by 参数过滤和分页
3. THE Python_Backend SHALL 提供 mark_as_read 方法，更新通知的 is_read 和 read_at 字段
4. THE Python_Backend SHALL 提供 dismiss_notification 方法，更新通知的 is_dismissed 和 dismissed_at 字段
5. THE Python_Backend SHALL 提供 batch_dismiss 方法，批量更新多个通知的 is_dismissed 字段
6. WHEN 查询通知时，THE Python_Backend SHALL 排除已过期的通知（expires_at < 当前时间）
7. THE Python_Backend SHALL 在 get_notifications 方法中返回 totalCount、unreadCount、hasMore 元数据

### 需求 6: 通知偏好设置管理

**用户故事**: 作为用户，我希望能够自定义通知偏好设置，以便控制接收哪些类型的通知。

#### 验收标准

1. THE Python_Backend SHALL 提供 get_preferences 方法，返回用户的通知偏好设置
2. THE Python_Backend SHALL 提供 update_preferences 方法，更新用户的通知偏好设置
3. WHEN 用户首次访问偏好设置，THE Python_Backend SHALL 返回默认偏好配置（所有类型启用，优先级为 normal）
4. THE Python_Backend SHALL 验证 enabled_types 数组中的通知类型是否有效
5. THE Python_Backend SHALL 验证 min_priority_level 是否为 urgent、high、normal、low 之一
6. THE Python_Backend SHALL 在更新偏好设置时更新 updated_at 时间戳

### 需求 7: 通知生成和调度

**用户故事**: 作为产品经理，我希望系统能够自动生成和调度通知，以便及时提醒用户重要信息。

#### 验收标准

1. THE Notification_Scheduler SHALL 监听学习进度事件，生成 learning_progress 类型通知
2. THE Notification_Scheduler SHALL 监听任务完成事件，生成 task_completed 类型通知
3. THE Notification_Scheduler SHALL 监听卡顿检测事件，生成 confusion_detected 类型通知
4. WHEN 生成通知时，THE Notification_Scheduler SHALL 检查用户的通知偏好设置，过滤被禁用的通知类型
5. WHEN 生成通知时，THE Notification_Scheduler SHALL 检查通知优先级是否满足用户的 min_priority_level 设置
6. WHEN 在静默时段内，THE Notification_Scheduler SHALL 延迟非紧急通知的发送
7. THE Notification_Scheduler SHALL 为每个通知设置合理的 expires_at 时间（例如 24 小时后）

### 需求 8: 实时通知推送（可选）

**用户故事**: 作为用户，我希望能够实时接收新通知，而无需手动刷新页面。

#### 验收标准

1. WHERE 实时推送功能启用，THE Python_Backend SHALL 维护 WebSocket 连接以推送新通知
2. WHERE 实时推送功能启用，WHEN 新通知创建，THE Python_Backend SHALL 通过 WebSocket 向对应用户推送通知
3. WHERE 实时推送功能启用，THE Tauri_Command_Handler SHALL 监听 WebSocket 消息并转发给前端
4. WHERE 实时推送功能未启用，THE Frontend_Service SHALL 使用轮询机制定期调用 fetch_notifications

### 需求 9: 测试通知功能

**用户故事**: 作为开发者，我希望能够发送测试通知，以便在开发环境中验证通知系统功能。

#### 验收标准

1. WHERE 环境变量 ENABLE_TEST_NOTIFICATIONS 为 true，THE Python_Backend SHALL 实现 POST /api/notifications/test 端点
2. WHERE 测试通知功能启用，THE Python_Backend SHALL 根据 notification_type 参数生成对应类型的测试通知
3. WHERE 测试通知功能启用，THE Python_Backend SHALL 为测试通知添加 [TEST] 前缀以区分真实通知
4. WHERE 环境变量 ENABLE_TEST_NOTIFICATIONS 为 false，THE Python_Backend SHALL 拒绝测试通知请求并返回 HTTP 403 状态码

### 需求 10: 错误处理和日志记录

**用户故事**: 作为运维工程师，我希望系统能够记录详细的错误日志，以便快速定位和解决问题。

#### 验收标准

1. WHEN Tauri 命令执行失败，THE Tauri_Command_Handler SHALL 记录错误日志，包含命令名称、参数和错误信息
2. WHEN HTTP 请求失败，THE HTTP_Client SHALL 记录请求 URL、方法、状态码和响应体
3. WHEN 数据库操作失败，THE Python_Backend SHALL 记录 SQL 语句和错误堆栈
4. THE Python_Backend SHALL 使用结构化日志格式（JSON），包含 timestamp、level、message、context 字段
5. THE Python_Backend SHALL 将错误日志写入日志文件，并在开发环境输出到控制台
6. WHEN 发生 HTTP 500 错误，THE Python_Backend SHALL 返回通用错误消息给客户端，避免泄露内部实现细节

### 需求 11: 数据序列化和反序列化

**用户故事**: 作为开发者，我希望数据在前后端传输时能够正确序列化和反序列化，以便保证数据一致性。

#### 验收标准

1. THE Tauri_Command_Handler SHALL 将 Rust 结构体序列化为 JSON 格式返回给前端
2. THE Tauri_Command_Handler SHALL 将前端传入的 JSON 参数反序列化为 Rust 结构体
3. THE Python_Backend SHALL 将 Python 字典序列化为 JSON 格式返回给 Tauri
4. THE Python_Backend SHALL 将 Tauri 传入的 JSON 请求体反序列化为 Python 字典
5. FOR ALL Notification 对象，序列化后反序列化 SHALL 产生等价的对象（round-trip property）
6. FOR ALL NotificationPreferences 对象，序列化后反序列化 SHALL 产生等价的对象（round-trip property）
7. WHEN 反序列化失败，THE 系统 SHALL 返回包含详细错误信息的 INVALID_REQUEST 错误

### 需求 12: 性能和可扩展性

**用户故事**: 作为系统架构师，我希望通知系统能够高效处理大量请求，以便支持未来的用户增长。

#### 验收标准

1. WHEN 查询通知列表，THE Python_Backend SHALL 在 100ms 内返回结果（数据库包含 10000 条通知）
2. WHEN 批量关闭通知，THE Python_Backend SHALL 使用单个 SQL 语句更新多条记录
3. THE Python_Backend SHALL 使用数据库连接池以复用连接
4. THE Python_Backend SHALL 限制单次查询返回的最大通知数量为 100 条
5. WHEN 通知数量超过 limit 参数，THE Python_Backend SHALL 设置 hasMore 字段为 true
6. THE Notification_Database SHALL 定期清理已过期且已关闭的通知（保留时间 > 30 天）

