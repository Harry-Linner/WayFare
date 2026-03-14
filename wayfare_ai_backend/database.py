import asyncpg
from loguru import logger
import json
from config import settings

# 全局数据库连接池句柄
db_pool: asyncpg.Pool = None

async def init_db_pool():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            dsn=settings.DB_DSN,
            min_size=1,
            max_size=20,
            command_timeout=60,
        )
        logger.info("Database connection pool initialized.")
        await init_tables()
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise

async def close_db_pool():
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed.")

async def init_tables():
    if db_pool is None: return
    async with db_pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        await conn.execute("""
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
            
            CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding 
            ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
            
            CREATE TABLE IF NOT EXISTS user_interactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) NOT NULL,
                chunk_id UUID REFERENCES knowledge_chunks(id),
                interaction_type VARCHAR(50), 
                duration_seconds INT DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                preferences JSONB, 
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS cognitive_traces (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) REFERENCES users(id),
                chunk_id UUID REFERENCES knowledge_chunks(id),
                trace_type VARCHAR(50), 
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS study_plans (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255) REFERENCES users(id),
                doc_hash VARCHAR(255),
                plan_content JSONB,
                deadline TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Database tables and pgvector extension are ready.")

async def insert_knowledge_chunk(doc_hash: str, page: int, content: str, kp: str, freq: str, bbox: dict, embedding: list[float]) -> str:
    query = """
        INSERT INTO knowledge_chunks (doc_hash, page, content, knowledge_point, frequency, bounding_box, embedding)
        VALUES ($1, $2, $3, $4, $5, $6, $7::vector)
        RETURNING id;
    """
    if db_pool is None: return "mock_uuid_no_db"
    async with db_pool.acquire() as conn:
        record_id = await conn.fetchval(query, doc_hash, page, content, kp, freq, json.dumps(bbox), str(embedding))
        return str(record_id)

async def search_similar_chunks(doc_hash: str, embedding: list[float], limit: int = 5) -> list[dict]:
    query = """
        SELECT id::text as segment_id, page, content as text, 
               1 - (embedding <=> $2::vector) AS score 
        FROM knowledge_chunks
        WHERE doc_hash = ANY($1::text[])
        ORDER BY embedding <=> $2::vector
        LIMIT $3;
    """
    if db_pool is None: return []
    async with db_pool.acquire() as conn:
        records = await conn.fetch(query, doc_hash, str(embedding), limit)
        return [dict(r) for r in records]

async def upsert_user_preference(user_id: str, preferences: dict):
    query = """
        INSERT INTO users (id, preferences)
        VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE 
        SET preferences = users.preferences || EXCLUDED.preferences;
    """
    if db_pool is None: return
    async with db_pool.acquire() as conn:
        await conn.execute(query, user_id, json.dumps(preferences))

async def get_user_preference(user_id: str) -> dict:
    query = "SELECT preferences FROM users WHERE id = $1;"
    if db_pool is None: return {}
    async with db_pool.acquire() as conn:
        val = await conn.fetchval(query, user_id)
        return json.loads(val) if val else {}

async def insert_cognitive_trace(user_id: str, chunk_id: str, trace_type: str, content: str):
    query = """
        INSERT INTO cognitive_traces (user_id, chunk_id, trace_type, content)
        VALUES ($1, $2::uuid, $3, $4);
    """
    if db_pool is None or chunk_id == "mock_uuid_no_db": return
    async with db_pool.acquire() as conn:
        await conn.execute(query, user_id, chunk_id, trace_type, content)

async def insert_study_plan(user_id: str, doc_hash: str, plan_content: dict, deadline: str = None):
    query = """
        INSERT INTO study_plans (user_id, doc_hash, plan_content, deadline)
        VALUES ($1, $2, $3, $4::timestamp with time zone);
    """
    if db_pool is None: return
    async with db_pool.acquire() as conn:
        await conn.execute(query, user_id, doc_hash, json.dumps(plan_content), deadline)
