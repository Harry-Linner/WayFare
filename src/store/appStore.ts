import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  EnhancedAnnotation,
  Document,
  ChatMessage,
  ConversationSession,
  LearnerProfile,
  LearningGoal,
  LearningProject,
  UserPreference,
  LongTermMemory,
  CognitiveBreadcrumb,
  InteractionHistory,
  ProactiveAgentTask,
} from '../types';

// ============= Store-Specific Types =============

/**
 * 后台任务 - 由 Agent 或系统调度
 */
export interface BackgroundJob {
  id: string;
  projectId: string;
  type: 'parse' | 'analyze' | 'index' | 'enrich' | 'monitor';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  priority: number;
  createdAt: number;
  updatedAt: number;
  progress: number;
  error?: string;
  estimatedTimeRemaining?: number;
}

// ============= Zustand Store Interface =============

interface AppStore {
  // ========== User Profile & Personalization ==========
  currentUserId: string | null;
  setCurrentUserId: (userId: string) => void;
  
  learnerProfile: LearnerProfile | null;
  setLearnerProfile: (profile: LearnerProfile) => void;
  updateLearnerProfile: (updates: Partial<LearnerProfile>) => void;
  updateUserProfile: (updates: Partial<LearnerProfile>) => void; // alias

  // ========== Learning Projects ==========
  projects: LearningProject[];
  currentProjectId: string | null;
  
  addProject: (project: LearningProject) => void;
  createProject: (project: LearningProject) => void; // alias
  updateProject: (projectId: string, updates: Partial<LearningProject>) => void;
  removeProject: (projectId: string) => void;
  setCurrentProject: (projectId: string | null) => void;
  getProject: (projectId: string) => LearningProject | undefined;
  getCurrentProject: () => LearningProject | undefined;

  // ========== Learning Goals & Preferences ==========
  learningGoals: LearningGoal[];
  addLearningGoal: (goal: LearningGoal) => void;
  updateLearningGoal: (goalId: string, updates: Partial<LearningGoal>) => void;
  
  userPreferences: Record<string, UserPreference>; // projectId -> UserPreference
  setUserPreference: (preference: UserPreference) => void;
  getUserPreference: (projectId: string) => UserPreference | undefined;

  // ========== Documents ==========
  documents: Document[];
  currentDocument: Document | null;
  
  addDocument: (doc: Document) => void;
  removeDocument: (docId: string) => void;
  setCurrentDocument: (doc: Document | null) => void;
  updateDocument: (docId: string, updates: Partial<Document>) => void;
  getDocumentsByProject: (projectId: string) => Document[];

  // ========== Annotations (Enhanced) ==========
  annotations: EnhancedAnnotation[];
  addAnnotation: (annotation: EnhancedAnnotation) => void;
  updateAnnotation: (id: string, updates: Partial<EnhancedAnnotation>) => void;
  deleteAnnotation: (id: string) => void;
  getAnnotationsByDocument: (docId: string) => EnhancedAnnotation[];
  getAnnotationsByPriority: (
    docId: string,
    priority: string
  ) => EnhancedAnnotation[];
  getAnnotationsByConfidence: (
    docId: string,
    confidence: string
  ) => EnhancedAnnotation[];
  
  // 批量操作
  batchUpdateAnnotations: (
    annotationIds: string[],
    updates: Partial<EnhancedAnnotation>
  ) => void;

  // ========== Conversations & Chat ==========
  conversations: ConversationSession[];
  currentConversationId: string | null;
  
  createConversation: (conversation: ConversationSession) => void;
  setCurrentConversation: (conversationId: string | null) => void;
  addChatMessage: (conversationId: string, message: ChatMessage) => void;
  getConversationsByDocument: (docId: string) => ConversationSession[];
  getCurrentConversation: () => ConversationSession | undefined;

  // ========== Interaction History (Long-term) ==========
  interactionHistory: InteractionHistory[];
  recordInteraction: (interaction: Omit<InteractionHistory, 'id'> & { id?: string }) => void;
  getInteractionsByDocument: (docId: string) => InteractionHistory[];
  getInteractionsInTimeRange: (startTime: number, endTime: number) => InteractionHistory[];
  getInteractionsByType: (type: InteractionHistory['type']) => InteractionHistory[];

  // ========== Long-term Memory ==========
  longTermMemory: LongTermMemory[];
  addOrUpdateMemory: (memory: LongTermMemory) => void;
  getMemoryByTopic: (topic: string) => LongTermMemory[];
  getMemoryByKey: (key: string) => LongTermMemory | undefined;
  recordLearnerMistake: (topic: string, description: string) => void;
  recordMastery: (topic: string, description: string) => void;
  
  // 🔥 修复漏洞#8：添加时间维度查询，支持长期回溯
  getMemoriesInTimeRange: (startTime: number, endTime: number) => LongTermMemory[];
  getRecentMistakes: (days?: number) => LongTermMemory[];
  getMasteredTopics: () => string[];
  getStrugglingTopics: () => string[];
  getMemoryTimeline: (topic: string) => LongTermMemory[];

  // ========== Cognitive Breadcrumbs (Learning Traces) ==========
  breadcrumbs: CognitiveBreadcrumb[];
  addBreadcrumb: (breadcrumb: CognitiveBreadcrumb) => void;
  getBreadcrumbsByAnnotation: (annotationId: string) => CognitiveBreadcrumb[];
  getBreadcrumbsByType: (type: CognitiveBreadcrumb['type']) => CognitiveBreadcrumb[];

  // ========== Proactive Agent Tasks ==========
  agentTasks: ProactiveAgentTask[];
  addAgentTask: (task: ProactiveAgentTask) => void;
  updateAgentTask: (taskId: string, updates: Partial<ProactiveAgentTask>) => void;
  getAgentTasksByStatus: (status: ProactiveAgentTask['status']) => ProactiveAgentTask[];
  getAgentTasksByProject: (projectId: string) => ProactiveAgentTask[];
  getAgentTasksByType: (type: ProactiveAgentTask['type']) => ProactiveAgentTask[];

  // ========== Background Jobs ==========
  jobs: BackgroundJob[];
  addJob: (job: BackgroundJob) => void;
  updateJob: (id: string, updates: Partial<BackgroundJob>) => void;
  removeJob: (id: string) => void;
  getJobsByStatus: (status: BackgroundJob['status']) => BackgroundJob[];

  // ========== UI State ==========
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  
  interactionMonitorActive: boolean;
  setInteractionMonitorActive: (active: boolean) => void;
  
  showProactiveMessages: boolean;
  setShowProactiveMessages: (show: boolean) => void;

  // ========== Statistics & Analytics ==========
  getStudyStats: (projectId: string) => {
    totalAnnotations: number;
    totalInteractions: number;
    totalStudyTime: number;
    topicsReviewed: string[];
    averageConfidence: number;
  };

  // ========== Utility ==========
  clearAll: () => void;
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      // ========== User Profile ==========
      currentUserId: null,
      setCurrentUserId: (userId) => set({ currentUserId: userId }),
      
      learnerProfile: null,
      setLearnerProfile: (profile) => set({ learnerProfile: profile }),
      updateLearnerProfile: (updates) =>
        set((state) => ({
          learnerProfile: state.learnerProfile
            ? { ...state.learnerProfile, ...updates, updatedAt: Date.now() }
            : null,
        })),
      updateUserProfile: (updates) =>
        set((state) => ({
          learnerProfile: state.learnerProfile
            ? { ...state.learnerProfile, ...updates, updatedAt: Date.now() }
            : null,
        })),

      // ========== Learning Projects ==========
      projects: [],
      currentProjectId: null,
      
      addProject: (project) =>
        set((state) => ({
          projects: [...state.projects, project],
        })),
      createProject: (project) =>
        set((state) => ({
          projects: [...state.projects, project],
        })),
      
      updateProject: (projectId, updates) =>
        set((state) => ({
          projects: state.projects.map((p) =>
            p.id === projectId
              ? { ...p, ...updates, updatedAt: Date.now() }
              : p
          ),
        })),
      
      removeProject: (projectId) =>
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== projectId),
          currentProjectId:
            state.currentProjectId === projectId ? null : state.currentProjectId,
        })),
      
      setCurrentProject: (projectId) =>
        set({ currentProjectId: projectId }),
      
      getProject: (projectId) => {
        const state = get();
        return state.projects.find((p) => p.id === projectId);
      },
      
      getCurrentProject: () => {
        const state = get();
        return state.projects.find((p) => p.id === state.currentProjectId);
      },

      // ========== Learning Goals & Preferences ==========
      learningGoals: [],
      addLearningGoal: (goal) =>
        set((state) => ({
          learningGoals: [...state.learningGoals, goal],
        })),
      
      updateLearningGoal: (goalId, updates) =>
        set((state) => ({
          learningGoals: state.learningGoals.map((g) =>
            g.id === goalId
              ? { ...g, ...updates, updatedAt: Date.now() }
              : g
          ),
        })),
      
      userPreferences: {},
      setUserPreference: (preference) =>
        set((state) => ({
          userPreferences: {
            ...state.userPreferences,
            [preference.projectId]: preference,
          },
        })),
      
      getUserPreference: (projectId) => {
        const state = get();
        return state.userPreferences[projectId];
      },

      // ========== Documents ==========
      documents: [],
      currentDocument: null,
      
      addDocument: (doc) =>
        set((state) => ({
          documents: [...state.documents, doc],
        })),
      
      removeDocument: (docId) =>
        set((state) => ({
          documents: state.documents.filter((d) => d.id !== docId),
          currentDocument:
            state.currentDocument?.id === docId ? null : state.currentDocument,
        })),
      
      setCurrentDocument: (doc) =>
        set({ currentDocument: doc }),
      
      updateDocument: (docId, updates) =>
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.id === docId
              ? { ...doc, ...updates, updatedAt: Date.now() }
              : doc
          ),
          currentDocument:
            state.currentDocument?.id === docId
              ? { ...state.currentDocument, ...updates, updatedAt: Date.now() }
              : state.currentDocument,
        })),
      
      getDocumentsByProject: (projectId) => {
        const state = get();
        return state.documents.filter((d) => d.projectId === projectId);
      },

      // ========== Annotations (Enhanced) ==========
      annotations: [],
      
      addAnnotation: (annotation) =>
        set((state) => ({
          annotations: [...state.annotations, annotation],
        })),
      
      updateAnnotation: (id, updates) =>
        set((state) => ({
          annotations: state.annotations.map((a) =>
            a.id === id
              ? { ...a, ...updates, updatedAt: Date.now() }
              : a
          ),
        })),
      
      deleteAnnotation: (id) =>
        set((state) => ({
          annotations: state.annotations.filter((a) => a.id !== id),
        })),
      
      getAnnotationsByDocument: (docId) => {
        const state = get();
        return state.annotations.filter((a) => a.documentId === docId);
      },
      
      getAnnotationsByPriority: (docId, priority) => {
        const state = get();
        return state.annotations.filter(
          (a) => a.documentId === docId && a.priority === priority
        );
      },
      
      getAnnotationsByConfidence: (docId, confidence) => {
        const state = get();
        return state.annotations.filter(
          (a) => a.documentId === docId && a.confidence === confidence
        );
      },
      
      batchUpdateAnnotations: (annotationIds, updates) =>
        set((state) => ({
          annotations: state.annotations.map((a) =>
            annotationIds.includes(a.id)
              ? { ...a, ...updates, updatedAt: Date.now() }
              : a
          ),
        })),

      // ========== Conversations ==========
      conversations: [],
      currentConversationId: null,
      
      createConversation: (conversation) =>
        set((state) => ({
          conversations: [...state.conversations, conversation],
        })),
      
      setCurrentConversation: (conversationId) =>
        set({ currentConversationId: conversationId }),
      
      addChatMessage: (conversationId, message) =>
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: [...c.messages, message],
                  updatedAt: Date.now(),
                }
              : c
          ),
        })),
      
      getConversationsByDocument: (docId) => {
        const state = get();
        return state.conversations.filter((c) => c.documentId === docId);
      },
      
      getCurrentConversation: () => {
        const state = get();
        return state.conversations.find(
          (c) => c.id === state.currentConversationId
        );
      },

      // ========== Interaction History ==========
      interactionHistory: [],
      
      recordInteraction: (interaction) =>
        set((state) => ({
          interactionHistory: [
            ...state.interactionHistory,
            {
              id:
                interaction.id ||
                `interaction_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
              ...interaction,
            } as InteractionHistory,
          ],
        })),
      
      getInteractionsByDocument: (docId) => {
        const state = get();
        return state.interactionHistory.filter((i) => i.documentId === docId);
      },
      
      getInteractionsInTimeRange: (startTime, endTime) => {
        const state = get();
        return state.interactionHistory.filter(
          (i) => i.timestamp >= startTime && i.timestamp <= endTime
        );
      },
      
      getInteractionsByType: (type) => {
        const state = get();
        return state.interactionHistory.filter((i) => i.type === type);
      },

      // ========== Long-term Memory ==========
      longTermMemory: [],
      
      addOrUpdateMemory: (memory) =>
        set((state) => {
          const existingIndex = state.longTermMemory.findIndex(
            (m) => m.key === memory.key && m.userId === memory.userId
          );
          
          if (existingIndex >= 0) {
            const updated = [...state.longTermMemory];
            updated[existingIndex] = {
              ...memory,
              occurrenceCount:
                state.longTermMemory[existingIndex].occurrenceCount + 1,
              lastOccurrenceAt: Date.now(),
            };
            return { longTermMemory: updated };
          }
          
          return {
            longTermMemory: [...state.longTermMemory, memory],
          };
        }),
      
      getMemoryByTopic: (topic) => {
        const state = get();
        return state.longTermMemory.filter((m) => m.topic === topic);
      },
      
      getMemoryByKey: (key) => {
        const state = get();
        return state.longTermMemory.find((m) => m.key === key);
      },
      
      recordLearnerMistake: (topic, description) => {
        const state = get();
        const userId = state.currentUserId;
        if (!userId) return;
        
        get().addOrUpdateMemory({
          id: `mistake_${Date.now()}`,
          userId,
          topic,
          key: `mistake_${topic}`,
          value: { description, type: 'misconception' },
          type: 'mistake',
          firstOccurrenceAt: Date.now(),
          lastOccurrenceAt: Date.now(),
          occurrenceCount: 1,
          confidence: 0.3,
        });
      },
      
      recordMastery: (topic, description) => {
        const state = get();
        const userId = state.currentUserId;
        if (!userId) return;
        
        get().addOrUpdateMemory({
          id: `mastery_${Date.now()}`,
          userId,
          topic,
          key: `mastery_${topic}`,
          value: { description, masteredAt: Date.now() },
          type: 'mastery',
          firstOccurrenceAt: Date.now(),
          lastOccurrenceAt: Date.now(),
          occurrenceCount: 1,
          confidence: 0.9,
        });
      },

      // 🔥 修复漏洞#8：时间维度回溯实现
      getMemoriesInTimeRange: (startTime, endTime) => {
        const state = get();
        return state.longTermMemory.filter(
          (m) => m.lastOccurrenceAt >= startTime && m.lastOccurrenceAt <= endTime
        );
      },

      getRecentMistakes: (days = 30) => {
        const state = get();
        const cutoffTime = Date.now() - days * 24 * 60 * 60 * 1000;
        return state.longTermMemory.filter(
          (m) => m.type === 'mistake' && m.lastOccurrenceAt >= cutoffTime
        );
      },

      getMasteredTopics: () => {
        const state = get();
        return state.longTermMemory
          .filter((m) => m.type === 'mastery' && m.confidence > 0.8)
          .map((m) => m.topic);
      },

      getStrugglingTopics: () => {
        const state = get();
        const mistakeTopics = state.longTermMemory
          .filter((m) => m.type === 'mistake' && m.occurrenceCount >= 2)
          .map((m) => m.topic);
        return [...new Set(mistakeTopics)]; // 去重
      },

      getMemoryTimeline: (topic) => {
        const state = get();
        return state.longTermMemory
          .filter((m) => m.topic === topic)
          .sort((a, b) => a.firstOccurrenceAt - b.firstOccurrenceAt);
      },

      // ========== Cognitive Breadcrumbs ==========
      breadcrumbs: [],
      
      addBreadcrumb: (breadcrumb) =>
        set((state) => ({
          breadcrumbs: [...state.breadcrumbs, breadcrumb],
        })),
      
      getBreadcrumbsByAnnotation: (annotationId) => {
        const state = get();
        return state.breadcrumbs.filter((b) => b.annotationId === annotationId);
      },
      
      getBreadcrumbsByType: (type) => {
        const state = get();
        return state.breadcrumbs.filter((b) => b.type === type);
      },

      // ========== Proactive Agent Tasks ==========
      agentTasks: [],
      
      addAgentTask: (task) =>
        set((state) => ({
          agentTasks: [...state.agentTasks, task],
        })),
      
      updateAgentTask: (taskId, updates) =>
        set((state) => ({
          agentTasks: state.agentTasks.map((t) =>
            t.id === taskId
              ? { ...t, ...updates }
              : t
          ),
        })),
      
      getAgentTasksByStatus: (status) => {
        const state = get();
        return state.agentTasks.filter((t) => t.status === status);
      },
      
      getAgentTasksByProject: (projectId) => {
        const state = get();
        return state.agentTasks.filter((t) => t.projectId === projectId);
      },
      
      getAgentTasksByType: (type) => {
        const state = get();
        return state.agentTasks.filter((t) => t.type === type);
      },

      // ========== Background Jobs ==========
      jobs: [],
      
      addJob: (job) =>
        set((state) => ({
          jobs: [...state.jobs, job],
        })),
      
      updateJob: (id, updates) =>
        set((state) => ({
          jobs: state.jobs.map((j) =>
            j.id === id ? { ...j, ...updates, updatedAt: Date.now() } : j
          ),
        })),
      
      removeJob: (id) =>
        set((state) => ({
          jobs: state.jobs.filter((j) => j.id !== id),
        })),
      
      getJobsByStatus: (status) => {
        const state = get();
        return state.jobs.filter((j) => j.status === status);
      },

      // ========== UI State ==========
      sidebarOpen: true,
      setSidebarOpen: (open) =>
        set({ sidebarOpen: open }),
      
      interactionMonitorActive: true,
      setInteractionMonitorActive: (active) =>
        set({ interactionMonitorActive: active }),
      
      showProactiveMessages: true,
      setShowProactiveMessages: (show) =>
        set({ showProactiveMessages: show }),

      // ========== Statistics ==========
      getStudyStats: (projectId) => {
        const state = get();
        const projectAnnotations = state.annotations.filter(
          (a) =>
            state.documents
              .filter((d) => d.projectId === projectId)
              .map((d) => d.id)
              .includes(a.documentId)
        );
        
        const projectInteractions = state.interactionHistory.filter(
          (i) =>
            state.documents
              .filter((d) => d.projectId === projectId)
              .map((d) => d.id)
              .includes(i.documentId)
        );
        
        const totalStudyTime = projectInteractions.reduce(
          (sum, i) => sum + (i.duration || 0),
          0
        );
        
        const averageConfidence =
          projectAnnotations.length > 0
            ? projectAnnotations.reduce((sum, a) => sum + (a.confidence ? 0.5 : 0), 0) /
              projectAnnotations.length
            : 0;
        
        return {
          totalAnnotations: projectAnnotations.length,
          totalInteractions: projectInteractions.length,
          totalStudyTime,
          topicsReviewed: [...new Set(projectAnnotations.map((a) => a.category || 'general'))],
          averageConfidence,
        };
      },

      // ========== Utility ==========
      clearAll: () =>
        set({
          currentUserId: null,
          learnerProfile: null,
          projects: [],
          currentProjectId: null,
          learningGoals: [],
          userPreferences: {},
          documents: [],
          currentDocument: null,
          annotations: [],
          conversations: [],
          currentConversationId: null,
          interactionHistory: [],
          longTermMemory: [],
          breadcrumbs: [],
          agentTasks: [],
          jobs: [],
        }),
    }),
    {
      name: 'wayfare-store',
      partialize: (state) => ({
        currentUserId: state.currentUserId,
        learnerProfile: state.learnerProfile,
        projects: state.projects,
        currentProjectId: state.currentProjectId,
        learningGoals: state.learningGoals,
        userPreferences: state.userPreferences,
        documents: state.documents,
        annotations: state.annotations,
        conversations: state.conversations,
        interactionHistory: state.interactionHistory,
        longTermMemory: state.longTermMemory,
        breadcrumbs: state.breadcrumbs,
        agentTasks: state.agentTasks,
        jobs: state.jobs,
        sidebarOpen: state.sidebarOpen,
        interactionMonitorActive: state.interactionMonitorActive,
        showProactiveMessages: state.showProactiveMessages,
      }),
    }
  )
);
