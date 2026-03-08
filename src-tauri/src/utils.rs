/// 工具函数集合
/// 支持各种后端相关的工具函数

use std::path::Path;
use std::fs;

/// 获取文件类型
pub fn get_file_type(file_path: &Path) -> Option<String> {
    file_path
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|s| s.to_lowercase())
}

/// 检查是否是学习资料文件
pub fn is_learning_material(file_path: &Path) -> bool {
    matches!(
        get_file_type(file_path).as_deref(),
        Some("pdf") | Some("md") | Some("markdown") | Some("txt") | Some("doc") | Some("docx")
    )
}

/// 估算文件阅读时间（以分钟计）
pub fn estimate_reading_time(word_count: usize) -> u32 {
    // 平均阅读速度：200-250 词/分钟
    // 学术内容阅读速度较慢，使用 150 词/分钟
    ((word_count / 150) as u32).max(1)
}

/// 从文本中提取关键词
pub fn extract_keywords(text: &str, count: usize) -> Vec<String> {
    // 简单的实现：按词频统计
    // TODO: 使用更高级的 NLP 库
    
    let words: Vec<&str> = text
        .split_whitespace()
        .filter(|w| w.len() > 3)
        .collect();
    
    let mut keyword_map = std::collections::HashMap::new();
    for word in words {
        *keyword_map.entry(word.to_lowercase()).or_insert(0) += 1;
    }
    
    let mut keywords: Vec<_> = keyword_map.into_iter().collect();
    keywords.sort_by(|a, b| b.1.cmp(&a.1));
    
    keywords
        .iter()
        .take(count)
        .map(|(k, _)| k.clone())
        .collect()
}

/// 计算文本相似度（简化版，使用 TF-IDF）
pub fn calculate_similarity(text1: &str, text2: &str) -> f32 {
    let words1: std::collections::HashSet<_> = text1.split_whitespace().collect();
    let words2: std::collections::HashSet<_> = text2.split_whitespace().collect();
    
    let intersection = words1.intersection(&words2).count();
    let union = words1.union(&words2).count();
    
    if union == 0 {
        0.0
    } else {
        intersection as f32 / union as f32
    }
}

/// 生成唯一的 ID
pub fn generate_id(prefix: &str) -> String {
    format!(
        "{}_{}_{}",
        prefix,
        chrono::Local::now().timestamp(),
        uuid::Uuid::new_v4().to_string()[..8].to_string()
    )
}

/// 获取系统当前时间戳（秒）
pub fn current_timestamp() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs()
}

/// 解析时间间隔
pub fn parse_duration(seconds: u64) -> String {
    if seconds < 60 {
        format!("{}秒", seconds)
    } else if seconds < 3600 {
        format!("{}分钟", seconds / 60)
    } else if seconds < 86400 {
        format!("{}小时", seconds / 3600)
    } else {
        format!("{}天", seconds / 86400)
    }
}

/// 检查路径是否存在
pub fn path_exists(path: &std::path::Path) -> bool {
    path.exists()
}

/// 递归扫描目录中的学习材料
pub fn scan_learning_materials(dir: &Path) -> std::io::Result<Vec<std::path::PathBuf>> {
    let mut materials = Vec::new();
    
    if dir.is_dir() {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.is_dir() {
                // 递归扫描子目录
                match scan_learning_materials(&path) {
                    Ok(mut sub_materials) => materials.append(&mut sub_materials),
                    Err(_) => continue,
                }
            } else if is_learning_material(&path) {
                materials.push(path);
            }
        }
    }
    
    Ok(materials)
}

/// 文件大小格式化
pub fn format_file_size(bytes: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB"];
    
    let mut size = bytes as f64;
    let mut unit_idx = 0;
    
    while size > 1024.0 && unit_idx < UNITS.len() - 1 {
        size /= 1024.0;
        unit_idx += 1;
    }
    
    format!("{:.2} {}", size, UNITS[unit_idx])
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_extract_keywords() {
        let text = "机器学习是人工智能的重要分支，机器学习技术应用广泛";
        let keywords = extract_keywords(text, 3);
        assert_eq!(keywords.len(), 3);
        assert!(keywords.contains(&"机器学习".to_string()));
    }
    
    #[test]
    fn test_calculate_similarity() {
        let text1 = "机器学习是人工智能";
        let text2 = "机器学习和人工智能";
        let similarity = calculate_similarity(text1, text2);
        assert!(similarity > 0.0 && similarity <= 1.0);
    }
    
    #[test]
    fn test_estimate_reading_time() {
        let time = estimate_reading_time(3000);
        assert_eq!(time, 20); // 3000 words / 150 = 20 minutes
    }
    
    #[test]
    fn test_generate_id() {
        let id = generate_id("test");
        assert!(id.starts_with("test_"));
    }
    
    #[test]
    fn test_parse_duration() {
        assert_eq!(parse_duration(30), "30秒");
        assert_eq!(parse_duration(120), "2分钟");
        assert_eq!(parse_duration(3600), "1小时");
        assert_eq!(parse_duration(86400), "1天");
    }
    
    #[test]
    fn test_format_file_size() {
        assert_eq!(format_file_size(512), "512.00 B");
        assert_eq!(format_file_size(1024), "1.00 KB");
    }
    
    #[test]
    fn test_is_learning_material() {
        assert!(is_learning_material(std::path::Path::new("document.pdf")));
        assert!(is_learning_material(std::path::Path::new("notes.md")));
        assert!(!is_learning_material(std::path::Path::new("image.png")));
    }
}

// ============= 额外工具函数 =============

/// 计算学习进度百分比
pub fn calculate_mastery_percentage(
    total_annotations: usize,
    understood_annotations: usize,
) -> f32 {
    if total_annotations == 0 {
        0.0
    } else {
        (understood_annotations as f32 / total_annotations as f32) * 100.0
    }
}

/// 估算学习难度 (0.0-1.0)
pub fn estimate_difficulty(
    word_count: usize,
    unique_terms: usize,
) -> f32 {
    let readability = (unique_terms as f32 / word_count.max(1) as f32) * 0.5;
    let complexity = (word_count as f32 / 1000.0).min(1.0) * 0.5;
    (readability + complexity).min(1.0)
}

/// 验证学习目标格式
pub fn validate_learning_goal(goal: &str) -> Result<(), String> {
    if goal.is_empty() {
        return Err("学习目标不能为空".to_string());
    }
    if goal.len() > 200 {
        return Err("学习目标不能超过200字".to_string());
    }
    Ok(())
}

/// 根据学习进度计算评级
pub fn calculate_grade(mastery: f32) -> &'static str {
    match (mastery * 10.0) as u32 {
        9..=10 => "优秀",
        8 => "良好",
        6..=7 => "中等",
        4..=5 => "及格",
        _ => "不及格",
    }
}

/// 计算学习建议
pub fn get_learning_recommendation(
    mastery_percentage: f32,
    study_time_hours: f32,
) -> String {
    if mastery_percentage < 0.3 {
        "你的掌握程度较低，建议多花时间学习和练习".to_string()
    } else if mastery_percentage < 0.6 {
        "继续努力，已经打下了基础，需要进一步加强".to_string()
    } else if mastery_percentage < 0.8 {
        "很好的进展！再加把劲就能完全掌握".to_string()
    } else {
        "太棒了！你已经掌握了大部分内容，可以尝试更难的题目".to_string()
    }
}

/// 规范化学习风格字符串
pub fn normalize_learning_style(style: &str) -> String {
    match style.to_lowercase().as_str() {
        "visual" | "视觉" => "visual".to_string(),
        "auditory" | "听觉" => "auditory".to_string(),
        "kinesthetic" | "运动" => "kinesthetic".to_string(),
        "reading" | "阅读" => "reading".to_string(),
        _ => "mixed".to_string(),
    }
}
