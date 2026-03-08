"""
IPC Parse Integration Example

演示如何使用IPCHandler集成DocumentParser进行异步文档解析。
展示完整的parse请求流程，包括：
- 立即返回processing状态
- 后台异步解析
- 主动推送完成/失败通知
"""

import asyncio
import json
import tempfile
from pathlib import Path

# 导入必要的模块
from wayfare.ipc import IPCHandler
from wayfare.document_parser import DocumentParser
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore
from wayfare.db import SQLiteDB


async def example_basic_parse_integration():
    """基础parse集成示例"""
    print("\n=== 基础Parse集成示例 ===\n")
    
    # 1. 初始化依赖组件
    print("1. 初始化组件...")
    
    # 创建临时数据库
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = SQLiteDB(str(db_path))
        await db.initialize()
        
        # 初始化embedding服务（使用mock）
        embedding_service = EmbeddingService(
            model_path="./models/bge-small-zh-v1.5.onnx"
        )
        
        # 初始化向量存储
        vector_store = VectorStore(qdrant_url="http://localhost:6333")
        await vector_store.initialize()
        
        # 初始化文档解析器
        doc_parser = DocumentParser(
            embedding_service=embedding_service,
            vector_store=vector_store,
            db=db
        )
        
        # 初始化IPC Handler
        ipc_handler = IPCHandler(doc_parser=doc_parser)
        
        print("✓ 组件初始化完成\n")
        
        # 2. 创建测试文档
        print("2. 创建测试文档...")
        test_doc = Path(tmpdir) / "test.md"
        test_doc.write_text("""
# 测试文档

这是一个测试文档，用于演示parse功能。

## 第一节

这是第一节的内容。包含一些测试文本。

## 第二节

这是第二节的内容。包含更多测试文本。
""", encoding='utf-8')
        
        print(f"✓ 测试文档创建: {test_doc}\n")
        
        # 3. 构造parse请求
        print("3. 发送parse请求...")
        parse_request = {
            "id": "req-001",
            "seq": 0,
            "method": "parse",
            "params": {"path": str(test_doc)}
        }
        
        raw_message = json.dumps(parse_request)
        print(f"请求: {json.dumps(parse_request, indent=2, ensure_ascii=False)}\n")
        
        # 4. 处理请求（立即返回）
        response_str = await ipc_handler.handle_request(raw_message)
        response = json.loads(response_str)
        
        print("4. 收到立即响应:")
        print(f"响应: {json.dumps(response, indent=2, ensure_ascii=False)}\n")
        
        # 验证立即响应
        assert response["success"] is True
        assert response["data"]["status"] == "processing"
        doc_hash = response["data"]["docHash"]
        print(f"✓ 文档hash: {doc_hash}")
        print("✓ 状态: processing (后台解析中)\n")
        
        # 5. 等待异步解析完成
        print("5. 等待异步解析完成...")
        await asyncio.sleep(1)  # 等待后台任务完成
        
        # 6. 检查数据库状态
        print("\n6. 检查解析结果...")
        doc = await db.get_document(doc_hash)
        if doc:
            print(f"✓ 文档状态: {doc['status']}")
            segment_count = await db.count_segments(doc_hash)
            print(f"✓ 片段数量: {segment_count}")
        
        print("\n✓ Parse集成示例完成!")


async def example_parse_with_notification_capture():
    """带通知捕获的parse示例"""
    print("\n=== Parse通知捕获示例 ===\n")
    
    # 创建一个自定义的IPC Handler来捕获通知
    class NotificationCapturingHandler(IPCHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.notifications = []
        
        async def _send_notification(self, data):
            """重写_send_notification来捕获通知"""
            self.notifications.append(data)
            print(f"\n📢 收到通知: {data['type']}")
            print(f"   内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # 初始化组件（简化版）
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = SQLiteDB(str(db_path))
        await db.initialize()
        
        # 使用mock组件
        from unittest.mock import MagicMock, AsyncMock
        from wayfare.document_parser import ParseResult
        
        mock_embedding = MagicMock()
        mock_vector_store = MagicMock()
        mock_vector_store.initialize = AsyncMock()
        
        doc_parser = DocumentParser(
            embedding_service=mock_embedding,
            vector_store=mock_vector_store,
            db=db
        )
        
        # 使用自定义Handler
        ipc_handler = NotificationCapturingHandler(doc_parser=doc_parser)
        
        # 创建测试文档
        test_doc = Path(tmpdir) / "test.md"
        test_doc.write_text("# Test\n\nContent", encoding='utf-8')
        
        # 发送parse请求
        print("1. 发送parse请求...")
        parse_request = {
            "id": "req-002",
            "seq": 0,
            "method": "parse",
            "params": {"path": str(test_doc)}
        }
        
        response_str = await ipc_handler.handle_request(json.dumps(parse_request))
        response = json.loads(response_str)
        
        print(f"✓ 立即响应: status={response['data']['status']}")
        
        # 等待异步解析和通知
        print("\n2. 等待异步解析...")
        await asyncio.sleep(1)
        
        # 检查捕获的通知
        print(f"\n3. 捕获到 {len(ipc_handler.notifications)} 个通知")
        for i, notification in enumerate(ipc_handler.notifications, 1):
            print(f"\n通知 {i}:")
            print(f"  类型: {notification['type']}")
            print(f"  状态: {notification.get('status', 'N/A')}")
            if 'error' in notification:
                print(f"  错误: {notification['error']}")
        
        print("\n✓ 通知捕获示例完成!")


async def example_parse_error_handling():
    """Parse错误处理示例"""
    print("\n=== Parse错误处理示例 ===\n")
    
    # 创建带通知捕获的Handler
    class NotificationCapturingHandler(IPCHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.notifications = []
        
        async def _send_notification(self, data):
            self.notifications.append(data)
    
    # 使用mock组件
    from unittest.mock import MagicMock, AsyncMock
    
    mock_parser = MagicMock()
    mock_parser.compute_hash = MagicMock(return_value="error_doc_hash")
    mock_parser.parse_document = AsyncMock(side_effect=Exception("Parse failed!"))
    
    ipc_handler = NotificationCapturingHandler(doc_parser=mock_parser)
    
    # 发送parse请求
    print("1. 发送parse请求（将会失败）...")
    parse_request = {
        "id": "req-003",
        "seq": 0,
        "method": "parse",
        "params": {"path": "/nonexistent/file.pdf"}
    }
    
    response_str = await ipc_handler.handle_request(json.dumps(parse_request))
    response = json.loads(response_str)
    
    print(f"✓ 立即响应: status={response['data']['status']}")
    
    # 等待异步解析失败
    print("\n2. 等待异步解析（预期失败）...")
    await asyncio.sleep(0.5)
    
    # 检查失败通知
    print("\n3. 检查失败通知:")
    if ipc_handler.notifications:
        notification = ipc_handler.notifications[0]
        print(f"  类型: {notification['type']}")
        print(f"  状态: {notification['status']}")
        print(f"  错误: {notification['error']}")
        
        assert notification['type'] == 'parse_failed'
        assert notification['status'] == 'failed'
        print("\n✓ 错误处理正确!")
    
    print("\n✓ 错误处理示例完成!")


async def example_multiple_concurrent_parses():
    """多个并发parse请求示例"""
    print("\n=== 多个并发Parse请求示例 ===\n")
    
    # 创建带通知捕获的Handler
    class NotificationCapturingHandler(IPCHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.notifications = []
        
        async def _send_notification(self, data):
            self.notifications.append(data)
            print(f"📢 通知: {data['type']} for {data['docHash'][:8]}...")
    
    # 使用mock组件
    from unittest.mock import MagicMock, AsyncMock
    from wayfare.document_parser import ParseResult
    
    async def mock_parse(path):
        """模拟解析（带延迟）"""
        await asyncio.sleep(0.2)
        return ParseResult(
            doc_hash=f"hash_{path}",
            version_hash=f"version_{path}",
            segment_count=5,
            status="completed"
        )
    
    mock_parser = MagicMock()
    mock_parser.compute_hash = lambda path: f"hash_{path}"
    mock_parser.parse_document = mock_parse
    
    ipc_handler = NotificationCapturingHandler(doc_parser=mock_parser)
    
    # 发送多个parse请求
    print("1. 发送3个并发parse请求...\n")
    
    paths = ["/doc1.pdf", "/doc2.pdf", "/doc3.pdf"]
    responses = []
    
    for i, path in enumerate(paths):
        request = {
            "id": f"req-{i}",
            "seq": i,
            "method": "parse",
            "params": {"path": path}
        }
        
        response_str = await ipc_handler.handle_request(json.dumps(request))
        response = json.loads(response_str)
        responses.append(response)
        
        print(f"✓ 请求 {i+1}: {path} -> status={response['data']['status']}")
    
    # 等待所有异步解析完成
    print("\n2. 等待所有异步解析完成...\n")
    await asyncio.sleep(1)
    
    # 检查通知
    print(f"\n3. 收到 {len(ipc_handler.notifications)} 个完成通知")
    
    completed = [n for n in ipc_handler.notifications if n['type'] == 'parse_completed']
    print(f"✓ 成功完成: {len(completed)} 个")
    
    print("\n✓ 并发Parse示例完成!")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("IPC Parse Integration Examples")
    print("=" * 60)
    
    try:
        # 注意：这些示例需要实际的组件初始化
        # 在生产环境中使用时，确保所有依赖都已正确配置
        
        # await example_basic_parse_integration()
        await example_parse_with_notification_capture()
        await example_parse_error_handling()
        await example_multiple_concurrent_parses()
        
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
