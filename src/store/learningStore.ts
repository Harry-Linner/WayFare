import { atom } from 'nanostores';
import type { Annotation, KnowledgeBase } from '../types/sharedtypes';

/**
 * 状态中心：用于中间阅读区与右侧 AI 对话框的解耦通信
 */

// 1. 当前被选中的批注（初始为 null）
// 当用户点击中间阅读区的气泡时，这里会存储对应的批注数据
export const activeAnnotation = atom<Annotation | null>(null);

// 2. AI 对话框的开关状态（初始为 true，方便调试看样式）
export const isChatOpen = atom<boolean>(true);

// 3. 辅助函数：由气泡组件触发
export function setActiveAnnotation(ann: Annotation) {
  console.log("Store: 激活知识点 ->", ann.knowledgePoint);
  activeAnnotation.set(ann);
  isChatOpen.set(true);
}

// 4. 清除函数：点击空白处或关闭对话时使用
export function clearActiveAnnotation() {
  activeAnnotation.set(null);
}

// 5. 知识库列表
export const knowledgeBases = atom<KnowledgeBase[]>([
  {
    id: 'math-101',
    name: '数据结构基础',
    description: '计算机科学基础课程，涵盖树、图、排序等核心概念',
    progress: 75,
    lastAccessed: '2025-11-24',
    documentCount: 12,
    color: 'bg-brand-blue',
    icon: '🌳',
    purpose: 'long-term',
    subject: 'computer-science',
    creationMethod: 'create',
    createdAt: '2025-11-20T10:00:00Z'
  },
  {
    id: 'os-intro',
    name: '操作系统导论',
    description: '进程管理、内存管理、文件系统等操作系统核心概念',
    progress: 45,
    lastAccessed: '2025-11-23',
    documentCount: 8,
    color: 'bg-priority-important',
    icon: '💻',
    purpose: 'long-term',
    subject: 'computer-science',
    creationMethod: 'create',
    createdAt: '2025-11-18T14:30:00Z'
  },
  {
    id: 'network-basic',
    name: '计算机网络基础',
    description: 'TCP/IP协议栈、网络分层、HTTP协议等网络知识',
    progress: 30,
    lastAccessed: '2025-11-22',
    documentCount: 15,
    color: 'bg-priority-critical',
    icon: '🌐',
    purpose: 'long-term',
    subject: 'computer-science',
    creationMethod: 'create',
    createdAt: '2025-11-15T09:15:00Z'
  }
]);

// 6. 添加新知识库
export function addKnowledgeBase(kb: Omit<KnowledgeBase, 'id' | 'createdAt' | 'lastAccessed'>) {
  try {
    const newKb: KnowledgeBase = {
      ...kb,
      id: `kb-${Date.now()}`,
      createdAt: new Date().toISOString(),
      lastAccessed: new Date().toISOString(),
      progress: 0,
      documentCount: 0
    };
    
    const currentKbs = knowledgeBases.get();
    const updatedKbs = [...currentKbs, newKb];
    
    // 先设置新状态
    knowledgeBases.set(updatedKbs);
    
    console.log('新增知识库:', newKb);
    console.log('更新后的知识库列表长度:', updatedKbs.length);
    
    // 延迟触发自定义事件，确保状态已经完全更新
    setTimeout(() => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('knowledgebase:added', { 
          detail: { knowledgeBase: newKb, allKnowledgeBases: updatedKbs }
        }));
        console.log('已触发自定义事件: knowledgebase:added');
      }
    }, 0);
    
    return newKb;
  } catch (error) {
    console.error('添加知识库失败:', error);
    throw error;
  }
}

// 7. 更新知识库访问时间
export function updateKnowledgeBaseAccess(kbId: string) {
  const currentKbs = knowledgeBases.get();
  const updatedKbs = currentKbs.map(kb => 
    kb.id === kbId ? { ...kb, lastAccessed: new Date().toISOString() } : kb
  );
  knowledgeBases.set(updatedKbs);
}