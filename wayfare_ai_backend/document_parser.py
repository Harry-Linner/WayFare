import fitz  # PyMuPDF
import re
from loguru import logger
from typing import List, Dict, Any


def _extract_and_chunk_pdf_sync(path: str) -> List[Dict[str, Any]]:
    """
    同步的 PDF 解析与切块逻辑（供 run_in_executor 调用，防止阻塞 asyncio）
    """
    chunks = []
    try:
        doc = fitz.open(path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # 获取页面所有的文本块及其坐标
            blocks = page.get_text("blocks")

            for b in blocks:
                x0, y0, x1, y1, text, block_no, block_type = b
                # 过滤掉非文本块 (如图片) 和极其短小的无意义空白
                text = text.strip()
                if block_type != 0 or len(text) < 5:
                    continue

                # 构建 Chunk 对象
                chunks.append({
                    "page": page_num,
                    "text": text,
                    "bbox": {
                        "x": round(x0, 2),
                        "y": round(y0, 2),
                        "w": round(x1 - x0, 2),
                        "h": round(y1 - y0, 2)
                    }
                })
        doc.close()
        return chunks
    except Exception as e:
        logger.error(f"PyMuPDF failed to parse {path}: {e}")
        raise