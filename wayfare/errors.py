"""
错误处理模块

定义自定义异常类和错误处理工具，包括：
- 可恢复错误（DocumentParseError、VectorSearchError等）
- 不可恢复错误（ModelLoadError、DatabaseInitError等）
- 错误监控器（ErrorMonitor）
- 用户友好的错误消息转换
"""

import time
import logging
from typing import Dict, List, Type, Optional

logger = logging.getLogger("wayfare.errors")


# ============================================================================
# 可恢复错误 (Recoverable Errors)
# ============================================================================

class DocumentParseError(Exception):
    """
    文档解析失败
    
    当PDF或Markdown文档解析失败时抛出此异常。
    这是可恢复错误，系统可以继续运行。
    """
    
    def __init__(self, path: str, reason: str):
        """
        初始化文档解析错误
        
        Args:
            path: 文档路径
            reason: 失败原因
        """
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to parse document {path}: {reason}")


class VectorSearchError(Exception):
    """
    向量检索失败
    
    当Qdrant向量检索失败时抛出此异常。
    这是可恢复错误，可以返回空结果或使用降级策略。
    """
    pass


class LLMGenerationError(Exception):
    """
    LLM生成失败
    
    当LLM API调用失败或生成内容失败时抛出此异常。
    这是可恢复错误，可以使用降级策略返回预设文本。
    """
    pass


class DatabaseError(Exception):
    """
    数据库操作失败
    
    当SQLite数据库操作失败时抛出此异常。
    这是可恢复错误，但需要记录日志并向上层报告。
    """
    pass


class ValidationError(Exception):
    """
    数据验证失败
    
    当输入数据验证失败时抛出此异常。
    这是可恢复错误，应该向用户返回验证错误信息。
    """
    pass


# ============================================================================
# 不可恢复错误 (Unrecoverable Errors)
# ============================================================================

class ModelLoadError(Exception):
    """
    模型加载失败
    
    当ONNX模型加载失败时抛出此异常。
    这是不可恢复错误，系统应该记录日志并退出。
    """
    pass


class DatabaseInitError(Exception):
    """
    数据库初始化失败
    
    当SQLite数据库初始化失败时抛出此异常。
    这是不可恢复错误，系统应该记录日志并退出。
    """
    pass


class ConfigurationError(Exception):
    """
    配置错误
    
    当系统配置无效或缺失时抛出此异常。
    这是不可恢复错误，系统应该记录日志并退出。
    """
    pass


# ============================================================================
# 错误监控器
# ============================================================================

class ErrorMonitor:
    """
    错误监控器
    
    跟踪错误发生频率，当错误频率超过阈值时发送告警。
    MVP阶段仅记录日志，未来可以集成告警系统。
    """
    
    def __init__(self, error_threshold: int = 10, time_window: int = 600):
        """
        初始化错误监控器
        
        Args:
            error_threshold: 错误阈值，默认10次
            time_window: 时间窗口（秒），默认600秒（10分钟）
        """
        self.error_threshold = error_threshold
        self.time_window = time_window
        self.error_counts: Dict[str, List[float]] = {}
        self.logger = logging.getLogger("wayfare.errors.monitor")
    
    def record_error(self, error_type: str):
        """
        记录错误
        
        Args:
            error_type: 错误类型（通常是异常类名）
        """
        now = time.time()
        
        # 初始化错误类型的记录列表
        if error_type not in self.error_counts:
            self.error_counts[error_type] = []
        
        # 添加当前错误时间戳
        self.error_counts[error_type].append(now)
        
        # 清理过期记录（超出时间窗口）
        self.error_counts[error_type] = [
            t for t in self.error_counts[error_type]
            if now - t < self.time_window
        ]
        
        # 检查是否需要告警
        if len(self.error_counts[error_type]) >= self.error_threshold:
            self._send_alert(error_type)
    
    def _send_alert(self, error_type: str):
        """
        发送告警
        
        MVP阶段仅记录critical级别日志。
        未来可以集成邮件、Slack、钉钉等告警渠道。
        
        Args:
            error_type: 错误类型
        """
        count = len(self.error_counts.get(error_type, []))
        self.logger.critical(
            f"Alert: {error_type} occurred {count} times "
            f"in the last {self.time_window} seconds (threshold: {self.error_threshold})"
        )
        
        # 重置计数器，避免重复告警
        self.error_counts[error_type] = []
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        获取错误统计信息
        
        Returns:
            错误类型到计数的映射
        """
        now = time.time()
        stats = {}
        
        for error_type, timestamps in self.error_counts.items():
            # 只统计时间窗口内的错误
            recent_errors = [t for t in timestamps if now - t < self.time_window]
            stats[error_type] = len(recent_errors)
        
        return stats
    
    def reset(self):
        """重置所有错误计数"""
        self.error_counts.clear()


# ============================================================================
# 用户友好的错误消息转换
# ============================================================================

# 错误类型到用户友好消息的映射
USER_FRIENDLY_MESSAGES: Dict[Type[Exception], str] = {
    DocumentParseError: "无法解析文档，请检查文件格式是否正确。",
    VectorSearchError: "检索服务暂时不可用，请稍后重试。",
    LLMGenerationError: "AI助手暂时不可用，请稍后重试。",
    DatabaseError: "数据保存失败，请检查磁盘空间。",
    ValidationError: "输入数据格式不正确，请检查后重试。",
    ModelLoadError: "系统初始化失败，请联系技术支持。",
    DatabaseInitError: "数据库初始化失败，请联系技术支持。",
    ConfigurationError: "系统配置错误，请联系技术支持。",
}


def format_user_error(error: Exception) -> str:
    """
    将技术错误转换为用户友好的消息
    
    Args:
        error: 异常对象
        
    Returns:
        用户友好的错误消息
    """
    error_type = type(error)
    
    # 查找匹配的错误消息
    user_message = USER_FRIENDLY_MESSAGES.get(error_type)
    
    if user_message:
        return user_message
    
    # 未知错误类型，返回通用消息
    return "发生未知错误，请联系技术支持。"


def get_fallback_annotation(annotation_type: str) -> str:
    """
    获取降级批注内容
    
    当LLM生成失败时，返回预设的降级文本。
    
    Args:
        annotation_type: 批注类型（explanation/question/summary）
        
    Returns:
        降级批注内容
    """
    fallbacks = {
        "explanation": "AI助手暂时不可用，请稍后重试。",
        "question": "思考一下：这段内容的核心概念是什么？",
        "summary": "请尝试用自己的话总结这段内容。"
    }
    
    return fallbacks.get(annotation_type, "AI助手暂时不可用。")


# ============================================================================
# 错误处理装饰器
# ============================================================================

def handle_errors(error_monitor: Optional[ErrorMonitor] = None):
    """
    错误处理装饰器
    
    自动捕获异常、记录日志、更新错误监控器。
    
    Args:
        error_monitor: 错误监控器实例（可选）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 记录日志
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                
                # 更新错误监控器
                if error_monitor:
                    error_monitor.record_error(type(e).__name__)
                
                # 重新抛出异常
                raise
        
        return wrapper
    return decorator
