"""Behavior Analyzer模块

分析用户学习行为并触发主动干预（MVP简化版）。

主要功能：
1. 记录用户行为数据（页面浏览、文本选择、滚动等）
2. 存储行为数据到SQLite数据库
3. 检测触发条件（停留时间超过阈值）
4. 查询行为数据

Requirements: 6.1, 6.2
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4

from wayfare.db import SQLiteDB, BehaviorEvent


@dataclass
class BehaviorStatistics:
    """行为统计数据"""
    total_views: int
    total_selects: int
    total_scrolls: int
    avg_duration: float


class BehaviorAnalyzer:
    """用户行为分析器
    
    负责记录和分析用户学习行为，支持主动干预触发。
    MVP阶段实现基于停留时间的简单触发逻辑。
    """
    
    def __init__(self, db: SQLiteDB, intervention_threshold: int = 120):
        """初始化行为分析器
        
        Args:
            db: SQLite数据库实例
            intervention_threshold: 主动干预阈值（秒），默认120秒
        """
        self.db = db
        self.intervention_threshold = intervention_threshold
        
        # 跟踪当前页面的停留时间
        # key: "{doc_hash}_{page}", value: start_time
        self.page_start_times: Dict[str, datetime] = {}
    
    async def record_behavior(
        self,
        doc_hash: str,
        page: int,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BehaviorEvent:
        """记录用户行为
        
        Args:
            doc_hash: 文档hash
            page: 页码
            event_type: 事件类型 ('page_view', 'text_select', 'scroll')
            metadata: 可选的额外元数据
            
        Returns:
            创建的行为事件对象
            
        Raises:
            ValueError: 如果event_type不是有效值
        """
        # 验证事件类型
        valid_types = ['page_view', 'text_select', 'scroll']
        if event_type not in valid_types:
            raise ValueError(
                f"Invalid event_type: {event_type}. "
                f"Must be one of {valid_types}"
            )
        
        # 创建行为事件
        event = BehaviorEvent(
            id=str(uuid4()),
            doc_hash=doc_hash,
            page=page,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        )
        
        # 保存到数据库
        await self.db.save_behavior(event)
        
        # 如果是页面浏览事件，开始跟踪停留时间
        if event_type == "page_view":
            self._track_page_view(doc_hash, page)
        
        return event
    
    def _track_page_view(self, doc_hash: str, page: int):
        """跟踪页面浏览，记录开始时间
        
        Args:
            doc_hash: 文档hash
            page: 页码
        """
        key = f"{doc_hash}_{page}"
        self.page_start_times[key] = datetime.now(timezone.utc)
    
    async def check_intervention_trigger(
        self,
        doc_hash: str,
        page: int
    ) -> bool:
        """检查是否应该触发主动干预
        
        基于停留时间判断：如果用户在同一页面停留超过阈值，返回True。
        
        Args:
            doc_hash: 文档hash
            page: 页码
            
        Returns:
            是否应该触发干预
        """
        key = f"{doc_hash}_{page}"
        
        if key not in self.page_start_times:
            return False
        
        # 计算停留时间
        start_time = self.page_start_times[key]
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # 检查是否超过阈值
        if elapsed >= self.intervention_threshold:
            # 重置计时器，避免重复触发
            del self.page_start_times[key]
            return True
        
        return False
    
    async def get_behaviors(
        self,
        doc_hash: str,
        page: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> List[BehaviorEvent]:
        """查询行为数据
        
        Args:
            doc_hash: 文档hash
            page: 可选的页码过滤
            event_type: 可选的事件类型过滤
            
        Returns:
            行为事件列表，按时间倒序排列
        """
        # 从数据库获取行为数据
        behaviors = await self.db.get_behaviors(doc_hash, page)
        
        # 如果指定了事件类型，进行过滤
        if event_type:
            behaviors = [b for b in behaviors if b.event_type == event_type]
        
        return behaviors
    
    async def get_page_statistics(
        self,
        doc_hash: str,
        page: int
    ) -> BehaviorStatistics:
        """获取页面统计信息
        
        用于生成干预内容或分析学习行为。
        
        Args:
            doc_hash: 文档hash
            page: 页码
            
        Returns:
            页面统计数据
        """
        # 获取该页面的所有行为
        behaviors = await self.db.get_behaviors(doc_hash, page)
        
        # 统计各类事件
        total_views = sum(1 for b in behaviors if b.event_type == "page_view")
        total_selects = sum(1 for b in behaviors if b.event_type == "text_select")
        total_scrolls = sum(1 for b in behaviors if b.event_type == "scroll")
        
        # 计算平均停留时间
        view_events = [b for b in behaviors if b.event_type == "page_view"]
        avg_duration = 0.0
        
        if len(view_events) >= 2:
            # 按时间戳排序（升序）
            view_events_sorted = sorted(view_events, key=lambda b: b.timestamp)
            
            durations = []
            for i in range(len(view_events_sorted) - 1):
                start = datetime.fromisoformat(view_events_sorted[i].timestamp)
                end = datetime.fromisoformat(view_events_sorted[i + 1].timestamp)
                duration = (end - start).total_seconds()
                durations.append(duration)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
        
        return BehaviorStatistics(
            total_views=total_views,
            total_selects=total_selects,
            total_scrolls=total_scrolls,
            avg_duration=avg_duration
        )
    
    def reset_page_timer(self, doc_hash: str, page: int):
        """重置页面计时器
        
        用于手动重置停留时间跟踪，例如用户明确表示理解内容后。
        
        Args:
            doc_hash: 文档hash
            page: 页码
        """
        key = f"{doc_hash}_{page}"
        if key in self.page_start_times:
            del self.page_start_times[key]
    
    def get_current_dwell_time(self, doc_hash: str, page: int) -> float:
        """获取当前页面的停留时间
        
        Args:
            doc_hash: 文档hash
            page: 页码
            
        Returns:
            停留时间（秒），如果未跟踪则返回0
        """
        key = f"{doc_hash}_{page}"
        
        if key not in self.page_start_times:
            return 0.0
        
        start_time = self.page_start_times[key]
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        return elapsed
    
    async def send_intervention(
        self,
        doc_hash: str,
        page: int,
        ipc_handler=None
    ):
        """发送主动干预推送
        
        通过IPC Handler向前端发送主动干预消息，包含页面统计信息。
        这是一个松耦合设计：如果提供了ipc_handler，则发送推送；
        否则仅记录日志（用于测试或独立使用场景）。
        
        Requirements: 6.4 - THE Behavior_Analyzer SHALL 通过IPC向前端发送主动消息推送
        
        Args:
            doc_hash: 文档hash
            page: 页码
            ipc_handler: 可选的IPC Handler实例，用于发送通知
        """
        # 获取页面统计信息
        stats = await self.get_page_statistics(doc_hash, page)
        
        # 构建干预消息
        intervention_data = {
            "type": "intervention",
            "docHash": doc_hash,
            "page": page,
            "message": f"您在第{page}页停留了较长时间，需要帮助吗？",
            "statistics": {
                "totalViews": stats.total_views,
                "totalSelects": stats.total_selects,
                "totalScrolls": stats.total_scrolls,
                "avgDuration": stats.avg_duration
            }
        }
        
        # 如果提供了IPC Handler，发送通知
        if ipc_handler is not None:
            # 调用IPC Handler的_send_notification方法
            await ipc_handler._send_notification(intervention_data)
        else:
            # 未提供IPC Handler，仅记录日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"Intervention triggered for {doc_hash} page {page}, "
                f"but no IPC handler provided. Statistics: {stats}"
            )


