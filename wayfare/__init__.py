"""
WayFare MVP Backend - 智能学习助手后端服务

WayFare是一个智能学习助手系统，作为Tauri应用的Sidecar进程运行。
本系统最大化复用nanobot框架的现有能力，通过导入、继承和配置的方式避免重复开发基础设施。
"""

__version__ = "0.1.0"

# 导出核心类
from wayfare.config import WayFareConfig, ConfigManager
from wayfare.db import SQLiteDB, BoundingBox, DocumentSegment, Annotation, BehaviorEvent
from wayfare.ipc import IPCHandler, IPCRequest, IPCResponse
from wayfare.logging import setup_logging, get_logger, set_log_level, shutdown_logging, StructuredLogger, LogContext
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore, SearchResult
from wayfare.document_parser import DocumentParser, ParseResult
from wayfare.llm_provider import WayFareLLMProvider, create_llm_provider
from wayfare.context_builder import WayFareContextBuilder, create_context_builder
from wayfare.annotation_generator import AnnotationGenerator, create_annotation_generator
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

__all__ = [
    # 配置管理
    "WayFareConfig",
    "ConfigManager",
    # 数据库
    "SQLiteDB",
    "BoundingBox",
    "DocumentSegment",
    "Annotation",
    "BehaviorEvent",
    # IPC通信
    "IPCHandler",
    "IPCRequest",
    "IPCResponse",
    # 日志系统
    "setup_logging",
    "get_logger",
    "set_log_level",
    "shutdown_logging",
    "StructuredLogger",
    "LogContext",
    # Embedding和向量存储
    "EmbeddingService",
    "VectorStore",
    "SearchResult",
    # 文档解析
    "DocumentParser",
    "ParseResult",
    # LLM和上下文构建
    "WayFareLLMProvider",
    "create_llm_provider",
    "WayFareContextBuilder",
    "create_context_builder",
    # 批注生成
    "AnnotationGenerator",
    "create_annotation_generator",
    # 错误处理
    "DocumentParseError",
    "VectorSearchError",
    "LLMGenerationError",
    "DatabaseError",
    "ValidationError",
    "ModelLoadError",
    "DatabaseInitError",
    "ConfigurationError",
    "ErrorMonitor",
    "format_user_error",
    "get_fallback_annotation",
]
