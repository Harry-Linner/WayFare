/// Tauri Commands - 前端/Tauri中枢与后端API的通信接口
/// 
/// 职责划分：
/// - 前端通过 invoke 调用这些命令 → Tauri 中枢处理 → 转发至后端 API
/// - 负责人 A 需要实现：文件监控、交互上报、API 转发
/// - 后端部门负责：卡顿检测、批注增强、资源查询等业务逻辑

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::State;
use crate::agent_scheduler::AgentScheduler;

// ============= 数据结构定义 =============

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProjectInitRequest {
    pub user_id: String,
    pub project_name: String,
    pub folder_path: PathBuf,
    pub learning_goal: String,
    pub target_date: Option<u64>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ProjectInitResponse {
    pub project_id: String,
    pub status: String,
    pub message: String,
}

/// 前端上报的交互记录
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct InteractionData {
    #[serde(rename = "type")]
    pub interaction_type: String,
    pub timestamp: u64,
    pub document_id: Option<String>,
    pub page_number: Option<u32>,
    pub duration: Option<u32>,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ReportInteractionsRequest {
    pub interactions: Vec<InteractionData>,
    pub batch_id: String,
    pub document_id: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ReportInteractionsResponse {
    pub status: String,
    pub batch_id: String,
    pub processed_count: usize,
}

/// 卡顿检测请求 - 由前端在用户长时间停留时触发
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CheckConfusionRequest {
    pub document_id: String,
    pub page_number: Option<u32>,
    pub time_elapsed_sec: u32,
    pub user_id: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CheckConfusionResponse {
    pub is_confused: bool,
    pub confidence: f64,
    pub suggestions: Vec<String>,
}

/// 批注增强请求 - 由前端或后台任务触发
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EnrichAnnotationRequest {
    pub annotation_id: String,
    pub source_text: String,
    pub document_type: String, // 'pdf' or 'markdown'
    pub page_number: Option<u32>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct EnrichAnnotationResponse {
    pub annotation_id: String,
    pub scaffolding: Option<serde_json::Value>,
    pub priority: String,
}

/// 获取补充资源
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FetchResourcesRequest {
    pub topic: String,
    pub document_id: String,
    pub learning_style: Option<String>, // 'visual', 'auditory', etc.
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FetchResourcesResponse {
    pub resources: Vec<ResourceItem>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ResourceItem {
    pub id: String,
    pub title: String,
    pub url: String,
    pub resource_type: String,
    pub difficulty: String,
}

// ============= Tauri 命令实现 =============

/// 1. 初始化项目监控
/// 
/// 前端流程：
/// 1. 用户完成项目设置向导
/// 2. 前端调用 invoke('start_project_monitoring', {...})
/// 3. Tauri 启动文件监控
/// 
/// Tauri 职责：
/// - 验证文件夹路径
/// - 启动 file_monitor.rs 的监控
/// - 注册项目到 agent_scheduler
#[tauri::command]
pub async fn start_project_monitoring(
    user_id: String,
    project_id: String,
    folder_path: String,
    scheduler: State<'_, AgentScheduler>,
) -> Result<ProjectInitResponse, String> {
    println!("📁 Tauri: 初始化项目监控");
    println!("   项目 ID: {}", project_id);
    println!("   文件夹: {}", folder_path);

    // 验证文件夹存在
    let path = PathBuf::from(&folder_path);
    if !path.exists() {
        return Err(format!("文件夹不存在: {}", folder_path));
    }

    // 添加到 Agent 调度器
    scheduler.register_project(&project_id, &folder_path);

    Ok(ProjectInitResponse {
        project_id,
        status: "initialized".to_string(),
        message: "项目监控已启动".to_string(),
    })
}

/// 2. 报告前端交互
/// 
/// 由 useInteractionMonitor hook 定期调用
/// 前端负责：收集交互数据，批量上报
/// Tauri 负责：接收、验证、转发给后端 API
/// 后端负责：存储、分析、检测卡顿模式
#[tauri::command]
pub async fn report_interactions(
    request: ReportInteractionsRequest,
) -> Result<ReportInteractionsResponse, String> {
    println!("📊 Tauri: 接收交互批次 {}", request.batch_id);
    println!("   交互数量: {}", request.interactions.len());

    // TODO: 职责边界 - 后端部门实现
    // 这里应该调用后端 API: POST /api/interactions/record
    // 
    // let response = call_backend_api("/api/interactions/record", request).await?;
    // return Ok(response);

    // 临时响应（开发用）
    Ok(ReportInteractionsResponse {
        status: "pending".to_string(),
        batch_id: request.batch_id,
        processed_count: request.interactions.len(),
    })
}

/// 3. 检测用户卡顿
/// 
/// 场景：用户在某个页面停留超过 3 分钟
/// 前端职责：
/// - useInteractionMonitor 监听停留时长
/// - 超过阈值时调用此命令
/// 
/// Tauri 职责：
/// - 调用后端 API 进行卡顿检测
/// - 接收检测结果和建议
/// - 通过事件推送给前端
/// 
/// 后端职责：
/// - 分析卡顿原因（内容难度、用户背景等）
/// - 生成帮助建议
#[tauri::command]
pub async fn check_confusion(
    document_id: String,
    page_number: Option<u32>,
    time_elapsed_sec: u32,
) -> Result<CheckConfusionResponse, String> {
    println!("⚠️ Tauri: 检测卡顿");
    println!("   文档: {}, 页数: {:?}", document_id, page_number);
    println!("   停留时间: {} 秒", time_elapsed_sec);

    // 只有停留超过 180 秒才触发检测
    if time_elapsed_sec < 180 {
        return Ok(CheckConfusionResponse {
            is_confused: false,
            confidence: 0.0,
            suggestions: vec![],
        });
    }

    // TODO: 职责边界 - 后端部门实现
    // let request = CheckConfusionRequest { document_id, page_number, time_elapsed_sec, user_id: None };
    // let response = call_backend_api("/api/agent/detect-confusion", request).await?;
    
    // 后端返回后，由 Tauri 通过事件推送给前端
    // emit_to_frontend("agent_proactive_message", response).await;

    Ok(CheckConfusionResponse {
        is_confused: true,
        confidence: 0.85,
        suggestions: vec![
            "你在这个地方停留了很久，是不是卡住了？".to_string(),
        ],
    })
}

/// 4. 获取补充资源
/// 
/// 通过 Agent 的主动推荐或用户请求触发
/// 前端 → Tauri → 后端知识库 → 资源列表 → 前端
#[tauri::command]
pub async fn fetch_resources(
    topic: String,
    document_id: String,
    learning_style: Option<String>,
) -> Result<FetchResourcesResponse, String> {
    println!("🔍 Tauri: 查询补充资源");
    println!("   主题: {}", topic);
    println!("   学习风格: {:?}", learning_style);

    // TODO: 职责边界 - 后端部门实现
    // let request = FetchResourcesRequest { topic, document_id, learning_style };
    // let response = call_backend_api("/api/resources/fetch-supplementary", request).await?;

    Ok(FetchResourcesResponse {
        resources: vec![],
    })
}

/// 5. 请求批注增强
/// 
/// 当打开文档或手动请求时触发
/// Tauri 调用后端 API，由模型部门处理核心增强逻辑
#[tauri::command]
pub async fn enrich_annotation(
    annotation_id: String,
    source_text: String,
    document_type: String,
    page_number: Option<u32>,
) -> Result<EnrichAnnotationResponse, String> {
    println!("✨ Tauri: 请求批注增强");
    println!("   批注 ID: {}", annotation_id);
    println!("   文本: {}...", &source_text.chars().take(50).collect::<String>());

    // TODO: 职责边界 - 后端/模型部门实现
    // let request = EnrichAnnotationRequest {
    //     annotation_id,
    //     source_text,
    //     document_type,
    //     page_number,
    // };
    // let response = call_backend_api("/api/annotations/enrich", request).await?;

    Ok(EnrichAnnotationResponse {
        annotation_id,
        scaffolding: None,
        priority: "medium".to_string(),
    })
}

/// 6. 分析学习进度
/// 
/// 定期由 Agent 调度器调用，汇总统计数据
#[tauri::command]
pub async fn analyze_learning_progress(
    project_id: String,
) -> Result<serde_json::Value, String> {
    println!("📈 Tauri: 分析学习进度");
    println!("   项目: {}", project_id);

    // TODO: 职责边界 - 后端部门实现统计分析
    // 这里应该查询已有数据，计算进度指标

    Ok(serde_json::json!({
        "status": "pending",
        "project_id": project_id
    }))
}

/// 7. 识别常见错误
/// 
/// 当检测到用户多次在同一个地方失手时触发
#[tauri::command]
pub async fn identify_misconception(
    document_id: String,
    topic: String,
    error_count: usize,
) -> Result<serde_json::Value, String> {
    println!("🔍 Tauri: 识别常见错误");
    println!("   文档: {}, 主题: {}", document_id, topic);
    println!("   错误次数: {}", error_count);

    // TODO: 职责边界 - 后端/模型部门实现
    // let response = call_backend_api("/api/learning/detect-misconception", {...}).await?;

    Ok(serde_json::json!({
        "status": "pending"
    }))
}

/// 8. 保存文档
/// 
/// Markdown 编辑器保存时调用
#[tauri::command]
pub async fn save_document(
    document_id: String,
    content: String,
    document_type: String, // 'pdf' or 'markdown'
) -> Result<serde_json::Value, String> {
    println!("💾 Tauri: 保存文档");
    println!("   文档 ID: {}, 类型: {}", document_id, document_type);

    // TODO: 职责边界 - 可能由 Tauri 本地存储，或转发给后端
    // 如果是 markdown，保存到文件系统
    // 如果有变化，触发批注重新分析

    Ok(serde_json::json!({
        "status": "saved",
        "document_id": document_id
    }))
}

/// 9. 获取文档批注
/// 
/// 打开文档时调用，获取该文档的所有批注
#[tauri::command]
pub async fn get_document_annotations(
    document_id: String,
) -> Result<serde_json::Value, String> {
    println!("📌 Tauri: 获取文档批注");
    println!("   文档 ID: {}", document_id);

    // TODO: 职责边界 - 后端部门实现存储查询
    // let annotations = call_backend_api("/api/documents/{}/annotations", {...}).await?;

    Ok(serde_json::json!({
        "document_id": document_id,
        "annotations": []
    }))
}

/// 10. 保存批注
/// 
/// 用户添加或修改批注时调用
#[tauri::command]
pub async fn save_annotation(
    annotation_id: String,
    document_id: String,
    content: String,
    position: serde_json::Value,
) -> Result<serde_json::Value, String> {
    println!("⭐ Tauri: 保存批注");
    println!("   批注 ID: {}", annotation_id);

    // TODO: 职责边界 - 后端部门实现持久化
    // let response = call_backend_api("/api/annotations/{}", {...}).await?;

    Ok(serde_json::json!({
        "status": "saved",
        "annotation_id": annotation_id
    }))
}

/// 11. 记录学习痕迹
/// 
/// 用户与批注或资源交互时调用
/// 这用于长期记忆系统
#[tauri::command]
pub async fn record_learning_trace(
    user_id: String,
    trace_type: String, // 'confusion', 'clarification', 'mastery', etc.
    content: String,
    related_annotation_id: Option<String>,
) -> Result<serde_json::Value, String> {
    println!("🧠 Tauri: 记录学习痕迹");
    println!("   用户: {}, 类型: {}", user_id, trace_type);

    // TODO: 职责边界 - 后端部门实现长期记忆存储
    // 这些数据用于后续识别用户的强点和弱点

    Ok(serde_json::json!({
        "status": "recorded"
    }))
}

/// 12. 生成学习计划
/// 
/// 结合用户目标、已有资料、学习风格生成个性化计划
#[tauri::command]
pub async fn generate_learning_plan(
    project_id: String,
    learning_goal: String,
    target_date: Option<u64>,
    available_documents: Vec<String>,
) -> Result<serde_json::Value, String> {
    println!("📋 Tauri: 生成学习计划");
    println!("   项目: {}", project_id);
    println!("   目标: {}", learning_goal);

    // TODO: 职责边界 - 后端部门实现计划生成算法
    // let response = call_backend_api("/api/plans/generate", {...}).await?;

    Ok(serde_json::json!({
        "status": "pending"
    }))
}

// ============= 辅助函数 =============

/// 这是一个占位符，实际实现应该由后端部门完成
/// 用于 Tauri 与后端 API 的 HTTP 通信
/// 
/// 应该：
/// 1. 构造 HTTP 请求
/// 2. 添加认证 token
/// 3. 处理超时和重试
/// 4. 返回序列化后的响应
///
/// async fn call_backend_api<T: Serialize, R: DeserializeOwned>(
///     endpoint: &str,
///     request: T,
/// ) -> Result<R, String> {
///     // TODO: 实现 HTTP 调用
///     todo!("after backend service is ready")
/// }
