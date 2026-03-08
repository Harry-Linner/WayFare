"""SQLite数据库层使用示例

演示如何使用wayfare.db模块进行数据库操作。
"""

import asyncio
from datetime import datetime, timezone
from wayfare.db import (
    SQLiteDB,
    BoundingBox,
    DocumentSegment,
    Annotation,
    BehaviorEvent
)


async def main():
    """演示数据库基本操作"""
    
    # 1. 初始化数据库
    print("1. 初始化数据库...")
    db = SQLiteDB(".wayfare/example.db")
    await db.initialize()
    print("   ✓ 数据库初始化完成\n")
    
    # 2. 保存文档
    print("2. 保存文档...")
    doc = {
        "hash": "doc_example_123",
        "path": "/path/to/example.pdf",
        "status": "processing",
        "version_hash": "version_abc"
    }
    await db.save_document(doc)
    print(f"   ✓ 文档已保存: {doc['hash']}\n")
    
    # 3. 保存文档片段
    print("3. 保存文档片段...")
    segments = [
        DocumentSegment(
            id="seg_1",
            doc_hash="doc_example_123",
            text="这是第一个文档片段，包含一些示例文本。",
            page=0,
            bbox=BoundingBox(x=10.0, y=20.0, width=200.0, height=50.0)
        ),
        DocumentSegment(
            id="seg_2",
            doc_hash="doc_example_123",
            text="这是第二个文档片段，用于演示分段存储。",
            page=0,
            bbox=BoundingBox(x=10.0, y=80.0, width=200.0, height=50.0)
        )
    ]
    await db.save_segments(segments)
    count = await db.count_segments("doc_example_123")
    print(f"   ✓ 已保存 {count} 个片段\n")
    
    # 4. 更新文档状态
    print("4. 更新文档状态...")
    await db.update_document_status("doc_example_123", "completed")
    updated_doc = await db.get_document("doc_example_123")
    print(f"   ✓ 文档状态已更新为: {updated_doc['status']}\n")
    
    # 5. 保存批注
    print("5. 保存批注...")
    annotation = Annotation(
        id="ann_1",
        doc_hash="doc_example_123",
        version_hash="version_abc",
        type="explanation",
        content="这是一个费曼式解释批注，用简单的语言解释复杂概念。",
        bbox=BoundingBox(x=50.0, y=100.0, width=300.0, height=80.0),
        created_at=datetime.now(timezone.utc).isoformat()
    )
    await db.save_annotation(annotation)
    print(f"   ✓ 批注已保存: {annotation.id}\n")
    
    # 6. 保存用户行为
    print("6. 保存用户行为...")
    behavior = BehaviorEvent(
        id="beh_1",
        doc_hash="doc_example_123",
        page=0,
        event_type="page_view",
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata={"duration": 120, "scroll_depth": 0.8}
    )
    await db.save_behavior(behavior)
    print(f"   ✓ 行为数据已保存: {behavior.event_type}\n")
    
    # 7. 查询数据
    print("7. 查询数据...")
    
    # 获取文档的所有片段
    all_segments = await db.get_segments_by_document("doc_example_123")
    print(f"   - 文档片段数: {len(all_segments)}")
    
    # 获取文档的所有批注
    annotations = await db.get_annotations_by_document("doc_example_123")
    print(f"   - 批注数: {len(annotations)}")
    
    # 获取文档的行为数据
    behaviors = await db.get_behaviors("doc_example_123")
    print(f"   - 行为记录数: {len(behaviors)}\n")
    
    # 8. 展示查询结果
    print("8. 展示查询结果...")
    print(f"   片段1: {all_segments[0].text[:30]}...")
    print(f"   批注1: {annotations[0].content[:30]}...")
    print(f"   行为1: {behaviors[0].event_type} (停留{behaviors[0].metadata['duration']}秒)\n")
    
    print("✓ 示例完成！")


if __name__ == "__main__":
    asyncio.run(main())
