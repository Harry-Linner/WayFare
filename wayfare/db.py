"""SQLite数据库层实现

提供文档、片段、批注和行为数据的CRUD操作。
"""

import aiosqlite
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """边界框数据类"""
    x: float
    y: float
    width: float
    height: float


@dataclass
class DocumentSegment:
    """文档片段数据类"""
    id: str
    doc_hash: str
    text: str
    page: int
    bbox: BoundingBox


@dataclass
class Annotation:
    """批注数据类"""
    id: str
    doc_hash: str
    version_hash: str
    type: str
    content: str
    bbox: BoundingBox
    created_at: str


@dataclass
class BehaviorEvent:
    """行为事件数据类"""
    id: str
    doc_hash: str
    page: int
    event_type: str
    timestamp: str
    metadata: Dict[str, Any]


class SQLiteDB:
    """SQLite数据库管理类
    
    负责数据库连接管理和所有表的CRUD操作。
    """
    
    def __init__(self, db_path: str = ".wayfare/wayfare.db"):
        """初始化数据库
        
        Args:
            db_path: 数据库文件路径，默认为.wayfare/wayfare.db
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """初始化数据库，创建所有表和索引"""
        async with aiosqlite.connect(self.db_path) as db:
            # 启用外键约束
            await db.execute("PRAGMA foreign_keys = ON")
            
            # 创建documents表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    hash TEXT PRIMARY KEY,
                    path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    version_hash TEXT NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_status 
                ON documents(status)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_path 
                ON documents(path)
            """)
            
            # 创建segments表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS segments (
                    id TEXT PRIMARY KEY,
                    doc_hash TEXT NOT NULL,
                    text TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    bbox_x REAL NOT NULL,
                    bbox_y REAL NOT NULL,
                    bbox_width REAL NOT NULL,
                    bbox_height REAL NOT NULL,
                    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_segments_doc_hash 
                ON segments(doc_hash)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_segments_page 
                ON segments(doc_hash, page)
            """)
            
            # 创建annotations表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id TEXT PRIMARY KEY,
                    doc_hash TEXT NOT NULL,
                    version_hash TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    bbox_x REAL NOT NULL,
                    bbox_y REAL NOT NULL,
                    bbox_width REAL NOT NULL,
                    bbox_height REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_doc_hash 
                ON annotations(doc_hash)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_version 
                ON annotations(doc_hash, version_hash)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_annotations_type 
                ON annotations(type)
            """)
            
            # 创建behaviors表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS behaviors (
                    id TEXT PRIMARY KEY,
                    doc_hash TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_behaviors_doc_page 
                ON behaviors(doc_hash, page)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_behaviors_timestamp 
                ON behaviors(timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_behaviors_type 
                ON behaviors(event_type)
            """)
            
            await db.commit()
    
    # Documents表CRUD操作
    
    async def save_document(self, doc: Dict[str, Any]):
        """保存或更新文档元数据
        
        Args:
            doc: 文档数据字典，包含hash、path、status、version_hash等字段
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("""
                INSERT OR REPLACE INTO documents 
                (hash, path, status, updated_at, version_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (
                doc["hash"],
                doc["path"],
                doc["status"],
                doc.get("updated_at", datetime.now(timezone.utc).isoformat()),
                doc["version_hash"]
            ))
            await db.commit()
    
    async def get_document(self, doc_hash: str) -> Optional[Dict[str, Any]]:
        """获取文档元数据
        
        Args:
            doc_hash: 文档hash
            
        Returns:
            文档数据字典，如果不存在返回None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM documents WHERE hash = ?",
                (doc_hash,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def update_document_status(self, doc_hash: str, status: str):
        """更新文档状态
        
        Args:
            doc_hash: 文档hash
            status: 新状态 (pending/processing/completed/failed)
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute(
                "UPDATE documents SET status = ?, updated_at = ? WHERE hash = ?",
                (status, datetime.now(timezone.utc).isoformat(), doc_hash)
            )
            await db.commit()
    
    async def delete_document(self, doc_hash: str):
        """删除文档及其关联数据
        
        Args:
            doc_hash: 文档hash
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("DELETE FROM documents WHERE hash = ?", (doc_hash,))
            await db.commit()
    
    # Segments表CRUD操作
    
    async def save_segments(self, segments: List[DocumentSegment]):
        """批量保存片段
        
        Args:
            segments: 片段列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            for seg in segments:
                await db.execute("""
                    INSERT OR REPLACE INTO segments
                    (id, doc_hash, text, page, bbox_x, bbox_y, bbox_width, bbox_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    seg.id,
                    seg.doc_hash,
                    seg.text,
                    seg.page,
                    seg.bbox.x,
                    seg.bbox.y,
                    seg.bbox.width,
                    seg.bbox.height
                ))
            await db.commit()
    
    async def get_segment(self, segment_id: str) -> Optional[DocumentSegment]:
        """获取单个片段
        
        Args:
            segment_id: 片段ID
            
        Returns:
            片段对象，如果不存在返回None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM segments WHERE id = ?",
                (segment_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return DocumentSegment(
                        id=row["id"],
                        doc_hash=row["doc_hash"],
                        text=row["text"],
                        page=row["page"],
                        bbox=BoundingBox(
                            x=row["bbox_x"],
                            y=row["bbox_y"],
                            width=row["bbox_width"],
                            height=row["bbox_height"]
                        )
                    )
                return None
    
    async def get_segments_by_document(self, doc_hash: str) -> List[DocumentSegment]:
        """获取文档的所有片段
        
        Args:
            doc_hash: 文档hash
            
        Returns:
            片段列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM segments WHERE doc_hash = ? ORDER BY page, id",
                (doc_hash,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    DocumentSegment(
                        id=row["id"],
                        doc_hash=row["doc_hash"],
                        text=row["text"],
                        page=row["page"],
                        bbox=BoundingBox(
                            x=row["bbox_x"],
                            y=row["bbox_y"],
                            width=row["bbox_width"],
                            height=row["bbox_height"]
                        )
                    )
                    for row in rows
                ]
    
    async def count_segments(self, doc_hash: str) -> int:
        """统计文档片段数
        
        Args:
            doc_hash: 文档hash
            
        Returns:
            片段数量
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM segments WHERE doc_hash = ?",
                (doc_hash,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    async def delete_segments(self, doc_hash: str):
        """删除文档的所有片段
        
        Args:
            doc_hash: 文档hash
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM segments WHERE doc_hash = ?", (doc_hash,))
            await db.commit()
    
    # Annotations表CRUD操作
    
    async def save_annotation(self, annotation: Annotation):
        """保存批注
        
        Args:
            annotation: 批注对象
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO annotations
                (id, doc_hash, version_hash, type, content, 
                 bbox_x, bbox_y, bbox_width, bbox_height, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                annotation.id,
                annotation.doc_hash,
                annotation.version_hash,
                annotation.type,
                annotation.content,
                annotation.bbox.x,
                annotation.bbox.y,
                annotation.bbox.width,
                annotation.bbox.height,
                annotation.created_at
            ))
            await db.commit()
    
    async def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        """获取单个批注
        
        Args:
            annotation_id: 批注ID
            
        Returns:
            批注对象，如果不存在返回None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM annotations WHERE id = ?",
                (annotation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Annotation(
                        id=row["id"],
                        doc_hash=row["doc_hash"],
                        version_hash=row["version_hash"],
                        type=row["type"],
                        content=row["content"],
                        bbox=BoundingBox(
                            x=row["bbox_x"],
                            y=row["bbox_y"],
                            width=row["bbox_width"],
                            height=row["bbox_height"]
                        ),
                        created_at=row["created_at"]
                    )
                return None
    
    async def get_annotations_by_document(
        self, 
        doc_hash: str,
        version_hash: Optional[str] = None
    ) -> List[Annotation]:
        """获取文档的所有批注
        
        Args:
            doc_hash: 文档hash
            version_hash: 可选的版本hash，用于过滤特定版本的批注
            
        Returns:
            批注列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if version_hash:
                query = """
                    SELECT * FROM annotations 
                    WHERE doc_hash = ? AND version_hash = ?
                    ORDER BY created_at DESC
                """
                params = (doc_hash, version_hash)
            else:
                query = """
                    SELECT * FROM annotations 
                    WHERE doc_hash = ?
                    ORDER BY created_at DESC
                """
                params = (doc_hash,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    Annotation(
                        id=row["id"],
                        doc_hash=row["doc_hash"],
                        version_hash=row["version_hash"],
                        type=row["type"],
                        content=row["content"],
                        bbox=BoundingBox(
                            x=row["bbox_x"],
                            y=row["bbox_y"],
                            width=row["bbox_width"],
                            height=row["bbox_height"]
                        ),
                        created_at=row["created_at"]
                    )
                    for row in rows
                ]
    
    async def delete_annotation(self, annotation_id: str):
        """删除批注
        
        Args:
            annotation_id: 批注ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
            await db.commit()
    
    async def delete_annotations_by_document(self, doc_hash: str):
        """删除文档的所有批注
        
        Args:
            doc_hash: 文档hash
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM annotations WHERE doc_hash = ?", (doc_hash,))
            await db.commit()
    
    # Behaviors表CRUD操作
    
    async def save_behavior(self, behavior: BehaviorEvent):
        """保存行为数据
        
        Args:
            behavior: 行为事件对象
        """
        import json
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO behaviors
                (id, doc_hash, page, event_type, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                behavior.id,
                behavior.doc_hash,
                behavior.page,
                behavior.event_type,
                behavior.timestamp,
                json.dumps(behavior.metadata) if behavior.metadata else None
            ))
            await db.commit()
    
    async def get_behaviors(
        self, 
        doc_hash: str, 
        page: Optional[int] = None
    ) -> List[BehaviorEvent]:
        """获取行为数据
        
        Args:
            doc_hash: 文档hash
            page: 可选的页码过滤
            
        Returns:
            行为事件列表
        """
        import json
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if page is not None:
                query = """
                    SELECT * FROM behaviors 
                    WHERE doc_hash = ? AND page = ?
                    ORDER BY timestamp DESC
                """
                params = (doc_hash, page)
            else:
                query = """
                    SELECT * FROM behaviors 
                    WHERE doc_hash = ?
                    ORDER BY timestamp DESC
                """
                params = (doc_hash,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    BehaviorEvent(
                        id=row["id"],
                        doc_hash=row["doc_hash"],
                        page=row["page"],
                        event_type=row["event_type"],
                        timestamp=row["timestamp"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                    )
                    for row in rows
                ]
    
    async def delete_behaviors(self, doc_hash: str):
        """删除文档的所有行为数据
        
        Args:
            doc_hash: 文档hash
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM behaviors WHERE doc_hash = ?", (doc_hash,))
            await db.commit()
