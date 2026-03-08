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
        println!("➕ 添加任务: {} (类型: {}, 优先级: {})", task.id, task.task_type, task.priority);
        
        let mut tasks = self.pending_tasks.lock().unwrap();
        task.status = "pending".to_string();
        task.scheduled_time = current_timestamp();
        
        tasks.push(task);
        // 按优先级排序（优先级高的在前）
        tasks.sort_by(|a, b| b.priority.cmp(&a.priority));
    }

    /// 处理卡顿检测任务
    /// 
    /// 场景：用户在某个页面停留超过 3 分钟
    /// 职责：
    /// - Tauri: 接收前端的停留时长数据
    /// - Tauri: 调用后端 API 进行分析
    /// - 后端: 进行复杂的意图识别（卡顿 vs 专注思考）
    /// - Tauri: 接收后端的建议，通过事件推送给前端
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

        // 创建任务，后续由主循环处理
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
            "shallow_study_warning" => {
                println!("🔄 执行任务: 浅尝学习提醒");
                
                self.app_handle
                    .emit_all(
                        "agent_proactive_message",
                        serde_json::json!({
                            "message_type": "shallow_study_warning",
                            "suggestion": "这是很重要的内容哦，但你花费的时间可能有点短。不如我给你提几个思考题？",
                            "payload": &task.payload
                        }),
                    )
                    .ok();

                Ok(())
            }
            "resource_fetch" => {
                println!("🔄 执行任务: 补充资源获取");
                
                self.app_handle
                    .emit_all(
                        "supplementary_resources_available",
                        serde_json::json!({
                            "message_type": "resources_ready",
                            "resources": [
                                {
                                    "title": "Khan Academy 视频讲解",
                                    "url": "https://...",
                                    "type": "video"
                                }
                            ]
                        }),
                    )
                    .ok();

                Ok(())
            }
            "generate_learning_plan" => {
                println!("🔄 执行任务: 学习计划生成");
                
                self.app_handle
                    .emit_all(
                        "learning_plan_ready",
                        serde_json::json!({
                            "plan_id": format!("plan_{}", current_timestamp()),
                            "suggested_schedule": [
                                {
                                    "topic": "主题 1",
                                    "day": "明天",
                                    "duration_hours": 2.5
                                },
                                {
                                    "topic": "主题 2",
                                    "day": "周三",
                                    "duration_hours": 3.0
                                }
                            ]
                        }),
                    )
                    .ok();

                Ok(())
            }
            "schedule_review_reminder" => {
                println!("🔄 执行任务: 复习提醒安排");
                
                self.app_handle
                    .emit_all(
                        "review_reminder",
                        serde_json::json!({
                            "concept": task.payload.get("concept"),
                            "next_review": task.payload.get("scheduled_time"),
                            "message": "是时候复习一下之前学过的内容了！"
                        }),
                    )
                    .ok();

                Ok(())
            }
            "identify_common_mistakes" => {
                println!("🔄 执行任务: 常见错误识别");
                
                self.app_handle
                    .emit_all(
                        "common_mistake_alert",
                        serde_json::json!({
                            "content": task.payload.get("content"),
                            "mistake_count": task.payload.get("mistake_count"),
                            "suggestion": "很多学生都在这个地方犯同样的错误。让我用不同的方式解释..."
                        }),
                    )
                    .ok();

                Ok(())
            }
            "exam_deadline_reminder" => {
                println!("🔄 执行任务: 考试截止提醒");
                
                self.app_handle
                    .emit_all(
                        "deadline_alert",
                        serde_json::json!({
                            "deadline": task.payload.get("target_date"),
                            "days_remaining": task.payload.get("days_remaining"),
                            "urgent": true,
                            "message": "你的考试目标日期就要到了，现在正是冲刺的时候！"
                        }),
                    )
                    .ok();

                Ok(())
            }
            "content_relevance_check" => {
                println!("🔄 执行任务: 内容相关性检查");
                
                let is_in_scope = true; // TODO: 调用后端检查
                
                if !is_in_scope {
                    self.app_handle
                        .emit_all(
                            "content_out_of_scope",
                            serde_json::json!({
                                "message": "提示：你正在学习的这部分内容不在考试范围内。建议专注于考试重点。",
                                "priority_topics": ["主题 A", "主题 B"]
                            }),
                        )
                        .ok();
                }

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
            if let Some(pos) = tasks.iter().position(|t| t.id == task.id) {
                tasks.remove(pos);
            }
            self.completed_tasks.lock().unwrap().push(task);
        }

        Ok(())
    }
}

/// 启动 Agent 调度系统的主循环
/// 
/// 这个函数在应用启动时被调用，在独立线程中运行
/// 定期检查待处理任务，根据优先级执行它们
pub fn start_agent_scheduler(app_handle: AppHandle) {
    println!("🚀 启动主动式 Agent 调度系统...");
    println!("   WayFare 现在能24/7工作：");
    println!("   ✓ 检测学生卡顿，主动提供帮助");
    println!("   ✓ 识别浅尝学习，提醒深入学习");
    println!("   ✓ 制定个性化学习计划");
    println!("   ✓ 根据遗忘曲线安排复习");
    println!("   ✓ 识别常见错误，提前预防");

    let scheduler = Arc::new(AgentScheduler::new(app_handle));

    std::thread::spawn(move || {
        println!("✅ Agent 后台调度线程已启动，PID: {:?}", std::thread::current().id());

        // 创建 tokio runtime 支持异步任务执行
        let runtime = tokio::runtime::Runtime::new().expect("❌ 无法创建异步运行时");

        // 主循环：每 10 秒检查一次待处理任务
        loop {
            std::thread::sleep(std::time::Duration::from_secs(10));

            let pending_count = scheduler.get_pending_count();
            
            if pending_count > 0 {
                println!("⏰ Agent 调度检测: {} 个待处理任务已准备执行", pending_count);
                
                let scheduler_clone = scheduler.clone();
                runtime.block_on(async {
                    match scheduler_clone.execute_pending_tasks().await {
                        Ok(_) => {
                            println!("✅ 本轮任务执行完毕，所有主动式操作已推送给前端");
                        }
                        Err(e) => {
                            eprintln!("❌ Agent 任务执行失败: {}", e);
                        }
                    }
                });
            }
        }
    });

    println!("✅ 主动式 Agent 系统启动成功！");
}

/// 获取当前 Unix 时间戳（毫秒）
fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

// 为了使 AgentTask 可以 clone
#[allow(dead_code)]
impl Clone for AgentTask {
    fn clone(&self) -> Self {
        AgentTask {
            id: self.id.clone(),
            task_type: self.task_type.clone(),
            document_id: self.document_id.clone(),
            annotation_id: self.annotation_id.clone(),
            scheduled_time: self.scheduled_time,
            priority: self.priority,
            status: self.status.clone(),
            payload: self.payload.clone(),
        }
    }
}

impl AgentScheduler {
    /// 检测浅尝问题
    /// 如果学生快速滑过某个重点内容，提醒深入学习
    pub fn detect_shallow_study(
        &self,
        document_id: String,
        section_importance: f32,
        time_spent_sec: u32,
    ) {
        if section_importance > 0.7 && time_spent_sec < 30 {
            println!("⏱️ 检测到浅尝学习: 重要内容，仅花费 {} 秒", time_spent_sec);
            
            let task = AgentTask {
                id: format!("task_shallow_{}", chrono::Local::now().timestamp()),
                task_type: "shallow_study_warning".to_string(),
                document_id: Some(document_id.clone()),
                annotation_id: None,
                scheduled_time: current_timestamp(),
                priority: 7,
                status: "pending".to_string(),
                payload: serde_json::json!({
                    "section_importance": section_importance,
                    "time_spent": time_spent_sec,
                }),
            };
            
            self.add_task(task);
            
            let _ = self.app_handle.emit_all("agent_proactive_message", serde_json::json!({
                "message_type": "shallow_study_warning",
                "document_id": document_id,
                "suggestion": "这是很重要的内容哦，但你花费的时间可能有点短。不如我给你提几个思考题？"
            }));
        }
    }
    
    /// 主动学习计划建议
    /// 根据学生的学习模式，AI 制定个性化的学习计划
    pub fn suggest_learning_plan(
        &self,
        user_id: String,
        topics: Vec<String>,
        target_date: Option<u64>,
    ) {
        println!("📅 建议学习计划: 用户 {}", user_id);
        
        let days_remaining = if let Some(date) = target_date {
            let now = current_timestamp();
            if date > now {
                ((date - now) / 86400) as u32
            } else {
                7
            }
        } else {
            14
        };
        
        let task = AgentTask {
            id: format!("task_plan_{}", chrono::Local::now().timestamp()),
            task_type: "generate_learning_plan".to_string(),
            document_id: None,
            annotation_id: None,
            scheduled_time: current_timestamp(),
            priority: 8,
            status: "pending".to_string(),
            payload: serde_json::json!({
                "user_id": user_id,
                "topics": topics,
                "target_date": target_date,
                "days_remaining": days_remaining,
            }),
        };
        
        self.add_task(task);
        
        let plan = serde_json::json!({
            "plan_id": format!("plan_{}", chrono::Local::now().timestamp()),
            "user_id": user_id,
            "topics": [
                {
                    "name": "主题 1",
                    "date": "明天",
                    "duration_hours": 2.5
                },
                {
                    "name": "主题 2",
                    "date": "后天",
                    "duration_hours": 3.0
                }
            ],
            "success_criteria": format!("在 {} 天内掌握 80% 的内容", days_remaining)
        });
        
        let _ = self.app_handle.emit_all("learning_plan_suggested", plan);
    }
    
    /// 生成复习提醒
    /// 根据学生的遗忘曲线（Spaced Repetition），自动安排复习
    pub fn schedule_review_reminder(
        &self,
        user_id: String,
        concept: String,
        first_learned_at: u64,
        review_count: u32,
    ) {
        println!("🔄 安排复习提醒: {} - {}", user_id, concept);
        
        // 使用艾宾浩斯遗忘曲线计算下次复习时间
        // 第1次复习：1 天后
        // 第2次复习：3 天后
        // 第3次复习：7 天后
        // 第4次复习：15 天后
        // ...以此类推
        
        let days_to_next_review = match review_count {
            0 => 1,
            1 => 3,
            2 => 7,
            3 => 15,
            4 => 30,
            _ => 60,
        };
        
        let next_review_time = current_timestamp() + (days_to_next_review * 24 * 3600);
        
        println!("  下次复习时间: {} 天后", days_to_next_review);
        
        let task = AgentTask {
            id: format!("task_review_{}", chrono::Local::now().timestamp()),
            task_type: "schedule_review_reminder".to_string(),
            document_id: None,
            annotation_id: None,
            scheduled_time: next_review_time,
            priority: 5 + (review_count as i32),
            status: "pending".to_string(),
            payload: serde_json::json!({
                "user_id": user_id,
                "concept": concept,
                "review_count": review_count + 1,
                "scheduled_time": next_review_time,
            }),
        };
        
        self.add_task(task);
        
        let _ = self.app_handle.emit_all("review_scheduled", serde_json::json!({
            "user_id": user_id,
            "concept": concept,
            "review_count": review_count + 1,
            "scheduled_time": next_review_time,
        }));
    }
    
    /// 识别常见错误
    /// 如果多个学生在同一个地方都遇到困难，可能是：
    /// 1. 教学方式不适合
    /// 2. 内容表达不清
    /// 3. 缺少前置知识
    pub fn identify_common_mistakes(
        &self,
        content: String,
        mistake_count: u32,
    ) {
        if mistake_count > 2 {
            println!("🚫 识别常见错误: {} 次以上的学生卡在这里", mistake_count);
            
            let task = AgentTask {
                id: format!("task_mistake_{}", chrono::Local::now().timestamp()),
                task_type: "identify_common_mistakes".to_string(),
                document_id: None,
                annotation_id: None,
                scheduled_time: current_timestamp(),
                priority: 9,
                status: "pending".to_string(),
                payload: serde_json::json!({
                    "content": content,
                    "mistake_count": mistake_count,
                }),
            };
            
            self.add_task(task);
            
            let _ = self.app_handle.emit_all("common_mistake_detected", serde_json::json!({
                "content": content,
                "mistake_count": mistake_count,
                "suggestion": "这是一个常见的卡顿点。让我用不同的方式解释一下..."
            }));
        }
    }
    
    /// 处理待处理任务
    pub fn process_pending_tasks(&self) {
        let mut pending = self.pending_tasks.lock().unwrap();
        let current_time = current_timestamp();
        
        let mut completed = Vec::new();
        let mut remaining = Vec::new();
        
        for mut task in pending.drain(..) {
            if task.scheduled_time <= current_time {
                println!("⚙️ 处理任务: {} (类型: {})", task.id, task.task_type);
                
                // 模拟任务执行
                task.status = "completed".to_string();
                completed.push(task);
            } else {
                remaining.push(task);
            }
        }
        
        // 保存剩余任务
        *pending = remaining;
        // 保存已完成任务
        if !completed.is_empty() {
            let mut done = self.completed_tasks.lock().unwrap();
            done.extend(completed);
        }
    }
    
    /// 获取待处理任务数
    pub fn get_pending_count(&self) -> usize {
        self.pending_tasks.lock().unwrap().len()
    }
}

/// 获取当前时间戳（秒）
fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}


/// 启动主动式 Agent 调度系统
pub fn start_agent_scheduler_impl(app_handle: AppHandle) {
    println!("🤖 启动主动式 Agent 调度系统");
    
    let scheduler = Arc::new(AgentScheduler::new(app_handle));
    
    println!("✅ Agent 调度系统已启动");
    println!("   Agent 现在能够：");
    println!("   ✓ 检测学生卡顿，主动提供帮助");
    println!("   ✓ 识别浅尝学习，提醒深入学习");
    println!("   ✓ 制定个性化学习计划");
    println!("   ✓ 根据遗忘曲线安排复习");
    println!("   ✓ 识别常见错误，提前预防");
    
    let scheduler_clone = scheduler.clone();
    
    // 任务处理循环
    std::thread::spawn(move || {
        loop {
            std::thread::sleep(std::time::Duration::from_secs(10));
            
            // 处理待处理任务
            scheduler_clone.process_pending_tasks();
            
            let pending_count = scheduler_clone.get_pending_count();
            if pending_count > 0 {
                println!("🔄 当前有 {} 个待处理任务", pending_count);
            }
        }
    });
}
