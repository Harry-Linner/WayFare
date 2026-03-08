# Task 1.7 实现总结：日志系统和错误处理框架

## 任务概述

实现了WayFare MVP Backend的日志系统和错误处理框架，包括：
- 配置logging模块，支持文件和控制台输出
- 实现RotatingFileHandler，日志文件自动轮转
- 定义自定义异常类（DocumentParseError、VectorSearchError等）
- 实现错误监控器ErrorMonitor类
- 实现用户友好的错误消息转换函数

## 实现内容

### 1. 日志系统 (`wayfare/logging.py`)

#### 核心功能

**setup_logging()**
- 配置双输出：文件（INFO级别）和控制台（WARNING级别）
- 使用RotatingFileHandler实现自动日志轮转（10MB，保留5个备份）
- 控制台输出到stderr，避免干扰IPC的stdout通信
- 支持自定义日志目录、文件名、大小、备份数量和日志级别

**get_logger()**
- 获取logger实例
- 支持自定义logger名称

**set_log_level()**
- 动态调整日志级别
- 支持分别设置文件和控制台handler的级别

**shutdown_logging()**
- 优雅关闭日志系统
- 清理所有handler，确保日志文件正确关闭

#### 高级功能

**StructuredLogger类**
- 提供结构化的日志记录方法
- `log_request()`: 记录IPC请求
- `log_response()`: 记录IPC响应
- `log_operation()`: 记录操作执行和耗时
- `log_error()`: 记录错误信息
- `log_metric()`: 记录性能指标

**LogContext上下文管理器**
- 自动记录操作的开始和结束
- 自动计算执行时间
- 自动捕获和记录异常

### 2. 错误处理 (`wayfare/errors.py`)

#### 可恢复错误 (Recoverable Errors)

这些错误不会导致系统崩溃，可以向用户返回错误信息并继续运行：

- **DocumentParseError**: 文档解析失败
  - 属性：path（文档路径）、reason（失败原因）
- **VectorSearchError**: 向量检索失败
- **LLMGenerationError**: LLM生成失败
- **DatabaseError**: 数据库操作失败
- **ValidationError**: 数据验证失败

#### 不可恢复错误 (Unrecoverable Errors)

这些错误表示系统配置或环境问题，需要记录日志并优雅退出：

- **ModelLoadError**: ONNX模型加载失败
- **DatabaseInitError**: 数据库初始化失败
- **ConfigurationError**: 配置错误

#### 错误监控器 (ErrorMonitor)

**核心功能**：
- 跟踪错误发生频率
- 当错误频率超过阈值时发送告警
- 支持时间窗口内的错误统计
- 自动清理过期的错误记录

**主要方法**：
- `record_error(error_type)`: 记录错误
- `get_error_stats()`: 获取错误统计信息
- `reset()`: 重置所有错误计数
- `_send_alert(error_type)`: 发送告警（MVP阶段记录CRITICAL日志）

#### 用户友好的错误消息

**format_user_error(error)**
- 将技术错误转换为用户友好的消息
- 支持所有自定义异常类型
- 未知错误返回通用消息

**get_fallback_annotation(annotation_type)**
- 获取降级批注内容
- 当LLM生成失败时使用
- 支持三种批注类型：explanation、question、summary

### 3. 测试 (`tests/wayfare/`)

#### test_logging.py (26个测试)

**TestSetupLogging** (7个测试)
- ✅ 创建logger
- ✅ 创建日志文件
- ✅ 创建日志目录
- ✅ 文件handler日志级别
- ✅ 控制台handler日志级别
- ✅ 自定义日志格式
- ✅ 幂等性（重复调用不重复添加handler）

**TestGetLogger** (3个测试)
- ✅ 获取默认名称的logger
- ✅ 获取自定义名称的logger
- ✅ 返回同一实例

**TestSetLogLevel** (3个测试)
- ✅ 设置所有handler的日志级别
- ✅ 只设置文件handler
- ✅ 只设置控制台handler

**TestShutdownLogging** (2个测试)
- ✅ 移除所有handler
- ✅ 关闭所有handler

**TestLoggingOutput** (2个测试)
- ✅ 日志写入文件
- ✅ 不同日志级别

**TestRotatingFileHandler** (1个测试)
- ✅ 日志文件轮转

**TestStructuredLogger** (5个测试)
- ✅ 记录IPC请求
- ✅ 记录IPC响应
- ✅ 记录操作执行
- ✅ 记录错误
- ✅ 记录性能指标

**TestLogContext** (3个测试)
- ✅ 成功操作的日志上下文
- ✅ 失败操作的日志上下文
- ✅ 记录执行时间

#### test_errors.py (40个测试)

**TestRecoverableErrors** (5个测试)
- ✅ DocumentParseError
- ✅ VectorSearchError
- ✅ LLMGenerationError
- ✅ DatabaseError
- ✅ ValidationError

**TestUnrecoverableErrors** (3个测试)
- ✅ ModelLoadError
- ✅ DatabaseInitError
- ✅ ConfigurationError

**TestErrorMonitor** (9个测试)
- ✅ 初始化
- ✅ 记录错误
- ✅ 记录多个错误
- ✅ 错误阈值告警
- ✅ 错误时间窗口清理
- ✅ 获取错误统计
- ✅ 获取错误统计（包含过期错误）
- ✅ 重置
- ✅ 告警记录critical日志
- ✅ 告警后重置计数器

**TestFormatUserError** (9个测试)
- ✅ 所有错误类型的用户友好消息转换

**TestGetFallbackAnnotation** (4个测试)
- ✅ explanation类型的降级批注
- ✅ question类型的降级批注
- ✅ summary类型的降级批注
- ✅ 未知类型的降级批注

**TestErrorInheritance** (2个测试)
- ✅ 可恢复错误继承自Exception
- ✅ 不可恢复错误继承自Exception

**TestErrorRaising** (4个测试)
- ✅ 抛出和捕获各种错误

**TestErrorMonitorIntegration** (3个测试)
- ✅ 监控多种错误类型
- ✅ 真实时间窗口的错误监控
- ✅ 并发错误记录

### 4. 文档和示例

#### README_LOGGING_ERRORS.md
- 完整的使用文档
- 包含概述、日志系统、错误处理、最佳实践
- 提供详细的API说明和代码示例

#### logging_error_usage_example.py
- 6个完整的使用示例
- 演示所有核心功能
- 可直接运行查看效果

### 5. 集成到wayfare包

更新了`wayfare/__init__.py`，导出所有日志和错误处理相关的类和函数：

**日志系统**：
- setup_logging
- get_logger
- set_log_level
- shutdown_logging
- StructuredLogger
- LogContext

**错误处理**：
- 所有自定义异常类
- ErrorMonitor
- format_user_error
- get_fallback_annotation

## 设计特点

### 1. 符合设计文档

完全按照`.kiro/specs/wayfare-mvp-backend/design.md`中的错误处理章节实现：
- 错误分类（可恢复/不可恢复）
- 日志策略（RotatingFileHandler、分级记录）
- 错误监控和告警
- 用户友好的错误消息

### 2. 遵循项目模式

- 使用Pydantic风格的类型注解
- 遵循现有的代码结构和命名规范
- 与config、db、ipc模块保持一致的设计风格

### 3. 生产就绪

- 完整的单元测试覆盖（66个测试，100%通过）
- 详细的文档和使用示例
- 考虑了性能和资源管理
- 支持动态配置和扩展

### 4. 易于使用

- 简洁的API设计
- 合理的默认配置
- 丰富的使用示例
- 清晰的文档说明

## 文件清单

### 核心实现
- `wayfare/logging.py` - 日志系统实现（约250行）
- `wayfare/errors.py` - 错误处理实现（约280行）

### 测试
- `tests/wayfare/test_logging.py` - 日志系统测试（26个测试，约400行）
- `tests/wayfare/test_errors.py` - 错误处理测试（40个测试，约400行）

### 文档和示例
- `wayfare/README_LOGGING_ERRORS.md` - 完整使用文档（约600行）
- `examples/logging_error_usage_example.py` - 使用示例（约350行）

### 集成
- `wayfare/__init__.py` - 更新导出列表

## 测试结果

```bash
# 日志系统测试
pytest tests/wayfare/test_logging.py -v
# 结果: 26 passed

# 错误处理测试
pytest tests/wayfare/test_errors.py -v
# 结果: 40 passed

# 总计: 66 passed
```

## 使用示例

### 基础日志配置

```python
from wayfare.logging import setup_logging

# 配置日志系统
logger = setup_logging()

# 使用日志
logger.info("文档解析成功")
logger.error("文档解析失败")
```

### 结构化日志

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
```

### 日志上下文

```python
from wayfare.logging import LogContext, get_logger

logger = get_logger()

with LogContext(logger, "parse_document"):
    # 执行文档解析
    result = await parse_document(path)
```

### 错误处理

```python
from wayfare.errors import DocumentParseError, format_user_error

try:
    result = await parse_document(path)
except DocumentParseError as e:
    logger.error(f"文档解析失败: {e}")
    user_message = format_user_error(e)
    return {"success": False, "message": user_message}
```

### 错误监控

```python
from wayfare.errors import ErrorMonitor

error_monitor = ErrorMonitor(error_threshold=10, time_window=600)

try:
    result = await parse_document(path)
except DocumentParseError as e:
    logger.error(f"文档解析失败: {e}")
    error_monitor.record_error("DocumentParseError")
```

## 后续集成

这个日志系统和错误处理框架将在后续任务中被集成到：

1. **Document_Parser** (Task 2.1-2.3)
   - 使用DocumentParseError处理解析错误
   - 使用LogContext记录解析操作
   - 使用ErrorMonitor监控解析失败

2. **Embedding_Service** (Task 3.1)
   - 使用ModelLoadError处理模型加载失败
   - 使用日志记录推理性能

3. **Vector_Store** (Task 3.2)
   - 使用VectorSearchError处理检索失败
   - 使用日志记录检索操作

4. **Annotation_Generator** (Task 4.1-4.3)
   - 使用LLMGenerationError处理生成失败
   - 使用get_fallback_annotation实现降级策略
   - 使用LogContext记录批注生成

5. **IPC_Handler** (Task 1.5, 2.4, 4.4, 5.2)
   - 使用format_user_error转换错误消息
   - 使用StructuredLogger记录IPC请求/响应
   - 使用ValidationError处理请求验证失败

## 总结

Task 1.7已完成，实现了完整的日志系统和错误处理框架：

✅ 配置logging模块，支持文件和控制台输出
✅ 实现RotatingFileHandler，日志文件自动轮转
✅ 定义自定义异常类（8个异常类）
✅ 实现错误监控器ErrorMonitor类
✅ 实现用户友好的错误消息转换函数
✅ 实现结构化日志记录器
✅ 实现日志上下文管理器
✅ 编写完整的单元测试（66个测试）
✅ 编写详细的使用文档
✅ 提供完整的使用示例

所有功能已实现并通过测试，可以在后续任务中使用。
