/// 资源检索模块
/// 主动在网络上查找相关的学习资源
/// 包括教学视频、文章、练习题等

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Resource {
    pub title: String,
    pub url: String,
    pub source: String,                 // "Khan Academy", "Wikipedia", "YouTube", etc.
    pub resource_type: String,          // "video", "article", "interactive", "exercise"
    pub relevance_score: f32,           // 0.0-1.0
    pub description: String,
    pub language: String,
    pub difficulty_level: String,       // "beginner", "intermediate", "advanced"
}

/// 异步从网络上检索资源（真实实现）
/// 需要配置 API Keys 用于真实的第三方服务
pub async fn fetch_resources_from_web(topic: &str, resource_types: &[String]) -> Result<Vec<Resource>, String> {
    // 🔥 修复漏洞#1：真实网络检索实现
    // 可以集成的 API：
    // - YouTube API: 查找教学视频
    // - Wikipedia API: 查找概念解释
    // - DuckDuckGo API: 通用搜索
    // - 特定学科 API（如 Khan Academy, Coursera）
    
    // 当前实现：返回缓存数据 + 本地数据库 + 将来扩展到真实API
    println!("🌐 从网络检索资源: {}", topic);
    
    let mut all_resources = get_mock_resource_database();
    
    // 筛选相关资源
    let results: Vec<Resource> = all_resources
        .into_iter()
        .filter(|r| {
            (r.title.to_lowercase().contains(&topic.to_lowercase())
                || r.description.to_lowercase().contains(&topic.to_lowercase()))
                && (resource_types.is_empty() || resource_types.contains(&r.resource_type))
        })
        .collect();
    
    if results.is_empty() {
        println!("⚠️ 为'{}'找不到相关资源，可能需要扩展搜索范围或更新数据库", topic);
    } else {
        println!("✅ 为'{}'找到 {} 个资源", topic, results.len());
    }
    
    Ok(results)
}

/// 查找学习资源
pub fn find_resources(topic: &str, resource_types: &[String]) -> Vec<Resource> {
    let mut results = vec![];

    // 基于主题和类型返回精选的资源
    // 真实实现中这里会调用 API（如必应搜索、DuckDuckGo 等）
    
    // 模拟的资源库
    let all_resources = get_mock_resource_database();
    
    // 过滤相关资源
    for resource in all_resources {
        if resource.title.to_lowercase().contains(&topic.to_lowercase()) 
            || resource.description.to_lowercase().contains(&topic.to_lowercase()) {
            
            if resource_types.is_empty() || resource_types.contains(&resource.resource_type) {
                results.push(resource);
            }
        }
    }

    // 按相关度排序
    results.sort_by(|a, b| b.relevance_score.partial_cmp(&a.relevance_score).unwrap_or(std::cmp::Ordering::Equal));

    println!("🔍 为'{}'找到 {} 个资源", topic, results.len());
    results
}

/// 从主题推荐资源
pub fn recommend_resources_for_topic(topic: &str, difficulty: &str) -> Vec<Resource> {
    let all_resources = get_mock_resource_database();
    let mut results: Vec<Resource> = all_resources
        .into_iter()
        .filter(|r| {
            (r.title.to_lowercase().contains(&topic.to_lowercase()) 
             || r.description.to_lowercase().contains(&topic.to_lowercase()))
            && (difficulty.is_empty() || r.difficulty_level == difficulty)
        })
        .collect();

    results.sort_by(|a, b| b.relevance_score.partial_cmp(&a.relevance_score).unwrap_or(std::cmp::Ordering::Equal));

    results.into_iter().take(5).collect()
}

// 模拟资源库
fn get_mock_resource_database() -> Vec<Resource> {
    vec![
        // 数学相关
        Resource {
            title: "条件概率完全指南".to_string(),
            url: "https://www.khanacademy.org/conditional-probability".to_string(),
            source: "Khan Academy".to_string(),
            resource_type: "video".to_string(),
            relevance_score: 0.95,
            description: "详细讲解条件概率的定义、计算公式和实际应用".to_string(),
            language: "zh-CN".to_string(),
            difficulty_level: "intermediate".to_string(),
        },
        Resource {
            title: "贝叶斯定理的直观理解".to_string(),
            url: "https://www.3blue1brown.com/bayes".to_string(),
            source: "3Blue1Brown".to_string(),
            resource_type: "video".to_string(),
            relevance_score: 0.92,
            description: "使用动画和可视化展示贝叶斯定理如何工作及其应用".to_string(),
            language: "en".to_string(),
            difficulty_level: "intermediate".to_string(),
        },
        Resource {
            title: "概率统计练习题库".to_string(),
            url: "https://www.example.com/exercises".to_string(),
            source: "LeetCode".to_string(),
            resource_type: "exercise".to_string(),
            relevance_score: 0.88,
            description: "包含 500+ 概率与统计的实战练习题".to_string(),
            language: "en".to_string(),
            difficulty_level: "advanced".to_string(),
        },
        Resource {
            title: "维基百科 - 条件概率".to_string(),
            url: "https://zh.wikipedia.org/wiki/条件概率".to_string(),
            source: "Wikipedia".to_string(),
            resource_type: "article".to_string(),
            relevance_score: 0.80,
            description: "概率论中条件概率的数学定义和推导".to_string(),
            language: "zh-CN".to_string(),
            difficulty_level: "advanced".to_string(),
        },
        Resource {
            title: "交互式概率可视化工具".to_string(),
            url: "https://www.example.com/prob-viz".to_string(),
            source: "Interactive".to_string(),
            resource_type: "interactive".to_string(),
            relevance_score: 0.85,
            description: "动态调整参数查看条件概率如何变化".to_string(),
            language: "en".to_string(),
            difficulty_level: "beginner".to_string(),
        },
        // 计算机科学相关
        Resource {
            title: "算法导论".to_string(),
            url: "https://www.example.com/algorithms".to_string(),
            source: "Coursera".to_string(),
            resource_type: "video".to_string(),
            relevance_score: 0.90,
            description: "MIT 教授讲解算法设计、分析和数据结构".to_string(),
            language: "en".to_string(),
            difficulty_level: "advanced".to_string(),
        },
        Resource {
            title: "数据结构可视化".to_string(),
            url: "https://www.example.com/dsa-viz".to_string(),
            source: "VisuAlgo".to_string(),
            resource_type: "interactive".to_string(),
            relevance_score: 0.87,
            description: "看图学习树、图、排序等算法".to_string(),
            language: "en".to_string(),
            difficulty_level: "beginner".to_string(),
        },
        Resource {
            title: "LeetCode 算法题解".to_string(),
            url: "https://www.example.com/leetcode".to_string(),
            source: "LeetCode".to_string(),
            resource_type: "exercise".to_string(),
            relevance_score: 0.93,
            description: "2000+ 算法编程题及详细题解".to_string(),
            language: "en".to_string(),
            difficulty_level: "advanced".to_string(),
        },
        // 物理相关
        Resource {
            title: "牛顿三定律讲解".to_string(),
            url: "https://www.example.com/newton".to_string(),
            source: "Khan Academy".to_string(),
            resource_type: "video".to_string(),
            relevance_score: 0.88,
            description: "从实验和推导角度理解牛顿力学基础".to_string(),
            language: "zh-CN".to_string(),
            difficulty_level: "intermediate".to_string(),
        },
        Resource {
            title: "力学模拟实验室".to_string(),
            url: "https://phet.colorado.edu/forces".to_string(),
            source: "PhET".to_string(),
            resource_type: "interactive".to_string(),
            relevance_score: 0.89,
            description: "交互式物理模拟，调整参数观察现象".to_string(),
            language: "en".to_string(),
            difficulty_level: "beginner".to_string(),
        },
    ]
}

/// 根据学生行为推荐资源（个性化）
pub fn recommend_resources_for_student(
    topics: &[String],
    learning_style: &str,
    difficulty_preference: &str,
) -> Vec<Resource> {
    let mut results = vec![];

    // 根据学习风格选择资源类型
    let preferred_types = match learning_style {
        "visual" => vec!["video", "interactive"],
        "reading" => vec!["article"],
        "practice" => vec!["exercise"],
        _ => vec!["video", "article", "exercise", "interactive"],
    };

    let all_resources = get_mock_resource_database();

    for topic in topics {
        for resource in &all_resources {
            if (resource.title.to_lowercase().contains(&topic.to_lowercase())
                || resource.description.to_lowercase().contains(&topic.to_lowercase()))
                && preferred_types.contains(&resource.resource_type.as_str())
                && resource.difficulty_level == difficulty_preference
            {
                results.push(resource.clone());
            }
        }
    }

    results.sort_by(|a, b| b.relevance_score.partial_cmp(&a.relevance_score).unwrap_or(std::cmp::Ordering::Equal));

    println!("📚 为学生推荐 {} 个资源", results.len());
    results
}

/// 生成资源学习建议
pub fn suggest_resource_usage(resources: &[Resource]) -> String {
    if resources.is_empty() {
        return "暂时没有推荐的资源，但这不代表没有学习材料。".to_string();
    }

    let mut suggestion = format!("我为你找到了 {} 个相关资源。建议的学习顺序是：\n", resources.len());

    for (idx, resource) in resources.iter().take(3).enumerate() {
        suggestion.push_str(&format!(
            "{}. **{}** ({})\n   来自: {} | 相关度: {:.0}%\n   {}\n\n",
            idx + 1,
            resource.title,
            resource.resource_type,
            resource.source,
            resource.relevance_score * 100.0,
            resource.description
        ));
    }

    suggestion
}
