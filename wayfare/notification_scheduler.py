"""
通知调度器 - 监听事件并生成通知

监听学习进度、任务完成、卡顿检测等事件，
根据用户偏好设置生成和调度通知。
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone, time as dt_time
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


class NotificationScheduler:
    """通知调度器，负责监听事件并生成通知"""
    
    def __init__(self, notification_manager):
        """
        初始化通知调度器
        
        Args:
            notification_manager: NotificationManager 实例
        """
        self.manager = notification_manager
        self.priority_levels = ['urgent', 'high', 'normal', 'low']
    
    async def on_learning_progress(
        self,
        user_id: str,
        document_id: str,
        progress: float,
        **kwargs
    ):
        """
        处理学习进度事件
        
        Args:
            user_id: 用户 ID
            document_id: 文档 ID
            progress: 进度百分比（0-100）
            **kwargs: 其他元数据
        """
        # 检查用户偏好
        if not await self._should_send_notification(
            user_id=user_id,
            notification_type='learning_progress',
            priority='normal'
        ):
            logger.debug(f"Skipping learning_progress notification for user {user_id} (filtered by preferences)")
            return
        
        # 生成通知
        await self.manager.create_notification(
            user_id=user_id,
            notification_type='learning_progress',
            title='学习进度更新',
            message=f'您的学习进度已达到 {progress:.0f}%',
            priority='normal',
            metadata={
                'documentId': document_id,
                'currentProgress': progress,
                **kwargs
            }
        )
        logger.info(f"Created learning_progress notification for user {user_id}")
    
    async def on_task_completed(
        self,
        user_id: str,
        task_id: str,
        task_name: str,
        **kwargs
    ):
        """
        处理任务完成事件
        
        Args:
            user_id: 用户 ID
            task_id: 任务 ID
            task_name: 任务名称
            **kwargs: 其他元数据
        """
        if not await self._should_send_notification(
            user_id=user_id,
            notification_type='task_completed',
            priority='high'
        ):
            logger.debug(f"Skipping task_completed notification for user {user_id}")
            return
        
        await self.manager.create_notification(
            user_id=user_id,
            notification_type='task_completed',
            title='任务完成',
            message=f'您已完成任务：{task_name}',
            priority='high',
            metadata={
                'taskId': task_id,
                'taskName': task_name,
                **kwargs
            }
        )
        logger.info(f"Created task_completed notification for user {user_id}")
    
    async def on_confusion_detected(
        self,
        user_id: str,
        document_id: str,
        topic: str,
        duration: int,
        **kwargs
    ):
        """
        处理卡顿检测事件
        
        Args:
            user_id: 用户 ID
            document_id: 文档 ID
            topic: 主题
            duration: 停留时长（秒）
            **kwargs: 其他元数据
        """
        if not await self._should_send_notification(
            user_id=user_id,
            notification_type='confusion_detected',
            priority='high'
        ):
            logger.debug(f"Skipping confusion_detected notification for user {user_id}")
            return
        
        await self.manager.create_notification(
            user_id=user_id,
            notification_type='confusion_detected',
            title='需要帮助？',
            message=f'您在"{topic}"这里停留了 {duration} 秒',
            priority='high',
            action_url=f'/document/{document_id}',
            action_label='查看解释',
            metadata={
                'documentId': document_id,
                'topic': topic,
                'duration': duration,
                **kwargs
            }
        )
        logger.info(f"Created confusion_detected notification for user {user_id}")
    
    async def _should_send_notification(
        self,
        user_id: str,
        notification_type: str,
        priority: str
    ) -> bool:
        """
        检查是否应该发送通知（根据用户偏好）
        
        Args:
            user_id: 用户 ID
            notification_type: 通知类型
            priority: 优先级
        
        Returns:
            True 如果应该发送，False 如果应该过滤
        """
        # 获取用户偏好
        prefs = await self.manager.get_preferences(user_id)
        
        # 检查通知类型是否启用
        if notification_type not in prefs['enabled_types']:
            return False
        
        # 检查优先级是否满足最低要求
        min_priority = prefs['min_priority_level']
        if not self._meets_priority_threshold(priority, min_priority):
            return False
        
        # 检查静默时段（紧急通知除外）
        if priority != 'urgent' and not await self._is_outside_quiet_hours(prefs):
            logger.debug(f"Notification delayed due to quiet hours")
            # TODO: 实现延迟队列
            return False
        
        return True
    
    def _meets_priority_threshold(self, priority: str, min_priority: str) -> bool:
        """
        检查优先级是否满足最低要求
        
        Args:
            priority: 通知优先级
            min_priority: 最低优先级要求
        
        Returns:
            True 如果满足，False 如果不满足
        """
        try:
            priority_index = self.priority_levels.index(priority)
            min_index = self.priority_levels.index(min_priority)
            return priority_index <= min_index
        except ValueError:
            return True  # 未知优先级默认允许
    
    async def _is_outside_quiet_hours(self, prefs: Dict[str, Any]) -> bool:
        """
        检查当前是否在静默时段之外
        
        Args:
            prefs: 用户偏好设置
        
        Returns:
            True 如果在静默时段之外，False 如果在静默时段内
        """
        quiet_hours = prefs.get('quiet_hours')
        if not quiet_hours or not quiet_hours.get('enabled'):
            return True
        
        now = datetime.now(timezone.utc).time()
        from_time = dt_time.fromisoformat(quiet_hours['from'])
        to_time = dt_time.fromisoformat(quiet_hours['to'])
        
        # 处理跨午夜的情况
        if from_time <= to_time:
            # 正常情况：22:00 - 08:00
            return not (from_time <= now <= to_time)
        else:
            # 跨午夜：08:00 - 22:00 (静默时段在白天)
            return from_time <= now <= to_time


# 使用示例
async def example_usage():
    """使用示例"""
    from db import SQLiteDB
    from notification_manager import NotificationManager
    
    db = SQLiteDB(db_path='.wayfare/wayfare.db')
    await db.initialize()
    
    manager = NotificationManager(db)
    scheduler = NotificationScheduler(manager)
    
    # 监听学习进度事件
    await scheduler.on_learning_progress(
        user_id='user123',
        document_id='doc456',
        progress=75.0
    )
    
    # 监听任务完成事件
    await scheduler.on_task_completed(
        user_id='user123',
        task_id='task789',
        task_name='每日复习'
    )
    
    # 监听卡顿检测事件
    await scheduler.on_confusion_detected(
        user_id='user123',
        document_id='doc456',
        topic='导数定义',
        duration=120
    )
