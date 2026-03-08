"""
测试mock_data的基本功能

验证mock_data生成的数据格式正确，可以用于测试。
这些测试展示了如何在测试中使用mock_data。
"""

import pytest
from tests.fixtures.mock_data import (
    mock_document,
    mock_segment,
    mock_annotation,
    mock_behavior,
    mock_ipc_request,
    mock_ipc_response,
    generate_complete_test_scenario
)


def test_mock_document_format():
    """测试mock文档数据格式正确"""
    doc = mock_document(path="/test/doc.pdf", status="completed")
    
    # 验证必需字段存在
    assert "hash" in doc
    assert "path" in doc
    assert "status" in doc
    assert "updated_at" in doc
    assert "version_hash" in doc
    
    # 验证字段值正确
    assert doc["path"] == "/test/doc.pdf"
    assert doc["status"] == "completed"
    assert doc["hash"].startswith("doc_")
    assert doc["version_hash"].startswith("ver_")


def test_mock_segment_format():
    """测试mock片段数据格式正确"""
    doc_hash = "test_doc_hash"
    segment = mock_segment(doc_hash, text="测试文本", page=0)
    
    # 验证必需字段存在
    assert "id" in segment
    assert "doc_hash" in segment
    assert "text" in segment
    assert "page" in segment
    assert "bbox_x" in segment
    assert "bbox_y" in segment
    assert "bbox_width" in segment
    assert "bbox_height" in segment
    
    # 验证字段值正确
    assert segment["doc_hash"] == doc_hash
    assert segment["text"] == "测试文本"
    assert segment["page"] == 0


def test_mock_annotation_format():
    """测试mock批注数据格式正确"""
    doc_hash = "test_doc_hash"
    version_hash = "test_version_hash"
    annotation = mock_annotation(
        doc_hash,
        version_hash,
        annotation_type="explanation",
        content="测试批注"
    )
    
    # 验证必需字段存在
    assert "id" in annotation
    assert "doc_hash" in annotation
    assert "version_hash" in annotation
    assert "type" in annotation
    assert "content" in annotation
    assert "created_at" in annotation
    
    # 验证字段值正确
    assert annotation["doc_hash"] == doc_hash
    assert annotation["version_hash"] == version_hash
    assert annotation["type"] == "explanation"
    assert annotation["content"] == "测试批注"


def test_mock_behavior_format():
    """测试mock行为数据格式正确"""
    doc_hash = "test_doc_hash"
    behavior = mock_behavior(
        doc_hash,
        page=0,
        event_type="page_view"
    )
    
    # 验证必需字段存在
    assert "id" in behavior
    assert "doc_hash" in behavior
    assert "page" in behavior
    assert "event_type" in behavior
    assert "timestamp" in behavior
    assert "metadata" in behavior
    
    # 验证字段值正确
    assert behavior["doc_hash"] == doc_hash
    assert behavior["page"] == 0
    assert behavior["event_type"] == "page_view"


def test_complete_scenario_structure():
    """测试完整场景数据结构正确"""
    scenario = generate_complete_test_scenario()
    
    # 验证场景包含所有必需部分
    assert "document" in scenario
    assert "segments" in scenario
    assert "annotations" in scenario
    assert "behaviors" in scenario
    
    # 验证数据数量
    assert len(scenario["segments"]) > 0
    assert len(scenario["annotations"]) > 0
    assert len(scenario["behaviors"]) > 0
    
    # 验证数据关联性
    doc_hash = scenario["document"]["hash"]
    for segment in scenario["segments"]:
        assert segment["doc_hash"] == doc_hash
    for annotation in scenario["annotations"]:
        assert annotation["doc_hash"] == doc_hash
    for behavior in scenario["behaviors"]:
        assert behavior["doc_hash"] == doc_hash


def test_mock_ipc_request_format():
    """测试mock IPC请求格式正确"""
    # 生成parse请求
    request = mock_ipc_request("parse", {"path": "/test/doc.pdf"})
    
    # 验证格式
    assert "id" in request
    assert "seq" in request
    assert "method" in request
    assert "params" in request
    assert request["method"] == "parse"
    assert request["params"]["path"] == "/test/doc.pdf"


def test_mock_ipc_response_format():
    """测试mock IPC响应格式正确"""
    # 生成成功响应
    response = mock_ipc_response(
        request_id="test-id",
        seq=1,
        success=True,
        data={"docHash": "abc123"}
    )
    
    # 验证格式
    assert response["id"] == "test-id"
    assert response["seq"] == 1
    assert response["success"] is True
    assert "data" in response
    assert response["data"]["docHash"] == "abc123"
    
    # 生成失败响应
    error_response = mock_ipc_response(
        request_id="test-id",
        seq=2,
        success=False,
        error="Test error"
    )
    
    # 验证格式
    assert error_response["success"] is False
    assert "error" in error_response
    assert error_response["error"] == "Test error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
