"""
IPC Handler Parse Integration Tests

测试IPCHandler与DocumentParser的集成，包括：
- 异步parse请求处理
- 主动推送通知机制
- 错误处理
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from wayfare.ipc import IPCHandler, IPCRequest, IPCResponse
from wayfare.document_parser import ParseResult


class TestIPCParseIntegration:
    """测试IPC Handler的parse方法集成"""
    
    @pytest.fixture
    def mock_doc_parser(self):
        """创建mock DocumentParser"""
        parser = MagicMock()
        parser.compute_hash = MagicMock(return_value="test_doc_hash_123")
        parser.parse_document = AsyncMock(return_value=ParseResult(
            doc_hash="test_doc_hash_123",
            version_hash="test_version_hash_456",
            segment_count=10,
            status="completed"
        ))
        return parser
    
    @pytest.fixture
    def handler_with_parser(self, mock_doc_parser):
        """创建带DocumentParser的IPCHandler"""
        return IPCHandler(doc_parser=mock_doc_parser)
    
    @pytest.mark.asyncio
    async def test_handle_parse_returns_processing_immediately(self, handler_with_parser, mock_doc_parser):
        """测试：parse请求立即返回processing状态"""
        params = {"path": "/test/document.pdf"}
        
        result = await handler_with_parser.handle_parse(params)
        
        # 验证立即返回processing状态
        assert result["status"] == "processing"
        assert result["docHash"] == "test_doc_hash_123"
        
        # 验证调用了compute_hash
        mock_doc_parser.compute_hash.assert_called_once_with("/test/document.pdf")
    
    @pytest.mark.asyncio
    async def test_handle_parse_missing_path_parameter(self, handler_with_parser):
        """测试：parse请求缺少path参数"""
        params = {}
        
        with pytest.raises(ValueError, match="Missing required parameter: path"):
            await handler_with_parser.handle_parse(params)
    
    @pytest.mark.asyncio
    async def test_handle_parse_without_doc_parser(self):
        """测试：未初始化DocumentParser时调用parse"""
        handler = IPCHandler()  # 没有doc_parser
        params = {"path": "/test/document.pdf"}
        
        with pytest.raises(ValueError, match="DocumentParser not initialized"):
            await handler.handle_parse(params)
    
    @pytest.mark.asyncio
    async def test_handle_parse_compute_hash_failure(self, handler_with_parser, mock_doc_parser):
        """测试：compute_hash失败时的错误处理"""
        mock_doc_parser.compute_hash.side_effect = FileNotFoundError("File not found")
        params = {"path": "/test/nonexistent.pdf"}
        
        with pytest.raises(ValueError, match="Failed to compute document hash"):
            await handler_with_parser.handle_parse(params)
    
    @pytest.mark.asyncio
    async def test_async_parse_success_sends_notification(self, handler_with_parser, mock_doc_parser):
        """测试：异步解析成功后发送完成通知"""
        path = "/test/document.pdf"
        doc_hash = "test_doc_hash_123"
        
        # Mock _send_notification
        handler_with_parser._send_notification = AsyncMock()
        
        # 执行异步解析
        await handler_with_parser._async_parse(path, doc_hash)
        
        # 验证调用了parse_document
        mock_doc_parser.parse_document.assert_called_once_with(path)
        
        # 验证发送了完成通知
        handler_with_parser._send_notification.assert_called_once()
        notification_data = handler_with_parser._send_notification.call_args[0][0]
        
        assert notification_data["type"] == "parse_completed"
        assert notification_data["docHash"] == doc_hash
        assert notification_data["segmentCount"] == 10
        assert notification_data["versionHash"] == "test_version_hash_456"
        assert notification_data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_async_parse_failure_sends_error_notification(self, handler_with_parser, mock_doc_parser):
        """测试：异步解析失败后发送错误通知"""
        path = "/test/document.pdf"
        doc_hash = "test_doc_hash_123"
        
        # Mock parse_document to raise exception
        mock_doc_parser.parse_document.side_effect = Exception("Parse error")
        
        # Mock _send_notification
        handler_with_parser._send_notification = AsyncMock()
        
        # 执行异步解析
        await handler_with_parser._async_parse(path, doc_hash)
        
        # 验证发送了失败通知
        handler_with_parser._send_notification.assert_called_once()
        notification_data = handler_with_parser._send_notification.call_args[0][0]
        
        assert notification_data["type"] == "parse_failed"
        assert notification_data["docHash"] == doc_hash
        assert "Parse error" in notification_data["error"]
        assert notification_data["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_send_notification_outputs_to_stdout(self, handler_with_parser):
        """测试：_send_notification输出到stdout"""
        notification_data = {
            "type": "parse_completed",
            "docHash": "test_hash",
            "status": "completed"
        }
        
        with patch('builtins.print') as mock_print:
            await handler_with_parser._send_notification(notification_data)
            
            # 验证调用了print
            mock_print.assert_called_once()
            
            # 验证输出的JSON格式
            call_args = mock_print.call_args
            output = call_args[0][0]
            parsed = json.loads(output)
            
            assert parsed["type"] == "notification"
            assert parsed["data"]["type"] == "parse_completed"
            assert parsed["data"]["docHash"] == "test_hash"
    
    @pytest.mark.asyncio
    async def test_full_parse_request_flow(self, handler_with_parser, mock_doc_parser):
        """测试：完整的parse请求流程"""
        # 构造请求消息
        raw_message = json.dumps({
            "id": "req-123",
            "seq": 0,
            "method": "parse",
            "params": {"path": "/test/document.pdf"}
        })
        
        # Mock _send_notification
        handler_with_parser._send_notification = AsyncMock()
        
        # 处理请求
        response_str = await handler_with_parser.handle_request(raw_message)
        response = json.loads(response_str)
        
        # 验证立即响应
        assert response["success"] is True
        assert response["data"]["status"] == "processing"
        assert response["data"]["docHash"] == "test_doc_hash_123"
        
        # 等待异步任务完成
        await asyncio.sleep(0.1)
        
        # 验证异步解析被触发
        mock_doc_parser.parse_document.assert_called_once_with("/test/document.pdf")
        
        # 验证发送了通知
        handler_with_parser._send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_does_not_block_other_requests(self, handler_with_parser, mock_doc_parser):
        """测试：parse请求不阻塞其他请求"""
        # 让parse_document执行较长时间
        async def slow_parse(path):
            await asyncio.sleep(0.2)
            return ParseResult(
                doc_hash="test_hash",
                version_hash="version_hash",
                segment_count=5,
                status="completed"
            )
        
        mock_doc_parser.parse_document = slow_parse
        handler_with_parser._send_notification = AsyncMock()
        
        # 发送parse请求
        parse_request = json.dumps({
            "id": "req-1",
            "seq": 0,
            "method": "parse",
            "params": {"path": "/test/doc.pdf"}
        })
        
        # 发送config请求
        config_request = json.dumps({
            "id": "req-2",
            "seq": 1,
            "method": "config",
            "params": {"llmModel": "deepseek-chat"}
        })
        
        # 处理parse请求（应该立即返回）
        parse_response_str = await handler_with_parser.handle_request(parse_request)
        parse_response = json.loads(parse_response_str)
        
        # 验证parse立即返回processing
        assert parse_response["data"]["status"] == "processing"
        
        # 处理config请求（应该不被阻塞）
        config_response_str = await handler_with_parser.handle_request(config_request)
        config_response = json.loads(config_response_str)
        
        # 验证config请求正常处理
        assert config_response["success"] is True
        
        # 等待异步parse完成
        await asyncio.sleep(0.3)
        
        # 验证异步parse完成并发送了通知
        handler_with_parser._send_notification.assert_called_once()


class TestIPCHandlerInitialization:
    """测试IPCHandler的初始化"""
    
    def test_init_with_all_dependencies(self):
        """测试：使用所有依赖初始化"""
        doc_parser = MagicMock()
        annotation_gen = MagicMock()
        vector_store = MagicMock()
        config_manager = MagicMock()
        behavior_analyzer = MagicMock()
        
        handler = IPCHandler(
            doc_parser=doc_parser,
            annotation_gen=annotation_gen,
            vector_store=vector_store,
            config_manager=config_manager,
            behavior_analyzer=behavior_analyzer
        )
        
        assert handler.doc_parser is doc_parser
        assert handler.annotation_gen is annotation_gen
        assert handler.vector_store is vector_store
        assert handler.config_manager is config_manager
        assert handler.behavior_analyzer is behavior_analyzer
    
    def test_init_with_partial_dependencies(self):
        """测试：使用部分依赖初始化"""
        doc_parser = MagicMock()
        
        handler = IPCHandler(doc_parser=doc_parser)
        
        assert handler.doc_parser is doc_parser
        assert handler.annotation_gen is None
        assert handler.vector_store is None
        assert handler.config_manager is None
        assert handler.behavior_analyzer is None
    
    def test_init_without_dependencies(self):
        """测试：不使用依赖初始化"""
        handler = IPCHandler()
        
        assert handler.doc_parser is None
        assert handler.annotation_gen is None
        assert handler.vector_store is None
        assert handler.config_manager is None
        assert handler.behavior_analyzer is None
