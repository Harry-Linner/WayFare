"""BehaviorAnalyzer单元测试

测试行为分析器的核心功能：
1. 记录行为数据
2. 查询行为数据
3. 检测主动干预触发
4. 统计页面行为
"""

import pytest
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os

from wayfare.behavior_analyzer import BehaviorAnalyzer, BehaviorStatistics
from wayfare.db import SQLiteDB, BehaviorEvent


@pytest.fixture
async def db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = SQLiteDB(db_path)
        await db.initialize()
        yield db


@pytest.fixture
def analyzer(db):
    """创建BehaviorAnalyzer实例"""
    return BehaviorAnalyzer(db, intervention_threshold=5)  # 5秒阈值用于测试


class TestRecordBehavior:
    """测试record_behavior方法"""
    
    @pytest.mark.asyncio
    async def test_record_page_view(self, analyzer):
        """测试记录页面浏览事件"""
        event = await analyzer.record_behavior(
            doc_hash="test_doc",
            page=1,
            event_type="page_view"
        )
        
        assert event.doc_hash == "test_doc"
        assert event.page == 1
        assert event.event_type == "page_view"
        assert event.id is not None
        assert event.timestamp is not None
        assert event.metadata == {}
    
    @pytest.mark.asyncio
    async def test_record_text_select(self, analyzer):
        """测试记录文本选择事件"""
        metadata = {"selected_text": "测试文本"}
        event = await analyzer.record_behavior(
            doc_hash="test_doc",
            page=2,
            event_type="text_select",
            metadata=metadata
        )
        
        assert event.event_type == "text_select"
        assert event.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_record_scroll(self, analyzer):
        """测试记录滚动事件"""
        metadata = {"scroll_position": 0.5}
        event = await analyzer.record_behavior(
            doc_hash="test_doc",
            page=3,
            event_type="scroll",
            metadata=metadata
        )
        
        assert event.event_type == "scroll"
        assert event.metadata["scroll_position"] == 0.5
    
    @pytest.mark.asyncio
    async def test_invalid_event_type(self, analyzer):
        """测试无效的事件类型"""
        with pytest.raises(ValueError, match="Invalid event_type"):
            await analyzer.record_behavior(
                doc_hash="test_doc",
                page=1,
                event_type="invalid_type"
            )
    
    @pytest.mark.asyncio
    async def test_page_view_starts_tracking(self, analyzer):
        """测试页面浏览事件开始跟踪停留时间"""
        await analyzer.record_behavior(
            doc_hash="test_doc",
            page=1,
            event_type="page_view"
        )
        
        # 验证开始跟踪
        key = "test_doc_1"
        assert key in analyzer.page_start_times
        assert isinstance(analyzer.page_start_times[key], datetime)


class TestGetBehaviors:
    """测试get_behaviors查询方法"""
    
    @pytest.mark.asyncio
    async def test_get_all_behaviors(self, analyzer):
        """测试获取文档的所有行为"""
        # 记录多个行为
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 2, "page_view")
        
        behaviors = await analyzer.get_behaviors("doc1")
        
        assert len(behaviors) == 3
        assert all(b.doc_hash == "doc1" for b in behaviors)
    
    @pytest.mark.asyncio
    async def test_get_behaviors_by_page(self, analyzer):
        """测试按页码过滤行为"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 2, "page_view")
        
        behaviors = await analyzer.get_behaviors("doc1", page=1)
        
        assert len(behaviors) == 2
        assert all(b.page == 1 for b in behaviors)
    
    @pytest.mark.asyncio
    async def test_get_behaviors_by_event_type(self, analyzer):
        """测试按事件类型过滤行为"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 1, "scroll")
        
        behaviors = await analyzer.get_behaviors("doc1", event_type="text_select")
        
        assert len(behaviors) == 1
        assert behaviors[0].event_type == "text_select"
    
    @pytest.mark.asyncio
    async def test_get_behaviors_combined_filters(self, analyzer):
        """测试组合过滤条件"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 2, "text_select")
        
        behaviors = await analyzer.get_behaviors(
            "doc1",
            page=1,
            event_type="text_select"
        )
        
        assert len(behaviors) == 1
        assert behaviors[0].page == 1
        assert behaviors[0].event_type == "text_select"
    
    @pytest.mark.asyncio
    async def test_get_behaviors_empty_result(self, analyzer):
        """测试查询不存在的行为"""
        behaviors = await analyzer.get_behaviors("nonexistent_doc")
        
        assert len(behaviors) == 0


class TestInterventionTrigger:
    """测试主动干预触发逻辑"""
    
    @pytest.mark.asyncio
    async def test_trigger_after_threshold(self, analyzer):
        """测试超过阈值后触发干预"""
        # 记录页面浏览
        await analyzer.record_behavior("doc1", 1, "page_view")
        
        # 等待超过阈值（5秒）
        await asyncio.sleep(6)
        
        # 检查是否触发
        should_trigger = await analyzer.check_intervention_trigger("doc1", 1)
        
        assert should_trigger is True
    
    @pytest.mark.asyncio
    async def test_no_trigger_before_threshold(self, analyzer):
        """测试未超过阈值时不触发"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        
        # 等待少于阈值
        await asyncio.sleep(2)
        
        should_trigger = await analyzer.check_intervention_trigger("doc1", 1)
        
        assert should_trigger is False
    
    @pytest.mark.asyncio
    async def test_no_trigger_without_page_view(self, analyzer):
        """测试未记录页面浏览时不触发"""
        should_trigger = await analyzer.check_intervention_trigger("doc1", 1)
        
        assert should_trigger is False
    
    @pytest.mark.asyncio
    async def test_trigger_resets_timer(self, analyzer):
        """测试触发后重置计时器"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        await asyncio.sleep(6)
        
        # 第一次触发
        should_trigger = await analyzer.check_intervention_trigger("doc1", 1)
        assert should_trigger is True
        
        # 第二次检查不应触发（计时器已重置）
        should_trigger = await analyzer.check_intervention_trigger("doc1", 1)
        assert should_trigger is False
    
    @pytest.mark.asyncio
    async def test_different_pages_tracked_separately(self, analyzer):
        """测试不同页面独立跟踪"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 2, "page_view")
        
        await asyncio.sleep(6)
        
        # 两个页面都应该触发
        assert await analyzer.check_intervention_trigger("doc1", 1) is True
        assert await analyzer.check_intervention_trigger("doc1", 2) is True


class TestPageStatistics:
    """测试页面统计功能"""
    
    @pytest.mark.asyncio
    async def test_basic_statistics(self, analyzer):
        """测试基本统计信息"""
        # 记录多种行为
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 1, "scroll")
        
        stats = await analyzer.get_page_statistics("doc1", 1)
        
        assert stats.total_views == 1
        assert stats.total_selects == 2
        assert stats.total_scrolls == 1
    
    @pytest.mark.asyncio
    async def test_average_duration_calculation(self, analyzer):
        """测试平均停留时间计算"""
        # 记录两次页面浏览
        await analyzer.record_behavior("doc1", 1, "page_view")
        await asyncio.sleep(2)
        await analyzer.record_behavior("doc1", 1, "page_view")
        
        stats = await analyzer.get_page_statistics("doc1", 1)
        
        # 平均停留时间应该约为2秒
        assert stats.avg_duration >= 1.5
        assert stats.avg_duration <= 2.5
    
    @pytest.mark.asyncio
    async def test_statistics_empty_page(self, analyzer):
        """测试空页面的统计"""
        stats = await analyzer.get_page_statistics("doc1", 1)
        
        assert stats.total_views == 0
        assert stats.total_selects == 0
        assert stats.total_scrolls == 0
        assert stats.avg_duration == 0.0


class TestUtilityMethods:
    """测试辅助方法"""
    
    @pytest.mark.asyncio
    async def test_reset_page_timer(self, analyzer):
        """测试重置页面计时器"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        
        # 验证计时器存在
        assert "doc1_1" in analyzer.page_start_times
        
        # 重置计时器
        analyzer.reset_page_timer("doc1", 1)
        
        # 验证计时器已删除
        assert "doc1_1" not in analyzer.page_start_times
    
    @pytest.mark.asyncio
    async def test_get_current_dwell_time(self, analyzer):
        """测试获取当前停留时间"""
        await analyzer.record_behavior("doc1", 1, "page_view")
        
        await asyncio.sleep(2)
        
        dwell_time = analyzer.get_current_dwell_time("doc1", 1)
        
        # 停留时间应该约为2秒
        assert dwell_time >= 1.5
        assert dwell_time <= 2.5
    
    @pytest.mark.asyncio
    async def test_get_dwell_time_not_tracked(self, analyzer):
        """测试获取未跟踪页面的停留时间"""
        dwell_time = analyzer.get_current_dwell_time("doc1", 1)
        
        assert dwell_time == 0.0


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, analyzer):
        """测试完整的行为分析工作流"""
        # 1. 用户打开页面
        await analyzer.record_behavior("doc1", 1, "page_view")
        
        # 2. 用户选择文本
        await analyzer.record_behavior(
            "doc1", 1, "text_select",
            metadata={"selected_text": "重要概念"}
        )
        
        # 3. 用户滚动页面
        await analyzer.record_behavior(
            "doc1", 1, "scroll",
            metadata={"scroll_position": 0.3}
        )
        
        # 4. 查询行为
        behaviors = await analyzer.get_behaviors("doc1", page=1)
        assert len(behaviors) == 3
        
        # 5. 获取统计
        stats = await analyzer.get_page_statistics("doc1", 1)
        assert stats.total_views == 1
        assert stats.total_selects == 1
        assert stats.total_scrolls == 1
        
        # 6. 等待触发干预
        await asyncio.sleep(6)
        should_trigger = await analyzer.check_intervention_trigger("doc1", 1)
        assert should_trigger is True
    
    @pytest.mark.asyncio
    async def test_multiple_documents(self, analyzer):
        """测试多文档场景"""
        # 记录不同文档的行为
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc2", 1, "page_view")
        await analyzer.record_behavior("doc1", 2, "page_view")
        
        # 查询各文档的行为
        doc1_behaviors = await analyzer.get_behaviors("doc1")
        doc2_behaviors = await analyzer.get_behaviors("doc2")
        
        assert len(doc1_behaviors) == 2
        assert len(doc2_behaviors) == 1
        
        # 验证独立跟踪
        await asyncio.sleep(6)
        assert await analyzer.check_intervention_trigger("doc1", 1) is True
        assert await analyzer.check_intervention_trigger("doc2", 1) is True
        assert await analyzer.check_intervention_trigger("doc1", 2) is True


class TestEdgeCases:
    """边界情况测试"""
    
    @pytest.mark.asyncio
    async def test_empty_metadata(self, analyzer):
        """测试空元数据"""
        event = await analyzer.record_behavior(
            "doc1", 1, "page_view",
            metadata=None
        )
        
        assert event.metadata == {}
    
    @pytest.mark.asyncio
    async def test_large_metadata(self, analyzer):
        """测试大量元数据"""
        large_metadata = {
            "selected_text": "很长的文本" * 100,
            "context": {"key": "value" * 50}
        }
        
        event = await analyzer.record_behavior(
            "doc1", 1, "text_select",
            metadata=large_metadata
        )
        
        assert event.metadata == large_metadata
    
    @pytest.mark.asyncio
    async def test_concurrent_page_views(self, analyzer):
        """测试并发页面浏览"""
        # 同时记录多个页面浏览
        tasks = [
            analyzer.record_behavior(f"doc{i}", 1, "page_view")
            for i in range(10)
        ]
        
        events = await asyncio.gather(*tasks)
        
        assert len(events) == 10
        assert all(e.event_type == "page_view" for e in events)


class TestSendIntervention:
    """测试send_intervention方法"""
    
    @pytest.mark.asyncio
    async def test_send_intervention_without_ipc_handler(self, analyzer):
        """测试不提供IPC Handler时的干预发送"""
        # 记录一些行为
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        
        # 不提供IPC Handler，应该只记录日志，不抛出异常
        await analyzer.send_intervention("doc1", 1, ipc_handler=None)
    
    @pytest.mark.asyncio
    async def test_send_intervention_with_mock_ipc_handler(self, analyzer):
        """测试提供IPC Handler时的干预发送"""
        # 记录一些行为
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 1, "scroll")
        
        # 创建模拟的IPC Handler
        class MockIPCHandler:
            def __init__(self):
                self.notifications = []
            
            async def _send_notification(self, data):
                self.notifications.append(data)
        
        mock_handler = MockIPCHandler()
        
        # 发送干预
        await analyzer.send_intervention("doc1", 1, ipc_handler=mock_handler)
        
        # 验证通知被发送
        assert len(mock_handler.notifications) == 1
        
        notification = mock_handler.notifications[0]
        assert notification["type"] == "intervention"
        assert notification["docHash"] == "doc1"
        assert notification["page"] == 1
        assert "message" in notification
        assert "statistics" in notification
    
    @pytest.mark.asyncio
    async def test_intervention_includes_statistics(self, analyzer):
        """测试干预消息包含统计信息"""
        # 记录多种行为
        await analyzer.record_behavior("doc1", 1, "page_view")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 1, "text_select")
        await analyzer.record_behavior("doc1", 1, "scroll")
        
        # 创建模拟的IPC Handler
        class MockIPCHandler:
            def __init__(self):
                self.notifications = []
            
            async def _send_notification(self, data):
                self.notifications.append(data)
        
        mock_handler = MockIPCHandler()
        
        # 发送干预
        await analyzer.send_intervention("doc1", 1, ipc_handler=mock_handler)
        
        # 验证统计信息
        notification = mock_handler.notifications[0]
        stats = notification["statistics"]
        
        assert stats["totalViews"] == 1
        assert stats["totalSelects"] == 2
        assert stats["totalScrolls"] == 1
        assert "avgDuration" in stats
    
    @pytest.mark.asyncio
    async def test_intervention_for_empty_page(self, analyzer):
        """测试空页面的干预发送"""
        # 创建模拟的IPC Handler
        class MockIPCHandler:
            def __init__(self):
                self.notifications = []
            
            async def _send_notification(self, data):
                self.notifications.append(data)
        
        mock_handler = MockIPCHandler()
        
        # 发送干预（页面没有任何行为记录）
        await analyzer.send_intervention("doc1", 1, ipc_handler=mock_handler)
        
        # 验证通知被发送，统计信息为0
        assert len(mock_handler.notifications) == 1
        
        notification = mock_handler.notifications[0]
        stats = notification["statistics"]
        
        assert stats["totalViews"] == 0
        assert stats["totalSelects"] == 0
        assert stats["totalScrolls"] == 0
        assert stats["avgDuration"] == 0.0
