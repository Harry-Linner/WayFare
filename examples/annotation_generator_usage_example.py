"""
Annotation Generator使用示例

演示如何使用Annotation Generator生成学习辅助批注。
"""

import asyncio
import os
from pathlib import Path

from wayfare.annotation_generator import create_annotation_generator
from wayfare.llm_provider import create_llm_provider
from wayfare.context_builder import create_context_builder
from wayfare.vector_store import VectorStore
from wayfare.embedding import EmbeddingService
from wayfare.db import SQLiteDB


async def main():
    """主函数：演示Annotation Generator的使用"""
    
    print("=" * 60)
    print("Annotation Generator使用示例")
    print("=" * 60)
    
    # 1. 初始化所有依赖组件
    print("\n1. 初始化组件...")
    
    # LLM Provider
    llm_provider = create_llm_provider(
        api_key=os.getenv("SILICONFLOW_API_KEY"),
        model="deepseek-chat"
    )
    print("✓ LLM Provider初始化完成")
    
    # Context Builder
    context_builder = create_context_builder()
    print("✓ Context Builder初始化完成")
    
    # Vector Store
    vector_store = VectorStore(qdrant_url="http://localhost:6333")
    await vector_store.initialize()
    print("✓ Vector Store初始化完成")
    
    # Embedding Service
    embedding_service = EmbeddingService(
        model_path="./models/bge-small-zh-v1.5.onnx"
    )
    print("✓ Embedding Service初始化完成")
    
    # SQLite Database
    db = SQLiteDB(db_path=".wayfare/wayfare.db")
    await db.initialize()
    print("✓ SQLite Database初始化完成")
    
    # 2. 创建Annotation Generator
    print("\n2. 创建Annotation Generator...")
    generator = create_annotation_generator(
        llm_provider=llm_provider,
        context_builder=context_builder,
        vector_store=vector_store,
        embedding_service=embedding_service,
        db=db
    )
    print("✓ Annotation Generator创建完成")
    
    # 3. 生成批注示例
    print("\n3. 生成批注示例...")
    
    # 示例参数
    doc_hash = "example_doc_hash_123"
    page = 1
    bbox = {
        "x": 100.0,
        "y": 200.0,
        "width": 300.0,
        "height": 50.0
    }
    
    # 3.1 生成解释型批注
    print("\n3.1 生成解释型批注 (explanation)...")
    try:
        annotation_explanation = await generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type="explanation",
            context="费曼技巧是一种学习方法，通过用简单的语言解释复杂概念来检验理解程度。"
        )
        
        print(f"✓ 批注ID: {annotation_explanation.id}")
        print(f"  类型: {annotation_explanation.type}")
        print(f"  内容: {annotation_explanation.content[:100]}...")
        print(f"  位置: ({annotation_explanation.bbox.x}, {annotation_explanation.bbox.y})")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
    
    # 3.2 生成提问型批注
    print("\n3.2 生成提问型批注 (question)...")
    try:
        annotation_question = await generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type="question",
            context="认知负荷理论认为，工作记忆容量有限，学习材料的设计应该减少不必要的认知负荷。"
        )
        
        print(f"✓ 批注ID: {annotation_question.id}")
        print(f"  类型: {annotation_question.type}")
        print(f"  内容: {annotation_question.content[:100]}...")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
    
    # 3.3 生成总结型批注
    print("\n3.3 生成总结型批注 (summary)...")
    try:
        annotation_summary = await generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type="summary",
            context="""
            间隔重复是一种学习技术，通过在逐渐增加的时间间隔内复习信息来提高长期记忆。
            这种方法基于遗忘曲线理论，即人们在学习新信息后会逐渐遗忘。
            通过在最佳时机复习，可以强化记忆并延长保持时间。
            """
        )
        
        print(f"✓ 批注ID: {annotation_summary.id}")
        print(f"  类型: {annotation_summary.type}")
        print(f"  内容: {annotation_summary.content[:100]}...")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
    
    # 4. 演示错误处理
    print("\n4. 演示错误处理...")
    
    # 4.1 无效的批注类型
    print("\n4.1 测试无效的批注类型...")
    try:
        await generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type="invalid_type",
            context="测试文本"
        )
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")
    
    # 4.2 空的上下文
    print("\n4.2 测试空的上下文...")
    try:
        await generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox=bbox,
            annotation_type="explanation",
            context=""
        )
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")
    
    # 4.3 无效的bbox
    print("\n4.3 测试无效的bbox...")
    try:
        await generator.generate_annotation(
            doc_hash=doc_hash,
            page=page,
            bbox={"x": 0, "y": 0},  # 缺少width和height
            annotation_type="explanation",
            context="测试文本"
        )
    except ValueError as e:
        print(f"✓ 正确捕获错误: {e}")
    
    # 5. 演示RAG检索
    print("\n5. 演示RAG检索...")
    try:
        context_docs = await generator._retrieve_context(
            doc_hash=doc_hash,
            query_text="什么是费曼技巧？",
            top_k=5
        )
        print(f"✓ 检索到 {len(context_docs)} 个相关文档片段")
        for i, doc in enumerate(context_docs[:3], 1):
            print(f"  片段{i}: {doc[:50]}...")
    except Exception as e:
        print(f"✗ 检索失败: {e}")
    
    # 6. 演示Prompt构建
    print("\n6. 演示Prompt构建...")
    messages = generator._build_prompt(
        selected_text="费曼技巧",
        annotation_type="explanation",
        context_docs=["片段1", "片段2"]
    )
    print(f"✓ 构建了 {len(messages)} 条消息")
    print(f"  系统消息: {messages[0]['content'][:50]}...")
    print(f"  用户消息: {messages[1]['content'][:50]}...")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
