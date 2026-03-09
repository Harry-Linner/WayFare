# 通知系统文档

## 概述

Wayfare 通知系统实现了前后端的完整对接，支持多种通知类型、优先级管理、偏好设置和批量操作。

## 架构

```
前端 (React/TypeScript)
    ↓ Tauri 命令
Tauri 中枢 (Rust)
    ↓ HTTP API
Python 后端 (Flask)
    ↓ 数据库操作
SQLite 数据库
```

## 组件

### 1. 数据库层 (`wayfare/db.py`)
- `save_notification()` - 保存通知
- `get_notification()` - 获取单个通知
- `query_notifications()` - 查询通知列表（支持过滤、分页、排序）
- `count_notifications()` - 统计通知数量
- `update_notification()` - 更新通知
- `batch_update_notifications()` - 批量更新通知
- `get_notification_preferences()` - 获取偏好设置
- `save_notification_preferences()` - 保存偏好设置

### 2. 通知管理器 (`wayfare/notification_manager.py`)
- `create_notification()` - 创建新通知（生成 UUID、时间戳、过期时间）
- `get_notifications()` - 获取通知列表（支持过滤、分页、统计）
- `mark_as_read()` - 标记通知为已读
- `dismiss_notification()` - 关闭通知
- `batch_dismiss()` - 批量关闭通知
- `get_preferences()` - 获取偏好设置（返回默认值如果不存在）
- `update_preferences()` - 更新偏好设置（验证输入）
- `create_test_notification()` - 创建测试通知

### 3. Python API (`wayfare/notification_api.py`)

#### 端点列表

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/notifications/fetch` | 获取通知列表 |
| POST | `/api/notifications/:id/read` | 标记通知为已读 |
| DELETE | `/api/notifications/:id` | 关闭通知 |
| POST | `/api/notifications/batch-dismiss` | 批量关闭通知 |
| GET | `/api/notifications/preferences` | 获取偏好设置 |
| PUT | `/api/notifications/preferences` | 更新偏好设置 |
| POST | `/api/notifications/test` | 发送测试通知 |
| GET | `/health` | 健康检查 |

#### 请求示例

**获取通知列表**
```bash
curl -X POST http://localhost:3001/api/notifications/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "limit": 20,
    "offset": 0,
    "types": ["learning_progress"],
    "unread_only": false,
    "sort_by": "recent"
  }'
```

**标记为已读**
```bash
curl -X POST http://localhost:3001/api/notifications/{id}/read \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

### 4. Tauri 命令 (`src-tauri/src/notifications.rs`)

#### 命令列表

| 命令 | 参数 | 返回值 |
|------|------|--------|
| `fetch_notifications` | user_id, project_id?, limit, offset, types, unread_only, sort_by | NotificationBatch |
| `mark_notification_as_read` | notification_id, user_id | Notification |
| `dismiss_notification` | notification_id, user_id | success |
| `batch_dismiss_notifications` | notification_ids, user_id | success |
| `get_notification_preferences` | user_id | NotificationPreferences |
| `update_notification_preferences` | preferences | success |
| `refresh_notification_stream` | user_id | success |
| `send_test_notification` | user_id, notification_type | Notification |

#### 前端调用示例

```typescript
import { invoke } from '@tauri-apps/api/core';

// 获取通知
const batch = await invoke('fetch_notifications', {
  userId: 'user123',
  limit: 20,
  offset: 0,
  types: [],
  unreadOnly: false,
  sortBy: 'recent'
});

// 标记为已读
await invoke('mark_notification_as_read', {
  notificationId: 'notif-123',
  userId: 'user123'
});
```

## 数据模型

### Notification
```typescript
{
  id: string;
  userId: string;
  type: string;  // learning_progress, task_completed, etc.
  title: string;
  message: string;
  priority: string;  // urgent, high, normal, low
  icon?: string;
  actionUrl?: string;
  actionLabel?: string;
  actionType?: string;
  actionPayload?: object;
  metadata?: object;
  createdAt: number;  // Unix timestamp
  scheduledAt?: number;
  expiresAt?: number;
  isRead: boolean;
  readAt?: number;
  isDismissed?: boolean;
  dismissedAt?: number;
}
```

### NotificationPreferences
```typescript
{
  userId: string;
  enabledTypes: string[];
  enableBrowserNotifications: boolean;
  enableInAppNotifications: boolean;
  enableEmailNotifications: boolean;
  minPriorityLevel: string;
  quietHours?: {
    enabled: boolean;
    from: string;  // HH:MM
    to: string;    // HH:MM
  };
  maxNotificationsPerHour?: number;
  updatedAt: number;
}
```

## 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `BACKEND_URL` | `http://localhost:3001` | Python 后端 URL |
| `DATABASE_PATH` | `.wayfare/wayfare.db` | SQLite 数据库路径 |
| `BACKEND_PORT` | `3001` | Flask 服务器端口 |
| `ENABLE_TEST_NOTIFICATIONS` | `false` | 启用测试通知功能 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

## 启动指南

### 1. 初始化数据库
```bash
python -c "import asyncio; from wayfare.init_notification_db import init_notification_tables; asyncio.run(init_notification_tables('.wayfare/wayfare.db'))"
```

### 2. 启动 Python 后端
```bash
export ENABLE_TEST_NOTIFICATIONS=true
python wayfare/notification_api.py
```

### 3. 启动 Tauri 应用
```bash
cd src-tauri
cargo tauri dev
```

## 测试

### 发送测试通知
```bash
curl -X POST http://localhost:3001/api/notifications/test \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "notification_type": "learning_progress"
  }'
```

### 健康检查
```bash
curl http://localhost:3001/health
```

## 错误处理

所有 API 端点返回标准的错误响应：

```json
{
  "error": "错误描述"
}
```

HTTP 状态码：
- `400` - 请求参数错误
- `403` - 权限不足（测试通知未启用）
- `404` - 资源不存在
- `500` - 服务器内部错误
- `503` - 服务不可用（健康检查失败）

Tauri 命令错误格式：
- `NETWORK_ERROR: ...` - 网络连接错误
- `SERVER_ERROR: ...` - 服务器返回错误状态码
- `INVALID_RESPONSE: ...` - 响应解析失败
- `NOT_FOUND: ...` - 资源不存在
- `FORBIDDEN: ...` - 权限不足

## 性能优化

- 查询限制：最大返回 100 条通知
- 数据库索引：user_id, created_at, (is_read, is_dismissed) 复合索引
- 批量操作：使用单个 SQL 语句
- 自动清理：定期删除 30 天前的已关闭通知

## 安全考虑

- 所有操作验证 user_id 权限
- 测试通知功能需要显式启用
- 输入验证防止无效数据
- 错误日志记录便于调试

## 扩展性

### 添加新通知类型
1. 在 `NotificationManager.create_test_notification()` 中添加模板
2. 在前端 `notificationService.ts` 中添加类型定义
3. 更新偏好设置的 `enabled_types` 验证

### 实现通知调度器
参考 `wayfare/notification_scheduler.py`（待实现）：
- 监听学习进度事件
- 监听任务完成事件
- 监听卡顿检测事件
- 根据偏好设置过滤和延迟通知

## 故障排查

### 前端无法获取通知
1. 检查 Python 后端是否运行：`curl http://localhost:3001/health`
2. 检查 BACKEND_URL 环境变量是否正确
3. 查看浏览器控制台和 Tauri 日志

### 数据库错误
1. 确认数据库已初始化
2. 检查数据库文件权限
3. 查看 Python 日志

### 测试通知返回 403
1. 设置环境变量：`export ENABLE_TEST_NOTIFICATIONS=true`
2. 重启 Python 后端

## 相关文档

- [通知协议规范](../NOTIFICATION_PROTOCOL.md)
- [API 设计文档](../.kiro/specs/frontend-backend-notification-integration/design.md)
- [需求文档](../.kiro/specs/frontend-backend-notification-integration/requirements.md)
