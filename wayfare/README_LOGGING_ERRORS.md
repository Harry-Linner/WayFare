# WayFare 日志系统和错误处理框架

本文档介绍WayFare的日志系统和错误处理框架的设计、使用方法和最佳实践。

## 目录

- [概述](#概述)
- [日志系统](#日志系统)
  - [基础配置](#基础配置)
  - [结构化日志](#结构化日志)
  - [日志上下文管理器](#日志上下文管理器)
- [错误处理](#错误处理)
  - [自定义异常类](#自定义异常类)
  - [错误监控器](#错误监控器)
  - [用户友好的错误消息](#用户友好的错误消息)
- [最佳实践](#最佳实践)
- [示例代码](#示例代码)

## 概述

WayFare的日志系统和错误处理框架提供了完整的日志记录和错误管理能力：

- **日志系统**：支持文件和控制台双输出、自动日志轮转、结构化日志记录
- **错误处理**：定义了可恢复和不可恢复错误、错误监控、用户友好的错误消息转换

## 日志系统

### 基础配置

使用`setup_logging()`函数配置日志系统：

```python
from wayfare.logging import setup_logging

# 基础配置
logger = setup_logging()

# 自定义配置
logger = setup_logging(
    log_dir=".wayfare",           # 日志目录
    log_file="wayfare.log",       # 日志文件名
    max_bytes=10*1024*1024,       # 单个文件最大10MB
    backup_count=5,               # 保留5个备份文件
    file_level=logging.INFO,      # 文件日志级别
    console_level=logging.WARNING # 控制台日志级别
)
```

**特性**：

- **双输出**：同时输出到文件和控制台（stderr）
- **自动轮转**：使用`RotatingFileHandler`，文件达到最大大小时自动轮转
- **级别控制**：文件和控制台可以设置不同的日志级别
- **避免IPC干扰**：控制台输出到stderr，不影响stdout的IPC通信

### 日志级别

```python
logger.debug("详细的调试信息")
logger.info("普通的运行信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

**默认配置**：
- 文件：INFO级别及以上
- 控制台：WARNING级别及以上

### 动态调整日志级别

```python
from wayfare.logging import set_log_level
import logging

# 设置所有handler为DEBUG级别
set_log_level(logging.DEBUG)

# 只设置文件handler
set_log_level(logging.DEBUG, handler_type="file")

# 只设置控制台handler
set_log_level(logging.ERROR, handler_type="console")
```

### 结构化日志

使用`StructuredLogger`记录结构化的日志信息：

```python
from wayfare.logging import StructuredLogger

structured_logger = StructuredLogger()

# 记录IPC请求
structured_logger.log_request(
    method="parse",
    request_id="req-123",
    seq=1,
    path="/documents/test.pdf"
)

# 记录IPC响应
structured_logger.log_response(
    request_id="req-123",
    seq=1,
    success=True,
    doc_hash="abc123"
)

# 记录操作执行
structured_logger.log_operation(
    operation="parse_document",
    duration_ms=1234.56,
    success=True,
    doc_hash="abc123"
)

# 记录错误
structured_logger.log_error(
    error_type="DocumentParseError",
    error_message="Invalid PDF format",
    path="/documents/corrupted.pdf"
)

# 记录性能指标
structured_logger.log_metric(
    metric_name="parse_duration",
    value=1234.56,
    unit="ms",
    doc_type="pdf"
)
```

### 日志上下文管理器

使用`LogContext`自动记录操作的开始、结束和执行时间：

```python
from wayfare.logging import LogContext, get_logger

logger = get_logger()

# 成功的操作
with LogContext(logger, "parse_document"):
    # 执行文档解析
    result = await parse_document(path)

# 失败的操作（自动记录异常）
try:
    with LogContext(logger, "generate_annotation"):
        result = await generate_annotation(doc_hash)
except Exception as e:
    # 异常已被LogContext记录
    pass
```

**输出示例**：
```
2024-01-15 10:30:00 - wayfare - INFO - Starting: parse_document
2024-01-15 10:30:01 - wayfare - INFO - Completed: parse_document (1234.56ms)
```

## 错误处理

### 自定义异常类

WayFare定义了两类错误：

#### 1. 可恢复错误 (Recoverable Errors)

这些错误不会导致系统崩溃，可以向用户返回错误信息并继续运行。

```python
from wayfare.errors import (
    DocumentParseError,
    VectorSearchError,
    LLMGenerationError,
    DatabaseError,
    ValidationError
)

# 文档解析错误
try:
    result = await parse_pdf(path)
except DocumentParseError as e:
    logger.error(f"文档解析失败: {e}")
    return {"success": False, "error": str(e)}

# 向量检索错误（可以返回空结果）
try:
    results = await vector_store.search(query)
except VectorSearchError as e:
    logger.warning(f"检索失败，返回空结果: {e}")
    results = []

# LLM生成错误（可以使用降级策略）
try:
    annotation = await llm.generate(context)
except LLMGenerationError as e:
    logger.warning(f"LLM生成失败，使用降级策略: {e}")
    annotation = get_fallback_annotation("explanation")
```

#### 2. 不可恢复错误 (Unrecoverable Errors)

这些错误表示系统配置或环境问题，需要记录日志并优雅退出。

```python
from wayfare.errors import (
    ModelLoadError,
    DatabaseInitError,
    ConfigurationError
)

# 模型加载错误
try:
    embedding_service = EmbeddingService(model_path)
except ModelLoadError as e:
    logger.critical(f"模型加载失败: {e}")
    sys.exit(1)

# 数据库初始化错误
try:
    await db.initialize()
except DatabaseInitError as e:
    logger.critical(f"数据库初始化失败: {e}")
    sys.exit(1)
```

### 错误监控器

使用`ErrorMonitor`跟踪错误发生频率，当错误频率超过阈值时发送告警：

```python
from wayfare.errors import ErrorMonitor

# 创建错误监控器
error_monitor = ErrorMonitor(
    error_threshold=10,  # 10次错误触发告警
    time_window=600      # 10分钟时间窗口
)

# 记录错误
try:
    result = await parse_document(path)
except DocumentParseError as e:
    logger.error(f"文档解析失败: {e}")
    error_monitor.record_error("DocumentParseError")

# 获取错误统计
stats = error_monitor.get_error_stats()
print(f"错误统计: {stats}")

# 重置错误计数
error_monitor.reset()
```

**告警机制**：
- 当某类错误在时间窗口内达到阈值时，自动记录CRITICAL级别日志
- 告警后自动重置计数器，避免重复告警
- MVP阶段仅记录日志，未来可以集成邮件、Slack等告警渠道

### 用户友好的错误消息

使用`format_user_error()`将技术错误转换为用户友好的消息：

```python
from wayfare.errors import format_user_error, DocumentParseError

try:
    result = await parse_document(path)
except DocumentParseError as e:
    # 技术错误消息
    logger.error(f"文档解析失败: {e}")
    
    # 用户友好消息
    user_message = format_user_error(e)
    # 输出: "无法解析文档，请检查文件格式是否正确。"
    
    return {"success": False, "message": user_message}
```

**错误消息映射**：

| 错误类型 | 用户友好消息 |
|---------|------------|
| DocumentParseError | 无法解析文档，请检查文件格式是否正确。 |
| VectorSearchError | 检索服务暂时不可用，请稍后重试。 |
| LLMGenerationError | AI助手暂时不可用，请稍后重试。 |
| DatabaseError | 数据保存失败，请检查磁盘空间。 |
| ValidationError | 输入数据格式不正确，请检查后重试。 |
| ModelLoadError | 系统初始化失败，请联系技术支持。 |
| DatabaseInitError | 数据库初始化失败，请联系技术支持。 |
| ConfigurationError | 系统配置错误，请联系技术支持。 |

### 降级策略

当LLM生成失败时，使用`get_fallback_annotation()`返回预设的降级文本：

```python
from wayfare.errors import get_fallback_annotation, LLMGenerationError

try:
    annotation = await llm.generate(context)
except LLMGenerationError as e:
    logger.warning(f"LLM生成失败，使用降级策略: {e}")
    annotation = get_fallback_annotation("explanation")
    # 返回: "AI助手暂时不可用，请稍后重试。"
```

**降级批注类型**：

| 批注类型 | 降级文本 |
|---------|---------|
| explanation | AI助手暂时不可用，请稍后重试。 |
| question | 思考一下：这段内容的核心概念是什么？ |
| summary | 请尝试用自己的话总结这段内容。 |

## 最佳实践

### 1. 日志记录原则

- **DEBUG**：详细的调试信息，仅在开发和调试时使用
- **INFO**：正常的运行信息，记录关键操作和状态变化
- **WARNING**：警告信息，表示潜在问题但不影响运行
- **ERROR**：错误信息，表示操作失败但系统可以继续运行
- **CRITICAL**：严重错误，表示系统可能无法继续运行

### 2. 错误处理策略

#### IPC层错误处理

所有IPC请求的错误都应该被捕获并转换为标准的错误响应：

```python
async def handle_request(self, raw_message: str) -> str:
    try:
        request = self._parse_request(raw_message)
        response = await self._route_request(request)
        return self._serialize_response(response)
    except json.JSONDecodeError as e:
        return self._error_response("Invalid JSON format")
    except ValidationError as e:
        return self._error_response(f"Invalid request: {e}")
    except Exception as e:
        logger.exception("Unexpected error handling request")
        return self._error_response("Internal server error")
```

#### 异步任务错误处理

对于异步执行的任务，错误应该被记录并通过主动推送通知前端：

```python
async def _async_parse(self, path: str, doc_hash: str):
    try:
        result = await self.doc_parser.parse_document(path)
        await self._send_notification({
            "type": "parse_completed",
            "docHash": doc_hash,
            "status": "completed"
        })
    except DocumentParseError as e:
        logger.error(f"Parse failed for {path}: {e}")
        await self.db.update_document_status(doc_hash, "failed")
        await self._send_notification({
            "type": "parse_failed",
            "docHash": doc_hash,
            "error": format_user_error(e),
            "status": "failed"
        })
```

#### 外部服务错误处理

对于外部服务（Qdrant、LLM API），应该实现重试机制和降级策略：

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def search_with_retry(self, query_vector: np.ndarray):
    """带重试的向量检索"""
    try:
        return await self.vector_store.search(query_vector)
    except Exception as e:
        logger.warning(f"Vector search attempt failed: {e}")
        raise VectorSearchError(f"Search failed: {e}")
```

### 3. 日志文件管理

- **位置**：`.wayfare/wayfare.log`
- **大小**：单个文件最大10MB
- **备份**：保留5个备份文件（wayfare.log.1 ~ wayfare.log.5）
- **编码**：UTF-8
- **格式**：`时间 - 模块 - 级别 - 消息`

### 4. 性能考虑

- 避免在循环中记录大量DEBUG日志
- 使用结构化日志记录关键操作
- 定期清理旧的日志文件
- 在生产环境中提高日志级别（INFO或WARNING）

## 示例代码

完整的使用示例请参考：`examples/logging_error_usage_example.py`

### 快速开始

```python
from wayfare.logging import setup_logging, LogContext
from wayfare.errors import DocumentParseError, format_user_error, ErrorMonitor

# 1. 初始化日志系统
logger = setup_logging()

# 2. 创建错误监控器
error_monitor = ErrorMonitor(error_threshold=10, time_window=600)

# 3. 使用日志上下文记录操作
async def parse_document(path: str):
    with LogContext(logger, f"parse_document: {path}"):
        try:
            # 执行文档解析
            result = await do_parse(path)
            logger.info(f"文档解析成功: {path}")
            return {"success": True, "result": result}
        except DocumentParseError as e:
            # 记录错误
            logger.error(f"文档解析失败: {e}")
            
            # 更新错误监控器
            error_monitor.record_error("DocumentParseError")
            
            # 返回用户友好的错误消息
            return {
                "success": False,
                "message": format_user_error(e)
            }
```

## 测试

运行测试：

```bash
# 测试日志系统
pytest tests/wayfare/test_logging.py -v

# 测试错误处理
pytest tests/wayfare/test_errors.py -v

# 运行所有测试
pytest tests/wayfare/ -v
```

## 相关文档

- [配置管理](./README_CONFIG.md)
- [数据库系统](./README_DB.md)
- [IPC通信](./README_IPC.md)
