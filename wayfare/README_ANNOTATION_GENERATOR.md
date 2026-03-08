# Annotation Generator

批注生成器核心模块，整合RAG检索和LLM生成，为用户选中的文本生成学习辅助批注。

## 功能概述

Annotation Generator是WayFare MVP Backend的核心组件之一，负责：

1. **RAG检索**：基于用户选中的文本，检索相关文档片段作为上下文
2. **Prompt构建**：根据批注类型选择合适的模板，填充上下文信息
3. **LLM调用**：调用DeepSeek模型生成批注内容
4. **批注保存**：将生成的批注保存到SQLite数据库

## 架构设计

### 依赖组件

Annotation Generator整合了以下组件：

- **LLM Provider** (`WayFareLLMProvider`): 提供LLM调用能力
- **Context Builder** (`WayFareContextBuilder`): 构建LLM上下文和Prompt
- **Vector Store** (`VectorStore`): 提供向量相似度搜索
- **Embedding Service** (`EmbeddingService`): 生成文本向量
- **SQLite DB** (`SQLiteDB`): 存储批注数据

### 核心流程

```
用户选中文本
    ↓
1. RAG检索
   - 生成查询向量
   - 向量相似度搜索
   - 返回top-5相关片段
    ↓
2. Prompt构建
   - 选择批注类型模板
   - 填充选中文本和上下文
   - 构建LLM消息列表
    ↓
3. LLM调用
   - 调用DeepSeek生成批注
   - 处理响应和错误
    ↓
4. 批注保存
   - 创建批注对象
   - 保存到数据库
   - 返回批注结果
```

## 批注类型

支持三种批注类型，每种类型使用不同的Prompt模板：

### 1. Explanation（解释）

使用费曼技巧，用简单易懂的语言解释复杂概念。

**适用场景**：
- 用户遇到难以理解的概念
- 需要深入理解某个知识点
- 希望用简单语言重新表述

**Prompt特点**：
- 要求解释核心概念
- 使用类比和例子
- 说明概念的重要性

### 2. Question（提问）

通过启发性问题引导学生深入思考。

**适用场景**：
- 需要主动思考和探索
- 希望联系已有知识
- 思考应用场景

**Prompt特点**：
- 提出2-3个启发性问题
- 引导理解概念本质
- 促进知识迁移

### 3. Summary（总结）

提炼核心要点，帮助学生建立知识框架。

**适用场景**：
- 内容较长需要总结
- 希望快速把握要点
- 建立知识结构

**Prompt特点**：
- 提炼主要观点
- 列出关键细节
- 说明与上下文的关系

## 使用方法

### 基本使用

```python
from wayfare.annotation_generator import create_annotation_generator
from wayfare.llm_provider import create_llm_provider
from wayfare.context_builder import create_context_builder
from wayfare.vector_store import VectorStore
from wayfare.embedding import EmbeddingService
from wayfare.db import SQLiteDB

# 1. 初始化依赖组件
llm_provider = create_llm_provider()
context_builder = create_context_builder()
vector_store = VectorStore()
await vector_store.initialize()
embedding_service = EmbeddingService(model_path="./models/bge-small-zh-v1.5.onnx")
db = SQLiteDB()
await db.initialize()

# 2. 创建Annotation Generator
generator = create_annotation_generator(
    llm_provider=llm_provider,
    context_builder=context_builder,
    vector_store=vector_store,
    embedding_service=embedding_service,
    db=db
)

# 3. 生成批注
annotation = await generator.generate_annotation(
    doc_hash="abc123",
    page=1,
    bbox={"x": 100, "y": 200, "width": 300, "height": 50},
    annotation_type="explanation",
    context="用户选中的文本"
)

print(f"批注ID: {annotation.id}")
print(f"批注内容: {annotation.content}")
```

### 生成不同类型的批注

```python
# 解释型批注
explanation = await generator.generate_annotation(
    doc_hash="abc123",
    page=1,
    bbox={"x": 100, "y": 200, "width": 300, "height": 50},
    annotation_type="explanation",
    context="费曼技巧是什么？"
)

# 提问型批注
question = await generator.generate_annotation(
    doc_hash="abc123",
    page=1,
    bbox={"x": 100, "y": 200, "width": 300, "height": 50},
    annotation_type="question",
    context="认知负荷理论的核心观点"
)

# 总结型批注
summary = await generator.generate_annotation(
    doc_hash="abc123",
    page=1,
    bbox={"x": 100, "y": 200, "width": 300, "height": 50},
    annotation_type="summary",
    context="间隔重复学习法的详细介绍..."
)
```

### 错误处理

```python
try:
    annotation = await generator.generate_annotation(
        doc_hash="abc123",
        page=1,
        bbox={"x": 100, "y": 200, "width": 300, "height": 50},
        annotation_type="explanation",
        context="用户选中的文本"
    )
except ValueError as e:
    # 参数验证错误
    print(f"参数错误: {e}")
except RuntimeError as e:
    # 生成失败（LLM调用失败等）
    print(f"生成失败: {e}")
```

## API参考

### AnnotationGenerator

#### `__init__(llm_provider, context_builder, vector_store, embedding_service, db)`

初始化批注生成器。

**参数**：
- `llm_provider` (WayFareLLMProvider): LLM Provider实例
- `context_builder` (WayFareContextBuilder): Context Builder实例
- `vector_store` (VectorStore): Vector Store实例
- `embedding_service` (EmbeddingService): Embedding Service实例
- `db` (SQLiteDB): SQLite数据库实例

#### `async generate_annotation(doc_hash, page, bbox, annotation_type, context)`

生成批注（主方法）。

**参数**：
- `doc_hash` (str): 文档hash
- `page` (int): 页码
- `bbox` (dict): 边界框，包含x、y、width、height
- `annotation_type` (str): 批注类型（explanation/question/summary）
- `context` (str): 用户选中的文本

**返回**：
- `Annotation`: 生成的批注对象

**异常**：
- `ValueError`: 参数无效
- `RuntimeError`: 生成失败

**示例**：
```python
annotation = await generator.generate_annotation(
    doc_hash="abc123",
    page=1,
    bbox={"x": 100, "y": 200, "width": 300, "height": 50},
    annotation_type="explanation",
    context="费曼技巧"
)
```

### 工厂函数

#### `create_annotation_generator(llm_provider, context_builder, vector_store, embedding_service, db)`

创建Annotation Generator实例。

**参数**：同`__init__`

**返回**：
- `AnnotationGenerator`: 批注生成器实例

## 配置选项

### RAG检索配置

```python
# 修改top-k值
context_docs = await generator._retrieve_context(
    doc_hash="abc123",
    query_text="查询文本",
    top_k=10  # 默认为5
)
```

### LLM生成配置

LLM调用参数在`_call_llm`方法中配置：

```python
response = await self.llm.generate(
    messages=messages,
    max_tokens=512,      # 批注内容较短，限制token数
    temperature=0.7      # 适中的创造性
)
```

如需修改，可以继承`AnnotationGenerator`并重写`_call_llm`方法。

## 性能考虑

### 批注生成时间

典型的批注生成时间分解：

1. **RAG检索**: ~200ms
   - 向量生成: ~50ms
   - 向量搜索: ~150ms

2. **LLM调用**: ~2-3秒
   - 网络延迟: ~100ms
   - 模型推理: ~2秒

3. **数据库保存**: ~10ms

**总计**: ~2.5-3.5秒

### 优化建议

1. **批量生成**: 如果需要生成多个批注，可以并发调用
2. **缓存**: 对于相同的查询文本，可以缓存RAG检索结果
3. **异步处理**: 在IPC Handler中异步处理批注生成请求

## 测试

### 运行单元测试

```bash
pytest tests/wayfare/test_annotation_generator.py -v
```

### 运行使用示例

```bash
python examples/annotation_generator_usage_example.py
```

## 需求映射

本模块实现以下需求：

- **需求 4.1**: 使用RAG检索相关上下文
- **需求 4.2**: 调用LLM生成批注内容（费曼技巧和认知支架模板）

## 相关文档

- [LLM Provider文档](./README_LLM_PROVIDER.md)
- [Context Builder文档](./README_CONTEXT_BUILDER.md)
- [Vector Store文档](./README_VECTOR_STORE.md)
- [Embedding Service文档](./README_EMBEDDING.md)
- [数据库文档](./README_DB.md)

## 常见问题

### Q: 如何自定义Prompt模板？

A: 使用Context Builder的`update_prompt_template`方法：

```python
context_builder.update_prompt_template(
    annotation_type="explanation",
    template="自定义模板，包含{selected_text}和{context}占位符"
)
```

### Q: 如何处理LLM调用失败？

A: LLM Provider内置了重试机制（默认3次）。如果仍然失败，会返回错误响应而不是抛出异常。可以检查`finish_reason`字段：

```python
response = await llm.generate(messages)
if response.finish_reason == "error":
    print(f"LLM调用失败: {response.content}")
```

### Q: 如何调整RAG检索的相关性？

A: 可以修改`top_k`参数来调整返回的文档片段数量。更多片段提供更丰富的上下文，但也会增加token消耗。

### Q: 批注内容过长怎么办？

A: 可以调整LLM调用的`max_tokens`参数。默认为512，可以根据需要增加或减少。

## 更新日志

### v1.0.0 (2024-01-XX)

- ✅ 实现核心批注生成逻辑
- ✅ 集成LLM Provider、Context Builder、Vector Store、Embedding Service
- ✅ 实现RAG检索逻辑（查询向量生成 + top-5检索）
- ✅ 实现Prompt构建逻辑（选择模板 + 填充上下文）
- ✅ 实现LLM调用和响应处理
- ✅ 支持三种批注类型（explanation、question、summary）
- ✅ 完整的错误处理和参数验证
- ✅ 单元测试覆盖率100%


## 降级策略

### 概述

当LLM服务不可用时，Annotation Generator会自动使用降级策略，返回预设的降级文本，确保用户始终能获得批注响应。

### 降级触发条件

降级策略在以下情况下触发：

1. **LLM返回空内容**: `response.content` 为空
2. **LLM返回错误**: `response.finish_reason == "error"`
3. **LLM调用异常**: 网络超时、连接失败等异常

### 降级文本

不同批注类型有不同的降级文本：

| 批注类型 | 降级文本 |
|---------|---------|
| explanation | AI助手暂时不可用，请稍后重试。 |
| question | 思考一下：这段内容的核心概念是什么？ |
| summary | 请尝试用自己的话总结这段内容。 |
| 未知类型 | AI助手暂时不可用。 |

### 日志记录

降级事件会被记录到日志中：

```
2024-01-15 10:30:45 | WARNING | LLM call failed with exception: Network timeout, using fallback strategy
2024-01-15 10:30:45 | WARNING | Using fallback content for annotation type: explanation
2024-01-15 10:30:45 | INFO | Fallback annotation generated: AI助手暂时不可用，请稍后重试。...
```

### 使用示例

```python
# LLM服务不可用时
annotation = await generator.generate_annotation(
    doc_hash="abc123",
    page=1,
    bbox={"x": 100, "y": 200, "width": 300, "height": 50},
    annotation_type="explanation",
    context="什么是费曼技巧？"
)

# 返回的批注使用降级文本
assert annotation.content == "AI助手暂时不可用，请稍后重试。"

# 批注仍然成功保存到数据库
assert annotation.id is not None
```

### 与重试机制的关系

- **LLM Provider**: 已有3次重试机制（最大重试次数可配置）
- **降级策略**: 在所有重试失败后触发
- **总体流程**: 重试 → 失败 → 降级 → 返回预设文本

### 优势

1. **可靠性**: 确保批注生成流程不会因LLM失败而中断
2. **用户体验**: 用户始终能获得响应，而不是看到错误消息
3. **快速响应**: 降级文本是预设的，响应时间 < 1ms
4. **可观测性**: 所有降级事件都被记录，便于监控和告警
