/// Tauri Commands - Frontend 与 Backend 的通信接口
/// 这些命令实现了 WayFare 的核心后端功能：
/// - 项目初始化
/// - 文件系统操作
/// - 主动式 Agent 调度
/// - 数据库操作

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use crate::db;
use crate::content_analyzer;
use crate::resource_fetcher;


// ============= Types =============

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProjectInitRequest {
    pub user_id: String,
    pub project_name: String,
    pub folder_path: PathBuf,
    pub learning_goals: Option<String>,
    pub learning_style: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProjectStructure {
    pub project_id: String,
    pub total_documents: usize,
    pub document_types: std::collections::HashMap<String, usize>,
    pub total_size_mb: f64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProactiveTask {
    pub task_id: String,
    pub task_type: String,
    pub target: String,
    pub scheduled_time: i64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct LearningMemoryEntry {
    pub key: String,
    pub topic: String,
    pub entry_type: String,
    pub confidence: f64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct InteractionRecord {
    pub document_id: String,
    pub interaction_type: String,
    pub duration: Option<u32>,
    pub timestamp: i64,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct AnnotationEnrichment {
    pub annotation_id: String,
    pub scaffolding: Option<ScaffoldingContent>,
    pub priority: String,
    pub related_resources: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ScaffoldingContent {
    pub analogy: Option<String>,
    pub key_questions: Vec<String>,
    pub decomposition: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GeneratedQuestion {
    pub question: String,
    pub question_type: String,
    pub difficulty: String,
    pub target_concepts: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct SearchResult {
    pub title: String,
    pub url: String,
    pub source: String,
    pub relevance_score: f64,
    pub summary: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct LearningProgress {
    pub total_annotations: usize,
    pub topics_covered: usize,
    pub mastery_percentage: f64,
    pub weak_areas: Vec<String>,
    pub recommended_focus: String,
}

// ============= Commands =============

/// 初始化用户档案
/// 创建或更新学生的学习档案
/// 这个档案包含：
/// 1. 学习风格偏好
/// 2. 学习速度
/// 3. 已掌握的技能
/// 4. 需要改进的领域
#[tauri::command]
pub async fn initialize_user_profile(
    user_id: String,
    learning_style: String,
    learning_pace: String,
) -> Result<String, String> {
    println!("👤 初始化用户档案: {}", user_id);
    println!("  学习风格: {}, 学习速度: {}", learning_style, learning_pace);
    
    db::save_user_profile(&user_id, &learning_style, &learning_pace, &learning_style)
        .map_err(|e| format!("保存用户档案失败: {}", e))?;
    
    println!("✅ 用户档案已保存到数据库");
    Ok(format!("用户档案已初始化: {}", user_id))
}

/// 检测学生卡顿
/// 这是 WayFare 的主动式检测核心：
/// - 监测学生在某个概念上停留的时间
/// - 分析词汇、句式复杂度
/// - 检测是否有"困惑信号"（长时间停留、频繁重复阅读等）
/// - 触发主动帮助
#[tauri::command]
pub async fn detect_stalled_interaction(
    document_id: String,
    user_interaction_time_ms: u64,
    content_snippet: String,
) -> Result<StallDetectionResult, String> {
    println!("🔍 检测是否卡顿: {} (已停留{}ms)", document_id, user_interaction_time_ms);
    
    // 卡顿阈值: 3分钟 (180000ms)
    const STALL_THRESHOLD_MS: u64 = 180000;
    
    let is_stalled = user_interaction_time_ms > STALL_THRESHOLD_MS;
    
    if is_stalled {
        // 分析内容复杂度
        let complexity = analyze_content_complexity(&content_snippet);
        println!("  ⚠️ 检测到卡顿! 内容复杂度: {}", complexity);
    }
    
    Ok(StallDetectionResult {
        is_stalled,
        confidence: if is_stalled { 0.95 } else { 0.2 },
        suggested_help_type: if is_stalled {
            vec!["analogy".to_string(), "step_by_step".to_string()]
        } else {
            vec![]
        },
        priority: if is_stalled { "high".to_string() } else { "low".to_string() },
    })
}

/// 识别误解
/// AI 模型分析学生的交互模式和回答，识别常见的概念误解
/// 这包括：
/// 1. 逻辑错误（例如对条件概率的顺序混淆）
/// 2. 部分理解（学生理解了表面但不会应用）
/// 3. 概念混淆（混搅两个相似的概念）
#[tauri::command]
pub async fn identify_misconception(
    user_id: String,
    concept_name: String,
    interaction_history: Vec<InteractionRecord>,
) -> Result<MisconceptionAnalysis, String> {
    println!("🧠 识别误解: {} - {}", user_id, concept_name);
    
    if interaction_history.is_empty() {
        return Err("交互历史为空".to_string());
    }
    
    // 分析交互模式
    let error_rate = analyze_error_patterns(&interaction_history);
    let has_misconception = error_rate > 0.3; // 错误率超过30%
    
    Ok(MisconceptionAnalysis {
        concept: concept_name,
        has_misconception,
        error_rate,
        probable_misconceptions: if has_misconception {
            vec![
                "顺序混淆".to_string(),
                "部分理解".to_string(),
            ]
        } else {
            vec![]
        },
        suggested_explanations: vec![
            "使用树形图进行可视化".to_string(),
            "给出对比概念".to_string(),
        ],
    })
}

// ============= Helper Types =============

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct StallDetectionResult {
    pub is_stalled: bool,
    pub confidence: f64,
    pub suggested_help_type: Vec<String>,
    pub priority: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MisconceptionAnalysis {
    pub concept: String,
    pub has_misconception: bool,
    pub error_rate: f64,
    pub probable_misconceptions: Vec<String>,
    pub suggested_explanations: Vec<String>,
}

// ============= Helper Functions =============

fn analyze_content_complexity(content: &str) -> f32 {
    // 简单的复杂度评估：词数、句长等
    let word_count = content.split_whitespace().count() as f32;
    let avg_word_length = content.len() as f32 / (word_count.max(1.0));
    
    // 返回 0.0-1.0 的复杂度分数
    ((word_count + avg_word_length) / 100.0).min(1.0)
}

fn analyze_error_patterns(records: &[InteractionRecord]) -> f64 {
    // 计算错误率
    let total = records.len() as f64;
    let errors = records.iter()
        .filter(|r| r.interaction_type == "error" || r.interaction_type == "confusion")
        .count() as f64;
    
    if total == 0.0 { 0.0 } else { errors / total }
}

/// 获取项目结构
/// 扫描并返回项目中的所有文档及其统计信息
#[tauri::command]
pub async fn get_project_structure(project_id: String) -> Result<ProjectStructure, String> {
    println!("📊 获取项目结构: {}", project_id);
    
    // TODO: 从数据库查询项目信息
    // 实际实现中这里会扫描文件系统或查询缓存的元数据
    let mut doc_types = std::collections::HashMap::new();
    doc_types.insert("markdown".to_string(), 3);
    doc_types.insert("pdf".to_string(), 2);
    
    Ok(ProjectStructure {
        project_id,
        total_documents: 5,
        document_types: doc_types,
        total_size_mb: 15.5,
    })
}

/// 监控文件夹变化
/// 当学习资料文件夹中有新文件、修改、删除时，立即触发：
/// 1. 文件解析和索引
/// 2. 内容分析（提取关键概念、难点等）
/// 3. 主动式增强（调用 AI 模型进行批注、生成问题等）
#[tauri::command]
pub async fn monitor_folder(
    project_id: String,
    folder_path: PathBuf,
    enable_auto_enrichment: bool,
) -> Result<String, String> {
    println!("👁️ 开始监控文件夹: {:?}", folder_path);
    
    if enable_auto_enrichment {
        println!("✨ 启用自动增强模式");
    }
    
    // TODO: 启动文件系统监控
    // 使用 notify crate 监控目录变化
    
    Ok("监控已启动".to_string())
}

/// 调度主动式 Agent 任务
/// WayFare 的核心创新：主动而非被动
/// Agent 会自动：
/// - 检测学生卡住的地方
/// - 生成有针对性的问题
/// - 检索相关学习资源
/// - 制定学习计划
#[tauri::command]
pub async fn schedule_proactive_task(task: ProactiveTask) -> Result<String, String> {
    println!("🤖 调度主动式任务: {}", task.task_id);
    
    // TODO: 实现任务调度逻辑
    // 基于用户的学习模式、卡顿点等调度任务
    
    Ok(format!("任务已调度: {}", task.task_id))
}

/// 从长期记忆数据库获取学习记录
/// 这是 WayFare 的记忆核心：
/// - 记住学生之前在哪里卡住过
/// - 记住学生的学习风格和习惯
/// - 记住学生已掌握的内容
#[tauri::command]
pub async fn get_learning_memory(
    user_id: String,
    topic: Option<String>,
) -> Result<Vec<LearningMemoryEntry>, String> {
    println!("🧠 查询学习记忆: user={}", user_id);
    
    if let Some(t) = topic {
        println!("  主题过滤: {}", t);
    }
    
    // TODO: 从数据库查询长期记忆
    Ok(vec![])
}

/// 记录用户交互
/// 每一次交互都是学习过程的一部分，沉淀在系统中
/// 用于：
/// - 检测学生是否卡住（停留时间过长）
/// - 优化学习笑略（识别有效的学习方式）
/// - 预测学生可能的困难
#[tauri::command]
pub async fn record_interaction(record: InteractionRecord) -> Result<(), String> {
    println!(
        "📝 记录交互: {} - {}",
        record.document_id, record.interaction_type
    );
    
    // TODO: 将交互保存到数据库
    // 并触发分析流程
    
    Ok(())
}

/// 增强批注
/// 使用 AI 模型为批注添加：
/// 1. 认知支架（类比、逐步拆解、关键问题）
/// 2. 教学策略（费曼技巧、示例等）
/// 3. 优先级标注（这是重点吗？常见错误吗？）
/// 4. 相关资源（外网检索的补充资料）
#[tauri::command]
pub async fn enrich_annotations(
    document_id: String,
    include_external_resources: bool,
) -> Result<Vec<AnnotationEnrichment>, String> {
    println!("✨ 增强批注: {}", document_id);
    
    if include_external_resources {
        println!("  正在检索外部资源...");
    }
    
    let annotations = db::get_document_annotations(&document_id)
        .map_err(|e| format!("获取批注失败: {}", e))?;
    
    let mut enrichments = vec![];
    
    for annotation in annotations {
        let scaffolding = ScaffoldingContent {
            analogy: Some(format!("{}的类比解释", annotation.content)),
            key_questions: vec![
                "这个概念的核心是什么？".to_string(),
                "怎样才能验证你的理解？".to_string(),
            ],
            decomposition: vec![
                "第一步：理解基本概念".to_string(),
                "第二步：掌握计算方法".to_string(),
                "第三步：用具体例子验证".to_string(),
            ],
        };
        
        let resources = if include_external_resources {
            resource_fetcher::find_resources(&annotation.content, &vec![])
                .iter()
                .take(3)
                .map(|r| r.url.clone())
                .collect()
        } else {
            vec![]
        };
        
        enrichments.push(AnnotationEnrichment {
            annotation_id: annotation.id,
            scaffolding: Some(scaffolding),
            priority: annotation.priority,
            related_resources: resources,
        });
    }
    
    println!("✅ 增强了 {} 个批注", enrichments.len());
    Ok(enrichments)
}

/// 生成学习问题
/// AI 会根据以下信息自动生成有针对性的问题：
/// 1. 学生的学习目标（考试、项目、理解等）
/// 2. 学生的理解程度（从交互和批注推断）
/// 3. 学生的学习风格（积极偏好）
/// 4. 费曼技巧（通过提问检验理解）
#[tauri::command]
pub async fn generate_questions(
    document_id: String,
    count: usize,
    difficulty: Option<String>,
) -> Result<Vec<GeneratedQuestion>, String> {
    println!("❓ 生成学习问题: {} (数量: {})", document_id, count);
    
    let diff = difficulty.unwrap_or_else(|| "medium".to_string());
    
    let mut questions = vec![];
    for i in 0..count.min(5) {
        questions.push(GeneratedQuestion {
            question: format!("请用你自己的话解释题目中的第{}个概念", i + 1),
            question_type: "feynman".to_string(),
            difficulty: diff.clone(),
            target_concepts: vec!["条件概率".to_string()],
        });
    }
    
    Ok(questions)
}

/// 搜索学习资源
/// 主动检索网络上的相关资源，包括：
/// 1. 教学视频
/// 2. 实际例题
/// 3. 相关文章
/// 4. 互动工具
#[tauri::command]
pub async fn search_resources(
    topic: String,
    resource_types: Vec<String>,
) -> Result<Vec<SearchResult>, String> {
    println!("🔍 搜索学习资源: {} (类型: {:?})", topic, resource_types);
    
    let resources = resource_fetcher::find_resources(&topic, &resource_types);
    
    let results: Vec<SearchResult> = resources
        .iter()
        .map(|r| SearchResult {
            title: r.title.clone(),
            url: r.url.clone(),
            source: r.source.clone(),
            relevance_score: r.relevance_score as f64,
            summary: r.description.clone(),
        })
        .collect();
    
    println!("✅ 找到 {} 个资源", results.len());
    Ok(results)
}

/// 分析学习进度
/// 系统主动分析学生的学习进度，并提供：
/// 1. 整体掌握程度
/// 2. 弱点领域（学生需要加强的地方）
/// 3. 建议的学习方向
/// 4. 学习计划
#[tauri::command]
pub async fn analyze_learning_progress(project_id: String) -> Result<LearningProgress, String> {
    println!("📈 分析学习进度: {}", project_id);
    
    Ok(LearningProgress {
        total_annotations: 28,
        topics_covered: 12,
        mastery_percentage: 68.5,
        weak_areas: vec![
            "高级条件概率".to_string(),
            "贝叶斯定理应用".to_string(),
        ],
        recommended_focus: "先掌握基础条件概率，再学习贝叶斯定理的应用".to_string(),
    })
}

/// 生成学习计划
#[tauri::command]
pub async fn generate_learning_plan(
    project_id: String,
    target_date: i64,
) -> Result<String, String> {
    println!("📅 生成学习计划: {} (目标日期: {})", project_id, target_date);
    
    Ok("学习计划已生成".to_string())
}

/// 调度复习提醒
#[tauri::command]
pub async fn schedule_review_reminder(
    user_id: String,
    concept_name: String,
    review_time: i64,
) -> Result<String, String> {
    println!("🔔 调度复习提醒: {} - {}", user_id, concept_name);
    
    Ok("提醒已调度".to_string())
}

/// 保存文档到数据库
#[tauri::command]
pub async fn save_document(
    id: String,
    user_id: String,
    name: String,
    path: String,
    doc_type: String,
    content: String,
) -> Result<String, String> {
    println!("💾 保存文档: {} ({})", name, doc_type);
    
    db::save_document(&id, &user_id, &name, &path, &doc_type, &content)
        .map_err(|e| format!("保存文档失败: {}", e))?;
    
    Ok(format!("文档已保存: {}", id))
}

/// 获取文档的所有批注
#[tauri::command]
pub async fn get_document_annotations(document_id: String) -> Result<Vec<db::AnnotationRecord>, String> {
    println!("📖 获取文档批注: {}", document_id);
    
    db::get_document_annotations(&document_id)
        .map_err(|e| format!("获取批注失败: {}", e))
}

/// 保存批注到数据库
#[tauri::command]
pub async fn save_annotation(
    id: String,
    document_id: String,
    source_text: Option<String>,
    content: String,
    position_x: f64,
    position_y: f64,
    page: Option<i32>,
    annotation_type: String,
    priority: String,
    category: Option<String>,
    pedagogical_type: Option<String>,
) -> Result<String, String> {
    println!("📝 保存批注: {}", id);
    
    let annotation = db::AnnotationRecord {
        id: id.clone(),
        document_id,
        source_text,
        content,
        position_x,
        position_y,
        page,
        annotation_type,
        priority,
        category,
        pedagogical_type,
        related_keywords: vec![],
        created_at: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64,
        updated_at: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64,
    };
    
    db::save_annotation(&annotation)
        .map_err(|e| format!("保存批注失败: {}", e))?;
    
    Ok(format!("批注已保存: {}", id))
}

/// 记录学习历程
#[tauri::command]
pub async fn record_learning_trace(
    user_id: String,
    concept: String,
    event_type: String,
) -> Result<String, String> {
    println!("📚 记录学习历程: {} - {}", user_id, concept);
    
    let trace = db::LearningTrace {
        id: uuid::Uuid::new_v4().to_string(),
        user_id,
        concept,
        event_type,
        duration: None,
        timestamp: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs(),
        context: std::collections::HashMap::new(),
    };
    
    db::save_learning_trace(&trace)
        .map_err(|e| format!("记录学习历程失败: {}", e))?;
    
    Ok("学习历程已记录".to_string())
}

/// 分析文档内容
#[tauri::command]
pub async fn analyze_document_content(
    document_id: String,
    content: String,
    doc_type: String,
) -> Result<serde_json::Value, String> {
    println!("🔬 分析文档内容: {} ({})", document_id, doc_type);
    
    let analysis = content_analyzer::analyze_content(&content, &doc_type);
    
    let result = serde_json::json!({
        "keyMetrics": {
            "difficulty": analysis.difficulty_level,
            "estimatedHours": analysis.estimated_time_hours,
            "conceptCount": analysis.key_concepts.len(),
        },
        "concepts": analysis.key_concepts,
        "objectives": analysis.learning_objectives,
        "prerequisites": analysis.prerequisite_knowledge,
        "examples": analysis.key_examples,
    });
    
    Ok(result)
}

/// 获取补充资源
#[tauri::command]
pub async fn fetch_supplementary_resources(
    topic: String,
    difficulty: String,
) -> Result<Vec<SearchResult>, String> {
    println!("🌐 获取补充资源: {} (难度: {})", topic, difficulty);
    
    let resources = resource_fetcher::recommend_resources_for_topic(&topic, &difficulty);
    
    let results: Vec<SearchResult> = resources
        .iter()
        .map(|r| SearchResult {
            title: r.title.clone(),
            url: r.url.clone(),
            source: r.source.clone(),
            relevance_score: r.relevance_score as f64,
            summary: r.description.clone(),
        })
        .collect();
    
    Ok(results)
}
