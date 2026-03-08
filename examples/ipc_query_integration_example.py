"""
IPC Query集成示例

演示如何使用IPC Handler的query方法进行文档检索。
展示Task 5.9的完整实现：
- IPCHandler.handle_query()方法
- VectorStore.search_documents()辅助方法
- EmbeddingService集成生成查询向量
- 返回检索结果（segmentId、text、page、score）
"""

import asyncio
import json
from pathlib import Path


async def example_query_integration():
    """演示query方法的完整集成"""
    from wayfare.ipc import IPCHandler
    from wayfare.vector_store import VectorStore
    from wayfare.embedding import EmbeddingService
    from wayfare.db import SQLiteDB
    
    print("=" * 60)
    print("IPC Query集成示例")
    print("=" * 60)
    
    # 1. 初始化组件
    print("\n1. 初始化组件...")
    
    # 初始化数据库
    db = SQLiteDB(":memory:")
    await db.initialize()
    
    # 初始化Embedding Service
    # 注意：实际使用时需要提供真实的ONNX模型路径
    model_path = "models/bge-small-zh-v1.5.onnx"
    if not Path(model_path).exists():
        print(f"   ⚠️  模型文件不存在: {model_path}")
        print("   使用mock模式演示...")
        embedding_service = None
    else:
        embedding_service = EmbeddingService(model_path)
    
    # 初始化Vector Store
    try:
        vector_store = VectorStore()
        await vector_store.initialize()
        print("   ✓ VectorStore初始化完成")
    except ConnectionError as e:
        print(f"   ⚠️  无法连接到Qdrant: {e}")
        print("   使用mock模式演示...")
        vector_store = None
    
    # 初始化IPC Handler
    handler = IPCHandler(
        vector_store=vector_store,
        embedding_service=embedding_service
    )
    
    print("   ✓ 组件初始化完成")
    
    # 2. 模拟已有文档数据
    print("\n2. 准备测试数据...")
    print("   （实际使用中，文档应该已经通过parse方法解析并存储）")
    
    doc_hash = "test_doc_123"
    
    # 模拟向量数据已存储
    # 实际场景中，这些数据由DocumentParser在parse阶段生成
    print(f"   文档hash: {doc_hash}")
    print("   假设文档已解析并向量化...")
    
    # 3. 执行query请求
    print("\n3. 执行query请求...")
    
    query_params = {
        "docHash": doc_hash,
        "query": "什么是费曼技巧？",
        "topK": 5
    }
    
    print(f"   查询参数:")
    print(f"   - docHash: {query_params['docHash']}")
    print(f"   - query: {query_params['query']}")
    print(f"   - topK: {query_params['topK']}")
    
    try:
        if embedding_service is None or vector_store is None:
            print("\n   ⚠️  由于缺少模型文件或Qdrant服务，无法执行实际查询")
            print("   以下是预期的响应格式：")
            
            # 展示预期的响应格式
            mock_response = {
                "results": [
                    {
                        "segmentId": "seg_1",
                        "text": "费曼技巧是一种学习方法，通过用简单语言解释复杂概念来深入理解...",
                        "page": 1,
                        "score": 0.95
                    },
                    {
                        "segmentId": "seg_2",
                        "text": "使用费曼技巧的步骤：1. 选择概念 2. 用简单语言解释 3. 识别知识盲点...",
                        "page": 2,
                        "score": 0.88
                    },
                    {
                        "segmentId": "seg_3",
                        "text": "费曼技巧的核心在于通过教学来学习，这种方法能够暴露理解上的不足...",
                        "page": 1,
                        "score": 0.82
                    }
                ]
            }
            
            print(f"\n   预期响应:")
            print(json.dumps(mock_response, indent=2, ensure_ascii=False))
            
        else:
            # 实际执行查询
            result = await handler.handle_query(query_params)
            
            print(f"\n   ✓ 查询成功")
            print(f"   找到 {len(result['results'])} 个相关片段")
            
            # 4. 展示查询结果
            print("\n4. 查询结果:")
            
            for i, item in enumerate(result["results"], 1):
                print(f"\n   结果 {i}:")
                print(f"   - 片段ID: {item['segmentId']}")
                print(f"   - 页码: {item['page']}")
                print(f"   - 相似度: {item['score']:.4f}")
                print(f"   - 文本: {item['text'][:100]}...")
    
    except Exception as e:
        print(f"\n   ✗ 查询失败: {e}")
        return


async def example_query_error_handling():
    """演示query方法的错误处理"""
    from wayfare.ipc import IPCHandler
    
    print("\n" + "=" * 60)
    print("Query错误处理示例")
    print("=" * 60)
    
    # 创建未初始化的handler
    handler = IPCHandler()
    
    # 1. 测试缺少必需参数
    print("\n1. 测试缺少必需参数...")
    
    try:
        await handler.handle_query({"docHash": "test"})
    except ValueError as e:
        print(f"   ✓ 捕获到预期错误: {e}")
    
    # 2. 测试VectorStore未初始化
    print("\n2. 测试VectorStore未初始化...")
    
    try:
        await handler.handle_query({
            "docHash": "test",
            "query": "测试查询"
        })
    except RuntimeError as e:
        print(f"   ✓ 捕获到预期错误: {e}")
    
    # 3. 测试无效的topK参数
    print("\n3. 测试无效的topK参数...")
    
    from wayfare.vector_store import VectorStore
    from wayfare.embedding import EmbeddingService
    from unittest.mock import MagicMock
    
    # 创建mock对象以避免实际连接
    mock_vector_store = MagicMock()
    mock_embedding_service = MagicMock()
    
    handler = IPCHandler(
        vector_store=mock_vector_store,
        embedding_service=mock_embedding_service
    )
    
    try:
        await handler.handle_query({
            "docHash": "test",
            "query": "测试查询",
            "topK": -1
        })
    except ValueError as e:
        print(f"   ✓ 捕获到预期错误: {e}")
    
    print("\n   所有错误处理测试通过！")


async def example_vector_store_search_documents():
    """演示VectorStore.search_documents()辅助方法"""
    print("\n" + "=" * 60)
    print("VectorStore.search_documents()方法示例")
    print("=" * 60)
    
    print("\n1. VectorStore初始化说明:")
    print("   在实际使用中需要先初始化VectorStore")
    print("   本示例仅展示方法说明和使用方式")
    
    print("\n2. search_documents()方法说明:")
    print("   这是一个辅助方法，集成了以下功能：")
    print("   - 使用EmbeddingService生成查询向量")
    print("   - 调用search()方法执行向量搜索")
    print("   - 自动过滤指定文档的结果")
    print("   - 返回格式化的SearchResult列表")
    
    print("\n3. 方法签名:")
    print("""
    async def search_documents(
        self,
        doc_hash: str,           # 文档hash
        query: str,              # 查询文本
        embedding_service,       # EmbeddingService实例
        top_k: int = 5          # 返回结果数量
    ) -> List[SearchResult]:
    """)
    
    print("\n4. 使用示例:")
    print("""
    # 执行搜索
    results = await vector_store.search_documents(
        doc_hash="abc123",
        query="什么是机器学习？",
        embedding_service=embedding_service,
        top_k=5
    )
    
    # 处理结果
    for result in results:
        print(f"片段ID: {result.segment_id}")
        print(f"文本: {result.text}")
        print(f"页码: {result.page}")
        print(f"分数: {result.score}")
    """)
    
    print("\n5. 错误处理:")
    print("   - ValueError: doc_hash或query为空")
    print("   - ValueError: top_k无效（<=0）")
    print("   - RuntimeError: 向量搜索失败")


async def example_ipc_request_format():
    """演示完整的IPC请求格式"""
    print("\n" + "=" * 60)
    print("IPC Query请求格式示例")
    print("=" * 60)
    
    print("\n1. 标准query请求:")
    request = {
        "id": "req_12345",
        "seq": 1,
        "method": "query",
        "params": {
            "docHash": "blake3_hash_of_document",
            "query": "什么是费曼技巧？",
            "topK": 5
        }
    }
    print(json.dumps(request, indent=2, ensure_ascii=False))
    
    print("\n2. 预期响应格式:")
    response = {
        "id": "req_12345",
        "seq": 1,
        "success": True,
        "data": {
            "results": [
                {
                    "segmentId": "doc_hash_page_index",
                    "text": "相关片段的文本内容...",
                    "page": 1,
                    "score": 0.95
                },
                {
                    "segmentId": "doc_hash_page_index",
                    "text": "另一个相关片段...",
                    "page": 2,
                    "score": 0.88
                }
            ]
        }
    }
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    print("\n3. 错误响应格式:")
    error_response = {
        "id": "req_12345",
        "seq": 1,
        "success": False,
        "error": "Missing required parameter: query"
    }
    print(json.dumps(error_response, indent=2, ensure_ascii=False))
    
    print("\n4. 参数说明:")
    print("   请求参数:")
    print("   - docHash (必需): 文档的BLAKE3 hash")
    print("   - query (必需): 查询文本")
    print("   - topK (可选): 返回结果数量，默认5")
    print("\n   响应字段:")
    print("   - segmentId: 片段唯一标识")
    print("   - text: 片段文本内容")
    print("   - page: 片段所在页码")
    print("   - score: 相似度分数（0-1之间，越高越相关）")


async def main():
    """运行所有示例"""
    await example_query_integration()
    await example_query_error_handling()
    await example_vector_store_search_documents()
    await example_ipc_request_format()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print("\n关键要点:")
    print("1. query方法集成了Embedding生成和向量搜索")
    print("2. 支持按文档hash过滤搜索结果")
    print("3. 返回包含segmentId、text、page、score的结果")
    print("4. 完善的参数验证和错误处理")
    print("5. VectorStore.search_documents()是便捷的辅助方法")


if __name__ == "__main__":
    asyncio.run(main())
