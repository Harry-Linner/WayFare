import { atom } from 'nanostores';
import type { Annotation, KnowledgeBase } from '../types/sharedtypes';

export const activeAnnotation = atom<Annotation | null>(null);
export const isChatOpen = atom<boolean>(true);

export function setActiveAnnotation(ann: Annotation) {
  console.log('Store: 激活知识点 ->', ann.knowledgePoint);
  activeAnnotation.set(ann);
  isChatOpen.set(true);
}

export function clearActiveAnnotation() {
  activeAnnotation.set(null);
}

const KNOWLEDGE_BASES_STORAGE_KEY = 'wayfare:knowledge-bases';

const defaultKnowledgeBases: KnowledgeBase[] = [
  {
    id: 'math-101',
    name: '数据结构基础',
    description: '计算机科学基础课程，涵盖树、图、排序等核心概念',
    progress: 75,
    lastAccessed: '2025-11-24',
    documentCount: 12,
    color: 'bg-brand-blue',
    icon: '📦',
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
    description: 'TCP/IP 协议栈、网络分层、HTTP 协议等网络知识',
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
];

function loadKnowledgeBases(): KnowledgeBase[] {
  if (typeof window === 'undefined') {
    return defaultKnowledgeBases;
  }

  try {
    const raw = window.localStorage.getItem(KNOWLEDGE_BASES_STORAGE_KEY);
    if (!raw) {
      return defaultKnowledgeBases;
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : defaultKnowledgeBases;
  } catch (error) {
    console.error('加载知识库列表失败，已回退到默认数据', error);
    return defaultKnowledgeBases;
  }
}

function persistKnowledgeBases(kbs: KnowledgeBase[]) {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.setItem(KNOWLEDGE_BASES_STORAGE_KEY, JSON.stringify(kbs));
  } catch (error) {
    console.error('保存知识库列表失败', error);
  }
}

export const knowledgeBases = atom<KnowledgeBase[]>(loadKnowledgeBases());

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

    knowledgeBases.set(updatedKbs);
    persistKnowledgeBases(updatedKbs);

    console.log('新增知识库', newKb);
    console.log('更新后的知识库列表长度', updatedKbs.length);

    setTimeout(() => {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('knowledgebase:added', {
            detail: { knowledgeBase: newKb, allKnowledgeBases: updatedKbs }
          })
        );
        console.log('已触发自定义事件: knowledgebase:added');
      }
    }, 0);

    return newKb;
  } catch (error) {
    console.error('添加知识库失败', error);
    throw error;
  }
}

export function deleteKnowledgeBase(kbId: string) {
  const currentKbs = knowledgeBases.get();
  const updatedKbs = currentKbs.filter((kb) => kb.id !== kbId);

  knowledgeBases.set(updatedKbs);
  persistKnowledgeBases(updatedKbs);

  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('knowledgebase:deleted', {
        detail: { kbId, allKnowledgeBases: updatedKbs }
      })
    );
  }
}

export function updateKnowledgeBaseAccess(kbId: string) {
  const currentKbs = knowledgeBases.get();
  const updatedKbs = currentKbs.map(kb =>
    kb.id === kbId ? { ...kb, lastAccessed: new Date().toISOString() } : kb
  );
  knowledgeBases.set(updatedKbs);
  persistKnowledgeBases(updatedKbs);
}
