"""
通知管理器 - 负责通知的 CRUD 操作

提供通知的创建、查询、更新、删除等核心功能，
以及通知偏好设置的管理。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import sys
from pathlib import Path

# 直接导入，避免触发 wayfare/__init__.py
sys.path.insert(0, str(Path(__file__).parent))

# 导入 logging，但避免通过 wayfare 包
try:
    from logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class NotificationManager:
    """通知管理器，负责通知的 CRUD 操作"""
    
    def __init__(self, db):
        """
        初始化通知管理器
        
        Args:
            db: SQLiteDB 实例
        """
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
        """
        创建新通知
        
        Args:
            user_id: 用户 ID
            notification_type: 通知类型
            title: 标题
            message: 消息内容
            priority: 优先级（urgent, high, normal, low）
            **kwargs: 其他可选字段
        
        Returns:
            创建的通知对象
        """
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
        logger.info(f"Created notification {notification_id} for user {user_id}")
        return notification

    async def get_notifications(
        self,
        user_id: str,
        project_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        types: Optional[List[str]] = None,
        unread_only: bool = False,
        sort_by: str = 'recent'
    ) -> Dict[str, Any]:
        """
        获取通知列表
        
        Args:
            user_id: 用户 ID
            project_id: 项目 ID（可选）
            limit: 返回数量限制（最大 100）
            offset: 偏移量
            types: 通知类型过滤
            unread_only: 只返回未读通知
            sort_by: 排序方式（recent 或 priority）
        
        Returns:
            NotificationBatch 对象
        """
        # 限制最大返回数量
        limit = min(limit, 100)
        
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
        
        logger.debug(f"Fetched {len(notifications)} notifications for user {user_id}")
        
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
        """
        标记通知为已读
        
        Args:
            notification_id: 通知 ID
            user_id: 用户 ID
        
        Returns:
            更新后的通知对象，如果不存在或权限不足则返回 None
        """
        notification = await self.db.get_notification(notification_id)
        
        if not notification or notification['user_id'] != user_id:
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
            return None
        
        now = int(datetime.now(timezone.utc).timestamp())
        await self.db.update_notification(notification_id, {
            'is_read': True,
            'read_at': now
        })
        
        notification['is_read'] = True
        notification['read_at'] = now
        logger.info(f"Marked notification {notification_id} as read")
        return notification
    
    async def dismiss_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """
        关闭通知
        
        Args:
            notification_id: 通知 ID
            user_id: 用户 ID
        
        Returns:
            成功返回 True，失败返回 False
        """
        notification = await self.db.get_notification(notification_id)
        
        if not notification or notification['user_id'] != user_id:
            logger.warning(f"Notification {notification_id} not found or access denied for user {user_id}")
            return False
        
        now = int(datetime.now(timezone.utc).timestamp())
        await self.db.update_notification(notification_id, {
            'is_dismissed': True,
            'dismissed_at': now
        })
        
        logger.info(f"Dismissed notification {notification_id}")
        return True

    async def batch_dismiss(
        self,
        notification_ids: List[str],
        user_id: str
    ):
        """
        批量关闭通知
        
        Args:
            notification_ids: 通知 ID 列表
            user_id: 用户 ID
        """
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
        
        logger.info(f"Batch dismissed {len(notification_ids)} notifications for user {user_id}")
    
    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户偏好设置
        
        Args:
            user_id: 用户 ID
        
        Returns:
            NotificationPreferences 对象
        """
        prefs = await self.db.get_notification_preferences(user_id)
        
        if not prefs:
            # 返回默认偏好
            logger.info(f"Returning default preferences for user {user_id}")
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
        """
        更新用户偏好设置
        
        Args:
            prefs: NotificationPreferences 对象
        
        Raises:
            ValueError: 如果输入验证失败
        """
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
        logger.info(f"Updated preferences for user {prefs['user_id']}")
    
    async def create_test_notification(
        self,
        user_id: str,
        notification_type: str = 'learning_progress'
    ) -> Dict[str, Any]:
        """
        创建测试通知（仅开发环境）
        
        Args:
            user_id: 用户 ID
            notification_type: 通知类型
        
        Returns:
            创建的测试通知对象
        """
        test_notifications = {
            'learning_progress': {
                'title': '[TEST] 学习进度更新',
                'message': '您在认知心理学的进度已达到 75%',
                'priority': 'normal',
                'metadata': {
                    'documentId': 'test_doc_123',
                    'currentProgress': 75,
                    'targetProgress': 100
                }
            },
            'task_completed': {
                'title': '[TEST] 任务完成',
                'message': '您已完成今日的学习任务',
                'priority': 'high',
                'metadata': {
                    'taskId': 'test_task_456',
                    'taskName': '每日复习'
                }
            },
            'confusion_detected': {
                'title': '[TEST] 需要帮助？',
                'message': '您在导数定义这里停留了很久',
                'priority': 'high',
                'metadata': {
                    'documentId': 'test_doc_123',
                    'topic': '导数定义'
                }
            }
        }
        
        template = test_notifications.get(notification_type, test_notifications['learning_progress'])
        
        return await self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            **template
        )
