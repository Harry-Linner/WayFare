"""
Document Parser使用示例

演示如何使用DocumentParser解析PDF和Markdown文档。
"""

import asyncio
import logging
from pathlib import Path

from wayfare.document_parser import DocumentParser
from wayfare.embedding import EmbeddingService
from wayfare.vector_store import VectorStore
from wayfare.db import SQLiteDB

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_basic_usage():
    """基本使用示例"""
    print("\n=== 基本使用示例 ===\n")
    
    # 1. 初始化依赖
    embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
    vector_store = VectorStore("http://localhost:6333")
    db = SQLiteDB(".wayfare/wayfare.db")
    
    # 初始化数据库和向量存储
    await db.initialize()
    await vector_store.initialize()
    
    # 2. 创建DocumentParser
    parser = DocumentParser(
        embedding_service=embedding_service,
        vector_store=vector_store,
        db=db,
        chunk_size=300,
        chunk_overlap=50
    )
    
    # 3. 解析文档
    try:
        result = await parser.parse_document("example.pdf")
        
        print(f"✓ 文档解析成功")
        print(f"  - Document Hash: {result.doc_hash}")
        print(f"  - Version Hash: {result.version_hash}")
        print(f"  - Segment Count: {result.segment_count}")
        print(f"  - Status: {result.status}")
        
    except Exception as e:
        print(f"✗ 文档解析失败: {e}")


async def example_compute_hashes():
    """Hash计算示例"""
    print("\n=== Hash计算示例 ===\n")
    
    # 创建临时文件用于演示
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("这是测试文档内容")
        temp_path = f.name
    
    try:
        # 初始化parser（简化版，不需要完整依赖）
        parser = DocumentParser(
            embedding_service=None,
            vector_store=None,
            db=None
        )
        
        # 1. 计算文件hash
        doc_hash = parser.compute_hash(temp_path)
        print(f"文件Hash (BLAKE3): {doc_hash}")
        print(f"Hash长度: {len(doc_hash)} 字符")
        
        # 2. 计算版本hash
        content = "这是文档内容文本"
        version_hash = parser.compute_version_hash(content)
        print(f"\n版本Hash: {version_hash}")
        
        # 3. 验证hash一致性
        doc_hash2 = parser.compute_hash(temp_path)
        print(f"\nHash一致性验证: {doc_hash == doc_hash2}")
        
    finally:
        Path(temp_path).unlink()


async def example_text_chunking():
    """文本分块示例"""
    print("\n=== 文本分块示例 ===\n")
    
    parser = DocumentParser(
        embedding_service=None,
        vector_store=None,
        db=None,
        chunk_size=100,  # 较小的chunk用于演示
        chunk_overlap=20
    )
    
    # 测试文本
    text = """
    这是第一段内容。它包含了一些重要的信息。
    这是第二段内容。它继续讨论相关的主题。
    这是第三段内容。它总结了前面的观点。
    这是第四段内容。它提出了新的问题。
    这是第五段内容。它给出了最终的结论。
    """.strip()
    
    # 分块
    chunks = parser.chunk_text(text)
    
    print(f"原始文本长度: {len(text)} 字符")
    print(f"生成chunk数量: {len(chunks)}\n")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1} ({len(chunk)} 字符):")
        print(f"  {chunk[:50]}...")
        print()


async def example_parse_pdf():
    """PDF解析示例"""
    print("\n=== PDF解析示例 ===\n")
    
    # 初始化依赖
    embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
    vector_store = VectorStore("http://localhost:6333")
    db = SQLiteDB(".wayfare/wayfare.db")
    
    await db.initialize()
    await vector_store.initialize()
    
    parser = DocumentParser(
        embedding_service=embedding_service,
        vector_store=vector_store,
        db=db
    )
    
    # 解析PDF
    pdf_path = "example.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠ PDF文件不存在: {pdf_path}")
        print("  请提供一个有效的PDF文件路径")
        return
    
    try:
        # 计算hash
        doc_hash = parser.compute_hash(pdf_path)
        print(f"Document Hash: {doc_hash}\n")
        
        # 解析PDF
        segments = await parser.parse_pdf(pdf_path, doc_hash)
        
        print(f"✓ PDF解析成功")
        print(f"  - 总片段数: {len(segments)}")
        print(f"  - 总页数: {max(s.page for s in segments) + 1}")
        
        # 显示前3个片段
        print("\n前3个片段:")
        for i, segment in enumerate(segments[:3]):
            print(f"\n  Segment {i + 1}:")
            print(f"    - ID: {segment.id}")
            print(f"    - Page: {segment.page}")
            print(f"    - Text: {segment.text[:80]}...")
            print(f"    - BBox: ({segment.bbox.x}, {segment.bbox.y}, "
                  f"{segment.bbox.width}, {segment.bbox.height})")
        
    except Exception as e:
        print(f"✗ PDF解析失败: {e}")


async def example_parse_markdown():
    """Markdown解析示例"""
    print("\n=== Markdown解析示例 ===\n")
    
    # 创建临时Markdown文件
    import tempfile
    
    markdown_content = """
# 第一章：引言

这是引言部分的内容。它介绍了文档的主要主题。

## 1.1 背景

背景部分提供了必要的上下文信息。

## 1.2 目标

本文档的目标是演示Markdown解析功能。

# 第二章：主要内容

这是主要内容部分。它详细讨论了核心概念。

## 2.1 概念A

概念A的详细说明。

## 2.2 概念B

概念B的详细说明。
"""
    
    with tempfile.NamedTemporaryFile(
        mode='w', 
        delete=False, 
        suffix='.md',
        encoding='utf-8'
    ) as f:
        f.write(markdown_content)
        temp_path = f.name
    
    try:
        # 初始化依赖
        embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
        vector_store = VectorStore("http://localhost:6333")
        db = SQLiteDB(".wayfare/wayfare.db")
        
        await db.initialize()
        await vector_store.initialize()
        
        parser = DocumentParser(
            embedding_service=embedding_service,
            vector_store=vector_store,
            db=db
        )
        
        # 计算hash
        doc_hash = parser.compute_hash(temp_path)
        print(f"Document Hash: {doc_hash}\n")
        
        # 解析Markdown
        segments = await parser.parse_markdown(temp_path, doc_hash)
        
        print(f"✓ Markdown解析成功")
        print(f"  - 总片段数: {len(segments)}")
        print(f"  - 总节数: {max(s.page for s in segments) + 1}")
        
        # 显示所有片段
        print("\n所有片段:")
        for i, segment in enumerate(segments):
            print(f"\n  Segment {i + 1}:")
            print(f"    - Section: {segment.page}")
            print(f"    - Text: {segment.text[:100]}...")
        
    except Exception as e:
        print(f"✗ Markdown解析失败: {e}")
    finally:
        Path(temp_path).unlink()


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===\n")
    
    from wayfare.errors import DocumentParseError
    
    parser = DocumentParser(
        embedding_service=None,
        vector_store=None,
        db=None
    )
    
    # 1. 文件不存在
    print("1. 测试文件不存在:")
    try:
        parser.compute_hash("/nonexistent/file.pdf")
    except FileNotFoundError as e:
        print(f"   ✓ 捕获到预期错误: {type(e).__name__}")
    
    # 2. 不支持的文件类型
    print("\n2. 测试不支持的文件类型:")
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("text content")
        temp_path = f.name
    
    try:
        # 需要完整的parser来测试parse_document
        embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
        vector_store = VectorStore("http://localhost:6333")
        db = SQLiteDB(".wayfare/wayfare.db")
        
        await db.initialize()
        
        full_parser = DocumentParser(
            embedding_service=embedding_service,
            vector_store=vector_store,
            db=db
        )
        
        await full_parser.parse_document(temp_path)
    except DocumentParseError as e:
        print(f"   ✓ 捕获到预期错误: {type(e).__name__}")
        print(f"   错误信息: {e}")
    finally:
        Path(temp_path).unlink()


async def example_complete_workflow():
    """完整工作流示例"""
    print("\n=== 完整工作流示例 ===\n")
    
    # 创建测试文档
    import tempfile
    
    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.md',
        encoding='utf-8'
    ) as f:
        f.write("# 测试文档\n\n这是测试内容。" * 50)
        temp_path = f.name
    
    try:
        # 1. 初始化所有组件
        print("1. 初始化组件...")
        embedding_service = EmbeddingService("models/bge-small-zh-v1.5.onnx")
        vector_store = VectorStore("http://localhost:6333")
        db = SQLiteDB(".wayfare/wayfare.db")
        
        await db.initialize()
        await vector_store.initialize()
        
        parser = DocumentParser(
            embedding_service=embedding_service,
            vector_store=vector_store,
            db=db
        )
        print("   ✓ 组件初始化完成\n")
        
        # 2. 解析文档
        print("2. 解析文档...")
        result = await parser.parse_document(temp_path)
        print(f"   ✓ 解析完成")
        print(f"   - Hash: {result.doc_hash}")
        print(f"   - Segments: {result.segment_count}\n")
        
        # 3. 查询数据库验证
        print("3. 验证数据库存储...")
        doc = await db.get_document(result.doc_hash)
        segments = await db.get_segments_by_document(result.doc_hash)
        print(f"   ✓ 数据库验证成功")
        print(f"   - 文档状态: {doc['status']}")
        print(f"   - 存储片段数: {len(segments)}\n")
        
        # 4. 测试重复解析（应该使用缓存）
        print("4. 测试重复解析...")
        result2 = await parser.parse_document(temp_path)
        print(f"   ✓ 使用缓存结果")
        print(f"   - Hash匹配: {result.doc_hash == result2.doc_hash}")
        print(f"   - Segment数匹配: {result.segment_count == result2.segment_count}\n")
        
        print("✓ 完整工作流测试成功！")
        
    except Exception as e:
        print(f"✗ 工作流失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        Path(temp_path).unlink()


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("Document Parser 使用示例")
    print("=" * 60)
    
    # 运行各个示例
    await example_compute_hashes()
    await example_text_chunking()
    await example_error_handling()
    
    # 以下示例需要实际的模型和服务
    print("\n" + "=" * 60)
    print("注意：以下示例需要实际的ONNX模型和Qdrant服务")
    print("=" * 60)
    
    # await example_basic_usage()
    # await example_parse_pdf()
    # await example_parse_markdown()
    # await example_complete_workflow()


if __name__ == "__main__":
    asyncio.run(main())
