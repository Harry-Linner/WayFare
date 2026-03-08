"""
IPC Handler annotate方法集成示例

演示如何使用IPC Handler的annotate方法生成批注。
展示完整的IPC请求-响应流程。

注意：本示例使用mock对象演示IPC流程，实际使用时需要初始化完整的依赖。
"""

import asyncio
import json
from unittest.mock import AsyncMock
from wayfare.ipc import IPCHandler
from wayfare.db import Annotation, BoundingBox


async def create_mock_annotation_generator():
    """创建mock的AnnotationGenerator用于演示"""
    mock = AsyncMock()
    
    # 模拟generate_annotation方法
    async def mock_generate(doc_hash, page, bbox, annotation_type, context):
        # 根据类型生成不同的批注内容
        content_templates = {
            "explanation": f"【解释】{context}\n\n这是一个核心概念的解释。通过简单的语言和类比，我们可以更好地理解它。",
            "question": f"【提问】关于\"{context}\"，你可以思考：\n1. 这个概念的本质是什么？\n2. 它与你已知的知识有什么联系？",
            "summary": f"【总结】{context}\n\n核心要点：\n- 主要观点\n- 关键细节\n- 与上下文的关系"
        }
        
        return Annotation(
            id=f"annotation_{annotation_type}_{hash(context) % 10000}",
            doc_hash=doc_hash,
            version_hash="test_version_hash",
            type=annotation_type,
            content=content_templates.get(annotation_type, "默认批注内容"),
            bbox=BoundingBox(**bbox),
            created_at="2024-01-01T00:00:00Z"
        )
    
    mock.generate_annotation = mock_generate
    return mock


async def main():
    """演示IPC Handler的annotate方法"""
    
    print("=" * 60)
    print("IPC Handler annotate方法集成示例")
    print("=" * 60)
    
    # 1. 创建mock的AnnotationGenerator
    print("\n1. 创建AnnotationGenerator（使用mock演示）...")
    annotation_gen = await create_mock_annotation_generator()
    
    # 2. 创建IPC Handler
    print("2. 创建IPC Handler...")
    ipc_handler = IPCHandler(annotation_gen=annotation_gen)
    
    # 3. 发送annotate请求
    print("\n3. 发送annotate请求...")
    
    # 构建IPC请求消息
    request_message = {
        "id": "request_001",
        "seq": 0,
        "method": "annotate",
        "params": {
            "docHash": "test_doc_hash_123",
            "page": 1,
            "bbox": {
                "x": 100.0,
                "y": 200.0,
                "width": 300.0,
                "height": 50.0
            },
            "type": "explanation",
            "context": "费曼技巧是一种学习方法，通过用简单的语言解释复杂概念来检验理解程度。"
        }
    }
    
    print(f"\n请求消息:")
    print(json.dumps(request_message, indent=2, ensure_ascii=False))
    
    # 发送请求
    response_str = await ipc_handler.handle_request(json.dumps(request_message))
    response = json.loads(response_str)
    
    print(f"\n响应消息:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    # 4. 验证响应
    print("\n4. 验证响应...")
    if response["success"]:
        print("   ✓ 请求成功")
        print(f"   ✓ 批注ID: {response['data']['annotationId']}")
        print(f"   ✓ 批注类型: {response['data']['type']}")
        print(f"   ✓ 批注内容:")
        print(f"     {response['data']['content']}")
    else:
        print(f"   ✗ 请求失败: {response.get('error', 'Unknown error')}")
    
    # 5. 测试不同的批注类型
    print("\n5. 测试不同的批注类型...")
    
    annotation_types = [
        ("question", "提问式批注"),
        ("summary", "总结式批注")
    ]
    
    for idx, (ann_type, description) in enumerate(annotation_types, start=1):
        print(f"\n   测试 {idx}: {description}")
        
        request = {
            "id": f"request_00{idx+1}",
            "seq": idx,
            "method": "annotate",
            "params": {
                "docHash": "test_doc_hash_123",
                "page": 1,
                "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
                "type": ann_type,
                "context": "费曼技巧是一种学习方法。"
            }
        }
        
        response_str = await ipc_handler.handle_request(json.dumps(request))
        response = json.loads(response_str)
        
        if response["success"]:
            print(f"   ✓ {description}生成成功")
            print(f"     批注ID: {response['data']['annotationId']}")
            print(f"     内容预览:")
            print(f"     {response['data']['content']}")
        else:
            print(f"   ✗ {description}生成失败: {response.get('error', 'Unknown error')}")
    
    # 6. 测试错误处理
    print("\n6. 测试错误处理...")
    
    # 测试无效的批注类型
    print("\n   测试 1: 无效的批注类型")
    invalid_request = {
        "id": "request_error_001",
        "seq": 3,
        "method": "annotate",
        "params": {
            "docHash": "test_doc_hash_123",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0, "width": 300.0, "height": 50.0},
            "type": "invalid_type",
            "context": "测试文本"
        }
    }
    
    response_str = await ipc_handler.handle_request(json.dumps(invalid_request))
    response = json.loads(response_str)
    
    if not response["success"]:
        print(f"   ✓ 正确捕获错误: {response['error']}")
    else:
        print("   ✗ 应该返回错误但返回了成功")
    
    # 测试缺少必需参数
    print("\n   测试 2: 缺少必需参数")
    missing_param_request = {
        "id": "request_error_002",
        "seq": 4,
        "method": "annotate",
        "params": {
            "docHash": "test_doc_hash_123",
            "page": 1,
            # 缺少bbox参数
            "type": "explanation",
            "context": "测试文本"
        }
    }
    
    response_str = await ipc_handler.handle_request(json.dumps(missing_param_request))
    response = json.loads(response_str)
    
    if not response["success"]:
        print(f"   ✓ 正确捕获错误: {response['error']}")
    else:
        print("   ✗ 应该返回错误但返回了成功")
    
    # 测试缺少bbox字段
    print("\n   测试 3: bbox缺少必需字段")
    invalid_bbox_request = {
        "id": "request_error_003",
        "seq": 5,
        "method": "annotate",
        "params": {
            "docHash": "test_doc_hash_123",
            "page": 1,
            "bbox": {"x": 100.0, "y": 200.0},  # 缺少width和height
            "type": "explanation",
            "context": "测试文本"
        }
    }
    
    response_str = await ipc_handler.handle_request(json.dumps(invalid_bbox_request))
    response = json.loads(response_str)
    
    if not response["success"]:
        print(f"   ✓ 正确捕获错误: {response['error']}")
    else:
        print("   ✗ 应该返回错误但返回了成功")
    
    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
    print("\n说明：")
    print("- 本示例使用mock对象演示IPC流程")
    print("- 实际使用时需要初始化完整的依赖：")
    print("  * LLMProvider")
    print("  * ContextBuilder")
    print("  * VectorStore")
    print("  * EmbeddingService")
    print("  * SQLiteDB")
    print("- 参考 wayfare/annotation_generator.py 中的 create_annotation_generator 函数")


if __name__ == "__main__":
    asyncio.run(main())
