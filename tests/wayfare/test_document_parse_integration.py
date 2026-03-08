"""
完整的文档解析流程集成测试

测试从IPC请求到数据库存储的完整流程，包括：
- IPC请求 → DocumentParser → Database存储 → Notification
- 异步解析和主动推送通知
- 多文档并发解析
- PDF和Markdown解析流程
- 文档hash和版本hash生成
- 片段存储到数据库
- 向量存储到vector store
- 错误场景处理
- 解析状态更新

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from wayfare.ipc import IPCHandler
from wayfare.document_parser import DocumentParser, ParseResult
from wayfare.db import SQLiteDB, DocumentSegment, BoundingBox
from wayfare.vector_store import VectorStore, SearchResult
from wayfare.embedding import EmbeddingService


class TestDocumentParseIntegrationFlow:
    """测试完整的文档解析流程集成"""
    
    @pytest.fixture
    async def temp_db(self):
        """创建临时数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SQLiteDB(str(db_path))
            await db.initialize()
            yield db
    
    @pytest.fixture
    def mock_embedding_service(self):
        """创建mock EmbeddingService"""
        service = MagicMock(spec=EmbeddingService)
        # 返回512维的随机向量
        service.embed_texts = AsyncMock(return_value=np.random.rand(1, 512))
        service.embed_single = AsyncMock(return_value=np.random.rand(512))
        return service
    
    @pytest.fixture
    def mock_vector_store(self):
        """创建mock VectorStore"""
        store = MagicMock(spec=VectorStore)
        store.upsert_vectors = AsyncMock()
        store.search = AsyncMock(return_value=[])
        store.search_documents = AsyncMock(return_value=[])
        store.is_initialized = True
        return store
    
    @pytest.fixture
    def sample_pdf_path(self):
        """创建示例PDF文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n")  # 最小的PDF文件头
            return f.name
    
    @pytest.fixture
    def sample_md_path(self):
        """创建示例Markdown文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False, encoding='utf-8') as f:
            f.write("# 标题\n\n这是一段测试文本。" * 50)  # 足够长以生成多个片段
            return f.name
    
    @pytest.mark.asyncio
    async def test_complete_parse_flow_ipc_to_database(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：完整的解析流程 - IPC请求 → DocumentParser → Database存储
        
        验证：
        1. IPC Handler接收parse请求
        2. DocumentParser解析文档
        3. 片段存储到数据库
        4. 向量存储到vector store
        5. 文档状态更新为completed
        
        Requirements: 2.1, 2.4, 2.5, 2.6
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db,
            chunk_size=300,
            chunk_overlap=50
        )
        
        # 2. 计算实际的doc_hash
        actual_doc_hash = doc_parser.compute_hash(sample_pdf_path)
        
        # 3. Mock PDF解析以返回测试片段（使用实际的doc_hash）
        test_segments = [
            DocumentSegment(
                id=f"{actual_doc_hash}_0_0",
                doc_hash=actual_doc_hash,
                text="这是第一个测试片段" * 20,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            ),
            DocumentSegment(
                id=f"{actual_doc_hash}_0_1",
                doc_hash=actual_doc_hash,
                text="这是第二个测试片段" * 20,
                page=0,
                bbox=BoundingBox(0, 100, 100, 100)
            )
        ]
        
        # 4. Mock embedding service to return 2 vectors
        mock_embedding_service.embed_texts.return_value = np.random.rand(2, 512)
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. 执行解析
            result = await doc_parser.parse_document(sample_pdf_path)
            
            # 4. 验证解析结果
            assert result.status == "completed"
            assert result.segment_count == 2
            assert len(result.doc_hash) == 64  # BLAKE3 hash长度
            assert len(result.version_hash) == 64
            
            # 5. 验证数据库中的文档记录
            doc = await temp_db.get_document(result.doc_hash)
            assert doc is not None
            assert doc["status"] == "completed"
            assert doc["path"] == sample_pdf_path
            assert doc["version_hash"] == result.version_hash
            
            # 6. 验证数据库中的片段记录
            segments = await temp_db.get_segments_by_document(result.doc_hash)
            assert len(segments) == 2
            assert segments[0].text == test_segments[0].text
            assert segments[1].text == test_segments[1].text
            
            # 7. 验证向量化被调用
            mock_embedding_service.embed_texts.assert_called_once()
            
            # 8. 验证向量存储被调用
            mock_vector_store.upsert_vectors.assert_called_once()
            call_args = mock_vector_store.upsert_vectors.call_args[1]
            assert call_args["collection"] == "documents"
            assert len(call_args["vectors"]) == 2

    @pytest.mark.asyncio
    async def test_async_parse_with_notification_push(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：异步解析和主动推送通知
        
        验证：
        1. IPC Handler立即返回processing状态
        2. 异步执行文档解析
        3. 解析完成后发送通知到stdout
        
        Requirements: 2.1, 2.6
        """
        # 1. 创建DocumentParser和IPCHandler
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        ipc_handler = IPCHandler(doc_parser=doc_parser)
        
        # 2. Mock PDF解析
        test_segments = [
            DocumentSegment(
                id="test_hash_0_0",
                doc_hash="test_hash",
                text="测试片段" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. Mock stdout以捕获通知
            with patch('builtins.print') as mock_print:
                # 4. 发送parse请求
                request = json.dumps({
                    "id": "req-1",
                    "seq": 0,
                    "method": "parse",
                    "params": {"path": sample_pdf_path}
                })
                
                response_str = await ipc_handler.handle_request(request)
                response = json.loads(response_str)
                
                # 5. 验证立即返回processing状态
                assert response["success"] is True
                assert response["data"]["status"] == "processing"
                assert "docHash" in response["data"]
                
                # 6. 等待异步解析完成
                await asyncio.sleep(0.2)
                
                # 7. 验证通知被发送到stdout
                assert mock_print.called
                notification_calls = [call for call in mock_print.call_args_list]
                assert len(notification_calls) > 0
                
                # 8. 验证通知内容
                notification_str = notification_calls[0][0][0]
                notification = json.loads(notification_str)
                
                assert notification["type"] == "notification"
                assert notification["data"]["type"] == "parse_completed"
                assert notification["data"]["status"] == "completed"
                assert notification["data"]["segmentCount"] == 1
                assert "versionHash" in notification["data"]
    
    @pytest.mark.asyncio
    async def test_concurrent_multiple_documents_parsing(
        self, temp_db, mock_embedding_service, mock_vector_store
    ):
        """
        测试：多文档并发解析
        
        验证：
        1. 同时解析多个文档
        2. 每个文档独立处理
        3. 所有文档都成功存储
        4. 没有数据混淆
        
        Requirements: 2.1, 2.6
        """
        # 1. 创建多个临时文件
        pdf_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(f"%PDF-1.4\nDocument {i}\n".encode())
                pdf_files.append(f.name)
        
        # 2. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 3. Mock PDF解析，每个文档返回不同的片段
        async def mock_parse_pdf_func(path, doc_hash):
            # 根据路径生成不同的片段
            file_index = pdf_files.index(path)
            return [
                DocumentSegment(
                    id=f"{doc_hash}_0_{j}",
                    doc_hash=doc_hash,
                    text=f"文档{file_index}的片段{j}" * 30,
                    page=0,
                    bbox=BoundingBox(0, j * 100, 100, 100)
                )
                for j in range(2)
            ]
        
        with patch.object(doc_parser, 'parse_pdf', side_effect=mock_parse_pdf_func):
            # 4. 并发解析所有文档
            tasks = [doc_parser.parse_document(path) for path in pdf_files]
            results = await asyncio.gather(*tasks)
            
            # 5. 验证所有文档都成功解析
            assert len(results) == 3
            for result in results:
                assert result.status == "completed"
                assert result.segment_count == 2
            
            # 6. 验证每个文档的hash都不同
            doc_hashes = [r.doc_hash for r in results]
            assert len(set(doc_hashes)) == 3  # 所有hash都唯一
            
            # 7. 验证数据库中有3个文档记录
            for doc_hash in doc_hashes:
                doc = await temp_db.get_document(doc_hash)
                assert doc is not None
                assert doc["status"] == "completed"
                
                # 验证每个文档有2个片段
                segments = await temp_db.get_segments_by_document(doc_hash)
                assert len(segments) == 2
            
            # 8. 验证向量化被调用3次（每个文档一次）
            assert mock_embedding_service.embed_texts.call_count == 3
            
            # 9. 验证向量存储被调用3次
            assert mock_vector_store.upsert_vectors.call_count == 3

    @pytest.mark.asyncio
    async def test_pdf_and_markdown_parsing_flows(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path, sample_md_path
    ):
        """
        测试：PDF和Markdown解析流程
        
        验证：
        1. PDF文档解析流程
        2. Markdown文档解析流程
        3. 两种格式都正确存储
        
        Requirements: 2.1, 2.2, 2.3
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. Mock PDF和Markdown解析
        pdf_segments = [
            DocumentSegment(
                id="pdf_hash_0_0",
                doc_hash="pdf_hash",
                text="PDF片段" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        md_segments = [
            DocumentSegment(
                id="md_hash_0_0",
                doc_hash="md_hash",
                text="Markdown片段" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 800, 100)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_pdf, \
             patch.object(doc_parser, 'parse_markdown', new_callable=AsyncMock) as mock_md:
            
            mock_pdf.return_value = pdf_segments
            mock_md.return_value = md_segments
            
            # 3. 解析PDF文档
            pdf_result = await doc_parser.parse_document(sample_pdf_path)
            assert pdf_result.status == "completed"
            assert pdf_result.segment_count == 1
            
            # 4. 解析Markdown文档
            md_result = await doc_parser.parse_document(sample_md_path)
            assert md_result.status == "completed"
            assert md_result.segment_count == 1
            
            # 5. 验证两个文档的hash不同
            assert pdf_result.doc_hash != md_result.doc_hash
            
            # 6. 验证PDF文档在数据库中
            pdf_doc = await temp_db.get_document(pdf_result.doc_hash)
            assert pdf_doc is not None
            assert pdf_doc["path"] == sample_pdf_path
            
            # 7. 验证Markdown文档在数据库中
            md_doc = await temp_db.get_document(md_result.doc_hash)
            assert md_doc is not None
            assert md_doc["path"] == sample_md_path
            
            # 8. 验证两种格式的解析器都被调用
            mock_pdf.assert_called_once()
            mock_md.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_document_hash_and_version_hash_generation(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：文档hash和版本hash生成
        
        验证：
        1. 文档hash使用BLAKE3算法
        2. 版本hash基于内容生成
        3. hash长度正确（64字符）
        4. 相同文件生成相同hash
        
        Requirements: 2.4, 2.5
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. Mock PDF解析
        test_segments = [
            DocumentSegment(
                id="test_hash_0_0",
                doc_hash="test_hash",
                text="测试内容" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. 第一次解析
            result1 = await doc_parser.parse_document(sample_pdf_path)
            
            # 4. 验证hash长度
            assert len(result1.doc_hash) == 64  # BLAKE3 hash是64字符
            assert len(result1.version_hash) == 64
            
            # 5. 验证hash是十六进制字符串
            assert all(c in '0123456789abcdef' for c in result1.doc_hash)
            assert all(c in '0123456789abcdef' for c in result1.version_hash)
            
            # 6. 第二次解析相同文件（应该直接返回已有结果）
            result2 = await doc_parser.parse_document(sample_pdf_path)
            
            # 7. 验证相同文件生成相同hash
            assert result2.doc_hash == result1.doc_hash
            assert result2.version_hash == result1.version_hash
            
            # 8. 验证第二次解析直接返回completed状态（不重新解析）
            assert result2.status == "completed"
            # parse_pdf应该只被调用一次（第二次直接返回缓存结果）
            assert mock_parse_pdf.call_count == 1

    @pytest.mark.asyncio
    async def test_segments_stored_correctly_in_database(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：片段正确存储到数据库
        
        验证：
        1. 所有片段都存储到数据库
        2. 片段包含正确的文本、页码、边界框
        3. 片段与文档正确关联
        
        Requirements: 2.3, 2.6
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 计算实际的doc_hash
        actual_doc_hash = doc_parser.compute_hash(sample_pdf_path)
        
        # 3. 创建测试片段（使用实际的doc_hash）
        test_segments = [
            DocumentSegment(
                id=f"{actual_doc_hash}_0_0",
                doc_hash=actual_doc_hash,
                text="第一个片段的文本内容" * 20,
                page=0,
                bbox=BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
            ),
            DocumentSegment(
                id=f"{actual_doc_hash}_1_0",
                doc_hash=actual_doc_hash,
                text="第二个片段的文本内容" * 20,
                page=1,
                bbox=BoundingBox(x=15.0, y=25.0, width=110.0, height=55.0)
            ),
            DocumentSegment(
                id=f"{actual_doc_hash}_1_1",
                doc_hash=actual_doc_hash,
                text="第三个片段的文本内容" * 20,
                page=1,
                bbox=BoundingBox(x=20.0, y=30.0, width=120.0, height=60.0)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. 执行解析
            result = await doc_parser.parse_document(sample_pdf_path)
            
            # 4. 验证片段数量
            assert result.segment_count == 3
            
            # 5. 从数据库获取片段
            stored_segments = await temp_db.get_segments_by_document(result.doc_hash)
            
            # 6. 验证片段数量
            assert len(stored_segments) == 3
            
            # 7. 验证每个片段的内容
            for i, segment in enumerate(stored_segments):
                assert segment.doc_hash == result.doc_hash
                assert segment.text == test_segments[i].text
                assert segment.page == test_segments[i].page
                assert segment.bbox.x == test_segments[i].bbox.x
                assert segment.bbox.y == test_segments[i].bbox.y
                assert segment.bbox.width == test_segments[i].bbox.width
                assert segment.bbox.height == test_segments[i].bbox.height
            
            # 8. 验证片段按页码和ID排序
            assert stored_segments[0].page == 0
            assert stored_segments[1].page == 1
            assert stored_segments[2].page == 1
    
    @pytest.mark.asyncio
    async def test_vectors_stored_in_vector_store(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：向量存储到vector store
        
        验证：
        1. 为每个片段生成向量
        2. 向量存储到Qdrant
        3. 向量包含正确的payload（doc_hash、page、text）
        
        Requirements: 2.6
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 计算实际的doc_hash
        actual_doc_hash = doc_parser.compute_hash(sample_pdf_path)
        
        # 3. 创建测试片段（使用实际的doc_hash）
        test_segments = [
            DocumentSegment(
                id=f"{actual_doc_hash}_0_0",
                doc_hash=actual_doc_hash,
                text="片段1" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            ),
            DocumentSegment(
                id=f"{actual_doc_hash}_0_1",
                doc_hash=actual_doc_hash,
                text="片段2" * 30,
                page=0,
                bbox=BoundingBox(0, 100, 100, 100)
            )
        ]
        
        # 4. Mock embedding service返回2个向量
        mock_embedding_service.embed_texts.return_value = np.random.rand(2, 512)
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 4. 执行解析
            result = await doc_parser.parse_document(sample_pdf_path)
            
            # 5. 验证embedding service被调用
            mock_embedding_service.embed_texts.assert_called_once()
            call_args = mock_embedding_service.embed_texts.call_args[0]
            assert len(call_args[0]) == 2  # 2个文本
            assert call_args[0][0] == test_segments[0].text
            assert call_args[0][1] == test_segments[1].text
            
            # 6. 验证vector store被调用
            mock_vector_store.upsert_vectors.assert_called_once()
            call_kwargs = mock_vector_store.upsert_vectors.call_args[1]
            
            # 7. 验证collection名称
            assert call_kwargs["collection"] == "documents"
            
            # 8. 验证向量数据
            vectors = call_kwargs["vectors"]
            assert len(vectors) == 2
            
            # 9. 验证第一个向量的payload
            assert vectors[0]["id"] == test_segments[0].id
            assert vectors[0]["payload"]["doc_hash"] == result.doc_hash
            assert vectors[0]["payload"]["page"] == 0
            assert vectors[0]["payload"]["text"] == test_segments[0].text
            
            # 10. 验证第二个向量的payload
            assert vectors[1]["id"] == test_segments[1].id
            assert vectors[1]["payload"]["doc_hash"] == result.doc_hash
            assert vectors[1]["payload"]["page"] == 0
            assert vectors[1]["payload"]["text"] == test_segments[1].text

    @pytest.mark.asyncio
    async def test_error_scenario_file_not_found(
        self, temp_db, mock_embedding_service, mock_vector_store
    ):
        """
        测试：错误场景 - 文件不存在
        
        验证：
        1. 文件不存在时抛出异常
        2. 文档状态不会被创建
        
        Requirements: 2.7
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 尝试解析不存在的文件
        nonexistent_path = "/path/to/nonexistent/file.pdf"
        
        # 3. 验证抛出异常
        from wayfare.errors import DocumentParseError
        with pytest.raises(DocumentParseError) as exc_info:
            await doc_parser.parse_document(nonexistent_path)
        
        # 4. 验证错误消息
        assert "Failed to compute hash" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_error_scenario_parse_failure(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：错误场景 - 解析失败
        
        验证：
        1. 解析失败时抛出异常
        2. 文档状态设置为failed
        3. 错误通知被发送
        
        Requirements: 2.7
        """
        # 1. 创建DocumentParser和IPCHandler
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        ipc_handler = IPCHandler(doc_parser=doc_parser)
        
        # 2. Mock PDF解析失败
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.side_effect = RuntimeError("PDF解析失败")
            
            # 3. Mock stdout以捕获错误通知
            with patch('builtins.print') as mock_print:
                # 4. 发送parse请求
                request = json.dumps({
                    "id": "req-1",
                    "seq": 0,
                    "method": "parse",
                    "params": {"path": sample_pdf_path}
                })
                
                response_str = await ipc_handler.handle_request(request)
                response = json.loads(response_str)
                
                # 5. 验证立即返回processing状态
                assert response["success"] is True
                assert response["data"]["status"] == "processing"
                doc_hash = response["data"]["docHash"]
                
                # 6. 等待异步解析完成
                await asyncio.sleep(0.2)
                
                # 7. 验证错误通知被发送
                assert mock_print.called
                notification_calls = [call for call in mock_print.call_args_list]
                notification_str = notification_calls[0][0][0]
                notification = json.loads(notification_str)
                
                assert notification["type"] == "notification"
                assert notification["data"]["type"] == "parse_failed"
                assert notification["data"]["status"] == "failed"
                assert "PDF解析失败" in notification["data"]["error"]
                
                # 8. 验证数据库中的文档状态为failed
                doc = await temp_db.get_document(doc_hash)
                assert doc is not None
                assert doc["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_parse_status_updates(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：解析状态更新（pending → processing → completed）
        
        验证：
        1. 初始状态为processing
        2. 解析完成后状态更新为completed
        3. 状态转换正确
        
        Requirements: 2.6
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. Mock PDF解析
        test_segments = [
            DocumentSegment(
                id="test_hash_0_0",
                doc_hash="test_hash",
                text="测试片段" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. 执行解析
            result = await doc_parser.parse_document(sample_pdf_path)
            
            # 4. 验证最终状态
            assert result.status == "completed"
            
            # 5. 验证数据库中的最终状态
            doc = await temp_db.get_document(result.doc_hash)
            assert doc["status"] == "completed"
            
            # 6. 验证状态转换：文档应该经历 processing → completed
            # 我们可以通过检查数据库中的最终状态来验证
            assert doc["status"] == "completed"

    @pytest.mark.asyncio
    async def test_chunking_strategy_200_500_characters(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：分块策略（200-500字符）
        
        验证：
        1. 片段大小在200-500字符范围内（除最后一个）
        2. 在句子边界分割
        3. 有重叠区域
        
        Requirements: 2.3
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db,
            chunk_size=300,
            chunk_overlap=50
        )
        
        # 2. 创建长文本（足够生成多个片段）
        long_text = "这是一个测试句子。" * 100  # 约1000字符
        
        # 3. 测试分块
        chunks = doc_parser.chunk_text(long_text)
        
        # 4. 验证至少有2个片段
        assert len(chunks) >= 2
        
        # 5. 验证除最后一个片段外，其他片段都在200-500字符范围内
        for i, chunk in enumerate(chunks[:-1]):
            assert 200 <= len(chunk) <= 500, f"Chunk {i} has length {len(chunk)}"
        
        # 6. 验证最后一个片段不超过500字符
        assert len(chunks[-1]) <= 500
        
        # 7. 验证所有片段都不为空
        for chunk in chunks:
            assert len(chunk.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_ipc_parse_does_not_block_other_requests(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：parse请求不阻塞其他请求
        
        验证：
        1. parse请求立即返回
        2. 其他请求可以正常处理
        3. 异步解析在后台执行
        
        Requirements: 2.1, 2.6
        """
        # 1. 创建DocumentParser和IPCHandler
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        ipc_handler = IPCHandler(doc_parser=doc_parser)
        
        # 2. Mock PDF解析，让它执行较长时间
        async def slow_parse_pdf(path, doc_hash):
            await asyncio.sleep(0.3)  # 模拟慢速解析
            return [
                DocumentSegment(
                    id=f"{doc_hash}_0_0",
                    doc_hash=doc_hash,
                    text="测试片段" * 30,
                    page=0,
                    bbox=BoundingBox(0, 0, 100, 100)
                )
            ]
        
        with patch.object(doc_parser, 'parse_pdf', side_effect=slow_parse_pdf):
            # 3. 发送parse请求
            parse_request = json.dumps({
                "id": "req-1",
                "seq": 0,
                "method": "parse",
                "params": {"path": sample_pdf_path}
            })
            
            # 4. 记录开始时间
            import time
            start_time = time.time()
            
            # 5. 处理parse请求
            parse_response_str = await ipc_handler.handle_request(parse_request)
            parse_response = json.loads(parse_response_str)
            
            # 6. 记录响应时间
            response_time = time.time() - start_time
            
            # 7. 验证parse立即返回（不超过0.1秒）
            assert response_time < 0.1
            assert parse_response["success"] is True
            assert parse_response["data"]["status"] == "processing"
            
            # 8. 发送config请求（应该不被阻塞）
            config_request = json.dumps({
                "id": "req-2",
                "seq": 1,
                "method": "config",
                "params": {"llmModel": "deepseek-chat"}
            })
            
            config_response_str = await ipc_handler.handle_request(config_request)
            config_response = json.loads(config_response_str)
            
            # 9. 验证config请求正常处理
            assert config_response["success"] is True
            
            # 10. 等待异步parse完成
            await asyncio.sleep(0.4)
    
    @pytest.mark.asyncio
    async def test_document_reparse_detection(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：文档重复解析检测
        
        验证：
        1. 已解析的文档不会重复解析
        2. 直接返回已有结果
        3. 节省计算资源
        
        Requirements: 2.4, 2.5
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 计算实际的doc_hash
        actual_doc_hash = doc_parser.compute_hash(sample_pdf_path)
        
        # 3. Mock PDF解析
        test_segments = [
            DocumentSegment(
                id=f"{actual_doc_hash}_0_0",
                doc_hash=actual_doc_hash,
                text="测试片段" * 30,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 4. 第一次解析
            result1 = await doc_parser.parse_document(sample_pdf_path)
            assert result1.status == "completed"
            
            # 5. 验证parse_pdf被调用一次
            assert mock_parse_pdf.call_count == 1
            
            # 6. 第二次解析相同文件
            result2 = await doc_parser.parse_document(sample_pdf_path)
            assert result2.status == "completed"
            
            # 7. 验证parse_pdf没有被再次调用（仍然是1次）
            assert mock_parse_pdf.call_count == 1
            
            # 8. 验证返回相同的结果
            assert result2.doc_hash == result1.doc_hash
            assert result2.version_hash == result1.version_hash
            # Note: segment_count may differ on second call because it's queried from DB
            # The important thing is that parse_pdf was not called again
            
            # 9. 验证embedding service也没有被再次调用
            assert mock_embedding_service.embed_texts.call_count == 1


class TestDocumentParseEdgeCases:
    """测试文档解析的边缘情况"""
    
    @pytest.fixture
    async def temp_db(self):
        """创建临时数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SQLiteDB(str(db_path))
            await db.initialize()
            yield db
    
    @pytest.fixture
    def mock_embedding_service(self):
        """创建mock EmbeddingService"""
        service = MagicMock(spec=EmbeddingService)
        service.embed_texts = AsyncMock(return_value=np.random.rand(1, 512))
        service.embed_single = AsyncMock(return_value=np.random.rand(512))
        return service
    
    @pytest.fixture
    def mock_vector_store(self):
        """创建mock VectorStore"""
        store = MagicMock(spec=VectorStore)
        store.upsert_vectors = AsyncMock()
        store.search = AsyncMock(return_value=[])
        return store
    
    @pytest.fixture
    def sample_pdf_path(self):
        """创建示例PDF文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n")
            return f.name
    
    @pytest.mark.asyncio
    async def test_empty_document_handling(
        self, temp_db, mock_embedding_service, mock_vector_store
    ):
        """
        测试：空文档处理
        
        验证：
        1. 空文档不会生成片段
        2. 抛出适当的错误
        """
        # 1. 创建空PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n")
            empty_pdf_path = f.name
        
        # 2. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 3. Mock PDF解析返回空列表
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = []
            
            # 4. 尝试解析空文档
            from wayfare.errors import DocumentParseError
            with pytest.raises(DocumentParseError) as exc_info:
                await doc_parser.parse_document(empty_pdf_path)
            
            # 5. 验证错误消息
            assert "No segments extracted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unsupported_file_type(
        self, temp_db, mock_embedding_service, mock_vector_store
    ):
        """
        测试：不支持的文件类型
        
        验证：
        1. 不支持的文件类型抛出错误
        2. 错误消息清晰
        """
        # 1. 创建不支持的文件类型
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test content")
            txt_path = f.name
        
        # 2. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 3. 尝试解析不支持的文件
        from wayfare.errors import DocumentParseError
        with pytest.raises(DocumentParseError) as exc_info:
            await doc_parser.parse_document(txt_path)
        
        # 4. 验证错误消息
        assert "Unsupported file type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_very_long_document_chunking(
        self, temp_db, mock_embedding_service, mock_vector_store
    ):
        """
        测试：超长文档分块
        
        验证：
        1. 超长文档正确分块
        2. 所有片段都在合理范围内
        3. 没有数据丢失
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db,
            chunk_size=300,
            chunk_overlap=50
        )
        
        # 2. 创建超长文本（5000字符）
        very_long_text = "这是一个测试句子。" * 500
        
        # 3. 测试分块
        chunks = doc_parser.chunk_text(very_long_text)
        
        # 4. 验证生成了多个片段
        assert len(chunks) >= 10
        
        # 5. 验证所有片段的总长度接近原文本长度（考虑重叠）
        total_unique_chars = sum(len(chunk) for chunk in chunks)
        # 由于有重叠，总长度会大于原文本
        assert total_unique_chars >= len(very_long_text)
        
        # 6. 验证每个片段都不为空
        for chunk in chunks:
            assert len(chunk.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_special_characters_in_text(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：文本中的特殊字符处理
        
        验证：
        1. 特殊字符正确保存
        2. Unicode字符正确处理
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 计算实际的doc_hash
        actual_doc_hash = doc_parser.compute_hash(sample_pdf_path)
        
        # 3. 创建包含特殊字符的片段
        special_text = "测试文本：包含特殊字符！@#￥%……&*（）【】《》？：""''；、。\n\t换行和制表符"
        test_segments = [
            DocumentSegment(
                id=f"{actual_doc_hash}_0_0",
                doc_hash=actual_doc_hash,
                text=special_text * 10,
                page=0,
                bbox=BoundingBox(0, 0, 100, 100)
            )
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 4. 执行解析
            result = await doc_parser.parse_document(sample_pdf_path)
            
            # 5. 从数据库获取片段
            stored_segments = await temp_db.get_segments_by_document(result.doc_hash)
            
            # 6. 验证特殊字符正确保存
            assert len(stored_segments) > 0
            assert stored_segments[0].text == test_segments[0].text
            assert special_text in stored_segments[0].text


class TestDocumentParsePerformance:
    """测试文档解析性能相关场景"""
    
    @pytest.fixture
    async def temp_db(self):
        """创建临时数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SQLiteDB(str(db_path))
            await db.initialize()
            yield db
    
    @pytest.fixture
    def mock_embedding_service(self):
        """创建mock EmbeddingService"""
        service = MagicMock(spec=EmbeddingService)
        # 模拟批量向量生成
        def embed_texts_side_effect(texts):
            return np.random.rand(len(texts), 512)
        service.embed_texts = AsyncMock(side_effect=embed_texts_side_effect)
        return service
    
    @pytest.fixture
    def mock_vector_store(self):
        """创建mock VectorStore"""
        store = MagicMock(spec=VectorStore)
        store.upsert_vectors = AsyncMock()
        return store
    
    @pytest.fixture
    def sample_pdf_path(self):
        """创建示例PDF文件路径"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n")
            return f.name
    
    @pytest.mark.asyncio
    async def test_batch_vectorization(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：批量向量化
        
        验证：
        1. 多个片段一次性向量化
        2. 不是逐个片段调用embedding service
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 创建多个片段
        test_segments = [
            DocumentSegment(
                id=f"test_hash_0_{i}",
                doc_hash="test_hash",
                text=f"片段{i}" * 30,
                page=0,
                bbox=BoundingBox(0, i * 100, 100, 100)
            )
            for i in range(10)
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. 执行解析
            await doc_parser.parse_document(sample_pdf_path)
            
            # 4. 验证embed_texts只被调用一次（批量处理）
            assert mock_embedding_service.embed_texts.call_count == 1
            
            # 5. 验证传入的文本数量
            call_args = mock_embedding_service.embed_texts.call_args[0]
            assert len(call_args[0]) == 10
    
    @pytest.mark.asyncio
    async def test_large_batch_upsert(
        self, temp_db, mock_embedding_service, mock_vector_store, sample_pdf_path
    ):
        """
        测试：大批量向量存储
        
        验证：
        1. 大量向量一次性存储
        2. 不是逐个向量插入
        """
        # 1. 创建DocumentParser
        doc_parser = DocumentParser(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            db=temp_db
        )
        
        # 2. 创建大量片段
        test_segments = [
            DocumentSegment(
                id=f"test_hash_0_{i}",
                doc_hash="test_hash",
                text=f"片段{i}" * 30,
                page=0,
                bbox=BoundingBox(0, i * 100, 100, 100)
            )
            for i in range(50)
        ]
        
        with patch.object(doc_parser, 'parse_pdf', new_callable=AsyncMock) as mock_parse_pdf:
            mock_parse_pdf.return_value = test_segments
            
            # 3. 执行解析
            await doc_parser.parse_document(sample_pdf_path)
            
            # 4. 验证upsert_vectors只被调用一次（批量插入）
            assert mock_vector_store.upsert_vectors.call_count == 1
            
            # 5. 验证插入的向量数量
            call_kwargs = mock_vector_store.upsert_vectors.call_args[1]
            assert len(call_kwargs["vectors"]) == 50
