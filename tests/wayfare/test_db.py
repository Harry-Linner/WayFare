"""SQLite数据库层测试"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

from wayfare.db import (
    SQLiteDB,
    BoundingBox,
    DocumentSegment,
    Annotation,
    BehaviorEvent
)


@pytest.fixture
async def db():
    """创建临时数据库用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        database = SQLiteDB(db_path)
        await database.initialize()
        yield database


@pytest.mark.asyncio
class TestDocumentsCRUD:
    """测试documents表的CRUD操作"""
    
    async def test_save_and_get_document(self, db):
        """测试保存和获取文档"""
        doc = {
            "hash": "test_hash_123",
            "path": "/path/to/doc.pdf",
            "status": "pending",
            "version_hash": "version_123"
        }
        
        await db.save_document(doc)
        retrieved = await db.get_document("test_hash_123")
        
        assert retrieved is not None
        assert retrieved["hash"] == "test_hash_123"
        assert retrieved["path"] == "/path/to/doc.pdf"
        assert retrieved["status"] == "pending"
        assert retrieved["version_hash"] == "version_123"
    
    async def test_update_document_status(self, db):
        """测试更新文档状态"""
        doc = {
            "hash": "test_hash_456",
            "path": "/path/to/doc2.pdf",
            "status": "pending",
            "version_hash": "version_456"
        }
        
        await db.save_document(doc)
        await db.update_document_status("test_hash_456", "completed")
        
        retrieved = await db.get_document("test_hash_456")
        assert retrieved["status"] == "completed"
    
    async def test_delete_document(self, db):
        """测试删除文档"""
        doc = {
            "hash": "test_hash_789",
            "path": "/path/to/doc3.pdf",
            "status": "completed",
            "version_hash": "version_789"
        }
        
        await db.save_document(doc)
        await db.delete_document("test_hash_789")
        
        retrieved = await db.get_document("test_hash_789")
        assert retrieved is None
    
    async def test_get_nonexistent_document(self, db):
        """测试获取不存在的文档"""
        retrieved = await db.get_document("nonexistent_hash")
        assert retrieved is None


@pytest.mark.asyncio
class TestSegmentsCRUD:
    """测试segments表的CRUD操作"""
    
    async def test_save_and_get_segments(self, db):
        """测试保存和获取片段"""
        # 先创建文档
        doc = {
            "hash": "doc_hash_1",
            "path": "/path/to/doc.pdf",
            "status": "processing",
            "version_hash": "version_1"
        }
        await db.save_document(doc)
        
        # 创建片段
        segments = [
            DocumentSegment(
                id="seg_1",
                doc_hash="doc_hash_1",
                text="This is segment 1",
                page=0,
                bbox=BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
            ),
            DocumentSegment(
                id="seg_2",
                doc_hash="doc_hash_1",
                text="This is segment 2",
                page=0,
                bbox=BoundingBox(x=10.0, y=80.0, width=100.0, height=50.0)
            )
        ]
        
        await db.save_segments(segments)
        
        # 获取单个片段
        seg = await db.get_segment("seg_1")
        assert seg is not None
        assert seg.id == "seg_1"
        assert seg.text == "This is segment 1"
        assert seg.bbox.x == 10.0
        
        # 获取文档的所有片段
        all_segs = await db.get_segments_by_document("doc_hash_1")
        assert len(all_segs) == 2
    
    async def test_count_segments(self, db):
        """测试统计片段数量"""
        doc = {
            "hash": "doc_hash_2",
            "path": "/path/to/doc2.pdf",
            "status": "processing",
            "version_hash": "version_2"
        }
        await db.save_document(doc)
        
        segments = [
            DocumentSegment(
                id=f"seg_{i}",
                doc_hash="doc_hash_2",
                text=f"Segment {i}",
                page=0,
                bbox=BoundingBox(x=0.0, y=float(i*50), width=100.0, height=50.0)
            )
            for i in range(5)
        ]
        
        await db.save_segments(segments)
        count = await db.count_segments("doc_hash_2")
        assert count == 5
    
    async def test_delete_segments(self, db):
        """测试删除片段"""
        doc = {
            "hash": "doc_hash_3",
            "path": "/path/to/doc3.pdf",
            "status": "processing",
            "version_hash": "version_3"
        }
        await db.save_document(doc)
        
        segments = [
            DocumentSegment(
                id="seg_del_1",
                doc_hash="doc_hash_3",
                text="To be deleted",
                page=0,
                bbox=BoundingBox(x=0.0, y=0.0, width=100.0, height=50.0)
            )
        ]
        
        await db.save_segments(segments)
        await db.delete_segments("doc_hash_3")
        
        count = await db.count_segments("doc_hash_3")
        assert count == 0


@pytest.mark.asyncio
class TestAnnotationsCRUD:
    """测试annotations表的CRUD操作"""
    
    async def test_save_and_get_annotation(self, db):
        """测试保存和获取批注"""
        doc = {
            "hash": "doc_hash_ann_1",
            "path": "/path/to/doc.pdf",
            "status": "completed",
            "version_hash": "version_ann_1"
        }
        await db.save_document(doc)
        
        annotation = Annotation(
            id="ann_1",
            doc_hash="doc_hash_ann_1",
            version_hash="version_ann_1",
            type="explanation",
            content="This is an explanation",
            bbox=BoundingBox(x=50.0, y=100.0, width=200.0, height=80.0),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        await db.save_annotation(annotation)
        
        retrieved = await db.get_annotation("ann_1")
        assert retrieved is not None
        assert retrieved.id == "ann_1"
        assert retrieved.type == "explanation"
        assert retrieved.content == "This is an explanation"
    
    async def test_get_annotations_by_document(self, db):
        """测试获取文档的所有批注"""
        doc = {
            "hash": "doc_hash_ann_2",
            "path": "/path/to/doc2.pdf",
            "status": "completed",
            "version_hash": "version_ann_2"
        }
        await db.save_document(doc)
        
        annotations = [
            Annotation(
                id=f"ann_{i}",
                doc_hash="doc_hash_ann_2",
                version_hash="version_ann_2",
                type="explanation",
                content=f"Annotation {i}",
                bbox=BoundingBox(x=0.0, y=float(i*100), width=200.0, height=80.0),
                created_at=datetime.now(timezone.utc).isoformat()
            )
            for i in range(3)
        ]
        
        for ann in annotations:
            await db.save_annotation(ann)
        
        retrieved = await db.get_annotations_by_document("doc_hash_ann_2")
        assert len(retrieved) == 3
    
    async def test_filter_annotations_by_version(self, db):
        """测试按版本过滤批注"""
        doc = {
            "hash": "doc_hash_ann_3",
            "path": "/path/to/doc3.pdf",
            "status": "completed",
            "version_hash": "version_ann_3"
        }
        await db.save_document(doc)
        
        # 创建不同版本的批注
        ann1 = Annotation(
            id="ann_v1",
            doc_hash="doc_hash_ann_3",
            version_hash="version_ann_3",
            type="explanation",
            content="Version 1",
            bbox=BoundingBox(x=0.0, y=0.0, width=200.0, height=80.0),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        ann2 = Annotation(
            id="ann_v2",
            doc_hash="doc_hash_ann_3",
            version_hash="version_ann_3_updated",
            type="explanation",
            content="Version 2",
            bbox=BoundingBox(x=0.0, y=0.0, width=200.0, height=80.0),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        await db.save_annotation(ann1)
        await db.save_annotation(ann2)
        
        # 只获取特定版本的批注
        v1_anns = await db.get_annotations_by_document(
            "doc_hash_ann_3", 
            version_hash="version_ann_3"
        )
        assert len(v1_anns) == 1
        assert v1_anns[0].content == "Version 1"
    
    async def test_delete_annotation(self, db):
        """测试删除批注"""
        doc = {
            "hash": "doc_hash_ann_4",
            "path": "/path/to/doc4.pdf",
            "status": "completed",
            "version_hash": "version_ann_4"
        }
        await db.save_document(doc)
        
        annotation = Annotation(
            id="ann_del",
            doc_hash="doc_hash_ann_4",
            version_hash="version_ann_4",
            type="explanation",
            content="To be deleted",
            bbox=BoundingBox(x=0.0, y=0.0, width=200.0, height=80.0),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        await db.save_annotation(annotation)
        await db.delete_annotation("ann_del")
        
        retrieved = await db.get_annotation("ann_del")
        assert retrieved is None


@pytest.mark.asyncio
class TestBehaviorsCRUD:
    """测试behaviors表的CRUD操作"""
    
    async def test_save_and_get_behaviors(self, db):
        """测试保存和获取行为数据"""
        doc = {
            "hash": "doc_hash_beh_1",
            "path": "/path/to/doc.pdf",
            "status": "completed",
            "version_hash": "version_beh_1"
        }
        await db.save_document(doc)
        
        behavior = BehaviorEvent(
            id="beh_1",
            doc_hash="doc_hash_beh_1",
            page=0,
            event_type="page_view",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"duration": 120}
        )
        
        await db.save_behavior(behavior)
        
        behaviors = await db.get_behaviors("doc_hash_beh_1")
        assert len(behaviors) == 1
        assert behaviors[0].event_type == "page_view"
        assert behaviors[0].metadata["duration"] == 120
    
    async def test_filter_behaviors_by_page(self, db):
        """测试按页码过滤行为数据"""
        doc = {
            "hash": "doc_hash_beh_2",
            "path": "/path/to/doc2.pdf",
            "status": "completed",
            "version_hash": "version_beh_2"
        }
        await db.save_document(doc)
        
        # 创建不同页面的行为
        behaviors = [
            BehaviorEvent(
                id=f"beh_{i}",
                doc_hash="doc_hash_beh_2",
                page=i % 3,  # 页面0, 1, 2
                event_type="page_view",
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={}
            )
            for i in range(6)
        ]
        
        for beh in behaviors:
            await db.save_behavior(beh)
        
        # 只获取页面1的行为
        page1_behaviors = await db.get_behaviors("doc_hash_beh_2", page=1)
        assert len(page1_behaviors) == 2
        assert all(b.page == 1 for b in page1_behaviors)
    
    async def test_delete_behaviors(self, db):
        """测试删除行为数据"""
        doc = {
            "hash": "doc_hash_beh_3",
            "path": "/path/to/doc3.pdf",
            "status": "completed",
            "version_hash": "version_beh_3"
        }
        await db.save_document(doc)
        
        behavior = BehaviorEvent(
            id="beh_del",
            doc_hash="doc_hash_beh_3",
            page=0,
            event_type="page_view",
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={}
        )
        
        await db.save_behavior(behavior)
        await db.delete_behaviors("doc_hash_beh_3")
        
        behaviors = await db.get_behaviors("doc_hash_beh_3")
        assert len(behaviors) == 0


@pytest.mark.asyncio
class TestDatabaseInitialization:
    """测试数据库初始化"""
    
    async def test_initialize_creates_tables(self):
        """测试初始化创建所有表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "init_test.db")
            db = SQLiteDB(db_path)
            await db.initialize()
            
            # 验证数据库文件已创建
            assert Path(db_path).exists()
            
            # 验证可以执行基本操作
            doc = {
                "hash": "init_test",
                "path": "/test.pdf",
                "status": "pending",
                "version_hash": "v1"
            }
            await db.save_document(doc)
            retrieved = await db.get_document("init_test")
            assert retrieved is not None
    
    async def test_initialize_is_idempotent(self):
        """测试重复初始化不会出错"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "idempotent_test.db")
            db = SQLiteDB(db_path)
            
            # 多次初始化
            await db.initialize()
            await db.initialize()
            await db.initialize()
            
            # 验证数据库仍然正常工作
            doc = {
                "hash": "idempotent_test",
                "path": "/test.pdf",
                "status": "pending",
                "version_hash": "v1"
            }
            await db.save_document(doc)
            retrieved = await db.get_document("idempotent_test")
            assert retrieved is not None


@pytest.mark.asyncio
class TestCascadeDelete:
    """测试级联删除"""
    
    async def test_delete_document_cascades_to_segments(self, db):
        """测试删除文档会级联删除片段"""
        doc = {
            "hash": "cascade_doc",
            "path": "/test.pdf",
            "status": "completed",
            "version_hash": "v1"
        }
        await db.save_document(doc)
        
        segments = [
            DocumentSegment(
                id=f"cascade_seg_{i}",
                doc_hash="cascade_doc",
                text=f"Segment {i}",
                page=0,
                bbox=BoundingBox(x=0.0, y=0.0, width=100.0, height=50.0)
            )
            for i in range(3)
        ]
        await db.save_segments(segments)
        
        # 删除文档
        await db.delete_document("cascade_doc")
        
        # 验证片段也被删除
        count = await db.count_segments("cascade_doc")
        assert count == 0
