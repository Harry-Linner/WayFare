"""
批注生成降级策略示例

演示当LLM服务不可用时，批注生成器如何使用降级策略。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import numpy as np

from wayfare.annotation_generator import create_annotation_generator
from wayfare.llm_provider import WayFareLLMProvider
from wayfare.context_builder import WayFareContextBuilder
from wayfare.vector_store import VectorStore, SearchResult
from wayfare.embedding import EmbeddingService
from wayfare.db import SQLiteDB
from nanobot.providers.base import LLMResponse


async def example_normal_generation():
    """示例1: 正常的批注生成（LLM成功）"""
    print("=" * 60)
    print("示例1: 正常的批注生成")
    print("=" * 60)
    
    # 创建mock组件
    llm_provider = AsyncMock()
    llm_provider.generate = AsyncMock(return_value=LLMResponse(
        content="费曼技巧是一种学习方法，通过用简单的语言解释复杂概念来检验理解程度。",
        finish_reason="stop"
    ))
    
    context_builder = WayFareContextBuilder()
    
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[
        SearchResult(
            segment_id="seg_1",
            text="费曼技巧强调用自己的话解释概念",
            page=1,
            score=0.9,
            doc_hash="test_hash"
        )
    ])
    
    embedding_service = AsyncMock()
    embedding_service.embed_single = AsyncMock(return_value=np.random.rand(512))
    
    db = AsyncMock()
    db.get_document = AsyncMock(return_value={
        "hash": "test_hash",
        "version_hash": "v1",
        "path": "/test/doc.pdf",
        "status": "completed"
    })
    db.save_annotation = AsyncMock()
    
    # 创建批注生成器
    generator = create_annotation_generator(
        llm_provider=llm_provider,
        context_builder=context_builder,
        vector_store=vector_store,
        embedding_service=embedding_service,
        db=db
    )
    
    # 生成批注
    annotation = await generator.generate_annotation(
        doc_hash="test_hash",
        page=1,
        bbox={"x": 100, "y": 200, "width": 300, "height": 50},
        annotation_type="explanation",
        context="什么是费曼技巧？"
    )
    
    print(f"✅ 批注生成成功")
    print(f"   批注ID: {annotation.id}")
    print(f"   批注类型: {annotation.type}")
    print(f"   批注内容: {annotation.content}")
    print()


async def example_llm_failure_fallback():
    """示例2: LLM失败时的降级策略"""
    print("=" * 60)
    print("示例2: LLM失败时的降级策略")
    print("=" * 60)
    
    # 创建mock组件
    llm_provider = AsyncMock()
    # 模拟LLM服务不可用
    llm_provider.generate = AsyncMock(
        side_effect=Exception("Network timeout: Unable to connect to LLM service")
    )
    
    context_builder = WayFareContextBuilder()
    
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[
        SearchResult(
            segment_id="seg_1",
            text="费曼技巧强调用自己的话解释概念",
            page=1,
            score=0.9,
            doc_hash="test_hash"
        )
    ])
    
    embedding_service = AsyncMock()
    embedding_service.embed_single = AsyncMock(return_value=np.random.rand(512))
    
    db = AsyncMock()
    db.get_document = AsyncMock(return_value={
        "hash": "test_hash",
        "version_hash": "v1",
        "path": "/test/doc.pdf",
        "status": "completed"
    })
    db.save_annotation = AsyncMock()
    
    # 创建批注生成器
    generator = create_annotation_generator(
        llm_provider=llm_provider,
        context_builder=context_builder,
        vector_store=vector_store,
        embedding_service=embedding_service,
        db=db
    )
    
    # 生成批注（LLM失败，使用降级策略）
    annotation = await generator.generate_annotation(
        doc_hash="test_hash",
        page=1,
        bbox={"x": 100, "y": 200, "width": 300, "height": 50},
        annotation_type="explanation",
        context="什么是费曼技巧？"
    )
    
    print(f"⚠️  LLM服务不可用，使用降级策略")
    print(f"   批注ID: {annotation.id}")
    print(f"   批注类型: {annotation.type}")
    print(f"   批注内容: {annotation.content}")
    print(f"   说明: 批注仍然成功保存，用户获得友好的降级文本")
    print()


async def example_all_annotation_types_fallback():
    """示例3: 不同批注类型的降级文本"""
    print("=" * 60)
    print("示例3: 不同批注类型的降级文本")
    print("=" * 60)
    
    # 创建mock组件
    llm_provider = AsyncMock()
    llm_provider.generate = AsyncMock(return_value=LLMResponse(
        content="",  # 空响应，触发降级
        finish_reason="stop"
    ))
    
    context_builder = WayFareContextBuilder()
    
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[])
    
    embedding_service = AsyncMock()
    embedding_service.embed_single = AsyncMock(return_value=np.random.rand(512))
    
    db = AsyncMock()
    db.get_document = AsyncMock(return_value={
        "hash": "test_hash",
        "version_hash": "v1",
        "path": "/test/doc.pdf",
        "status": "completed"
    })
    db.save_annotation = AsyncMock()
    
    # 创建批注生成器
    generator = create_annotation_generator(
        llm_provider=llm_provider,
        context_builder=context_builder,
        vector_store=vector_store,
        embedding_service=embedding_service,
        db=db
    )
    
    # 测试三种批注类型的降级文本
    annotation_types = ["explanation", "question", "summary"]
    
    for annotation_type in annotation_types:
        annotation = await generator.generate_annotation(
            doc_hash="test_hash",
            page=1,
            bbox={"x": 100, "y": 200, "width": 300, "height": 50},
            annotation_type=annotation_type,
            context="测试文本"
        )
        
        print(f"📝 {annotation_type}类型的降级文本:")
        print(f"   {annotation.content}")
        print()


async def example_error_response_fallback():
    """示例4: LLM返回错误响应时的降级"""
    print("=" * 60)
    print("示例4: LLM返回错误响应时的降级")
    print("=" * 60)
    
    # 创建mock组件
    llm_provider = AsyncMock()
    # 模拟LLM返回错误响应
    llm_provider.generate = AsyncMock(return_value=LLMResponse(
        content="Rate limit exceeded. Please try again later.",
        finish_reason="error"
    ))
    
    context_builder = WayFareContextBuilder()
    
    vector_store = AsyncMock()
    vector_store.search = AsyncMock(return_value=[])
    
    embedding_service = AsyncMock()
    embedding_service.embed_single = AsyncMock(return_value=np.random.rand(512))
    
    db = AsyncMock()
    db.get_document = AsyncMock(return_value={
        "hash": "test_hash",
        "version_hash": "v1",
        "path": "/test/doc.pdf",
        "status": "completed"
    })
    db.save_annotation = AsyncMock()
    
    # 创建批注生成器
    generator = create_annotation_generator(
        llm_provider=llm_provider,
        context_builder=context_builder,
        vector_store=vector_store,
        embedding_service=embedding_service,
        db=db
    )
    
    # 生成批注
    annotation = await generator.generate_annotation(
        doc_hash="test_hash",
        page=1,
        bbox={"x": 100, "y": 200, "width": 300, "height": 50},
        annotation_type="question",
        context="测试文本"
    )
    
    print(f"⚠️  LLM返回错误响应（Rate limit exceeded）")
    print(f"   批注ID: {annotation.id}")
    print(f"   批注类型: {annotation.type}")
    print(f"   批注内容: {annotation.content}")
    print(f"   说明: 系统自动使用降级文本，避免向用户暴露技术错误")
    print()


async def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "批注生成降级策略示例" + " " * 26 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 示例1: 正常生成
    await example_normal_generation()
    
    # 示例2: LLM失败降级
    await example_llm_failure_fallback()
    
    # 示例3: 不同类型的降级文本
    await example_all_annotation_types_fallback()
    
    # 示例4: 错误响应降级
    await example_error_response_fallback()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print("✅ 降级策略确保批注生成的可靠性")
    print("✅ 用户始终能获得批注响应")
    print("✅ 不同批注类型有不同的降级文本")
    print("✅ 降级事件被记录到日志中")
    print()


if __name__ == "__main__":
    asyncio.run(main())
