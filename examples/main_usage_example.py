"""
WayFare Main Program使用示例

演示如何手动测试main.py的功能。
"""

import asyncio
import json
import tempfile
from pathlib import Path


async def test_main_initialization():
    """测试主程序初始化"""
    from wayfare.main import WayFareBackend
    
    print("=" * 60)
    print("测试1: 主程序初始化")
    print("=" * 60)
    
    # 创建临时工作区
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"创建临时工作区: {tmpdir}")
        
        # 创建Backend实例
        backend = WayFareBackend(
            workspace=tmpdir,
            config_path=None,
            log_level="INFO"
        )
        
        print("Backend实例创建成功")
        print(f"  - Workspace: {backend.workspace}")
        print(f"  - Log level: {backend.log_level}")
        print(f"  - Shutdown requested: {backend.shutdown_requested}")
        
        # 注意：完整初始化需要Qdrant服务和ONNX模型
        # 这里只演示实例创建
        print("\n提示: 完整初始化需要:")
        print("  1. Qdrant服务运行在 http://localhost:6333")
        print("  2. ONNX模型文件存在")
        print("  3. SILICONFLOW_API_KEY环境变量设置")


def test_ipc_request_format():
    """测试IPC请求格式"""
    print("\n" + "=" * 60)
    print("测试2: IPC请求格式")
    print("=" * 60)
    
    # Parse请求示例
    parse_request = {
        "id": "req_001",
        "seq": 1,
        "method": "parse",
        "params": {
            "path": "/path/to/document.pdf"
        }
    }
    
    print("\nParse请求示例:")
    print(json.dumps(parse_request, indent=2, ensure_ascii=False))
    
    # Annotate请求示例
    annotate_request = {
        "id": "req_002",
        "seq": 2,
        "method": "annotate",
        "params": {
            "docHash": "abc123",
            "page": 1,
            "bbox": {"x": 100, "y": 200, "width": 300, "height": 50},
            "type": "explanation",
            "context": "费曼技巧是什么？"
        }
    }
    
    print("\nAnnotate请求示例:")
    print(json.dumps(annotate_request, indent=2, ensure_ascii=False))
    
    # Query请求示例
    query_request = {
        "id": "req_003",
        "seq": 3,
        "method": "query",
        "params": {
            "docHash": "abc123",
            "query": "什么是费曼技巧？",
            "topK": 5
        }
    }
    
    print("\nQuery请求示例:")
    print(json.dumps(query_request, indent=2, ensure_ascii=False))


def test_command_line_usage():
    """测试命令行使用方式"""
    print("\n" + "=" * 60)
    print("测试3: 命令行使用方式")
    print("=" * 60)
    
    examples = [
        {
            "description": "基本用法",
            "command": "python -m wayfare.main --workspace /path/to/workspace"
        },
        {
            "description": "指定配置文件",
            "command": "python -m wayfare.main --workspace /path/to/workspace --config config.yaml"
        },
        {
            "description": "设置日志级别",
            "command": "python -m wayfare.main --workspace /path/to/workspace --log-level DEBUG"
        },
        {
            "description": "查看帮助",
            "command": "python -m wayfare.main --help"
        },
        {
            "description": "查看版本",
            "command": "python -m wayfare.main --version"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n示例 {i}: {example['description']}")
        print(f"  {example['command']}")


def test_environment_variables():
    """测试环境变量配置"""
    print("\n" + "=" * 60)
    print("测试4: 环境变量配置")
    print("=" * 60)
    
    env_vars = [
        {
            "name": "SILICONFLOW_API_KEY",
            "description": "SiliconFlow API密钥",
            "example": "export SILICONFLOW_API_KEY=your_api_key"
        },
        {
            "name": "WAYFARE_LLM_MODEL",
            "description": "LLM模型名称",
            "example": "export WAYFARE_LLM_MODEL=deepseek-chat"
        },
        {
            "name": "WAYFARE_CHUNK_SIZE",
            "description": "文档分块大小",
            "example": "export WAYFARE_CHUNK_SIZE=400"
        },
        {
            "name": "WAYFARE_QDRANT_URL",
            "description": "Qdrant服务地址",
            "example": "export WAYFARE_QDRANT_URL=http://localhost:6333"
        }
    ]
    
    print("\n支持的环境变量:")
    for var in env_vars:
        print(f"\n  {var['name']}")
        print(f"    描述: {var['description']}")
        print(f"    示例: {var['example']}")


def test_directory_structure():
    """测试目录结构"""
    print("\n" + "=" * 60)
    print("测试5: 工作区目录结构")
    print("=" * 60)
    
    structure = """
workspace/
├── .wayfare/
│   ├── config.yaml          # 配置文件
│   ├── wayfare.db           # SQLite数据库
│   ├── wayfare.log          # 当前日志文件
│   ├── wayfare.log.1        # 轮转日志文件
│   └── ...
└── your_documents/
    ├── document1.pdf
    └── document2.md
    """
    
    print(structure)


def test_error_scenarios():
    """测试错误场景"""
    print("\n" + "=" * 60)
    print("测试6: 常见错误场景")
    print("=" * 60)
    
    errors = [
        {
            "error": "Model Not Found",
            "message": "Embedding model not found: ./models/bge-small-zh-v1.5.onnx",
            "solution": "下载ONNX模型文件到指定路径"
        },
        {
            "error": "Qdrant Connection Failed",
            "message": "Failed to connect to Qdrant at http://localhost:6333",
            "solution": "启动Qdrant服务: docker run -p 6333:6333 qdrant/qdrant"
        },
        {
            "error": "API Key Not Found",
            "message": "SiliconFlow API key not found",
            "solution": "设置环境变量: export SILICONFLOW_API_KEY=your_api_key"
        },
        {
            "error": "Workspace Not Found",
            "message": "Workspace directory does not exist",
            "solution": "创建工作区目录: mkdir -p /path/to/workspace"
        }
    ]
    
    for i, error in enumerate(errors, 1):
        print(f"\n错误 {i}: {error['error']}")
        print(f"  消息: {error['message']}")
        print(f"  解决: {error['solution']}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("WayFare Main Program 使用示例")
    print("=" * 60)
    
    # 运行所有测试
    await test_main_initialization()
    test_ipc_request_format()
    test_command_line_usage()
    test_environment_variables()
    test_directory_structure()
    test_error_scenarios()
    
    print("\n" + "=" * 60)
    print("示例完成")
    print("=" * 60)
    print("\n提示: 要运行完整的main程序，请确保:")
    print("  1. Qdrant服务正在运行")
    print("  2. ONNX模型文件已下载")
    print("  3. SILICONFLOW_API_KEY已设置")
    print("\n然后运行:")
    print("  python -m wayfare.main --workspace /path/to/workspace")


if __name__ == "__main__":
    asyncio.run(main())
