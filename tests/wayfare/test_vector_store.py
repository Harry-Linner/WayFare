"""
Vector Store测试

测试向量存储服务的功能，包括初始化、向量存储、搜索和删除。
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from wayfare.vector_store import VectorStore, SearchResult


class TestVectorStore:
    """测试VectorStore类"""
    
    @pytest.fixture
    def store(self):
        """创建VectorStore实例"""
        return VectorStore(
            qdrant_url="http://localhost:6333",
            collection_name="test_documents"
        )
    
    def test_init(self, store):
        """测试初始化"""
        assert store.qdrant_url == "http://localhost:6333"
        assert store.collection_name == "test_documents"
        assert not store.is_initialized
        assert store.client is None
    
    def test_init_with_defaults(self):
        """测试使用默认参数初始化"""
        store = VectorStore()
        
        assert store.qdrant_url == "http://localhost:6333"
        assert store.collection_name == "documents"
        assert not store.is_initialized
    
    @patch('qdrant_client.QdrantClient')
    async def test_initialize_creates_collection(self, mock_qdrant_client):
        """测试初始化时创建collection"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        # 模拟collection不存在
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        # 验证
        assert store.is_initialized
        assert store.client == mock_client
        
        # 验证创建了collection
        mock_client.create_collection.assert_called_once()
        call_args = mock_client.create_collection.call_args
        assert call_args[1]["collection_name"] == "documents"
    
    @patch('qdrant_client.QdrantClient')
    async def test_initialize_existing_collection(self, mock_qdrant_client):
        """测试初始化时collection已存在"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        # 模拟collection已存在
        mock_collection = Mock()
        mock_collection.name = "documents"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        # 验证
        assert store.is_initialized
        
        # 验证没有创建collection
        mock_client.create_collection.assert_not_called()
    
    @patch('qdrant_client.QdrantClient')
    async def test_initialize_multiple_times(self, mock_qdrant_client):
        """测试多次初始化不会重复创建"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        
        # 多次初始化
        await store.initialize()
        await store.initialize()
        
        # 验证只创建了一次
        assert mock_qdrant_client.call_count == 1
    
    @patch('qdrant_client.QdrantClient')
    async def test_initialize_connection_error(self, mock_qdrant_client):
        """测试初始化时连接失败"""
        mock_qdrant_client.side_effect = Exception("Connection failed")
        
        store = VectorStore()
        
        with pytest.raises(ConnectionError, match="Failed to connect to Qdrant"):
            await store.initialize()
    
    async def test_upsert_vectors_not_initialized(self):
        """测试未初始化时插入向量"""
        store = VectorStore()
        
        with pytest.raises(RuntimeError, match="not initialized"):
            await store.upsert_vectors([{"id": "1", "vector": [0.1], "payload": {}}])
    
    @patch('qdrant_client.QdrantClient')
    async def test_upsert_vectors(self, mock_qdrant_client):
        """测试插入向量"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        # 准备测试数据
        vectors = [
            {
                "id": "seg_1",
                "vector": [0.1] * 512,
                "payload": {
                    "doc_hash": "abc123",
                    "page": 1,
                    "text": "示例文本1"
                }
            },
            {
                "id": "seg_2",
                "vector": [0.2] * 512,
                "payload": {
                    "doc_hash": "abc123",
                    "page": 2,
                    "text": "示例文本2"
                }
            }
        ]
        
        # 执行插入
        await store.upsert_vectors(vectors)
        
        # 验证调用
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args
        assert call_args[1]["collection_name"] == "documents"
        assert len(call_args[1]["points"]) == 2
    
    @patch('qdrant_client.QdrantClient')
    async def test_upsert_vectors_empty_list(self, mock_qdrant_client):
        """测试插入空向量列表"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        with pytest.raises(ValueError, match="vectors cannot be empty"):
            await store.upsert_vectors([])
    
    @patch('qdrant_client.QdrantClient')
    async def test_upsert_vectors_invalid_format(self, mock_qdrant_client):
        """测试插入格式不正确的向量"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        # 缺少必需字段
        invalid_vectors = [
            {"id": "1", "vector": [0.1]}  # 缺少payload
        ]
        
        with pytest.raises(ValueError, match="must contain 'id', 'vector', and 'payload'"):
            await store.upsert_vectors(invalid_vectors)
    
    async def test_search_not_initialized(self):
        """测试未初始化时搜索"""
        store = VectorStore()
        query_vector = np.random.randn(512)
        
        with pytest.raises(RuntimeError, match="not initialized"):
            await store.search(query_vector)
    
    @patch('qdrant_client.QdrantClient')
    async def test_search(self, mock_qdrant_client):
        """测试向量搜索"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        # 模拟搜索结果
        mock_hit1 = Mock()
        mock_hit1.id = "seg_1"
        mock_hit1.score = 0.95
        mock_hit1.payload = {
            "doc_hash": "abc123",
            "page": 1,
            "text": "相关文本1"
        }
        
        mock_hit2 = Mock()
        mock_hit2.id = "seg_2"
        mock_hit2.score = 0.85
        mock_hit2.payload = {
            "doc_hash": "abc123",
            "page": 2,
            "text": "相关文本2"
        }
        
        mock_client.search.return_value = [mock_hit1, mock_hit2]
        
        store = VectorStore()
        await store.initialize()
        
        # 执行搜索
        query_vector = np.random.randn(512)
        results = await store.search(query_vector, top_k=5)
        
        # 验证结果
        assert len(results) == 2
        assert results[0].segment_id == "seg_1"
        assert results[0].score == 0.95
        assert results[0].text == "相关文本1"
        assert results[0].page == 1
        assert results[0].doc_hash == "abc123"
        
        # 验证调用参数
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert call_args[1]["collection_name"] == "documents"
        assert call_args[1]["limit"] == 5
        assert call_args[1]["query_filter"] is None
    
    @patch('qdrant_client.QdrantClient')
    async def test_search_with_doc_hash_filter(self, mock_qdrant_client):
        """测试带doc_hash过滤的搜索"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        mock_client.search.return_value = []
        
        store = VectorStore()
        await store.initialize()
        
        # 执行搜索
        query_vector = np.random.randn(512)
        await store.search(query_vector, top_k=3, doc_hash="abc123")
        
        # 验证调用参数
        call_args = mock_client.search.call_args
        assert call_args[1]["query_filter"] is not None
    
    @patch('qdrant_client.QdrantClient')
    async def test_search_invalid_vector_shape(self, mock_qdrant_client):
        """测试搜索时向量维度不正确"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        # 错误的向量维度
        invalid_vector = np.random.randn(256)
        
        with pytest.raises(ValueError, match="must have shape \\(512,\\)"):
            await store.search(invalid_vector)
    
    @patch('qdrant_client.QdrantClient')
    async def test_search_invalid_top_k(self, mock_qdrant_client):
        """测试搜索时top_k无效"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        query_vector = np.random.randn(512)
        
        with pytest.raises(ValueError, match="top_k must be positive"):
            await store.search(query_vector, top_k=0)
        
        with pytest.raises(ValueError, match="top_k must be positive"):
            await store.search(query_vector, top_k=-1)
    
    async def test_delete_document_not_initialized(self):
        """测试未初始化时删除文档"""
        store = VectorStore()
        
        with pytest.raises(RuntimeError, match="not initialized"):
            await store.delete_document("abc123")
    
    @patch('qdrant_client.QdrantClient')
    async def test_delete_document(self, mock_qdrant_client):
        """测试删除文档向量"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        # 执行删除
        await store.delete_document("abc123")
        
        # 验证调用
        mock_client.delete.assert_called_once()
        call_args = mock_client.delete.call_args
        assert call_args[1]["collection_name"] == "documents"
    
    @patch('qdrant_client.QdrantClient')
    async def test_delete_document_empty_hash(self, mock_qdrant_client):
        """测试删除空doc_hash"""
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        store = VectorStore()
        await store.initialize()
        
        with pytest.raises(ValueError, match="doc_hash cannot be empty"):
            await store.delete_document("")
    
    @patch('qdrant_client.QdrantClient')
    async def test_search_result_dataclass(self, mock_qdrant_client):
        """测试SearchResult数据类"""
        result = SearchResult(
            segment_id="seg_1",
            text="示例文本",
            page=1,
            score=0.95,
            doc_hash="abc123"
        )
        
        assert result.segment_id == "seg_1"
        assert result.text == "示例文本"
        assert result.page == 1
        assert result.score == 0.95
        assert result.doc_hash == "abc123"
    
    @patch('qdrant_client.QdrantClient')
    async def test_search_handles_missing_payload_fields(self, mock_qdrant_client):
        """测试搜索时处理缺失的payload字段"""
        # 设置mock
        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        # 模拟payload缺少某些字段的搜索结果
        mock_hit = Mock()
        mock_hit.id = "seg_1"
        mock_hit.score = 0.95
        mock_hit.payload = {}  # 空payload
        
        mock_client.search.return_value = [mock_hit]
        
        store = VectorStore()
        await store.initialize()
        
        # 执行搜索
        query_vector = np.random.randn(512)
        results = await store.search(query_vector)
        
        # 验证使用了默认值
        assert len(results) == 1
        assert results[0].text == ""
        assert results[0].page == 0
        assert results[0].doc_hash == ""


class TestVectorStoreIntegration:
    """集成测试（需要实际的Qdrant服务）"""
    
    @pytest.mark.skip(reason="Requires running Qdrant instance")
    async def test_real_qdrant_operations(self):
        """测试真实Qdrant操作（需要运行Qdrant服务）"""
        store = VectorStore(
            qdrant_url="http://localhost:6333",
            collection_name="test_integration"
        )
        
        # 初始化
        await store.initialize()
        assert store.is_initialized
        
        # 插入向量
        vectors = [
            {
                "id": "test_1",
                "vector": np.random.randn(512).tolist(),
                "payload": {
                    "doc_hash": "test_doc",
                    "page": 1,
                    "text": "测试文本1"
                }
            },
            {
                "id": "test_2",
                "vector": np.random.randn(512).tolist(),
                "payload": {
                    "doc_hash": "test_doc",
                    "page": 2,
                    "text": "测试文本2"
                }
            }
        ]
        
        await store.upsert_vectors(vectors)
        
        # 搜索
        query_vector = np.random.randn(512)
        results = await store.search(query_vector, top_k=2)
        
        assert len(results) <= 2
        
        # 带过滤的搜索
        filtered_results = await store.search(
            query_vector,
            top_k=2,
            doc_hash="test_doc"
        )
        
        assert len(filtered_results) <= 2
        for r in filtered_results:
            assert r.doc_hash == "test_doc"
        
        # 删除文档
        await store.delete_document("test_doc")
        
        # 验证删除
        results_after_delete = await store.search(
            query_vector,
            top_k=2,
            doc_hash="test_doc"
        )
        
        assert len(results_after_delete) == 0
