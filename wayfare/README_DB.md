# WayFare SQLite数据库层

## 概述

`wayfare.db`模块提供了WayFare后端的SQLite数据库层实现，负责存储和管理文档元数据、片段、批注和用户行为数据。

## 特性

- ✅ 完整的CRUD操作支持
- ✅ 异步API（基于aiosqlite）
- ✅ 外键约束和级联删除
- ✅ 自动索引优化
- ✅ 类型安全的数据类
- ✅ 完整的单元测试覆盖

## 数据模型

### 1. Documents（文档表）

存储文档元数据和解析状态。

```python
{
    "hash": str,           # BLAKE3文档hash（主键）
    "path": str,           # 文档路径
    "status": str,         # 状态: pending/processing/completed/failed
    "updated_at": str,     # 最后更新时间（ISO 8601）
    "version_hash": str    # 内容版本hash
}
```

### 2. Segments（片段表）

存储文档片段和位置信息。

```python
DocumentSegment(
    id: str,              # 片段ID
    doc_hash: str,        # 关联的文档hash
    text: str,            # 片段文本内容
    page: int,            # 页码
    bbox: BoundingBox     # 边界框
)
```

### 3. Annotations（批注表）

存储AI生成的批注。

```python
Annotation(
    id: str,              # 批注ID（UUID）
    doc_hash: str,        # 关联的文档hash
    version_hash: str,    # 文档版本hash
    type: str,            # 批注类型: explanation/question/summary
    content: str,         # 批注内容
    bbox: BoundingBox,    # 批注位置
    created_at: str       # 创建时间
)
```

### 4. Behaviors（行为表）

存储用户学习行为数据。

```python
BehaviorEvent(
    id: str,              # 行为ID（UUID）
    doc_hash: str,        # 关联的文档hash
    page: int,            # 页码
    event_type: str,      # 事件类型: page_view/text_select/scroll
    timestamp: str,       # 事件时间
    metadata: dict        # 额外元数据（JSON）
)
```

## 使用示例

### 初始化数据库

```python
from wayfare.db import SQLiteDB

db = SQLiteDB(".wayfare/wayfare.db")
await db.initialize()
```

### 文档操作

```python
# 保存文档
doc = {
    "hash": "doc_hash_123",
    "path": "/path/to/doc.pdf",
    "status": "processing",
    "version_hash": "version_abc"
}
await db.save_document(doc)

# 获取文档
doc = await db.get_document("doc_hash_123")

# 更新状态
await db.update_document_status("doc_hash_123", "completed")

# 删除文档（级联删除关联数据）
await db.delete_document("doc_hash_123")
```

### 片段操作

```python
from wayfare.db import DocumentSegment, BoundingBox

# 保存片段
segments = [
    DocumentSegment(
        id="seg_1",
        doc_hash="doc_hash_123",
        text="这是一个文档片段",
        page=0,
        bbox=BoundingBox(x=10.0, y=20.0, width=200.0, height=50.0)
    )
]
await db.save_segments(segments)

# 获取单个片段
segment = await db.get_segment("seg_1")

# 获取文档的所有片段
segments = await db.get_segments_by_document("doc_hash_123")

# 统计片段数量
count = await db.count_segments("doc_hash_123")

# 删除文档的所有片段
await db.delete_segments("doc_hash_123")
```

### 批注操作

```python
from wayfare.db import Annotation
from datetime import datetime, timezone

# 保存批注
annotation = Annotation(
    id="ann_1",
    doc_hash="doc_hash_123",
    version_hash="version_abc",
    type="explanation",
    content="这是一个解释性批注",
    bbox=BoundingBox(x=50.0, y=100.0, width=300.0, height=80.0),
    created_at=datetime.now(timezone.utc).isoformat()
)
await db.save_annotation(annotation)

# 获取单个批注
annotation = await db.get_annotation("ann_1")

# 获取文档的所有批注
annotations = await db.get_annotations_by_document("doc_hash_123")

# 按版本过滤批注
annotations = await db.get_annotations_by_document(
    "doc_hash_123", 
    version_hash="version_abc"
)

# 删除批注
await db.delete_annotation("ann_1")

# 删除文档的所有批注
await db.delete_annotations_by_document("doc_hash_123")
```

### 行为数据操作

```python
from wayfare.db import BehaviorEvent

# 保存行为数据
behavior = BehaviorEvent(
    id="beh_1",
    doc_hash="doc_hash_123",
    page=0,
    event_type="page_view",
    timestamp=datetime.now(timezone.utc).isoformat(),
    metadata={"duration": 120, "scroll_depth": 0.8}
)
await db.save_behavior(behavior)

# 获取文档的所有行为数据
behaviors = await db.get_behaviors("doc_hash_123")

# 按页码过滤行为数据
behaviors = await db.get_behaviors("doc_hash_123", page=0)

# 删除文档的所有行为数据
await db.delete_behaviors("doc_hash_123")
```

## 数据库Schema

### 表结构

```sql
-- 文档表
CREATE TABLE documents (
    hash TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version_hash TEXT NOT NULL
);

-- 片段表
CREATE TABLE segments (
    id TEXT PRIMARY KEY,
    doc_hash TEXT NOT NULL,
    text TEXT NOT NULL,
    page INTEGER NOT NULL,
    bbox_x REAL NOT NULL,
    bbox_y REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
);

-- 批注表
CREATE TABLE annotations (
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
);

-- 行为数据表
CREATE TABLE behaviors (
    id TEXT PRIMARY KEY,
    doc_hash TEXT NOT NULL,
    page INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
);
```

### 索引

- `idx_documents_status`: 文档状态索引
- `idx_documents_path`: 文档路径索引
- `idx_segments_doc_hash`: 片段文档hash索引
- `idx_segments_page`: 片段页码索引
- `idx_annotations_doc_hash`: 批注文档hash索引
- `idx_annotations_version`: 批注版本索引
- `idx_annotations_type`: 批注类型索引
- `idx_behaviors_doc_page`: 行为文档+页码索引
- `idx_behaviors_timestamp`: 行为时间戳索引
- `idx_behaviors_type`: 行为类型索引

## 级联删除

删除文档时，会自动级联删除：
- 该文档的所有片段
- 该文档的所有批注
- 该文档的所有行为数据

这通过SQLite的外键约束`ON DELETE CASCADE`实现。

## 测试

运行测试：

```bash
python -m pytest tests/wayfare/test_db.py -v
```

测试覆盖：
- ✅ Documents表CRUD操作
- ✅ Segments表CRUD操作
- ✅ Annotations表CRUD操作
- ✅ Behaviors表CRUD操作
- ✅ 数据库初始化
- ✅ 级联删除

## 性能考虑

1. **索引优化**: 所有常用查询字段都建立了索引
2. **批量操作**: `save_segments`支持批量插入
3. **外键约束**: 启用外键约束确保数据完整性
4. **异步操作**: 所有数据库操作都是异步的，不会阻塞主线程

## 依赖

- `aiosqlite>=0.20.0`: 异步SQLite库

## 注意事项

1. 数据库文件默认存储在`.wayfare/wayfare.db`
2. 所有时间戳使用ISO 8601格式（UTC时区）
3. 外键约束默认启用，确保数据完整性
4. 删除文档会级联删除所有关联数据
5. 使用`datetime.now(timezone.utc)`而非已弃用的`datetime.utcnow()`

## 完整示例

参见`examples/db_usage_example.py`获取完整的使用示例。
