"""
Annotation Generator单元测试

测试批注生成器的核心功能：
- RAG检索逻辑
- Prompt构建
- LLM调用
- 批注保存
- 错误处理
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from wayfare.annotation_generator import AnnotationGenerator, create_annotation_generator
from wayfare.db import Annotation, BoundingBox
from wayfare.vector_store import SearchResult
from nanobot.providers.base import LLMResponse


@pytest.fixture
def mock_llm_provider():
    """Mock LLM Provider"""
    provider = AsyncMock()
    provider.generate = AsyncMock(return_value=LLMResponse(
        content="这是一个测试批注内容",
        finish_reason="stop"
    ))
    return provider


@pytest.fixture
def mock_context_builder():
    """Mock Context Builder"""
    builder = MagicMock()
    builder.build_messages = MagicMock(return_value=[
        {"role": "system", "content": "系统提示词"},
        {"role": "user", "content": "用户消息"}
    ])
    builder.get_available_types = MagicMock(return_value=[
        "explanation", "question", "summary"
    ])
    return builder


@pytest.fixture
def mock_vector_store():
    """Mock Vector Store"""
    store = AsyncMock()
    store.search = AsyncMock(return_value=[
        SearchResult(
            segment_id="seg_1",
            text="相关片段1",
            page=1,
            score=0.9,
            doc_hash="test_hash"
        ),
        SearchResult(
            segment_id="seg_2",
            text="相关片段2",
            page=1,
            score=0.8,
            doc_hash="test_hash"
        )
    ])
    return store


@pytest.fixture
def mock_embedding_service():
    """Mock Embedding Service"""
    service = AsyncMock()
    service.embed_single = AsyncMock(return_value=np.random.rand(512))
    return service


@pytest.fixture
def mock_db():
    """Mock SQLite DB"""
    db = AsyncMock()
    db.get_document = AsyncMock(return_value={
        "hash": "test_hash",
        "version_hash": "v1",
        "path": "/test/doc.pdf",
        "status": "completed"
    })
    db.save_annotation = AsyncMock()
    return db


@pytest.fixture
def annotation_generator(
    mock_llm_provider,
    mock_context_builder,
    mock_vector_store,
    mock_embedding_service,
    mock_db
):
    """创建Annotation Generator实例"""
    return AnnotationGenerator(
        llm_provider=mock_llm_provider,
        context_builder=mock_context_builder,
        vector_store=mock_vector_store,
        embedding_service=mock_embedding_service,
        db=mock_db
    )


class TestAnnotationGenerator:
    """Annotation Generator核心功能测试"""
    
    @pytest.mark.asyncio
    async def test_generate_annotation_success(self, annotation_generator):
        """测试成功生成批注"""
        # Arrange
        doc_hash = "test_hash"
        page = 1
        bbox = {"x": 100, "y": 200, "width": 300, "height": 50}
        annotation_type = "explanation"
        context = "什么是费曼技巧？"
        
        # Act
        annotation = await annotation_generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type=annotation_type,
            context=context
        )
        
        # Assert
        assert annotation is not None
        assert annotation.doc_hash == doc_hash
        assert annotation.version_hash == "v1"
        assert annotation.type == annotation_type
        assert annotation.content == "这是一个测试批注内容"
        assert annotation.bbox.x == 100
        assert annotation.bbox.y == 200
        assert annotation.bbox.width == 300
        assert annotation.bbox.height == 50
        
        # 验证调用链
        annotation_generator.embedding_service.embed_single.assert_called_once_with(context)
        annotation_generator.vector_store.search.assert_called_once()
        annotation_generator.context_builder.build_messages.assert_called_once()
        annotation_generator.llm.generate.assert_called_once()
        annotation_generator.db.save_annotation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_retrieval_logic(self, annotation_generator):
        """测试RAG检索逻辑"""
        # Arrange
        doc_hash = "test_hash"
        query_text = "测试查询"
        
        # Act
        context_docs = await annotation_generator._retrieve_context(
            doc_hash=doc_hash,
            query_text=query_text,
            top_k=5
        )
        
        # Assert
        assert len(context_docs) == 2
        assert context_docs[0] == "相关片段1"
        assert context_docs[1] == "相关片段2"
        
        # 验证向量生成
        annotation_generator.embedding_service.embed_single.assert_called_once_with(query_text)
        
        # 验证向量搜索
        call_args = annotation_generator.vector_store.search.call_args
        assert call_args.kwargs["top_k"] == 5
        assert call_args.kwargs["doc_hash"] == doc_hash
    
    @pytest.mark.asyncio
    async def test_prompt_building(self, annotation_generator):
        """测试Prompt构建逻辑"""
        # Arrange
        selected_text = "费曼技巧"
        annotation_type = "explanation"
        context_docs = ["片段1", "片段2"]
        
        # Act
        messages = annotation_generator._build_prompt(
            selected_text=selected_text,
            annotation_type=annotation_type,
            context_docs=context_docs
        )
        
        # Assert
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        
        # 验证Context Builder调用
        annotation_generator.context_builder.build_messages.assert_called_once_with(
            selected_text=selected_text,
            annotation_type=annotation_type,
            context_docs=context_docs
        )
    
    @pytest.mark.asyncio
    async def test_llm_call_success(self, annotation_generator):
        """测试LLM调用成功"""
        # Arrange
        messages = [
            {"role": "system", "content": "系统提示词"},
            {"role": "user", "content": "用户消息"}
        ]
        annotation_type = "explanation"
        
        # Act
        content = await annotation_generator._call_llm(messages, annotation_type)
        
        # Assert
        assert content == "这是一个测试批注内容"
        
        # 验证LLM调用参数
        call_args = annotation_generator.llm.generate.call_args
        assert call_args.kwargs["messages"] == messages
        assert call_args.kwargs["max_tokens"] == 512
        assert call_args.kwargs["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_llm_call_empty_content_fallback(self, annotation_generator):
        """测试LLM返回空内容时使用降级策略"""
        # Arrange
        annotation_generator.llm.generate = AsyncMock(return_value=LLMResponse(
            content="",
            finish_reason="stop"
        ))
        messages = [{"role": "user", "content": "test"}]
        annotation_type = "explanation"
        
        # Act
        content = await annotation_generator._call_llm(messages, annotation_type)
        
        # Assert - 应该返回降级文本
        assert content == "AI助手暂时不可用，请稍后重试。"
    
    @pytest.mark.asyncio
    async def test_llm_call_error_response_fallback(self, annotation_generator):
        """测试LLM返回错误时使用降级策略"""
        # Arrange
        annotation_generator.llm.generate = AsyncMock(return_value=LLMResponse(
            content="Error message",
            finish_reason="error"
        ))
        messages = [{"role": "user", "content": "test"}]
        annotation_type = "question"
        
        # Act
        content = await annotation_generator._call_llm(messages, annotation_type)
        
        # Assert - 应该返回降级文本
        assert content == "思考一下：这段内容的核心概念是什么？"
    
    @pytest.mark.asyncio
    async def test_llm_call_exception_fallback(self, annotation_generator):
        """测试LLM调用异常时使用降级策略"""
        # Arrange
        annotation_generator.llm.generate = AsyncMock(
            side_effect=Exception("Network error")
        )
        messages = [{"role": "user", "content": "test"}]
        annotation_type = "summary"
        
        # Act
        content = await annotation_generator._call_llm(messages, annotation_type)
        
        # Assert - 应该返回降级文本
        assert content == "请尝试用自己的话总结这段内容。"
    
    @pytest.mark.asyncio
    async def test_get_version_hash_success(self, annotation_generator):
        """测试获取版本hash成功"""
        # Arrange
        doc_hash = "test_hash"
        
        # Act
        version_hash = await annotation_generator._get_version_hash(doc_hash)
        
        # Assert
        assert version_hash == "v1"
        annotation_generator.db.get_document.assert_called_once_with(doc_hash)
    
    @pytest.mark.asyncio
    async def test_get_version_hash_document_not_found(self, annotation_generator):
        """测试文档不存在"""
        # Arrange
        annotation_generator.db.get_document = AsyncMock(return_value=None)
        doc_hash = "nonexistent"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Document not found"):
            await annotation_generator._get_version_hash(doc_hash)
    
    def test_create_annotation(self, annotation_generator):
        """测试创建批注对象"""
        # Arrange
        doc_hash = "test_hash"
        version_hash = "v1"
        annotation_type = "explanation"
        content = "测试内容"
        bbox = {"x": 10, "y": 20, "width": 100, "height": 50}
        
        # Act
        annotation = annotation_generator._create_annotation(
            doc_hash=doc_hash,
            version_hash=version_hash,
            annotation_type=annotation_type,
            content=content,
            bbox=bbox
        )
        
        # Assert
        assert annotation.doc_hash == doc_hash
        assert annotation.version_hash == version_hash
        assert annotation.type == annotation_type
        assert annotation.content == content
        assert annotation.bbox.x == 10
        assert annotation.bbox.y == 20
        assert annotation.bbox.width == 100
        assert annotation.bbox.height == 50
        assert annotation.id is not None
        assert annotation.created_at is not None
    
    def test_validate_params_success(self, annotation_generator):
        """测试参数验证成功"""
        # Arrange
        doc_hash = "test_hash"
        annotation_type = "explanation"
        context = "测试文本"
        bbox = {"x": 0, "y": 0, "width": 100, "height": 50}
        
        # Act & Assert (不应抛出异常)
        annotation_generator._validate_params(doc_hash, annotation_type, context, bbox)
    
    def test_validate_params_empty_doc_hash(self, annotation_generator):
        """测试空doc_hash"""
        with pytest.raises(ValueError, match="doc_hash cannot be empty"):
            annotation_generator._validate_params("", "explanation", "text", {})
    
    def test_validate_params_empty_context(self, annotation_generator):
        """测试空context"""
        with pytest.raises(ValueError, match="context cannot be empty"):
            annotation_generator._validate_params("hash", "explanation", "", {})
    
    def test_validate_params_invalid_type(self, annotation_generator):
        """测试无效的批注类型"""
        with pytest.raises(ValueError, match="Invalid annotation_type"):
            annotation_generator._validate_params(
                "hash", "invalid_type", "text",
                {"x": 0, "y": 0, "width": 100, "height": 50}
            )
    
    def test_validate_params_missing_bbox_key(self, annotation_generator):
        """测试bbox缺少必需字段"""
        with pytest.raises(ValueError, match="bbox missing required key"):
            annotation_generator._validate_params(
                "hash", "explanation", "text",
                {"x": 0, "y": 0}  # 缺少width和height
            )
    
    def test_validate_params_invalid_bbox_value(self, annotation_generator):
        """测试bbox值类型错误"""
        with pytest.raises(ValueError, match="must be a number"):
            annotation_generator._validate_params(
                "hash", "explanation", "text",
                {"x": "invalid", "y": 0, "width": 100, "height": 50}
            )
    
    def test_get_fallback_content_explanation(self, annotation_generator):
        """测试获取explanation类型的降级内容"""
        # Act
        content = annotation_generator._get_fallback_content("explanation")
        
        # Assert
        assert content == "AI助手暂时不可用，请稍后重试。"
    
    def test_get_fallback_content_question(self, annotation_generator):
        """测试获取question类型的降级内容"""
        # Act
        content = annotation_generator._get_fallback_content("question")
        
        # Assert
        assert content == "思考一下：这段内容的核心概念是什么？"
    
    def test_get_fallback_content_summary(self, annotation_generator):
        """测试获取summary类型的降级内容"""
        # Act
        content = annotation_generator._get_fallback_content("summary")
        
        # Assert
        assert content == "请尝试用自己的话总结这段内容。"
    
    def test_get_fallback_content_unknown_type(self, annotation_generator):
        """测试获取未知类型的降级内容"""
        # Act
        content = annotation_generator._get_fallback_content("unknown_type")
        
        # Assert
        assert content == "AI助手暂时不可用。"
    
    @pytest.mark.asyncio
    async def test_generate_annotation_all_types(self, annotation_generator):
        """测试生成所有类型的批注"""
        # Arrange
        doc_hash = "test_hash"
        page = 1
        bbox = {"x": 0, "y": 0, "width": 100, "height": 50}
        context = "测试文本"
        
        types = ["explanation", "question", "summary"]
        
        # Act & Assert
        for annotation_type in types:
            annotation = await annotation_generator.generate_annotation(
                doc_hash=doc_hash,
                page=page,
                bbox=bbox,
                annotation_type=annotation_type,
                context=context
            )
            
            assert annotation.type == annotation_type
            assert annotation.content is not None
    
    @pytest.mark.asyncio
    async def test_generate_annotation_with_no_context_docs(self, annotation_generator):
        """测试没有检索到上下文文档的情况"""
        # Arrange
        annotation_generator.vector_store.search = AsyncMock(return_value=[])
        
        doc_hash = "test_hash"
        page = 1
        bbox = {"x": 0, "y": 0, "width": 100, "height": 50}
        annotation_type = "explanation"
        context = "测试文本"
        
        # Act
        annotation = await annotation_generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type=annotation_type,
            context=context
        )
        
        # Assert - 应该仍然能生成批注，只是没有上下文
        assert annotation is not None
        assert annotation.content == "这是一个测试批注内容"


class TestAnnotationGeneratorFactory:
    """测试工厂函数"""
    
    def test_create_annotation_generator(
        self,
        mock_llm_provider,
        mock_context_builder,
        mock_vector_store,
        mock_embedding_service,
        mock_db
    ):
        """测试工厂函数创建实例"""
        # Act
        generator = create_annotation_generator(
            llm_provider=mock_llm_provider,
            context_builder=mock_context_builder,
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            db=mock_db
        )
        
        # Assert
        assert isinstance(generator, AnnotationGenerator)
        assert generator.llm == mock_llm_provider
        assert generator.context_builder == mock_context_builder
        assert generator.vector_store == mock_vector_store
        assert generator.embedding_service == mock_embedding_service
        assert generator.db == mock_db


class TestAnnotationGeneratorIntegration:
    """集成测试（测试组件间交互）"""
    
    @pytest.mark.asyncio
    async def test_full_annotation_generation_flow(self, annotation_generator):
        """测试完整的批注生成流程"""
        # Arrange
        doc_hash = "test_hash"
        page = 1
        bbox = {"x": 100, "y": 200, "width": 300, "height": 50}
        annotation_type = "explanation"
        context = "什么是费曼技巧？"
        
        # Act
        annotation = await annotation_generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type=annotation_type,
            context=context
        )
        
        # Assert - 验证完整流程
        # 1. 向量生成
        annotation_generator.embedding_service.embed_single.assert_called_once()
        
        # 2. RAG检索
        annotation_generator.vector_store.search.assert_called_once()
        search_call = annotation_generator.vector_store.search.call_args
        assert search_call.kwargs["doc_hash"] == doc_hash
        assert search_call.kwargs["top_k"] == 5
        
        # 3. Prompt构建
        annotation_generator.context_builder.build_messages.assert_called_once()
        build_call = annotation_generator.context_builder.build_messages.call_args
        assert build_call.kwargs["selected_text"] == context
        assert build_call.kwargs["annotation_type"] == annotation_type
        assert len(build_call.kwargs["context_docs"]) == 2
        
        # 4. LLM调用
        annotation_generator.llm.generate.assert_called_once()
        llm_call = annotation_generator.llm.generate.call_args
        assert llm_call.kwargs["max_tokens"] == 512
        assert llm_call.kwargs["temperature"] == 0.7
        
        # 5. 数据库保存
        annotation_generator.db.save_annotation.assert_called_once()
        save_call = annotation_generator.db.save_annotation.call_args
        saved_annotation = save_call.args[0]
        assert saved_annotation.doc_hash == doc_hash
        assert saved_annotation.type == annotation_type
        
        # 6. 返回结果验证
        assert annotation.id is not None
        assert annotation.content == "这是一个测试批注内容"
    
    @pytest.mark.asyncio
    async def test_annotation_generation_with_llm_failure(self, annotation_generator):
        """测试LLM失败时的完整流程（使用降级策略）"""
        # Arrange
        annotation_generator.llm.generate = AsyncMock(
            side_effect=Exception("LLM service unavailable")
        )
        
        doc_hash = "test_hash"
        page = 1
        bbox = {"x": 100, "y": 200, "width": 300, "height": 50}
        annotation_type = "explanation"
        context = "什么是费曼技巧？"
        
        # Act
        annotation = await annotation_generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type=annotation_type,
            context=context
        )
        
        # Assert - 应该成功生成批注，使用降级内容
        assert annotation is not None
        assert annotation.content == "AI助手暂时不可用，请稍后重试。"
        assert annotation.doc_hash == doc_hash
        assert annotation.type == annotation_type
        
        # 验证仍然执行了RAG检索
        annotation_generator.embedding_service.embed_single.assert_called_once()
        annotation_generator.vector_store.search.assert_called_once()
        
        # 验证保存到数据库
        annotation_generator.db.save_annotation.assert_called_once()
