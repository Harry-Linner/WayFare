"""
IPC Handler使用示例

演示如何使用IPCHandler处理各种IPC请求。
"""

import asyncio
import json
from wayfare.ipc import IPCHandler


async def main():
    """演示IPC Handler的基本用法"""
    
    # 创建IPC Handler实例
    handler = IPCHandler()
    
    print("=" * 60)
    print("IPC Handler使用示例")
    print("=" * 60)
    
    # 示例1: 处理parse请求
    print("\n1. 处理parse请求:")
    parse_request = json.dumps({
        "id": "req-001",
        "seq": 0,
        "method": "parse",
        "params": {
            "path": "/path/to/document.pdf"
        }
    })
    print(f"请求: {parse_request}")
    
    response = await handler.handle_request(parse_request)
    print(f"响应: {response}")
    
    # 示例2: 处理annotate请求
    print("\n2. 处理annotate请求:")
    annotate_request = json.dumps({
        "id": "req-002",
        "seq": 1,
        "method": "annotate",
        "params": {
            "docHash": "abc123",
            "page": 5,
            "bbox": {"x": 100, "y": 200, "width": 300, "height": 50},
            "type": "explanation",
            "context": "费曼技巧是什么？"
        }
    })
    print(f"请求: {annotate_request}")
    
    response = await handler.handle_request(annotate_request)
    print(f"响应: {response}")
    
    # 示例3: 处理query请求
    print("\n3. 处理query请求:")
    query_request = json.dumps({
        "id": "req-003",
        "seq": 2,
        "method": "query",
        "params": {
            "docHash": "abc123",
            "query": "什么是费曼技巧？",
            "topK": 5
        }
    })
    print(f"请求: {query_request}")
    
    response = await handler.handle_request(query_request)
    print(f"响应: {response}")
    
    # 示例4: 处理config请求
    print("\n4. 处理config请求:")
    config_request = json.dumps({
        "id": "req-004",
        "seq": 3,
        "method": "config",
        "params": {
            "llm_model": "deepseek-chat",
            "retrieval_top_k": 10
        }
    })
    print(f"请求: {config_request}")
    
    response = await handler.handle_request(config_request)
    print(f"响应: {response}")
    
    # 示例5: 处理错误请求（缺少必需字段）
    print("\n5. 处理错误请求（缺少method字段）:")
    invalid_request = json.dumps({
        "id": "req-005",
        "seq": 4,
        "params": {}
    })
    print(f"请求: {invalid_request}")
    
    response = await handler.handle_request(invalid_request)
    print(f"响应: {response}")
    
    # 示例6: 处理乱序请求
    print("\n6. 处理乱序请求（演示seq排序）:")
    
    # 创建新的handler实例
    handler2 = IPCHandler()
    
    # 先发送seq=2的请求
    request_seq2 = json.dumps({
        "id": "req-006",
        "seq": 2,
        "method": "parse",
        "params": {"path": "/path/to/doc2.pdf"}
    })
    print(f"发送seq=2的请求: {request_seq2}")
    response = await handler2.handle_request(request_seq2)
    print(f"响应: {response}")
    
    # 再发送seq=0的请求
    request_seq0 = json.dumps({
        "id": "req-007",
        "seq": 0,
        "method": "parse",
        "params": {"path": "/path/to/doc0.pdf"}
    })
    print(f"发送seq=0的请求: {request_seq0}")
    response = await handler2.handle_request(request_seq0)
    print(f"响应: {response}")
    
    # 发送seq=1的请求（会触发seq=2的处理）
    request_seq1 = json.dumps({
        "id": "req-008",
        "seq": 1,
        "method": "parse",
        "params": {"path": "/path/to/doc1.pdf"}
    })
    print(f"发送seq=1的请求: {request_seq1}")
    response = await handler2.handle_request(request_seq1)
    print(f"响应: {response}")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
