# WayFare 测试数据和示例文件

本目录包含用于测试WayFare后端的示例文件和测试数据生成工具。

## 目录结构

```
tests/fixtures/
├── README.md                          # 本文件
├── mock_data.py                       # 测试数据生成器
└── sample_documents/                  # 示例文档目录
    ├── generate_sample_pdf.py         # PDF生成脚本
    ├── simple_test.md                 # 简单测试Markdown
    ├── sample_markdown.md             # 费曼学习法示例Markdown
    ├── simple_test.pdf                # 简单测试PDF（需生成）
    └── sample_learning_material.pdf   # 学习材料示例PDF（需生成）
```

## 示例文档

### Markdown文件

1. **simple_test.md**
   - 简单的测试文档
   - 包含基本的标题和段落结构
   - 用于测试基本的Markdown解析功能

2. **sample_markdown.md**
   - 费曼学习法介绍文档
   - 包含多级标题、段落、列表等复杂结构
   - 用于测试完整的Markdown解析和分块功能

### PDF文件

PDF文件需要通过脚本生成。运行以下命令：

```bash
# 确保安装了reportlab
pip install reportlab

# 生成PDF文件
cd tests/fixtures/sample_documents
python generate_sample_pdf.py
```

生成的PDF文件：

1. **simple_test.pdf**
   - 简单的测试PDF
   - 包含3个章节的英文内容
   - 用于测试基本的PDF解析功能

2. **sample_learning_material.pdf**
   - Python基础学习材料
   - 包含4个章节的详细内容
   - 用于测试完整的PDF解析和分块功能

## 测试数据生成器 (mock_data.py)

`mock_data.py` 提供了一套完整的测试数据生成函数，用于在单元测试和集成测试中创建模拟数据。

### 主要功能

#### 1. 单个数据生成

```python
from tests.fixtures.mock_data import *

# 生成文档
doc = mock_document(path="/test/doc.pdf", status="completed")

# 生成片段
segment = mock_segment(doc["hash"], text="测试文本", page=0)

# 生成批注
annotation = mock_annotation(
    doc["hash"],
    doc["version_hash"],
    annotation_type="explanation",
    content="这是一条批注"
)

# 生成行为数据
behavior = mock_behavior(
    doc["hash"],
    page=0,
    event_type="page_view"
)

# 生成IPC请求
request = mock_ipc_request("parse", {"path": "/test/doc.pdf"})

# 生成IPC响应
response = mock_ipc_response(
    request_id="123",
    seq=1,
    success=True,
    data={"docHash": "abc123"}
)

# 生成向量
vector = mock_vector(dimension=512)

# 生成搜索结果
result = mock_search_result(text="搜索结果", score=0.85)
```

#### 2. 批量数据生成

```python
# 生成多个文档
documents = generate_mock_documents(count=5)

# 生成多个片段
segments = generate_mock_segments(doc_hash="abc123", count=10)

# 生成多个批注
annotations = generate_mock_annotations(
    doc_hash="abc123",
    version_hash="ver123",
    count=5
)

# 生成多个行为数据
behaviors = generate_mock_behaviors(
    doc_hash="abc123",
    count=20,
    time_span_minutes=60
)
```

#### 3. 完整场景生成

```python
# 生成一个完整的测试场景
scenario = generate_complete_test_scenario()

# scenario 包含:
# - document: 1个文档
# - segments: 15个片段
# - annotations: 8个批注
# - behaviors: 30个行为记录
```

#### 4. 边缘情况测试数据

```python
# 空文档
empty_doc = mock_empty_document()

# 超大片段
large_segment = mock_large_segment(doc_hash="abc123")

# 特殊字符片段
special_segment = mock_special_characters_segment(doc_hash="abc123")

# Unicode字符片段
unicode_segment = mock_unicode_segment(doc_hash="abc123")
```

### 使用示例

#### 在单元测试中使用

```python
import pytest
from tests.fixtures.mock_data import mock_document, mock_segment

def test_document_parser():
    # 使用mock数据
    doc = mock_document(path="/test/doc.pdf")
    segment = mock_segment(doc["hash"], text="测试文本")
    
    # 执行测试
    assert doc["status"] == "completed"
    assert segment["doc_hash"] == doc["hash"]
```

#### 在集成测试中使用

```python
from tests.fixtures.mock_data import generate_complete_test_scenario

async def test_complete_workflow():
    # 生成完整场景
    scenario = generate_complete_test_scenario()
    
    # 使用场景数据进行测试
    doc = scenario["document"]
    segments = scenario["segments"]
    
    # 测试文档解析流程
    # ...
```

## 数据格式说明

### 文档 (Document)

```python
{
    "hash": "doc_abc123...",           # 文档hash (BLAKE3)
    "path": "/path/to/document.pdf",   # 文档路径
    "status": "completed",             # 状态: pending/processing/completed/failed
    "updated_at": "2024-01-01T12:00:00",  # 更新时间 (ISO格式)
    "version_hash": "ver_xyz789..."    # 版本hash
}
```

### 片段 (Segment)

```python
{
    "id": "seg_abc123...",             # 片段ID
    "doc_hash": "doc_abc123...",       # 所属文档hash
    "text": "片段文本内容",             # 文本内容
    "page": 0,                         # 页码
    "bbox_x": 0.0,                     # 边界框X坐标
    "bbox_y": 0.0,                     # 边界框Y坐标
    "bbox_width": 100.0,               # 边界框宽度
    "bbox_height": 50.0                # 边界框高度
}
```

### 批注 (Annotation)

```python
{
    "id": "ann_abc123...",             # 批注ID
    "doc_hash": "doc_abc123...",       # 所属文档hash
    "version_hash": "ver_xyz789...",   # 文档版本hash
    "type": "explanation",             # 类型: explanation/question/summary
    "content": "批注内容",              # 批注文本
    "bbox_x": 0.0,                     # 边界框X坐标
    "bbox_y": 0.0,                     # 边界框Y坐标
    "bbox_width": 100.0,               # 边界框宽度
    "bbox_height": 50.0,               # 边界框高度
    "created_at": "2024-01-01T12:00:00"  # 创建时间 (ISO格式)
}
```

### 行为 (Behavior)

```python
{
    "id": "beh_abc123...",             # 行为ID
    "doc_hash": "doc_abc123...",       # 所属文档hash
    "page": 0,                         # 页码
    "event_type": "page_view",         # 事件类型: page_view/text_select/scroll
    "timestamp": "2024-01-01T12:00:00",  # 时间戳 (ISO格式)
    "metadata": "{...}"                # 额外元数据 (JSON字符串)
}
```

### IPC请求 (IPC Request)

```python
{
    "id": "uuid-string",               # 请求ID (UUID)
    "seq": 1,                          # 序列号
    "method": "parse",                 # 方法: parse/annotate/query/config
    "params": {...}                    # 请求参数
}
```

### IPC响应 (IPC Response)

```python
{
    "id": "uuid-string",               # 请求ID (与请求对应)
    "seq": 1,                          # 序列号 (与请求对应)
    "success": true,                   # 是否成功
    "data": {...}                      # 响应数据 (成功时)
    # 或
    "error": "错误信息"                 # 错误信息 (失败时)
}
```

## 添加自定义测试数据

如果需要添加自定义的测试文档：

1. **添加Markdown文件**：直接在 `sample_documents/` 目录下创建 `.md` 文件

2. **添加PDF文件**：
   - 方法1：手动复制PDF文件到 `sample_documents/` 目录
   - 方法2：修改 `generate_sample_pdf.py` 脚本添加新的生成函数

3. **添加新的mock函数**：在 `mock_data.py` 中添加新的数据生成函数

## 注意事项

1. **PDF生成依赖**：生成PDF文件需要安装 `reportlab` 库
2. **文件大小**：示例文档应保持较小的文件大小（< 1MB）
3. **字符编码**：所有文本文件使用UTF-8编码
4. **数据一致性**：使用mock_data.py生成的数据保证ID和hash的一致性
5. **时间戳**：行为数据的时间戳使用ISO 8601格式

## 测试最佳实践

1. **使用mock数据**：优先使用 `mock_data.py` 生成测试数据，而不是硬编码
2. **场景测试**：使用 `generate_complete_test_scenario()` 进行端到端测试
3. **边缘情况**：使用提供的边缘情况函数测试异常处理
4. **数据隔离**：每个测试使用独立的mock数据，避免测试间相互影响
5. **清理数据**：测试结束后清理生成的临时数据

## 相关文档

- [测试指南](../../DEVELOPMENT.md#测试)
- [API文档](../../API.md)
- [架构文档](../../ARCHITECTURE.md)
