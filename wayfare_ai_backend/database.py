import json
import math
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from config import settings

try:
    import asyncpg  # type: ignore
except Exception:  # pragma: no cover - fallback for local MVP mode
    asyncpg = None


db_pool = None

LOCAL_DATA_DIR = Path(__file__).resolve().parent / "data"
LOCAL_CHUNK_STORE_PATH = LOCAL_DATA_DIR / "knowledge_chunks.json"


def _ensure_local_store_dir():
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_local_chunks() -> list[dict[str, Any]]:
    _ensure_local_store_dir()
    if not LOCAL_CHUNK_STORE_PATH.exists():
        return []
    try:
        return json.loads(LOCAL_CHUNK_STORE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"Failed to read local chunk store, using empty fallback: {exc}")
        return []


def _save_local_chunks(chunks: list[dict[str, Any]]):
    _ensure_local_store_dir()
    LOCAL_CHUNK_STORE_PATH.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    if length == 0:
        return 0.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for index in range(length):
        lv = float(left[index])
        rv = float(right[index])
        dot += lv * rv
        left_norm += lv * lv
        right_norm += rv * rv
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


async def init_db_pool():
    global db_pool
    if asyncpg is None:
        logger.warning("asyncpg is unavailable; WayFare AI sidecar will use local JSON retrieval fallback.")
        db_pool = None
        return

    try:
        db_pool = await asyncpg.create_pool(
            dsn=settings.DB_DSN,
            min_size=1,
            max_size=20,
            command_timeout=60,
        )
        logger.info("Database connection pool initialized.")
        await init_tables()
    except Exception as exc:
        logger.warning(f"Database unavailable, falling back to local JSON retrieval store: {exc}")
        db_pool = None


async def close_db_pool():
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed.")


async def init_tables():
    if db_pool is None:
        return

    async with db_pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                doc_hash VARCHAR(255) NOT NULL,
                page INT DEFAULT 0,
                content TEXT NOT NULL,
                knowledge_point VARCHAR(255),
                frequency VARCHAR(50),
                bounding_box JSONB,
                embedding vector(1024),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding
            ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_interactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                chunk_id UUID REFERENCES knowledge_chunks(id),
                interaction_type VARCHAR(50),
                duration_seconds INT DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                preferences JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cognitive_traces (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255),
                chunk_id UUID REFERENCES knowledge_chunks(id),
                trace_type VARCHAR(50),
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_plans (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255),
                doc_hash VARCHAR(255),
                plan_content JSONB,
                deadline TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        logger.info("Database tables and pgvector extension are ready.")


async def insert_knowledge_chunk(
    doc_hash: str,
    page: int,
    content: str,
    kp: str,
    freq: str,
    bbox: dict,
    embedding: list[float],
) -> str:
    if db_pool is None:
        chunks = _load_local_chunks()
        record_id = str(uuid.uuid4())
        chunks.append(
            {
                "id": record_id,
                "doc_hash": doc_hash,
                "page": page,
                "content": content,
                "knowledge_point": kp,
                "frequency": freq,
                "bounding_box": bbox,
                "embedding": embedding,
            }
        )
        _save_local_chunks(chunks)
        return record_id

    query = """
        INSERT INTO knowledge_chunks (doc_hash, page, content, knowledge_point, frequency, bounding_box, embedding)
        VALUES ($1, $2, $3, $4, $5, $6, $7::vector)
        RETURNING id;
    """
    async with db_pool.acquire() as conn:
        record_id = await conn.fetchval(
            query, doc_hash, page, content, kp, freq, json.dumps(bbox), str(embedding)
        )
        return str(record_id)


async def search_similar_chunks(doc_hashes: list[str] | str, embedding: list[float], limit: int = 5) -> list[dict]:
    if isinstance(doc_hashes, str):
        doc_hash_list = [doc_hashes]
    else:
        doc_hash_list = [item for item in doc_hashes if item]

    if not doc_hash_list:
        return []

    if db_pool is None:
        chunks = _load_local_chunks()
        filtered = [chunk for chunk in chunks if chunk.get("doc_hash") in doc_hash_list]
        scored = []
        for chunk in filtered:
            score = _cosine_similarity(chunk.get("embedding", []), embedding)
            scored.append(
                {
                    "segment_id": chunk.get("id", ""),
                    "page": chunk.get("page", 0),
                    "text": chunk.get("content", ""),
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return scored[:limit]

    query = """
        SELECT id::text as segment_id, page, content as text,
               1 - (embedding <=> $2::vector) AS score
        FROM knowledge_chunks
        WHERE doc_hash = ANY($1::text[])
        ORDER BY embedding <=> $2::vector
        LIMIT $3;
    """
    try:
        async with db_pool.acquire() as conn:
            records = await conn.fetch(query, doc_hash_list, str(embedding), limit)
            return [dict(record) for record in records]
    except Exception as exc:
        logger.error(f"search_similar_chunks failed: {exc}")
        return []


async def upsert_user_preference(user_id: str, preferences: dict):
    if db_pool is None:
        return
    query = """
        INSERT INTO users (id, preferences)
        VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE
        SET preferences = users.preferences || EXCLUDED.preferences;
    """
    async with db_pool.acquire() as conn:
        await conn.execute(query, user_id, json.dumps(preferences))


async def get_user_preference(user_id: str) -> dict:
    if db_pool is None:
        return {}
    query = "SELECT preferences FROM users WHERE id = $1;"
    async with db_pool.acquire() as conn:
        value = await conn.fetchval(query, user_id)
        return json.loads(value) if value else {}


async def insert_cognitive_trace(user_id: str, chunk_id: str, trace_type: str, content: str):
    if db_pool is None or chunk_id == "mock_uuid_no_db":
        return
    query = """
        INSERT INTO cognitive_traces (user_id, chunk_id, trace_type, content)
        VALUES ($1, $2::uuid, $3, $4);
    """
    async with db_pool.acquire() as conn:
        await conn.execute(query, user_id, chunk_id, trace_type, content)


async def insert_study_plan(user_id: str, doc_hash: str, plan_content: dict, deadline: str = None):
    if db_pool is None:
        return
    query = """
        INSERT INTO study_plans (user_id, doc_hash, plan_content, deadline)
        VALUES ($1, $2, $3, $4::timestamp with time zone);
    """
    async with db_pool.acquire() as conn:
        await conn.execute(query, user_id, doc_hash, json.dumps(plan_content), deadline)
