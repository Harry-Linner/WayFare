# IPC Handler模块文档

## 概述

IPC Handler模块实现了与Tauri前端的通信协议，负责处理JSON-RPC格式的IPC请求和响应。

## 核心功能

### 1. 请求解析和验证

- 解析JSON格式的IPC请求
- 验证必需字段（id、seq、method、params）
- 验证method是否支持（parse、annotate、query、config）
- 提供详细的错误消息

### 2. 请求队列和seq排序

实现了按seq序列号顺序处理请求的机制，防止"先发后到"问题：

- 如果收到的请求seq是下一个期望的seq，立即处理
- 如果seq大于期望值，暂存到pending_requests中
- 当收到缺失的seq时，自动处理所有连续的pending请求
- 忽略重复或过期的请求（seq小于期望值）

### 3. 异步文档解析（Phase 2已实现）

parse方法实现了异步文档解析机制：

- **立即响应**: 收到parse请求后立即返回"processing"状态，不阻塞其他请求
- **后台处理**: 在后台异步执行文档解析任务
- **主动推送**: 解析完成或失败后，通过stdout主动推送通知给前端

**通知格式:**
```json
{
  "type": "notification",
  "data": {
    "type": "parse_completed",  // 或 "parse_failed"
    "docHash": "blake3_hash",
    "segmentCount": 42,
    "versionHash": "content_hash",
    "status": "completed"       // 或 "failed"
  }
}
```

### 4. 错误处理

提供标准化的错误响应格式：

```json
{
  "id": "request-id",
  "seq": 0,
  "success": false,
  "error": "错误描述"
}
```

### 5. 方法路由

支持五种IPC方法：

- **parse**: 文档解析请求（已集成DocumentParser）
- **annotate**: 批注生成请求（已集成AnnotationGenerator）
- **query**: 文档检索请求（已集成VectorStore）
- **config**: 配置更新请求（待实现）
- **behavior**: 用户行为记录请求（已集成BehaviorAnalyzer）

### 6. 行为分析和主动干预（Phase 7已实现）

behavior方法实现了用户行为分析和主动干预机制：

- **行为记录**: 接收前端发送的用户行为数据（page_view、text_select、scroll）
- **停留时间跟踪**: 自动跟踪用户在页面的停留时间
- **定期检查**: 后台任务定期检查是否需要触发干预
- **主动推送**: 当停留时间超过阈值时，自动推送干预消息

**干预通知格式:**
```json
{
  "type": "notification",
  "data": {
    "type": "intervention",
    "docHash": "blake3_hash",
    "page": 1,
    "message": "您在第1页停留了较长时间，需要帮助吗？",
    "statistics": {
      "totalViews": 5,
      "totalSelects": 3,
      "totalScrolls": 2,
      "avgDuration": 45.5
    }
  }
}
```

## 数据模型

### IPCRequest

```python
@dataclass
class IPCRequest:
    id: str              # 请求唯一标识
    seq: int             # 请求序列号（用于排序）
    method: str          # 方法名称
    params: Dict[str, Any]  # 方法参数
```

### IPCResponse

```python
@dataclass
class IPCResponse:
    id: str              # 对应请求的ID
    seq: int             # 对应请求的seq
    success: bool        # 是否成功
    data: Optional[Dict[str, Any]]    # 成功时的数据
    error: Optional[str]              # 失败时的错误消息
```

## 使用示例

### 基本使用（带DocumentParser集成）

```python
import asyncio
import json
from wayfare.ipc import IPCHandler
from wayfare.document_parser import DocumentParser
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore
from wayfare.db import SQLiteDB

async def main():
    # 初始化依赖组件
    db = SQLiteDB(".wayfare/wayfare.db")
    await db.initialize()
    
    embedding_service = EmbeddingService("./models/bge-small-zh-v1.5.onnx")
    
    vector_store = VectorStore("http://localhost:6333")
    await vector_store.initialize()
    
    doc_parser = DocumentParser(
        embedding_service=embedding_service,
        vector_store=vector_store,
        db=db
    )
    
    # 创建IPC Handler（注入DocumentParser）
    handler = IPCHandler(doc_parser=doc_parser)
    
    # 构造parse请求
    request = json.dumps({
        "id": "req-001",
        "seq": 0,
        "method": "parse",
        "params": {
            "path": "/path/to/document.pdf"
        }
    })
    
    # 处理请求（立即返回processing状态）
    response = await handler.handle_request(request)
    print(response)
    # 输出: {"id": "req-001", "seq": 0, "success": true, 
    #        "data": {"docHash": "...", "status": "processing"}}
    
    # 后台异步解析完成后，会通过stdout发送通知
    # 前端监听stdout即可接收通知

asyncio.run(main())
```

### 监听异步解析通知

```python
import sys
import json

# 前端代码示例（监听stdout）
def handle_backend_output(line):
    """处理backend的输出"""
    try:
        message = json.loads(line)
        
        if message.get("type") == "notification":
            data = message["data"]
            
            if data["type"] == "parse_completed":
                print(f"✓ 文档解析完成: {data['docHash']}")
                print(f"  片段数: {data['segmentCount']}")
                print(f"  版本: {data['versionHash']}")
            
            elif data["type"] == "parse_failed":
                print(f"✗ 文档解析失败: {data['docHash']}")
                print(f"  错误: {data['error']}")
    
    except json.JSONDecodeError:
        pass  # 不是JSON消息，忽略
```

### 处理乱序请求

```python
handler = IPCHandler()

# 先发送seq=2的请求（会被缓存）
await handler.handle_request(json.dumps({
    "id": "req-1", "seq": 2, "method": "parse", 
    "params": {"path": "/doc2.pdf"}
}))

# 发送seq=0的请求（立即处理）
await handler.handle_request(json.dumps({
    "id": "req-2", "seq": 0, "method": "parse",
    "params": {"path": "/doc0.pdf"}
}))

# 发送seq=1的请求（处理后会自动处理seq=2）
await handler.handle_request(json.dumps({
    "id": "req-3", "seq": 1, "method": "parse",
    "params": {"path": "/doc1.pdf"}
}))
```

## API接口规范

### parse方法（已集成DocumentParser）

**功能**: 异步解析PDF或Markdown文档

**请求参数:**
```json
{
  "path": "/path/to/document.pdf"  // 文档路径（必需）
}
```

**立即响应数据:**
```json
{
  "docHash": "blake3_hash",        // 文档hash
  "status": "processing"           // 处理状态（立即返回）
}
```

**异步通知（解析完成）:**
```json
{
  "type": "notification",
  "data": {
    "type": "parse_completed",
    "docHash": "blake3_hash",
    "segmentCount": 42,            // 片段数量
    "versionHash": "content_hash", // 版本hash
    "status": "completed"
  }
}
```

**异步通知（解析失败）:**
```json
{
  "type": "notification",
  "data": {
    "type": "parse_failed",
    "docHash": "blake3_hash",
    "error": "错误描述",
    "status": "failed"
  }
}
```

**特性:**
- ✅ 立即返回，不阻塞其他请求
- ✅ 后台异步执行文档解析
- ✅ 完成后主动推送通知
- ✅ 错误处理和失败通知
- ✅ 支持PDF和Markdown格式

### annotate方法

**请求参数:**
```json
{
  "docHash": "blake3_hash",        // 文档hash（必需）
  "page": 5,                       // 页码（必需）
  "bbox": {                        // 边界框（必需）
    "x": 100,
    "y": 200,
    "width": 300,
    "height": 50
  },
  "type": "explanation",           // 批注类型（必需）
  "context": "用户选中的文本"        // 上下文（必需）
}
```

**响应数据:**
```json
{
  "annotationId": "uuid",          // 批注ID
  "content": "AI生成的批注内容",    // 批注内容
  "type": "explanation"            // 批注类型
}
```

### query方法

**请求参数:**
```json
{
  "docHash": "blake3_hash",        // 文档hash（必需）
  "query": "什么是费曼技巧？",      // 查询文本（必需）
  "topK": 5                        // 返回结果数量（可选，默认5）
}
```

**响应数据:**
```json
{
  "results": [
    {
      "segmentId": "uuid",         // 片段ID
      "text": "相关片段文本",       // 片段内容
      "page": 3,                   // 页码
      "score": 0.85                // 相似度分数
    }
  ]
}
```

### config方法

**请求参数:**
```json
{
  "llm_model": "deepseek-chat",           // LLM模型（可选）
  "embedding_model": "bge-small-zh-v1.5", // Embedding模型（可选）
  "retrieval_top_k": 5,                   // 检索top-k（可选）
  "intervention_threshold": 120           // 干预阈值（可选）
}
```

**响应数据:**
```json
{
  "updated": true                  // 是否更新成功
}
```

### behavior方法（已集成BehaviorAnalyzer）

**功能**: 记录用户行为数据，支持主动干预触发

**请求参数:**
```json
{
  "docHash": "blake3_hash",        // 文档hash（必需）
  "page": 1,                       // 页码（必需）
  "eventType": "page_view",        // 事件类型（必需）
  "metadata": {                    // 可选的额外元数据
    "duration": 30,
    "text": "选中的文本"
  }
}
```

**事件类型:**
- `page_view`: 页面浏览事件（会启动停留时间跟踪）
- `text_select`: 文本选择事件
- `scroll`: 滚动事件

**响应数据:**
```json
{
  "recorded": true,                // 是否成功记录
  "eventId": "uuid"                // 行为事件ID
}
```

**主动干预通知（当停留时间超过阈值）:**
```json
{
  "type": "notification",
  "data": {
    "type": "intervention",
    "docHash": "blake3_hash",
    "page": 1,
    "message": "您在第1页停留了较长时间，需要帮助吗？",
    "statistics": {
      "totalViews": 5,             // 浏览次数
      "totalSelects": 3,           // 选择次数
      "totalScrolls": 2,           // 滚动次数
      "avgDuration": 45.5          // 平均停留时间（秒）
    }
  }
}
```

**特性:**
- ✅ 记录用户行为到数据库
- ✅ 自动跟踪页面停留时间
- ✅ 定期检查干预触发条件（默认每30秒）
- ✅ 超过阈值自动推送干预消息（默认120秒）
- ✅ 支持多页面并发跟踪
- ✅ 提供行为统计信息

## 错误处理

### 常见错误类型

1. **缺少必需字段**
   ```json
   {
     "success": false,
     "error": "Missing required field: method"
   }
   ```

2. **不支持的方法**
   ```json
   {
     "success": false,
     "error": "Unsupported method: unknown_method. Supported methods: parse, annotate, query, config"
   }
   ```

3. **JSON解析错误**
   ```json
   {
     "success": false,
     "error": "Invalid JSON: Expecting value: line 1 column 1 (char 0)"
   }
   ```

4. **缺少方法参数**
   ```json
   {
     "success": false,
     "error": "Missing required parameter: path"
   }
   ```

## 实现细节

### seq排序机制

IPC Handler使用以下机制确保请求按seq顺序处理：

1. 维护`next_expected_seq`变量，记录下一个期望的seq
2. 维护`pending_requests`字典，缓存seq不连续的请求
3. 当收到期望的seq时，处理该请求并递增`next_expected_seq`
4. 检查`pending_requests`中是否有后续连续的请求，如果有则依次处理

### 异步处理

所有方法都是异步的（async/await），支持：

- 非阻塞的请求处理
- 并发处理多个请求（通过asyncio）
- 与其他异步组件（如数据库、LLM调用）的集成

### 线程安全

使用`asyncio.Lock`确保请求队列的线程安全：

- `processing_lock`保护队列操作
- 防止并发修改`request_queue`和`pending_requests`

## 测试

运行单元测试：

```bash
# 测试基础IPC功能
python -m pytest tests/wayfare/test_ipc.py -v

# 测试parse集成功能
python -m pytest tests/wayfare/test_ipc_parse_integration.py -v

# 测试annotate集成功能
python -m pytest tests/wayfare/test_ipc_annotate_integration.py -v

# 测试query集成功能
python -m pytest tests/wayfare/test_ipc_query_integration.py -v

# 测试behavior集成功能
python -m pytest tests/wayfare/test_ipc_behavior_integration.py -v
```

测试覆盖：

**基础功能:**
- ✅ 请求解析和验证
- ✅ 错误处理
- ✅ seq排序机制
- ✅ 所有支持的方法
- ✅ 参数验证
- ✅ 乱序请求处理

**Parse集成:**
- ✅ 异步parse请求处理
- ✅ 立即返回processing状态
- ✅ 后台异步解析
- ✅ 完成通知推送
- ✅ 失败通知推送
- ✅ 错误处理
- ✅ 并发parse请求
- ✅ 不阻塞其他请求

**Annotate集成:**
- ✅ 批注生成请求处理
- ✅ RAG上下文检索
- ✅ LLM批注生成
- ✅ 批注存储
- ✅ 错误处理

**Query集成:**
- ✅ 向量检索请求处理
- ✅ Embedding生成
- ✅ 相似度搜索
- ✅ 结果排序和过滤
- ✅ 错误处理

**Behavior集成:**
- ✅ 行为记录请求处理
- ✅ 页面停留时间跟踪
- ✅ 定期干预检查
- ✅ 主动干预推送
- ✅ 多页面并发跟踪
- ✅ 行为统计查询
- ✅ 错误处理

## 未来扩展

在后续阶段，IPC Handler将继续集成以下组件：

- ✅ **Phase 2 (已完成)**: 集成DocumentParser处理parse请求
- ✅ **Phase 3 (已完成)**: 集成AnnotationGenerator处理annotate请求
- ✅ **Phase 3 (已完成)**: 集成VectorStore处理query请求
- ✅ **Phase 7 (已完成)**: 集成BehaviorAnalyzer处理behavior请求
- **Phase 1**: 集成ConfigManager处理config请求

## 示例代码

完整的使用示例请参考：
- `examples/ipc_usage_example.py` - 基础IPC使用示例
- `examples/ipc_parse_integration_example.py` - Parse集成示例
- `examples/ipc_annotate_integration_example.py` - Annotate集成示例
- `examples/ipc_query_integration_example.py` - Query集成示例
- `examples/ipc_behavior_integration_example.py` - Behavior集成示例

## 参考

- 需求文档: `.kiro/specs/wayfare-mvp-backend/requirements.md`
- 设计文档: `.kiro/specs/wayfare-mvp-backend/design.md`
- 任务列表: `.kiro/specs/wayfare-mvp-backend/tasks.md`
