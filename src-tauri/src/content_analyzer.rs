/// 内容分析模块
/// 自动解读学习资料中的：
/// - 重点概念
/// - 难点难度
/// - 例题
/// - 关键统计数据

use regex::Regex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentAnalysis {
    pub key_concepts: Vec<KeyConcept>,
    pub difficulty_level: f32,          // 0.0-1.0
    pub estimated_time_hours: f32,
    pub key_examples: Vec<String>,
    pub related_topics: Vec<String>,
    pub learning_objectives: Vec<String>,
    pub prerequisite_knowledge: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyConcept {
    pub concept: String,
    pub importance: f32,                // 0.0-1.0
    pub frequency: i32,
    pub difficulty: f32,                // 0.0-1.0
    pub section_reference: Option<String>,
}

/// 分析文档内容
pub fn analyze_content(content: &str, doc_type: &str) -> ContentAnalysis {
    let mut analysis = ContentAnalysis {
        key_concepts: Vec::new(),
        difficulty_level: 0.5,
        estimated_time_hours: 1.0,
        key_examples: Vec::new(),
        related_topics: Vec::new(),
        learning_objectives: Vec::new(),
        prerequisite_knowledge: Vec::new(),
    };

    match doc_type {
        "markdown" => analyze_markdown(content, &mut analysis),
        "pdf" => analyze_pdf_text(content, &mut analysis),
        _ => analyze_text(content, &mut analysis),
    }

    // 估计学习时间（基于单词数）
    let word_count = content.split_whitespace().count();
    analysis.estimated_time_hours = (word_count as f32 / 300.0) * difficulty_multiplier(analysis.difficulty_level);

    analysis
}

/// 分析 Markdown 内容
fn analyze_markdown(content: &str, analysis: &mut ContentAnalysis) {
    let lines: Vec<&str> = content.lines().collect();
    let mut current_section = String::new();

    for line in &lines {
        // 识别标题层级 = 难度指示
        if line.starts_with("# ") {
            current_section = line.trim_start_matches("# ").to_string();
            analysis.learning_objectives.push(current_section.clone());
            analysis.difficulty_level = 0.3;
        } else if line.starts_with("## ") {
            let subsection = line.trim_start_matches("## ").to_string();
            analysis.difficulty_level = (analysis.difficulty_level + 0.4) / 2.0;
        } else if line.starts_with("### ") {
            analysis.difficulty_level = (analysis.difficulty_level + 0.6) / 2.0;
        }

        // 识别重点概念（**粗体**、***加粗*** 通常标记重要概念）
        extract_bold_concepts(line, analysis);

        // 识别例题
        if line.contains("例") || line.contains("Example") || line.contains("示例") {
            let example = extract_example_text(line, &lines);
            if !example.is_empty() {
                analysis.key_examples.push(example);
            }
        }

        // 识别公式和复杂表达式（难度指示）
        if line.contains("$$") || line.contains("$") {
            analysis.difficulty_level = (analysis.difficulty_level + 0.8) / 2.0;
        }
    }

    // 识别前置知识
    extract_prerequisites(content, analysis);
}

/// 分析 PDF 文本
fn analyze_pdf_text(content: &str, analysis: &mut ContentAnalysis) {
    // PDF 的复杂度通常较高
    analysis.difficulty_level = 0.6;
    
    // 基于结构关键词识别内容类型
    if content.contains("定义") || content.contains("Definition") {
        analysis.learning_objectives.push("掌握关键定义".to_string());
    }
    
    if content.contains("定理") || content.contains("Theorem") {
        analysis.difficulty_level = (analysis.difficulty_level + 0.8) / 2.0;
        analysis.learning_objectives.push("理解重要定理".to_string());
    }

    extract_bold_concepts(&content.lines().next().unwrap_or(""), analysis);
}

/// 分析文本内容
fn analyze_text(content: &str, analysis: &mut ContentAnalysis) {
    // 通用文本分析
    let word_count = content.split_whitespace().count();
    
    // 根据文本复杂度估计难度
    if word_count < 500 {
        analysis.difficulty_level = 0.3;
    } else if word_count < 2000 {
        analysis.difficulty_level = 0.5;
    } else {
        analysis.difficulty_level = 0.7;
    }

    // 提取潜在的关键概念（单词频率）
    let freq_words = extract_frequency_words(content);
    for (word, freq) in freq_words.iter().take(10) {
        analysis.key_concepts.push(KeyConcept {
            concept: word.clone(),
            importance: (*freq as f32) / 100.0,
            frequency: *freq,
            difficulty: analysis.difficulty_level,
            section_reference: None,
        });
    }
}

/// 提取加粗文本中的概念
fn extract_bold_concepts(line: &str, analysis: &mut ContentAnalysis) {
    let bold_pattern = Regex::new(r"\*\*(.+?)\*\*").unwrap();
    
    for cap in bold_pattern.captures_iter(line) {
        if let Some(concept) = cap.get(1) {
            let concept_text = concept.as_str().to_string();
            
            // 检查概念是否已存在
            if !analysis.key_concepts.iter().any(|c| c.concept == concept_text) {
                analysis.key_concepts.push(KeyConcept {
                    concept: concept_text,
                    importance: 0.9,                  // 加粗文本被认为很重要
                    frequency: 1,
                    difficulty: 0.5,
                    section_reference: None,
                });
            }
        }
    }
}

/// 提取例题
fn extract_example_text(line: &str, _lines: &[&str]) -> String {
    if line.contains("例") || line.contains("Example") {
        line.trim().to_string()
    } else {
        String::new()
    }
}

/// 识别前置知识
fn extract_prerequisites(content: &str, analysis: &mut ContentAnalysis) {
    if content.contains("首先") || content.contains("基础") || content.contains("预备") {
        analysis.prerequisite_knowledge.push("确保掌握基础概念".to_string());
    }
    
    if content.contains("微积分") || content.contains("代数") {
        analysis.prerequisite_knowledge.push("需要微积分基础".to_string());
    }
}

/// 提取高频词汇（关键词）
fn extract_frequency_words(content: &str) -> Vec<(String, i32)> {
    let mut word_freq: std::collections::HashMap<String, i32> = std::collections::HashMap::new();
    
    let lowercase_content = content.to_lowercase();
    let words: Vec<&str> = lowercase_content
        .split(|c: char| !c.is_alphanumeric() && c != '_')
        .filter(|w| w.len() > 3)        // 只取长度 > 3 的词
        .collect();

    for word in words {
        *word_freq.entry(word.to_string()).or_insert(0) += 1;
    }

    let mut freq_vec: Vec<_> = word_freq.into_iter().collect();
    freq_vec.sort_by(|a, b| b.1.cmp(&a.1));

    freq_vec
}

/// 难度倍数（用于估计学习时间）
fn difficulty_multiplier(difficulty: f32) -> f32 {
    1.0 + (difficulty * 2.0)
}

/// 检测文本复杂度得分
pub fn calculate_complexity_score(content: &str) -> f32 {
    let word_count = content.split_whitespace().count();
    let sentence_count = content.split('.').count();
    let avg_word_length = content.chars().count() as f32 / (word_count as f32).max(1.0);
    
    let avg_sentence_length = word_count as f32 / sentence_count as f32;
    
    // 使用 Flesch-Kincaid 公式的简化版本
    let score = (0.39 * avg_sentence_length + 11.8 * avg_word_length - 15.59) / 20.0;
    
    score.max(0.0).min(1.0)
}

/// 生成学习策略建议
pub fn suggest_learning_strategy(analysis: &ContentAnalysis) -> Vec<String> {
    let mut suggestions = vec![];

    if analysis.difficulty_level > 0.7 {
        suggestions.push("这个主题很复杂，建议多看例题".to_string());
        suggestions.push("先掌握基础概念再深入理解".to_string());
    } else if analysis.difficulty_level > 0.4 {
        suggestions.push("适度难度，按顺序学习效果会很好".to_string());
    } else {
        suggestions.push("基础知识，要掌握透彻哦".to_string());
    }

    if !analysis.key_examples.is_empty() {
        suggestions.push(format!("有 {} 个例题可以参考", analysis.key_examples.len()));
    }

    if analysis.estimated_time_hours > 3.0 {
        suggestions.push(format!("预计需要 {:.1} 小时学习", analysis.estimated_time_hours));
    }

    suggestions
}
