# Document Parser 文档

## 概述

DocumentParser是WayFare后端的文档解析引擎，负责将PDF和Markdown文档转换为结构化片段，并生成向量用于语义检索。

## 核心功能

1. **文档Hash计算**: 使用BLAKE3算法生成文档唯一标识
2. **版本Hash计算**: 检测文档内容变更
3. **PDF解析**: 使用PyMuPDF提取文本、页码和边界框信息
4. **Markdown解析**: 使用markdown-it-py提取结构化内容
5. **智能分块**: 在句子边界分割文本，保持语义连贯性
6. **向量化**: 自动生成片段向量并存储到Qdrant

## 依赖要求

```bash
pip install blake3 PyMuPDF markdown-it-py
```

## 使用示例

### 基本用法

```python
from wayfare.document_parser import DocumentParser
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore
from wayfare.db import SQLiteDB

# 初始化依赖
embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
vector_store = VectorStore("http://localhost:6333")
db = SQLiteDB(".wayfare/wayfare.db")

# 创建解析器
parser = DocumentParser(
    embedding_service=embedding_service,
    vector_store=vector_store,
    db=db,
    chunk_size=300,
    chunk_overlap=50
)

# 解析文档
result = await parser.parse_document("document.pdf")
print(f"Document hash: {result.doc_hash}")
print(f"Segments: {result.segment_count}")
print(f"Status: {result.status}")
```

### 计算文档Hash

```python
# 计算文件hash（BLAKE3）
doc_hash = parser.compute_hash("document.pdf")
print(f"Document hash: {doc_hash}")  # 64字符的十六进制字符串

# 计算内容版本hash
content = "文档内容文本"
version_hash = parser.compute_version_hash(content)
print(f"Version hash: {version_hash}")
```

### 解析PDF文档

```python
# 解析PDF并提取片段
segments = await parser.parse_pdf("document.pdf", "doc_hash_123")

for segment in segments:
    print(f"Page {segment.page}: {segment.text[:50]}...")
    print(f"BBox: ({segment.bbox.x}, {segment.bbox.y})")
```

### 解析Markdown文档

```python
# 解析Markdown文档
segments = await parser.parse_markdown("document.md", "doc_hash_456")

for segment in segments:
    print(f"Section {segment.page}: {segment.text[:50]}...")
```

### 文本分块

```python
# 智能分块（在句子边界分割）
text = "这是第一句话。这是第二句话。" * 100
chunks = parser.chunk_text(text)

print(f"Total chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {len(chunk)} chars")
```

## API参考

### DocumentParser类

#### 构造函数

```python
DocumentParser(
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    db: SQLiteDB,
    chunk_size: int = 300,
    chunk_overlap: int = 50
)
```

**参数**:
- `embedding_service`: Embedding服务实例
- `vector_store`: 向量存储实例
- `db`: SQLite数据库实例
- `chunk_size`: 分块大小（字符数），默认300
- `chunk_overlap`: 分块重叠大小（字符数），默认50

#### 方法

##### compute_hash(path: str) -> str

计算文档的BLAKE3 hash。

**参数**:
- `path`: 文档路径

**返回**: 64字符的十六进制hash字符串

**异常**:
- `FileNotFoundError`: 文件不存在
- `IOError`: 文件读取失败

##### compute_version_hash(content: str) -> str

计算内容的版本hash。

**参数**:
- `content`: 文档内容文本

**返回**: 64字符的十六进制hash字符串

##### async parse_document(path: str) -> ParseResult

解析文档的主入口方法。

**参数**:
- `path`: 文档路径

**返回**: `ParseResult`对象，包含:
- `doc_hash`: 文档hash
- `version_hash`: 版本hash
- `segment_count`: 片段数量
- `status`: 解析状态

**异常**:
- `FileNotFoundError`: 文件不存在
- `ValueError`: 不支持的文件类型
- `DocumentParseError`: 解析失败

##### async parse_pdf(path: str, doc_hash: str) -> List[DocumentSegment]

解析PDF文档。

**参数**:
- `path`: PDF文件路径
- `doc_hash`: 文档hash

**返回**: `DocumentSegment`列表

**异常**:
- `ImportError`: PyMuPDF未安装
- `RuntimeError`: PDF解析失败

##### async parse_markdown(path: str, doc_hash: str) -> List[DocumentSegment]

解析Markdown文档。

**参数**:
- `path`: Markdown文件路径
- `doc_hash`: 文档hash

**返回**: `DocumentSegment`列表

**异常**:
- `ImportError`: markdown-it-py未安装
- `RuntimeError`: Markdown解析失败

##### chunk_text(text: str) -> List[str]

将文本分割为语义连贯的片段。

**参数**:
- `text`: 输入文本

**返回**: 文本片段列表

**特性**:
- 优先在句子边界分割（。！？.!?）
- 使用滑动窗口保持上下文连贯性
- 自动处理空文本和短文本

## 数据模型

### ParseResult

```python
@dataclass
class ParseResult:
    doc_hash: str          # 文档hash
    version_hash: str      # 版本hash
    segment_count: int     # 片段数量
    status: str           # 状态: completed/failed
```

### DocumentSegment

```python
@dataclass
class DocumentSegment:
    id: str               # 片段ID: {doc_hash}_{page}_{index}
    doc_hash: str         # 文档hash
    text: str            # 片段文本
    page: int            # 页码
    bbox: BoundingBox    # 边界框
```

### BoundingBox

```python
@dataclass
class BoundingBox:
    x: float             # X坐标
    y: float             # Y坐标
    width: float         # 宽度
    height: float        # 高度
```

## 工作流程

### 文档解析流程

```
1. 计算文档hash (BLAKE3)
   ↓
2. 检查是否已解析
   ↓
3. 根据文件类型选择解析器
   ├─ PDF → parse_pdf()
   └─ Markdown → parse_markdown()
   ↓
4. 提取文本并分块
   ↓
5. 计算版本hash
   ↓
6. 保存文档元数据到SQLite
   ↓
7. 保存片段到SQLite
   ↓
8. 生成向量并存储到Qdrant
   ↓
9. 更新文档状态为completed
```

### 分块策略

```
输入文本
   ↓
检查长度 ≤ chunk_size?
   ├─ 是 → 返回单个chunk
   └─ 否 → 滑动窗口分块
           ↓
       查找句子边界
           ↓
       在边界处分割
           ↓
       应用overlap
           ↓
       返回chunk列表
```

## 配置参数

### 分块参数

- **chunk_size**: 300字符
  - 平衡语义完整性和检索精度
  - 适合中文文档（约150-200个汉字）

- **chunk_overlap**: 50字符
  - 保持上下文连贯性
  - 避免句子被截断

### Hash算法

- **BLAKE3**: 
  - 比SHA-256更快
  - 安全性高
  - 64字符十六进制输出

## 错误处理

### 可恢复错误

```python
from wayfare.errors import DocumentParseError

try:
    result = await parser.parse_document("document.pdf")
except DocumentParseError as e:
    print(f"Parse failed: {e.reason}")
    # 可以继续处理其他文档
```

### 不可恢复错误

```python
from wayfare.errors import ModelLoadError

try:
    parser = DocumentParser(...)
except ModelLoadError as e:
    print(f"Fatal error: {e}")
    # 系统应该退出
```

## 性能优化

### 批量向量化

```python
# 自动批量处理，无需手动优化
segments = await parser.parse_pdf("large.pdf", "hash")
# 内部会批量调用 embedding_service.embed_texts()
```

### 缓存已解析文档

```python
# 自动检查数据库，避免重复解析
result = await parser.parse_document("document.pdf")
# 如果已解析，直接返回缓存结果
```

## 测试

运行单元测试：

```bash
pytest tests/wayfare/test_document_parser.py -v
```

测试覆盖：
- Hash计算（文件hash和版本hash）
- 文本分块（短文本、长文本、句子边界）
- PDF解析（单页、多页、错误处理）
- Markdown解析（标题、段落、错误处理）
- 向量化（成功、失败、空列表）
- 集成测试（完整解析流程）

## 限制和注意事项

1. **PDF解析限制**:
   - 仅支持文本PDF，不支持扫描版PDF（需要OCR）
   - 边界框信息简化为页面级别（MVP阶段）
   - 不处理图片、表格等非文本内容

2. **Markdown解析限制**:
   - 使用虚拟页码（没有真实页码概念）
   - 以标题为分段依据
   - 不处理代码块、表格等复杂结构

3. **分块限制**:
   - 简单的滑动窗口策略
   - 可能在长句子中间分割
   - 不考虑段落或章节语义

4. **性能考虑**:
   - 大文件（>10MB）解析可能较慢
   - 向量化是CPU密集型操作
   - 建议异步处理，避免阻塞

## 未来改进

1. **增强PDF解析**:
   - 精确的文本块边界框
   - 表格和图片提取
   - OCR支持

2. **智能分块**:
   - 基于语义的分块
   - 段落和章节感知
   - 动态chunk大小

3. **性能优化**:
   - GPU加速向量化
   - 并行处理多文档
   - 增量更新（仅处理变更部分）

4. **格式支持**:
   - Word文档（.docx）
   - PowerPoint（.pptx）
   - HTML网页

## 相关文档

- [Embedding Service](./README_EMBEDDING.md)
- [Vector Store](./README_VECTOR_STORE.md)
- [Database](./README_DB.md)
- [Error Handling](./README_LOGGING_ERRORS.md)

## Requirements映射

本模块实现以下需求：

- **Requirement 2.1**: Parse PDF files and extract text, page numbers, and bounding box information
- **Requirement 2.4**: Generate unique hash identifier for each document (using BLAKE3)
- **Requirement 2.5**: Generate versionHash to detect content changes
- **Requirement 9.1**: Parse PDF documents and generate structured DocumentSegment objects
