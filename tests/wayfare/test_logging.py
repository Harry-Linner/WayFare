"""
日志系统测试

测试logging模块的功能，包括：
- 日志配置和初始化
- 文件和控制台输出
- RotatingFileHandler日志轮转
- 结构化日志记录
- 日志上下文管理器
"""

import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from wayfare.logging import (
    setup_logging,
    get_logger,
    set_log_level,
    shutdown_logging,
    StructuredLogger,
    LogContext
)


@pytest.fixture
def temp_log_dir():
    """创建临时日志目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 清理
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def clean_logger():
    """清理logger的handlers"""
    logger = logging.getLogger("wayfare")
    # 保存原始handlers
    original_handlers = logger.handlers[:]
    
    yield logger
    
    # 恢复原始状态
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    for handler in original_handlers:
        logger.addHandler(handler)


class TestSetupLogging:
    """测试日志配置和初始化"""
    
    def test_setup_logging_creates_logger(self, temp_log_dir, clean_logger):
        """测试setup_logging创建logger"""
        logger = setup_logging(log_dir=temp_log_dir)
        
        assert logger is not None
        assert logger.name == "wayfare"
        assert len(logger.handlers) == 2  # 文件和控制台handler
    
    def test_setup_logging_creates_log_file(self, temp_log_dir, clean_logger):
        """测试setup_logging创建日志文件"""
        setup_logging(log_dir=temp_log_dir, log_file="test.log")
        
        log_file = Path(temp_log_dir) / "test.log"
        assert log_file.exists()
    
    def test_setup_logging_creates_directory(self, temp_log_dir, clean_logger):
        """测试setup_logging创建日志目录"""
        log_dir = Path(temp_log_dir) / "nested" / "logs"
        setup_logging(log_dir=str(log_dir))
        
        assert log_dir.exists()
    
    def test_setup_logging_file_handler_level(self, temp_log_dir, clean_logger):
        """测试文件handler的日志级别"""
        logger = setup_logging(log_dir=temp_log_dir, file_level=logging.DEBUG)
        
        file_handler = None
        for handler in logger.handlers:
            if hasattr(handler, 'baseFilename'):
                file_handler = handler
                break
        
        assert file_handler is not None
        assert file_handler.level == logging.DEBUG
    
    def test_setup_logging_console_handler_level(self, temp_log_dir, clean_logger):
        """测试控制台handler的日志级别"""
        logger = setup_logging(log_dir=temp_log_dir, console_level=logging.ERROR)
        
        console_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, 'baseFilename'):
                console_handler = handler
                break
        
        assert console_handler is not None
        assert console_handler.level == logging.ERROR
    
    def test_setup_logging_custom_format(self, temp_log_dir, clean_logger):
        """测试自定义日志格式"""
        custom_format = '%(levelname)s - %(message)s'
        logger = setup_logging(log_dir=temp_log_dir, log_format=custom_format)
        
        # 检查formatter
        for handler in logger.handlers:
            assert handler.formatter._fmt == custom_format
    
    def test_setup_logging_idempotent(self, temp_log_dir, clean_logger):
        """测试重复调用setup_logging不会重复添加handler"""
        logger1 = setup_logging(log_dir=temp_log_dir)
        handler_count1 = len(logger1.handlers)
        
        logger2 = setup_logging(log_dir=temp_log_dir)
        handler_count2 = len(logger2.handlers)
        
        assert handler_count1 == handler_count2
        assert logger1 is logger2


class TestGetLogger:
    """测试获取logger"""
    
    def test_get_logger_default_name(self):
        """测试获取默认名称的logger"""
        logger = get_logger()
        assert logger.name == "wayfare"
    
    def test_get_logger_custom_name(self):
        """测试获取自定义名称的logger"""
        logger = get_logger("wayfare.test")
        assert logger.name == "wayfare.test"
    
    def test_get_logger_returns_same_instance(self):
        """测试多次获取返回同一实例"""
        logger1 = get_logger("wayfare.test")
        logger2 = get_logger("wayfare.test")
        assert logger1 is logger2


class TestSetLogLevel:
    """测试动态设置日志级别"""
    
    def test_set_log_level_all_handlers(self, temp_log_dir, clean_logger):
        """测试设置所有handler的日志级别"""
        logger = setup_logging(log_dir=temp_log_dir)
        set_log_level(logging.DEBUG)
        
        for handler in logger.handlers:
            assert handler.level == logging.DEBUG
    
    def test_set_log_level_file_handler(self, temp_log_dir, clean_logger):
        """测试只设置文件handler的日志级别"""
        logger = setup_logging(log_dir=temp_log_dir)
        set_log_level(logging.DEBUG, handler_type="file")
        
        for handler in logger.handlers:
            if hasattr(handler, 'baseFilename'):
                assert handler.level == logging.DEBUG
    
    def test_set_log_level_console_handler(self, temp_log_dir, clean_logger):
        """测试只设置控制台handler的日志级别"""
        logger = setup_logging(log_dir=temp_log_dir)
        set_log_level(logging.CRITICAL, handler_type="console")
        
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, 'baseFilename'):
                assert handler.level == logging.CRITICAL


class TestShutdownLogging:
    """测试关闭日志系统"""
    
    def test_shutdown_logging_removes_handlers(self, temp_log_dir, clean_logger):
        """测试shutdown_logging移除所有handler"""
        logger = setup_logging(log_dir=temp_log_dir)
        assert len(logger.handlers) > 0
        
        shutdown_logging()
        assert len(logger.handlers) == 0
    
    def test_shutdown_logging_closes_handlers(self, temp_log_dir, clean_logger):
        """测试shutdown_logging关闭所有handler"""
        logger = setup_logging(log_dir=temp_log_dir)
        handlers = logger.handlers[:]
        
        shutdown_logging()
        
        # 验证文件handler已关闭
        for handler in handlers:
            if hasattr(handler, 'baseFilename'):  # RotatingFileHandler
                # 文件handler应该被关闭
                assert handler.stream is None or handler.stream.closed


class TestLoggingOutput:
    """测试日志输出"""
    
    def test_log_to_file(self, temp_log_dir, clean_logger):
        """测试日志写入文件"""
        logger = setup_logging(log_dir=temp_log_dir, log_file="test.log")
        
        test_message = "Test log message"
        logger.info(test_message)
        
        # 刷新handler
        for handler in logger.handlers:
            handler.flush()
        
        # 读取日志文件
        log_file = Path(temp_log_dir) / "test.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert test_message in content
    
    def test_log_levels(self, temp_log_dir, clean_logger):
        """测试不同日志级别"""
        logger = setup_logging(log_dir=temp_log_dir, file_level=logging.DEBUG)
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # 刷新handler
        for handler in logger.handlers:
            handler.flush()
        
        # 读取日志文件
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
        assert "Critical message" in content


class TestRotatingFileHandler:
    """测试日志轮转"""
    
    def test_log_rotation(self, temp_log_dir, clean_logger):
        """测试日志文件轮转"""
        # 设置小的文件大小以触发轮转
        max_bytes = 1024  # 1KB
        logger = setup_logging(
            log_dir=temp_log_dir,
            log_file="rotate.log",
            max_bytes=max_bytes,
            backup_count=2
        )
        
        # 写入大量日志触发轮转
        for i in range(100):
            logger.info(f"Log message {i} " + "x" * 100)
        
        # 刷新handler
        for handler in logger.handlers:
            handler.flush()
        
        # 检查是否生成了备份文件
        log_dir = Path(temp_log_dir)
        log_files = list(log_dir.glob("rotate.log*"))
        
        # 应该有主文件和至少一个备份文件
        assert len(log_files) >= 2


class TestStructuredLogger:
    """测试结构化日志记录器"""
    
    @pytest.fixture
    def structured_logger(self, temp_log_dir, clean_logger):
        """创建结构化日志记录器"""
        setup_logging(log_dir=temp_log_dir, file_level=logging.DEBUG)
        return StructuredLogger()
    
    def test_log_request(self, structured_logger, temp_log_dir):
        """测试记录IPC请求"""
        structured_logger.log_request(
            method="parse",
            request_id="test-id",
            seq=1,
            path="/test/doc.pdf"
        )
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "IPC Request" in content
        assert "method=parse" in content
        assert "id=test-id" in content
        assert "seq=1" in content
    
    def test_log_response(self, structured_logger, temp_log_dir):
        """测试记录IPC响应"""
        structured_logger.log_response(
            request_id="test-id",
            seq=1,
            success=True,
            result="completed"
        )
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "IPC Response" in content
        assert "id=test-id" in content
        assert "success=True" in content
    
    def test_log_operation(self, structured_logger, temp_log_dir):
        """测试记录操作执行"""
        structured_logger.log_operation(
            operation="parse_document",
            duration_ms=123.45,
            success=True,
            doc_hash="abc123"
        )
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "Operation" in content
        assert "name=parse_document" in content
        assert "duration=123.45ms" in content
        assert "success=True" in content
    
    def test_log_error(self, structured_logger, temp_log_dir):
        """测试记录错误"""
        structured_logger.log_error(
            error_type="DocumentParseError",
            error_message="Failed to parse PDF",
            path="/test/doc.pdf"
        )
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "Error" in content
        assert "type=DocumentParseError" in content
        assert "message=Failed to parse PDF" in content
    
    def test_log_metric(self, structured_logger, temp_log_dir):
        """测试记录性能指标"""
        structured_logger.log_metric(
            metric_name="parse_duration",
            value=123.45,
            unit="ms",
            doc_type="pdf"
        )
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "Metric" in content
        assert "name=parse_duration" in content
        assert "value=123.45ms" in content


class TestLogContext:
    """测试日志上下文管理器"""
    
    @pytest.fixture
    def logger(self, temp_log_dir, clean_logger):
        """创建logger"""
        return setup_logging(log_dir=temp_log_dir, file_level=logging.DEBUG)
    
    def test_log_context_success(self, logger, temp_log_dir):
        """测试成功操作的日志上下文"""
        with LogContext(logger, "test_operation"):
            pass
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "Starting: test_operation" in content
        assert "Completed: test_operation" in content
    
    def test_log_context_failure(self, logger, temp_log_dir):
        """测试失败操作的日志上下文"""
        try:
            with LogContext(logger, "test_operation"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        assert "Starting: test_operation" in content
        assert "Failed: test_operation" in content
        assert "ValueError: Test error" in content
    
    def test_log_context_duration(self, logger, temp_log_dir):
        """测试日志上下文记录执行时间"""
        import time
        
        with LogContext(logger, "test_operation"):
            time.sleep(0.1)  # 睡眠100ms
        
        # 验证日志内容
        log_file = Path(temp_log_dir) / "wayfare.log"
        content = log_file.read_text(encoding='utf-8')
        
        # 应该记录了执行时间（大约100ms）
        assert "Completed: test_operation" in content
        assert "ms)" in content
