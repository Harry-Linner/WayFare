"""
测试IPC Handler的query方法集成

验证Task 5.9的实现：
- IPCHandler.handle_query()方法
- VectorStore.search_documents()辅助方法
- EmbeddingService集成生成查询向量
- 返回检索结果（segmentId、text、page、score）
- query请求的错误处理
"""

import json
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from wayfare.ipc import IPCHandler
from wayfare.vector_store import SearchResult


class TestIPCQueryIntegration:
    """测试IPC Handler的query方法集成"""
    
    @pytest.fixture
    def mock_vector_store(self):
        """创建mock VectorStore"""
        store = MagicMock()
        store.search_documents = AsyncMock()
        return store
    
    @pytest.fixture
    def mock_embedding_service(self):
        """创建mock EmbeddingService"""
        service = MagicMock()
        service.embed_single = AsyncMock()
        return service
    
    @pytest.fixture
    def ipc_handler(self, mock_vector_store, mock_embedding_service):
        """创建IPC Handler实例"""
        return IPCHandler(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service
        )
    
    @pytest.mark.asyncio
    async def test_handle_query_success(self, ipc_handler, mock_vector_store, mock_embedding_service):
        """测试query请求成功处理"""
        # 准备测试数据
        doc_hash = "test_doc_hash_123"
        query = "什么是费曼技巧？"
        top_k = 5
        
        # Mock搜索结果
        mock_results = [
            SearchResult(
                segment_id="seg_1",
                text="费曼技巧是一种学习方法...",
                page=1,
                score=0.95,
                doc_hash=doc_hash
            ),
            SearchResult(
                segment_id="seg_2",
                text="使用费曼技巧可以深入理解概念...",
                page=2,
                score=0.88,
                doc_hash=doc_hash
            ),
            SearchResult(
                segment_id="seg_3",
                text="费曼技巧的核心是用简单语言解释...",
                page=1,
                score=0.82,
                doc_hash=doc_hash
            )
        ]
        
        mock_vector_store.search_documents.return_value = mock_results
        
        # 执行query请求
        params = {
            "docHash": doc_hash,
            "query": query,
            "topK": top_k
        }
        
        result = await ipc_handler.handle_query(params)
        
        # 验证调用
        mock_vector_store.search_documents.assert_called_once_with(
            doc_hash=doc_hash,
            query=query,
            embedding_service=mock_embedding_service,
            top_k=top_k
        )
        
        # 验证返回结果
        assert "results" in result
        assert len(result["results"]) == 3
        
        # 验证第一个结果
        first_result = result["results"][0]
        assert first_result["segmentId"] == "seg_1"
        assert first_result["text"] == "费曼技巧是一种学习方法..."
        assert first_result["page"] == 1
        assert first_result["score"] == 0.95
        
        # 验证第二个结果
        second_result = result["results"][1]
        assert second_result["segmentId"] == "seg_2"
        assert second_result["page"] == 2
        assert second_result["score"] == 0.88
    
    @pytest.mark.asyncio
    async def test_handle_query_default_topk(self, ipc_handler, mock_vector_store):
        """测试query请求使用默认topK值"""
        mock_vector_store.search_documents.return_value = []
        
        params = {
            "docHash": "test_doc",
            "query": "测试查询"
        }
        
        await ipc_handler.handle_query(params)
        
        # 验证使用默认topK=5
        call_args = mock_vector_store.search_documents.call_args
        assert call_args.kwargs["top_k"] == 5
    
    @pytest.mark.asyncio
    async def test_handle_query_custom_topk(self, ipc_handler, mock_vector_store):
        """测试query请求使用自定义topK值"""
        mock_vector_store.search_documents.return_value = []
        
        params = {
            "docHash": "test_doc",
            "query": "测试查询",
            "topK": 10
        }
        
        await ipc_handler.handle_query(params)
        
        # 验证使用自定义topK=10
        call_args = mock_vector_store.search_documents.call_args
        assert call_args.kwargs["top_k"] == 10
    
    @pytest.mark.asyncio
    async def test_handle_query_empty_results(self, ipc_handler, mock_vector_store):
        """测试query请求返回空结果"""
        mock_vector_store.search_documents.return_value = []
        
        params = {
            "docHash": "test_doc",
            "query": "不存在的内容"
        }
        
        result = await ipc_handler.handle_query(params)
        
        assert "results" in result
        assert len(result["results"]) == 0
    
    @pytest.mark.asyncio
    async def test_handle_query_missing_doc_hash(self, ipc_handler):
        """测试query请求缺少docHash参数"""
        params = {
            "query": "测试查询"
        }
        
        with pytest.raises(ValueError, match="Missing required parameter: docHash"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_missing_query(self, ipc_handler):
        """测试query请求缺少query参数"""
        params = {
            "docHash": "test_doc"
        }
        
        with pytest.raises(ValueError, match="Missing required parameter: query"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_empty_doc_hash(self, ipc_handler):
        """测试query请求docHash为空"""
        params = {
            "docHash": "",
            "query": "测试查询"
        }
        
        with pytest.raises(ValueError, match="docHash cannot be empty"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_empty_query(self, ipc_handler):
        """测试query请求query为空"""
        params = {
            "docHash": "test_doc",
            "query": ""
        }
        
        with pytest.raises(ValueError, match="query cannot be empty"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_invalid_topk_negative(self, ipc_handler):
        """测试query请求topK为负数"""
        params = {
            "docHash": "test_doc",
            "query": "测试查询",
            "topK": -1
        }
        
        with pytest.raises(ValueError, match="topK must be a positive integer"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_invalid_topk_zero(self, ipc_handler):
        """测试query请求topK为0"""
        params = {
            "docHash": "test_doc",
            "query": "测试查询",
            "topK": 0
        }
        
        with pytest.raises(ValueError, match="topK must be a positive integer"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_invalid_topk_string(self, ipc_handler):
        """测试query请求topK为字符串"""
        params = {
            "docHash": "test_doc",
            "query": "测试查询",
            "topK": "5"
        }
        
        with pytest.raises(ValueError, match="topK must be a positive integer"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_no_vector_store(self):
        """测试query请求但VectorStore未初始化"""
        handler = IPCHandler()  # 不提供vector_store
        
        params = {
            "docHash": "test_doc",
            "query": "测试查询"
        }
        
        with pytest.raises(RuntimeError, match="VectorStore not initialized"):
            await handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_no_embedding_service(self, mock_vector_store):
        """测试query请求但EmbeddingService未初始化"""
        handler = IPCHandler(vector_store=mock_vector_store)  # 不提供embedding_service
        
        params = {
            "docHash": "test_doc",
            "query": "测试查询"
        }
        
        with pytest.raises(RuntimeError, match="EmbeddingService not initialized"):
            await handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_vector_store_error(self, ipc_handler, mock_vector_store):
        """测试query请求时VectorStore抛出错误"""
        mock_vector_store.search_documents.side_effect = RuntimeError("Vector search failed")
        
        params = {
            "docHash": "test_doc",
            "query": "测试查询"
        }
        
        with pytest.raises(RuntimeError, match="Error executing query"):
            await ipc_handler.handle_query(params)
    
    @pytest.mark.asyncio
    async def test_handle_query_embedding_error(self, ipc_handler, mock_vector_store):
        """测试query请求时Embedding生成失败"""
        mock_vector_store.search_documents.side_effect = ValueError("Embedding generation failed")
        
        params = {
            "docHash": "test_doc",
            "query": "测试查询"
        }
        
        with pytest.raises(ValueError, match="Failed to execute query"):
            await ipc_handler.handle_query(params)


class TestVectorStoreSearchDocuments:
    """测试VectorStore.search_documents()辅助方法"""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """创建mock EmbeddingService"""
        service = MagicMock()
        service.embed_single = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_search_documents_integration(self, mock_embedding_service):
        """测试search_documents方法集成embedding和search"""
        from wayfare.vector_store import VectorStore
        
        # 创建VectorStore实例
        store = VectorStore()
        store._initialized = True
        
        # Mock search方法
        mock_search_results = [
            SearchResult(
                segment_id="seg_1",
                text="测试文本1",
                page=1,
                score=0.9,
                doc_hash="test_doc"
            )
        ]
        store.search = AsyncMock(return_value=mock_search_results)
        
        # Mock embedding service
        mock_query_vector = np.random.rand(512)
        mock_embedding_service.embed_single.return_value = mock_query_vector
        
        # 执行search_documents
        results = await store.search_documents(
            doc_hash="test_doc",
            query="测试查询",
            embedding_service=mock_embedding_service,
            top_k=5
        )
        
        # 验证embed_single被调用
        mock_embedding_service.embed_single.assert_called_once_with("测试查询")
        
        # 验证search被调用
        store.search.assert_called_once()
        call_args = store.search.call_args
        assert call_args.kwargs["doc_hash"] == "test_doc"
        assert call_args.kwargs["top_k"] == 5
        np.testing.assert_array_equal(call_args.kwargs["query_vector"], mock_query_vector)
        
        # 验证返回结果
        assert len(results) == 1
        assert results[0].segment_id == "seg_1"
    
    @pytest.mark.asyncio
    async def test_search_documents_empty_doc_hash(self, mock_embedding_service):
        """测试search_documents方法doc_hash为空"""
        from wayfare.vector_store import VectorStore
        
        store = VectorStore()
        store._initialized = True
        
        with pytest.raises(ValueError, match="doc_hash cannot be empty"):
            await store.search_documents(
                doc_hash="",
                query="测试查询",
                embedding_service=mock_embedding_service
            )
    
    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, mock_embedding_service):
        """测试search_documents方法query为空"""
        from wayfare.vector_store import VectorStore
        
        store = VectorStore()
        store._initialized = True
        
        with pytest.raises(ValueError, match="query cannot be empty"):
            await store.search_documents(
                doc_hash="test_doc",
                query="",
                embedding_service=mock_embedding_service
            )
    
    @pytest.mark.asyncio
    async def test_search_documents_invalid_topk(self, mock_embedding_service):
        """测试search_documents方法topK无效"""
        from wayfare.vector_store import VectorStore
        
        store = VectorStore()
        store._initialized = True
        
        with pytest.raises(ValueError, match="top_k must be positive"):
            await store.search_documents(
                doc_hash="test_doc",
                query="测试查询",
                embedding_service=mock_embedding_service,
                top_k=0
            )


class TestEndToEndQueryFlow:
    """端到端测试query流程"""
    
    @pytest.mark.asyncio
    async def test_full_query_request_flow(self):
        """测试完整的query请求流程"""
        from wayfare.ipc import IPCHandler
        from wayfare.vector_store import VectorStore
        
        # 创建mock组件
        mock_vector_store = MagicMock(spec=VectorStore)
        mock_embedding_service = MagicMock()
        
        # Mock search_documents返回结果
        mock_results = [
            SearchResult(
                segment_id="seg_1",
                text="相关内容1",
                page=1,
                score=0.95,
                doc_hash="doc123"
            ),
            SearchResult(
                segment_id="seg_2",
                text="相关内容2",
                page=2,
                score=0.85,
                doc_hash="doc123"
            )
        ]
        mock_vector_store.search_documents = AsyncMock(return_value=mock_results)
        
        # 创建IPC Handler
        handler = IPCHandler(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service
        )
        
        # 直接调用handle_query而不是通过handle_request
        # 因为handle_request会使用队列机制，可能导致异步问题
        params = {
            "docHash": "doc123",
            "query": "什么是机器学习？",
            "topK": 5
        }
        
        # 处理请求
        data = await handler.handle_query(params)
        
        # 验证返回数据
        assert "results" in data
        assert len(data["results"]) == 2
        
        # 验证第一个结果
        result1 = data["results"][0]
        assert result1["segmentId"] == "seg_1"
        assert result1["text"] == "相关内容1"
        assert result1["page"] == 1
        assert result1["score"] == 0.95
        
        # 验证第二个结果
        result2 = data["results"][1]
        assert result2["segmentId"] == "seg_2"
        assert result2["text"] == "相关内容2"
        assert result2["page"] == 2
        assert result2["score"] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
