"""
测试文档解析器的错误处理和恢复机制

验证parse_document()方法在各种错误场景下的行为：
- 文档状态管理（pending/processing/completed/failed）
- 错误恢复机制
- 失败状态的正确设置
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from wayfare.document_parser import DocumentParser, ParseResult
from wayfare.errors import DocumentParseError


class TestErrorHandlingAndRecovery:
    """测试错误处理和恢复机制"""
    
    @pytest.fixture
    def mock_services(self):
        """创建mock服务"""
        embedding_service = AsyncMock()
        vector_store = AsyncMock()
        db = AsyncMock()
        return embedding_service, vector_store, db
    
    @pytest.fixture
    def parser(self, mock_services):
        """创建DocumentParser实例"""
        embedding_service, vector_store, db = mock_services
        return DocumentParser(
            embedding_service=embedding_service,
            vector_store=vector_store,
            db=db
        )
    
    @pytest.mark.asyncio
    async def test_parse_document_sets_failed_status_on_parse_error(self, parser, tmp_path):
        """测试：解析失败时设置failed状态"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash返回固定hash
        parser.compute_hash = MagicMock(return_value="test_hash_123")
        
        # Mock db.get_document返回None（文档不存在）
        parser.db.get_document = AsyncMock(return_value=None)
        
        # Mock parse_pdf抛出异常
        parser.parse_pdf = AsyncMock(side_effect=RuntimeError("PDF parsing failed"))
        
        # Mock db.save_document
        parser.db.save_document = AsyncMock()
        
        # 执行并验证抛出异常
        with pytest.raises(DocumentParseError) as exc_info:
            await parser.parse_document(str(test_file))
        
        assert "PDF parsing failed" in str(exc_info.value)
        
        # 验证save_document被调用两次：一次设置failed状态
        assert parser.db.save_document.call_count >= 1
        
        # 检查最后一次调用是否设置了failed状态
        last_call = parser.db.save_document.call_args_list[-1]
        doc_data = last_call[0][0]
        assert doc_data["status"] == "failed"
        assert doc_data["hash"] == "test_hash_123"
    
    @pytest.mark.asyncio
    async def test_parse_document_sets_failed_status_on_vectorization_error(self, parser, tmp_path):
        """测试：向量化失败时设置failed状态"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash
        parser.compute_hash = MagicMock(return_value="test_hash_456")
        
        # Mock compute_version_hash
        parser.compute_version_hash = MagicMock(return_value="version_hash_456")
        
        # Mock db.get_document返回None
        parser.db.get_document = AsyncMock(return_value=None)
        
        # Mock parse_pdf返回segments
        from wayfare.db import DocumentSegment, BoundingBox
        mock_segment = DocumentSegment(
            id="seg_1",
            doc_hash="test_hash_456",
            text="Test segment",
            page=0,
            bbox=BoundingBox(0, 0, 100, 100)
        )
        parser.parse_pdf = AsyncMock(return_value=[mock_segment])
        
        # Mock db methods
        parser.db.save_document = AsyncMock()
        parser.db.save_segments = AsyncMock()
        
        # Mock _vectorize_segments抛出异常
        parser._vectorize_segments = AsyncMock(side_effect=RuntimeError("Vectorization failed"))
        
        # 执行并验证抛出异常
        with pytest.raises(DocumentParseError) as exc_info:
            await parser.parse_document(str(test_file))
        
        assert "Vectorization failed" in str(exc_info.value)
        
        # 验证save_document被调用设置failed状态
        calls = parser.db.save_document.call_args_list
        assert len(calls) >= 2  # 至少两次：processing和failed
        
        # 检查最后一次调用设置了failed状态
        last_call = calls[-1]
        doc_data = last_call[0][0]
        assert doc_data["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_parse_document_retry_failed_document(self, parser, tmp_path):
        """测试：可以重试失败的文档"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash
        parser.compute_hash = MagicMock(return_value="test_hash_789")
        
        # Mock compute_version_hash
        parser.compute_version_hash = MagicMock(return_value="version_hash_789")
        
        # Mock db.get_document返回failed状态的文档
        parser.db.get_document = AsyncMock(return_value={
            "hash": "test_hash_789",
            "status": "failed",
            "version_hash": "",
            "path": str(test_file)
        })
        
        # Mock parse_pdf返回segments
        from wayfare.db import DocumentSegment, BoundingBox
        mock_segment = DocumentSegment(
            id="seg_1",
            doc_hash="test_hash_789",
            text="Test segment",
            page=0,
            bbox=BoundingBox(0, 0, 100, 100)
        )
        parser.parse_pdf = AsyncMock(return_value=[mock_segment])
        
        # Mock db methods
        parser.db.save_document = AsyncMock()
        parser.db.save_segments = AsyncMock()
        parser.db.update_document_status = AsyncMock()
        
        # Mock _vectorize_segments
        parser._vectorize_segments = AsyncMock()
        
        # 执行
        result = await parser.parse_document(str(test_file))
        
        # 验证结果
        assert result.status == "completed"
        assert result.doc_hash == "test_hash_789"
        
        # 验证文档被重新处理
        assert parser.parse_pdf.called
        assert parser.db.save_segments.called
        assert parser._vectorize_segments.called
    
    @pytest.mark.asyncio
    async def test_parse_document_handles_processing_state(self, parser, tmp_path):
        """测试：处理processing状态的文档（允许重试）"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash
        parser.compute_hash = MagicMock(return_value="test_hash_proc")
        
        # Mock compute_version_hash
        parser.compute_version_hash = MagicMock(return_value="version_hash_proc")
        
        # Mock db.get_document返回processing状态
        parser.db.get_document = AsyncMock(return_value={
            "hash": "test_hash_proc",
            "status": "processing",
            "version_hash": "old_version",
            "path": str(test_file)
        })
        
        # Mock parse_pdf返回segments
        from wayfare.db import DocumentSegment, BoundingBox
        mock_segment = DocumentSegment(
            id="seg_1",
            doc_hash="test_hash_proc",
            text="Test segment",
            page=0,
            bbox=BoundingBox(0, 0, 100, 100)
        )
        parser.parse_pdf = AsyncMock(return_value=[mock_segment])
        
        # Mock db methods
        parser.db.save_document = AsyncMock()
        parser.db.save_segments = AsyncMock()
        parser.db.update_document_status = AsyncMock()
        
        # Mock _vectorize_segments
        parser._vectorize_segments = AsyncMock()
        
        # 执行
        result = await parser.parse_document(str(test_file))
        
        # 验证允许重试
        assert result.status == "completed"
        assert parser.parse_pdf.called
    
    @pytest.mark.asyncio
    async def test_parse_document_no_segments_extracted(self, parser, tmp_path):
        """测试：未提取到任何片段时设置failed状态"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash
        parser.compute_hash = MagicMock(return_value="test_hash_empty")
        
        # Mock db.get_document返回None
        parser.db.get_document = AsyncMock(return_value=None)
        
        # Mock parse_pdf返回空列表
        parser.parse_pdf = AsyncMock(return_value=[])
        
        # Mock db.save_document
        parser.db.save_document = AsyncMock()
        
        # 执行并验证抛出异常
        with pytest.raises(DocumentParseError) as exc_info:
            await parser.parse_document(str(test_file))
        
        assert "No segments extracted" in str(exc_info.value)
        
        # 验证设置了failed状态
        calls = parser.db.save_document.call_args_list
        assert len(calls) >= 1
        last_call = calls[-1]
        doc_data = last_call[0][0]
        assert doc_data["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_parse_document_version_hash_computation_error(self, parser, tmp_path):
        """测试：版本hash计算失败时设置failed状态"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash
        parser.compute_hash = MagicMock(return_value="test_hash_vh")
        
        # Mock db.get_document返回None
        parser.db.get_document = AsyncMock(return_value=None)
        
        # Mock parse_pdf返回segments
        from wayfare.db import DocumentSegment, BoundingBox
        mock_segment = DocumentSegment(
            id="seg_1",
            doc_hash="test_hash_vh",
            text="Test segment",
            page=0,
            bbox=BoundingBox(0, 0, 100, 100)
        )
        parser.parse_pdf = AsyncMock(return_value=[mock_segment])
        
        # Mock compute_version_hash抛出异常
        parser.compute_version_hash = MagicMock(side_effect=RuntimeError("Hash computation failed"))
        
        # Mock db.save_document
        parser.db.save_document = AsyncMock()
        
        # 执行并验证抛出异常
        with pytest.raises(DocumentParseError) as exc_info:
            await parser.parse_document(str(test_file))
        
        assert "Hash computation failed" in str(exc_info.value)
        
        # 验证设置了failed状态
        calls = parser.db.save_document.call_args_list
        assert len(calls) >= 1
        last_call = calls[-1]
        doc_data = last_call[0][0]
        assert doc_data["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_parse_document_completed_not_reprocessed(self, parser, tmp_path):
        """测试：已完成的文档不会被重新处理"""
        # 创建测试文件
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")
        
        # Mock compute_hash
        parser.compute_hash = MagicMock(return_value="test_hash_completed")
        
        # Mock db.get_document返回completed状态
        parser.db.get_document = AsyncMock(return_value={
            "hash": "test_hash_completed",
            "status": "completed",
            "version_hash": "existing_version",
            "path": str(test_file)
        })
        
        # Mock db.count_segments
        parser.db.count_segments = AsyncMock(return_value=5)
        
        # Mock parse_pdf（不应该被调用）
        parser.parse_pdf = AsyncMock()
        
        # 执行
        result = await parser.parse_document(str(test_file))
        
        # 验证返回已有结果
        assert result.status == "completed"
        assert result.doc_hash == "test_hash_completed"
        assert result.version_hash == "existing_version"
        assert result.segment_count == 5
        
        # 验证parse_pdf未被调用
        assert not parser.parse_pdf.called
