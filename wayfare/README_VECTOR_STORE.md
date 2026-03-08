# Vector Store模块

## 概述

Vector Store模块封装了Qdrant向量数据库客户端，提供向量存储、相似度搜索和文档删除功能。支持按文档hash过滤搜索结果，是WayFare RAG系统的核心组件。

## 功能特性

- ✅ 自动创建和管理Qdrant collection
- ✅ 批量向量存储（upsert操作）
- ✅ 向量相似度搜索（余弦相似度）
- ✅ 按文档hash过滤搜索结果
- ✅ 删除文档的所有向量
- ✅ 延迟初始化，避免启动时阻塞

## 需求映射

- **需求3.3**: 将向量数据存储到Qdrant向量数据库
- **需求3.4**: 执行向量相似度搜索并返回top-k相关片段
- **需求3.5**: 支持按文档hash过滤搜索结果

## 快速开始

### 安装依赖

```bash
pip install qdrant-client
```

### 启动Qdrant服务

使用Docker启动本地Qdrant实例：

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 基本使用

```python
import numpy as np
from wayfare.vector_store import VectorStore

# 1. 创建VectorStore实例
store = VectorStore(
    qdrant_url="http://localhost:6333",
    collection_name="documents"
)

# 2. 初始化（创建collection）
await store.initialize()

# 3. 插入向量
vectors = [
    {
        "id": "seg_1",
        "vector": [0.1, 0.2, ...],  # 512维向量
        "payload": {
            "doc_hash": "abc123",
            "page": 1,
            "text": "这是文档的第一段内容"
        }
    },
    {
        "id": "seg_2",
        "vector": [0.3, 0.4, ...],
        "payload": {
            "doc_hash": "abc123",
            "page": 1,
            "text": "这是文档的第二段内容"
        }
    }
]

await store.upsert_vectors(vectors)

# 4. 搜索相似向量
query_vector = np.random.randn(512)
results = await store.search(
    query_vector=query_vector,
    top_k=5,
    doc_hash="abc123"  # 可选：只在特定文档中搜索
)

for result in results:
    print(f"片段ID: {result.segment_id}")
    print(f"文本: {result.text}")
    print(f"页码: {result.page}")
    print(f"相似度: {result.score}")
    print("---")

# 5. 删除文档的所有向量
await store.delete_document("abc123")
```

## API参考

### VectorStore类

#### 初始化

```python
store = VectorStore(
    qdrant_url: str = "http://localhost:6333",
    collection_name: str = "documents"
)
```

**参数**:
- `qdrant_url`: Qdrant服务地址，默认为本地服务
- `collection_name`: Collection名称，默认为"documents"

#### initialize()

初始化Qdrant collection。如果collection不存在，则自动创建。

```python
await store.initialize()
```

**异常**:
- `ImportError`: 缺少qdrant-client依赖
- `ConnectionError`: 无法连接到Qdrant服务

#### upsert_vectors()

批量插入或更新向量。

```python
await store.upsert_vectors(vectors: List[Dict[str, Any]])
```

**参数**:
- `vectors`: 向量列表，每个元素包含:
  - `id` (str): 片段唯一标识
  - `vector` (list): 512维向量数组
  - `payload` (dict): 元数据，包含doc_hash、page、text等

**异常**:
- `RuntimeError`: 未初始化或插入失败
- `ValueError`: vectors为空或格式不正确

**示例**:
```python
vectors = [
    {
        "id": "doc1_seg1",
        "vector": embedding_vector.tolist(),
        "payload": {
            "doc_hash": "abc123",
            "page": 1,
            "text": "文档内容",
            "bbox": {"x": 0, "y": 0, "width": 100, "height": 50}
        }
    }
]
await store.upsert_vectors(vectors)
```

#### search()

向量相似度搜索。

```python
results = await store.search(
    query_vector: np.ndarray,
    top_k: int = 5,
    doc_hash: Optional[str] = None
) -> List[SearchResult]
```

**参数**:
- `query_vector`: 查询向量，shape为(512,)
- `top_k`: 返回top-k结果，默认5
- `doc_hash`: 可选的文档hash过滤

**返回**:
- `List[SearchResult]`: 搜索结果列表，按相似度降序排列

**异常**:
- `RuntimeError`: 未初始化或搜索失败
- `ValueError`: query_vector格式不正确或top_k无效

**示例**:
```python
# 全局搜索
results = await store.search(query_vector, top_k=10)

# 在特定文档中搜索
results = await store.search(
    query_vector,
    top_k=5,
    doc_hash="abc123"
)
```

#### delete_document()

删除文档的所有向量。

```python
await store.delete_document(doc_hash: str)
```

**参数**:
- `doc_hash`: 文档hash

**异常**:
- `RuntimeError`: 未初始化或删除失败
- `ValueError`: doc_hash为空

**示例**:
```python
await store.delete_document("abc123")
```

### SearchResult数据类

搜索结果的数据结构。

```python
@dataclass
class SearchResult:
    segment_id: str    # 片段ID
    text: str          # 片段文本
    page: int          # 页码
    score: float       # 相似度分数（0-1）
    doc_hash: str      # 文档hash
```

## 使用场景

### 场景1: 文档解析后存储向量

```python
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore

# 初始化服务
embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
vector_store = VectorStore()
await vector_store.initialize()

# 文档片段
segments = [
    {"id": "seg_1", "text": "片段1", "page": 1},
    {"id": "seg_2", "text": "片段2", "page": 1},
]

# 生成向量
texts = [seg["text"] for seg in segments]
embeddings = await embedding_service.embed_texts(texts)

# 准备向量数据
vectors = [
    {
        "id": seg["id"],
        "vector": emb.tolist(),
        "payload": {
            "doc_hash": "abc123",
            "page": seg["page"],
            "text": seg["text"]
        }
    }
    for seg, emb in zip(segments, embeddings)
]

# 存储向量
await vector_store.upsert_vectors(vectors)
```

### 场景2: RAG检索相关上下文

```python
# 用户查询
user_query = "什么是费曼技巧？"

# 生成查询向量
query_vector = await embedding_service.embed_single(user_query)

# 检索相关片段
results = await vector_store.search(
    query_vector=query_vector,
    top_k=5,
    doc_hash="abc123"  # 只在当前文档中搜索
)

# 构建上下文
context = "\n\n".join([r.text for r in results])
print(f"检索到{len(results)}个相关片段")
print(f"上下文:\n{context}")
```

### 场景3: 文档更新时重新索引

```python
# 删除旧向量
await vector_store.delete_document("abc123")

# 重新解析文档并生成向量
# ... (解析和向量化代码)

# 插入新向量
await vector_store.upsert_vectors(new_vectors)
```

## 配置建议

### 生产环境配置

```python
# 使用远程Qdrant服务
store = VectorStore(
    qdrant_url="http://qdrant-server:6333",
    collection_name="wayfare_documents"
)
```

### 开发环境配置

```python
# 使用本地Qdrant
store = VectorStore(
    qdrant_url="http://localhost:6333",
    collection_name="dev_documents"
)
```

### 从配置文件加载

```python
from wayfare.config import ConfigManager

config_manager = ConfigManager()
config = config_manager.get_config()

store = VectorStore(
    qdrant_url=config.qdrant_url,
    collection_name=config.qdrant_collection
)
```

## 性能优化

### 批量操作

```python
# ✅ 推荐：批量插入
vectors = [...]  # 100个向量
await store.upsert_vectors(vectors)

# ❌ 不推荐：逐个插入
for vector in vectors:
    await store.upsert_vectors([vector])  # 慢100倍
```

### 合理设置top_k

```python
# 根据实际需求设置top_k
# RAG场景：3-5个片段通常足够
results = await store.search(query_vector, top_k=5)

# 如果需要更多上下文，可以增加top_k
results = await store.search(query_vector, top_k=10)
```

### 使用doc_hash过滤

```python
# ✅ 推荐：使用过滤减少搜索空间
results = await store.search(
    query_vector,
    top_k=5,
    doc_hash="abc123"  # 只搜索特定文档
)

# ❌ 不推荐：全局搜索后手动过滤
all_results = await store.search(query_vector, top_k=100)
filtered = [r for r in all_results if r.doc_hash == "abc123"]
```

## 错误处理

```python
from wayfare.vector_store import VectorStore

store = VectorStore()

try:
    await store.initialize()
except ConnectionError as e:
    print(f"无法连接到Qdrant: {e}")
    # 处理连接错误
except ImportError as e:
    print(f"缺少依赖: {e}")
    # 提示安装qdrant-client

try:
    results = await store.search(query_vector)
except RuntimeError as e:
    print(f"搜索失败: {e}")
    # 处理搜索错误
except ValueError as e:
    print(f"参数错误: {e}")
    # 处理参数错误
```

## 测试

运行单元测试：

```bash
pytest tests/wayfare/test_vector_store.py -v
```

运行集成测试（需要Qdrant服务）：

```bash
# 启动Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# 运行集成测试
pytest tests/wayfare/test_vector_store.py::TestVectorStoreIntegration -v
```

## 常见问题

### Q: 如何选择collection名称？

A: 建议使用描述性名称，如"documents"、"wayfare_docs"等。不同环境可以使用不同的collection名称（如"dev_documents"、"prod_documents"）。

### Q: 向量维度可以修改吗？

A: 当前固定为512维（bge-small-zh-v1.5模型）。如果需要使用其他模型，需要修改`initialize()`方法中的`size`参数。

### Q: 如何处理大量文档？

A: Qdrant支持数百万级别的向量。建议：
- 使用批量插入（每批1000-5000个向量）
- 合理设置top_k（通常5-10个结果足够）
- 使用doc_hash过滤减少搜索空间

### Q: 删除文档后向量会立即删除吗？

A: 是的，`delete_document()`会立即删除所有匹配的向量。

### Q: 支持更新单个向量吗？

A: 使用`upsert_vectors()`即可。如果向量ID已存在，会自动更新；否则插入新向量。

## 相关模块

- `wayfare.embedding`: 文本向量化服务
- `wayfare.db`: SQLite数据库管理
- `wayfare.config`: 配置管理

## 参考资料

- [Qdrant官方文档](https://qdrant.tech/documentation/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [BAAI/bge-small-zh-v1.5模型](https://huggingface.co/BAAI/bge-small-zh-v1.5)
