import asyncio
import json
import uuid
import hashlib
import time
from loguru import logger
from typing import Any, Dict

from config import settings
from database import (
    search_similar_chunks, insert_knowledge_chunk,
    insert_cognitive_trace
)
from llm_provider import llm_client
from embedding_provider import embed_client
from document_parser import _extract_and_chunk_pdf_sync
from context_builder import build_annotate_prompt

page_dwell_state: Dict[str, float] = {}


def send_notification(notification_data: dict):
    payload = {"type": "notification", "data": notification_data}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


# ----------------- 真实的 PARSE (解析与向量入库) -----------------
async def _background_parse(path: str, doc_hash: str):
    logger.info(f"Starting real background parse for {doc_hash} ({path})")
    try:
        loop = asyncio.get_running_loop()
        # 1. 在线程池中执行 CPU 密集型的 PDF 解析
        chunks = await loop.run_in_executor(None, _extract_and_chunk_pdf_sync, path)
        logger.info(f"Extracted {len(chunks)} chunks from {path}")

        # 2. 批量获取 Embedding 并存入 PostgreSQL
        success_count = 0
        for chunk in chunks:
            # 避免单次并发太高，稍微限流
            emb = await embed_client.get_embedding(chunk["text"])
            if emb and len(emb) > 0:
                await insert_knowledge_chunk(
                    doc_hash=doc_hash,
                    page=chunk["page"],
                    content=chunk["text"],
                    kp="",  # 稍后在用户查阅时由 LLM 提取填入，或独立跑批
                    freq="0",
                    bbox=chunk["bbox"],
                    embedding=emb
                )
                success_count += 1

        send_notification({
            "type": "parse_completed",
            "docHash": doc_hash,
            "segmentCount": success_count,
            "status": "completed"
        })
        logger.info(f"Parse completed for {doc_hash}, {success_count} vectors inserted.")

    except Exception as e:
        logger.error(f"Parse failed: {e}")
        send_notification({
            "type": "parse_failed",
            "docHash": doc_hash,
            "error": str(e)
        })


async def handle_parse(params: Dict[str, Any]) -> Dict[str, Any]:
    path = params.get("path")
    if not path:
        raise ValueError("path is required for parse")
    doc_hash = hashlib.md5(path.encode('utf-8')).hexdigest()
    asyncio.create_task(_background_parse(path, doc_hash))
    return {"docHash": doc_hash, "status": "processing"}


# ----------------- 真实的 ANNOTATE (RAG + 强制 JSON 输出) -----------------
async def handle_annotate(params: Dict[str, Any]) -> Dict[str, Any]:
    anno_type = params.get("type", "explanation")
    context = params.get("context", "")  # 用户选中的文字，或多轮对话的最新追问
    history = params.get("history", [])  # 接收前端传来的历史聊天记录

    # 【核心升级 1】：兼容处理单文件 docHash 和多文件 docHashes
    doc_hashes = params.get("docHashes")
    if not doc_hashes:
        single_hash = params.get("docHash", "")
        doc_hashes = [single_hash] if single_hash else []

    # 1. 将用户最新的提问向量化，准备去查背景资料
    query_emb = await embed_client.get_embedding(context)

    rag_results = []
    # 2. 跨文件检索：带着数组去 pgvector 里捞针 (取 top 3 作为上下文)
    if any(query_emb) and doc_hashes:
        rag_results = await search_similar_chunks(doc_hashes, query_emb, limit=3)

    # 3. 组装复杂的 Prompt (System与User指令，把查到的资料塞进去)
    sys_prompt, user_prompt = build_annotate_prompt(anno_type, context, rag_results)

    # 4. 请求大模型，要求严格返回 JSON，并【注入历史对话 history】
    annotation_id = f"anno_{uuid.uuid4().hex[:8]}"
    try:
        res_json = await llm_client.call_llm(
            prompt=user_prompt,
            system_prompt=sys_prompt,
            history=history,  # 【核心升级 2】：联系上下文
            force_json=True
        )
        content = res_json.get("content", "生成解释失败。")
        kp = res_json.get("knowledge_point", "未知考点")
        # 多轮追问时如果不涉及考频，模型可能会返回默认值
        freq = res_json.get("frequency", "0次")

        # 记录用户认知轨迹 (这里的 user_id 后续可以从 params 里获取真实数据)
        await insert_cognitive_trace("default_user", "mock_uuid_no_db", f"annotate_{anno_type}", f"[{kp}] {content}")

    except Exception as e:
        logger.error(f"LLM fallback triggered: {e}")
        content = "⚠️ The model service is not available now。"
        kp = "unknown"

    return {
        "annotationId": annotation_id,
        "type": anno_type,
        "knowledge_point": kp,
        "content": content
    }


async def _rewrite_query_with_history(current_query: str, history: list) -> str:
    """
    内部辅助函数：根据多轮对话历史，将含有代词的简写问题重写为完整的检索词。
    """
    if not history:
        return current_query

    sys_prompt = """你是一个专业的检索词重写专家。
请根据用户的历史对话，将用户的最新提问重写为一个独立、完整、且包含所有必要上下文（如代词指代的具体实体）的检索句子。
【严格准则】：
1. 必须且只能输出重写后的句子，绝对不要包含任何解释、语气词、Markdown或引号。
2. 如果当前提问本身已经很完整，不需要重写，请原样输出。
3. 绝对不要回答用户的问题！你的唯一任务是重写句子！"""

    try:
        # 注意：这里我们不需要 JSON 格式，只需要纯文本，所以 force_json=False
        res = await llm_client.call_llm(
            prompt=f"最新提问：{current_query}",
            system_prompt=sys_prompt,
            history=history,
            force_json=False
        )
        rewritten_query = res.get("content", current_query).strip()
        logger.info(f"🧠 Query Rewritten: [{current_query}] -> [{rewritten_query}]")
        return rewritten_query
    except Exception as e:
        logger.warning(f"⚠️ Query rewrite failed, falling back to original query: {e}")
        # 终极容灾：如果大模型抽风报错，直接拿原句去搜，保证系统不崩
        return current_query
# ----------------- 真实的 QUERY (语义检索) -----------------
async def handle_query(params: Dict[str, Any]) -> Dict[str, Any]:
    raw_query = params.get("query", "")
    top_k = params.get("topK", 5)
    history = params.get("history", [])  # 接收前端/Go网关传来的历史记录

    # 【核心升级 1】：兼容处理单文件 docHash 和多文件 docHashes
    doc_hashes = params.get("docHashes")
    if not doc_hashes:
        single_hash = params.get("docHash", "")
        doc_hashes = [single_hash] if single_hash else []

    # 1. 独立问题重写 (Query Rewriting)：把带有代词的残缺问题翻译成完整句子
    actual_query = await _rewrite_query_with_history(raw_query, history)

    # 2. 将完整的句子进行向量化
    query_emb = await embed_client.get_embedding(actual_query)

    results = []
    # 3. 只有在获取到向量且有目标文件哈希时，才去 pgvector 跨文件检索
    if any(query_emb) and doc_hashes:
        results = await search_similar_chunks(doc_hashes, query_emb, limit=top_k)

    return {"results": results}


# Behavior 和 Config 函数保持你原有的逻辑不变，直接粘贴即可
async def handle_behavior(params: Dict[str, Any]) -> Dict[str, Any]:
    doc_hash = params.get("docHash")
    page = params.get("page", 0)
    event_type = params.get("eventType")
    key = f"{doc_hash}_{page}"
    now = time.time()
    if event_type == "page_view":
        page_dwell_state[key] = now
    elif event_type in ["scroll", "text_select"] and key in page_dwell_state:
        page_dwell_state[key] = now
    return {"recorded": True}


async def _intervention_checker():
    while True:
        await asyncio.sleep(5)
        now = time.time()
        to_delete = []
        for key, start_time in page_dwell_state.items():
            duration = now - start_time
            if duration > settings.INTERVENTION_THRESHOLD:
                doc_hash, page_str = key.split('_')
                send_notification({
                    "type": "intervention", "trigger": "page_dwell_time",
                    "docHash": doc_hash, "page": int(page_str), "duration": round(duration, 1),
                    "message": "我看你在这个页面停留了很久，需要我用费曼技巧帮你拆解一下核心概念吗？"
                })
                to_delete.append(key)
        for k in to_delete:
            del page_dwell_state[k]


async def handle_config(params: Dict[str, Any]) -> Dict[str, Any]:
    if "llm_api_key" in params: settings.LLM_API_KEY = params["llm_api_key"]
    if "llm_model" in params: settings.LLM_MODEL_NAME = params["llm_model"]
    if "interventionThreshold" in params: settings.INTERVENTION_THRESHOLD = int(params["interventionThreshold"])
    return {"updated": True}


async def start_background_tasks():
    asyncio.create_task(_intervention_checker())