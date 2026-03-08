"""
日志系统模块

配置WayFare的日志系统，支持：
- 文件和控制台双输出
- RotatingFileHandler自动日志轮转
- 按严重程度分级记录
- 结构化日志格式
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_dir: str = ".wayfare",
    log_file: str = "wayfare.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    file_level: int = logging.INFO,
    console_level: int = logging.WARNING,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    配置WayFare日志系统
    
    创建一个logger，支持文件和控制台双输出：
    - 文件输出：INFO级别及以上，自动轮转（10MB，保留5个备份）
    - 控制台输出：WARNING级别及以上，输出到stderr（避免干扰IPC）
    
    Args:
        log_dir: 日志目录，默认为.wayfare
        log_file: 日志文件名，默认为wayfare.log
        max_bytes: 单个日志文件最大大小（字节），默认10MB
        backup_count: 保留的备份文件数量，默认5个
        file_level: 文件日志级别，默认INFO
        console_level: 控制台日志级别，默认WARNING
        log_format: 日志格式字符串，默认为标准格式
        
    Returns:
        配置好的logger对象
    """
    # 创建logger
    logger = logging.getLogger("wayfare")
    logger.setLevel(logging.DEBUG)  # 设置为最低级别，由handler控制实际输出
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 确保日志目录存在
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(log_format)
    
    # 文件handler（自动轮转）
    file_handler = RotatingFileHandler(
        filename=log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台handler（输出到stderr，避免干扰IPC的stdout）
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 记录初始化信息
    logger.info(f"Logging initialized: file={log_path / log_file}, level={logging.getLevelName(file_level)}")
    
    return logger


def get_logger(name: str = "wayfare") -> logging.Logger:
    """
    获取logger实例
    
    Args:
        name: logger名称，默认为"wayfare"
        
    Returns:
        logger对象
    """
    return logging.getLogger(name)


def set_log_level(level: int, handler_type: Optional[str] = None):
    """
    动态设置日志级别
    
    Args:
        level: 日志级别（logging.DEBUG, INFO, WARNING, ERROR, CRITICAL）
        handler_type: handler类型（"file"或"console"），None表示设置所有handler
    """
    logger = logging.getLogger("wayfare")
    
    if handler_type is None:
        # 设置所有handler的级别
        for handler in logger.handlers:
            handler.setLevel(level)
    else:
        # 设置特定类型的handler
        for handler in logger.handlers:
            if handler_type == "file" and isinstance(handler, RotatingFileHandler):
                handler.setLevel(level)
            elif handler_type == "console" and isinstance(handler, logging.StreamHandler):
                if not isinstance(handler, RotatingFileHandler):  # 排除RotatingFileHandler
                    handler.setLevel(level)
    
    logger.info(f"Log level changed to {logging.getLevelName(level)} for {handler_type or 'all handlers'}")


def shutdown_logging():
    """
    关闭日志系统
    
    清理所有handler，确保日志文件正确关闭。
    """
    logger = logging.getLogger("wayfare")
    
    # 记录关闭信息
    logger.info("Shutting down logging system")
    
    # 关闭所有handler
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


# ============================================================================
# 结构化日志工具
# ============================================================================

class StructuredLogger:
    """
    结构化日志记录器
    
    提供结构化的日志记录方法，便于日志分析和监控。
    """
    
    def __init__(self, logger_name: str = "wayfare"):
        """
        初始化结构化日志记录器
        
        Args:
            logger_name: logger名称
        """
        self.logger = logging.getLogger(logger_name)
    
    def log_request(self, method: str, request_id: str, seq: int, **kwargs):
        """
        记录IPC请求
        
        Args:
            method: 请求方法
            request_id: 请求ID
            seq: 序列号
            **kwargs: 额外的请求参数
        """
        self.logger.info(
            f"IPC Request: method={method}, id={request_id}, seq={seq}, params={kwargs}"
        )
    
    def log_response(self, request_id: str, seq: int, success: bool, **kwargs):
        """
        记录IPC响应
        
        Args:
            request_id: 请求ID
            seq: 序列号
            success: 是否成功
            **kwargs: 额外的响应数据
        """
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"IPC Response: id={request_id}, seq={seq}, success={success}, data={kwargs}"
        )
    
    def log_operation(self, operation: str, duration_ms: float, success: bool, **kwargs):
        """
        记录操作执行
        
        Args:
            operation: 操作名称
            duration_ms: 执行时间（毫秒）
            success: 是否成功
            **kwargs: 额外的操作信息
        """
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"Operation: name={operation}, duration={duration_ms:.2f}ms, "
            f"success={success}, details={kwargs}"
        )
    
    def log_error(self, error_type: str, error_message: str, **kwargs):
        """
        记录错误
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            **kwargs: 额外的错误信息
        """
        self.logger.error(
            f"Error: type={error_type}, message={error_message}, details={kwargs}"
        )
    
    def log_metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """
        记录性能指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            unit: 单位
            **kwargs: 额外的指标信息
        """
        self.logger.info(
            f"Metric: name={metric_name}, value={value}{unit}, details={kwargs}"
        )


# ============================================================================
# 日志上下文管理器
# ============================================================================

class LogContext:
    """
    日志上下文管理器
    
    用于记录操作的开始和结束，自动计算执行时间。
    """
    
    def __init__(self, logger: logging.Logger, operation: str, level: int = logging.INFO):
        """
        初始化日志上下文
        
        Args:
            logger: logger对象
            operation: 操作名称
            level: 日志级别
        """
        self.logger = logger
        self.operation = operation
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        """进入上下文"""
        import time
        self.start_time = time.time()
        self.logger.log(self.level, f"Starting: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        import time
        duration = (time.time() - self.start_time) * 1000  # 转换为毫秒
        
        if exc_type is None:
            self.logger.log(self.level, f"Completed: {self.operation} ({duration:.2f}ms)")
        else:
            self.logger.error(
                f"Failed: {self.operation} ({duration:.2f}ms) - {exc_type.__name__}: {exc_val}"
            )
        
        # 不抑制异常
        return False
