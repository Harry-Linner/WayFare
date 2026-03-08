/// Tauri 命令调用 Hook
/// 这个 hook 提供了对所有后端 Tauri 命令的类型安全调用

import { invoke } from '@tauri-apps/api/core';
import type { EnhancedAnnotation } from '../types';

// ============= Types =============

export interface StallDetectionResult {
  is_stalled: boolean;
  confidence: number;
  suggested_help_type: string[];
  priority: string;
}

export interface MisconceptionAnalysis {
  concept: string;
  has_misconception: boolean;
  error_rate: number;
  probable_misconceptions: string[];
  suggested_explanations: string[];
}

export interface AnnotationEnrichment {
  annotation_id: string;
  scaffolding?: {
    analogy?: string;
    key_questions: string[];
    decomposition: string[];
  };
  priority: string;
  related_resources: string[];
}

export interface GeneratedQuestion {
  question: string;
  question_type: string;
  difficulty: string;
  target_concepts: string[];
}

export interface SearchResult {
  title: string;
  url: string;
  source: string;
  relevance_score: number;
  summary: string;
}

export interface LearningProgress {
  total_annotations: number;
  topics_covered: number;
  mastery_percentage: number;
  weak_areas: string[];
  recommended_focus: string;
}

// ============= Hook =============

export function useTauriCommands() {
  /**
   * 初始化用户档案
   */
  const initializeUserProfile = async (
    userId: string,
    learningStyle: string,
    pace: string
  ): Promise<string> => {
    try {
      const result = await invoke<string>('initialize_user_profile', {
        user_id: userId,
        learning_style: learningStyle,
        preferred_pace: pace,
      });
      return result;
    } catch (error) {
      console.error('Failed to initialize user profile:', error);
      throw error;
    }
  };

  /**
   * 检测学生是否卡住（超过180秒）
   */
  const detectStalledInteraction = async (
    documentId: string,
    interactionTimeMs: number,
    contentSnippet: string
  ): Promise<StallDetectionResult> => {
    try {
      const result = await invoke<StallDetectionResult>(
        'detect_stalled_interaction',
        {
          document_id: documentId,
          user_interaction_time_ms: interactionTimeMs,
          content_snippet: contentSnippet,
        }
      );
      return result;
    } catch (error) {
      console.error('Failed to detect stalled interaction:', error);
      throw error;
    }
  };

  /**
   * 识别学生的误解
   */
  const identifyMisconception = async (
    userId: string,
    conceptName: string,
    interactionHistory: Array<{
      document_id: string;
      interaction_type: string;
      duration?: number;
      timestamp: number;
    }>
  ): Promise<MisconceptionAnalysis> => {
    try {
      const result = await invoke<MisconceptionAnalysis>(
        'identify_misconception',
        {
          user_id: userId,
          concept_name: conceptName,
          interaction_history: interactionHistory,
        }
      );
      return result;
    } catch (error) {
      console.error('Failed to identify misconception:', error);
      throw error;
    }
  };

  /**
   * 增强批注（添加认知支架和外部资源）
   */
  const enrichAnnotations = async (
    documentId: string,
    includeExternalResources: boolean = false
  ): Promise<AnnotationEnrichment[]> => {
    try {
      const result = await invoke<AnnotationEnrichment[]>(
        'enrich_annotations',
        {
          document_id: documentId,
          include_external_resources: includeExternalResources,
        }
      );
      return result;
    } catch (error) {
      console.error('Failed to enrich annotations:', error);
      throw error;
    }
  };

  /**
   * 生成学习问题
   */
  const generateQuestions = async (
    documentId: string,
    count: number = 3,
    difficulty?: string
  ): Promise<GeneratedQuestion[]> => {
    try {
      const result = await invoke<GeneratedQuestion[]>(
        'generate_questions',
        {
          document_id: documentId,
          count,
          difficulty,
        }
      );
      return result;
    } catch (error) {
      console.error('Failed to generate questions:', error);
      throw error;
    }
  };

  /**
   * 搜索学习资源（视频、文章、例题等）
   */
  const searchLearningResources = async (
    topic: string,
    resourceTypes: string[] = ['video', 'article', 'examples']
  ): Promise<SearchResult[]> => {
    try {
      const result = await invoke<SearchResult[]>(
        'search_learning_resources',
        {
          topic,
          resource_types: resourceTypes,
        }
      );
      return result;
    } catch (error) {
      console.error('Failed to search learning resources:', error);
      throw error;
    }
  };

  /**
   * 分析学习进度
   */
  const analyzeLearningProgress = async (
    projectId: string
  ): Promise<LearningProgress> => {
    try {
      const result = await invoke<LearningProgress>(
        'analyze_learning_progress',
        {
          project_id: projectId,
        }
      );
      return result;
    } catch (error) {
      console.error('Failed to analyze learning progress:', error);
      throw error;
    }
  };

  /**
   * 生成学习计划
   */
  const generateLearningPlan = async (
    projectId: string,
    targetDate: number
  ): Promise<string> => {
    try {
      const result = await invoke<string>('generate_learning_plan', {
        project_id: projectId,
        target_date: targetDate,
      });
      return result;
    } catch (error) {
      console.error('Failed to generate learning plan:', error);
      throw error;
    }
  };

  /**
   * 调度复习提醒
   */
  const scheduleReviewReminder = async (
    userId: string,
    conceptName: string,
    reviewTime: number
  ): Promise<string> => {
    try {
      const result = await invoke<string>('schedule_review_reminder', {
        user_id: userId,
        concept_name: conceptName,
        review_time: reviewTime,
      });
      return result;
    } catch (error) {
      console.error('Failed to schedule review reminder:', error);
      throw error;
    }
  };

  /**
   * 保存文档到数据库
   */
  const saveDocument = async (
    id: string,
    userId: string,
    name: string,
    path: string,
    docType: string,
    content: string
  ): Promise<string> => {
    try {
      return await invoke<string>('save_document', {
        id,
        user_id: userId,
        name,
        path,
        doc_type: docType,
        content,
      });
    } catch (error) {
      console.error('Failed to save document:', error);
      throw error;
    }
  };

  /**
   * 获取文档的所有批注
   */
  const getDocumentAnnotations = async (documentId: string): Promise<EnhancedAnnotation[]> => {
    try {
      return await invoke<EnhancedAnnotation[]>('get_document_annotations', {
        document_id: documentId,
      });
    } catch (error) {
      console.error('Failed to get document annotations:', error);
      throw error;
    }
  };

  /**
   * 保存批注到数据库
   */
  const saveAnnotation = async (
    id: string,
    documentId: string,
    sourceText: string | null,
    content: string,
    positionX: number,
    positionY: number,
    page: number | null,
    annotationType: string,
    priority: string,
    category?: string,
    pedagogicalType?: string
  ): Promise<string> => {
    try {
      return await invoke<string>('save_annotation', {
        id,
        document_id: documentId,
        source_text: sourceText,
        content,
        position_x: positionX,
        position_y: positionY,
        page,
        annotation_type: annotationType,
        priority,
        category,
        pedagogical_type: pedagogicalType,
      });
    } catch (error) {
      console.error('Failed to save annotation:', error);
      throw error;
    }
  };

  /**
   * 记录学习历程
   */
  const recordLearningTrace = async (
    userId: string,
    concept: string,
    eventType: string
  ): Promise<string> => {
    try {
      return await invoke<string>('record_learning_trace', {
        user_id: userId,
        concept,
        event_type: eventType,
      });
    } catch (error) {
      console.error('Failed to record learning trace:', error);
      throw error;
    }
  };

  /**
   * 分析文档内容
   */
  const analyzeDocumentContent = async (
    documentId: string,
    content: string,
    docType: string
  ): Promise<Record<string, unknown>> => {
    try {
      return await invoke<Record<string, unknown>>('analyze_document_content', {
        document_id: documentId,
        content,
        doc_type: docType,
      });
    } catch (error) {
      console.error('Failed to analyze document content:', error);
      throw error;
    }
  };

  /**
   * 获取补充资源
   */
  const fetchSupplementaryResources = async (
    topic: string,
    difficulty: string
  ): Promise<SearchResult[]> => {
    try {
      return await invoke<SearchResult[]>('fetch_supplementary_resources', {
        topic,
        difficulty,
      });
    } catch (error) {
      console.error('Failed to fetch supplementary resources:', error);
      throw error;
    }
  };

  return {
    initializeUserProfile,
    detectStalledInteraction,
    identifyMisconception,
    enrichAnnotations,
    generateQuestions,
    searchLearningResources,
    analyzeLearningProgress,
    generateLearningPlan,
    scheduleReviewReminder,
    saveDocument,
    getDocumentAnnotations,
    saveAnnotation,
    recordLearningTrace,
    analyzeDocumentContent,
    fetchSupplementaryResources,
  };
}

// ============= Standalone API Wrapper =============

/**
 * 如果需要在非 React 上下文中使用，可以直接调用这些函数
 */
export const tauriAPI = {
  async initializeUserProfile(userId: string, learningStyle: string, pace: string) {
    return invoke<string>('initialize_user_profile', {
      user_id: userId,
      learning_style: learningStyle,
      preferred_pace: pace,
    });
  },

  async detectStalledInteraction(
    documentId: string,
    interactionTimeMs: number,
    contentSnippet: string
  ) {
    return invoke<StallDetectionResult>('detect_stalled_interaction', {
      document_id: documentId,
      user_interaction_time_ms: interactionTimeMs,
      content_snippet: contentSnippet,
    });
  },

  async identifyMisconception(
    userId: string,
    conceptName: string,
    interactionHistory: Array<{
      document_id: string;
      interaction_type: string;
      duration?: number;
      timestamp: number;
    }>
  ) {
    return invoke<MisconceptionAnalysis>('identify_misconception', {
      user_id: userId,
      concept_name: conceptName,
      interaction_history: interactionHistory,
    });
  },

  async enrichAnnotations(documentId: string, includeExternalResources: boolean = false) {
    return invoke<AnnotationEnrichment[]>('enrich_annotations', {
      document_id: documentId,
      include_external_resources: includeExternalResources,
    });
  },

  async generateQuestions(documentId: string, count: number = 3, difficulty?: string) {
    return invoke<GeneratedQuestion[]>('generate_questions', {
      document_id: documentId,
      count,
      difficulty,
    });
  },

  async searchLearningResources(
    topic: string,
    resourceTypes: string[] = ['video', 'article', 'examples']
  ) {
    return invoke<SearchResult[]>('search_learning_resources', {
      topic,
      resource_types: resourceTypes,
    });
  },

  async analyzeLearningProgress(projectId: string) {
    return invoke<LearningProgress>('analyze_learning_progress', {
      project_id: projectId,
    });
  },

  async generateLearningPlan(projectId: string, targetDate: number) {
    return invoke<string>('generate_learning_plan', {
      project_id: projectId,
      target_date: targetDate,
    });
  },

  async scheduleReviewReminder(userId: string, conceptName: string, reviewTime: number) {
    return invoke<string>('schedule_review_reminder', {
      user_id: userId,
      concept_name: conceptName,
      review_time: reviewTime,
    });
  },
};
