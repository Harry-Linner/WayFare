/// SQLite 数据库管理层
/// 处理与 SQLite 数据库的所有交互
/// 包括：用户档案、文档、批注、学习历程、内存记录等

use rusqlite::{params, Connection, Result as SqliteResult};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use lazy_static::lazy_static;

lazy_static! {
    static ref DB_CONNECTION: Mutex<Option<Connection>> = Mutex::new(None);
}

/// 初始化数据库
pub fn init_db(db_path: &str) -> SqliteResult<()> {
    let conn = Connection::open(db_path)?;
    
    // 创建用户档案表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS user_profiles (
            id TEXT PRIMARY KEY,
            learning_style TEXT,
            learning_pace TEXT,
            preferred_explanation_type TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )",
        [],
    )?;

    // 创建文档表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            path TEXT,
            doc_type TEXT,
            content TEXT,
            created_at INTEGER,
            updated_at INTEGER
        )",
        [],
    )?;

    // 创建批注表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS annotations (
            id TEXT PRIMARY KEY,
            document_id TEXT,
            source_text TEXT,
            content TEXT,
            position_x REAL,
            position_y REAL,
            page INTEGER,
            annotation_type TEXT,
            priority TEXT,
            category TEXT,
            pedagogical_type TEXT,
            related_keywords TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )",
        [],
    )?;

    // 创建学习历程表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS learning_traces (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            concept TEXT,
            event_type TEXT,
            duration INTEGER,
            timestamp INTEGER,
            context TEXT
        )",
        [],
    )?;

    // 创建概念记忆表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS concept_memories (
            id TEXT PRIMARY KEY,
            concept_name TEXT UNIQUE,
            mastery_level REAL,
            review_count INTEGER,
            first_learned_at INTEGER,
            last_review_at INTEGER,
            next_review_at INTEGER,
            common_mistakes TEXT,
            effective_explanations TEXT
        )",
        [],
    )?;

    // 创建交互记录表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS interaction_records (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            document_id TEXT,
            interaction_type TEXT,
            duration INTEGER,
            timestamp INTEGER,
            page INTEGER,
            position_x REAL,
            position_y REAL
        )",
        [],
    )?;

    // 创建学习计划表
    conn.execute(
        "CREATE TABLE IF NOT EXISTS learning_plans (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            project_id TEXT,
            target_date INTEGER,
            created_at INTEGER,
            updated_at INTEGER,
            plan_data TEXT
        )",
        [],
    )?;

    // 创建索引以加快查询
    conn.execute("CREATE INDEX IF NOT EXISTS idx_annotations_document ON annotations(document_id)", [])?;
    conn.execute("CREATE INDEX IF NOT EXISTS idx_learning_traces_user ON learning_traces(user_id)", [])?;
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_records_user ON interaction_records(user_id)", [])?;

    println!("✅ 数据库初始化完成");
    
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    *db_conn = Some(conn);
    
    Ok(())
}

/// 保存用户档案
pub fn save_user_profile(
    user_id: &str,
    learning_style: &str,
    learning_pace: &str,
    preferred_explanation_type: &str,
) -> SqliteResult<()> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;
    
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;

    conn.execute(
        "INSERT OR REPLACE INTO user_profiles (id, learning_style, learning_pace, preferred_explanation_type, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![user_id, learning_style, learning_pace, preferred_explanation_type, now, now],
    )?;

    println!("✅ 用户档案已保存: {}", user_id);
    Ok(())
}

/// 获取用户档案
pub fn get_user_profile(user_id: &str) -> SqliteResult<Option<UserProfile>> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;
    
    let mut stmt = conn.prepare(
        "SELECT id, learning_style, learning_pace, preferred_explanation_type, created_at, updated_at
         FROM user_profiles WHERE id = ?1"
    )?;

    let profile = stmt.query_row(params![user_id], |row| {
        Ok(UserProfile {
            id: row.get(0)?,
            learning_style: row.get(1)?,
            learning_pace: row.get(2)?,
            preferred_explanation_type: row.get(3)?,
            created_at: row.get(4)?,
            updated_at: row.get(5)?,
        })
    }).ok();

    Ok(profile)
}

/// 保存文档
pub fn save_document(
    id: &str,
    user_id: &str,
    name: &str,
    path: &str,
    doc_type: &str,
    content: &str,
) -> SqliteResult<()> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;
    
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;

    conn.execute(
        "INSERT OR REPLACE INTO documents (id, user_id, name, path, doc_type, content, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![id, user_id, name, path, doc_type, content, now, now],
    )?;

    println!("✅ 文档已保存: {} ({})", name, id);
    Ok(())
}

/// 保存批注
pub fn save_annotation(annotation: &AnnotationRecord) -> SqliteResult<()> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;
    
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;

    let related_keywords = annotation.related_keywords.join(",");

    conn.execute(
        "INSERT OR REPLACE INTO annotations 
         (id, document_id, source_text, content, position_x, position_y, page, annotation_type, 
          priority, category, pedagogical_type, related_keywords, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14)",
        params![
            annotation.id,
            annotation.document_id,
            annotation.source_text,
            annotation.content,
            annotation.position_x,
            annotation.position_y,
            annotation.page,
            annotation.annotation_type,
            annotation.priority,
            annotation.category,
            annotation.pedagogical_type,
            related_keywords,
            now,
            now
        ],
    )?;

    println!("✅ 批注已保存: {}", annotation.id);
    Ok(())
}

/// 获取文档的所有批注
pub fn get_document_annotations(document_id: &str) -> SqliteResult<Vec<AnnotationRecord>> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;
    
    let mut stmt = conn.prepare(
        "SELECT id, document_id, source_text, content, position_x, position_y, page, 
                annotation_type, priority, category, pedagogical_type, related_keywords, created_at, updated_at
         FROM annotations WHERE document_id = ?1 ORDER BY created_at DESC"
    )?;

    let annotations = stmt.query_map(params![document_id], |row| {
        let keywords_str: String = row.get(11)?;
        Ok(AnnotationRecord {
            id: row.get(0)?,
            document_id: row.get(1)?,
            source_text: row.get(2)?,
            content: row.get(3)?,
            position_x: row.get(4)?,
            position_y: row.get(5)?,
            page: row.get(6)?,
            annotation_type: row.get(7)?,
            priority: row.get(8)?,
            category: row.get(9)?,
            pedagogical_type: row.get(10)?,
            related_keywords: keywords_str.split(',').map(|s| s.to_string()).collect(),
            created_at: row.get(12)?,
            updated_at: row.get(13)?,
        })
    })?.collect::<Result<Vec<_>, _>>()?;

    Ok(annotations)
}

/// 保存学习历程
pub fn save_learning_trace(trace: &LearningTrace) -> SqliteResult<()> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;

    let context = serde_json::to_string(&trace.context).unwrap_or_default();

    conn.execute(
        "INSERT INTO learning_traces (id, user_id, concept, event_type, duration, timestamp, context)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        params![trace.id, trace.user_id, trace.concept, trace.event_type, trace.duration, trace.timestamp, context],
    )?;

    Ok(())
}

/// 批量保存交互记录
pub fn save_interaction_records(records: &[InteractionRecord]) -> SqliteResult<()> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;

    for record in records {
        conn.execute(
            "INSERT INTO interaction_records 
             (id, user_id, document_id, interaction_type, duration, timestamp, page, position_x, position_y)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                record.id,
                record.user_id,
                record.document_id,
                record.interaction_type,
                record.duration,
                record.timestamp,
                record.page,
                record.position_x,
                record.position_y
            ],
        )?;
    }

    Ok(())
}

/// 保存概念理解程度
pub fn save_concept_memory(concept: &ConceptMemory) -> SqliteResult<()> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;

    let mistakes = serde_json::to_string(&concept.common_mistakes).unwrap_or_default();
    let explanations = serde_json::to_string(&concept.effective_explanations).unwrap_or_default();

    conn.execute(
        "INSERT OR REPLACE INTO concept_memories 
         (id, concept_name, mastery_level, review_count, first_learned_at, last_review_at, next_review_at, common_mistakes, effective_explanations)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        params![
            uuid::Uuid::new_v4().to_string(),
            concept.concept_name,
            concept.mastery_level,
            concept.review_count,
            concept.first_learned_at,
            concept.last_review_at,
            concept.next_review_at,
            mistakes,
            explanations
        ],
    )?;

    Ok(())
}

/// 从数据库获取概念理解程度
pub fn get_concept_memory(concept_name: &str) -> SqliteResult<Option<ConceptMemory>> {
    let mut db_conn = DB_CONNECTION.lock().unwrap();
    let conn = db_conn.as_ref().ok_or(rusqlite::Error::QueryReturnedNoRows)?;
    
    let mut stmt = conn.prepare(
        "SELECT concept_name, mastery_level, review_count, first_learned_at, last_review_at, 
                next_review_at, common_mistakes, effective_explanations
         FROM concept_memories WHERE concept_name = ?1"
    )?;

    let concept = stmt.query_row(params![concept_name], |row| {
        let mistakes_str: String = row.get(6)?;
        let explanations_str: String = row.get(7)?;
        
        Ok(ConceptMemory {
            concept_name: row.get(0)?,
            mastery_level: row.get(1)?,
            review_count: row.get(2)?,
            first_learned_at: row.get(3)?,
            last_review_at: row.get(4)?,
            next_review_at: row.get(5)?,
            common_mistakes: serde_json::from_str(&mistakes_str).unwrap_or_default(),
            effective_explanations: serde_json::from_str(&explanations_str).unwrap_or_default(),
        })
    }).ok();

    Ok(concept)
}

// ============= Data Structures =============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserProfile {
    pub id: String,
    pub learning_style: String,
    pub learning_pace: String,
    pub preferred_explanation_type: String,
    pub created_at: i64,
    pub updated_at: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnnotationRecord {
    pub id: String,
    pub document_id: String,
    pub source_text: Option<String>,
    pub content: String,
    pub position_x: f64,
    pub position_y: f64,
    pub page: Option<i32>,
    pub annotation_type: String,
    pub priority: String,
    pub category: Option<String>,
    pub pedagogical_type: Option<String>,
    pub related_keywords: Vec<String>,
    pub created_at: i64,
    pub updated_at: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LearningTrace {
    pub id: String,
    pub user_id: String,
    pub concept: String,
    pub event_type: String,
    pub duration: Option<u32>,
    pub timestamp: u64,
    pub context: std::collections::HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InteractionRecord {
    pub id: String,
    pub user_id: String,
    pub document_id: String,
    pub interaction_type: String,
    pub duration: Option<u32>,
    pub timestamp: u64,
    pub page: Option<i32>,
    pub position_x: Option<f64>,
    pub position_y: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConceptMemory {
    pub concept_name: String,
    pub mastery_level: f64,
    pub review_count: i32,
    pub first_learned_at: u64,
    pub last_review_at: Option<u64>,
    pub next_review_at: Option<u64>,
    pub common_mistakes: Vec<String>,
    pub effective_explanations: Vec<String>,
}
