"""
Vector Store使用示例

演示如何使用VectorStore进行向量存储、搜索和删除操作。
"""

import asyncio
import numpy as np
from wayfare.vector_store import VectorStore


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===\n")
    
    # 1. 创建VectorStore实例
    print("1. 创建VectorStore实例")
    store = VectorStore(
        qdrant_url="http://localhost:6333",
        collection_name="example_documents"
    )
    print(f"   Qdrant URL: {store.qdrant_url}")
    print(f"   Collection: {store.collection_name}")
    print(f"   已初始化: {store.is_initialized}\n")
    
    # 2. 初始化（创建collection）
    print("2. 初始化VectorStore")
    try:
        await store.initialize()
        print(f"   初始化成功！")
        print(f"   已初始化: {store.is_initialized}\n")
    except ConnectionError as e:
        print(f"   ❌ 连接失败: {e}")
        print("   请确保Qdrant服务正在运行：docker run -p 6333:6333 qdrant/qdrant")
        return
    
    # 3. 准备测试向量
    print("3. 准备测试向量")
    vectors = [
        {
            "id": "doc1_seg1",
            "vector": np.random.randn(512).tolist(),
            "payload": {
                "doc_hash": "doc_001",
                "page": 1,
                "text": "费曼技巧是一种学习方法，通过教授他人来检验自己的理解。"
            }
        },
        {
            "id": "doc1_seg2",
            "vector": np.random.randn(512).tolist(),
            "payload": {
                "doc_hash": "doc_001",
                "page": 1,
                "text": "这个方法的核心是用简单的语言解释复杂的概念。"
            }
        },
        {
            "id": "doc1_seg3",
            "vector": np.random.randn(512).tolist(),
            "payload": {
                "doc_hash": "doc_001",
                "page": 2,
                "text": "如果你不能简单地解释一个概念，说明你还没有真正理解它。"
            }
        },
        {
            "id": "doc2_seg1",
            "vector": np.random.randn(512).tolist(),
            "payload": {
                "doc_hash": "doc_002",
                "page": 1,
                "text": "机器学习是人工智能的一个重要分支。"
            }
        }
    ]
    print(f"   准备了 {len(vectors)} 个向量\n")
    
    # 4. 插入向量
    print("4. 插入向量到Qdrant")
    try:
        await store.upsert_vectors(vectors)
        print(f"   ✅ 成功插入 {len(vectors)} 个向量\n")
    except Exception as e:
        print(f"   ❌ 插入失败: {e}\n")
        return
    
    # 5. 搜索向量
    print("5. 搜索相似向量")
    query_vector = np.random.randn(512)
    
    try:
        # 全局搜索
        print("   5.1 全局搜索（top-3）")
        results = await store.search(query_vector, top_k=3)
        print(f"       找到 {len(results)} 个结果：")
        for i, result in enumerate(results, 1):
            print(f"       [{i}] ID: {result.segment_id}")
            print(f"           文档: {result.doc_hash}, 页码: {result.page}")
            print(f"           相似度: {result.score:.4f}")
            print(f"           文本: {result.text[:50]}...")
            print()
        
        # 带过滤的搜索
        print("   5.2 带doc_hash过滤的搜索（只搜索doc_001）")
        filtered_results = await store.search(
            query_vector,
            top_k=5,
            doc_hash="doc_001"
        )
        print(f"       找到 {len(filtered_results)} 个结果：")
        for i, result in enumerate(filtered_results, 1):
            print(f"       [{i}] ID: {result.segment_id}")
            print(f"           文档: {result.doc_hash}, 页码: {result.page}")
            print(f"           相似度: {result.score:.4f}")
            print()
        
    except Exception as e:
        print(f"   ❌ 搜索失败: {e}\n")
    
    # 6. 删除文档
    print("6. 删除文档向量")
    try:
        await store.delete_document("doc_001")
        print(f"   ✅ 成功删除 doc_001 的所有向量\n")
        
        # 验证删除
        print("   验证删除结果：")
        results_after_delete = await store.search(
            query_vector,
            top_k=10,
            doc_hash="doc_001"
        )
        print(f"   搜索 doc_001: 找到 {len(results_after_delete)} 个结果")
        
        results_doc2 = await store.search(
            query_vector,
            top_k=10,
            doc_hash="doc_002"
        )
        print(f"   搜索 doc_002: 找到 {len(results_doc2)} 个结果\n")
        
    except Exception as e:
        print(f"   ❌ 删除失败: {e}\n")


async def example_with_embedding():
    """结合Embedding Service的完整示例"""
    print("\n=== 结合Embedding Service的示例 ===\n")
    
    try:
        from wayfare.embedding import EmbeddingService
    except ImportError:
        print("❌ 需要安装依赖: pip install onnxruntime transformers")
        return
    
    # 初始化服务
    print("1. 初始化服务")
    
    # 注意：需要实际的ONNX模型文件
    model_path = "./models/bge-small-zh-v1.5.onnx"
    print(f"   模型路径: {model_path}")
    
    embedding_service = EmbeddingService(model_path)
    vector_store = VectorStore()
    
    try:
        await vector_store.initialize()
        print("   ✅ VectorStore初始化成功\n")
    except ConnectionError as e:
        print(f"   ❌ 连接Qdrant失败: {e}")
        return
    
    # 准备文档片段
    print("2. 准备文档片段")
    segments = [
        {
            "id": "seg_1",
            "text": "费曼技巧是一种高效的学习方法",
            "page": 1,
            "doc_hash": "learning_doc"
        },
        {
            "id": "seg_2",
            "text": "通过教授他人来检验自己的理解程度",
            "page": 1,
            "doc_hash": "learning_doc"
        },
        {
            "id": "seg_3",
            "text": "用简单的语言解释复杂的概念是关键",
            "page": 2,
            "doc_hash": "learning_doc"
        }
    ]
    print(f"   准备了 {len(segments)} 个片段\n")
    
    # 生成向量
    print("3. 生成向量")
    try:
        texts = [seg["text"] for seg in segments]
        embeddings = await embedding_service.embed_texts(texts)
        print(f"   ✅ 生成了 {len(embeddings)} 个向量")
        print(f"   向量维度: {embeddings.shape}\n")
    except Exception as e:
        print(f"   ❌ 生成向量失败: {e}")
        print("   注意：需要下载ONNX模型文件")
        return
    
    # 存储向量
    print("4. 存储向量")
    vectors = [
        {
            "id": seg["id"],
            "vector": emb.tolist(),
            "payload": {
                "doc_hash": seg["doc_hash"],
                "page": seg["page"],
                "text": seg["text"]
            }
        }
        for seg, emb in zip(segments, embeddings)
    ]
    
    try:
        await vector_store.upsert_vectors(vectors)
        print(f"   ✅ 成功存储 {len(vectors)} 个向量\n")
    except Exception as e:
        print(f"   ❌ 存储失败: {e}\n")
        return
    
    # RAG检索
    print("5. RAG检索示例")
    user_query = "如何有效地学习新知识？"
    print(f"   用户查询: {user_query}")
    
    try:
        # 生成查询向量
        query_vector = await embedding_service.embed_single(user_query)
        print(f"   ✅ 生成查询向量: {query_vector.shape}")
        
        # 检索相关片段
        results = await vector_store.search(
            query_vector=query_vector,
            top_k=3,
            doc_hash="learning_doc"
        )
        
        print(f"\n   检索到 {len(results)} 个相关片段：")
        for i, result in enumerate(results, 1):
            print(f"\n   [{i}] 相似度: {result.score:.4f}")
            print(f"       页码: {result.page}")
            print(f"       内容: {result.text}")
        
        # 构建RAG上下文
        context = "\n\n".join([r.text for r in results])
        print(f"\n   RAG上下文:\n   {context}\n")
        
    except Exception as e:
        print(f"   ❌ 检索失败: {e}\n")


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===\n")
    
    store = VectorStore()
    
    # 1. 未初始化时操作
    print("1. 未初始化时操作")
    try:
        await store.upsert_vectors([{"id": "1", "vector": [0.1], "payload": {}}])
    except RuntimeError as e:
        print(f"   ✅ 捕获到预期错误: {e}\n")
    
    # 2. 连接失败
    print("2. 连接到不存在的服务")
    bad_store = VectorStore(qdrant_url="http://localhost:9999")
    try:
        await bad_store.initialize()
    except ConnectionError as e:
        print(f"   ✅ 捕获到连接错误: {e}\n")
    
    # 初始化正常的store
    try:
        await store.initialize()
    except ConnectionError:
        print("   ⚠️  无法连接到Qdrant，跳过后续测试\n")
        return
    
    # 3. 空向量列表
    print("3. 插入空向量列表")
    try:
        await store.upsert_vectors([])
    except ValueError as e:
        print(f"   ✅ 捕获到参数错误: {e}\n")
    
    # 4. 格式不正确的向量
    print("4. 插入格式不正确的向量")
    try:
        await store.upsert_vectors([{"id": "1", "vector": [0.1]}])  # 缺少payload
    except ValueError as e:
        print(f"   ✅ 捕获到参数错误: {e}\n")
    
    # 5. 错误的向量维度
    print("5. 搜索时使用错误的向量维度")
    try:
        wrong_vector = np.random.randn(256)  # 应该是512维
        await store.search(wrong_vector)
    except ValueError as e:
        print(f"   ✅ 捕获到参数错误: {e}\n")
    
    # 6. 无效的top_k
    print("6. 使用无效的top_k")
    try:
        query_vector = np.random.randn(512)
        await store.search(query_vector, top_k=0)
    except ValueError as e:
        print(f"   ✅ 捕获到参数错误: {e}\n")
    
    # 7. 空doc_hash
    print("7. 删除空doc_hash")
    try:
        await store.delete_document("")
    except ValueError as e:
        print(f"   ✅ 捕获到参数错误: {e}\n")


async def example_batch_operations():
    """批量操作示例"""
    print("\n=== 批量操作示例 ===\n")
    
    store = VectorStore()
    
    try:
        await store.initialize()
    except ConnectionError as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 生成大量测试向量
    print("1. 生成1000个测试向量")
    import time
    
    vectors = []
    for i in range(1000):
        vectors.append({
            "id": f"batch_seg_{i}",
            "vector": np.random.randn(512).tolist(),
            "payload": {
                "doc_hash": f"batch_doc_{i // 100}",  # 10个文档，每个100个片段
                "page": i % 10,
                "text": f"这是第{i}个测试片段"
            }
        })
    
    print(f"   生成了 {len(vectors)} 个向量\n")
    
    # 批量插入
    print("2. 批量插入向量")
    start_time = time.time()
    
    try:
        await store.upsert_vectors(vectors)
        elapsed = time.time() - start_time
        print(f"   ✅ 插入完成")
        print(f"   耗时: {elapsed:.2f}秒")
        print(f"   速度: {len(vectors)/elapsed:.0f} 向量/秒\n")
    except Exception as e:
        print(f"   ❌ 插入失败: {e}\n")
        return
    
    # 批量搜索
    print("3. 批量搜索测试")
    query_vector = np.random.randn(512)
    
    start_time = time.time()
    results = await store.search(query_vector, top_k=10)
    elapsed = time.time() - start_time
    
    print(f"   ✅ 搜索完成")
    print(f"   找到 {len(results)} 个结果")
    print(f"   耗时: {elapsed*1000:.2f}毫秒\n")
    
    # 带过滤的搜索
    print("4. 带过滤的搜索测试")
    start_time = time.time()
    filtered_results = await store.search(
        query_vector,
        top_k=10,
        doc_hash="batch_doc_0"
    )
    elapsed = time.time() - start_time
    
    print(f"   ✅ 搜索完成")
    print(f"   找到 {len(filtered_results)} 个结果")
    print(f"   耗时: {elapsed*1000:.2f}毫秒\n")
    
    # 清理
    print("5. 清理测试数据")
    for i in range(10):
        await store.delete_document(f"batch_doc_{i}")
    print(f"   ✅ 清理完成\n")


async def main():
    """主函数"""
    print("=" * 60)
    print("Vector Store使用示例")
    print("=" * 60)
    print()
    
    # 运行示例
    await example_basic_usage()
    
    # 取消注释以运行其他示例
    # await example_with_embedding()
    # await example_error_handling()
    # await example_batch_operations()
    
    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
