/// 长期记忆数据库
/// 这是 WayFare 的知识库，记录：
/// 1. 学生的学习历程
/// 2. 常见的误解
/// 3. 需要复习的概念
/// 4. 已掌握的知识
/// 5. 最有效的教学策略
///
/// 长期记忆让学习不再是一次性消费，而是可复盘、可回溯的过程

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ConceptMemory {
    pub concept_name: String,
    pub first_learned_at: u64,
    pub mastery_level: f32,      // 0.0 - 1.0
    pub review_count: u32,
    pub common_mistakes: Vec<String>,
    pub effective_explanations: Vec<String>,
    pub next_review_date: Option<u64>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StudentProfile {
    pub user_id: String,
    pub preferred_learning_style: String,
    pub average_study_pace: f32,
    pub strong_areas: Vec<String>,
    pub weak_areas: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LearningTrace {
    pub id: String,
    pub user_id: String,
    pub concept: String,
    pub event_type: String,           // 'first_encounter', 'confusion', 'breakthrough', 'mastery', etc
    pub timestamp: u64,
    pub context: HashMap<String, String>,
}

pub struct MemoryDatabase {
    // 学生的概念掌握情况
    concepts: HashMap<String, ConceptMemory>,
    
    // 学生档案
    students: HashMap<String, StudentProfile>,
    
    // 学习轨迹（完整的学习历程记录）
    traces: Vec<LearningTrace>,
}

impl MemoryDatabase {
    pub fn new() -> Self {
        MemoryDatabase {
            concepts: HashMap::new(),
            students: HashMap::new(),
            traces: Vec::new(),
        }
    }
    
    /// 记录学生首次接触某个概念
    pub fn record_first_encounter(
        &mut self,
        user_id: String,
        concept: String,
        context: HashMap<String, String>,
    ) {
        println!("📖 首次接触: {} - {}", user_id, concept);
        
        if !self.concepts.contains_key(&concept) {
            self.concepts.insert(
                concept.clone(),
                ConceptMemory {
                    concept_name: concept.clone(),
                    first_learned_at: std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .unwrap()
                        .as_secs(),
                    mastery_level: 0.0,
                    review_count: 0,
                    common_mistakes: Vec::new(),
                    effective_explanations: Vec::new(),
                    next_review_date: None,
                },
            );
        }
        
        // 记录学习轨迹
        self.traces.push(LearningTrace {
            id: format!("trace_{}", chrono::Local::now().timestamp()),
            user_id,
            concept,
            event_type: "first_encounter".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            context,
        });
    }
    
    /// 记录学生的困惑
    pub fn record_confusion(
        &mut self,
        user_id: String,
        concept: String,
        mistake: String,
    ) {
        println!("❌ 困惑记录: {} - {}", concept, mistake);
        
        if let Some(concept_mem) = self.concepts.get_mut(&concept) {
            // 降低掌握度
            concept_mem.mastery_level = (concept_mem.mastery_level - 0.1).max(0.0);
            
            // 添加常见错误
            if !concept_mem.common_mistakes.contains(&mistake) {
                concept_mem.common_mistakes.push(mistake);
            }
        }
        
        // 记录学习轨迹
        let mut context = HashMap::new();
        context.insert("mistake".to_string(), mistake);
        
        self.traces.push(LearningTrace {
            id: format!("trace_{}", chrono::Local::now().timestamp()),
            user_id,
            concept,
            event_type: "confusion".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            context,
        });
    }
    
    /// 记录突破（学生理解某个概念了）
    pub fn record_breakthrough(
        &mut self,
        user_id: String,
        concept: String,
        explanation_method: String,
    ) {
        println!("💡 突破记录: {} - 使用方法: {}", concept, explanation_method);
        
        if let Some(concept_mem) = self.concepts.get_mut(&concept) {
            concept_mem.mastery_level = (concept_mem.mastery_level + 0.2).min(1.0);
            
            // 记录有效的解释方法
            if !concept_mem.effective_explanations.contains(&explanation_method) {
                concept_mem.effective_explanations.push(explanation_method);
            }
        }
        
        // 记录学习轨迹
        let mut context = HashMap::new();
        context.insert("method".to_string(), explanation_method);
        
        self.traces.push(LearningTrace {
            id: format!("trace_{}", chrono::Local::now().timestamp()),
            user_id,
            concept,
            event_type: "breakthrough".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            context,
        });
    }
    
    /// 记录掌握（学生已充分掌握某个概念）
    pub fn record_mastery(
        &mut self,
        user_id: String,
        concept: String,
    ) {
        println!("🏆 掌握记录: {}", concept);
        
        if let Some(concept_mem) = self.concepts.get_mut(&concept) {
            concept_mem.mastery_level = 1.0;
            concept_mem.review_count += 1;
        }
        
        // 记录学习轨迹
        self.traces.push(LearningTrace {
            id: format!("trace_{}", chrono::Local::now().timestamp()),
            user_id,
            concept,
            event_type: "mastery".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            context: HashMap::new(),
        });
    }
    
    /// 获取某个学生对某个概念的掌握情况
    pub fn get_concept_memory(
        &self,
        concept: &str,
    ) -> Option<&ConceptMemory> {
        self.concepts.get(concept)
    }
    
    /// 获取学生的学习轨迹
    pub fn get_learning_traces(
        &self,
        user_id: &str,
        limit: Option<usize>,
    ) -> Vec<&LearningTrace> {
        let mut traces: Vec<_> = self.traces
            .iter()
            .filter(|t| t.user_id == user_id)
            .collect();
        
        traces.reverse(); // 时间倒序
        
        if let Some(l) = limit {
            traces.truncate(l);
        }
        
        traces
    }
    
    /// 分析学生的强弱项
    pub fn analyze_student_profile(
        &mut self,
        user_id: &str,
    ) -> StudentProfile {
        println!("📊 分析学生档案: {}", user_id);
        
        let mut strong_areas = Vec::new();
        let mut weak_areas = Vec::new();
        
        for (concept, memory) in &self.concepts {
            if memory.mastery_level > 0.7 {
                strong_areas.push(concept.clone());
            } else if memory.mastery_level < 0.3 {
                weak_areas.push(concept.clone());
            }
        }
        
        let profile = StudentProfile {
            user_id: user_id.to_string(),
            preferred_learning_style: "mixed".to_string(), // TODO: 从交互数据推断
            average_study_pace: 1.0,
            strong_areas,
            weak_areas,
        };
        
        self.students.insert(user_id.to_string(), profile.clone());
        profile
    }
    
    /// 导出学习报告
    pub fn generate_learning_report(&self, user_id: &str) -> serde_json::Value {
        println!("📄 生成学习报告: {}", user_id);
        
        let traces = self.get_learning_traces(user_id, None);
        
        let total_concepts = self.concepts.len();
        let mastered = self.concepts
            .values()
            .filter(|c| c.mastery_level >= 0.8)
            .count();
        
        serde_json::json!({
            "user_id": user_id,
            "total_concepts": total_concepts,
            "mastered_concepts": mastered,
            "mastery_percentage": if total_concepts > 0 {
                (mastered as f32 / total_concepts as f32 * 100.0) as u32
            } else {
                0
            },
            "learning_events": traces.len(),
            "recent_events": traces.iter().take(10).map(|t| serde_json::json!({
                "concept": t.concept,
                "event": t.event_type,
                "time": t.timestamp,
            })).collect::<Vec<_>>(),
        })
    }
    
    /// 保存到 JSON 文件
    pub fn save_to_file(&self, path: &std::path::Path) -> Result<(), std::io::Error> {
        println!("💾 保存数据库到文件: {:?}", path);
        
        let data = serde_json::json!({
            "concepts": self.concepts
                .iter()
                .map(|(k, v)| (k.clone(), v))
                .collect::<Vec<_>>(),
            "students": self.students
                .iter()
                .map(|(k, v)| (k.clone(), v))
                .collect::<Vec<_>>(),
            "traces": self.traces.clone(),
        });
        
        let json_str = serde_json::to_string_pretty(&data)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))?;
        
        std::fs::write(path, json_str)?;
        println!("✅ 数据库已保存");
        Ok(())
    }
    
    /// 从 JSON 文件加载
    pub fn load_from_file(path: &std::path::Path) -> Result<Self, std::io::Error> {
        println!("📂 从文件加载数据库: {:?}", path);
        
        let json_str = std::fs::read_to_string(path)?;
        let data: serde_json::Value = serde_json::from_str(&json_str)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
        
        let mut db = MemoryDatabase::new();
        
        // 加载概念
        if let Some(concepts) = data["concepts"].as_array() {
            for concept_array in concepts {
                if let Some(arr) = concept_array.as_array() {
                    if arr.len() == 2 {
                        if let Ok(concept) = serde_json::from_value::<ConceptMemory>(arr[1].clone()) {
                            db.concepts.insert(concept.concept_name.clone(), concept);
                        }
                    }
                }
            }
        }
        
        // 加载学生档案
        if let Some(students) = data["students"].as_array() {
            for student_array in students {
                if let Some(arr) = student_array.as_array() {
                    if arr.len() == 2 {
                        if let Ok(student) = serde_json::from_value::<StudentProfile>(arr[1].clone()) {
                            db.students.insert(student.user_id.clone(), student);
                        }
                    }
                }
            }
        }
        
        // 加载学习轨迹
        if let Some(traces) = data["traces"].as_array() {
            for trace in traces {
                if let Ok(t) = serde_json::from_value::<LearningTrace>(trace.clone()) {
                    db.traces.push(t);
                }
            }
        }
        
        println!("✅ 数据库已加载");
        Ok(db)
    }
}

// 全局长期记忆数据库实例
use std::sync::Mutex;
use lazy_static::lazy_static;

lazy_static! {
    /// 全局长期记忆数据库
    /// 使用 Mutex 保证线程安全
    pub static ref MEMORY_DB: Mutex<MemoryDatabase> = Mutex::new(MemoryDatabase::new());
}
