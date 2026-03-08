# 通知系统 - 前后端通信协议

## 概述

通知系统采用 **Tauri IPC 通信**，前端通过 Tauri 命令与后端交互。所有通信都经过 Tauri 中枢代理，确保类型安全和进程隔离。

---

## 架构图

```
┌─────────────────────────────────────────────────────┐
│           前端 (React/TypeScript)                    │
│  ┌────────────────────────────────────────────────┐ │
│  │ useNotifications Hook                          │ │
│  │ - fetchNotifications()                         │ │
│  │ - markAsRead()                                 │ │
│  │ - dismissNotification()                        │ │
│  │ - batchDismiss()                               │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ NotificationService (notificationService.ts)   │ │
│  │ - invoke('fetch_notifications', {...})         │ │
│  │ - invoke('mark_notification_as_read', {...})   │ │
│  │ - invoke('dismiss_notification', {...})        │ │
│  │ - invoke('batch_dismiss_notifications', {...}) │ │
│  │ - invoke('get_notification_preferences', {...})│ │
│  │ - invoke('update_notification_preferences', ...)│ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓ Tauri IPC
┌─────────────────────────────────────────────────────┐
│         Tauri 中枢 (Rust - src-tauri)               │
│  ┌────────────────────────────────────────────────┐ │
│  │ Tauri 命令处理器 (commands.rs)                 │ │
│  │ - fetch_notifications                         │ │
│  │ - mark_notification_as_read                   │ │
│  │ - dismiss_notification                        │ │
│  │ - batch_dismiss_notifications                 │ │
│  │ - get_notification_preferences                │ │
│  │ - update_notification_preferences             │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ HTTP 客户端 / WebSocket 连接                   │ │
│  │ → 后端 API 通信                                │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────┐
│         后端服务 (Node.js / Python / Go) │
│  ┌────────────────────────────────────────────────┐ │
│  │ 通知 API 路由                                   │ │
│  │ - POST   /api/notifications/fetch              │ │
│  │ - POST   /api/notifications/:id/read           │ │
│  │ - DELETE /api/notifications/:id                │ │
│  │ - POST   /api/notifications/batch-dismiss      │ │
│  │ - GET    /api/notifications/preferences        │ │
│  │ - PUT    /api/notifications/preferences        │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ 数据库 (notifications 表)                       │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Tauri 命令定义

### 1. 获取通知列表

**命令名**: `fetch_notifications`

**前端调用** (TypeScript):
```typescript
const batch = await invoke<NotificationBatch>('fetch_notifications', {
  user_id: 'user_123',
  project_id: 'proj_456',
  limit: 20,
  offset: 0,
  types: ['learning_progress', 'task_completed'],
  unread_only: false,
  sort_by: 'recent'
});
```

**Tauri 后端需要实现** (Rust):
```rust
#[tauri::command]
async fn fetch_notifications(
    user_id: String,
    project_id: Option<String>,
    limit: u32,
    offset: u32,
    types: Vec<String>,
    unread_only: bool,
    sort_by: String,
) -> Result<NotificationBatch, String> {
    // 调用后端 API 获取通知
    // 返回 NotificationBatch 结构体
}
```

**返回数据结构**:
```typescript
interface NotificationBatch {
  notifications: Notification[];  // 通知数组
  totalCount: number;             // 总通知数
  unreadCount: number;            // 未读通知数
  hasMore: boolean;               // 是否还有更多
}

interface Notification {
  id: string;                     // 通知 ID
  userId: string;
  type: 'learning_progress' | 'task_completed' | 'confusion_detected' | ...;
  title: string;                  // 标题
  message: string;                // 消息内容
  priority: 'urgent' | 'high' | 'normal' | 'low';
  icon?: string;                  // 图标
  actionUrl?: string;             // 点击跳转链接
  actionLabel?: string;           // 按钮文本
  actionType?: 'navigate' | 'open_modal' | 'trigger_task' | 'none';
  actionPayload?: Record<string, any>;
  metadata?: {
    documentId?: string;
    annotationId?: string;
    taskId?: string;
    projectId?: string;
    currentProgress?: number;
    targetProgress?: number;
    questionCount?: number;
    completedCount?: number;
    estimatedTimeMinutes?: number;
    dueDate?: number;
    [key: string]: any;
  };
  createdAt: number;              // 创建时间戳
  scheduledAt?: number;
  expiresAt?: number;
  isRead: boolean;
  readAt?: number;
  isDismissed?: boolean;
  dismissedAt?: number;
}
```

---

### 2. 标记通知为已读

**命令名**: `mark_notification_as_read`

**前端调用**:
```typescript
const updated = await invoke<Notification>('mark_notification_as_read', {
  notification_id: 'notif_789',
  user_id: 'user_123'
});
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn mark_notification_as_read(
    notification_id: String,
    user_id: String,
) -> Result<Notification, String> {
    // 调用后端 API 标记为已读
    // 返回更新后的通知对象
}
```

**返回**: 更新后的 `Notification` 对象

---

### 3. 关闭通知

**命令名**: `dismiss_notification`

**前端调用**:
```typescript
const result = await invoke<{ dismissed: boolean }>('dismiss_notification', {
  notification_id: 'notif_789',
  user_id: 'user_123'
});
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn dismiss_notification(
    notification_id: String,
    user_id: String,
) -> Result<DismissResponse, String> {
    // 返回 { dismissed: true }
}
```

**返回**:
```typescript
{
  dismissed: boolean  // true 表示成功关闭
}
```

---

### 4. 批量关闭通知

**命令名**: `batch_dismiss_notifications`

**前端调用**:
```typescript
const result = await invoke<{ status: string }>('batch_dismiss_notifications', {
  notification_ids: ['notif_1', 'notif_2', 'notif_3'],
  user_id: 'user_123'
});
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn batch_dismiss_notifications(
    notification_ids: Vec<String>,
    user_id: String,
) -> Result<BatchDismissResponse, String> {
    // 批量关闭通知
    // 返回 { status: 'success' }
}
```

**返回**:
```typescript
{
  status: 'success' | 'partial_failure' | 'failure'
}
```

---

### 5. 获取通知偏好设置

**命令名**: `get_notification_preferences`

**前端调用**:
```typescript
const prefs = await invoke<NotificationPreferences>('get_notification_preferences', {
  user_id: 'user_123'
});
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn get_notification_preferences(
    user_id: String,
) -> Result<NotificationPreferences, String> {
    // 获取用户的通知偏好设置
}
```

**返回数据结构**:
```typescript
interface NotificationPreferences {
  userId: string;
  enabledTypes: string[];              // 启用的通知类型
  enableBrowserNotifications: boolean;
  enableInAppNotifications: boolean;
  enableEmailNotifications: boolean;
  minPriorityLevel: 'urgent' | 'high' | 'normal' | 'low';
  quietHours?: {
    enabled: boolean;
    from: string;   // "22:00"
    to: string;     // "08:00"
  };
  maxNotificationsPerHour?: number;
  updatedAt: number;
}
```

---

### 6. 更新通知偏好设置

**命令名**: `update_notification_preferences`

**前端调用**:
```typescript
const success = await invoke<{ status: string }>(
  'update_notification_preferences',
  {
    preferences: {
      userId: 'user_123',
      enabledTypes: ['learning_progress', 'task_completed'],
      enableBrowserNotifications: true,
      enableInAppNotifications: true,
      enableEmailNotifications: false,
      minPriorityLevel: 'normal',
      updatedAt: Date.now()
    }
  }
);
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn update_notification_preferences(
    preferences: NotificationPreferences,
) -> Result<UpdateResponse, String> {
    // 更新用户偏好设置
    // 返回 { status: 'success' }
}
```

**返回**:
```typescript
{
  status: 'success' | 'failure'
}
```

---

### 7. 刷新通知流

**命令名**: `refresh_notification_stream`

**前端调用**:
```typescript
const success = await invoke<{ success: boolean }>(
  'refresh_notification_stream',
  {
    user_id: 'user_123'
  }
);
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn refresh_notification_stream(
    user_id: String,
) -> Result<RefreshResponse, String> {
    // 刷新 WebSocket 或轮询连接
    // 返回 { success: true }
}
```

---

### 8. 发送测试通知（仅开发）

**命令名**: `send_test_notification`

**前端调用**:
```typescript
const notif = await invoke<Notification>('send_test_notification', {
  user_id: 'user_123',
  notification_type: 'learning_progress'
});
```

**Tauri 后端**:
```rust
#[tauri::command]
async fn send_test_notification(
    user_id: String,
    notification_type: String,
) -> Result<Notification, String> {
    // 仅在开发环境使用
    // 返回生成的测试通知
}
```

---

## 通知类型详解

### 1. 学习进度 (`learning_progress`)
```typescript
{
  type: 'learning_progress',
  title: '学习进度更新',
  message: '您在认知心理学的进度已达到 75%',
  priority: 'normal',
  metadata: {
    documentId: 'doc_123',
    currentProgress: 75,
    targetProgress: 100,
    topicsLearned: ['导数', '极限'],
    nextTopic: '积分'
  }
}
```

### 2. 任务完成 (`task_completed`)
```typescript
{
  type: 'task_completed',
  title: '任务完成',
  message: '您已完成今日的学习任务',
  priority: 'high',
  metadata: {
    taskId: 'task_456',
    taskName: '每日复习',
    completionTime: 1800,  // 秒
    points: 50
  }
}
```

### 3. 卡顿检测 (`confusion_detected`)
```typescript
{
  type: 'confusion_detected',
  title: '需要帮助？',
  message: '您在导数定义这里停留了很久',
  priority: 'high',
  metadata: {
    documentId: 'doc_123',
    annotationId: 'anno_789',
    topic: '导数定义',
    timeStuckSeconds: 300,
    suggestedActions: [
      { action: 'hint', description: '获取提示' },
      { action: 'resource', description: '查看补充资源' }
    ]
  }
}
```

### 4. 待处理问题 (`pending_questions`)
```typescript
{
  type: 'pending_questions',
  title: '待处理问题',
  message: '您有 2 个待处理的问题需要回答',
  priority: 'normal',
  metadata: {
    questionCount: 2,
    completedCount: 0,
    topicsWithQuestions: ['导数', '积分']
  }
}
```

### 5. 成就解锁 (`achievement_unlocked`)
```typescript
{
  type: 'achievement_unlocked',
  title: '🎉 成就解锁',
  message: '完成 10 次复习 - 复习小能手',
  priority: 'high',
  metadata: {
    achievementId: 'ach_001',
    achievementName: '复习小能手',
    points: 100,
    nextAchievement: {
      name: '复习达人',
      progress: 50
    }
  }
}
```

---

## 错误处理

所有 Tauri 命令可能抛出错误，前端应优雅处理：

```typescript
try {
  const batch = await notificationService.fetchNotifications({
    userId: 'user_123',
    limit: 20
  });
} catch (error) {
  console.error('Failed to fetch notifications:', error);
  // 显示错误提示给用户
  // 可选：重试逻辑
}
```

**常见错误码**:
- `UNAUTHORIZED` - 用户未授权
- `INVALID_REQUEST` - 请求参数错误
- `NOT_FOUND` - 资源不存在
- `SERVER_ERROR` - 后端服务错误
- `NETWORK_ERROR` - 网络连接失败

---

## 实时推送（可选）

对于实时通知推送，Tauri 中枢可实现 WebSocket 监听器：

```typescript
// 监听后端推送的新通知
const unsubscribe = useNotifications({
  onNotification: (notification: Notification) => {
    // 处理新通知
    console.log('New notification:', notification);
  }
});

// 清理时取消订阅
unsubscribe();
```

---

## 环境变量

**开发环境** (.env.development):
```
VITE_TAURI_API_ENDPOINT=http://localhost:3001
VITE_ENABLE_TEST_NOTIFICATIONS=true
```

**生产环境** (.env.production):
```
VITE_TAURI_API_ENDPOINT=https://api.wayfare.com
VITE_ENABLE_TEST_NOTIFICATIONS=false
```

---

## 总结

| 操作 | 命令名 | 请求数据 | 返回数据 |
|------|--------|---------|---------|
| 获取列表 | `fetch_notifications` | userId, projectId, limit, offset, ... | NotificationBatch |
| 标记已读 | `mark_notification_as_read` | notificationId, userId | Notification |
| 关闭通知 | `dismiss_notification` | notificationId, userId | { dismissed: boolean } |
| 批量关闭 | `batch_dismiss_notifications` | notificationIds[], userId | { status: string } |
| 获取偏好 | `get_notification_preferences` | userId | NotificationPreferences |
| 更新偏好 | `update_notification_preferences` | preferences | { status: string } |
| 刷新流 | `refresh_notification_stream` | userId | { success: boolean } |
| 测试通知 | `send_test_notification` | userId, type | Notification |
