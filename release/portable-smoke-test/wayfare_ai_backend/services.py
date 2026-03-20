import asyncio
import hashlib
import json
import time
import uuid
from typing import Any, Dict

from loguru import logger

from config import settings
from context_builder import build_annotate_prompt
from database import (
    insert_cognitive_trace,
    insert_knowledge_chunk,
    search_similar_chunks,
)
from document_parser import _extract_and_chunk_pdf_sync, get_document_metadata_sync
from embedding_provider import embed_client
from llm_provider import llm_client

page_dwell_state: Dict[str, float] = {}


def send_notification(notification_data: dict):
    payload = {"type": "notification", "data": notification_data}
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def _normalize_doc_hashes(params: Dict[str, Any]) -> list[str]:
    doc_hashes = params.get("docHashes")
    if isinstance(doc_hashes, list):
        return [str(item).strip() for item in doc_hashes if str(item).strip()]

    single_hash = str(params.get("docHash", "")).strip()
    return [single_hash] if single_hash else []


def _build_local_fallback_response(
    anno_type: str,
    context: str,
    rag_results: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> dict[str, str]:
    snippet = " ".join(str(context or "").split())
    snippet = snippet[:220] if snippet else "当前问题"
    knowledge_point = str(
        metadata.get("documentName")
        or metadata.get("knowledgeBaseName")
        or "当前材料"
    ).strip()

    if rag_results:
        top_page = rag_results[0].get("page", 0)
        knowledge_point = f"{knowledge_point} · 第 {top_page} 页"

    if anno_type == "summary":
        content = (
            f"我先给你一个稳定的中文总结：这段内容主要围绕“{knowledge_point}”展开。\n"
            f"1. 当前线索：{snippet}\n"
            "2. 建议继续结合上下文确认定义、条件和例外，再决定是否整理成复习提纲。"
        )
    elif anno_type == "ask":
        content = (
            f"基于当前可用材料，我的直接回答是：你的问题需要回到“{knowledge_point}”对应内容里核对。\n"
            f"当前线索：{snippet}\n"
            "如果你继续追问，我会优先围绕当前知识库和这份材料继续拆解。"
        )
    else:
        content = (
            f"我先给你一个保守解释：这段内容聚焦于“{knowledge_point}”。\n"
            f"原文线索：{snippet}\n"
            "理解时建议先确认它在当前章节里的定义，再判断它和上下游概念的关系。"
        )

    return {
        "knowledge_point": knowledge_point,
        "frequency": "本地回退",
        "content": content,
    }


async def _background_parse(path: str, doc_hash: str):
    logger.info(f"Starting background parse for {doc_hash} ({path})")
    try:
        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(None, _extract_and_chunk_pdf_sync, path)
        logger.info(f"Extracted {len(chunks)} chunks from {path}")

        success_count = 0
        for chunk in chunks:
            embedding = await embed_client.get_embedding(chunk["text"])
            if embedding and any(embedding):
                await insert_knowledge_chunk(
                    doc_hash=doc_hash,
                    page=chunk["page"],
                    content=chunk["text"],
                    kp="",
                    freq="0",
                    bbox=chunk["bbox"],
                    embedding=embedding,
                )
                success_count += 1

        send_notification(
            {
                "type": "parse_completed",
                "docHash": doc_hash,
                "segmentCount": success_count,
                "status": "completed",
            }
        )
        logger.info(f"Parse completed for {doc_hash}, stored {success_count} chunks.")
    except Exception as exc:
        logger.error(f"Parse failed for {doc_hash}: {exc}")
        send_notification(
            {
                "type": "parse_failed",
                "docHash": doc_hash,
                "error": str(exc),
            }
        )


async def handle_parse(params: Dict[str, Any]) -> Dict[str, Any]:
    path = params.get("path")
    if not path:
        raise ValueError("path is required for parse")

    doc_hash = hashlib.md5(path.encode("utf-8")).hexdigest()
    metadata = get_document_metadata_sync(path)
    asyncio.create_task(_background_parse(path, doc_hash))
    return {
        "docHash": doc_hash,
        "status": "processing",
        "pageCount": metadata.get("pageCount", 0),
    }


async def handle_annotate(params: Dict[str, Any]) -> Dict[str, Any]:
    anno_type = params.get("type", "explanation")
    context = str(params.get("context", "") or "").strip()
    history = params.get("history", []) or []
    metadata = params.get("meta", {}) or {}
    global_profile = str(params.get("globalProfile", "") or "").strip()
    knowledge_base_profile = str(params.get("knowledgeBaseProfile", "") or "").strip()
    response_language = str(params.get("responseLanguage", "简体中文") or "简体中文").strip()
    doc_hashes = _normalize_doc_hashes(params)

    query_embedding = await embed_client.get_embedding(context) if context else []
    rag_results: list[dict[str, Any]] = []
    if doc_hashes and query_embedding and any(query_embedding):
        rag_results = await search_similar_chunks(doc_hashes, query_embedding, limit=3)

    system_prompt, user_prompt = build_annotate_prompt(
        anno_type,
        context,
        rag_results,
        metadata,
        global_profile=global_profile,
        knowledge_base_profile=knowledge_base_profile,
        response_language=response_language,
    )
    annotation_id = f"anno_{uuid.uuid4().hex[:8]}"

    try:
        response = await llm_client.call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            history=history,
            force_json=True,
        )
        content = str(response.get("content", "") or "").strip()
        knowledge_point = str(response.get("knowledge_point", "") or "").strip() or "当前材料"
        frequency = str(response.get("frequency", "") or "").strip() or "未发现"
        if not content:
            raise ValueError("LLM returned empty content")
    except Exception as exc:
        logger.warning(f"LLM annotate fallback triggered: {exc}")
        response = _build_local_fallback_response(anno_type, context, rag_results, metadata)
        content = response["content"]
        knowledge_point = response["knowledge_point"]
        frequency = response["frequency"]

    await insert_cognitive_trace(
        "default_user",
        "mock_uuid_no_db",
        f"annotate_{anno_type}",
        f"[{knowledge_point}] {content}",
    )

    return {
        "annotationId": annotation_id,
        "type": anno_type,
        "knowledge_point": knowledge_point,
        "frequency": frequency,
        "content": content,
    }


async def _rewrite_query_with_history(current_query: str, history: list) -> str:
    if not history:
        return current_query

    system_prompt = (
        "你是检索查询重写助手。"
        "请根据多轮对话，把当前问题补全成一个独立、完整的检索句子。"
        "只返回重写后的句子，不要解释。"
    )

    try:
        response = await llm_client.call_llm(
            prompt=f"当前问题：{current_query}",
            system_prompt=system_prompt,
            history=history,
            force_json=False,
        )
        rewritten_query = response.get("content", current_query).strip()
        return rewritten_query or current_query
    except Exception as exc:
        logger.warning(f"Query rewrite fallback to original query: {exc}")
        return current_query


async def handle_query(params: Dict[str, Any]) -> Dict[str, Any]:
    raw_query = str(params.get("query", "") or "").strip()
    top_k = int(params.get("topK", 5) or 5)
    history = params.get("history", []) or []
    doc_hashes = _normalize_doc_hashes(params)

    actual_query = await _rewrite_query_with_history(raw_query, history)
    query_embedding = await embed_client.get_embedding(actual_query) if actual_query else []

    results = []
    if doc_hashes and query_embedding and any(query_embedding):
        results = await search_similar_chunks(doc_hashes, query_embedding, limit=top_k)

    return {"results": results}


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
                doc_hash, page_str = key.split("_")
                send_notification(
                    {
                        "type": "intervention",
                        "trigger": "page_dwell_time",
                        "docHash": doc_hash,
                        "page": int(page_str),
                        "duration": round(duration, 1),
                        "message": "我注意到你在这一页停留得比较久，需要我帮你快速解释当前概念吗？",
                    }
                )
                to_delete.append(key)
        for key in to_delete:
            del page_dwell_state[key]


async def handle_config(params: Dict[str, Any]) -> Dict[str, Any]:
    if "llm_api_key" in params:
        settings.LLM_API_KEY = params["llm_api_key"]
    if "llm_model" in params:
        settings.LLM_MODEL_NAME = params["llm_model"]
    if "interventionThreshold" in params:
        settings.INTERVENTION_THRESHOLD = int(params["interventionThreshold"])
    return {"updated": True}


async def start_background_tasks():
    asyncio.create_task(_intervention_checker())
