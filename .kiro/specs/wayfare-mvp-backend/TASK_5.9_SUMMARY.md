# Task 5.9 实现总结：集成query方法到IPC Handler

## 任务概述

实现IPC Handler的query方法，集成Vector Store和Embedding Service进行文档检索。

## 实现内容

### 1. IPCHandler.handle_query()方法实现

**文件**: `wayfare/ipc.py`

**功能**:
- 验证请求参数（docHash、query、可选topK）
- 检查VectorStore和EmbeddingService是否已初始化
- 调用VectorStore.search_documents()执行搜索
- 返回格式化的检索结果（segmentId、text、page、score）
- 完善的错误处理

**关键代码**:
```python
async def handle_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """处理query请求
    
    完整流程：
    1. 验证请求参数（docHash、query、可选topK）
    2. 使用EmbeddingService生成查询向量
    3. 调用VectorStore.search_documents()搜索相关片段
    4. 返回检索结果（segmentId、text、page、score）
    """
    # 1. 验证必需参数
    required_params = ["docHash", "query"]
    for param in required_params:
        if param not in params:
            raise ValueError(f"Missing required parameter: {param}")
    
    # 2. 检查依赖是否初始化
    if self.vector_store is None:
        raise RuntimeError("VectorStore not initialized...")
    
    if self.embedding_service is None:
        raise RuntimeError("EmbeddingService not initialized...")
    
    # 3. 获取参数
    doc_hash = params["docHash"]
    query = params["query"]
    top_k = params.get("topK", 5)  # 默认返回5个结果
    
    # 4. 验证参数
    if not doc_hash or not doc_hash.strip():
        raise ValueError("docHash cannot be empty")
    
    if not query or not query.strip():
        raise ValueError("query cannot be empty")
    
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError(f"topK must be a positive integer, got {top_k}")
    
    # 5. 执行搜索
    search_results = await self.vector_store.search_documents(
        doc_hash=doc_hash,
        query=query,
        embedding_service=self.embedding_service,
        top_k=top_k
    )
    
    # 6. 格式化返回结果
    results = [
        {
            "segmentId": result.segment_id,
            "text": result.text,
            "page": result.page,
            "score": result.score
        }
        for result in search_results
    ]
    
    return {"results": results}
```

### 2. VectorStore.search_documents()辅助方法

**文件**: `wayfare/vector_store.py`

**功能**:
- 集成embedding生成和向量搜索
- 接收查询文本和embedding_service
- 生成查询向量
- 调用search()方法执行向量搜索
- 自动过滤指定文档的结果

**关键代码**:
```python
async def search_documents(
    self,
    doc_hash: str,
    query: str,
    embedding_service,
    top_k: int = 5
) -> List[SearchResult]:
    """在指定文档中搜索相关片段
    
    这是一个辅助方法，集成了embedding生成和向量搜索。
    """
    # 参数验证
    if not doc_hash:
        raise ValueError("doc_hash cannot be empty")
    
    if not query or not query.strip():
        raise ValueError("query cannot be empty")
    
    if top_k <= 0:
        raise ValueError(f"top_k must be positive, got {top_k}")
    
    # 1. 生成查询向量
    query_vector = await embedding_service.embed_single(query)
    
    # 2. 执行向量搜索
    results = await self.search(
        query_vector=query_vector,
        top_k=top_k,
        doc_hash=doc_hash
    )
    
    return results
```

### 3. IPCHandler构造函数更新

**更新**: 添加embedding_service参数

```python
def __init__(self, 
             doc_parser=None,
             annotation_gen=None,
             vector_store=None,
             embedding_service=None,  # 新增
             config_manager=None,
             behavior_analyzer=None):
    """初始化IPC Handler
    
    Args:
        embedding_service: EmbeddingService实例（可选，用于query方法）
    """
    self.embedding_service = embedding_service
    # ... 其他初始化代码
```

## 测试覆盖

### 测试文件: `tests/wayfare/test_ipc_query_integration.py`

**测试类**:

1. **TestIPCQueryIntegration**: 测试IPC Handler的query方法
   - ✅ test_handle_query_success: 测试query请求成功处理
   - ✅ test_handle_query_default_topk: 测试默认topK值
   - ✅ test_handle_query_custom_topk: 测试自定义topK值
   - ✅ test_handle_query_empty_results: 测试空结果
   - ✅ test_handle_query_missing_doc_hash: 测试缺少docHash参数
   - ✅ test_handle_query_missing_query: 测试缺少query参数
   - ✅ test_handle_query_empty_doc_hash: 测试docHash为空
   - ✅ test_handle_query_empty_query: 测试query为空
   - ✅ test_handle_query_invalid_topk_negative: 测试topK为负数
   - ✅ test_handle_query_invalid_topk_zero: 测试topK为0
   - ✅ test_handle_query_invalid_topk_string: 测试topK为字符串
   - ✅ test_handle_query_no_vector_store: 测试VectorStore未初始化
   - ✅ test_handle_query_no_embedding_service: 测试EmbeddingService未初始化
   - ✅ test_handle_query_vector_store_error: 测试VectorStore错误
   - ✅ test_handle_query_embedding_error: 测试Embedding生成错误

2. **TestVectorStoreSearchDocuments**: 测试VectorStore.search_documents()方法
   - ✅ test_search_documents_integration: 测试方法集成
   - ✅ test_search_documents_empty_doc_hash: 测试doc_hash为空
   - ✅ test_search_documents_empty_query: 测试query为空
   - ✅ test_search_documents_invalid_topk: 测试topK无效

3. **TestEndToEndQueryFlow**: 端到端测试
   - ✅ test_full_query_request_flow: 测试完整query流程

**测试结果**: 20个测试全部通过 ✅

```
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_success PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_default_topk PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_custom_topk PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_empty_results PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_missing_doc_hash PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_missing_query PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_empty_doc_hash PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_empty_query PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_invalid_topk_negative PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_invalid_topk_zero PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_invalid_topk_string PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_no_vector_store PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_no_embedding_service PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_vector_store_error PASSED
tests/wayfare/test_ipc_query_integration.py::TestIPCQueryIntegration::test_handle_query_embedding_error PASSED
tests/wayfare/test_ipc_query_integration.py::TestVectorStoreSearchDocuments::test_search_documents_integration PASSED
tests/wayfare/test_ipc_query_integration.py::TestVectorStoreSearchDocuments::test_search_documents_empty_doc_hash PASSED
tests/wayfare/test_ipc_query_integration.py::TestVectorStoreSearchDocuments::test_search_documents_empty_query PASSED
tests/wayfare/test_ipc_query_integration.py::TestVectorStoreSearchDocuments::test_search_documents_invalid_topk PASSED
tests/wayfare/test_ipc_query_integration.py::TestEndToEndQueryFlow::test_full_query_request_flow PASSED

============== 20 passed in 5.33s ===============
```

## 示例代码

### 示例文件: `examples/ipc_query_integration_example.py`

**包含示例**:
1. **example_query_integration()**: 演示query方法的完整集成
2. **example_query_error_handling()**: 演示错误处理
3. **example_vector_store_search_documents()**: 演示VectorStore.search_documents()方法
4. **example_ipc_request_format()**: 演示IPC请求格式

**运行示例**:
```bash
python examples/ipc_query_integration_example.py
```

## IPC协议规范

### Query请求格式

```json
{
  "id": "req_12345",
  "seq": 1,
  "method": "query",
  "params": {
    "docHash": "blake3_hash_of_document",
    "query": "什么是费曼技巧？",
    "topK": 5
  }
}
```

### Query响应格式

**成功响应**:
```json
{
  "id": "req_12345",
  "seq": 1,
  "success": true,
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
```

**错误响应**:
```json
{
  "id": "req_12345",
  "seq": 1,
  "success": false,
  "error": "Missing required parameter: query"
}
```

## 参数说明

### 请求参数

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| docHash | string | 是 | - | 文档的BLAKE3 hash |
| query | string | 是 | - | 查询文本 |
| topK | integer | 否 | 5 | 返回结果数量 |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| segmentId | string | 片段唯一标识 |
| text | string | 片段文本内容 |
| page | integer | 片段所在页码 |
| score | float | 相似度分数（0-1之间，越高越相关） |

## 错误处理

### 参数验证错误 (ValueError)

- 缺少必需参数（docHash、query）
- docHash为空字符串
- query为空字符串
- topK不是正整数

### 运行时错误 (RuntimeError)

- VectorStore未初始化
- EmbeddingService未初始化
- 向量搜索失败
- Embedding生成失败

## 数据流

```
1. 前端发送query请求
   ↓
2. IPCHandler.handle_query()接收请求
   ↓
3. 验证参数（docHash、query、topK）
   ↓
4. 检查VectorStore和EmbeddingService是否初始化
   ↓
5. 调用VectorStore.search_documents()
   ↓
6. EmbeddingService.embed_single()生成查询向量
   ↓
7. VectorStore.search()执行向量搜索
   ↓
8. 过滤指定文档的结果
   ↓
9. 格式化返回结果
   ↓
10. 返回给前端
```

## 与其他组件的集成

### 依赖组件

1. **VectorStore** (`wayfare/vector_store.py`)
   - 提供向量搜索功能
   - search_documents()辅助方法

2. **EmbeddingService** (`wayfare/embedding.py`)
   - 生成查询向量
   - embed_single()方法

3. **SQLiteDB** (`wayfare/db.py`)
   - 存储文档片段元数据
   - 提供segment详细信息

### 被依赖组件

- 前端通过IPC调用query方法
- 批注生成器可能使用query方法获取相关上下文

## 性能考虑

1. **向量搜索性能**: 
   - Qdrant提供高效的向量搜索
   - 支持按文档hash过滤，减少搜索空间

2. **Embedding生成**:
   - 使用本地ONNX模型，避免网络延迟
   - 单次查询只需生成一个向量

3. **结果返回**:
   - 默认返回top-5结果，减少数据传输
   - 可通过topK参数调整

## 需求映射

### 需求 5.4: IPC_Handler支持query方法

✅ **完全实现**:
- IPCHandler.handle_query()方法完整实现
- 支持docHash、query、topK参数
- 返回segmentId、text、page、score
- 完善的错误处理

### 需求 3.4: Vector_Store执行向量相似度搜索

✅ **集成完成**:
- 通过VectorStore.search_documents()集成
- 支持按文档hash过滤
- 返回top-k相关片段

### 需求 3.5: Vector_Store支持按文档hash过滤

✅ **完全支持**:
- search_documents()方法自动过滤指定文档
- 只返回该文档的相关片段

## 后续工作

1. **性能优化**:
   - 考虑添加查询缓存
   - 优化向量搜索参数

2. **功能增强**:
   - 支持多文档联合搜索
   - 添加搜索结果排序选项
   - 支持高级过滤条件

3. **监控和日志**:
   - 添加查询性能监控
   - 记录查询统计信息

## 总结

Task 5.9成功实现了IPC Handler的query方法集成，包括：

✅ IPCHandler.handle_query()方法完整实现
✅ VectorStore.search_documents()辅助方法
✅ EmbeddingService集成生成查询向量
✅ 返回检索结果（segmentId、text、page、score）
✅ 完善的错误处理
✅ 20个测试全部通过
✅ 完整的示例代码和文档

该实现为前端提供了强大的文档检索能力，是批注生成和智能问答的基础。
