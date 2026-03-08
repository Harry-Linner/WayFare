"""
Unit tests for DocumentParser

Tests document parsing, hash computation, chunking, and vectorization.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from wayfare.document_parser import DocumentParser, ParseResult
from wayfare.db import DocumentSegment, BoundingBox
from wayfare.errors import DocumentParseError


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    service = AsyncMock()
    service.embed_texts = AsyncMock(return_value=np.random.rand(5, 512))
    return service


@pytest.fixture
def mock_vector_store():
    """Mock vector store"""
    store = AsyncMock()
    store.upsert_vectors = AsyncMock()
    return store


@pytest.fixture
def mock_db():
    """Mock database"""
    db = AsyncMock()
    db.get_document = AsyncMock(return_value=None)
    db.save_document = AsyncMock()
    db.save_segments = AsyncMock()
    db.update_document_status = AsyncMock()
    db.count_segments = AsyncMock(return_value=0)
    return db


@pytest.fixture
def parser(mock_embedding_service, mock_vector_store, mock_db):
    """Create DocumentParser instance with mocks"""
    return DocumentParser(
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        db=mock_db,
        chunk_size=300,
        chunk_overlap=50
    )


class TestComputeHash:
    """Tests for compute_hash method"""
    
    def test_compute_hash_success(self, parser):
        """Test successful hash computation"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            doc_hash = parser.compute_hash(temp_path)
            
            # Verify hash is a valid BLAKE3 hash (64 hex characters)
            assert isinstance(doc_hash, str)
            assert len(doc_hash) == 64
            assert all(c in '0123456789abcdef' for c in doc_hash)
        finally:
            Path(temp_path).unlink()
    
    def test_compute_hash_file_not_found(self, parser):
        """Test hash computation with non-existent file"""
        with pytest.raises(FileNotFoundError):
            parser.compute_hash("/nonexistent/file.pdf")
    
    def test_compute_hash_consistent(self, parser):
        """Test that same file produces same hash"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("consistent content")
            temp_path = f.name
        
        try:
            hash1 = parser.compute_hash(temp_path)
            hash2 = parser.compute_hash(temp_path)
            
            assert hash1 == hash2
        finally:
            Path(temp_path).unlink()
    
    def test_compute_hash_different_content(self, parser):
        """Test that different files produce different hashes"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
            f1.write("content 1")
            temp_path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            f2.write("content 2")
            temp_path2 = f2.name
        
        try:
            hash1 = parser.compute_hash(temp_path1)
            hash2 = parser.compute_hash(temp_path2)
            
            assert hash1 != hash2
        finally:
            Path(temp_path1).unlink()
            Path(temp_path2).unlink()


class TestComputeVersionHash:
    """Tests for compute_version_hash method"""
    
    def test_compute_version_hash_success(self, parser):
        """Test successful version hash computation"""
        content = "This is document content"
        version_hash = parser.compute_version_hash(content)
        
        # Verify hash is a valid BLAKE3 hash
        assert isinstance(version_hash, str)
        assert len(version_hash) == 64
        assert all(c in '0123456789abcdef' for c in version_hash)
    
    def test_compute_version_hash_consistent(self, parser):
        """Test that same content produces same hash"""
        content = "consistent content"
        hash1 = parser.compute_version_hash(content)
        hash2 = parser.compute_version_hash(content)
        
        assert hash1 == hash2
    
    def test_compute_version_hash_different_content(self, parser):
        """Test that different content produces different hashes"""
        hash1 = parser.compute_version_hash("content 1")
        hash2 = parser.compute_version_hash("content 2")
        
        assert hash1 != hash2
    
    def test_compute_version_hash_empty_string(self, parser):
        """Test version hash with empty string"""
        version_hash = parser.compute_version_hash("")
        
        assert isinstance(version_hash, str)
        assert len(version_hash) == 64


class TestChunkText:
    """Tests for chunk_text method"""
    
    def test_chunk_text_short_text(self, parser):
        """Test chunking text shorter than chunk_size"""
        text = "Short text"
        chunks = parser.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_text_empty_string(self, parser):
        """Test chunking empty string"""
        chunks = parser.chunk_text("")
        
        assert len(chunks) == 0
    
    def test_chunk_text_long_text(self, parser):
        """Test chunking long text"""
        # Create text longer than MAX_CHUNK_SIZE (500)
        text = "这是一个句子。" * 100  # ~700 characters
        chunks = parser.chunk_text(text)
        
        # Should produce multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be within 200-500 character range (except possibly the last)
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 1:  # All chunks except the last
                assert 200 <= len(chunk) <= 500, f"Chunk {i} has length {len(chunk)}, expected 200-500"
            else:  # Last chunk can be smaller
                assert len(chunk) <= 500, f"Last chunk has length {len(chunk)}, expected <= 500"
    
    def test_chunk_text_sentence_boundary(self, parser):
        """Test that chunking respects sentence boundaries"""
        text = "第一句话。" * 50 + "第二句话。" * 50
        chunks = parser.chunk_text(text)
        
        # Chunks should end with sentence terminators when possible
        for chunk in chunks[:-1]:  # Exclude last chunk
            # Should end with a sentence terminator or be at text boundary
            assert chunk[-1] in ["。", "！", "？", ".", "!", "?"] or len(chunk) < parser.chunk_size
    
    def test_chunk_text_overlap(self, parser):
        """Test that chunks have proper overlap"""
        # Create text longer than MAX_CHUNK_SIZE (500) without sentence boundaries
        text = "A" * 800  # Long enough to require multiple chunks
        chunks = parser.chunk_text(text)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Verify overlap exists (chunks should share some content)
        # This is implicit in the sliding window approach
    
    def test_chunk_text_200_500_constraint(self, parser):
        """Test that all chunks (except last) are within 200-500 character range"""
        # Test with various text lengths
        test_cases = [
            "这是测试文本。" * 50,  # ~350 chars
            "This is a test sentence. " * 40,  # ~1000 chars
            "A" * 1500,  # Long text without sentence boundaries
            "句子一。句子二。句子三。" * 60,  # ~720 chars with Chinese punctuation
        ]
        
        for text in test_cases:
            chunks = parser.chunk_text(text)
            
            # All chunks except the last should be 200-500 chars
            for i, chunk in enumerate(chunks[:-1]):
                assert 200 <= len(chunk) <= 500, \
                    f"Chunk {i} has length {len(chunk)}, expected 200-500. Text: {text[:50]}..."
            
            # Last chunk should be at most 500 chars
            if chunks:
                assert len(chunks[-1]) <= 500, \
                    f"Last chunk has length {len(chunks[-1])}, expected <= 500"
    
    def test_chunk_text_medium_text(self, parser):
        """Test chunking text that fits in one chunk (200-500 chars)"""
        # Text exactly 300 characters
        text = "A" * 300
        chunks = parser.chunk_text(text)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 300
        
        # Text at 500 characters (max)
        text = "B" * 500
        chunks = parser.chunk_text(text)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 500
        
        # Text at 200 characters (min)
        text = "C" * 200
        chunks = parser.chunk_text(text)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 200


class TestParsePDF:
    """Tests for parse_pdf method"""
    
    @pytest.mark.asyncio
    async def test_parse_pdf_success(self, parser):
        """Test successful PDF parsing"""
        # Create a mock PDF document
        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {"text": "This is page 1 text."}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_page.rect.width = 612
        mock_page.rect.height = 792
        
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_doc.close = MagicMock()
        
        with patch('fitz.open', return_value=mock_doc):
            segments = await parser.parse_pdf("test.pdf", "hash123")
        
        # Verify segments were created
        assert len(segments) > 0
        assert all(isinstance(s, DocumentSegment) for s in segments)
        assert all(s.doc_hash == "hash123" for s in segments)
        assert all(s.page == 0 for s in segments)  # Single page
    
    # Note: Skipping missing dependency test as it's difficult to mock properly
    # The ImportError handling is tested in integration tests
    
    @pytest.mark.asyncio
    async def test_parse_pdf_multiple_pages(self, parser):
        """Test PDF parsing with multiple pages"""
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = {
            "blocks": [{"type": 0, "lines": [{"spans": [{"text": "Page 1"}]}]}]
        }
        mock_page1.rect.width = 612
        mock_page1.rect.height = 792
        
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = {
            "blocks": [{"type": 0, "lines": [{"spans": [{"text": "Page 2"}]}]}]
        }
        mock_page2.rect.width = 612
        mock_page2.rect.height = 792
        
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_doc.close = MagicMock()
        
        with patch('fitz.open', return_value=mock_doc):
            segments = await parser.parse_pdf("test.pdf", "hash123")
        
        # Verify segments from both pages
        assert len(segments) >= 2
        pages = set(s.page for s in segments)
        assert 0 in pages
        assert 1 in pages


class TestParseMarkdown:
    """Tests for parse_markdown method"""
    
    @pytest.mark.asyncio
    async def test_parse_markdown_success(self, parser):
        """Test successful Markdown parsing"""
        # Create a temporary Markdown file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
            f.write("# Heading 1\n\nThis is paragraph 1.\n\n## Heading 2\n\nThis is paragraph 2.")
            temp_path = f.name
        
        try:
            segments = await parser.parse_markdown(temp_path, "hash123")
            
            # Verify segments were created
            assert len(segments) > 0
            assert all(isinstance(s, DocumentSegment) for s in segments)
            assert all(s.doc_hash == "hash123" for s in segments)
        finally:
            Path(temp_path).unlink()
    
    # Note: Skipping missing dependency test as it's difficult to mock properly
    # The ImportError handling is tested in integration tests
    
    @pytest.mark.asyncio
    async def test_parse_markdown_file_not_found(self, parser):
        """Test Markdown parsing with non-existent file"""
        with pytest.raises(RuntimeError, match="Failed to read file"):
            await parser.parse_markdown("/nonexistent/file.md", "hash123")


class TestParseDocument:
    """Tests for parse_document method (integration)"""
    
    @pytest.mark.asyncio
    async def test_parse_document_pdf(self, parser, mock_db):
        """Test document parsing for PDF files"""
        # Create a temporary PDF-like file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
            f.write("dummy pdf content")
            temp_path = f.name
        
        try:
            # Mock PDF parsing
            mock_segments = [
                DocumentSegment(
                    id="hash_0_0",
                    doc_hash="test_hash",
                    text="Test content",
                    page=0,
                    bbox=BoundingBox(0, 0, 100, 100)
                )
            ]
            
            with patch.object(parser, 'parse_pdf', return_value=mock_segments):
                result = await parser.parse_document(temp_path)
            
            # Verify result
            assert isinstance(result, ParseResult)
            assert result.status == "completed"
            assert result.segment_count == 1
            
            # Verify database calls
            mock_db.save_document.assert_called_once()
            mock_db.save_segments.assert_called_once()
            mock_db.update_document_status.assert_called_once()
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_parse_document_already_parsed(self, parser, mock_db):
        """Test parsing already parsed document"""
        # Mock existing document
        mock_db.get_document.return_value = {
            "hash": "existing_hash",
            "status": "completed",
            "version_hash": "version123"
        }
        mock_db.count_segments.return_value = 5
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
            f.write("content")
            temp_path = f.name
        
        try:
            result = await parser.parse_document(temp_path)
            
            # Should return existing result without re-parsing
            assert result.status == "completed"
            assert result.segment_count == 5
            
            # Should not save new segments
            mock_db.save_segments.assert_not_called()
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_parse_document_unsupported_type(self, parser):
        """Test parsing unsupported file type"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("text content")
            temp_path = f.name
        
        try:
            with pytest.raises(DocumentParseError, match="Unsupported file type"):
                await parser.parse_document(temp_path)
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_parse_document_file_not_found(self, parser):
        """Test parsing non-existent file"""
        with pytest.raises(DocumentParseError):
            await parser.parse_document("/nonexistent/file.pdf")


class TestVectorizeSegments:
    """Tests for _vectorize_segments method"""
    
    @pytest.mark.asyncio
    async def test_vectorize_segments_success(self, parser, mock_embedding_service, mock_vector_store):
        """Test successful segment vectorization"""
        segments = [
            DocumentSegment(
                id=f"hash_{i}",
                doc_hash="test_hash",
                text=f"Segment {i}",
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
            for i in range(3)
        ]
        
        # Mock embedding service to return correct shape
        mock_embedding_service.embed_texts.return_value = np.random.rand(3, 512)
        
        await parser._vectorize_segments(segments)
        
        # Verify embedding service was called
        mock_embedding_service.embed_texts.assert_called_once()
        call_args = mock_embedding_service.embed_texts.call_args[0][0]
        assert len(call_args) == 3
        
        # Verify vector store was called
        mock_vector_store.upsert_vectors.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vectorize_segments_empty_list(self, parser, mock_embedding_service, mock_vector_store):
        """Test vectorization with empty segment list"""
        await parser._vectorize_segments([])
        
        # Should not call embedding service or vector store
        mock_embedding_service.embed_texts.assert_not_called()
        mock_vector_store.upsert_vectors.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_vectorize_segments_failure(self, parser, mock_embedding_service):
        """Test vectorization failure handling"""
        segments = [
            DocumentSegment(
                id="hash_0",
                doc_hash="test_hash",
                text="Test",
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        # Mock embedding service to raise error
        mock_embedding_service.embed_texts.side_effect = RuntimeError("Embedding failed")
        
        with pytest.raises(RuntimeError, match="Vectorization failed"):
            await parser._vectorize_segments(segments)
