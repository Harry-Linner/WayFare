/// 文件系统监控服务
/// 这是 WayFare 主动式的基础：
/// - 持续监控学习资料文件夹
/// - 检测新文件、修改、删除
/// - 自动触发内容解析和 AI 增强
/// - 无需用户手动操作

use tauri::AppHandle;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::collections::HashMap;

pub struct FileMonitor {
    app_handle: AppHandle,
    watched_folders: Arc<Mutex<Vec<PathBuf>>>,
    file_timestamps: Arc<Mutex<HashMap<PathBuf, std::time::SystemTime>>>,
}

impl FileMonitor {
    pub fn new(app_handle: AppHandle) -> Self {
        FileMonitor {
            app_handle,
            watched_folders: Arc::new(Mutex::new(Vec::new())),
            file_timestamps: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    /// 添加监控的文件夹
    pub fn add_watched_folder(&self, path: PathBuf) {
        let mut folders = self.watched_folders.lock().unwrap();
        if !folders.contains(&path) {
            folders.push(path);
            println!("✅ 开始监控文件夹: {:?}", path);
        }
    }
    
    /// 移除监控的文件夹
    pub fn remove_watched_folder(&self, path: &PathBuf) {
        let mut folders = self.watched_folders.lock().unwrap();
        folders.retain(|p| p != path);
        println!("❌ 停止监控文件夹: {:?}", path);
    }
    
    /// 扫描文件夹变化
    pub fn scan_folder(&self, folder: &PathBuf) {
        if !folder.exists() {
            println!("⚠️ 文件夹不存在: {:?}", folder);
            return;
        }
        
        let mut timestamps = self.file_timestamps.lock().unwrap();
        
        if let Ok(entries) = std::fs::read_dir(folder) {
            for entry_result in entries {
                if let Ok(entry) = entry_result {
                    let path = entry.path();
                    if path.is_file() {
                        let file_name = path
                            .file_name()
                            .and_then(|n| n.to_str())
                            .unwrap_or("unknown");
                        
                        // 只处理学习资料文件
                        if !self.is_learning_material(file_name) {
                            continue;
                        }
                        
                        let current_time = std::time::SystemTime::now();
                        
                        if let Ok(metadata) = std::fs::metadata(&path) {
                            if let Ok(modified_time) = metadata.modified() {
                                // 检查是否是新文件
                                if !timestamps.contains_key(&path) {
                                    self.handle_new_file_sync(&path);
                                    timestamps.insert(path.clone(), current_time);
                                } else if timestamps[&path] != current_time {
                                    // 文件已修改
                                    if let Ok(duration) = modified_time.elapsed() {
                                        if duration.as_secs() < 10 {
                                            // 10秒内的修改
                                            self.handle_file_modified_sync(&path);
                                            timestamps.insert(path.clone(), current_time);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // 检测已删除的文件
        let mut deleted_files = Vec::new();
        for (path, _) in timestamps.iter() {
            if !path.exists() {
                deleted_files.push(path.clone());
            }
        }
        
        for path in deleted_files {
            self.handle_file_deleted_sync(&path);
            timestamps.remove(&path);
        }
    }
    
    /// 处理新文件检测
    /// 🔥 修复漏洞#2：自动触发后续的分析和标注任务
    fn handle_new_file_sync(&self, file_path: &PathBuf) {
        println!("🆕 检测到新文件: {:?}", file_path);
        
        let file_name = file_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");
        
        // 识别文件类型
        let file_type = if file_name.ends_with(".pdf") {
            "pdf"
        } else if file_name.ends_with(".md") || file_name.ends_with(".markdown") {
            "markdown"
        } else if file_name.ends_with(".txt") {
            "text"
        } else {
            "document"
        };
        
        println!("  文件类型: {}", file_type);
        
        // 解析文件内容
        if let Ok(content) = std::fs::read_to_string(&file_path) {
            let word_count = content.split_whitespace().count();
            println!("  字数: {}", word_count);
        }
        
        // 发送通知给前端
        let _ = self.app_handle.emit_all("file_added", serde_json::json!({
            "file_path": file_path.to_string_lossy(),
            "file_name": file_name,
            "file_type": file_type,
            "timestamp": chrono::Local::now().to_rfc3339(),
        }));
        
        // 🔥 新增：自动触发后续任务
        // 1. 提交内容分析任务
        println!("  ➡️ 提交内容分析任务到 Agent 调度器");
        let _ = self.app_handle.emit_all(
            "trigger_content_analysis",
            serde_json::json!({
                "file_path": file_path.to_string_lossy(),
                "file_type": file_type,
                "priority": 8,
            }),
        );
        
        // 2. 提交补充资源获取任务
        println!("  ➡️ 提交补充资源获取任务");
        let _ = self.app_handle.emit_all(
            "trigger_resource_fetch",
            serde_json::json!({
                "file_name": file_name,
                "priority": 6,
            }),
        );
    }
    
    /// 处理文件修改
    /// 🔥 修复漏洞#7：检测到修改后，重新分析内容并更新批注
    fn handle_file_modified_sync(&self, file_path: &PathBuf) {
        println!("✏️ 检测到文件修改: {:?}", file_path);
        
        let file_name = file_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");
        
        // 识别文件类型
        let file_type = if file_name.ends_with(".pdf") {
            "pdf"
        } else if file_name.ends_with(".md") || file_name.ends_with(".markdown") {
            "markdown"
        } else if file_name.ends_with(".txt") {
            "text"
        } else {
            "document"
        };
        
        // 读取新内容
        if let Ok(content) = std::fs::read_to_string(&file_path) {
            let new_word_count = content.split_whitespace().count();
            println!("  📊 更新内容统计：{}字", new_word_count);
        }
        
        // 发送通知给前端
        let _ = self.app_handle.emit_all("file_modified", serde_json::json!({
            "file_path": file_path.to_string_lossy(),
            "file_name": file_name,
            "file_type": file_type,
            "timestamp": chrono::Local::now().to_rfc3339(),
        }));
        
        // 🔥 新增：自动触发内容重新分析
        // 1. 重新分析内容
        println!("  ➡️ 触发内容重新分析任务");
        let _ = self.app_handle.emit_all(
            "trigger_content_re_analysis",
            serde_json::json!({
                "file_path": file_path.to_string_lossy(),
                "file_type": file_type,
                "priority": 7, // 比新文件优先级低，因为是更新而非新消息
            }),
        );
        
        // 2. 更新批注（删除已过时的，添加新的）
        println!("  ➡️ 触发批注更新任务");
        let _ = self.app_handle.emit_all(
            "trigger_annotation_update",
            serde_json::json!({
                "file_path": file_path.to_string_lossy(),
                "action": "refresh",
            }),
        );
    }
    
    /// 处理文件删除
    fn handle_file_deleted_sync(&self, file_path: &PathBuf) {
        println!("🗑️ 检测到文件删除: {:?}", file_path);
        
        // 发送通知给前端
        let _ = self.app_handle.emit_all("file_deleted", serde_json::json!({
            "file_path": file_path.to_string_lossy(),
            "timestamp": chrono::Local::now().to_rfc3339(),
        }));
    }
    
    /// 判断是否是学习资料文件
    fn is_learning_material(&self, file_name: &str) -> bool {
        file_name.ends_with(".pdf") 
            || file_name.ends_with(".md") 
            || file_name.ends_with(".markdown")
            || file_name.ends_with(".txt")
            || file_name.ends_with(".doc")
            || file_name.ends_with(".docx")
    }
    
    /// 解析 PDF 文件
    fn parse_pdf(&self, path: &PathBuf) -> Option<String> {
        println!("📄 解析 PDF 文件: {:?}", path);
        
        // 简单实现：读取文件大小作为内容长度指示
        if let Ok(metadata) = std::fs::metadata(path) {
            let size = metadata.len();
            Some(format!("PDF Document ({} bytes)", size))
        } else {
            None
        }
    }
    
    /// 解析 Markdown 文件
    fn parse_markdown(&self, path: &PathBuf) -> Option<String> {
        println!("📝 解析 Markdown 文件: {:?}", path);
        
        match std::fs::read_to_string(path) {
            Ok(content) => {
                let lines = content.lines().count();
                let headings = content.lines().filter(|l| l.starts_with('#')).count();
                Some(format!("Markdown ({} lines, {} headings)", lines, headings))
            }
            Err(_) => None,
        }
    }
}

/// 启动文件监控服务
/// 这个函数在后台运行，持续监控所有已注册的文件夹
pub fn start_file_monitor(app_handle: AppHandle) {
    println!("🚀 启动文件系统监控服务");
    println!("✅ 文件监控已启动");
    println!("   当文件夹中有新文件时自动检测");
    println!("   使用轮询机制，每5秒扫描一次");
    
    let monitor = Arc::new(FileMonitor::new(app_handle));
    
    // 模拟监控循环
    loop {
        std::thread::sleep(std::time::Duration::from_secs(5));
        
        // 扫描所有已注册的文件夹
        let folders = monitor.watched_folders.lock().unwrap().clone();
        for folder in folders {
            monitor.scan_folder(&folder);
        }
    }
}
