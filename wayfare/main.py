#!/usr/bin/env python3
"""
WayFare MVP Backend主程序入口

作为Tauri应用的Sidecar进程运行，通过stdin/stdout进行IPC通信。

主要功能：
1. 命令行参数解析（--workspace, --config, --log-level）
2. 初始化所有组件（数据库、向量存储、embedding、LLM等）
3. 启动IPC服务器（监听stdin，输出到stdout）
4. 优雅关闭处理（SIGINT, SIGTERM）

Requirements: 所有需求的集成
"""

import sys
import os
import asyncio
import signal
import argparse
from pathlib import Path
from typing import Optional

# 设置日志系统（必须在其他导入之前）
from wayfare.logging import setup_logging, shutdown_logging, get_logger

# 导入所有组件
from wayfare.config import ConfigManager
from wayfare.db import SQLiteDB
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore
from wayfare.document_parser import DocumentParser
from wayfare.llm_provider import create_llm_provider
from wayfare.context_builder import create_context_builder
from wayfare.annotation_generator import create_annotation_generator
from wayfare.behavior_analyzer import BehaviorAnalyzer
from wayfare.ipc import IPCHandler
from wayfare.errors import (
    ModelLoadError,
    DatabaseInitError,
    ConfigurationError,
    ErrorMonitor
)


class WayFareBackend:
    """
    WayFare Backend主类
    
    负责组件初始化、IPC服务器运行和优雅关闭。
    """
    
    def __init__(self, workspace: str, config_path: Optional[str] = None, log_level: str = "INFO"):
        """
        初始化WayFare Backend
        
        Args:
            workspace: 工作区目录路径
            config_path: 可选的配置文件路径
            log_level: 日志级别（DEBUG, INFO, WARNING, ERROR）
        """
        self.workspace = Path(workspace)
        self.config_path = config_path
        self.log_level = log_level
        
        # 组件实例（延迟初始化）
        self.config_manager: Optional[ConfigManager] = None
        self.db: Optional[SQLiteDB] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.vector_store: Optional[VectorStore] = None
        self.document_parser: Optional[DocumentParser] = None
        self.llm_provider = None
        self.context_builder = None
        self.annotation_generator = None
        self.behavior_analyzer: Optional[BehaviorAnalyzer] = None
        self.ipc_handler: Optional[IPCHandler] = None
        self.error_monitor: Optional[ErrorMonitor] = None
        
        # 日志记录器
        self.logger = None
        
        # 关闭标志
        self.shutdown_requested = False
    
    async def initialize(self):
        """
        初始化所有组件
        
        按照正确的依赖顺序初始化：
        1. 日志系统
        2. 配置管理器
        3. 错误监控器
        4. SQLite数据库
        5. Qdrant向量存储
        6. ONNX Embedding模型
        7. LLM Provider
        8. Context Builder
        9. Document Parser
        10. Annotation Generator
        11. Behavior Analyzer
        12. IPC Handler
        
        Raises:
            ConfigurationError: 配置错误
            DatabaseInitError: 数据库初始化失败
            ModelLoadError: 模型加载失败
        """
        # 1. 设置日志系统
        log_level_map = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50
        }
        log_level_int = log_level_map.get(self.log_level.upper(), 20)
        
        # 日志存储在workspace/.wayfare目录
        log_dir = self.workspace / ".wayfare"
        self.logger = setup_logging(
            log_dir=str(log_dir),
            log_file="wayfare.log",
            file_level=log_level_int,
            console_level=30  # 控制台只显示WARNING及以上
        )
        
        self.logger.info("=" * 60)
        self.logger.info("WayFare MVP Backend Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Workspace: {self.workspace}")
        self.logger.info(f"Log level: {self.log_level}")
        
        try:
            # 2. 加载配置
            self.logger.info("Loading configuration...")
            config_file = self.config_path or str(self.workspace / ".wayfare" / "config.yaml")
            self.config_manager = ConfigManager(config_path=config_file)
            config = self.config_manager.get_config()
            self.logger.info(f"Configuration loaded: {config_file}")
            
            # 3. 初始化错误监控器
            self.logger.info("Initializing error monitor...")
            self.error_monitor = ErrorMonitor(
                error_threshold=10,
                time_window=600
            )
            self.logger.info("Error monitor initialized")
            
            # 4. 初始化SQLite数据库
            self.logger.info("Initializing SQLite database...")
            db_path = self.workspace / config.db_path
            self.db = SQLiteDB(db_path=str(db_path))
            await self.db.initialize()
            self.logger.info(f"Database initialized: {db_path}")
            
            # 5. 初始化Qdrant向量存储
            self.logger.info("Initializing Qdrant vector store...")
            self.vector_store = VectorStore(
                qdrant_url=config.qdrant_url,
                collection_name=config.qdrant_collection
            )
            await self.vector_store.initialize()
            self.logger.info(f"Vector store initialized: {config.qdrant_url}")
            
            # 6. 加载ONNX Embedding模型
            self.logger.info("Loading ONNX embedding model...")
            model_path = Path(config.embedding_model_path)
            if not model_path.is_absolute():
                model_path = self.workspace / model_path
            
            if not model_path.exists():
                raise ModelLoadError(
                    f"Embedding model not found: {model_path}\n"
                    f"Please download the model from: "
                    f"https://huggingface.co/BAAI/bge-small-zh-v1.5"
                )
            
            self.embedding_service = EmbeddingService(model_path=str(model_path))
            self.logger.info(f"Embedding model loaded: {model_path}")
            
            # 7. 初始化LLM Provider
            self.logger.info("Initializing LLM provider...")
            self.llm_provider = create_llm_provider(
                api_key=config.llm_api_key,
                model=config.llm_model,
                max_retries=config.llm_max_retries,
                retry_delay=config.llm_retry_delay,
                timeout=config.llm_timeout
            )
            self.logger.info(f"LLM provider initialized: {config.llm_model}")
            
            # 8. 初始化Context Builder
            self.logger.info("Initializing context builder...")
            self.context_builder = create_context_builder()
            self.logger.info("Context builder initialized")
            
            # 9. 初始化Document Parser
            self.logger.info("Initializing document parser...")
            self.document_parser = DocumentParser(
                embedding_service=self.embedding_service,
                vector_store=self.vector_store,
                db=self.db,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap
            )
            self.logger.info("Document parser initialized")
            
            # 10. 初始化Annotation Generator
            self.logger.info("Initializing annotation generator...")
            self.annotation_generator = create_annotation_generator(
                llm_provider=self.llm_provider,
                context_builder=self.context_builder,
                vector_store=self.vector_store,
                embedding_service=self.embedding_service,
                db=self.db
            )
            self.logger.info("Annotation generator initialized")
            
            # 11. 初始化Behavior Analyzer
            self.logger.info("Initializing behavior analyzer...")
            self.behavior_analyzer = BehaviorAnalyzer(
                db=self.db,
                intervention_threshold=config.intervention_threshold
            )
            self.logger.info("Behavior analyzer initialized")
            
            # 12. 初始化IPC Handler
            self.logger.info("Initializing IPC handler...")
            self.ipc_handler = IPCHandler(
                doc_parser=self.document_parser,
                annotation_gen=self.annotation_generator,
                vector_store=self.vector_store,
                embedding_service=self.embedding_service,
                config_manager=self.config_manager,
                behavior_analyzer=self.behavior_analyzer
            )
            self.logger.info("IPC handler initialized")
            
            self.logger.info("=" * 60)
            self.logger.info("All components initialized successfully")
            self.logger.info("=" * 60)
            
        except ConfigurationError as e:
            self.logger.critical(f"Configuration error: {e}")
            raise
        except DatabaseInitError as e:
            self.logger.critical(f"Database initialization error: {e}")
            raise
        except ModelLoadError as e:
            self.logger.critical(f"Model loading error: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"Unexpected initialization error: {e}", exc_info=True)
            raise
    
    async def run(self):
        """
        运行IPC服务器主循环
        
        监听stdin的JSON消息，处理后输出到stdout。
        支持优雅关闭（SIGINT, SIGTERM）。
        """
        self.logger.info("Starting IPC server...")
        self.logger.info("Listening on stdin, writing to stdout")
        
        try:
            # 设置stdin为非阻塞模式
            loop = asyncio.get_event_loop()
            
            while not self.shutdown_requested:
                try:
                    # 从stdin读取一行
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    
                    # EOF检测（Tauri进程终止）
                    if not line:
                        self.logger.info("EOF detected on stdin, shutting down...")
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 处理IPC请求
                    response = await self.ipc_handler.handle_request(line)
                    
                    # 输出响应到stdout
                    print(response, flush=True)
                    
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}", exc_info=True)
                    # 继续处理下一个请求
                    continue
            
            self.logger.info("IPC server stopped")
            
        except Exception as e:
            self.logger.critical(f"Fatal error in IPC server: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """
        优雅关闭
        
        清理资源：
        1. 停止IPC Handler的后台任务
        2. 关闭数据库连接
        3. 关闭日志系统
        """
        self.logger.info("=" * 60)
        self.logger.info("WayFare MVP Backend Shutting Down")
        self.logger.info("=" * 60)
        
        self.shutdown_requested = True
        
        try:
            # 停止IPC Handler的后台任务
            if self.ipc_handler:
                self.logger.info("Stopping IPC handler background tasks...")
                self.ipc_handler.stop_intervention_check()
            
            # 数据库连接会自动关闭（使用async with）
            # 向量存储客户端会自动关闭
            
            self.logger.info("All resources cleaned up")
            self.logger.info("=" * 60)
            self.logger.info("WayFare MVP Backend Stopped")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            # 关闭日志系统
            shutdown_logging()


async def main_async(args):
    """
    异步主函数
    
    Args:
        args: 命令行参数
    """
    # 创建Backend实例
    backend = WayFareBackend(
        workspace=args.workspace,
        config_path=args.config,
        log_level=args.log_level
    )
    
    # 设置信号处理器
    loop = asyncio.get_event_loop()
    
    def signal_handler(signum, frame):
        """信号处理器"""
        backend.logger.info(f"Received signal {signum}")
        backend.shutdown_requested = True
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化所有组件
        await backend.initialize()
        
        # 运行IPC服务器
        await backend.run()
        
    except (ConfigurationError, DatabaseInitError, ModelLoadError) as e:
        # 不可恢复错误，记录日志并退出
        if backend.logger:
            backend.logger.critical(f"Fatal error: {e}")
        else:
            print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        # 未预期的错误
        if backend.logger:
            backend.logger.critical(f"Unexpected error: {e}", exc_info=True)
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
        
    finally:
        # 优雅关闭
        await backend.shutdown()


def main():
    """
    主函数入口
    
    解析命令行参数并启动异步事件循环。
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="WayFare MVP Backend - Intelligent Learning Assistant Sidecar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 基本用法
  python -m wayfare.main --workspace /path/to/workspace
  
  # 指定配置文件
  python -m wayfare.main --workspace /path/to/workspace --config config.yaml
  
  # 设置日志级别
  python -m wayfare.main --workspace /path/to/workspace --log-level DEBUG

Environment Variables:
  WAYFARE_*           Override configuration values (e.g., WAYFARE_LLM_API_KEY)
  SILICONFLOW_API_KEY SiliconFlow API key for LLM access
        """
    )
    
    parser.add_argument(
        "--workspace",
        type=str,
        required=True,
        help="Workspace directory path (required)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Configuration file path (default: <workspace>/.wayfare/config.yaml)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Log level (default: INFO)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="WayFare MVP Backend 0.1.0"
    )
    
    args = parser.parse_args()
    
    # 验证workspace路径
    workspace_path = Path(args.workspace)
    if not workspace_path.exists():
        print(f"Error: Workspace directory does not exist: {args.workspace}", file=sys.stderr)
        sys.exit(1)
    
    if not workspace_path.is_dir():
        print(f"Error: Workspace path is not a directory: {args.workspace}", file=sys.stderr)
        sys.exit(1)
    
    # 启动异步事件循环
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nShutdown by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
