"""
测试示例文档的可用性

验证tests/fixtures/sample_documents/目录下的示例文档可以被正确读取和解析。
"""

import pytest
from pathlib import Path


# 示例文档路径
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_documents"


def test_sample_documents_directory_exists():
    """测试示例文档目录存在"""
    assert FIXTURES_DIR.exists(), "示例文档目录不存在"
    assert FIXTURES_DIR.is_dir(), "示例文档路径不是目录"


def test_markdown_files_exist():
    """测试Markdown示例文件存在"""
    simple_md = FIXTURES_DIR / "simple_test.md"
    sample_md = FIXTURES_DIR / "sample_markdown.md"
    
    assert simple_md.exists(), "simple_test.md 不存在"
    assert sample_md.exists(), "sample_markdown.md 不存在"


def test_pdf_files_exist():
    """测试PDF示例文件存在"""
    simple_pdf = FIXTURES_DIR / "simple_test.pdf"
    sample_pdf = FIXTURES_DIR / "sample_learning_material.pdf"
    
    assert simple_pdf.exists(), "simple_test.pdf 不存在"
    assert sample_pdf.exists(), "sample_learning_material.pdf 不存在"


def test_markdown_files_readable():
    """测试Markdown文件可读"""
    simple_md = FIXTURES_DIR / "simple_test.md"
    sample_md = FIXTURES_DIR / "sample_markdown.md"
    
    # 读取simple_test.md
    with open(simple_md, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "simple_test.md 内容为空"
        assert "简单测试文档" in content, "simple_test.md 内容不正确"
    
    # 读取sample_markdown.md
    with open(sample_md, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "sample_markdown.md 内容为空"
        assert "费曼学习法" in content, "sample_markdown.md 内容不正确"


def test_pdf_files_readable():
    """测试PDF文件可读"""
    simple_pdf = FIXTURES_DIR / "simple_test.pdf"
    sample_pdf = FIXTURES_DIR / "sample_learning_material.pdf"
    
    # 检查文件大小
    assert simple_pdf.stat().st_size > 0, "simple_test.pdf 文件大小为0"
    assert sample_pdf.stat().st_size > 0, "sample_learning_material.pdf 文件大小为0"
    
    # 检查PDF文件头
    with open(simple_pdf, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF', "simple_test.pdf 不是有效的PDF文件"
    
    with open(sample_pdf, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF', "sample_learning_material.pdf 不是有效的PDF文件"


def test_mock_data_module_importable():
    """测试mock_data模块可导入"""
    from tests.fixtures import mock_data
    
    # 验证主要函数存在
    assert hasattr(mock_data, 'mock_document')
    assert hasattr(mock_data, 'mock_segment')
    assert hasattr(mock_data, 'mock_annotation')
    assert hasattr(mock_data, 'mock_behavior')
    assert hasattr(mock_data, 'mock_ipc_request')
    assert hasattr(mock_data, 'mock_ipc_response')
    assert hasattr(mock_data, 'generate_complete_test_scenario')


def test_mock_data_functions():
    """测试mock_data函数可用"""
    from tests.fixtures.mock_data import (
        mock_document,
        mock_segment,
        mock_annotation,
        generate_complete_test_scenario
    )
    
    # 测试生成文档
    doc = mock_document()
    assert "hash" in doc
    assert "path" in doc
    assert "status" in doc
    assert "version_hash" in doc
    
    # 测试生成片段
    segment = mock_segment(doc["hash"])
    assert "id" in segment
    assert "doc_hash" in segment
    assert segment["doc_hash"] == doc["hash"]
    
    # 测试生成批注
    annotation = mock_annotation(doc["hash"], doc["version_hash"])
    assert "id" in annotation
    assert "doc_hash" in annotation
    assert annotation["doc_hash"] == doc["hash"]
    
    # 测试生成完整场景
    scenario = generate_complete_test_scenario()
    assert "document" in scenario
    assert "segments" in scenario
    assert "annotations" in scenario
    assert "behaviors" in scenario
    assert len(scenario["segments"]) > 0
    assert len(scenario["annotations"]) > 0
    assert len(scenario["behaviors"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
