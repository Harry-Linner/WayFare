/// 主动式 Agent 调度系统
/// 
/// 这是 WayFare 的核心中枢，负责：
/// 1. 监听前端的交互数据
/// 2. 定期轮询待处理任务
/// 3. 调用后端 API 进行复杂分析
/// 4. 主动推送事件给前端
/// 
/// 数据流：
/// 前端交互 → report_interactions → 分析 → 生成任务 → emit_all 推送

use std::time::{SystemTime, UNIX_EPOCH, Duration};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use tauri::AppHandle;
use std::thread;

#[derive(Clone, Debug)]
pub struct AgentTask {
    pub id: String,
    pub task_type: String, // 'confusion_detection', 'resource_fetch', 'plan_generation', etc.
    pub document_id: Option<String>,
    pub annotation_id: Option<String>,
    pub scheduled_time: u64,
    pub priority: i32,
    pub status: String, // 'pending', 'processing', 'completed', 'failed'
    pub payload: serde_json::Value,
}

pub struct AgentScheduler {
    app_handle: AppHandle,
    pending_tasks: Arc<Mutex<Vec<AgentTask>>>,
    completed_tasks: Arc<Mutex<Vec<AgentTask>>>,
    monitored_projects: Arc<Mutex<HashMap<String, String>>>, // project_id -> folder_path
}

impl AgentScheduler {
    pub fn new(app_handle: AppHandle) -> Self {
        AgentScheduler {
            app_handle,
            pending_tasks: Arc::new(Mutex::new(Vec::new())),
            completed_tasks: Arc::new(Mutex::new(Vec::new())),
            monitored_projects: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// 注册需要监控的项目
    pub fn register_project(&self, project_id: &str, folder_path: &str) {
        let mut projects = self.monitored_projects.lock().unwrap();
        projects.insert(project_id.to_string(), folder_path.to_string());
        println!("✅ 已注册项目: {} -> {}", project_id, folder_path);
    }

    /// 添加主动式任务
    pub fn add_task(&self, mut task: AgentTask) {
        println!(
            "➕ 添加任务: {} (类型: {}, 优先级: {})",
            task.id, task.task_type, task.priority
        );

        let mut tasks = self.pending_tasks.lock().unwrap();
        task.status = "pending".to_string();
        task.scheduled_time = current_timestamp();

        tasks.push(task);
        // 按优先级排序（优先级高的在前）
        tasks.sort_by(|a, b| b.priority.cmp(&a.priority));
    }

    /// 处理卡顿检测
    /// 
    /// 场景：用户在某个页面停留超过 3 分钟
    /// Tauri 职责：
    /// - 接收前端的停留时长数据
    /// - 创建检测任务
    /// - 后端分析并推送建议
    pub fn detect_confusion(
        &self,
        document_id: String,
        page_number: u32,
        time_elapsed_sec: u32,
        user_id: String,
    ) {
        // 只有停留超过 180 秒（3 分钟）才认为可能卡顿
        if time_elapsed_sec < 180 {
            return;
        }

        println!(
            "⚠️ 检测到可能的卡顿: 文档 {}, 页面 {}, 停留时间 {} 秒",
            document_id, page_number, time_elapsed_sec
        );

        let task = AgentTask {
            id: format!("task_confusion_{}_{}", document_id, current_timestamp()),
            task_type: "confusion_detection".to_string(),
            document_id: Some(document_id.clone()),
            annotation_id: None,
            scheduled_time: current_timestamp(),
            priority: 10, // 高优先级
            status: "pending".to_string(),
            payload: serde_json::json!({
                "type": "confusion_detected",
                "document_id": document_id,
                "page_number": page_number,
                "time_elapsed": time_elapsed_sec,
                "user_id": user_id,
            }),
        };

        self.add_task(task);
    }

    /// 获取当前待处理任务数
    pub fn get_pending_count(&self) -> usize {
        self.pending_tasks.lock().unwrap().len()
    }

    /// 获取所有待处理任务（用于调试）
    pub fn get_pending_tasks(&self) -> Vec<AgentTask> {
        self.pending_tasks.lock().unwrap().clone()
    }

    /// 执行单个任务
    /// 这里主要是调用后端 API，由后端返回结果
    /// 然后通过事件推送给前端
    async fn execute_task(&self, task: &AgentTask) -> Result<(), String> {
        match task.task_type.as_str() {
            "confusion_detection" => {
                println!(
                    "🔄 执行任务: 卡顿检测 ({})",
                    task.document_id.as_ref().unwrap_or(&"unknown".to_string())
                );

                // TODO: 职责边界 - 后端部门实现
                // Tauri 这里应该调用 HTTP API，向后端发送卡顿检测请求
                // 
                // let backend_response = call_backend_api(
                //     "/api/agent/detect-confusion",
                //     &task.payload
                // ).await?;
                //
                // 然后发送事件给前端
                // self.app_handle.emit_all("agent_proactive_message", backend_response).ok();

                // 为了演示，这里模拟发送推送
                self.app_handle
                    .emit_all(
                        "agent_proactive_message",
                        serde_json::json!({
                            "message_type": "confusion_detected",
                            "suggestion": "你在这个地方停留了很久，需要帮助吗？",
                            "help_content": {
                                "analogy": "这个概念就像...",
                                "key_questions": vec!["为什么这样做？"]
                            }
                        }),
                    )
                    .ok();

                Ok(())
            }
            "resource_fetch" => {
                println!("🔄 执行任务: 资源查询");
                // TODO: 调用后端 API 获取资源
                Ok(())
            }
            "plan_generation" => {
                println!("🔄 执行任务: 学习计划生成");
                // TODO: 调用后端 API 生成计划
                Ok(())
            }
            _ => {
                println!("⚠️ 未知任务类型: {}", task.task_type);
                Ok(())
            }
        }
    }

    /// 执行所有待处理任务
    /// 这个方法在主循环中被定期调用
    pub async fn execute_pending_tasks(&self) -> Result<(), String> {
        let mut tasks = self.pending_tasks.lock().unwrap();

        if tasks.is_empty() {
            return Ok(());
        }

        println!("🎯 执行待处理任务，共 {} 个", tasks.len());

        // 取出所有待处理的任务
        let pending: Vec<AgentTask> = tasks
            .iter_mut()
            .filter(|t| t.status == "pending")
            .cloned()
            .collect();

        // 执行任务
        for mut task in pending {
            match self.execute_task(&task).await {
                Ok(_) => {
                    task.status = "completed".to_string();
                    println!("✅ 任务完成: {}", task.id);
                }
                Err(e) => {
                    task.status = "failed".to_string();
                    println!("❌ 任务失败: {} - {}", task.id, e);
                }
            }

            // 移出待处理列表，添加到已完成列表
            let tasks_mut = &mut *tasks;
            if let Some(pos) = tasks_mut.iter().position(|t| t.id == task.id) {
                tasks_mut.remove(pos);
            }
            self.completed_tasks.lock().unwrap().push(task);
        }

        Ok(())
    }
}

/// 启动 Agent 调度系统的主循环
/// 
/// 这个函数在应用启动时被调用，在独立线程中运行
/// 每 30 秒检查一次是否有待处理任务
pub fn start_agent_scheduler(app_handle: AppHandle) {
    println!("🚀 启动 Agent 调度系统...");

    let scheduler = Arc::new(AgentScheduler::new(app_handle));

    thread::spawn(move || {
        println!("✅ Agent 调度线程已启动，每 30 秒检查一次待处理任务");

        let runtime = tokio::runtime::Runtime::new().expect("Failed to create runtime");

        loop {
            // 每 30 秒检查一次
            thread::sleep(Duration::from_secs(30));

            // 执行待处理任务
            let pending_count = scheduler.get_pending_count();
            if pending_count > 0 {
                println!("⏰ [Agent] 定期检查: 有 {} 个待处理任务", pending_count);

                let scheduler_clone = scheduler.clone();
                runtime.block_on(async {
                    if let Err(e) = scheduler_clone.execute_pending_tasks().await {
                        println!("❌ 任务执行错误: {}", e);
                    }
                });
            }
        }
    });
}

/// 获取当前 Unix 时间戳（毫秒）
fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

// 为了使 AgentScheduler 可以共享跨线程
unsafe impl Send for AgentScheduler {}
unsafe impl Sync for AgentScheduler {}
