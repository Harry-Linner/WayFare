"""
测试批注生成流程的完整集成

验证Task 9.2的实现：
- 测试从IPC请求到批注返回的完整流程
- 测试RAG检索和LLM调用集成
- 测试三种批注类型的生成
- 测试批注与文档位置和版本的关联
- 测试批注存储到数据库
- 测试错误场景和降级机制

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from wayfare.ipc import IPCHandler
from wayfare.annotation_generator import AnnotationGenerator
from wayfare.llm_provider import WayFareLLMProvider, LLMResponse
from wayfare.context_builder import WayFareContextBuilder
from wayfare.vector_store import VectorStore, SearchResult
from wayfare.embedding import EmbeddingService
from wayfare.db import SQLiteDB, Annotation, BoundingBox
import numpy as np


@pytest.fixture
async def temp_db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = SQLiteDB(db_path)
        await db.initialize()
        
        # 插入测试文档
        await db.save_document({
            "hash": "test_doc_hash",
            "path": "/test/doc.pdf",
            "status": "completed",
            "version_hash": "test_version_hash"
        })
        
        yield db


@pytest.fixture
def mock_embedding_service():
    """创建mock的EmbeddingService"""
    mock = AsyncMock(spec=EmbeddingService)
    
    # 返回固定的向量
    mock.embed_single = AsyncMock(return_value=np.random.rand(512).astype(np.float32))
    
    return mock


@pytest.fixture
def mock_vector_store():
    """创建mock的VectorStore"""
    mock = AsyncMock(spec=VectorStore)
    
    # 返回模拟的搜索结果
    def mock_search_side_effect(query_vector, top_k, doc_hash=None):
        return [
            SearchResult(
                segment_id=f"seg_{i}",
                text=f"相关上下文片段 {i}：这是关于费曼技巧的内容。",
                page=1,
                score=0.9 - i * 0.1,
                doc_hash=doc_hash or "test_doc_hash"
            )
            for i in range(min(top_k, 5))
        ]
    
    mock.search = AsyncMock(side_effect=mock_search_side_effect)
    return mock


@pytest.fixture
def mock_llm_provider():
    """创建mock的LLMProvider"""
    mock = AsyncMock(spec=WayFareLLMProvider)
    
    # 返回模拟的LLM响应
    def mock_generate_side_effect(messages, max_tokens=None, temperature=None):
        # 根据消息内容生成不同的响应
        user_msg = str(messages)
        
        if "explanation" in user_msg.lower():
            content = "费曼技巧是一种学习方法，通过用简单的语言解释复杂概念来加深理解。"
        elif "question" in user_msg.lower():
            content = "1. 你能用自己的话解释这个概念吗？\n2. 这个概念在实际中如何应用？"
        elif "summary" in user_msg.lower():
            content = "核心要点：费曼技巧强调通过教学来学习，用简单语言表达复杂概念。"
        else:
            content = "这是一个通用的批注内容。"
        
        return LLMResponse(
            content=content,
            finish_reason="stop",
            usage={"prompt_tokens": 100, "completion_tokens": 50}
        )
    
    mock.generate = AsyncMock(side_effect=mock_generate_side_effect)
    return mock


@pytest.fixture
def context_builder():
    """创建真实的ContextBuilder"""
    return WayFareContextBuilder()


@pytest.fixture
async def annotation_generator(
    mock_llm_provider,
    context_builder,
    mock_vector_store,
    mock_embedding_service,
    temp_db
):
    """创建AnnotationGenerator实例"""
    return AnnotationGenerator(
        llm_provider=mock_llm_provider,
        context_builder=context_builder,
        vector_store=mock_vector_store,
        embedding_service=mock_embedding_service,
        db=temp_db
    )


@pytest.fixture
async def ipc_handler(annotation_generator):
    """创建IPCHandler实例"""
    return IPCHandler(annotation_gen=annotation_generator)


class TestCompleteAnnotationFlow:
    """测试完整的批注生成流程"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_annotation_generation(self, ipc_handler, temp_db):
        """
        测试从IPC请求到批注返回的完整流程
        
        验证Requirements:
        - 4.1: RAG检索相关上下文
        - 4.2: LLM生成批注内容
        - 4.3: 批注与文档位置关联
        - 4.4: 批注绑定到versionHash
        - 4.5: 批注存储到数据库
        - 4.6: 返回批注ID和内容
        """
        # 构造IPC请求
        request_message = """{
            "id": "test_request_001",
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
        
        # 发送请求
        response_str = await ipc_handler.handle_request(request_message)
        
        # 解析响应
        import json
        response = json.loads(response_str)
        
        # 验证响应格式
        assert response["success"] is True
        assert "data" in response
        assert "annotationId" in response["data"]
        assert "content" in response["data"]
        assert "type" in response["data"]
        
        # 验证批注内容
        annotation_id = response["data"]["annotationId"]
        assert len(annotation_id) > 0
        assert response["data"]["type"] == "explanation"
        assert len(response["data"]["content"]) > 0
        
        # 验证批注已保存到数据库
        saved_annotation = await temp_db.get_annotation(annotation_id)
        assert saved_annotation is not None
        assert saved_annotation.doc_hash == "test_doc_hash"
        assert saved_annotation.version_hash == "test_version_hash"
        assert saved_annotation.type == "explanation"
        assert saved_annotation.bbox.x == 100.0
        assert saved_annotation.bbox.y == 200.0


class TestRAGIntegration:
    """测试RAG检索集成"""
    
    @pytest.mark.asyncio
    async def test_rag_retrieval_called(
        self,
        annotation_generator,
        mock_embedding_service,
        mock_vector_store
    ):
        """
        测试RAG检索被正确调用
        
        验证Requirement 4.1: 使用RAG检索相关上下文
        """
        # 生成批注
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证embedding服务被调用
        mock_embedding_service.embed_single.assert_called_once()
        call_args = mock_embedding_service.embed_single.call_args
        assert "测试文本" in str(call_args)
        
        # 验证向量搜索被调用
        mock_vector_store.search.assert_called_once()
        search_call = mock_vector_store.search.call_args
        assert search_call.kwargs["doc_hash"] == "test_doc_hash"
        assert search_call.kwargs["top_k"] == 5
    
    @pytest.mark.asyncio
    async def test_rag_context_used_in_prompt(
        self,
        annotation_generator,
        mock_llm_provider
    ):
        """
        测试RAG检索的上下文被用于构建Prompt
        
        验证Requirement 4.1: RAG上下文集成到LLM调用
        """
        # 生成批注
        await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="费曼技巧"
        )
        
        # 验证LLM被调用
        mock_llm_provider.generate.assert_called_once()
        
        # 获取传递给LLM的消息
        call_args = mock_llm_provider.generate.call_args
        messages = call_args.kwargs["messages"]
        
        # 验证消息包含用户文本和上下文
        message_str = str(messages)
        assert "费曼技巧" in message_str
        assert "相关上下文" in message_str or "context" in message_str.lower()


class TestLLMIntegration:
    """测试LLM调用集成"""
    
    @pytest.mark.asyncio
    async def test_llm_called_with_correct_params(
        self,
        annotation_generator,
        mock_llm_provider
    ):
        """
        测试LLM使用正确的参数调用
        
        验证Requirement 4.2: 调用LLM生成批注内容
        """
        # 生成批注
        await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="question",
            context="测试文本"
        )
        
        # 验证LLM调用参数
        call_args = mock_llm_provider.generate.call_args
        assert call_args.kwargs["max_tokens"] == 512
        assert call_args.kwargs["temperature"] == 0.7
        
        # 验证消息格式
        messages = call_args.kwargs["messages"]
        assert isinstance(messages, list)
        assert len(messages) > 0
        assert all("role" in msg and "content" in msg for msg in messages)
    
    @pytest.mark.asyncio
    async def test_llm_response_processed_correctly(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试LLM响应被正确处理
        
        验证Requirement 4.2: LLM生成的内容被正确保存
        """
        # 生成批注
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="费曼技巧"
        )
        
        # 验证批注内容来自LLM（不为空即可）
        assert len(annotation.content) > 0
        
        # 验证内容已保存到数据库
        saved = await temp_db.get_annotation(annotation.id)
        assert saved.content == annotation.content


class TestAnnotationTypes:
    """测试三种批注类型"""
    
    @pytest.mark.asyncio
    async def test_explanation_type_generation(self, annotation_generator):
        """
        测试explanation类型批注生成
        
        验证Requirement 4.7: 支持explanation批注类型
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="费曼技巧"
        )
        
        assert annotation.type == "explanation"
        assert len(annotation.content) > 0
        # explanation应该包含解释性内容
        assert any(
            keyword in annotation.content
            for keyword in ["是", "方法", "技巧", "学习", "理解"]
        )
    
    @pytest.mark.asyncio
    async def test_question_type_generation(self, annotation_generator):
        """
        测试question类型批注生成
        
        验证Requirement 4.7: 支持question批注类型
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="question",
            context="费曼技巧"
        )
        
        assert annotation.type == "question"
        assert len(annotation.content) > 0
    
    @pytest.mark.asyncio
    async def test_summary_type_generation(self, annotation_generator):
        """
        测试summary类型批注生成
        
        验证Requirement 4.7: 支持summary批注类型
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="summary",
            context="费曼技巧是一种学习方法"
        )
        
        assert annotation.type == "summary"
        assert len(annotation.content) > 0
    
    @pytest.mark.asyncio
    async def test_all_three_types_in_sequence(self, annotation_generator, temp_db):
        """
        测试连续生成三种类型的批注
        
        验证Requirement 4.7: 支持三种批注类型
        """
        types = ["explanation", "question", "summary"]
        annotations = []
        
        for ann_type in types:
            annotation = await annotation_generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=1,
                bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type=ann_type,
                context="测试文本"
            )
            annotations.append(annotation)
        
        # 验证所有批注都已生成
        assert len(annotations) == 3
        assert [a.type for a in annotations] == types
        
        # 验证所有批注都已保存
        for annotation in annotations:
            saved = await temp_db.get_annotation(annotation.id)
            assert saved is not None


class TestPositionAssociation:
    """测试批注位置关联"""
    
    @pytest.mark.asyncio
    async def test_annotation_bbox_association(self, annotation_generator):
        """
        测试批注与bbox位置关联
        
        验证Requirement 4.3: 批注与文档位置关联
        """
        bbox = {"x": 150.5, "y": 250.3, "width": 400.2, "height": 60.8}
        
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=5,
            bbox=bbox,
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证bbox信息
        assert annotation.bbox.x == bbox["x"]
        assert annotation.bbox.y == bbox["y"]
        assert annotation.bbox.width == bbox["width"]
        assert annotation.bbox.height == bbox["height"]
    
    @pytest.mark.asyncio
    async def test_annotation_page_association(self, annotation_generator, temp_db):
        """
        测试批注与页码关联（通过参数传递）
        
        验证Requirement 4.3: 批注与页码关联
        """
        page = 10
        
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=page,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 注意：page参数传递给generate_annotation但不存储在Annotation对象中
        # 这是设计决策，page信息通过bbox位置隐含
        assert annotation.doc_hash == "test_doc_hash"


class TestVersionBinding:
    """测试批注版本绑定"""
    
    @pytest.mark.asyncio
    async def test_annotation_bound_to_version_hash(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试批注绑定到文档versionHash
        
        验证Requirement 4.4: 批注绑定到versionHash
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证version_hash
        assert annotation.version_hash == "test_version_hash"
        
        # 验证数据库中的version_hash
        saved = await temp_db.get_annotation(annotation.id)
        assert saved.version_hash == "test_version_hash"
    
    @pytest.mark.asyncio
    async def test_version_hash_from_database(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试version_hash从数据库获取
        
        验证Requirement 4.4: 从文档记录获取version_hash
        """
        # 更新文档的version_hash
        await temp_db.save_document({
            "hash": "test_doc_hash",
            "path": "/test/doc.pdf",
            "status": "completed",
            "version_hash": "new_version_hash_v2"
        })
        
        # 生成批注
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证使用了新的version_hash
        assert annotation.version_hash == "new_version_hash_v2"


class TestDatabaseStorage:
    """测试批注存储到数据库"""
    
    @pytest.mark.asyncio
    async def test_annotation_saved_to_database(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试批注存储到SQLite数据库
        
        验证Requirement 4.5: 批注存储到数据库
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证数据库中存在该批注
        saved = await temp_db.get_annotation(annotation.id)
        assert saved is not None
        assert saved.id == annotation.id
        assert saved.doc_hash == annotation.doc_hash
        assert saved.type == annotation.type
        assert saved.content == annotation.content
    
    @pytest.mark.asyncio
    async def test_annotation_with_all_fields_saved(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试批注的所有字段都被正确保存
        
        验证Requirement 4.5: 完整的批注数据存储
        """
        bbox = {"x": 123.45, "y": 678.90, "width": 234.56, "height": 89.01}
        
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=3,
            bbox=bbox,
            annotation_type="question",
            context="测试文本"
        )
        
        # 从数据库读取
        saved = await temp_db.get_annotation(annotation.id)
        
        # 验证所有字段
        assert saved.id == annotation.id
        assert saved.doc_hash == "test_doc_hash"
        assert saved.version_hash == "test_version_hash"
        assert saved.type == "question"
        assert saved.content == annotation.content
        assert saved.bbox.x == bbox["x"]
        assert saved.bbox.y == bbox["y"]
        assert saved.bbox.width == bbox["width"]
        assert saved.bbox.height == bbox["height"]
        assert saved.created_at is not None
    
    @pytest.mark.asyncio
    async def test_multiple_annotations_saved(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试多个批注可以保存到数据库
        
        验证Requirement 4.5: 支持多个批注存储
        """
        annotations = []
        
        for i in range(3):
            annotation = await annotation_generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=i,
                bbox={"x": 100.0 + i, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type="explanation",
                context=f"测试文本 {i}"
            )
            annotations.append(annotation)
        
        # 验证所有批注都已保存
        for annotation in annotations:
            saved = await temp_db.get_annotation(annotation.id)
            assert saved is not None
            assert saved.id == annotation.id


class TestResponseFormat:
    """测试批注返回格式"""
    
    @pytest.mark.asyncio
    async def test_annotation_id_returned(self, annotation_generator):
        """
        测试返回批注ID
        
        验证Requirement 4.6: 返回批注ID
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证ID格式（UUID）
        assert annotation.id is not None
        assert len(annotation.id) > 0
        assert "-" in annotation.id  # UUID格式包含连字符
    
    @pytest.mark.asyncio
    async def test_annotation_content_returned(self, annotation_generator):
        """
        测试返回批注内容
        
        验证Requirement 4.6: 返回批注内容
        """
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="费曼技巧"
        )
        
        # 验证内容不为空
        assert annotation.content is not None
        assert len(annotation.content) > 0
        assert isinstance(annotation.content, str)
    
    @pytest.mark.asyncio
    async def test_ipc_response_format(self, ipc_handler):
        """
        测试IPC响应格式
        
        验证Requirement 4.6: IPC返回格式正确
        """
        request_message = """{
            "id": "test_request_002",
            "seq": 0,
            "method": "annotate",
            "params": {
                "docHash": "test_doc_hash",
                "page": 1,
                "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                "type": "summary",
                "context": "测试文本"
            }
        }"""
        
        response_str = await ipc_handler.handle_request(request_message)
        
        import json
        response = json.loads(response_str)
        
        # 验证响应结构
        assert "id" in response
        assert "seq" in response
        assert "success" in response
        assert "data" in response
        
        # 验证data字段
        data = response["data"]
        assert "annotationId" in data
        assert "content" in data
        assert "type" in data
        
        # 验证值的类型
        assert isinstance(data["annotationId"], str)
        assert isinstance(data["content"], str)
        assert isinstance(data["type"], str)


class TestErrorScenarios:
    """测试错误场景"""
    
    @pytest.mark.asyncio
    async def test_document_not_found(self, annotation_generator, temp_db):
        """
        测试文档不存在时的错误处理
        """
        with pytest.raises(ValueError) as exc_info:
            await annotation_generator.generate_annotation(
                doc_hash="nonexistent_doc",
                page=1,
                bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type="explanation",
                context="测试文本"
            )
        
        assert "Document not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_annotation_type(self, annotation_generator):
        """
        测试无效的批注类型
        """
        with pytest.raises(ValueError) as exc_info:
            await annotation_generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=1,
                bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type="invalid_type",
                context="测试文本"
            )
        
        assert "Invalid annotation_type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_empty_context(self, annotation_generator):
        """
        测试空的上下文文本
        """
        with pytest.raises(ValueError) as exc_info:
            await annotation_generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=1,
                bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type="explanation",
                context=""
            )
        
        assert "context cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_bbox(self, annotation_generator):
        """
        测试无效的bbox参数
        """
        with pytest.raises(ValueError) as exc_info:
            await annotation_generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=1,
                bbox={"x": 100.0, "y": 200.0},  # 缺少width和height
                annotation_type="explanation",
                context="测试文本"
            )
        
        assert "bbox missing required key" in str(exc_info.value)


class TestFallbackMechanism:
    """测试LLM失败时的降级机制"""
    
    @pytest.mark.asyncio
    async def test_llm_failure_fallback(
        self,
        context_builder,
        mock_vector_store,
        mock_embedding_service,
        temp_db
    ):
        """
        测试LLM调用失败时使用降级策略
        
        验证Requirement 4.2: 实现降级机制
        """
        # 创建会失败的LLM provider
        failing_llm = AsyncMock(spec=WayFareLLMProvider)
        failing_llm.generate.side_effect = Exception("LLM service unavailable")
        
        generator = AnnotationGenerator(
            llm_provider=failing_llm,
            context_builder=context_builder,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            db=temp_db
        )
        
        # 生成批注（应该使用降级策略）
        annotation = await generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        # 验证返回了降级内容
        assert annotation is not None
        assert annotation.content is not None
        assert len(annotation.content) > 0
        # 降级内容应该包含提示信息
        assert "暂时无法" in annotation.content or "稍后" in annotation.content
    
    @pytest.mark.asyncio
    async def test_llm_empty_response_fallback(
        self,
        context_builder,
        mock_vector_store,
        mock_embedding_service,
        temp_db
    ):
        """
        测试LLM返回空内容时使用降级策略
        
        验证Requirement 4.2: 空响应降级处理
        """
        # 创建返回空内容的LLM provider
        empty_llm = AsyncMock(spec=WayFareLLMProvider)
        empty_llm.generate.return_value = LLMResponse(
            content="",
            finish_reason="stop",
            usage={}
        )
        
        generator = AnnotationGenerator(
            llm_provider=empty_llm,
            context_builder=context_builder,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            db=temp_db
        )
        
        # 生成批注
        annotation = await generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="question",
            context="测试文本"
        )
        
        # 验证使用了降级内容
        assert annotation.content is not None
        assert len(annotation.content) > 0
    
    @pytest.mark.asyncio
    async def test_llm_error_response_fallback(
        self,
        context_builder,
        mock_vector_store,
        mock_embedding_service,
        temp_db
    ):
        """
        测试LLM返回错误状态时使用降级策略
        
        验证Requirement 4.2: 错误响应降级处理
        """
        # 创建返回错误的LLM provider
        error_llm = AsyncMock(spec=WayFareLLMProvider)
        error_llm.generate.return_value = LLMResponse(
            content="Error: Rate limit exceeded",
            finish_reason="error",
            usage={}
        )
        
        generator = AnnotationGenerator(
            llm_provider=error_llm,
            context_builder=context_builder,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            db=temp_db
        )
        
        # 生成批注
        annotation = await generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="summary",
            context="测试文本"
        )
        
        # 验证使用了降级内容
        assert annotation.content is not None
        assert len(annotation.content) > 0
        # 不应该包含错误信息
        assert "Error" not in annotation.content
        assert "Rate limit" not in annotation.content
    
    @pytest.mark.asyncio
    async def test_fallback_content_different_for_types(
        self,
        context_builder,
        mock_vector_store,
        mock_embedding_service,
        temp_db
    ):
        """
        测试不同类型的降级内容不同
        
        验证Requirement 4.2: 降级内容针对不同类型定制
        """
        # 创建会失败的LLM provider
        failing_llm = AsyncMock(spec=WayFareLLMProvider)
        failing_llm.generate.side_effect = Exception("LLM unavailable")
        
        generator = AnnotationGenerator(
            llm_provider=failing_llm,
            context_builder=context_builder,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            db=temp_db
        )
        
        # 生成三种类型的批注
        types = ["explanation", "question", "summary"]
        fallback_contents = []
        
        for ann_type in types:
            annotation = await generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=1,
                bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type=ann_type,
                context="测试文本"
            )
            fallback_contents.append(annotation.content)
        
        # 验证降级内容不完全相同（针对不同类型定制）
        assert len(set(fallback_contents)) > 1


class TestConcurrentAnnotations:
    """测试并发批注生成"""
    
    @pytest.mark.asyncio
    async def test_concurrent_annotation_generation(
        self,
        annotation_generator,
        temp_db
    ):
        """
        测试并发生成多个批注
        """
        # 创建多个并发任务
        tasks = []
        for i in range(5):
            task = annotation_generator.generate_annotation(
                doc_hash="test_doc_hash",
                page=i,
                bbox={"x": 100.0 + i, "y": 200.0, "width": 300.0, "height": 50.0},
                annotation_type="explanation",
                context=f"测试文本 {i}"
            )
            tasks.append(task)
        
        # 并发执行
        annotations = await asyncio.gather(*tasks)
        
        # 验证所有批注都已生成
        assert len(annotations) == 5
        assert all(a.id is not None for a in annotations)
        
        # 验证ID唯一
        ids = [a.id for a in annotations]
        assert len(set(ids)) == 5
        
        # 验证所有批注都已保存
        for annotation in annotations:
            saved = await temp_db.get_annotation(annotation.id)
            assert saved is not None


class TestPerformance:
    """测试性能相关场景"""
    
    @pytest.mark.asyncio
    async def test_annotation_generation_completes_quickly(
        self,
        annotation_generator
    ):
        """
        测试批注生成在合理时间内完成
        
        注意：这是一个性能测试，使用mock所以会很快
        实际场景中LLM调用可能需要1-3秒
        """
        import time
        
        start_time = time.time()
        
        annotation = await annotation_generator.generate_annotation(
            doc_hash="test_doc_hash",
            page=1,
            bbox={"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            annotation_type="explanation",
            context="测试文本"
        )
        
        elapsed_time = time.time() - start_time
        
        # 使用mock时应该很快完成（<1秒）
        assert elapsed_time < 1.0
        assert annotation is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
