# 设计文档 - 前后端通知系统对接

## 概述

本设计文档描述前后端通知系统对接的技术实现方案。系统采用三层架构：前端 (React/TypeScript) → Tauri 中枢 (Rust) → Python 后端，通过 HTTP API 实现通知的完整生命周期管理。

设计目标：
- 复用现有的 wayfare/ipc.py 和 wayfare/db.py 基础设施
- 在 Tauri 中实现 8 个命令处理器，代理前端请求到 Python 后端
- 在 Python 后端实现 RESTful API 端点和通知生成逻辑
- 支持通知的 CRUD 操作、偏好设置管理和实时推送（可选）
- 确保数据一致性和错误处理

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────┐
│           前端 (React/TypeScript)                    │
│  ┌────────────────────────────────────────────────┐ │
│  │ NotificationService                            │ │
│  │ - fetchNotifications()                         │ │
│  │ - markAsRead()                                 │ │
│  │ - dismissNotification()                        │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓ Tauri IPC
┌─────────────────────────────────────────────────────┐
│         Tauri 中枢 (Rust - src-tauri)               │
│  ┌────────────────────────────────────────────────┐ │
│  │ 命令处理器 (commands/notifications.rs)         │ │
│  │ - fetch_notifications                         │ │
│  │ - mark_notification_as_read                   │ │
│  │ - dismiss_notification                        │ │
│  │ - batch_dismiss_notifications                 │ │
│  │ - get_notification_preferences                │ │
│  │ - update_notification_preferences             │ │
│  │ - refresh_notification_stream                 │ │
│  │ - send_test_notification                      │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ HTTP 客户端 (reqwest)                          │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓ HTTP
┌─────────────────────────────────────────────────────┐
│         Python 后端 (Flask/FastAPI)                 │
│  ┌────────────────────────────────────────────────┐ │
│  │ API 路由 (notification_api.py)                 │ │
│  │ - POST /api/notifications/fetch                   │ │
│  │ - POST /api/notifications/:id/read             │ │
│  │ - DELETE /api/notifications/:id                │ │
│  │ - POST /api/notifications/batch-dismiss        │ │
│  │ - GET /api/notifications/preferences           │ │
│  │ - PUT /api/notifications/preferences           │ │
│  │ - POST /api/notifications/test                 │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ 通知管理器 (notification_manager.py)           │ │
│  │ - create_notification()                        │ │
│  │ - get_notifications()                          │ │
│  │ - mark_as_read()                               │ │
│  │ - dismiss_notification()                       │ │
│  │ - batch_dismiss()                              │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ 通知调度器 (notification_scheduler.py)         │ │
│  │ - 监听学习进度事件                             │ │
│  │ - 监听任务完成事件                             │ │
│  │ - 监听卡顿检测事件                             │ │
│  │ - 检查用户偏好设置                             │ │
│  └────────────────────────────────────────────────┘ │
│                        ↓                             │
│  ┌────────────────────────────────────────────────┐ │
│  │ SQLite 数据库 (wayfare/db.py)                  │ │
│  │ - notifications 表                             │ │
│  │ - notification_preferences 表                  │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 数据流

#### 获取通知列表流程
```
1. 前端调用 fetchNotifications()
   ↓
2. Tauri 命令处理器接收请求
   ↓
3. HTTP 客户端发送 POST /api/notifications/fetch
   ↓
4. Python API 路由验证参数
   ↓
5. NotificationManager 查询数据库
   - 按 user_id、project_id 过滤
   - 按 types、unread_only 过滤
   - 分页 (limit, offset)
   - 排序 (sort_by)
   ↓
6. 返回 NotificationBatch 给 Tauri
   ↓
7. Tauri 序列化为 JSON 返回前端
```

#### 标记已读流程
```
1. 前端调用 markAsRead(notificationId)
   ↓
2. Tauri 命令处理器接收请求
   ↓
3. HTTP 客户端发送 POST /api/notifications/:id/read
   ↓
4. Python API 路由验证权限
   ↓
5. NotificationManager 更新数据库
   - 设置 is_read = true
   - 设置 read_at = 当前时间
   ↓
6. 返回更新后的 Notification 对象
   ↓
7. Tauri 返回给前端
```

#### 通知生成流程
```
1. 后端事件触发 (学习进度/任务完成/卡顿检测)
   ↓
2. NotificationScheduler 接收事件
   ↓
3. 查询用户偏好设置
   - 检查通知类型是否启用
   - 检查优先级是否满足
   - 检查静默时段
   ↓
4. 如果满足条件，调用 NotificationManager.create_notification()
   ↓
5. 保存到数据库
   ↓
6. (可选) 通过 WebSocket 推送给前端
```

## 组件和接口

### 1. Tauri 命令处理器 (Rust)

位置: `src-tauri/src/commands/notifications.rs`

#### 数据结构
```rust
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize, Deserialize)]
pub struct Notification {
    pub id: String,
    pub user_id: String,
    pub r#type: String,
    pub title: String,
    pub message: String,
    pub priority: String,
    pub icon: Option<String>,
    pub action_url: Option<String>,
    pub action_label: Option<String>,
    pub action_type: Option<String>,
    pub action_payload: Option<HashMap<String, serde_json::Value>>,
    pub metadata: Option<HashMap<String, serde_json::Value>>,
    pub created_at: i64,
    pub scheduled_at: Option<i64>,
    pub expires_at: Option<i64>,
    pub is_read: bool,
    pub read_at: Option<i64>,
    pub is_dismissed: Option<bool>,
    pub dismissed_at: Option<i64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NotificationBatch {
    pub notifications: Vec<Notification>,
    pub total_count: i32,
    pub unread_count: i32,
    pub has_more: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NotificationPreferences {
    pub user_id: String,
    pub enabled_types: Vec<String>,
    pub enable_browser_notifications: bool,
    pub enable_in_app_notifications: bool,
    pub enable_email_notifications: bool,
    pub min_priority_level: String,
    pub quiet_hours: Option<QuietHours>,
    pub max_notifications_per_hour: Option<i32>,
    pub updated_at: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QuietHours {
    pub enabled: bool,
    pub from: String,
    pub to: String,
}
```

#### 命令实现

```rust
use reqwest::Client;
use tauri::State;

pub struct AppState {
    pub http_client: Client,
    pub backend_url: String,
}

#[tauri::command]
pub async fn fetch_notifications(
    state: State<'_, AppState>,
    user_id: String,
    project_id: Option<String>,
    limit: u32,
    offset: u32,
    types: Vec<String>,
    unread_only: bool,
    sort_by: String,
) -> Result<NotificationBatch, String> {
    let url = format!("{}/api/notifications/fetch", state.backend_url);
    
    let body = serde_json::json!({
        "user_id": user_id,
        "project_id": project_id,
        "limit": limit,
        "offset": offset,
        "types": types,
        "unread_only": unread_only,
        "sort_by": sort_by,
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json::<NotificationBatch>()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}
```

#[tauri::command]
pub async fn mark_notification_as_read(
    state: State<'_, AppState>,
    notification_id: String,
    user_id: String,
) -> Result<Notification, String> {
    let url = format!("{}/api/notifications/{}/read", state.backend_url, notification_id);
    
    let body = serde_json::json!({
        "user_id": user_id,
    });
    
    let response = state.http_client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if response.status() == 404 {
        return Err("NOT_FOUND: Notification not found".to_string());
    }
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json::<Notification>()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}

#[tauri::command]
pub async fn dismiss_notification(
    state: State<'_, AppState>,
    notification_id: String,
    user_id: String,
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/notifications/{}", state.backend_url, notification_id);
    
    let response = state.http_client
        .delete(&url)
        .query(&[("user_id", user_id)])
        .send()
        .await
        .map_err(|e| format!("NETWORK_ERROR: {}", e))?;
    
    if !response.status().is_success() {
        return Err(format!("SERVER_ERROR: {}", response.status()));
    }
    
    response.json()
        .await
        .map_err(|e| format!("INVALID_RESPONSE: {}", e))
}
```

### 2. Python 后端 API

位置: `wayfare/notification_api.py`

#### Flask 实现示例

```python
from flask import Flask, request, jsonify
from wayfare.notification_manager import NotificationManager
from wayfare.db import SQLiteDB
import logging

logger = logging.getLogger(__name__)
app = Flask(__name__)

# 初始化
db = SQLiteDB()
notification_manager = NotificationManager(db)

@app.route('/api/notifications/fetch', methods=['POST'])
async def fetch_notifications():
    """获取通知列表"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id'}), 400
        
        user_id = data['user_id']
        project_id = data.get('project_id')
        limit = data.get('limit', 20)
        offset = data.get('offset', 0)
        types = data.get('types', [])
        unread_only = data.get('unread_only', False)
        sort_by = data.get('sort_by', 'recent')
        
        # 调用 NotificationManager
        batch = await notification_manager.get_notifications(
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
            types=types,
            unread_only=unread_only,
            sort_by=sort_by
        )
        
        return jsonify(batch), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
async def mark_as_read(notification_id):
    """标记通知为已读"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        notification = await notification_manager.mark_as_read(
            notification_id=notification_id,
            user_id=user_id
        )
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        return jsonify(notification), 200
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
```

@app.route('/api/notifications/<notification_id>', methods=['DELETE'])
async def dismiss_notification(notification_id):
    """关闭通知"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        success = await notification_manager.dismiss_notification(
            notification_id=notification_id,
            user_id=user_id
        )
        
        if not success:
            return jsonify({'error': 'Notification not found'}), 404
        
        return jsonify({'dismissed': True}), 200
        
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/batch-dismiss', methods=['POST'])
async def batch_dismiss():
    """批量关闭通知"""
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        user_id = data.get('user_id')
        
        if not user_id or not notification_ids:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        await notification_manager.batch_dismiss(
            notification_ids=notification_ids,
            user_id=user_id
        )
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error batch dismissing: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/preferences', methods=['GET'])
async def get_preferences():
    """获取通知偏好设置"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        prefs = await notification_manager.get_preferences(user_id)
        
        return jsonify(prefs), 200
        
    except Exception as e:
        logger.error(f"Error getting preferences: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
```

@app.route('/api/notifications/preferences', methods=['PUT'])
async def update_preferences():
    """更新通知偏好设置"""
    try:
        prefs = request.get_json()
        
        if 'user_id' not in prefs:
            return jsonify({'error': 'Missing user_id'}), 400
        
        await notification_manager.update_preferences(prefs)
        
        return jsonify({'status': 'success'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/notifications/test', methods=['POST'])
async def send_test_notification():
    """发送测试通知（仅开发环境）"""
    import os
    
    if os.getenv('ENABLE_TEST_NOTIFICATIONS') != 'true':
        return jsonify({'error': 'Test notifications disabled'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        notification_type = data.get('notification_type', 'learning_progress')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        notification = await notification_manager.create_test_notification(
            user_id=user_id,
            notification_type=notification_type
        )
        
        return jsonify(notification), 200
        
    except Exception as e:
        logger.error(f"Error creating test notification: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
```

### 3. 通知管理器

位置: `wayfare/notification_manager.py`

```python
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from wayfare.db import SQLiteDB

class NotificationManager:
    """通知管理器，负责通知的 CRUD 操作"""
    
    def __init__(self, db: SQLiteDB):
        self.db = db
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = 'normal',
        **kwargs
    ) -> Dict[str, Any]:
        """创建新通知"""
        notification_id = str(uuid4())
        now = datetime.now(timezone.utc)
        
        notification = {
            'id': notification_id,
            'user_id': user_id,
            'type': notification_type,
            'title': title,
            'message': message,
            'priority': priority,
            'created_at': int(now.timestamp()),
            'expires_at': int((now + timedelta(hours=24)).timestamp()),
            'is_read': False,
            'is_dismissed': False,
            **kwargs
        }
        
        await self.db.save_notification(notification)
        return notification

    async def get_notifications(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        types: List[str] = None,
        unread_only: bool = False,
        sort_by: str = 'recent'
    ) -> Dict[str, Any]:
        """获取通知列表"""
        # 构建查询条件
        filters = {'user_id': user_id}
        if project_id:
            filters['project_id'] = project_id
        if types:
            filters['types'] = types
        if unread_only:
            filters['is_read'] = False
        
        # 排除已过期的通知
        now = int(datetime.now(timezone.utc).timestamp())
        filters['expires_at_gt'] = now
        
        # 查询通知
        notifications = await self.db.query_notifications(
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by
        )
        
        # 统计总数和未读数
        total_count = await self.db.count_notifications(filters)
        unread_count = await self.db.count_notifications({
            **filters,
            'is_read': False
        })
        
        return {
            'notifications': notifications,
            'total_count': total_count,
            'unread_count': unread_count,
            'has_more': (offset + len(notifications)) < total_count
        }
    
    async def mark_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """标记通知为已读"""
        notification = await self.db.get_notification(notification_id)
        
        if not notification or notification['user_id'] != user_id:
            return None
        
        now = int(datetime.now(timezone.utc).timestamp())
        await self.db.update_notification(notification_id, {
            'is_read': True,
            'read_at': now
        })
        
        notification['is_read'] = True
        notification['read_at'] = now
        return notification
    
    async def dismiss_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """关闭通知"""
        notification = await self.db.get_notification(notification_id)
        
        if not notification or notification['user_id'] != user_id:
            return False
        
        now = int(datetime.now(timezone.utc).timestamp())
        await self.db.update_notification(notification_id, {
            'is_dismissed': True,
            'dismissed_at': now
        })
        
        return True

    async def batch_dismiss(
        self,
        notification_ids: List[str],
        user_id: str
    ):
        """批量关闭通知"""
        now = int(datetime.now(timezone.utc).timestamp())
        
        # 使用单个 SQL 语句批量更新
        await self.db.batch_update_notifications(
            notification_ids=notification_ids,
            user_id=user_id,
            updates={
                'is_dismissed': True,
                'dismissed_at': now
            }
        )
    
    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好设置"""
        prefs = await self.db.get_notification_preferences(user_id)
        
        if not prefs:
            # 返回默认偏好
            return {
                'user_id': user_id,
                'enabled_types': [
                    'learning_progress',
                    'task_completed',
                    'confusion_detected',
                    'pending_questions',
                    'achievement_unlocked'
                ],
                'enable_browser_notifications': True,
                'enable_in_app_notifications': True,
                'enable_email_notifications': False,
                'min_priority_level': 'normal',
                'updated_at': int(datetime.now(timezone.utc).timestamp())
            }
        
        return prefs
    
    async def update_preferences(self, prefs: Dict[str, Any]):
        """更新用户偏好设置"""
        # 验证通知类型
        valid_types = [
            'learning_progress', 'task_completed', 'confusion_detected',
            'pending_questions', 'achievement_unlocked'
        ]
        enabled_types = prefs.get('enabled_types', [])
        for t in enabled_types:
            if t not in valid_types:
                raise ValueError(f"Invalid notification type: {t}")
        
        # 验证优先级
        valid_priorities = ['urgent', 'high', 'normal', 'low']
        min_priority = prefs.get('min_priority_level', 'normal')
        if min_priority not in valid_priorities:
            raise ValueError(f"Invalid priority level: {min_priority}")
        
        # 更新时间戳
        prefs['updated_at'] = int(datetime.now(timezone.utc).timestamp())
        
        await self.db.save_notification_preferences(prefs)
```

## 数据模型

### 数据库表结构

#### notifications 表

```sql
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    icon TEXT,
    action_url TEXT,
    action_label TEXT,
    action_type TEXT,
    action_payload TEXT,  -- JSON
    metadata TEXT,        -- JSON
    created_at INTEGER NOT NULL,
    scheduled_at INTEGER,
    expires_at INTEGER,
    is_read BOOLEAN NOT NULL DEFAULT 0,
    read_at INTEGER,
    is_dismissed BOOLEAN NOT NULL DEFAULT 0,
    dismissed_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_read_dismissed 
    ON notifications(is_read, is_dismissed);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_expires_at ON notifications(expires_at);
```

#### notification_preferences 表

```sql
CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id TEXT PRIMARY KEY,
    enabled_types TEXT NOT NULL,  -- JSON array
    enable_browser_notifications BOOLEAN NOT NULL DEFAULT 1,
    enable_in_app_notifications BOOLEAN NOT NULL DEFAULT 1,
    enable_email_notifications BOOLEAN NOT NULL DEFAULT 0,
    min_priority_level TEXT NOT NULL DEFAULT 'normal',
    quiet_hours TEXT,  -- JSON: {"enabled": bool, "from": "22:00", "to": "08:00"}
    max_notifications_per_hour INTEGER,
    updated_at INTEGER NOT NULL
);
```

### 数据库操作扩展

需要在 `wayfare/db.py` 中添加以下方法：

```python
# 在 SQLiteDB 类中添加

async def save_notification(self, notification: Dict[str, Any]):
    """保存通知"""
    import json
    async with aiosqlite.connect(self.db_path) as db:
        await db.execute("""
            INSERT INTO notifications
            (id, user_id, type, title, message, priority, icon,
             action_url, action_label, action_type, action_payload,
             metadata, created_at, scheduled_at, expires_at,
             is_read, is_dismissed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            notification['id'],
            notification['user_id'],
            notification['type'],
            notification['title'],
            notification['message'],
            notification['priority'],
            notification.get('icon'),
            notification.get('action_url'),
            notification.get('action_label'),
            notification.get('action_type'),
            json.dumps(notification.get('action_payload')) if notification.get('action_payload') else None,
            json.dumps(notification.get('metadata')) if notification.get('metadata') else None,
            notification['created_at'],
            notification.get('scheduled_at'),
            notification.get('expires_at'),
            notification.get('is_read', False),
            notification.get('is_dismissed', False)
        ))
        await db.commit()

async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
    """获取单个通知"""
    import json
    async with aiosqlite.connect(self.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM notifications WHERE id = ?",
            (notification_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                notif = dict(row)
                if notif.get('action_payload'):
                    notif['action_payload'] = json.loads(notif['action_payload'])
                if notif.get('metadata'):
                    notif['metadata'] = json.loads(notif['metadata'])
                return notif
            return None

async def query_notifications(
    self,
    filters: Dict[str, Any],
    limit: int = 20,
    offset: int = 0,
    sort_by: str = 'recent'
) -> List[Dict[str, Any]]:
    """查询通知列表"""
    import json
    
    # 构建 WHERE 子句
    where_clauses = []
    params = []
    
    if 'user_id' in filters:
        where_clauses.append("user_id = ?")
        params.append(filters['user_id'])
    
    if 'project_id' in filters:
        where_clauses.append("json_extract(metadata, '$.projectId') = ?")
        params.append(filters['project_id'])
    
    if 'types' in filters and filters['types']:
        placeholders = ','.join('?' * len(filters['types']))
        where_clauses.append(f"type IN ({placeholders})")
        params.extend(filters['types'])
    
    if 'is_read' in filters:
        where_clauses.append("is_read = ?")
        params.append(filters['is_read'])
    
    if 'expires_at_gt' in filters:
        where_clauses.append("(expires_at IS NULL OR expires_at > ?)")
        params.append(filters['expires_at_gt'])
    
    # 默认不返回已关闭的通知
    where_clauses.append("is_dismissed = 0")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # 排序
    order_by = "created_at DESC" if sort_by == 'recent' else "priority DESC, created_at DESC"
    
    query = f"""
        SELECT * FROM notifications
        WHERE {where_sql}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    
    async with aiosqlite.connect(self.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            notifications = []
            for row in rows:
                notif = dict(row)
                if notif.get('action_payload'):
                    notif['action_payload'] = json.loads(notif['action_payload'])
                if notif.get('metadata'):
                    notif['metadata'] = json.loads(notif['metadata'])
                notifications.append(notif)
            return notifications

async def count_notifications(self, filters: Dict[str, Any]) -> int:
    """统计通知数量"""
    where_clauses = []
    params = []
    
    if 'user_id' in filters:
        where_clauses.append("user_id = ?")
        params.append(filters['user_id'])
    
    if 'is_read' in filters:
        where_clauses.append("is_read = ?")
        params.append(filters['is_read'])
    
    if 'expires_at_gt' in filters:
        where_clauses.append("(expires_at IS NULL OR expires_at > ?)")
        params.append(filters['expires_at_gt'])
    
    where_clauses.append("is_dismissed = 0")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    async with aiosqlite.connect(self.db_path) as db:
        async with db.execute(
            f"SELECT COUNT(*) FROM notifications WHERE {where_sql}",
            params
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def update_notification(
    self,
    notification_id: str,
    updates: Dict[str, Any]
):
    """更新通知"""
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ?")
        params.append(value)
    
    params.append(notification_id)
    
    set_sql = ", ".join(set_clauses)
    
    async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            f"UPDATE notifications SET {set_sql} WHERE id = ?",
            params
        )
        await db.commit()

async def batch_update_notifications(
    self,
    notification_ids: List[str],
    user_id: str,
    updates: Dict[str, Any]
):
    """批量更新通知"""
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ?")
        params.append(value)
    
    placeholders = ','.join('?' * len(notification_ids))
    params.extend(notification_ids)
    params.append(user_id)
    
    set_sql = ", ".join(set_clauses)
    
    async with aiosqlite.connect(self.db_path) as db:
        await db.execute(
            f"""
            UPDATE notifications 
            SET {set_sql}
            WHERE id IN ({placeholders}) AND user_id = ?
            """,
            params
        )
        await db.commit()

async def get_notification_preferences(
    self,
    user_id: str
) -> Optional[Dict[str, Any]]:
    """获取通知偏好设置"""
    import json
    async with aiosqlite.connect(self.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM notification_preferences WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                prefs = dict(row)
                prefs['enabled_types'] = json.loads(prefs['enabled_types'])
                if prefs.get('quiet_hours'):
                    prefs['quiet_hours'] = json.loads(prefs['quiet_hours'])
                return prefs
            return None

async def save_notification_preferences(self, prefs: Dict[str, Any]):
    """保存通知偏好设置"""
    import json
    async with aiosqlite.connect(self.db_path) as db:
        await db.execute("""
            INSERT OR REPLACE INTO notification_preferences
            (user_id, enabled_types, enable_browser_notifications,
             enable_in_app_notifications, enable_email_notifications,
             min_priority_level, quiet_hours, max_notifications_per_hour,
             updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prefs['user_id'],
            json.dumps(prefs['enabled_types']),
            prefs.get('enable_browser_notifications', True),
            prefs.get('enable_in_app_notifications', True),
            prefs.get('enable_email_notifications', False),
            prefs.get('min_priority_level', 'normal'),
            json.dumps(prefs['quiet_hours']) if prefs.get('quiet_hours') else None,
            prefs.get('max_notifications_per_hour'),
            prefs['updated_at']
        ))
        await db.commit()
```

现在我需要进行 prework 分析，然后编写正确性属性。让我使用 prework 工具：

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

基于需求文档的验收标准，我们识别出以下可测试的正确性属性。这些属性将通过基于属性的测试（Property-Based Testing）进行验证，确保系统在各种输入下的正确性。

### 属性反思

在编写属性之前，我们进行了冗余分析：

1. **命令处理器属性合并**: 需求 1.1-1.8 都是测试命令处理器的存在性，可以合并为一个综合属性
2. **HTTP 端点属性合并**: 需求 2.1-2.6 和 3.1-3.6 测试类似的端点功能，可以合并
3. **CRUD 操作属性**: 需求 5.1-5.5 的创建、读取、更新、删除操作可以通过 round-trip 属性验证
4. **偏好设置属性**: 需求 6.1-6.2 的读写操作可以合并为 round-trip 属性
5. **序列化属性**: 需求 11.5-11.6 已经明确是 round-trip 属性，无需重复

### 属性 1: Tauri 命令处理器完整性

*对于任意*有效的命令名称（fetch_notifications, mark_notification_as_read, dismiss_notification, batch_dismiss_notifications, get_notification_preferences, update_notification_preferences, refresh_notification_stream, send_test_notification），调用该命令应该返回成功响应或明确的错误，而不是崩溃或超时。

**验证需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8**

### 属性 2: 命令错误处理

*对于任意*导致错误的输入（如无效的 notification_id、缺失的 user_id），Tauri 命令处理器应该返回包含错误类型和错误消息的 Result::Err，而不是 panic 或返回成功。

**验证需求: 1.9, 2.7**

### 属性 3: HTTP 请求格式正确性

*对于任意*Tauri 命令调用，发送到 Python 后端的 HTTP 请求应该包含正确的 Content-Type 头（application/json）、正确的 HTTP 方法（POST/GET/PUT/DELETE）和正确的端点路径。

**验证需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8**

### 属性 4: API 端点输入验证

*对于任意*缺失必需参数或包含无效值的请求，Python 后端 API 应该返回 HTTP 400 状态码和描述性错误消息。

**验证需求: 3.7, 6.4, 6.5**

### 属性 5: 通知 CRUD Round-Trip

*对于任意*有效的通知对象，执行以下操作序列应该保持数据一致性：
1. 创建通知 (create_notification)
2. 查询通知 (get_notifications) - 应该能找到刚创建的通知
3. 标记为已读 (mark_as_read) - is_read 应该变为 true
4. 再次查询 - 应该反映已读状态
5. 关闭通知 (dismiss_notification) - is_dismissed 应该变为 true
6. 查询未关闭通知 - 不应该包含已关闭的通知

**验证需求: 5.1, 5.2, 5.3, 5.4**

### 属性 6: 批量操作一致性

*对于任意*通知 ID 列表，批量关闭操作 (batch_dismiss) 应该等价于对每个 ID 单独执行关闭操作，即所有指定的通知都应该被标记为已关闭。

**验证需求: 5.5**

### 属性 7: 通知过滤正确性

*对于任意*通知集合和过滤条件（user_id, project_id, types, unread_only），查询结果应该只包含满足所有过滤条件的通知，且不应该包含已过期的通知（expires_at < 当前时间）。

**验证需求: 5.2, 5.6**

### 属性 8: 分页元数据正确性

*对于任意*通知集合和分页参数（limit, offset），返回的 NotificationBatch 应该满足：
- totalCount 等于满足过滤条件的通知总数
- unreadCount 等于满足过滤条件且未读的通知数
- hasMore 为 true 当且仅当 (offset + 返回的通知数) < totalCount
- 返回的通知数不超过 limit

**验证需求: 5.7, 12.5**

### 属性 9: 偏好设置 Round-Trip

*对于任意*有效的 NotificationPreferences 对象，执行以下操作应该得到等价的对象：
1. 保存偏好设置 (update_preferences)
2. 读取偏好设置 (get_preferences)
3. 比较读取的对象与原始对象，所有字段应该相等（updated_at 可能不同）

**验证需求: 6.1, 6.2, 6.6**

### 属性 10: 通知调度器偏好过滤

*对于任意*用户和事件类型，如果用户的偏好设置中禁用了该通知类型或该通知的优先级低于用户设置的最低优先级，则 NotificationScheduler 不应该生成该通知。

**验证需求: 7.4, 7.5**

### 属性 11: 静默时段延迟

*对于任意*非紧急通知（priority != 'urgent'），如果当前时间在用户设置的静默时段内（quiet_hours.enabled = true 且当前时间在 from 和 to 之间），则该通知的 scheduled_at 应该被设置为静默时段结束后，而不是立即发送。

**验证需求: 7.6**

### 属性 12: 通知过期时间设置

*对于任意*新创建的通知，其 expires_at 字段应该被设置为一个未来的时间戳（大于 created_at），且默认应该是创建时间后 24 小时。

**验证需求: 7.7**

### 属性 13: 数据序列化 Round-Trip

*对于任意*Notification 或 NotificationPreferences 对象，执行以下操作应该得到等价的对象：
1. 将对象序列化为 JSON 字符串
2. 将 JSON 字符串反序列化为对象
3. 比较反序列化的对象与原始对象，所有字段应该相等

**验证需求: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**

### 属性 14: 反序列化错误处理

*对于任意*无效的 JSON 字符串（格式错误、缺失必需字段、类型不匹配），尝试反序列化应该返回明确的错误，而不是 panic 或返回部分数据。

**验证需求: 11.7**

### 示例测试用例

以下是一些重要的示例测试用例，用于验证特定场景：

#### 示例 1: 默认偏好设置

当用户首次访问偏好设置（数据库中不存在该用户的记录）时，get_preferences 应该返回默认配置，包含所有通知类型启用、优先级为 normal。

**验证需求: 6.3**

#### 示例 2: 资源不存在返回 404

当尝试标记一个不存在的 notification_id 为已读时，API 应该返回 HTTP 404 状态码。

**验证需求: 3.8**

#### 示例 3: 数据库 Schema 验证

数据库初始化后，应该存在 notifications 和 notification_preferences 表，且包含所有必需的字段和索引。

**验证需求: 4.1, 4.2, 4.3, 4.4, 4.5**

#### 示例 4: 测试通知功能访问控制

当环境变量 ENABLE_TEST_NOTIFICATIONS 为 false 时，调用 /api/notifications/test 端点应该返回 HTTP 403 状态码。

**验证需求: 9.4**

#### 示例 5: 测试通知标记

当环境变量 ENABLE_TEST_NOTIFICATIONS 为 true 时，生成的测试通知的 title 应该包含 "[TEST]" 前缀。

**验证需求: 9.3**

#### 示例 6: 查询限制

当请求的 limit 参数大于 100 时，API 应该最多返回 100 条通知。

**验证需求: 12.4**

#### 示例 7: 批量操作使用单个 SQL 语句

批量关闭通知操作应该使用单个 UPDATE 语句，而不是多个单独的 UPDATE 语句（可以通过 SQL 日志验证）。

**验证需求: 12.2**

## 错误处理

### 错误类型定义

系统定义以下错误类型，用于统一的错误处理：

```python
class NotificationError(Exception):
    """通知系统基础错误"""
    pass

class ValidationError(NotificationError):
    """输入验证错误"""
    pass

class NotFoundError(NotificationError):
    """资源不存在错误"""
    pass

class PermissionError(NotificationError):
    """权限错误"""
    pass

class DatabaseError(NotificationError):
    """数据库操作错误"""
    pass
```

### 错误处理策略

#### 1. Tauri 命令层错误处理

```rust
// 统一的错误响应格式
#[derive(Debug, Serialize)]
struct ErrorResponse {
    error_type: String,  // VALIDATION_ERROR, NOT_FOUND, NETWORK_ERROR, etc.
    message: String,
    details: Option<serde_json::Value>,
}

// 错误转换
impl From<reqwest::Error> for ErrorResponse {
    fn from(err: reqwest::Error) -> Self {
        ErrorResponse {
            error_type: "NETWORK_ERROR".to_string(),
            message: format!("Network request failed: {}", err),
            details: None,
        }
    }
}
```

#### 2. Python API 层错误处理

```python
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    logger.warning(f"Validation error: {e}")
    return jsonify({
        'error': str(e),
        'error_type': 'VALIDATION_ERROR'
    }), 400

@app.errorhandler(NotFoundError)
def handle_not_found(e):
    logger.info(f"Resource not found: {e}")
    return jsonify({
        'error': str(e),
        'error_type': 'NOT_FOUND'
    }), 404

@app.errorhandler(Exception)
def handle_generic_error(e):
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # 不暴露内部错误细节
    return jsonify({
        'error': 'Internal server error',
        'error_type': 'SERVER_ERROR'
    }), 500
```

#### 3. 数据库层错误处理

```python
async def safe_db_operation(operation, *args, **kwargs):
    """安全的数据库操作包装器"""
    try:
        return await operation(*args, **kwargs)
    except aiosqlite.IntegrityError as e:
        logger.error(f"Database integrity error: {e}")
        raise DatabaseError(f"Data integrity violation: {e}")
    except aiosqlite.OperationalError as e:
        logger.error(f"Database operational error: {e}")
        raise DatabaseError(f"Database operation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected database error: {e}", exc_info=True)
        raise DatabaseError(f"Database error: {e}")
```

### 日志记录策略

#### 日志级别

- **DEBUG**: 详细的调试信息（请求参数、SQL 查询）
- **INFO**: 正常操作信息（通知创建、用户操作）
- **WARNING**: 警告信息（验证失败、资源不存在）
- **ERROR**: 错误信息（数据库错误、网络错误）
- **CRITICAL**: 严重错误（系统崩溃、数据损坏）

#### 结构化日志格式

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log(self, level, message, **context):
        """记录结构化日志"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'context': context
        }
        
        if level == 'ERROR' or level == 'CRITICAL':
            # 错误日志包含堆栈跟踪
            import traceback
            log_entry['stack_trace'] = traceback.format_exc()
        
        self.logger.log(
            getattr(logging, level),
            json.dumps(log_entry, ensure_ascii=False)
        )
```

#### 日志配置

```python
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'DEBUG'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '.wayfare/logs/notifications.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'level': 'INFO'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '.wayfare/logs/errors.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json',
            'level': 'ERROR'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file', 'error_file']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## 测试策略

### 双重测试方法

本系统采用单元测试和基于属性的测试（Property-Based Testing, PBT）相结合的方法，确保全面的测试覆盖。

#### 单元测试

单元测试专注于：
- 特定示例和边界情况
- 组件集成点
- 错误条件和异常处理
- 数据库 schema 验证
- API 端点存在性

**示例单元测试**:

```python
# tests/test_notification_api.py
import pytest
from wayfare.notification_manager import NotificationManager
from wayfare.db import SQLiteDB

@pytest.fixture
async def notification_manager():
    db = SQLiteDB(':memory:')
    await db.initialize()
    return NotificationManager(db)

async def test_create_notification(notification_manager):
    """测试创建通知"""
    notification = await notification_manager.create_notification(
        user_id='user_123',
        notification_type='learning_progress',
        title='学习进度更新',
        message='您的进度已达到 75%',
        priority='normal'
    )
    
    assert notification['id'] is not None
    assert notification['user_id'] == 'user_123'
    assert notification['type'] == 'learning_progress'
    assert notification['is_read'] is False

async def test_get_notifications_filters_expired(notification_manager):
    """测试查询排除已过期通知"""
    from datetime import datetime, timezone, timedelta
    
    # 创建已过期通知
    expired_time = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
    await notification_manager.create_notification(
        user_id='user_123',
        notification_type='test',
        title='Expired',
        message='This is expired',
        expires_at=expired_time
    )
    
    # 创建未过期通知
    await notification_manager.create_notification(
        user_id='user_123',
        notification_type='test',
        title='Active',
        message='This is active'
    )
    
    # 查询通知
    batch = await notification_manager.get_notifications(user_id='user_123')
    
    # 应该只返回未过期的通知
    assert len(batch['notifications']) == 1
    assert batch['notifications'][0]['title'] == 'Active'

async def test_default_preferences(notification_manager):
    """测试默认偏好设置"""
    prefs = await notification_manager.get_preferences('new_user')
    
    assert prefs['user_id'] == 'new_user'
    assert 'learning_progress' in prefs['enabled_types']
    assert prefs['min_priority_level'] == 'normal'
    assert prefs['enable_in_app_notifications'] is True
```

#### 基于属性的测试

基于属性的测试使用 Hypothesis（Python）或 QuickCheck（Rust）库，通过生成大量随机输入来验证系统属性。

**配置要求**:
- 每个属性测试至少运行 100 次迭代
- 每个测试必须引用设计文档中的属性编号
- 使用标签格式: `Feature: frontend-backend-notification-integration, Property {number}: {property_text}`

**Python 示例（使用 Hypothesis）**:

```python
# tests/test_notification_properties.py
from hypothesis import given, strategies as st
import pytest

# 生成器：有效的通知对象
@st.composite
def notification_strategy(draw):
    return {
        'user_id': draw(st.text(min_size=1, max_size=50)),
        'type': draw(st.sampled_from([
            'learning_progress', 'task_completed', 'confusion_detected'
        ])),
        'title': draw(st.text(min_size=1, max_size=100)),
        'message': draw(st.text(min_size=1, max_size=500)),
        'priority': draw(st.sampled_from(['urgent', 'high', 'normal', 'low']))
    }

@given(notification=notification_strategy())
@pytest.mark.property_test
async def test_property_5_notification_crud_roundtrip(notification_manager, notification):
    """
    Feature: frontend-backend-notification-integration
    Property 5: 通知 CRUD Round-Trip
    
    对于任意有效的通知对象，创建、查询、更新、删除操作应该保持数据一致性。
    """
    # 1. 创建通知
    created = await notification_manager.create_notification(**notification)
    notification_id = created['id']
    
    # 2. 查询通知 - 应该能找到
    batch = await notification_manager.get_notifications(
        user_id=notification['user_id']
    )
    assert any(n['id'] == notification_id for n in batch['notifications'])
    
    # 3. 标记为已读
    updated = await notification_manager.mark_as_read(
        notification_id=notification_id,
        user_id=notification['user_id']
    )
    assert updated['is_read'] is True
    assert updated['read_at'] is not None
    
    # 4. 再次查询 - 应该反映已读状态
    batch = await notification_manager.get_notifications(
        user_id=notification['user_id']
    )
    found = next(n for n in batch['notifications'] if n['id'] == notification_id)
    assert found['is_read'] is True
    
    # 5. 关闭通知
    success = await notification_manager.dismiss_notification(
        notification_id=notification_id,
        user_id=notification['user_id']
    )
    assert success is True
    
    # 6. 查询未关闭通知 - 不应该包含已关闭的
    batch = await notification_manager.get_notifications(
        user_id=notification['user_id']
    )
    assert not any(n['id'] == notification_id for n in batch['notifications'])
```

**Rust 示例（使用 quickcheck）**:

```rust
// tests/notification_properties.rs
use quickcheck::{Arbitrary, Gen, QuickCheck};
use serde_json;

#[derive(Clone, Debug)]
struct TestNotification {
    user_id: String,
    notification_type: String,
    title: String,
    message: String,
    priority: String,
}

impl Arbitrary for TestNotification {
    fn arbitrary(g: &mut Gen) -> Self {
        let types = vec!["learning_progress", "task_completed", "confusion_detected"];
        let priorities = vec!["urgent", "high", "normal", "low"];
        
        TestNotification {
            user_id: format!("user_{}", u32::arbitrary(g)),
            notification_type: g.choose(&types).unwrap().to_string(),
            title: String::arbitrary(g),
            message: String::arbitrary(g),
            priority: g.choose(&priorities).unwrap().to_string(),
        }
    }
}

#[test]
fn test_property_13_serialization_roundtrip() {
    /// Feature: frontend-backend-notification-integration
    /// Property 13: 数据序列化 Round-Trip
    /// 
    /// 对于任意 Notification 对象，序列化后反序列化应该得到等价的对象。
    
    fn prop(notification: TestNotification) -> bool {
        // 序列化
        let json = serde_json::to_string(&notification).unwrap();
        
        // 反序列化
        let deserialized: TestNotification = serde_json::from_str(&json).unwrap();
        
        // 验证等价性
        notification.user_id == deserialized.user_id &&
        notification.notification_type == deserialized.notification_type &&
        notification.title == deserialized.title &&
        notification.message == deserialized.message &&
        notification.priority == deserialized.priority
    }
    
    QuickCheck::new()
        .tests(100)  // 至少 100 次迭代
        .quickcheck(prop as fn(TestNotification) -> bool);
}
```

### 集成测试

集成测试验证 Tauri 命令、HTTP 通信和 Python 后端的端到端流程。

```python
# tests/integration/test_notification_integration.py
import pytest
from unittest.mock import Mock, patch
import json

@pytest.mark.integration
async def test_fetch_notifications_integration():
    """测试完整的获取通知流程"""
    # 1. 准备测试数据
    test_user_id = 'test_user_123'
    
    # 2. 创建一些测试通知
    # ... (通过 NotificationManager 创建)
    
    # 3. 模拟 Tauri 命令调用
    # ... (调用 fetch_notifications 命令)
    
    # 4. 验证 HTTP 请求
    # ... (验证请求格式、端点、参数)
    
    # 5. 验证响应
    # ... (验证返回的 NotificationBatch 格式)
    
    pass

@pytest.mark.integration
async def test_notification_lifecycle():
    """测试通知的完整生命周期"""
    # 1. 触发事件（学习进度更新）
    # 2. 验证通知被创建
    # 3. 前端获取通知
    # 4. 用户标记为已读
    # 5. 用户关闭通知
    # 6. 验证通知状态变化
    pass
```

### 性能测试

性能测试验证系统在负载下的表现。

```python
# tests/performance/test_notification_performance.py
import pytest
import time
from wayfare.notification_manager import NotificationManager
from wayfare.db import SQLiteDB

@pytest.mark.performance
async def test_query_performance_with_10k_notifications():
    """
    验证需求 12.1: 查询通知列表应该在 100ms 内返回结果
    """
    db = SQLiteDB(':memory:')
    await db.initialize()
    manager = NotificationManager(db)
    
    # 创建 10000 条通知
    for i in range(10000):
        await manager.create_notification(
            user_id='user_123',
            notification_type='test',
            title=f'Notification {i}',
            message=f'Message {i}',
            priority='normal'
        )
    
    # 测量查询时间
    start = time.time()
    batch = await manager.get_notifications(
        user_id='user_123',
        limit=20,
        offset=0
    )
    elapsed = (time.time() - start) * 1000  # 转换为毫秒
    
    # 验证性能要求
    assert elapsed < 100, f"Query took {elapsed}ms, expected < 100ms"
    assert len(batch['notifications']) == 20
```

### 测试覆盖率目标

- 单元测试覆盖率: > 80%
- 属性测试覆盖: 所有 14 个正确性属性
- 集成测试覆盖: 所有 8 个 Tauri 命令
- 性能测试覆盖: 关键性能指标（查询、批量操作）

### 测试工具和库

**Python**:
- pytest: 测试框架
- pytest-asyncio: 异步测试支持
- hypothesis: 基于属性的测试
- pytest-cov: 代码覆盖率
- pytest-mock: Mock 支持

**Rust**:
- quickcheck: 基于属性的测试
- mockito: HTTP mock
- tokio-test: 异步测试支持

### 持续集成

测试应该在 CI/CD 流程中自动运行：

```yaml
# .github/workflows/test.yml
name: Test Notification System

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/ -v --cov=wayfare
      
      - name: Run property tests
        run: pytest tests/ -v -m property_test
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
      
      - name: Run performance tests
        run: pytest tests/performance/ -v
```

## 部署和配置

### 环境变量

系统使用以下环境变量进行配置：

```bash
# Python 后端配置
FLASK_ENV=development  # development 或 production
BACKEND_PORT=3001
DATABASE_PATH=.wayfare/wayfare.db

# 通知系统配置
ENABLE_TEST_NOTIFICATIONS=true  # 仅开发环境
NOTIFICATION_EXPIRY_HOURS=24
MAX_NOTIFICATIONS_PER_QUERY=100

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=.wayfare/logs

# Tauri 配置
BACKEND_URL=http://localhost:3001
```

### 数据库初始化

在首次运行时，系统需要初始化数据库表：

```python
# wayfare/init_notification_db.py
import asyncio
from wayfare.db import SQLiteDB

async def init_notification_tables():
    """初始化通知相关的数据库表"""
    db = SQLiteDB()
    
    async with aiosqlite.connect(db.db_path) as conn:
        # 创建 notifications 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'normal',
                icon TEXT,
                action_url TEXT,
                action_label TEXT,
                action_type TEXT,
                action_payload TEXT,
                metadata TEXT,
                created_at INTEGER NOT NULL,
                scheduled_at INTEGER,
                expires_at INTEGER,
                is_read BOOLEAN NOT NULL DEFAULT 0,
                read_at INTEGER,
                is_dismissed BOOLEAN NOT NULL DEFAULT 0,
                dismissed_at INTEGER
            )
        """)
        
        # 创建索引
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id 
            ON notifications(user_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at 
            ON notifications(created_at DESC)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_read_dismissed 
            ON notifications(is_read, is_dismissed)
        """)
        
        # 创建 notification_preferences 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id TEXT PRIMARY KEY,
                enabled_types TEXT NOT NULL,
                enable_browser_notifications BOOLEAN NOT NULL DEFAULT 1,
                enable_in_app_notifications BOOLEAN NOT NULL DEFAULT 1,
                enable_email_notifications BOOLEAN NOT NULL DEFAULT 0,
                min_priority_level TEXT NOT NULL DEFAULT 'normal',
                quiet_hours TEXT,
                max_notifications_per_hour INTEGER,
                updated_at INTEGER NOT NULL
            )
        """)
        
        await conn.commit()
        print("Notification tables initialized successfully")

if __name__ == '__main__':
    asyncio.run(init_notification_tables())
```

### Tauri 配置

在 `src-tauri/tauri.conf.json` 中注册命令：

```json
{
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      }
    }
  },
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  }
}
```

在 `src-tauri/src/main.rs` 中注册命令：

```rust
mod commands;

fn main() {
    let http_client = reqwest::Client::new();
    let backend_url = std::env::var("BACKEND_URL")
        .unwrap_or_else(|_| "http://localhost:3001".to_string());
    
    let app_state = commands::notifications::AppState {
        http_client,
        backend_url,
    };
    
    tauri::Builder::default()
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            commands::notifications::fetch_notifications,
            commands::notifications::mark_notification_as_read,
            commands::notifications::dismiss_notification,
            commands::notifications::batch_dismiss_notifications,
            commands::notifications::get_notification_preferences,
            commands::notifications::update_notification_preferences,
            commands::notifications::refresh_notification_stream,
            commands::notifications::send_test_notification,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### 启动流程

1. **启动 Python 后端**:
```bash
cd wayfare
python -m wayfare.notification_api
```

2. **启动 Tauri 应用**:
```bash
npm run tauri dev
```

3. **初始化数据库**（首次运行）:
```bash
python wayfare/init_notification_db.py
```

## 安全考虑

### 1. 输入验证

所有用户输入必须经过严格验证：
- user_id: 非空字符串，长度 1-50
- notification_id: UUID 格式
- types: 必须在预定义的类型列表中
- priority: 必须在 ['urgent', 'high', 'normal', 'low'] 中
- limit: 正整数，最大 100
- offset: 非负整数

### 2. 权限检查

所有操作必须验证用户权限：
- 用户只能访问自己的通知
- 用户只能修改自己的偏好设置
- 测试通知功能仅在开发环境可用

### 3. SQL 注入防护

- 使用参数化查询，永不拼接 SQL 字符串
- 使用 aiosqlite 的参数绑定机制
- 验证所有输入，拒绝包含 SQL 关键字的输入

### 4. 错误信息安全

- 生产环境不暴露内部错误细节
- 不在响应中包含堆栈跟踪
- 不暴露数据库结构信息
- 使用通用错误消息

### 5. 日志安全

- 不记录敏感信息（密码、token）
- 日志文件权限设置为 600
- 定期轮转日志文件
- 生产环境日志不包含调试信息

## 性能优化

### 1. 数据库优化

- 使用索引加速查询
- 批量操作使用单个 SQL 语句
- 定期清理过期数据
- 使用连接池复用连接

### 2. 缓存策略

```python
from functools import lru_cache
from datetime import datetime, timedelta

class NotificationCache:
    """通知缓存"""
    
    def __init__(self, ttl_seconds=60):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key):
        """获取缓存"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        """设置缓存"""
        self.cache[key] = (value, datetime.now())
    
    def invalidate(self, key):
        """失效缓存"""
        if key in self.cache:
            del self.cache[key]
```

### 3. 异步处理

- 使用 asyncio 处理 I/O 密集型操作
- 数据库操作使用 aiosqlite
- HTTP 请求使用 reqwest (Rust) 或 aiohttp (Python)

### 4. 批量操作优化

```python
async def batch_create_notifications(notifications: List[Dict[str, Any]]):
    """批量创建通知"""
    async with aiosqlite.connect(db_path) as db:
        await db.executemany("""
            INSERT INTO notifications
            (id, user_id, type, title, message, priority, created_at, expires_at, is_read, is_dismissed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                n['id'], n['user_id'], n['type'], n['title'], n['message'],
                n['priority'], n['created_at'], n['expires_at'], False, False
            )
            for n in notifications
        ])
        await db.commit()
```

## 监控和维护

### 1. 健康检查端点

```python
@app.route('/health', methods=['GET'])
async def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503
```

### 2. 指标收集

```python
class NotificationMetrics:
    """通知系统指标"""
    
    def __init__(self):
        self.total_created = 0
        self.total_read = 0
        self.total_dismissed = 0
        self.errors = 0
    
    def record_create(self):
        self.total_created += 1
    
    def record_read(self):
        self.total_read += 1
    
    def record_dismiss(self):
        self.total_dismissed += 1
    
    def record_error(self):
        self.errors += 1
    
    def get_stats(self):
        return {
            'total_created': self.total_created,
            'total_read': self.total_read,
            'total_dismissed': self.total_dismissed,
            'errors': self.errors
        }
```

### 3. 定期清理任务

```python
async def cleanup_expired_notifications():
    """清理已过期且已关闭的通知"""
    from datetime import datetime, timezone, timedelta
    
    # 删除 30 天前的已关闭通知
    cutoff_time = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
    
    async with aiosqlite.connect(db_path) as db:
        result = await db.execute("""
            DELETE FROM notifications
            WHERE is_dismissed = 1 AND dismissed_at < ?
        """, (cutoff_time,))
        
        deleted_count = result.rowcount
        await db.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired notifications")
        return deleted_count

# 定期执行清理任务
import asyncio

async def periodic_cleanup():
    """定期清理任务"""
    while True:
        try:
            await cleanup_expired_notifications()
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
        
        # 每天执行一次
        await asyncio.sleep(86400)
```

## 总结

本设计文档详细描述了前后端通知系统对接的技术实现方案，包括：

1. **架构设计**: 三层架构（前端 → Tauri → Python 后端），清晰的职责分离
2. **组件设计**: Tauri 命令处理器、Python API、通知管理器、数据库扩展
3. **数据模型**: 数据库表结构、索引设计、数据操作方法
4. **正确性属性**: 14 个可测试的属性，确保系统正确性
5. **错误处理**: 统一的错误类型、错误处理策略、结构化日志
6. **测试策略**: 单元测试 + 属性测试 + 集成测试 + 性能测试
7. **部署配置**: 环境变量、数据库初始化、启动流程
8. **安全考虑**: 输入验证、权限检查、SQL 注入防护
9. **性能优化**: 数据库优化、缓存策略、批量操作
10. **监控维护**: 健康检查、指标收集、定期清理

该设计复用了现有的 wayfare/ipc.py 和 wayfare/db.py 基础设施，确保与现有系统的兼容性和一致性。通过基于属性的测试，我们可以验证系统在各种输入下的正确性，确保高质量的实现。
