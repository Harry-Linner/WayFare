"""
Annotation Generator模块

批注生成器核心逻辑，整合LLM Provider、Context Builder、Vector Store和Embedding Service。
实现RAG检索和批注生成的完整流程。
支持LLM调用失败时的降级策略。
"""

from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime, timezone
from loguru import logger

from wayfare.llm_provider import WayFareLLMProvider
from wayfare.context_builder import WayFareContextBuilder
from wayfare.vector_store import VectorStore
from wayfare.embedding import EmbeddingService
from wayfare.db import SQLiteDB, Annotation, BoundingBox
from wayfare.errors import get_fallback_annotation


class AnnotationGenerator:
    """
    批注生成器
    
    整合RAG检索和LLM生成，为用户选中的文本生成学习辅助批注。
    支持三种批注类型：explanation（解释）、question（提问）、summary（总结）。
    
    降级策略：
    - 当LLM调用失败时，自动使用预设的降级文本
    - 降级事件会被记录到日志中
    - 确保用户始终能获得批注响应
    
    Requirements:
    - 4.1: Use RAG to retrieve relevant context when generating annotations
    - 4.2: Call LLM to generate annotation content using Feynman technique and cognitive scaffolding templates
    - 4.2: Implement fallback mechanism when LLM calls fail
    """
    
    def __init__(
        self,
        llm_provider: WayFareLLMProvider,
        context_builder: WayFareContextBuilder,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        db: SQLiteDB
    ):
        """
        初始化批注生成器
        
        Args:
            llm_provider: LLM Provider实例
            context_builder: Context Builder实例
            vector_store: Vector Store实例
            embedding_service: Embedding Service实例
            db: SQLite数据库实例
        """
        self.llm = llm_provider
        self.context_builder = context_builder
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.db = db
        
        logger.info("Initialized Annotation Generator")
    
    async def generate_annotation(
        self,
        doc_hash: str,
        page: int,
        bbox: Dict[str, float],
        annotation_type: str,
        context: str
    ) -> Annotation:
        """
        生成批注（主方法）
        
        完整流程：
        1. RAG检索：查询向量生成 + top-5检索
        2. Prompt构建：选择模板 + 填充上下文
        3. LLM调用：生成批注内容（失败时使用降级策略）
        4. 响应处理：保存批注到数据库
        
        Args:
            doc_hash: 文档hash
            page: 页码
            bbox: 边界框字典，包含x、y、width、height
            annotation_type: 批注类型（explanation/question/summary）
            context: 用户选中的文本
            
        Returns:
            生成的批注对象
            
        Raises:
            ValueError: 如果参数无效或文档不存在
            
        Note:
            LLM调用失败时会自动使用降级策略，不会抛出异常
            
        Example:
            >>> annotation = await generator.generate_annotation(
            ...     doc_hash="abc123",
            ...     page=1,
            ...     bbox={"x": 100, "y": 200, "width": 300, "height": 50},
            ...     annotation_type="explanation",
            ...     context="费曼技巧是什么？"
            ... )
        """
        # 验证参数
        self._validate_params(doc_hash, annotation_type, context, bbox)
        
        logger.info(
            f"Generating {annotation_type} annotation for doc_hash={doc_hash}, "
            f"page={page}"
        )
        
        # 1. RAG检索相关上下文
        context_docs = await self._retrieve_context(doc_hash, context)
        
        # 2. 构建Prompt
        messages = self._build_prompt(context, annotation_type, context_docs)
        
        # 3. 调用LLM生成批注（带降级策略）
        annotation_content = await self._call_llm(messages, annotation_type)
        
        # 4. 获取文档版本hash
        version_hash = await self._get_version_hash(doc_hash)
        
        # 5. 创建批注对象
        annotation = self._create_annotation(
            doc_hash=doc_hash,
            version_hash=version_hash,
            annotation_type=annotation_type,
            content=annotation_content,
            bbox=bbox
        )
        
        # 6. 保存到数据库
        await self.db.save_annotation(annotation)
        
        logger.info(
            f"Successfully generated annotation {annotation.id} "
            f"for doc_hash={doc_hash}"
        )
        
        return annotation
    
    async def _retrieve_context(
        self,
        doc_hash: str,
        query_text: str,
        top_k: int = 5
    ) -> List[str]:
        """
        RAG检索逻辑：查询向量生成 + top-k检索
        
        Args:
            doc_hash: 文档hash
            query_text: 查询文本
            top_k: 返回top-k结果，默认5
            
        Returns:
            相关文档片段列表
        """
        logger.debug(f"Retrieving top-{top_k} context for query: {query_text[:50]}...")
        
        # 1. 生成查询向量
        query_vector = await self.embedding_service.embed_single(query_text)
        
        # 2. 向量相似度搜索（过滤指定文档）
        search_results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            doc_hash=doc_hash
        )
        
        # 3. 提取文本内容
        context_docs = [result.text for result in search_results]
        
        logger.debug(
            f"Retrieved {len(context_docs)} context documents "
            f"with scores: {[r.score for r in search_results]}"
        )
        
        return context_docs
    
    def _build_prompt(
        self,
        selected_text: str,
        annotation_type: str,
        context_docs: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Prompt构建逻辑：选择模板 + 填充上下文
        
        Args:
            selected_text: 用户选中的文本
            annotation_type: 批注类型
            context_docs: RAG检索到的上下文文档
            
        Returns:
            LLM消息列表
        """
        logger.debug(f"Building prompt for annotation type: {annotation_type}")
        
        # 使用Context Builder构建消息
        messages = self.context_builder.build_messages(
            selected_text=selected_text,
            annotation_type=annotation_type,
            context_docs=context_docs
        )
        
        return messages
    
    async def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        annotation_type: str
    ) -> str:
        """
        LLM调用和响应处理（带降级策略）
        
        Args:
            messages: LLM消息列表
            annotation_type: 批注类型（用于降级策略）
            
        Returns:
            生成的批注内容
            
        Note:
            当LLM调用失败时，自动使用降级策略返回预设文本
        """
        logger.debug("Calling LLM to generate annotation content")
        
        try:
            # 调用LLM生成
            response = await self.llm.generate(
                messages=messages,
                max_tokens=512,  # 批注内容较短，限制token数
                temperature=0.7  # 适中的创造性
            )
            
            # 检查响应
            if not response.content:
                logger.warning("LLM returned empty content, using fallback")
                return self._get_fallback_content(annotation_type)
            
            if response.finish_reason == "error":
                logger.warning(
                    f"LLM generation error: {response.content}, using fallback"
                )
                return self._get_fallback_content(annotation_type)
            
            logger.debug(
                f"LLM generation successful, content length: {len(response.content)}"
            )
            
            return response.content
            
        except Exception as e:
            # 捕获所有异常，使用降级策略
            logger.warning(
                f"LLM call failed with exception: {e}, using fallback strategy"
            )
            return self._get_fallback_content(annotation_type)
    
    async def _get_version_hash(self, doc_hash: str) -> str:
        """
        获取文档版本hash
        
        Args:
            doc_hash: 文档hash
            
        Returns:
            版本hash
            
        Raises:
            ValueError: 如果文档不存在
        """
        doc = await self.db.get_document(doc_hash)
        
        if not doc:
            raise ValueError(f"Document not found: {doc_hash}")
        
        return doc["version_hash"]
    
    def _create_annotation(
        self,
        doc_hash: str,
        version_hash: str,
        annotation_type: str,
        content: str,
        bbox: Dict[str, float]
    ) -> Annotation:
        """
        创建批注对象
        
        Args:
            doc_hash: 文档hash
            version_hash: 版本hash
            annotation_type: 批注类型
            content: 批注内容
            bbox: 边界框字典
            
        Returns:
            批注对象
        """
        return Annotation(
            id=str(uuid4()),
            doc_hash=doc_hash,
            version_hash=version_hash,
            type=annotation_type,
            content=content,
            bbox=BoundingBox(
                x=bbox["x"],
                y=bbox["y"],
                width=bbox["width"],
                height=bbox["height"]
            ),
            created_at=datetime.now(timezone.utc).isoformat()
        )
    
    def _validate_params(
        self,
        doc_hash: str,
        annotation_type: str,
        context: str,
        bbox: Dict[str, float]
    ):
        """
        验证参数有效性
        
        Args:
            doc_hash: 文档hash
            annotation_type: 批注类型
            context: 用户选中的文本
            bbox: 边界框字典
            
        Raises:
            ValueError: 如果参数无效
        """
        if not doc_hash:
            raise ValueError("doc_hash cannot be empty")
        
        if not context or not context.strip():
            raise ValueError("context cannot be empty")
        
        # 验证批注类型
        valid_types = self.context_builder.get_available_types()
        if annotation_type not in valid_types:
            raise ValueError(
                f"Invalid annotation_type: {annotation_type}. "
                f"Valid types: {valid_types}"
            )
        
        # 验证bbox
        required_keys = ["x", "y", "width", "height"]
        for key in required_keys:
            if key not in bbox:
                raise ValueError(f"bbox missing required key: {key}")
            
            if not isinstance(bbox[key], (int, float)):
                raise ValueError(f"bbox[{key}] must be a number")
    
    def _get_fallback_content(self, annotation_type: str) -> str:
        """
        获取降级批注内容
        
        当LLM调用失败时，返回预设的降级文本。
        同时记录降级事件到日志。
        
        Args:
            annotation_type: 批注类型（explanation/question/summary）
            
        Returns:
            降级批注内容
        """
        # 记录降级事件
        logger.warning(
            f"Using fallback content for annotation type: {annotation_type}"
        )
        
        # 获取预设的降级文本
        fallback_content = get_fallback_annotation(annotation_type)
        
        logger.info(
            f"Fallback annotation generated: {fallback_content[:50]}..."
        )
        
        return fallback_content


def create_annotation_generator(
    llm_provider: WayFareLLMProvider,
    context_builder: WayFareContextBuilder,
    vector_store: VectorStore,
    embedding_service: EmbeddingService,
    db: SQLiteDB
) -> AnnotationGenerator:
    """
    工厂函数：创建Annotation Generator实例
    
    Args:
        llm_provider: LLM Provider实例
        context_builder: Context Builder实例
        vector_store: Vector Store实例
        embedding_service: Embedding Service实例
        db: SQLite数据库实例
        
    Returns:
        AnnotationGenerator实例
    """
    return AnnotationGenerator(
        llm_provider=llm_provider,
        context_builder=context_builder,
        vector_store=vector_store,
        embedding_service=embedding_service,
        db=db
    )
