"""
测试数据生成器

提供用于测试的模拟数据生成函数，包括文档、片段、批注、行为数据等。
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random


def generate_doc_hash() -> str:
    """生成模拟的文档hash"""
    return f"doc_{uuid.uuid4().hex[:16]}"


def generate_version_hash() -> str:
    """生成模拟的版本hash"""
    return f"ver_{uuid.uuid4().hex[:16]}"


def generate_segment_id() -> str:
    """生成模拟的片段ID"""
    return f"seg_{uuid.uuid4().hex[:16]}"


def generate_annotation_id() -> str:
    """生成模拟的批注ID"""
    return f"ann_{uuid.uuid4().hex[:16]}"


def generate_behavior_id() -> str:
    """生成模拟的行为ID"""
    return f"beh_{uuid.uuid4().hex[:16]}"


def mock_document(
    path: str = "/test/document.pdf",
    status: str = "completed",
    doc_hash: str = None,
    version_hash: str = None
) -> Dict[str, Any]:
    """
    生成模拟的文档数据
    
    Args:
        path: 文档路径
        status: 文档状态 (pending/processing/completed/failed)
        doc_hash: 文档hash（如果为None则自动生成）
        version_hash: 版本hash（如果为None则自动生成）
    
    Returns:
        文档数据字典
    """
    return {
        "hash": doc_hash or generate_doc_hash(),
        "path": path,
        "status": status,
        "updated_at": datetime.now().isoformat(),
        "version_hash": version_hash or generate_version_hash()
    }


def mock_segment(
    doc_hash: str,
    text: str = "这是一段测试文本。",
    page: int = 0,
    bbox: Dict[str, float] = None,
    segment_id: str = None
) -> Dict[str, Any]:
    """
    生成模拟的文档片段数据
    
    Args:
        doc_hash: 所属文档的hash
        text: 片段文本
        page: 页码
        bbox: 边界框 {x, y, width, height}
        segment_id: 片段ID（如果为None则自动生成）
    
    Returns:
        片段数据字典
    """
    if bbox is None:
        bbox = {"x": 0.0, "y": 0.0, "width": 100.0, "height": 50.0}
    
    return {
        "id": segment_id or generate_segment_id(),
        "doc_hash": doc_hash,
        "text": text,
        "page": page,
        "bbox_x": bbox["x"],
        "bbox_y": bbox["y"],
        "bbox_width": bbox["width"],
        "bbox_height": bbox["height"]
    }


def mock_annotation(
    doc_hash: str,
    version_hash: str,
    annotation_type: str = "explanation",
    content: str = "这是一条测试批注。",
    page: int = 0,
    bbox: Dict[str, float] = None,
    annotation_id: str = None
) -> Dict[str, Any]:
    """
    生成模拟的批注数据
    
    Args:
        doc_hash: 所属文档的hash
        version_hash: 文档版本hash
        annotation_type: 批注类型 (explanation/question/summary)
        content: 批注内容
        page: 页码
        bbox: 边界框 {x, y, width, height}
        annotation_id: 批注ID（如果为None则自动生成）
    
    Returns:
        批注数据字典
    """
    if bbox is None:
        bbox = {"x": 0.0, "y": 0.0, "width": 100.0, "height": 50.0}
    
    return {
        "id": annotation_id or generate_annotation_id(),
        "doc_hash": doc_hash,
        "version_hash": version_hash,
        "type": annotation_type,
        "content": content,
        "bbox_x": bbox["x"],
        "bbox_y": bbox["y"],
        "bbox_width": bbox["width"],
        "bbox_height": bbox["height"],
        "created_at": datetime.now().isoformat()
    }


def mock_behavior(
    doc_hash: str,
    page: int = 0,
    event_type: str = "page_view",
    metadata: Dict[str, Any] = None,
    behavior_id: str = None,
    timestamp: datetime = None
) -> Dict[str, Any]:
    """
    生成模拟的行为数据
    
    Args:
        doc_hash: 所属文档的hash
        page: 页码
        event_type: 事件类型 (page_view/text_select/scroll)
        metadata: 额外的元数据
        behavior_id: 行为ID（如果为None则自动生成）
        timestamp: 时间戳（如果为None则使用当前时间）
    
    Returns:
        行为数据字典
    """
    import json
    
    if metadata is None:
        metadata = {}
    
    return {
        "id": behavior_id or generate_behavior_id(),
        "doc_hash": doc_hash,
        "page": page,
        "event_type": event_type,
        "timestamp": (timestamp or datetime.now()).isoformat(),
        "metadata": json.dumps(metadata)
    }


def mock_ipc_request(
    method: str,
    params: Dict[str, Any],
    request_id: str = None,
    seq: int = 1
) -> Dict[str, Any]:
    """
    生成模拟的IPC请求
    
    Args:
        method: 方法名 (parse/annotate/query/config)
        params: 请求参数
        request_id: 请求ID（如果为None则自动生成）
        seq: 序列号
    
    Returns:
        IPC请求字典
    """
    return {
        "id": request_id or str(uuid.uuid4()),
        "seq": seq,
        "method": method,
        "params": params
    }


def mock_ipc_response(
    request_id: str,
    seq: int,
    success: bool = True,
    data: Dict[str, Any] = None,
    error: str = None
) -> Dict[str, Any]:
    """
    生成模拟的IPC响应
    
    Args:
        request_id: 请求ID
        seq: 序列号
        success: 是否成功
        data: 响应数据
        error: 错误信息
    
    Returns:
        IPC响应字典
    """
    response = {
        "id": request_id,
        "seq": seq,
        "success": success
    }
    
    if success:
        response["data"] = data or {}
    else:
        response["error"] = error or "Unknown error"
    
    return response


def mock_vector(dimension: int = 512) -> List[float]:
    """
    生成模拟的向量数据
    
    Args:
        dimension: 向量维度
    
    Returns:
        向量列表
    """
    import numpy as np
    
    # 生成随机向量并归一化
    vector = np.random.randn(dimension)
    vector = vector / np.linalg.norm(vector)
    return vector.tolist()


def mock_search_result(
    segment_id: str = None,
    text: str = "这是一段搜索结果文本。",
    page: int = 0,
    score: float = 0.85
) -> Dict[str, Any]:
    """
    生成模拟的搜索结果
    
    Args:
        segment_id: 片段ID（如果为None则自动生成）
        text: 片段文本
        page: 页码
        score: 相似度分数
    
    Returns:
        搜索结果字典
    """
    return {
        "segmentId": segment_id or generate_segment_id(),
        "text": text,
        "page": page,
        "score": score
    }


# ============================================
# 批量数据生成函数
# ============================================

def generate_mock_documents(count: int = 5) -> List[Dict[str, Any]]:
    """
    生成多个模拟文档
    
    Args:
        count: 文档数量
    
    Returns:
        文档列表
    """
    documents = []
    for i in range(count):
        doc = mock_document(
            path=f"/test/document_{i}.pdf",
            status=random.choice(["completed", "processing", "pending"])
        )
        documents.append(doc)
    return documents


def generate_mock_segments(doc_hash: str, count: int = 10) -> List[Dict[str, Any]]:
    """
    生成多个模拟片段
    
    Args:
        doc_hash: 文档hash
        count: 片段数量
    
    Returns:
        片段列表
    """
    segments = []
    sample_texts = [
        "这是第一段测试文本，包含一些基本内容。",
        "第二段文本讨论了一些重要的概念。",
        "第三段文本提供了详细的解释和示例。",
        "第四段文本总结了前面的内容。",
        "第五段文本引入了新的主题。",
        "第六段文本深入探讨了相关问题。",
        "第七段文本提供了实践建议。",
        "第八段文本分析了常见错误。",
        "第九段文本展示了最佳实践。",
        "第十段文本给出了结论和展望。"
    ]
    
    for i in range(count):
        segment = mock_segment(
            doc_hash=doc_hash,
            text=sample_texts[i % len(sample_texts)],
            page=i // 3,  # 每3个片段一页
            bbox={
                "x": 50.0,
                "y": 100.0 + (i % 3) * 150.0,
                "width": 500.0,
                "height": 100.0
            }
        )
        segments.append(segment)
    return segments


def generate_mock_annotations(
    doc_hash: str,
    version_hash: str,
    count: int = 5
) -> List[Dict[str, Any]]:
    """
    生成多个模拟批注
    
    Args:
        doc_hash: 文档hash
        version_hash: 版本hash
        count: 批注数量
    
    Returns:
        批注列表
    """
    annotations = []
    annotation_types = ["explanation", "question", "summary"]
    sample_contents = [
        "这个概念可以理解为...",
        "为什么会出现这种情况？",
        "总结：本节主要讨论了...",
        "这里需要注意的是...",
        "你能想到其他例子吗？"
    ]
    
    for i in range(count):
        annotation = mock_annotation(
            doc_hash=doc_hash,
            version_hash=version_hash,
            annotation_type=annotation_types[i % len(annotation_types)],
            content=sample_contents[i % len(sample_contents)],
            page=i,
            bbox={
                "x": 100.0,
                "y": 200.0,
                "width": 400.0,
                "height": 80.0
            }
        )
        annotations.append(annotation)
    return annotations


def generate_mock_behaviors(
    doc_hash: str,
    count: int = 20,
    time_span_minutes: int = 60
) -> List[Dict[str, Any]]:
    """
    生成多个模拟行为数据
    
    Args:
        doc_hash: 文档hash
        count: 行为数量
        time_span_minutes: 时间跨度（分钟）
    
    Returns:
        行为列表
    """
    behaviors = []
    event_types = ["page_view", "text_select", "scroll"]
    start_time = datetime.now() - timedelta(minutes=time_span_minutes)
    
    for i in range(count):
        timestamp = start_time + timedelta(minutes=i * time_span_minutes / count)
        event_type = event_types[i % len(event_types)]
        
        metadata = {}
        if event_type == "text_select":
            metadata = {"selected_text": f"选中的文本片段 {i}"}
        elif event_type == "scroll":
            metadata = {"scroll_position": random.randint(0, 1000)}
        
        behavior = mock_behavior(
            doc_hash=doc_hash,
            page=i % 5,  # 在5页之间切换
            event_type=event_type,
            metadata=metadata,
            timestamp=timestamp
        )
        behaviors.append(behavior)
    return behaviors


# ============================================
# 完整场景数据生成
# ============================================

def generate_complete_test_scenario() -> Dict[str, Any]:
    """
    生成一个完整的测试场景，包含文档、片段、批注和行为数据
    
    Returns:
        包含所有测试数据的字典
    """
    # 生成文档
    doc = mock_document(path="/test/learning_material.pdf", status="completed")
    doc_hash = doc["hash"]
    version_hash = doc["version_hash"]
    
    # 生成片段
    segments = generate_mock_segments(doc_hash, count=15)
    
    # 生成批注
    annotations = generate_mock_annotations(doc_hash, version_hash, count=8)
    
    # 生成行为数据
    behaviors = generate_mock_behaviors(doc_hash, count=30, time_span_minutes=120)
    
    return {
        "document": doc,
        "segments": segments,
        "annotations": annotations,
        "behaviors": behaviors
    }


# ============================================
# 边缘情况测试数据
# ============================================

def mock_empty_document() -> Dict[str, Any]:
    """生成空文档（用于测试边缘情况）"""
    return mock_document(path="/test/empty.pdf", status="failed")


def mock_large_segment(doc_hash: str) -> Dict[str, Any]:
    """生成超大片段（用于测试边缘情况）"""
    large_text = "这是一段很长的文本。" * 100  # 1000+ 字符
    return mock_segment(doc_hash=doc_hash, text=large_text)


def mock_special_characters_segment(doc_hash: str) -> Dict[str, Any]:
    """生成包含特殊字符的片段（用于测试边缘情况）"""
    special_text = "测试特殊字符：@#$%^&*()[]{}|\\<>?/~`"
    return mock_segment(doc_hash=doc_hash, text=special_text)


def mock_unicode_segment(doc_hash: str) -> Dict[str, Any]:
    """生成包含Unicode字符的片段（用于测试边缘情况）"""
    unicode_text = "测试Unicode：😀🎉🔥中文English日本語한국어"
    return mock_segment(doc_hash=doc_hash, text=unicode_text)


if __name__ == "__main__":
    # 演示用法
    print("=== 生成测试数据示例 ===\n")
    
    # 生成单个文档
    doc = mock_document()
    print(f"文档: {doc}\n")
    
    # 生成片段
    segment = mock_segment(doc["hash"])
    print(f"片段: {segment}\n")
    
    # 生成批注
    annotation = mock_annotation(doc["hash"], doc["version_hash"])
    print(f"批注: {annotation}\n")
    
    # 生成IPC请求
    request = mock_ipc_request("parse", {"path": "/test/doc.pdf"})
    print(f"IPC请求: {request}\n")
    
    # 生成完整场景
    scenario = generate_complete_test_scenario()
    print(f"完整场景包含:")
    print(f"  - 1个文档")
    print(f"  - {len(scenario['segments'])}个片段")
    print(f"  - {len(scenario['annotations'])}个批注")
    print(f"  - {len(scenario['behaviors'])}个行为记录")
