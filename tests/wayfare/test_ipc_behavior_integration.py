"""
IPC Behavior Integration Tests

测试IPC Handler与BehaviorAnalyzer的集成，验证完整的行为分析工作流。
"""

import pytest
import json
import asyncio
import tempfile
from pathlib import Path

from wayfare.ipc import IPCHandler
from wayfare.behavior_analyzer import BehaviorAnalyzer
from wayfare.db import SQLiteDB


class TestIPCBehaviorIntegration:
    """测试IPC Handler与BehaviorAnalyzer的集成"""
    
    @pytest.fixture
    async def db(self):
        """创建临时数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SQLiteDB(str(db_path))
            await db.initialize()
            yield db
    
    @pytest.fixture
    def behavior_analyzer(self, db):
        """创建BehaviorAnalyzer实例"""
        return BehaviorAnalyzer(db=db, intervention_threshold=5)  # 5秒阈值用于测试
    
    @pytest.fixture
    def handler(self, behavior_analyzer):
        """创建IPCHandler实例"""
        handler = IPCHandler(behavior_analyzer=behavior_analyzer)
        yield handler
        # 清理：停止干预检查任务
        handler.stop_intervention_check()
    
    @pytest.mark.asyncio
    async def test_record_behavior_via_ipc(self, handler, db):
        """测试通过IPC记录行为数据"""
        # 发送behavior请求
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "eventType": "page_view",
                "metadata": {"source": "test"}
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        # 验证响应
        assert response["success"] is True
        assert response["data"]["recorded"] is True
        assert "eventId" in response["data"]
        
        # 验证数据库中的记录
        behaviors = await db.get_behaviors("test_doc_hash", page=1)
        assert len(behaviors) == 1
        assert behaviors[0].event_type == "page_view"
        assert behaviors[0].metadata["source"] == "test"
    
    @pytest.mark.asyncio
    async def test_multiple_behavior_events(self, handler, db):
        """测试记录多个行为事件"""
        doc_hash = "test_doc_hash"
        page = 1
        
        # 发送多个不同类型的事件
        event_types = ["page_view", "text_select", "scroll"]
        
        for i, event_type in enumerate(event_types):
            raw_message = json.dumps({
                "id": f"test-id-{i}",
                "seq": i,
                "method": "behavior",
                "params": {
                    "docHash": doc_hash,
                    "page": page,
                    "eventType": event_type,
                    "metadata": {"index": i}
                }
            })
            
            response_str = await handler.handle_request(raw_message)
            response = json.loads(response_str)
            assert response["success"] is True
        
        # 验证所有事件都被记录
        behaviors = await db.get_behaviors(doc_hash, page=page)
        assert len(behaviors) == 3
        
        # 验证事件类型
        recorded_types = {b.event_type for b in behaviors}
        assert recorded_types == set(event_types)
    
    @pytest.mark.asyncio
    async def test_page_view_tracking(self, handler):
        """测试page_view事件启动页面跟踪"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "eventType": "page_view"
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is True
        
        # 验证活跃页面被跟踪
        key = "test_doc_hash_1"
        assert key in handler._active_pages
        assert handler._active_pages[key]["docHash"] == "test_doc_hash"
        assert handler._active_pages[key]["page"] == 1
        
        # 验证干预检查任务已启动
        assert handler._intervention_task is not None
        assert not handler._intervention_task.done()
    
    @pytest.mark.asyncio
    async def test_intervention_trigger(self, handler, behavior_analyzer, capsys):
        """测试干预触发机制"""
        # 设置较短的检查间隔用于测试
        handler._intervention_check_interval = 1  # 1秒检查一次
        
        # 发送page_view事件
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "eventType": "page_view"
            }
        })
        
        await handler.handle_request(raw_message)
        
        # 等待超过干预阈值（5秒）+ 检查间隔（1秒）
        await asyncio.sleep(6.5)
        
        # 检查是否发送了干预通知
        captured = capsys.readouterr()
        
        # 验证stdout中包含干预通知
        assert "intervention" in captured.out.lower()
        
        # 验证活跃页面被移除（已触发干预）
        key = "test_doc_hash_1"
        assert key not in handler._active_pages
    
    @pytest.mark.asyncio
    async def test_multiple_pages_tracking(self, handler):
        """测试跟踪多个页面"""
        doc_hash = "test_doc_hash"
        
        # 发送多个页面的page_view事件
        for page in [1, 2, 3]:
            raw_message = json.dumps({
                "id": f"test-id-{page}",
                "seq": page - 1,
                "method": "behavior",
                "params": {
                    "docHash": doc_hash,
                    "page": page,
                    "eventType": "page_view"
                }
            })
            
            await handler.handle_request(raw_message)
        
        # 验证所有页面都被跟踪
        assert len(handler._active_pages) == 3
        for page in [1, 2, 3]:
            key = f"{doc_hash}_{page}"
            assert key in handler._active_pages
    
    @pytest.mark.asyncio
    async def test_non_page_view_does_not_track(self, handler):
        """测试非page_view事件不启动跟踪"""
        # 发送text_select事件
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "eventType": "text_select"
            }
        })
        
        await handler.handle_request(raw_message)
        
        # 验证活跃页面未被跟踪
        assert len(handler._active_pages) == 0
        
        # 验证干预检查任务未启动（或已完成）
        assert handler._intervention_task is None or handler._intervention_task.done()
    
    @pytest.mark.asyncio
    async def test_behavior_statistics(self, handler, behavior_analyzer, db):
        """测试行为统计功能"""
        doc_hash = "test_doc_hash"
        page = 1
        
        # 记录多个行为事件
        events = [
            ("page_view", {}),
            ("text_select", {"text": "selected text 1"}),
            ("text_select", {"text": "selected text 2"}),
            ("scroll", {"position": 0.5}),
        ]
        
        for i, (event_type, metadata) in enumerate(events):
            raw_message = json.dumps({
                "id": f"test-id-{i}",
                "seq": i,
                "method": "behavior",
                "params": {
                    "docHash": doc_hash,
                    "page": page,
                    "eventType": event_type,
                    "metadata": metadata
                }
            })
            
            await handler.handle_request(raw_message)
        
        # 获取统计信息
        stats = await behavior_analyzer.get_page_statistics(doc_hash, page)
        
        # 验证统计数据
        assert stats.total_views == 1
        assert stats.total_selects == 2
        assert stats.total_scrolls == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_event_type(self, handler):
        """测试无效事件类型的错误处理"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "eventType": "invalid_type"
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "eventtype" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_params(self, handler):
        """测试缺少必需参数的错误处理"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_doc_hash"
                # 缺少page和eventType
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "parameter" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_cleanup_on_stop(self, handler):
        """测试停止时的清理工作"""
        # 启动一些页面跟踪
        for page in [1, 2, 3]:
            raw_message = json.dumps({
                "id": f"test-id-{page}",
                "seq": page - 1,
                "method": "behavior",
                "params": {
                    "docHash": "test_doc_hash",
                    "page": page,
                    "eventType": "page_view"
                }
            })
            
            await handler.handle_request(raw_message)
        
        # 验证任务正在运行
        assert handler._intervention_task is not None
        assert not handler._intervention_task.done()
        
        # 停止干预检查
        handler.stop_intervention_check()
        
        # 等待任务完成取消
        try:
            await handler._intervention_task
        except asyncio.CancelledError:
            pass
        
        # 验证任务已取消
        assert handler._intervention_task.cancelled() or handler._intervention_task.done()
