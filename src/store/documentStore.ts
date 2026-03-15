import { atom } from 'nanostores';
import type { KnowledgeBaseDocument, UploadProcessingMode } from '../types/sharedtypes';

const STORAGE_KEY = 'wayfare:knowledge-base-documents';

type DocumentMap = Record<string, KnowledgeBaseDocument[]>;

const DEFAULT_DOCUMENTS: DocumentMap = {};

export const knowledgeBaseDocuments = atom<DocumentMap>(DEFAULT_DOCUMENTS);

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

function isValidDocument(value: unknown): value is KnowledgeBaseDocument {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const document = value as KnowledgeBaseDocument;
  return (
    typeof document.id === 'string' &&
    typeof document.kbId === 'string' &&
    typeof document.name === 'string' &&
    typeof document.size === 'number' &&
    typeof document.type === 'string' &&
    typeof document.uploadedAt === 'string' &&
    typeof document.processingMode === 'string' &&
    typeof document.processingLabel === 'string'
  );
}

function isValidDocumentMap(value: unknown): value is DocumentMap {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  return Object.values(value as DocumentMap).every(
    (items) => Array.isArray(items) && items.every(isValidDocument)
  );
}

function readDocumentsFromStorage(): DocumentMap {
  if (!canUseStorage()) {
    return DEFAULT_DOCUMENTS;
  }

  const rawValue = window.localStorage.getItem(STORAGE_KEY);
  if (!rawValue) {
    return DEFAULT_DOCUMENTS;
  }

  try {
    const parsedValue = JSON.parse(rawValue);
    if (isValidDocumentMap(parsedValue)) {
      return parsedValue;
    }
  } catch (error) {
    console.warn('Failed to parse documents from localStorage.', error);
  }

  return DEFAULT_DOCUMENTS;
}

function persistDocuments(nextDocuments: DocumentMap) {
  if (!canUseStorage()) {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextDocuments));
}

function setDocuments(nextDocuments: DocumentMap) {
  knowledgeBaseDocuments.set(nextDocuments);
  persistDocuments(nextDocuments);
}

if (canUseStorage()) {
  const initialDocuments = readDocumentsFromStorage();
  knowledgeBaseDocuments.set(initialDocuments);

  if (!window.localStorage.getItem(STORAGE_KEY)) {
    persistDocuments(initialDocuments);
  }

  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY) {
      knowledgeBaseDocuments.set(readDocumentsFromStorage());
    }
  });
}

export function getDocumentsForKnowledgeBase(kbId: string) {
  return knowledgeBaseDocuments.get()[kbId] ?? [];
}

export function addDocumentsToKnowledgeBase(
  kbId: string,
  files: File[],
  processingMode: UploadProcessingMode,
  processingLabel: string
) {
  const currentDocuments = knowledgeBaseDocuments.get();
  const currentKnowledgeBaseDocuments = currentDocuments[kbId] ?? [];
  const uploadedAt = new Date().toISOString();

  const nextKnowledgeBaseDocuments = [
    ...currentKnowledgeBaseDocuments,
    ...files.map((file) => ({
      id: `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      kbId,
      name: file.name,
      size: file.size,
      type: file.type || 'application/octet-stream',
      uploadedAt,
      processingMode,
      processingLabel
    }))
  ];

  const nextDocuments = {
    ...currentDocuments,
    [kbId]: nextKnowledgeBaseDocuments
  };

  setDocuments(nextDocuments);
  return nextKnowledgeBaseDocuments;
}

export function addDocumentEntriesToKnowledgeBase(
  kbId: string,
  entries: Omit<KnowledgeBaseDocument, 'id' | 'kbId' | 'uploadedAt'>[]
) {
  const currentDocuments = knowledgeBaseDocuments.get();
  const currentKnowledgeBaseDocuments = currentDocuments[kbId] ?? [];
  const uploadedAt = new Date().toISOString();

  const nextKnowledgeBaseDocuments = [
    ...currentKnowledgeBaseDocuments,
    ...entries.map((entry) => ({
      ...entry,
      id: `doc-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      kbId,
      uploadedAt
    }))
  ];

  setDocuments({
    ...currentDocuments,
    [kbId]: nextKnowledgeBaseDocuments
  });

  return nextKnowledgeBaseDocuments;
}

export function removeDocumentFromKnowledgeBase(kbId: string, documentId: string) {
  const currentDocuments = knowledgeBaseDocuments.get();
  const nextKnowledgeBaseDocuments = (currentDocuments[kbId] ?? []).filter((item) => item.id !== documentId);

  setDocuments({
    ...currentDocuments,
    [kbId]: nextKnowledgeBaseDocuments
  });

  return nextKnowledgeBaseDocuments;
}

export function removeAllDocumentsForKnowledgeBase(kbId: string) {
  const currentDocuments = knowledgeBaseDocuments.get();
  const nextDocuments = { ...currentDocuments };
  delete nextDocuments[kbId];
  setDocuments(nextDocuments);
}
