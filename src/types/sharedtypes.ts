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
  demoScenarioId?: string;
  demoProcessingMode?: 'layered-annotation' | 'study-brief' | 'raw-only' | 'custom';
  demoProcessingLabel?: string;
  demoStatus?: 'idle' | 'processing' | 'completed';
}

// --- 前后端联调 API 类型 ---
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ApiDocument {
  id: number;
  projectId?: number;
  docHash: string;
  filename: string;
  status: DocumentStatus;
  createdAt: string;
  updatedAt?: string;
  fileUrl?: string;
}

export interface ApiChatHistoryMessage {
  id?: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  docHash?: string;
}

export interface ApiChatResponse {
  message: string;
  content?: string;
  annotationId?: string;
  knowledgePoint?: string;
  type?: string;
}

export interface ApiHealthResponse {
  status: string;
  service: string;
  timestamp: string;
  pythonAI?: boolean;
}

export interface ApiSystemStatus {
  services: {
    database: boolean;
    redis: boolean;
    python_ai: boolean;
    cpp_sandbox: boolean;
  };
  uptime: number;
  version: string;
  timestamp: string;
}

export type UploadProcessingMode = 'annotate' | 'summary' | 'nothing' | 'other';

export interface KnowledgeBaseDocument {
  id: string;
  kbId: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  processingMode: UploadProcessingMode;
  processingLabel: string;
  kind?: 'source' | 'generated';
  generatedType?: 'annotated-view' | 'study-brief' | 'outline';
}

export type AnnotationColorGroup = 'yellow' | 'red' | 'blue' | 'green' | 'purple';

export interface RenderReadyLegendItem {
  key: AnnotationColorGroup;
  label: string;
  color: string;
}

export interface RenderReadyMeta {
  documentId: string;
  title: string;
  course: string;
  week: string;
  mode: 'study_default' | 'exam_review' | 'paper_analysis' | 'book_report' | 'custom';
  userGoal: string;
}

export interface RenderReadyHighlight {
  id: string;
  text: string;
  colorGroup: AnnotationColorGroup;
  semanticType: string;
}

export interface RenderReadySidebarNote {
  title: string;
  paragraphFunction: string;
  logicRole: string;
  layer1: string;
  layer2: string;
  layer3: string;
  worthNoticing: string;
  possibleWeakness: string;
}

export interface RenderReadyParagraph {
  id: string;
  text: string;
  highlights: RenderReadyHighlight[];
  sidebarNote: RenderReadySidebarNote;
}

export interface RenderReadySection {
  id: string;
  title: string;
  paragraphs: RenderReadyParagraph[];
}

export interface RenderReadySummary {
  logicChain: string[];
  oneSentenceClaim: string;
  strongestPoint: string;
  weakestPoint: string;
}

export interface RenderReadyAnnotationDocument {
  schemaVersion: string;
  meta: RenderReadyMeta;
  legend: RenderReadyLegendItem[];
  sections: RenderReadySection[];
  summary: RenderReadySummary;
}

export interface DemoImportOption {
  id: string;
  label: string;
  description: string;
  processingMode: 'layered-annotation' | 'study-brief' | 'raw-only' | 'custom';
  processingLabel: string;
}

export interface DemoAssistantRule {
  id: string;
  keywords: string[];
  thinkingSteps: string[];
  streamChunks: string[];
}

export interface DemoScenario {
  id: string;
  triggerFiles: string[];
  detectedTitle: string;
  detectedDescription: string;
  options: DemoImportOption[];
  processingSteps: string[];
  annotatedDocument: RenderReadyAnnotationDocument;
  assistant: {
    initialMessages: ApiChatHistoryMessage[];
    quickActions: string[];
    rules: DemoAssistantRule[];
    defaultThinkingSteps: string[];
    defaultStreamChunks: string[];
  };
}
