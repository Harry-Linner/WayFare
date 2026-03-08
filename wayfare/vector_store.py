"""
Vector Store模块

封装Qdrant客户端，提供向量存储和相似度搜索功能。
支持批量向量存储、按doc_hash过滤搜索和文档删除。
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    向量搜索结果
    
    Attributes:
        segment_id: 片段ID
        text: 片段文本
        page: 页码
        score: 相似度分数
        doc_hash: 文档hash
    """
    segment_id: str
    text: str
    page: int
    score: float
    doc_hash: str


class VectorStore:
    """
    向量存储服务
    
    封装Qdrant客户端操作，提供向量存储、搜索和删除功能。
    支持按文档hash过滤搜索结果。
    
    Requirements:
    - 3.3: Store vector data in Qdrant vector database
    - 3.4: Execute vector similarity search and return top-k relevant segments
    - 3.5: Support filtering search results by document hash
    """
    
    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "documents"):
        """
        初始化Vector Store
        
        Args:
            qdrant_url: Qdrant服务地址
            collection_name: Collection名称
            
        Note:
            实际的Qdrant客户端在initialize()时创建
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.client: Optional[object] = None
        self._initialized = False
    
    async def initialize(self):
        """
        初始化Qdrant collection
        
        创建Qdrant客户端并确保collection存在。
        如果collection不存在，则创建一个新的collection。
        
        Raises:
            ImportError: 如果缺少qdrant-client依赖
            ConnectionError: 如果无法连接到Qdrant服务
        """
        if self._initialized:
            return
        
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as e:
            raise ImportError(
                "Missing required dependency. Please install: "
                "pip install qdrant-client"
            ) from e
        
        logger.info(f"Connecting to Qdrant at {self.qdrant_url}")
        
        try:
            # 创建Qdrant客户端
            self.client = QdrantClient(url=self.qdrant_url)
            
            # 检查collection是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                
                # 创建collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=512,  # bge-small-zh-v1.5的向量维度
                        distance=Distance.COSINE
                    )
                )
                
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise ConnectionError(f"Failed to connect to Qdrant at {self.qdrant_url}: {e}") from e
    
    async def upsert_vectors(self, vectors: List[Dict[str, Any]]):
        """
        批量插入或更新向量
        
        Args:
            vectors: 向量列表，每个元素包含:
                - id: 片段ID (str)
                - vector: 向量数组 (list of float)
                - payload: 元数据字典，包含doc_hash、page、text等
        
        Raises:
            RuntimeError: 如果未初始化或插入失败
            ValueError: 如果vectors为空或格式不正确
            
        Example:
            >>> await store.upsert_vectors([
            ...     {
            ...         "id": "seg_1",
            ...         "vector": [0.1, 0.2, ...],
            ...         "payload": {
            ...             "doc_hash": "abc123",
            ...             "page": 1,
            ...             "text": "示例文本"
            ...         }
            ...     }
            ... ])
        """
        if not self._initialized:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")
        
        if not vectors:
            raise ValueError("vectors cannot be empty")
        
        # 验证向量格式
        for v in vectors:
            if "id" not in v or "vector" not in v or "payload" not in v:
                raise ValueError("Each vector must contain 'id', 'vector', and 'payload'")
        
        try:
            from qdrant_client.models import PointStruct
            
            logger.debug(f"Upserting {len(vectors)} vectors to collection {self.collection_name}")
            
            # 转换为PointStruct
            points = [
                PointStruct(
                    id=v["id"],
                    vector=v["vector"],
                    payload=v["payload"]
                )
                for v in vectors
            ]
            
            # 批量插入
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.debug(f"Successfully upserted {len(vectors)} vectors")
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise RuntimeError(f"Failed to upsert vectors: {e}") from e
    
    async def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        doc_hash: Optional[str] = None
    ) -> List[SearchResult]:
        """
        向量相似度搜索
        
        Args:
            query_vector: 查询向量，shape为(512,)
            top_k: 返回top-k结果，默认5
            doc_hash: 可选的文档hash过滤，只返回该文档的结果
            
        Returns:
            搜索结果列表，按相似度分数降序排列
            
        Raises:
            RuntimeError: 如果未初始化或搜索失败
            ValueError: 如果query_vector格式不正确或top_k无效
            
        Example:
            >>> results = await store.search(
            ...     query_vector=np.array([0.1, 0.2, ...]),
            ...     top_k=5,
            ...     doc_hash="abc123"
            ... )
            >>> for r in results:
            ...     print(f"{r.text} (score: {r.score})")
        """
        if not self._initialized:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")
        
        if query_vector.shape != (512,):
            raise ValueError(f"query_vector must have shape (512,), got {query_vector.shape}")
        
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            logger.debug(f"Searching for top-{top_k} results" + 
                        (f" in doc_hash={doc_hash}" if doc_hash else ""))
            
            # 构建过滤条件
            query_filter = None
            if doc_hash:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="doc_hash",
                            match=MatchValue(value=doc_hash)
                        )
                    ]
                )
            
            # 执行搜索
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=query_filter
            )
            
            # 转换结果
            results = []
            for hit in search_results:
                results.append(SearchResult(
                    segment_id=str(hit.id),
                    text=hit.payload.get("text", ""),
                    page=hit.payload.get("page", 0),
                    score=hit.score,
                    doc_hash=hit.payload.get("doc_hash", "")
                ))
            
            logger.debug(f"Found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise RuntimeError(f"Failed to search vectors: {e}") from e
    
    async def delete_document(self, doc_hash: str):
        """
        删除文档的所有向量
        
        Args:
            doc_hash: 文档hash
            
        Raises:
            RuntimeError: 如果未初始化或删除失败
            ValueError: 如果doc_hash为空
            
        Example:
            >>> await store.delete_document("abc123")
        """
        if not self._initialized:
            raise RuntimeError("VectorStore not initialized. Call initialize() first.")
        
        if not doc_hash:
            raise ValueError("doc_hash cannot be empty")
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector
            
            logger.info(f"Deleting all vectors for doc_hash={doc_hash}")
            
            # 删除所有匹配的向量
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="doc_hash",
                                match=MatchValue(value=doc_hash)
                            )
                        ]
                    )
                )
            )
            
            logger.info(f"Successfully deleted vectors for doc_hash={doc_hash}")
            
        except Exception as e:
            logger.error(f"Failed to delete document vectors: {e}")
            raise RuntimeError(f"Failed to delete document vectors: {e}") from e
    async def search_documents(
        self,
        doc_hash: str,
        query: str,
        embedding_service,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        在指定文档中搜索相关片段

        这是一个辅助方法，集成了embedding生成和向量搜索。

        Args:
            doc_hash: 文档hash，用于过滤搜索结果
            query: 查询文本
            embedding_service: EmbeddingService实例，用于生成查询向量
            top_k: 返回top-k结果，默认5

        Returns:
            搜索结果列表，按相似度分数降序排列

        Raises:
            RuntimeError: 如果未初始化或搜索失败
            ValueError: 如果参数无效

        Example:
            >>> results = await store.search_documents(
            ...     doc_hash="abc123",
            ...     query="什么是费曼技巧？",
            ...     embedding_service=embed_service,
            ...     top_k=5
            ... )
            >>> for r in results:
            ...     print(f"{r.text} (score: {r.score})")
        """
        if not doc_hash:
            raise ValueError("doc_hash cannot be empty")

        if not query or not query.strip():
            raise ValueError("query cannot be empty")

        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

        logger.debug(f"Searching documents with query='{query}', doc_hash={doc_hash}, top_k={top_k}")

        try:
            # 1. 生成查询向量
            query_vector = await embedding_service.embed_single(query)

            # 2. 执行向量搜索
            results = await self.search(
                query_vector=query_vector,
                top_k=top_k,
                doc_hash=doc_hash
            )

            logger.debug(f"Found {len(results)} results for query")

            return results

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise RuntimeError(f"Failed to search documents: {e}") from e

    
    @property
    def is_initialized(self) -> bool:
        """
        检查服务是否已初始化
        
        Returns:
            True如果已初始化，否则False
        """
        return self._initialized
