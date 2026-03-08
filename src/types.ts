// ============= Priority & Severity Levels =============
export const LearningPriority = {
  CRITICAL: 'critical',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  REVIEW: 'review'
} as const;

export type LearningPriorityType = typeof LearningPriority[keyof typeof LearningPriority];

export const ConfidenceLevel = {
  VERY_LOW: 'very_low',
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  MASTERED: 'mastered'
} as const;

export type ConfidenceLevelType = typeof ConfidenceLevel[keyof typeof ConfidenceLevel];

// ============= Position & Core Types =============
export interface Position {
  page?: number;
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  sectionId?: string;
}

// ============= Annotation System =============
export interface Annotation {
  id: string;
  documentId: string;
  sourceText?: string;
  position: Position;
  content: string;
  type: 'highlight' | 'bubble';
  severity?: 'low' | 'medium' | 'high';
  category?: 'core_concept' | 'misunderstanding' | 'learning_strategy' | 'exam_preparation';
  pedagogicalType?: 'analogy' | 'strategy' | 'comparison' | 'procedure' | 'evidence_based' | 'hint';
  relatedKeywords?: string[];
  createdAt?: number;
  updatedAt?: number;
  metadata?: {
    frequency?: string;
    mistakeRate?: number;
    correctRate?: number;
    estimatedTimeToUnderstand?: number;
    [key: string]: unknown;
  };
}

/**
 * 增强的批注，支持优先级、认知支架、学习路径等
 * 每个批注是学生认知痕迹的一部分，沉淀回材料本身
 */
export interface EnhancedAnnotation extends Annotation {
  priority: LearningPriorityType;
  confidence: ConfidenceLevelType;
  
  // 认知支架：教学心理学中的支持系统
  scaffolding?: {
    analogy?: string;           // 类比：用A解释B
    decomposition?: string[];   // 拆解：复杂概念的步骤分解
    keyQuestions?: string[];    // 关键问题：费曼技巧的问组
    priorKnowledge?: string;    // 前置知识：需要先掌握什么
  };
  
  // 经历与进度
  firstMissingAt?: number;      // 第一次卡住的时间
  masterAt?: number;            // 掌握时间
  reviewCount?: number;         // 复习次数
  lastReviewAt?: number;        // 最后一次复习
  
  // 学生的个性化反馈循环
  studentResponses?: {
    feedback?: string;          // 学生的反馈
    clarifications?: string[];  // 还需要澄清的地方
    timestamp?: number;
  };
}

export interface AnnotationFile {
  documentId: string;
  documentName: string;
  documentType: 'markdown' | 'pdf';
  annotations: EnhancedAnnotation[];
  metadata?: {
    createdAt: number;
    updatedAt: number;
    totalAnnotations: number;
    lastEnrichedAt?: number;   // 最后一次 AI 增强批注时间
    [key: string]: unknown;
  };
}

// ============= Conversation & Chat =============
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  annotationId?: string;       // 关联的批注 ID
  documentId?: string;         // 关联的文档 ID
  relatedAnnotations?: string[]; // 相关批注列表
}

/**
 * 对话会话，每个学习项目有一个会话
 * 所有对话沉淀在项目中，形成学习记录
 */
export interface ConversationSession {
  id: string;
  projectId: string;
  documentId: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  summary?: string;            // Token 版本的总结
  tags?: string[];             // 学习标签
}

// ============= Document =============
export interface Document {
  id: string;
  name: string;
  path: string;
  type: 'pdf' | 'markdown' | 'image' | 'ppt';
  content?: string;
  createdAt: number;
  updatedAt: number;
  size?: number;
  pages?: number;
  projectId?: string;          // 所属项目
  enrichedSummary?: string;    // AI 生成的内容摘要
  keyTopics?: string[];        // 关键主题自动提取
}

// ============= User Profile & Personalization =============
/**
 * 学习风格偏好 - 认知心理学研究
 */
export interface LearnerProfile {
  userId: string;
  
  // 基础信息
  displayName?: string;
  createdAt: number;
  updatedAt: number;
  
  // 学习风格与习惯
  preferredLearningStyle?: 'visual' | 'auditory' | 'kinesthetic' | 'reading-writing' | 'mixed';
  preferredPaceLevel?: 'slow' | 'medium' | 'fast';
  studySchedule?: {
    preferredHours?: string[];  // 偏好学习时段
    averageDailyMinutes?: number;
  };
  
  // 理解方式偏好
  explanationPreferences?: {
    useAnalogies?: boolean;            // 偏好类比解释
    useStepByStep?: boolean;           // 偏好逐步拆解
    useExamples?: boolean;             // 偏好大量例题
    useVisualDiagrams?: boolean;       // 偏好图表
    preferredLanguageLevel?: 'simple' | 'formal' | 'technical';
  };
  
  // 强化学习的信息
  knownDifficulties?: string[];        // 已知的学习困难
  strengths?: string[];                // 学习优势
  previousMasteredTopics?: string[];   // 已掌握的主题
}

/**
 * 学习目标 - 每个项目的学习目标
 */
export interface LearningGoal {
  id: string;
  projectId: string;
  userId: string;
  
  title: string;
  description?: string;
  
  // 目标设定
  targetDate?: number;
  expectedDurationHours?: number;
  targetMasteryLevel?: 'familiar' | 'proficient' | 'expert';
  
  // 考试或评估相关
  assessmentType?: 'exam' | 'project' | 'presentation' | 'none';
  examTopics?: string[];       // 考试涉及的主题
  
  // 关键成果指标
  keyResults?: Array<{
    id: string;
    description: string;
    successCriteria: string;
  }>;
  
  createdAt: number;
  updatedAt: number;
  status: 'active' | 'completed' | 'abandoned';
}

/**
 * 长期记忆条目 - 系统自动维护
 * 记录学生的学习轨迹、常见误区、掌握进度
 */
export interface LongTermMemory {
  id: string;
  userId: string;
  
  // 记忆内容
  topic: string;
  key: string;                 // 可检索的键
  value: Record<string, unknown>; // 实际记忆的内容
  
  // 记忆类型
  type: 'concept_understanding' | 'mistake' | 'mastery' | 'clarification' | 'resource';
  
  // 时间与频率
  firstOccurrenceAt: number;
  lastOccurrenceAt: number;
  occurrenceCount: number;
  
  // 关联信息
  sourceDocuments?: string[];  // 来源文档 ID
  relatedAnnotations?: string[];
  
  // 信心度
  confidence: number;          // 0-1，系统对该记忆的确定度
}

/**
 * 认知痕迹 - 学生的学习足迹
 * 每个批注、每次交互、每次理解深化都沉淀在这里
 */
export interface CognitiveBreadcrumb {
  id: string;
  userId: string;
  documentId: string;
  annotationId: string;
  
  // 痕迹类型
  type: 'first_confusion' | 'clarification' | 'deepening' | 'mastery' | 'regression' | 'application';
  
  // 内容
  description: string;         // "第一次在第3页卡住"、"通过类比理解了" 等
  timestamp: number;
  
  // 关联信息
  conversationId?: string;     // 相关的对话 ID
  relatedBreadcrumbs?: string[]; // 相关的其他痕迹
  
  // 这次交互的教学意义
  pedagogicalInsight?: string; // e.g., "学生容易混淆这两个概念"
}

/**
 * 交互历史 - 完整的用户行为记录
 * 用于主动式系统的决策：何时推送、何时提醒、何时深化
 */
export interface InteractionHistory {
  id: string;
  userId: string;
  documentId: string;
  
  // 交互内容
  type: 'view' | 'annotate' | 'question' | 'hover' | 'scroll_stop' | 'chat' | 'review';
  metadata?: Record<string, unknown>;
  
  // 时间信息
  timestamp: number;
  duration?: number;           // 该交互的持续时间（秒）
  
  // 位置信息
  position?: Position;
  paraphPosition?: number;     // 段落位置
  
  // 关联信息
  annotationId?: string;
  conversationMessageId?: string;
  
  // 前后文
  pageContext?: {
    beforeInteraction?: string;
    afterInteraction?: string;
  };
}

// ============= Project & Task Management =============
/**
 * 学习项目 - 一个学科/主题/考试的完整学习单元
 */
export interface LearningProject {
  id: string;
  userId: string;
  
  name: string;
  description?: string;
  folderPath: string;
  
  // 个性化定制
  learningGoal: LearningGoal;
  userPreferences: UserPreference;
  
  // 资源
  documents: Document[];
  
  // 进度与统计
  createdAt: number;
  updatedAt: number;
  lastAccessAt?: number;
  estimatedCompletionDate?: number;
  completionPercentage?: number;
  
  // 状态
  status: 'active' | 'archived' | 'completed';
}

/**
 * 用户偏好 - 项目级别的定制
 */
export interface UserPreference {
  projectId: string;
  userId: string;
  
  // 内容推荐偏好
  focusAreas?: string[];       // 重点关注的领域
  skipTopics?: string[];       // 跳过的主题
  
  // 交互偏好
  pushNotificationFrequency?: 'real-time' | 'daily' | 'weekly' | 'manual';
  allowProactiveMessages?: boolean;
  
  // AI 导师的人格设置
  tutorPersonality?: 'encouraging' | 'challenging' | 'socratic' | 'neutral';
  feedbackDetailLevel?: 'concise' | 'moderate' | 'detailed';
  learningStyleForProject?: 'visual' | 'auditory' | 'kinesthetic' | 'reading-writing' | 'mixed';
  
  // 难度自适应
  difficultyLevel?: 'beginner' | 'intermediate' | 'advanced';
  autoAdjustDifficulty?: boolean;
  
  // 记录时间
  updatedAt: number;
}

// ============= Agent & Proactive System =============
/**
 * 主动式代理任务
 */
export interface ProactiveAgentTask {
  id: string;
  projectId: string;
  userId: string;
  
  // 任务类型
  type: 'content_enrichment' | 'knowledge_retrieval' | 'question_generation' 
      | 'progress_check' | 'confusion_detection' | 'resource_recommendation'
      | 'learning_reminder' | 'misconception_correction';
  
  // 目标
  targetDocumentId?: string;
  targetAnnotationId?: string;
  targetTopic?: string;
  
  // 执行状态
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: number;
  executedAt?: number;
  scheduledFor?: number;      // 计划执行时间
  
  // 优先级与配置
  priority: number;             // 0-100
  maxRetries?: number;
  
  // 结果
  result?: {
    content?: string;
    resources?: string[];
    suggestedActions?: string[];
    timestamp?: number;
  };
  
  error?: string;
}
