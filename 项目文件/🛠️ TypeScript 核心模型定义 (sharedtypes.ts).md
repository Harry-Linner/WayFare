## 🛠️ TypeScript 核心模型定义 (`shared/types.ts`)

我们将模型分为：用户画像、知识库实体、交互内容、以及文件操作。

### 1. 用户与项目画像 (Personas)

TypeScript

```
// 全局用户画像
export interface UserPersona {
  uid: string;
  goal: 'structured' | 'casual' | 'exam_oriented'; // 学习目标：系统、随性、应试
  preferences: {
    difficulty: number; // 1-5 难度偏好
    aiRole: string;     // 当前关联的 AI 角色卡 ID
    language: string;
  };
}

// 知识库专属画像
export interface KnowledgeBasePersona {
  kbId: string;
  targetExam?: string;    // 例如："2026计算机统考408" 或 "大学物理期末"
  rootPath: string;     // 物理路径，用于 C++/Go 监控
  skillIds: string[];   // 该库启用的技能（如：生成路线图、自动批注）
  isStrict: boolean;    // 是否严格管理（决定是否自动生成大量辅助文件）
}
```

### 2. 内容与气泡批注 (Content & Annotations)

这是三栏布局中“中间阅读栏”的核心。

TypeScript

```
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}
export interface Annotation {
  id: string;
  contentId: string;
  offset: number; 
  
    // --- 核心修正：PDF 物理定位 ---
  pageNumber: number;        // 批注所在的 PDF 页码
  boundingBox: BoundingBox;  // C++ 解析出的物理坐标，前端据此做 position: absolute
  
  // --- 核心修正：备考场景元数据 ---
  knowledgePoint: string;    // 提取的知识点名称（如："AVL树的旋转"）
  frequency: number;        // 历年卷考频统计（如：近5年考了 3 次）
  
  // --- 新增：优先级相关字段 ---
  /** * 优先级类型：
   * critical: 核心考点/必看（红色系）
   * important: 重要补充/常见问题（橙/黄色系）
   * normal: 普通注释/百科扩展（蓝色系）
   * low: 细节说明/趣味补充（灰色系）
   */
  priority: 'critical' | 'important' | 'normal' | 'low';

  /**
   * 权重分值 (0.0 - 1.0)：
   * 用于控制颜色的“深浅”或气泡的“大小/透明度”。
   * 例如：0.9 表示该级别下非常重要的内容。
   */
  weight: number; 
  
  // --- 原有字段 ---
  type: 'summary' | 'qa' | 'concept' | 'quiz';
  aiComment: string;
  contextQuote: string;
}

export interface DocumentContent {
  id: string;
  title: string;
  rawText: string;
  annotations: Annotation[]; // 该文档下所有的气泡点
}
```

### 3. AI 对话上下文 (AI Interaction)

TypeScript

```
export interface ChatMessage {
  id: string;                // 消息本身的唯一 ID
  conversationId: string;    // 所属的会话 ID，用于后端关联上下文
  role: 'user' | 'assistant' | 'system';
  content: string;
  // 重点：关联的批注 ID 或原文片段，实现“点击气泡提问”
  relatedAnnotationId?: string; 
  suggestedActions?: string[]; // AI 给出的下一步建议
}
```

### 4. 文件操作协议 (File Events)

用于处理拖入文件或外部复制进来的交互。

TypeScript

```
export interface FileActionRequest {
  fileName: string;
  filePath: string;
  source: 'drag_and_drop' | 'external_copy'; // 来源
  suggestedOps: ('nothing' | 'annotate' | 'note' | 'roadmap')[]; // 推荐操作
}
```