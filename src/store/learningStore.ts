import { atom } from 'nanostores';
import type { Annotation, KnowledgeBase } from '../types/sharedtypes';

const STORAGE_KEY = 'wayfare:knowledge-bases';
const KNOWLEDGE_BASES_UPDATED_EVENT = 'knowledgebases:updated';

const DEFAULT_KNOWLEDGE_BASES: KnowledgeBase[] = [
  {
    id: 'math-101',
    name: '数据结构基础',
    description: '计算机科学基础课程，涵盖树、图、排序等核心概念。',
    progress: 75,
    lastAccessed: '2026-03-12T10:00:00.000Z',
    documentCount: 12,
    color: 'bg-brand-blue',
    icon: '📘',
    purpose: 'long-term',
    subject: 'computer-science',
    creationMethod: 'create',
    createdAt: '2026-03-01T10:00:00.000Z'
  },
  {
    id: 'os-intro',
    name: '操作系统导论',
    description: '进程管理、内存管理、文件系统等操作系统核心内容。',
    progress: 45,
    lastAccessed: '2026-03-11T14:30:00.000Z',
    documentCount: 8,
    color: 'bg-priority-important',
    icon: '💻',
    purpose: 'long-term',
    subject: 'computer-science',
    creationMethod: 'create',
    createdAt: '2026-02-25T14:30:00.000Z'
  },
  {
    id: 'network-basic',
    name: '计算机网络基础',
    description: 'TCP/IP 协议栈、网络分层、HTTP 协议等网络知识。',
    progress: 30,
    lastAccessed: '2026-03-10T09:15:00.000Z',
    documentCount: 15,
    color: 'bg-priority-critical',
    icon: '🌐',
    purpose: 'long-term',
    subject: 'computer-science',
    creationMethod: 'create',
    createdAt: '2026-02-20T09:15:00.000Z'
  }
];

export const activeAnnotation = atom<Annotation | null>(null);
export const isChatOpen = atom<boolean>(true);
export const knowledgeBases = atom<KnowledgeBase[]>(DEFAULT_KNOWLEDGE_BASES);

type NewKnowledgeBaseInput = Omit<KnowledgeBase, 'id' | 'createdAt' | 'lastAccessed'>;

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function isValidKnowledgeBase(value: unknown): value is KnowledgeBase {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const kb = value as KnowledgeBase;

  return (
    typeof kb.id === 'string' &&
    typeof kb.name === 'string' &&
    typeof kb.description === 'string' &&
    typeof kb.progress === 'number' &&
    typeof kb.lastAccessed === 'string' &&
    typeof kb.documentCount === 'number' &&
    typeof kb.color === 'string' &&
    typeof kb.icon === 'string' &&
    typeof kb.purpose === 'string' &&
    typeof kb.createdAt === 'string' &&
    (kb.demoScenarioId === undefined || typeof kb.demoScenarioId === 'string') &&
    (kb.demoProcessingLabel === undefined || typeof kb.demoProcessingLabel === 'string') &&
    (kb.demoProcessingMode === undefined ||
      kb.demoProcessingMode === 'layered-annotation' ||
      kb.demoProcessingMode === 'study-brief' ||
      kb.demoProcessingMode === 'raw-only' ||
      kb.demoProcessingMode === 'custom') &&
    (kb.demoStatus === undefined ||
      kb.demoStatus === 'idle' ||
      kb.demoStatus === 'processing' ||
      kb.demoStatus === 'completed') &&
    (kb.creationMethod === 'import' || kb.creationMethod === 'create')
  );
}

function readKnowledgeBasesFromStorage(): KnowledgeBase[] {
  if (!canUseStorage()) {
    return DEFAULT_KNOWLEDGE_BASES;
  }

  const rawValue = window.localStorage.getItem(STORAGE_KEY);
  if (!rawValue) {
    return DEFAULT_KNOWLEDGE_BASES;
  }

  try {
    const parsedValue = JSON.parse(rawValue);
    if (Array.isArray(parsedValue) && parsedValue.every(isValidKnowledgeBase)) {
      return parsedValue;
    }
  } catch (error) {
    console.warn('Failed to parse knowledge bases from localStorage.', error);
  }

  return DEFAULT_KNOWLEDGE_BASES;
}

function persistKnowledgeBases(nextKnowledgeBases: KnowledgeBase[]) {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextKnowledgeBases));
}

function emitKnowledgeBasesUpdated(nextKnowledgeBases: KnowledgeBase[]) {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(
    new CustomEvent(KNOWLEDGE_BASES_UPDATED_EVENT, {
      detail: { knowledgeBases: nextKnowledgeBases }
    })
  );
}

function setKnowledgeBases(nextKnowledgeBases: KnowledgeBase[]) {
  knowledgeBases.set(nextKnowledgeBases);
  persistKnowledgeBases(nextKnowledgeBases);
  emitKnowledgeBasesUpdated(nextKnowledgeBases);
}

if (canUseStorage()) {
  const initialKnowledgeBases = readKnowledgeBasesFromStorage();
  knowledgeBases.set(initialKnowledgeBases);

  if (!window.localStorage.getItem(STORAGE_KEY)) {
    persistKnowledgeBases(initialKnowledgeBases);
  }

  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY) {
      knowledgeBases.set(readKnowledgeBasesFromStorage());
    }
  });
}

export function setActiveAnnotation(annotation: Annotation) {
  activeAnnotation.set(annotation);
  isChatOpen.set(true);
}

export function clearActiveAnnotation() {
  activeAnnotation.set(null);
}

export function addKnowledgeBase(kb: NewKnowledgeBaseInput) {
  const now = new Date().toISOString();
  const newKnowledgeBase: KnowledgeBase = {
    ...kb,
    id: `kb-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: now,
    lastAccessed: now,
    progress: Number.isFinite(kb.progress) ? Math.max(0, Math.min(100, kb.progress)) : 0,
    documentCount: Number.isFinite(kb.documentCount) ? Math.max(0, kb.documentCount) : 0
  };

  setKnowledgeBases([...knowledgeBases.get(), newKnowledgeBase]);

  return newKnowledgeBase;
}

export function updateKnowledgeBaseAccess(kbId: string) {
  const nextKnowledgeBases = knowledgeBases.get().map((kb) =>
    kb.id === kbId
      ? {
          ...kb,
          lastAccessed: new Date().toISOString()
        }
      : kb
  );

  setKnowledgeBases(nextKnowledgeBases);
}

export function updateKnowledgeBaseDocumentCount(kbId: string, documentCount: number) {
  const safeCount = Number.isFinite(documentCount) ? Math.max(0, documentCount) : 0;

  const nextKnowledgeBases = knowledgeBases.get().map((kb) =>
    kb.id === kbId
      ? {
          ...kb,
          documentCount: safeCount,
          lastAccessed: new Date().toISOString()
        }
      : kb
  );

  setKnowledgeBases(nextKnowledgeBases);
}

export function updateKnowledgeBaseDemoState(
  kbId: string,
  updates: Partial<Pick<KnowledgeBase, 'demoScenarioId' | 'demoProcessingMode' | 'demoProcessingLabel' | 'demoStatus'>>
) {
  const nextKnowledgeBases = knowledgeBases.get().map((kb) =>
    kb.id === kbId
      ? {
          ...kb,
          ...updates,
          lastAccessed: new Date().toISOString()
        }
      : kb
  );

  setKnowledgeBases(nextKnowledgeBases);
}

export function removeKnowledgeBase(kbId: string) {
  const nextKnowledgeBases = knowledgeBases.get().filter((kb) => kb.id !== kbId);
  setKnowledgeBases(nextKnowledgeBases);
}

export function resetKnowledgeBases() {
  setKnowledgeBases(DEFAULT_KNOWLEDGE_BASES);
}
