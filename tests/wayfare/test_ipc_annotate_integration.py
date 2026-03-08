"""
测试IPC Handler的annotate方法集成

验证Task 5.8的实现：
- 参数解析和验证
- AnnotationGenerator集成
- 错误处理
- 响应格式
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from wayfare.ipc import IPCHandler, IPCRequest, IPCResponse
from wayfare.db import Annotation, BoundingBox


@pytest.fixture
def mock_annotation_gen():
    """创建mock的AnnotationGenerator"""
    mock = AsyncMock()
    
    # 模拟generate_annotation返回
    async def mock_generate(doc_hash, page, bbox, annotation_type, context):
        return Annotation(
            id="test_annotation_id_123",
            doc_hash=doc_hash,
            version_hash="test_version_hash",
            type=annotation_type,
            content=f"Generated {annotation_type} annotation for: {context}",
            bbox=BoundingBox(**bbox),
            created_at="2024-01-01T00:00:00Z"
        )
    
    mock.generate_annotation = mock_generate
    return mock


@pytest.fixture
def ipc_handler(mock_annotation_gen):
    """创建带有mock依赖的IPCHandler"""
    return IPCHandler(annotation_gen=mock_annotation_gen)


class TestHandleAnnotateBasic:
    """测试handle_annotate的基本功能"""
    
    @pytest.mark.asyncio
    async def test_handle_annotate_success(self, ipc_handler):
        """测试成功生成批注"""
        params = {
            "docHash": "test_doc_hash",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "explanation",
            "context": "费曼技巧是什么？"
        }
        
        result = await ipc_handler.handle_annotate(params)
        
        assert "annotationId" in result
        assert "content" in result
        assert "type" in result
        assert result["annotationId"] == "test_annotation_id_123"
        assert result["type"] == "explanation"
        assert "费曼技巧是什么？" in result["content"]
    
    @pytest.mark.asyncio
    async def test_handle_annotate_all_types(self, ipc_handler):
        """测试所有批注类型"""
        types = ["explanation", "question", "summary"]
        
        for annotation_type in types:
            params = {
                "docHash": "test_doc_hash",
                "page": 1,
                "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                "type": annotation_type,
                "context": "测试文本"
            }
            
            result = await ipc_handler.handle_annotate(params)
            
            assert result["type"] == annotation_type
            assert annotation_type in result["content"]


class TestHandleAnnotateValidation:
    """测试handle_annotate的参数验证"""
    
    @pytest.mark.asyncio
    async def test_missing_required_param(self, ipc_handler):
        """测试缺少必需参数"""
        required_params = ["docHash", "page", "bbox", "type", "context"]
        
        for missing_param in required_params:
            params = {
                "docHash": "test_doc_hash",
                "page": 1,
                "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                "type": "explanation",
                "context": "测试文本"
            }
            del params[missing_param]
            
            with pytest.raises(ValueError) as exc_info:
                await ipc_handler.handle_annotate(params)
            
            assert f"Missing required parameter: {missing_param}" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_missing_bbox_field(self, ipc_handler):
        """测试bbox缺少必需字段"""
        bbox_fields = ["x", "y", "width", "height"]
        
        for missing_field in bbox_fields:
            bbox = {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0}
            del bbox[missing_field]
            
            params = {
                "docHash": "test_doc_hash",
                "page": 1,
                "bbox": bbox,
                "type": "explanation",
                "context": "测试文本"
            }
            
            with pytest.raises(ValueError) as exc_info:
                await ipc_handler.handle_annotate(params)
            
            assert f"Missing required bbox field: {missing_field}" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_annotation_type(self, ipc_handler):
        """测试无效的批注类型"""
        params = {
            "docHash": "test_doc_hash",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "invalid_type",
            "context": "测试文本"
        }
        
        with pytest.raises(ValueError) as exc_info:
            await ipc_handler.handle_annotate(params)
        
        assert "Invalid annotation type" in str(exc_info.value)
        assert "invalid_type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_annotation_gen_not_initialized(self):
        """测试AnnotationGenerator未初始化"""
        handler = IPCHandler()  # 不传入annotation_gen
        
        params = {
            "docHash": "test_doc_hash",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "explanation",
            "context": "测试文本"
        }
        
        with pytest.raises(RuntimeError) as exc_info:
            await handler.handle_annotate(params)
        
        assert "AnnotationGenerator not initialized" in str(exc_info.value)


class TestHandleAnnotateErrorHandling:
    """测试handle_annotate的错误处理"""
    
    @pytest.mark.asyncio
    async def test_annotation_gen_value_error(self):
        """测试AnnotationGenerator抛出ValueError"""
        mock_gen = AsyncMock()
        mock_gen.generate_annotation.side_effect = ValueError("Document not found")
        
        handler = IPCHandler(annotation_gen=mock_gen)
        
        params = {
            "docHash": "nonexistent_doc",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "explanation",
            "context": "测试文本"
        }
        
        with pytest.raises(ValueError) as exc_info:
            await handler.handle_annotate(params)
        
        assert "Failed to generate annotation" in str(exc_info.value)
        assert "Document not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_annotation_gen_runtime_error(self):
        """测试AnnotationGenerator抛出其他异常"""
        mock_gen = AsyncMock()
        mock_gen.generate_annotation.side_effect = Exception("Database error")
        
        handler = IPCHandler(annotation_gen=mock_gen)
        
        params = {
            "docHash": "test_doc_hash",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "explanation",
            "context": "测试文本"
        }
        
        with pytest.raises(RuntimeError) as exc_info:
            await handler.handle_annotate(params)
        
        assert "Error generating annotation" in str(exc_info.value)
        assert "Database error" in str(exc_info.value)


class TestHandleAnnotateIntegration:
    """测试handle_annotate的完整IPC流程"""
    
    @pytest.mark.asyncio
    async def test_full_ipc_request_flow(self, ipc_handler):
        """测试完整的IPC请求流程"""
        request_message = """{
            "id": "test_request_123",
            "seq": 0,
            "method": "annotate",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                "type": "explanation",
                "context": "费曼技巧是什么？"
            }
        }"""
        
        response_str = await ipc_handler.handle_request(request_message)
        
        import json
        response = json.loads(response_str)
        
        assert response["id"] == "test_request_123"
        assert response["seq"] == 0
        assert response["success"] is True
        assert "data" in response
        assert "annotationId" in response["data"]
        assert "content" in response["data"]
        assert "type" in response["data"]
    
    @pytest.mark.asyncio
    async def test_ipc_request_with_error(self, ipc_handler):
        """测试IPC请求错误处理"""
        request_message = """{
            "id": "test_request_456",
            "seq": 0,
            "method": "annotate",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                "type": "invalid_type",
                "context": "测试文本"
            }
        }"""
        
        response_str = await ipc_handler.handle_request(request_message)
        
        import json
        response = json.loads(response_str)
        
        assert response["id"] == "test_request_456"
        assert response["seq"] == 0
        assert response["success"] is False
        assert "error" in response
        assert "Invalid annotation type" in response["error"]


class TestHandleAnnotateRequirements:
    """测试Requirements 5.4, 5.5, 5.6的验证"""
    
    @pytest.mark.asyncio
    async def test_requirement_5_4_parse_params(self, ipc_handler):
        """验证Requirement 5.4: 解析annotate请求参数"""
        params = {
            "docHash": "test_doc_hash",
            "page": 5,
            "bbox": {"x": 150.0, "y": 250.0, "width": 400.0, "height": 60.0},
            "type": "question",
            "context": "这是用户选中的文本"
        }
        
        result = await ipc_handler.handle_annotate(params)
        
        # 验证所有参数都被正确处理
        assert result is not None
        assert "annotationId" in result
    
    @pytest.mark.asyncio
    async def test_requirement_5_5_call_annotation_generator(self, mock_annotation_gen):
        """验证Requirement 5.5: 调用AnnotationGenerator生成批注"""
        handler = IPCHandler(annotation_gen=mock_annotation_gen)
        
        params = {
            "docHash": "test_doc_hash",
            "page": 3,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "summary",
            "context": "测试上下文"
        }
        
        result = await handler.handle_annotate(params)
        
        # 验证AnnotationGenerator被调用
        assert result["annotationId"] == "test_annotation_id_123"
        assert result["type"] == "summary"
    
    @pytest.mark.asyncio
    async def test_requirement_5_6_return_annotation_id_and_content(self, ipc_handler):
        """验证Requirement 5.6: 返回批注ID和内容"""
        params = {
            "docHash": "test_doc_hash",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "explanation",
            "context": "测试文本"
        }
        
        result = await ipc_handler.handle_annotate(params)
        
        # 验证返回格式
        assert "annotationId" in result
        assert "content" in result
        assert "type" in result
        assert isinstance(result["annotationId"], str)
        assert isinstance(result["content"], str)
        assert isinstance(result["type"], str)
        assert len(result["annotationId"]) > 0
        assert len(result["content"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
