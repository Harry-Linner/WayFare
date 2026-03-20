from typing import Any, Dict, List

import fitz  # PyMuPDF
from loguru import logger

MIN_BLOCK_TEXT_LENGTH = 5
LOW_TEXT_DENSITY_THRESHOLD = 32


def _page_text_density(text_blocks: List[Dict[str, Any]]) -> int:
    return sum(len(block.get("text", "").strip()) for block in text_blocks)


def _normalize_block(raw_block: tuple[Any, ...]) -> Dict[str, Any] | None:
    x0, y0, x1, y1, text, _block_no, block_type = raw_block
    normalized_text = str(text or "").strip()
    if block_type != 0 or len(normalized_text) < MIN_BLOCK_TEXT_LENGTH:
        return None

    return {
        "text": normalized_text,
        "bbox": {
            "x": round(float(x0), 2),
            "y": round(float(y0), 2),
            "w": round(float(x1) - float(x0), 2),
            "h": round(float(y1) - float(y0), 2),
        },
    }


def get_document_metadata_sync(path: str) -> Dict[str, Any]:
    try:
        doc = fitz.open(path)
        low_text_pages = 0
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = [_normalize_block(block) for block in page.get_text("blocks")]
            blocks = [block for block in blocks if block]
            if _page_text_density(blocks) < LOW_TEXT_DENSITY_THRESHOLD:
                low_text_pages += 1

        meta = {
            "pageCount": len(doc),
            "ocrRecommended": low_text_pages > 0,
            "lowTextPageCount": low_text_pages,
        }
        doc.close()
        return meta
    except Exception as exc:
        logger.error(f"PyMuPDF failed to read metadata for {path}: {exc}")
        return {"pageCount": 0, "ocrRecommended": False, "lowTextPageCount": 0}


def _extract_and_chunk_pdf_sync(path: str) -> List[Dict[str, Any]]:
    """
    同步 PDF 解析与切块逻辑。

    当前策略：
    1. 优先走文本型 PDF 的 PyMuPDF 抽取；
    2. 对低文本密度页面记录日志，为后续 OCR fallback 预留判断点；
    3. 统一输出 page / text / bbox 结构，便于后续替换成更成熟的 OCR 管线。
    """

    chunks: List[Dict[str, Any]] = []
    try:
        doc = fitz.open(path)
        low_text_pages = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            raw_blocks = page.get_text("blocks")
            blocks = [_normalize_block(block) for block in raw_blocks]
            blocks = [block for block in blocks if block]

            if _page_text_density(blocks) < LOW_TEXT_DENSITY_THRESHOLD:
                low_text_pages.append(page_num + 1)

            for block in blocks:
                chunks.append(
                    {
                        "page": page_num,
                        "text": block["text"],
                        "bbox": block["bbox"],
                    }
                )

        doc.close()

        if low_text_pages:
            logger.warning(
                f"PDF text density is low on pages {low_text_pages}; OCR fallback is recommended for future runs."
            )

        return chunks
    except Exception as exc:
        logger.error(f"PyMuPDF failed to parse {path}: {exc}")
        raise
