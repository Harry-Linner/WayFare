// --- 用户与项目画像 ---
export interface UserPersona {
  uid: string;
  goal: 'structured' | 'casual' | 'exam_oriented'; 
  preferences: {
    difficulty: number; // 1-5
    aiRole: string;     
    language: string;
  };
}

export interface KnowledgeBasePersona {
  kbId: string;
  targetExam?: string;    
  rootPath: string;     
  skillIds: string[];   
  isStrict: boolean;    
}

// --- 核心批注与坐标 ---
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Annotation {
  id: string;
  contentId: string;
  pageNumber: number;        
  boundingBox: BoundingBox;  
  knowledgePoint: string;    
  frequency: number;        
  priority: 'critical' | 'important' | 'normal' | 'low';
  weight: number; // 0.0 - 1.0
  type: 'summary' | 'qa' | 'concept' | 'quiz';
  aiComment: string;
  contextQuote: string;
}

// --- AI 交互 ---
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  relatedAnnotationId?: string; 
  suggestedActions?: string[]; 
}

// --- 知识库 ---
export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  progress: number;
  lastAccessed: string;
  documentCount: number;
  color: string;
  icon: string;
  purpose: string;
  subject?: string;
  learningGoals?: string;
  studyTime?: 'short' | 'medium' | 'long';
  creationMethod: 'import' | 'create';
  folderName?: string;
  createdAt: string;
}