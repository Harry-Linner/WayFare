"""
Document Parser模块

解析PDF和Markdown文档，提取结构化片段并生成向量。
支持文档hash计算、版本控制和异步处理。
"""

import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """文档解析结果"""
    doc_hash: str
    version_hash: str
    segment_count: int
    status: str


class DocumentParser:
    """
    文档解析器
    
    负责解析PDF和Markdown文档，生成结构化片段。
    
    Requirements:
    - 2.1: Parse PDF files and extract text, page numbers, and bounding box information
    - 2.4: Generate unique hash identifier for each document (using BLAKE3)
    - 2.5: Generate versionHash to detect content changes
    - 9.1: Parse PDF documents and generate structured DocumentSegment objects
    """
    
    def __init__(self, 
                 embedding_service,
                 vector_store,
                 db,
                 chunk_size: int = 300,
                 chunk_overlap: int = 50):
        """
        初始化文档解析器
        
        Args:
            embedding_service: Embedding服务实例
            vector_store: 向量存储实例
            db: SQLite数据库实例
            chunk_size: 分块大小，默认300字符
            chunk_overlap: 分块重叠大小，默认50字符
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.db = db
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def compute_hash(self, path: str) -> str:
        """
        计算文档hash（使用BLAKE3）
        
        Args:
            path: 文档路径
            
        Returns:
            BLAKE3 hash字符串
            
        Raises:
            FileNotFoundError: 如果文件不存在
            IOError: 如果文件读取失败
            
        Example:
            >>> parser = DocumentParser(...)
            >>> doc_hash = parser.compute_hash("document.pdf")
            >>> len(doc_hash)
            64
        """
        try:
            import blake3
        except ImportError as e:
            raise ImportError(
                "Missing required dependency. Please install: pip install blake3"
            ) from e
        
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        logger.debug(f"Computing BLAKE3 hash for {path}")
        
        hasher = blake3.blake3()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            
            doc_hash = hasher.hexdigest()
            logger.debug(f"Computed hash: {doc_hash}")
            return doc_hash
            
        except IOError as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise IOError(f"Failed to read file: {e}") from e
    
    def compute_version_hash(self, content: str) -> str:
        """
        计算内容版本hash
        
        Args:
            content: 文档内容文本
            
        Returns:
            BLAKE3 hash字符串
            
        Example:
            >>> parser = DocumentParser(...)
            >>> version_hash = parser.compute_version_hash("document content")
            >>> len(version_hash)
            64
        """
        try:
            import blake3
        except ImportError as e:
            raise ImportError(
                "Missing required dependency. Please install: pip install blake3"
            ) from e
        
        logger.debug(f"Computing version hash for content ({len(content)} chars)")
        
        version_hash = blake3.blake3(content.encode('utf-8')).hexdigest()
        logger.debug(f"Computed version hash: {version_hash}")
        return version_hash
    
    async def parse_document(self, path: str) -> ParseResult:
        """
        解析文档的主入口（完整流程）
        
        实现完整的文档解析流程：
        1. 计算文档hash和版本hash
        2. 检测文件类型并选择解析器
        3. 解析文档并分块
        4. 生成向量
        5. 存储到数据库和向量存储
        6. 管理文档状态（pending/processing/completed/failed）
        7. 错误处理和恢复机制
        
        Requirements:
        - 2.1: Parse PDF files and extract text, page numbers, and bounding box information
        - 2.2: Parse Markdown files and extract structured content
        - 2.3: Split documents into semantically coherent segments (200-500 characters each)
        - 2.4: Generate unique hash identifier for each document (using BLAKE3)
        - 2.5: Generate versionHash to detect content changes
        - 2.6: Store segment information to SQLite database when parsing completes
        
        Args:
            path: 文档路径
            
        Returns:
            解析结果对象，包含doc_hash、version_hash、segment_count和status
            
        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件类型不支持
            DocumentParseError: 如果解析失败
            
        Example:
            >>> parser = DocumentParser(...)
            >>> result = await parser.parse_document("document.pdf")
            >>> result.status
            'completed'
        """
        from wayfare.errors import DocumentParseError
        from wayfare.db import DocumentSegment
        from datetime import datetime, timezone
        
        logger.info(f"Starting document parsing: {path}")
        
        doc_hash = None
        
        try:
            # 1. 计算hash
            try:
                doc_hash = self.compute_hash(path)
                logger.debug(f"Computed document hash: {doc_hash}")
            except Exception as e:
                logger.error(f"Failed to compute hash for {path}: {e}")
                raise DocumentParseError(path, f"Failed to compute hash: {e}")
            
            # 2. 检查是否已解析
            existing = await self.db.get_document(doc_hash)
            if existing:
                status = existing.get("status")
                if status == "completed":
                    logger.info(f"Document already parsed: {doc_hash}")
                    segment_count = await self.db.count_segments(doc_hash)
                    return ParseResult(
                        doc_hash=doc_hash,
                        version_hash=existing["version_hash"],
                        segment_count=segment_count,
                        status="completed"
                    )
                elif status == "processing":
                    logger.warning(f"Document is already being processed: {doc_hash}")
                    # Allow retry for stuck processing state
                elif status == "failed":
                    logger.info(f"Retrying failed document: {doc_hash}")
                    # Continue with re-parsing
            
            # 3. 根据文件类型选择解析器
            suffix = Path(path).suffix.lower()
            try:
                if suffix == ".pdf":
                    segments = await self.parse_pdf(path, doc_hash)
                elif suffix in [".md", ".markdown"]:
                    segments = await self.parse_markdown(path, doc_hash)
                else:
                    raise ValueError(f"Unsupported file type: {suffix}")
                
                if not segments:
                    raise ValueError("No segments extracted from document")
                    
                logger.info(f"Extracted {len(segments)} segments from document")
                
            except Exception as e:
                logger.error(f"Failed to parse document {path}: {e}")
                # Set status to failed before raising
                if doc_hash:
                    try:
                        await self.db.save_document({
                            "hash": doc_hash,
                            "path": path,
                            "status": "failed",
                            "version_hash": "",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        })
                    except Exception as db_error:
                        logger.error(f"Failed to update document status to failed: {db_error}")
                raise DocumentParseError(path, str(e))
            
            # 4. 计算版本hash
            try:
                full_text = " ".join(s.text for s in segments)
                version_hash = self.compute_version_hash(full_text)
                logger.debug(f"Computed version hash: {version_hash}")
            except Exception as e:
                logger.error(f"Failed to compute version hash: {e}")
                await self._set_failed_status(doc_hash, path)
                raise DocumentParseError(path, f"Failed to compute version hash: {e}")
            
            # 5. 保存文档元数据（设置为processing状态）
            try:
                await self.db.save_document({
                    "hash": doc_hash,
                    "path": path,
                    "status": "processing",
                    "version_hash": version_hash,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                logger.debug(f"Saved document metadata with status=processing")
            except Exception as e:
                logger.error(f"Failed to save document metadata: {e}")
                raise DocumentParseError(path, f"Failed to save document metadata: {e}")
            
            # 6. 保存片段
            try:
                await self.db.save_segments(segments)
                logger.info(f"Saved {len(segments)} segments for document {doc_hash}")
            except Exception as e:
                logger.error(f"Failed to save segments: {e}")
                await self._set_failed_status(doc_hash, path)
                raise DocumentParseError(path, f"Failed to save segments: {e}")
            
            # 7. 生成向量并存储
            try:
                await self._vectorize_segments(segments)
                logger.info(f"Vectorized and stored {len(segments)} segments")
            except Exception as e:
                logger.error(f"Failed to vectorize segments: {e}")
                await self._set_failed_status(doc_hash, path)
                raise DocumentParseError(path, f"Failed to vectorize segments: {e}")
            
            # 8. 更新状态为completed
            try:
                await self.db.update_document_status(doc_hash, "completed")
                logger.info(f"Document parsing completed successfully: {doc_hash}")
            except Exception as e:
                logger.error(f"Failed to update document status to completed: {e}")
                # Document is actually complete, but status update failed
                # Log warning but don't fail the entire operation
                logger.warning(f"Document parsing succeeded but status update failed: {doc_hash}")
            
            return ParseResult(
                doc_hash=doc_hash,
                version_hash=version_hash,
                segment_count=len(segments),
                status="completed"
            )
            
        except DocumentParseError:
            # Re-raise DocumentParseError as-is
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error during document parsing: {e}", exc_info=True)
            if doc_hash:
                await self._set_failed_status(doc_hash, path)
            raise DocumentParseError(path, f"Unexpected error: {e}")
    
    async def _set_failed_status(self, doc_hash: str, path: str) -> None:
        """
        设置文档状态为failed（错误恢复辅助方法）
        
        Args:
            doc_hash: 文档hash
            path: 文档路径
        """
        from datetime import datetime, timezone
        
        try:
            await self.db.save_document({
                "hash": doc_hash,
                "path": path,
                "status": "failed",
                "version_hash": "",
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Set document status to failed: {doc_hash}")
        except Exception as e:
            logger.error(f"Failed to set document status to failed: {e}")
    
    async def parse_pdf(self, path: str, doc_hash: str) -> List:
        """
        解析PDF文档
        
        使用PyMuPDF提取文本、页码和边界框信息。
        
        Args:
            path: PDF文件路径
            doc_hash: 文档hash
            
        Returns:
            DocumentSegment列表
            
        Raises:
            ImportError: 如果PyMuPDF未安装
            RuntimeError: 如果PDF解析失败
            
        Example:
            >>> parser = DocumentParser(...)
            >>> segments = await parser.parse_pdf("doc.pdf", "hash123")
            >>> len(segments) > 0
            True
        """
        from wayfare.db import DocumentSegment, BoundingBox
        
        try:
            import fitz  # PyMuPDF
        except ImportError as e:
            raise ImportError(
                "Missing required dependency. Please install: pip install PyMuPDF"
            ) from e
        
        logger.info(f"Parsing PDF: {path}")
        
        segments = []
        
        try:
            doc = fitz.open(path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 提取文本块（包含bbox信息）
                blocks = page.get_text("dict")["blocks"]
                
                page_text = ""
                for block in blocks:
                    if block["type"] == 0:  # 文本块
                        for line in block["lines"]:
                            for span in line["spans"]:
                                page_text += span["text"] + " "
                
                # 分块
                chunks = self.chunk_text(page_text.strip())
                
                # 为每个chunk创建segment
                for i, chunk in enumerate(chunks):
                    # 简化：使用页面级别的bbox
                    bbox = BoundingBox(
                        x=0,
                        y=i * 100,  # 简化的y坐标
                        width=page.rect.width,
                        height=100
                    )
                    
                    segment = DocumentSegment(
                        id=f"{doc_hash}_{page_num}_{i}",
                        doc_hash=doc_hash,
                        text=chunk,
                        page=page_num,
                        bbox=bbox
                    )
                    segments.append(segment)
                
                logger.debug(f"Extracted {len(chunks)} chunks from page {page_num}")
            
            doc.close()
            logger.info(f"PDF parsing completed: {len(segments)} segments extracted")
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {path}: {e}")
            raise RuntimeError(f"PDF parsing failed: {e}") from e
        
        return segments
    
    async def parse_markdown(self, path: str, doc_hash: str) -> List:
        """
        解析Markdown文档
        
        使用markdown-it-py提取结构化内容。
        
        Args:
            path: Markdown文件路径
            doc_hash: 文档hash
            
        Returns:
            DocumentSegment列表
            
        Raises:
            ImportError: 如果markdown-it-py未安装
            RuntimeError: 如果Markdown解析失败
            
        Example:
            >>> parser = DocumentParser(...)
            >>> segments = await parser.parse_markdown("doc.md", "hash123")
            >>> len(segments) > 0
            True
        """
        from wayfare.db import DocumentSegment, BoundingBox
        
        try:
            from markdown_it import MarkdownIt
        except ImportError as e:
            raise ImportError(
                "Missing required dependency. Please install: pip install markdown-it-py"
            ) from e
        
        logger.info(f"Parsing Markdown: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read Markdown file {path}: {e}")
            raise RuntimeError(f"Failed to read file: {e}") from e
        
        md = MarkdownIt()
        tokens = md.parse(content)
        
        segments = []
        current_text = ""
        page = 0  # Markdown没有页码概念，使用虚拟页码
        
        for token in tokens:
            if token.type == "heading_open":
                # 遇到标题时，保存之前的文本
                if current_text.strip():
                    chunks = self.chunk_text(current_text.strip())
                    for i, chunk in enumerate(chunks):
                        segment = DocumentSegment(
                            id=f"{doc_hash}_{page}_{i}",
                            doc_hash=doc_hash,
                            text=chunk,
                            page=page,
                            bbox=BoundingBox(0, 0, 800, 100)
                        )
                        segments.append(segment)
                    page += 1
                    current_text = ""
            
            elif token.type == "inline":
                current_text += token.content + " "
        
        # 处理最后的文本
        if current_text.strip():
            chunks = self.chunk_text(current_text.strip())
            for i, chunk in enumerate(chunks):
                segment = DocumentSegment(
                    id=f"{doc_hash}_{page}_{i}",
                    doc_hash=doc_hash,
                    text=chunk,
                    page=page,
                    bbox=BoundingBox(0, 0, 800, 100)
                )
                segments.append(segment)
        
        logger.info(f"Markdown parsing completed: {len(segments)} segments extracted")
        
        return segments
    
    def chunk_text(self, text: str) -> List[str]:
        """
        将文本分割为语义连贯的片段
        
        使用滑动窗口策略，优先在句子边界分割。
        确保每个片段在200-500字符范围内（除了最后一个片段可能小于200）。
        
        Requirements:
        - 2.3: Split documents into semantically coherent segments (200-500 characters each)
        
        Args:
            text: 输入文本
            
        Returns:
            文本片段列表，每个片段200-500字符（最后一个片段可能小于200）
            
        Example:
            >>> parser = DocumentParser(...)
            >>> chunks = parser.chunk_text("这是第一句。这是第二句。" * 100)
            >>> all(200 <= len(c) <= 500 for c in chunks[:-1])  # All but last
            True
        """
        MIN_CHUNK_SIZE = 200
        MAX_CHUNK_SIZE = 500
        
        chunks = []
        text = text.strip()
        
        if not text:
            return []
        
        # If text is shorter than min size, return as-is
        if len(text) <= MIN_CHUNK_SIZE:
            return [text]
        
        # If text is between min and max, return as-is
        if len(text) <= MAX_CHUNK_SIZE:
            return [text]
        
        start = 0
        while start < len(text):
            remaining = len(text) - start
            
            # If remaining text is small enough, take it all
            if remaining <= MAX_CHUNK_SIZE:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # Try to find a good split point between MIN and MAX
            # Start looking from the target chunk_size (300)
            end = start + self.chunk_size
            
            # Look for sentence boundary between MIN and MAX
            best_punct_pos = -1
            search_start = start + MIN_CHUNK_SIZE
            search_end = min(start + MAX_CHUNK_SIZE, len(text))
            
            for punct in ["。", "！", "？", ".", "!", "?"]:
                # Search backwards from search_end to find the last punctuation
                punct_pos = text.rfind(punct, search_start, search_end)
                if punct_pos != -1 and punct_pos > best_punct_pos:
                    best_punct_pos = punct_pos
            
            if best_punct_pos != -1:
                end = best_punct_pos + 1
            else:
                # No sentence boundary found, use MAX_CHUNK_SIZE
                end = search_end
            
            # Extract chunk
            chunk = text[start:end].strip()
            
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            # Ensure we make progress and don't get stuck
            next_start = end - self.chunk_overlap
            if next_start <= start:
                next_start = end
            
            start = next_start
        
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks
    
    async def _vectorize_segments(self, segments: List) -> None:
        """
        为片段生成向量并存储到Qdrant
        
        Args:
            segments: DocumentSegment列表
            
        Raises:
            RuntimeError: 如果向量化或存储失败
        """
        if not segments:
            logger.warning("No segments to vectorize")
            return
        
        logger.info(f"Vectorizing {len(segments)} segments")
        
        try:
            # 批量生成向量
            texts = [s.text for s in segments]
            vectors = await self.embedding_service.embed_texts(texts)
            
            # 存储到Qdrant
            await self.vector_store.upsert_vectors(
                collection="documents",
                vectors=[
                    {
                        "id": seg.id,
                        "vector": vec.tolist(),
                        "payload": {
                            "doc_hash": seg.doc_hash,
                            "page": seg.page,
                            "text": seg.text
                        }
                    }
                    for seg, vec in zip(segments, vectors)
                ]
            )
            
            logger.info(f"Successfully vectorized and stored {len(segments)} segments")
            
        except Exception as e:
            logger.error(f"Failed to vectorize segments: {e}")
            raise RuntimeError(f"Vectorization failed: {e}") from e
