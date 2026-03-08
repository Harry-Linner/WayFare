"""
日志系统和错误处理使用示例

演示如何使用WayFare的日志系统和错误处理框架。
"""

import asyncio
from wayfare.logging import setup_logging, get_logger, StructuredLogger, LogContext
from wayfare.errors import (
    DocumentParseError,
    VectorSearchError,
    LLMGenerationError,
    ErrorMonitor,
    format_user_error,
    get_fallback_annotation,
)


# ============================================================================
# 示例1: 基础日志配置
# ============================================================================

def example_basic_logging():
    """示例：基础日志配置"""
    print("\n=== 示例1: 基础日志配置 ===")
    
    # 配置日志系统
    logger = setup_logging(
        log_dir=".wayfare",
        log_file="wayfare.log",
        file_level=10,  # DEBUG
        console_level=30  # WARNING
    )
    
    # 使用不同级别的日志
    logger.debug("这是调试信息（只写入文件）")
    logger.info("这是普通信息（只写入文件）")
    logger.warning("这是警告信息（文件和控制台）")
    logger.error("这是错误信息（文件和控制台）")
    logger.critical("这是严重错误（文件和控制台）")
    
    print("日志已写入 .wayfare/wayfare.log")


# ============================================================================
# 示例2: 结构化日志
# ============================================================================

def example_structured_logging():
    """示例：结构化日志记录"""
    print("\n=== 示例2: 结构化日志 ===")
    
    # 初始化日志系统
    setup_logging()
    
    # 创建结构化日志记录器
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
        doc_hash="abc123",
        status="completed"
    )
    
    # 记录操作执行
    structured_logger.log_operation(
        operation="parse_document",
        duration_ms=1234.56,
        success=True,
        doc_hash="abc123",
        segments=42
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
    
    print("结构化日志已记录")


# ============================================================================
# 示例3: 日志上下文管理器
# ============================================================================

async def example_log_context():
    """示例：使用日志上下文管理器"""
    print("\n=== 示例3: 日志上下文管理器 ===")
    
    # 初始化日志系统
    logger = setup_logging()
    
    # 成功的操作
    with LogContext(logger, "parse_document"):
        # 模拟文档解析
        await asyncio.sleep(0.1)
        print("文档解析成功")
    
    # 失败的操作
    try:
        with LogContext(logger, "generate_annotation"):
            # 模拟LLM调用失败
            await asyncio.sleep(0.05)
            raise LLMGenerationError("API timeout")
    except LLMGenerationError:
        print("批注生成失败（已记录日志）")
    
    print("日志上下文已记录执行时间")


# ============================================================================
# 示例4: 错误处理
# ============================================================================

async def example_error_handling():
    """示例：错误处理"""
    print("\n=== 示例4: 错误处理 ===")
    
    # 初始化日志系统
    logger = setup_logging()
    
    # 示例：文档解析错误
    try:
        raise DocumentParseError("/test/doc.pdf", "Invalid PDF format")
    except DocumentParseError as e:
        logger.error(f"文档解析失败: {e}")
        user_message = format_user_error(e)
        print(f"用户友好消息: {user_message}")
    
    # 示例：向量检索错误
    try:
        raise VectorSearchError("Qdrant connection failed")
    except VectorSearchError as e:
        logger.error(f"向量检索失败: {e}")
        user_message = format_user_error(e)
        print(f"用户友好消息: {user_message}")
    
    # 示例：LLM生成错误（使用降级策略）
    try:
        raise LLMGenerationError("API rate limit exceeded")
    except LLMGenerationError as e:
        logger.warning(f"LLM生成失败，使用降级策略: {e}")
        fallback = get_fallback_annotation("explanation")
        print(f"降级批注: {fallback}")


# ============================================================================
# 示例5: 错误监控
# ============================================================================

async def example_error_monitoring():
    """示例：错误监控"""
    print("\n=== 示例5: 错误监控 ===")
    
    # 初始化日志系统
    setup_logging()
    
    # 创建错误监控器
    error_monitor = ErrorMonitor(
        error_threshold=3,  # 3次错误触发告警
        time_window=60  # 60秒时间窗口
    )
    
    # 模拟错误发生
    print("模拟错误发生...")
    
    # 记录2次错误（未达到阈值）
    error_monitor.record_error("DocumentParseError")
    error_monitor.record_error("DocumentParseError")
    
    stats = error_monitor.get_error_stats()
    print(f"当前错误统计: {stats}")
    
    # 记录第3次错误（达到阈值，触发告警）
    print("记录第3次错误（将触发告警）...")
    error_monitor.record_error("DocumentParseError")
    
    stats = error_monitor.get_error_stats()
    print(f"告警后错误统计: {stats}")
    
    # 记录不同类型的错误
    error_monitor.record_error("VectorSearchError")
    error_monitor.record_error("LLMGenerationError")
    
    stats = error_monitor.get_error_stats()
    print(f"最终错误统计: {stats}")


# ============================================================================
# 示例6: 完整的错误处理流程
# ============================================================================

async def parse_document_with_error_handling(path: str, error_monitor: ErrorMonitor):
    """示例：带完整错误处理的文档解析"""
    logger = get_logger()
    
    with LogContext(logger, f"parse_document: {path}"):
        try:
            # 模拟文档解析
            if "corrupted" in path:
                raise DocumentParseError(path, "Invalid PDF format")
            
            # 模拟成功解析
            await asyncio.sleep(0.1)
            logger.info(f"文档解析成功: {path}")
            return {"status": "success", "doc_hash": "abc123"}
            
        except DocumentParseError as e:
            # 记录错误
            logger.error(f"文档解析失败: {e}")
            
            # 更新错误监控器
            error_monitor.record_error("DocumentParseError")
            
            # 返回用户友好的错误消息
            return {
                "status": "error",
                "message": format_user_error(e)
            }


async def example_complete_error_handling():
    """示例：完整的错误处理流程"""
    print("\n=== 示例6: 完整的错误处理流程 ===")
    
    # 初始化日志系统和错误监控器
    setup_logging()
    error_monitor = ErrorMonitor(error_threshold=3, time_window=60)
    
    # 解析正常文档
    result1 = await parse_document_with_error_handling("/docs/normal.pdf", error_monitor)
    print(f"结果1: {result1}")
    
    # 解析损坏的文档
    result2 = await parse_document_with_error_handling("/docs/corrupted.pdf", error_monitor)
    print(f"结果2: {result2}")
    
    # 查看错误统计
    stats = error_monitor.get_error_stats()
    print(f"错误统计: {stats}")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """运行所有示例"""
    print("=" * 60)
    print("WayFare 日志系统和错误处理使用示例")
    print("=" * 60)
    
    # 运行示例
    example_basic_logging()
    example_structured_logging()
    await example_log_context()
    await example_error_handling()
    await example_error_monitoring()
    await example_complete_error_handling()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("查看日志文件: .wayfare/wayfare.log")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
