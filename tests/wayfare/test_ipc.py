"""
IPC Handler单元测试

测试IPC请求解析、验证、队列管理和响应封装功能。
"""

import pytest
import json
import asyncio
from wayfare.ipc import IPCHandler, IPCRequest, IPCResponse


class TestIPCRequest:
    """测试IPCRequest数据模型"""
    
    def test_valid_request(self):
        """测试创建有效的请求"""
        request = IPCRequest(
            id="test-id",
            seq=1,
            method="parse",
            params={"path": "/test/path"}
        )
        assert request.id == "test-id"
        assert request.seq == 1
        assert request.method == "parse"
        assert request.params == {"path": "/test/path"}
    
    def test_request_without_params(self):
        """测试创建不带params的请求"""
        request = IPCRequest(
            id="test-id",
            seq=1,
            method="parse"
        )
        assert request.params == {}
    
    def test_request_with_empty_id(self):
        """测试空id应该抛出异常"""
        with pytest.raises(ValueError, match="Request id is required"):
            IPCRequest(id="", seq=1, method="parse")
    
    def test_request_with_negative_seq(self):
        """测试负数seq应该抛出异常"""
        with pytest.raises(ValueError, match="Request seq must be non-negative"):
            IPCRequest(id="test-id", seq=-1, method="parse")
    
    def test_request_with_empty_method(self):
        """测试空method应该抛出异常"""
        with pytest.raises(ValueError, match="Request method is required"):
            IPCRequest(id="test-id", seq=1, method="")


class TestIPCResponse:
    """测试IPCResponse数据模型"""
    
    def test_success_response(self):
        """测试成功响应"""
        response = IPCResponse(
            id="test-id",
            seq=1,
            success=True,
            data={"result": "ok"}
        )
        response_dict = response.to_dict()
        assert response_dict["id"] == "test-id"
        assert response_dict["seq"] == 1
        assert response_dict["success"] is True
        assert response_dict["data"] == {"result": "ok"}
        assert "error" not in response_dict
    
    def test_error_response(self):
        """测试错误响应"""
        response = IPCResponse(
            id="test-id",
            seq=1,
            success=False,
            error="Something went wrong"
        )
        response_dict = response.to_dict()
        assert response_dict["id"] == "test-id"
        assert response_dict["seq"] == 1
        assert response_dict["success"] is False
        assert response_dict["error"] == "Something went wrong"
        assert "data" not in response_dict


class TestIPCHandler:
    """测试IPCHandler类"""
    
    @pytest.fixture
    def mock_doc_parser(self):
        """创建mock DocumentParser"""
        from unittest.mock import MagicMock, AsyncMock
        from wayfare.document_parser import ParseResult
        
        parser = MagicMock()
        parser.compute_hash = MagicMock(return_value="mock_hash_123")
        
        # Configure AsyncMock to return a proper ParseResult object
        mock_result = ParseResult(
            doc_hash="mock_hash_123",
            version_hash="mock_version_123",
            segment_count=5,
            status="completed"
        )
        parser.parse_document = AsyncMock(return_value=mock_result)
        return parser
    
    @pytest.fixture
    def mock_vector_store(self):
        """创建mock VectorStore"""
        from unittest.mock import MagicMock, AsyncMock
        from dataclasses import dataclass
        
        @dataclass
        class MockSearchResult:
            segment_id: str
            text: str
            page: int
            score: float
        
        store = MagicMock()
        store.search_documents = AsyncMock(return_value=[
            MockSearchResult(
                segment_id="seg_1",
                text="mock result",
                page=1,
                score=0.9
            )
        ])
        return store
    
    @pytest.fixture
    def mock_annotation_gen(self):
        """创建mock AnnotationGenerator"""
        from unittest.mock import MagicMock, AsyncMock
        from dataclasses import dataclass
        
        @dataclass
        class MockAnnotation:
            id: str
            content: str
            type: str
        
        gen = MagicMock()
        gen.generate_annotation = AsyncMock(return_value=MockAnnotation(
            id="anno_123",
            content="mock annotation",
            type="explanation"
        ))
        return gen
    
    @pytest.fixture
    def mock_embedding_service(self):
        """创建mock EmbeddingService"""
        from unittest.mock import MagicMock, AsyncMock
        
        service = MagicMock()
        service.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        return service
    
    @pytest.fixture
    def mock_config_manager(self):
        """创建mock ConfigManager"""
        from unittest.mock import MagicMock
        
        manager = MagicMock()
        manager.update_config = MagicMock(return_value={"status": "updated"})
        return manager
    
    @pytest.fixture
    def mock_behavior_analyzer(self):
        """创建mock BehaviorAnalyzer"""
        from unittest.mock import MagicMock, AsyncMock
        from dataclasses import dataclass
        
        @dataclass
        class MockBehaviorEvent:
            id: str
            doc_hash: str
            page: int
            event_type: str
            timestamp: str
            metadata: dict
        
        analyzer = MagicMock()
        analyzer.record_behavior = AsyncMock(return_value=MockBehaviorEvent(
            id="behavior_123",
            doc_hash="doc_hash",
            page=1,
            event_type="page_view",
            timestamp="2024-01-01T00:00:00Z",
            metadata={}
        ))
        analyzer.check_intervention_trigger = AsyncMock(return_value=False)
        analyzer.send_intervention = AsyncMock()
        return analyzer
    
    @pytest.fixture
    def handler(self, mock_doc_parser, mock_vector_store, mock_annotation_gen, 
                mock_embedding_service, mock_config_manager, mock_behavior_analyzer):
        """创建IPCHandler实例（带所有mock依赖）"""
        return IPCHandler(
            doc_parser=mock_doc_parser,
            vector_store=mock_vector_store,
            annotation_gen=mock_annotation_gen,
            embedding_service=mock_embedding_service,
            config_manager=mock_config_manager,
            behavior_analyzer=mock_behavior_analyzer
        )
    
    @pytest.mark.asyncio
    async def test_parse_valid_request(self, handler):
        """测试解析有效的请求"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "parse",
            "params": {"path": "/test/path"}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["id"] == "test-id"
        assert response["seq"] == 0
        assert response["success"] is True
        assert "data" in response
    
    @pytest.mark.asyncio
    async def test_parse_request_without_id(self, handler):
        """测试缺少id的请求"""
        raw_message = json.dumps({
            "seq": 0,
            "method": "parse",
            "params": {"path": "/test/path"}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "id" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_parse_request_without_seq(self, handler):
        """测试缺少seq的请求"""
        raw_message = json.dumps({
            "id": "test-id",
            "method": "parse",
            "params": {"path": "/test/path"}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "seq" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_parse_request_without_method(self, handler):
        """测试缺少method的请求"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "params": {"path": "/test/path"}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "method" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_unsupported_method(self, handler):
        """测试不支持的方法"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "unsupported_method",
            "params": {}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "unsupported method" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_json(self, handler):
        """测试无效的JSON"""
        raw_message = "not a valid json"
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        # JSON解析错误消息可能包含"json"或"expecting value"等关键词
        assert ("json" in response["error"].lower() or 
                "expecting" in response["error"].lower())
    
    @pytest.mark.asyncio
    async def test_sequential_requests(self, handler):
        """测试按seq顺序处理请求"""
        # 发送seq=0的请求
        raw_message_0 = json.dumps({
            "id": "test-id-0",
            "seq": 0,
            "method": "parse",
            "params": {"path": "/test/path0"}
        })
        response_str_0 = await handler.handle_request(raw_message_0)
        response_0 = json.loads(response_str_0)
        assert response_0["seq"] == 0
        assert response_0["success"] is True
        
        # 发送seq=1的请求
        raw_message_1 = json.dumps({
            "id": "test-id-1",
            "seq": 1,
            "method": "query",
            "params": {"docHash": "hash", "query": "test"}
        })
        response_str_1 = await handler.handle_request(raw_message_1)
        response_1 = json.loads(response_str_1)
        assert response_1["seq"] == 1
        assert response_1["success"] is True
    
    @pytest.mark.asyncio
    async def test_out_of_order_requests(self, handler):
        """测试乱序请求的处理"""
        # 先发送seq=2的请求（会被缓存）
        raw_message_2 = json.dumps({
            "id": "test-id-2",
            "seq": 2,
            "method": "parse",
            "params": {"path": "/test/path2"}
        })
        response_str_2 = await handler.handle_request(raw_message_2)
        response_2 = json.loads(response_str_2)
        # 应该返回queued状态
        assert response_2["success"] is True
        
        # 再发送seq=0的请求（应该立即处理）
        raw_message_0 = json.dumps({
            "id": "test-id-0",
            "seq": 0,
            "method": "parse",
            "params": {"path": "/test/path0"}
        })
        response_str_0 = await handler.handle_request(raw_message_0)
        response_0 = json.loads(response_str_0)
        assert response_0["seq"] == 0
        assert response_0["success"] is True
    
    @pytest.mark.asyncio
    async def test_parse_method_missing_path(self, handler):
        """测试parse方法缺少path参数"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "parse",
            "params": {}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "path" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_annotate_method_missing_params(self, handler):
        """测试annotate方法缺少必需参数"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "annotate",
            "params": {"docHash": "hash"}  # 缺少其他必需参数
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "parameter" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_query_method_missing_params(self, handler):
        """测试query方法缺少必需参数"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "query",
            "params": {"docHash": "hash"}  # 缺少query参数
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "query" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_config_method(self, handler):
        """测试config方法"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "config",
            "params": {"llm_model": "deepseek-chat"}
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is True
        assert "data" in response
    
    @pytest.mark.asyncio
    async def test_all_supported_methods(self, handler):
        """测试所有支持的方法"""
        methods = ["parse", "annotate", "query", "config", "behavior"]
        
        for i, method in enumerate(methods):
            # 为每个方法构造合适的参数
            if method == "parse":
                params = {"path": "/test/path"}
            elif method == "annotate":
                params = {
                    "docHash": "hash",
                    "page": 1,
                    "bbox": {"x": 0, "y": 0, "width": 100, "height": 100},
                    "type": "explanation",
                    "context": "test context"
                }
            elif method == "query":
                params = {"docHash": "hash", "query": "test query"}
            elif method == "behavior":
                params = {
                    "docHash": "hash",
                    "page": 1,
                    "eventType": "page_view",
                    "metadata": {}
                }
            else:  # config
                params = {"llm_model": "test-model"}
            
            raw_message = json.dumps({
                "id": f"test-id-{i}",
                "seq": i,
                "method": method,
                "params": params
            })
            
            response_str = await handler.handle_request(raw_message)
            response = json.loads(response_str)
            
            assert response["success"] is True
            assert response["seq"] == i
    
    @pytest.mark.asyncio
    async def test_behavior_method_valid_request(self, handler):
        """测试behavior方法的有效请求"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_hash",
                "page": 1,
                "eventType": "page_view",
                "metadata": {"duration": 30}
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is True
        assert response["data"]["recorded"] is True
        assert "eventId" in response["data"]
        
        # 验证BehaviorAnalyzer被调用
        handler.behavior_analyzer.record_behavior.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_behavior_method_missing_params(self, handler):
        """测试behavior方法缺少必需参数"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {"docHash": "hash"}  # 缺少page和eventType
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "parameter" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_behavior_method_invalid_event_type(self, handler):
        """测试behavior方法使用无效的事件类型"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "hash",
                "page": 1,
                "eventType": "invalid_type"
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "eventtype" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_behavior_method_without_analyzer(self):
        """测试behavior方法在没有BehaviorAnalyzer时的行为"""
        handler = IPCHandler()  # 不提供behavior_analyzer
        
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "hash",
                "page": 1,
                "eventType": "page_view"
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is False
        assert "not initialized" in response["error"].lower()
    
    @pytest.mark.asyncio
    async def test_behavior_page_view_starts_intervention_check(self, handler):
        """测试page_view事件启动干预检查任务"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_hash",
                "page": 1,
                "eventType": "page_view"
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is True
        
        # 验证活跃页面被跟踪
        key = "test_hash_1"
        assert key in handler._active_pages
        assert handler._active_pages[key]["docHash"] == "test_hash"
        assert handler._active_pages[key]["page"] == 1
        
        # 清理任务
        handler.stop_intervention_check()
    
    @pytest.mark.asyncio
    async def test_behavior_non_page_view_does_not_track(self, handler):
        """测试非page_view事件不启动跟踪"""
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_hash",
                "page": 1,
                "eventType": "text_select"
            }
        })
        
        response_str = await handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        assert response["success"] is True
        
        # 验证活跃页面未被跟踪
        key = "test_hash_1"
        assert key not in handler._active_pages
    
    @pytest.mark.asyncio
    async def test_stop_intervention_check(self, handler):
        """测试停止干预检查任务"""
        # 先启动一个page_view事件
        raw_message = json.dumps({
            "id": "test-id",
            "seq": 0,
            "method": "behavior",
            "params": {
                "docHash": "test_hash",
                "page": 1,
                "eventType": "page_view"
            }
        })
        
        await handler.handle_request(raw_message)
        
        # 停止干预检查
        handler.stop_intervention_check()
        
        # 等待任务完成取消
        if handler._intervention_task:
            try:
                await handler._intervention_task
            except asyncio.CancelledError:
                pass  # 预期的取消错误
            
            # 验证任务被取消
            assert handler._intervention_task.cancelled() or handler._intervention_task.done()
