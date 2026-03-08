"""
错误处理测试

测试errors模块的功能，包括：
- 自定义异常类
- 错误监控器
- 用户友好的错误消息转换
- 降级批注内容
"""

import pytest
import time
from unittest.mock import Mock, patch

from wayfare.errors import (
    # 可恢复错误
    DocumentParseError,
    VectorSearchError,
    LLMGenerationError,
    DatabaseError,
    ValidationError,
    # 不可恢复错误
    ModelLoadError,
    DatabaseInitError,
    ConfigurationError,
    # 错误处理工具
    ErrorMonitor,
    format_user_error,
    get_fallback_annotation,
)


class TestRecoverableErrors:
    """测试可恢复错误"""
    
    def test_document_parse_error(self):
        """测试DocumentParseError"""
        path = "/test/doc.pdf"
        reason = "Invalid PDF format"
        
        error = DocumentParseError(path, reason)
        
        assert error.path == path
        assert error.reason == reason
        assert path in str(error)
        assert reason in str(error)
    
    def test_vector_search_error(self):
        """测试VectorSearchError"""
        error = VectorSearchError("Search failed")
        assert "Search failed" in str(error)
    
    def test_llm_generation_error(self):
        """测试LLMGenerationError"""
        error = LLMGenerationError("Generation failed")
        assert "Generation failed" in str(error)
    
    def test_database_error(self):
        """测试DatabaseError"""
        error = DatabaseError("Database operation failed")
        assert "Database operation failed" in str(error)
    
    def test_validation_error(self):
        """测试ValidationError"""
        error = ValidationError("Invalid input")
        assert "Invalid input" in str(error)


class TestUnrecoverableErrors:
    """测试不可恢复错误"""
    
    def test_model_load_error(self):
        """测试ModelLoadError"""
        error = ModelLoadError("Failed to load ONNX model")
        assert "Failed to load ONNX model" in str(error)
    
    def test_database_init_error(self):
        """测试DatabaseInitError"""
        error = DatabaseInitError("Failed to initialize database")
        assert "Failed to initialize database" in str(error)
    
    def test_configuration_error(self):
        """测试ConfigurationError"""
        error = ConfigurationError("Invalid configuration")
        assert "Invalid configuration" in str(error)


class TestErrorMonitor:
    """测试错误监控器"""
    
    @pytest.fixture
    def error_monitor(self):
        """创建错误监控器"""
        return ErrorMonitor(error_threshold=3, time_window=10)
    
    def test_error_monitor_initialization(self, error_monitor):
        """测试错误监控器初始化"""
        assert error_monitor.error_threshold == 3
        assert error_monitor.time_window == 10
        assert error_monitor.error_counts == {}
    
    def test_record_error(self, error_monitor):
        """测试记录错误"""
        error_monitor.record_error("TestError")
        
        assert "TestError" in error_monitor.error_counts
        assert len(error_monitor.error_counts["TestError"]) == 1
    
    def test_record_multiple_errors(self, error_monitor):
        """测试记录多个错误"""
        error_monitor.record_error("TestError")
        error_monitor.record_error("TestError")
        error_monitor.record_error("AnotherError")
        
        assert len(error_monitor.error_counts["TestError"]) == 2
        assert len(error_monitor.error_counts["AnotherError"]) == 1
    
    def test_error_threshold_alert(self, error_monitor):
        """测试错误阈值告警"""
        with patch.object(error_monitor, '_send_alert') as mock_alert:
            # 记录3次错误（达到阈值）
            for _ in range(3):
                error_monitor.record_error("TestError")
            
            # 应该触发告警
            mock_alert.assert_called_once_with("TestError")
    
    def test_error_window_cleanup(self, error_monitor):
        """测试错误时间窗口清理"""
        # 记录一个错误
        error_monitor.record_error("TestError")
        
        # 模拟时间流逝（超过时间窗口）
        with patch('time.time', return_value=time.time() + 11):
            error_monitor.record_error("TestError")
        
        # 旧的错误应该被清理
        assert len(error_monitor.error_counts["TestError"]) == 1
    
    def test_get_error_stats(self, error_monitor):
        """测试获取错误统计"""
        error_monitor.record_error("Error1")
        error_monitor.record_error("Error1")
        error_monitor.record_error("Error2")
        
        stats = error_monitor.get_error_stats()
        
        assert stats["Error1"] == 2
        assert stats["Error2"] == 1
    
    def test_get_error_stats_with_expired_errors(self, error_monitor):
        """测试获取错误统计（包含过期错误）"""
        # 记录一个错误
        error_monitor.record_error("TestError")
        
        # 模拟时间流逝（超过时间窗口）
        with patch('time.time', return_value=time.time() + 11):
            stats = error_monitor.get_error_stats()
        
        # 过期的错误不应该被统计
        assert stats.get("TestError", 0) == 0
    
    def test_reset(self, error_monitor):
        """测试重置错误计数"""
        error_monitor.record_error("Error1")
        error_monitor.record_error("Error2")
        
        error_monitor.reset()
        
        assert error_monitor.error_counts == {}
    
    def test_send_alert_logs_critical(self, error_monitor):
        """测试告警记录critical日志"""
        with patch.object(error_monitor.logger, 'critical') as mock_critical:
            error_monitor._send_alert("TestError")
            
            # 应该记录critical日志
            mock_critical.assert_called_once()
            call_args = mock_critical.call_args[0][0]
            assert "Alert" in call_args
            assert "TestError" in call_args
    
    def test_send_alert_resets_counter(self, error_monitor):
        """测试告警后重置计数器"""
        # 记录3次错误触发告警
        for _ in range(3):
            error_monitor.record_error("TestError")
        
        # 计数器应该被重置
        assert len(error_monitor.error_counts["TestError"]) == 0


class TestFormatUserError:
    """测试用户友好的错误消息转换"""
    
    def test_format_document_parse_error(self):
        """测试DocumentParseError的用户消息"""
        error = DocumentParseError("/test/doc.pdf", "Invalid format")
        message = format_user_error(error)
        
        assert "无法解析文档" in message
        assert "文件格式" in message
    
    def test_format_vector_search_error(self):
        """测试VectorSearchError的用户消息"""
        error = VectorSearchError("Search failed")
        message = format_user_error(error)
        
        assert "检索服务" in message
        assert "稍后重试" in message
    
    def test_format_llm_generation_error(self):
        """测试LLMGenerationError的用户消息"""
        error = LLMGenerationError("Generation failed")
        message = format_user_error(error)
        
        assert "AI助手" in message
        assert "稍后重试" in message
    
    def test_format_database_error(self):
        """测试DatabaseError的用户消息"""
        error = DatabaseError("Save failed")
        message = format_user_error(error)
        
        assert "数据保存失败" in message
        assert "磁盘空间" in message
    
    def test_format_validation_error(self):
        """测试ValidationError的用户消息"""
        error = ValidationError("Invalid input")
        message = format_user_error(error)
        
        assert "输入数据" in message
        assert "格式不正确" in message
    
    def test_format_model_load_error(self):
        """测试ModelLoadError的用户消息"""
        error = ModelLoadError("Failed to load model")
        message = format_user_error(error)
        
        assert "系统初始化失败" in message
        assert "技术支持" in message
    
    def test_format_database_init_error(self):
        """测试DatabaseInitError的用户消息"""
        error = DatabaseInitError("Failed to init database")
        message = format_user_error(error)
        
        assert "数据库初始化失败" in message
        assert "技术支持" in message
    
    def test_format_configuration_error(self):
        """测试ConfigurationError的用户消息"""
        error = ConfigurationError("Invalid config")
        message = format_user_error(error)
        
        assert "系统配置错误" in message
        assert "技术支持" in message
    
    def test_format_unknown_error(self):
        """测试未知错误的用户消息"""
        error = RuntimeError("Unknown error")
        message = format_user_error(error)
        
        assert "未知错误" in message
        assert "技术支持" in message


class TestGetFallbackAnnotation:
    """测试降级批注内容"""
    
    def test_get_fallback_explanation(self):
        """测试explanation类型的降级批注"""
        annotation = get_fallback_annotation("explanation")
        
        assert "AI助手" in annotation
        assert "稍后重试" in annotation
    
    def test_get_fallback_question(self):
        """测试question类型的降级批注"""
        annotation = get_fallback_annotation("question")
        
        assert "思考" in annotation
        assert "核心概念" in annotation
    
    def test_get_fallback_summary(self):
        """测试summary类型的降级批注"""
        annotation = get_fallback_annotation("summary")
        
        assert "总结" in annotation
        assert "自己的话" in annotation
    
    def test_get_fallback_unknown_type(self):
        """测试未知类型的降级批注"""
        annotation = get_fallback_annotation("unknown_type")
        
        assert "AI助手" in annotation
        assert "不可用" in annotation


class TestErrorInheritance:
    """测试错误类的继承关系"""
    
    def test_recoverable_errors_inherit_exception(self):
        """测试可恢复错误继承自Exception"""
        assert issubclass(DocumentParseError, Exception)
        assert issubclass(VectorSearchError, Exception)
        assert issubclass(LLMGenerationError, Exception)
        assert issubclass(DatabaseError, Exception)
        assert issubclass(ValidationError, Exception)
    
    def test_unrecoverable_errors_inherit_exception(self):
        """测试不可恢复错误继承自Exception"""
        assert issubclass(ModelLoadError, Exception)
        assert issubclass(DatabaseInitError, Exception)
        assert issubclass(ConfigurationError, Exception)


class TestErrorRaising:
    """测试错误抛出和捕获"""
    
    def test_raise_and_catch_document_parse_error(self):
        """测试抛出和捕获DocumentParseError"""
        with pytest.raises(DocumentParseError) as exc_info:
            raise DocumentParseError("/test/doc.pdf", "Invalid format")
        
        assert exc_info.value.path == "/test/doc.pdf"
        assert exc_info.value.reason == "Invalid format"
    
    def test_raise_and_catch_vector_search_error(self):
        """测试抛出和捕获VectorSearchError"""
        with pytest.raises(VectorSearchError):
            raise VectorSearchError("Search failed")
    
    def test_raise_and_catch_llm_generation_error(self):
        """测试抛出和捕获LLMGenerationError"""
        with pytest.raises(LLMGenerationError):
            raise LLMGenerationError("Generation failed")
    
    def test_catch_base_exception(self):
        """测试使用基类Exception捕获自定义错误"""
        try:
            raise DocumentParseError("/test/doc.pdf", "Invalid format")
        except Exception as e:
            assert isinstance(e, DocumentParseError)


class TestErrorMonitorIntegration:
    """测试错误监控器集成场景"""
    
    def test_monitor_multiple_error_types(self):
        """测试监控多种错误类型"""
        monitor = ErrorMonitor(error_threshold=5, time_window=10)  # 提高阈值避免触发告警
        
        # 记录不同类型的错误
        monitor.record_error("DocumentParseError")
        monitor.record_error("VectorSearchError")
        monitor.record_error("DocumentParseError")
        
        stats = monitor.get_error_stats()
        
        assert stats["DocumentParseError"] == 2
        assert stats["VectorSearchError"] == 1
    
    def test_monitor_with_real_time_window(self):
        """测试真实时间窗口的错误监控"""
        monitor = ErrorMonitor(error_threshold=3, time_window=1)  # 1秒窗口
        
        # 记录2个错误
        monitor.record_error("TestError")
        monitor.record_error("TestError")
        
        # 等待超过时间窗口
        time.sleep(1.1)
        
        # 再记录1个错误
        monitor.record_error("TestError")
        
        # 应该只有1个错误在窗口内
        stats = monitor.get_error_stats()
        assert stats["TestError"] == 1
    
    def test_monitor_concurrent_errors(self):
        """测试并发错误记录"""
        monitor = ErrorMonitor(error_threshold=15, time_window=10)  # 提高阈值避免触发告警
        
        # 模拟并发记录多个错误
        error_types = ["Error1", "Error2", "Error3"]
        for _ in range(10):
            for error_type in error_types:
                monitor.record_error(error_type)
        
        stats = monitor.get_error_stats()
        
        for error_type in error_types:
            assert stats[error_type] == 10
