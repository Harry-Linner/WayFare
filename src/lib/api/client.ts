const LOCAL_DEV_HOSTS = new Set(['127.0.0.1', 'localhost']);
const LOCAL_DEV_API_BASE_URL = 'http://127.0.0.1:8080';

function normalizeApiBaseUrl(value: string) {
  return String(value || '').trim().replace(/\/+$/, '');
}

function getConfiguredApiBaseUrl() {
  return normalizeApiBaseUrl(import.meta.env.PUBLIC_API_BASE_URL || '');
}

function getLocalDevApiBaseUrl() {
  if (typeof window === 'undefined') {
    return '';
  }

  if (!LOCAL_DEV_HOSTS.has(window.location.hostname)) {
    return '';
  }

  const configured = getConfiguredApiBaseUrl();
  if (configured) {
    try {
      const parsed = new URL(configured);
      if (LOCAL_DEV_HOSTS.has(parsed.hostname)) {
        return configured;
      }
    } catch {
      // Ignore invalid configured URL and fall back to the default local backend target.
    }
  }

  return LOCAL_DEV_API_BASE_URL;
}

const API_BASE_URL = getLocalDevApiBaseUrl() || getConfiguredApiBaseUrl();

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    mode: 'cors',
    credentials: 'include',
  });

  const data = await parseResponse(response);
  if (!response.ok) {
    if (response.status === 401 && typeof window !== 'undefined') {
      const nextPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      window.location.href = `/login?next=${encodeURIComponent(nextPath)}`;
    }
    const message =
      typeof data === 'object' && data !== null && 'error' in data
        ? String((data as { error?: unknown }).error)
        : `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, data);
  }

  return data as T;
}

export interface UploadResponse {
  message: string;
  docHash: string;
  documentId: string | number;
  pageCount: number;
  status: string;
}

export interface ChatResponse {
  content: string;
  knowledgePoint?: string;
}

export interface FeedbackPayload {
  category: string;
  sentiment: string;
  message: string;
  contact?: string;
  page?: string;
  scope?: string;
  recentAction?: string;
  recentActionAt?: string;
  knowledgeBaseId?: string;
  knowledgeBaseName?: string;
  documentId?: string;
  documentName?: string;
  metadata?: Record<string, unknown>;
}

export interface FeedbackResponse {
  ok: boolean;
  id: string;
  savedAt: string;
}

export interface PromptProfile {
  scope: string;
  knowledgeBaseId?: string;
  content: string;
  exists: boolean;
  updatedAt?: string;
}

export type ChatSelectionAction = 'explain' | 'summary' | 'ask';

export interface ChatRequestPayload {
  projectId: number;
  knowledgeBaseId?: string;
  context?: string;
  displayMessage?: string;
  requestType?: 'freeform' | 'selection_action';
  action?: ChatSelectionAction;
  selectedText?: string;
  page?: number;
  documentName?: string;
}

export interface KnowledgeBaseItem {
  id: string;
  name: string;
  description: string;
  purpose?: string;
  subject?: string;
  learningGoals?: string;
  studyTime?: string;
  creationMethod?: string;
  folderName?: string;
  documentCount: number;
  readyDocumentCount?: number;
  processingDocumentCount?: number;
  failedDocumentCount?: number;
  progress?: number;
  createdAt: string;
  updatedAt: string;
}

export interface KnowledgeBasePayload {
  name: string;
  description?: string;
  purpose?: string;
  subject?: string;
  learningGoals?: string;
  studyTime?: string;
  creationMethod?: string;
  folderName?: string;
}

export interface DocumentItem {
  id: string | number;
  knowledgeBaseId: string;
  fileName: string;
  fileType: string;
  pageCount: number;
  status: string;
  docHash: string;
  createdAt: string;
  fileUrl: string;
}

export type ScheduleRepeatRule = 'none' | 'daily' | 'weekdays' | 'weekly';
export type ScheduleStatus = 'pending' | 'completed';

export interface ScheduleItem {
  id: number;
  projectId: number;
  title: string;
  description: string;
  scheduledFor: string;
  reminderOffsetMinutes: number;
  repeatRule: ScheduleRepeatRule;
  status: ScheduleStatus;
  snoozedUntil?: string | null;
  lastNotifiedAt?: string | null;
  lastCompletedAt?: string | null;
  nextTriggerAt?: string | null;
  isRecurring: boolean;
}

export interface SchedulePayload {
  projectId?: number;
  title: string;
  description?: string;
  scheduledFor: string;
  reminderOffsetMinutes?: number;
  repeatRule?: ScheduleRepeatRule;
}

export async function listKnowledgeBases(): Promise<KnowledgeBaseItem[]> {
  const response = await request<{ knowledgeBases: KnowledgeBaseItem[] }>('/knowledge-bases');
  return response.knowledgeBases ?? [];
}

export async function getKnowledgeBase(id: string): Promise<KnowledgeBaseItem> {
  const response = await request<{ knowledgeBase: KnowledgeBaseItem }>(
    `/knowledge-bases/${encodeURIComponent(id)}`
  );
  return response.knowledgeBase;
}

export async function createKnowledgeBase(payload: KnowledgeBasePayload): Promise<KnowledgeBaseItem> {
  const response = await request<{ knowledgeBase: KnowledgeBaseItem }>('/knowledge-bases', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return response.knowledgeBase;
}

export async function deleteKnowledgeBase(id: string): Promise<{ deleted: boolean; id: string }> {
  return request<{ deleted: boolean; id: string }>(`/knowledge-bases/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

export async function uploadFile(
  file: File,
  kbId: string,
  relativePath?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('kbId', kbId);
  if (relativePath) {
    formData.append('relativePath', relativePath);
  } else if ((file as File & { webkitRelativePath?: string }).webkitRelativePath) {
    formData.append('relativePath', (file as File & { webkitRelativePath?: string }).webkitRelativePath!);
  }

  return request<UploadResponse>('/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function sendChatMessage(payload: ChatRequestPayload): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function listDocuments(kbId: string): Promise<DocumentItem[]> {
  const response = await request<{ documents: DocumentItem[] }>(
    `/documents?kbId=${encodeURIComponent(kbId)}`
  );
  return response.documents ?? [];
}

export async function deleteDocument(id: string | number): Promise<{ deleted: boolean; id: string | number }> {
  return request<{ deleted: boolean; id: string | number }>(`/documents/${encodeURIComponent(String(id))}`, {
    method: 'DELETE',
  });
}

export async function listSchedules(projectId = 1): Promise<ScheduleItem[]> {
  const response = await request<{ schedules: ScheduleItem[] }>(
    `/schedules?projectId=${encodeURIComponent(String(projectId))}`
  );
  return response.schedules ?? [];
}

export async function createSchedule(payload: SchedulePayload): Promise<ScheduleItem> {
  const response = await request<{ schedule: ScheduleItem }>('/schedules', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return response.schedule;
}

export async function updateSchedule(id: number, payload: SchedulePayload): Promise<ScheduleItem> {
  const response = await request<{ schedule: ScheduleItem }>(`/schedules/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return response.schedule;
}

export async function completeSchedule(id: number): Promise<ScheduleItem> {
  const response = await request<{ schedule: ScheduleItem }>(`/schedules/${id}/complete`, {
    method: 'POST',
  });
  return response.schedule;
}

export async function snoozeSchedule(id: number, minutes = 10): Promise<ScheduleItem> {
  const response = await request<{ schedule: ScheduleItem }>(`/schedules/${id}/snooze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ minutes }),
  });
  return response.schedule;
}

export async function rescheduleSchedule(id: number, scheduledFor: string): Promise<ScheduleItem> {
  const response = await request<{ schedule: ScheduleItem }>(`/schedules/${id}/reschedule`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ scheduledFor }),
  });
  return response.schedule;
}

export async function deleteSchedule(id: number): Promise<{ deleted: boolean; id: number }> {
  return request<{ deleted: boolean; id: number }>(`/schedules/${id}`, {
    method: 'DELETE',
  });
}

export async function acknowledgeSchedule(id: number): Promise<ScheduleItem> {
  const response = await request<{ schedule: ScheduleItem }>(`/schedules/${id}/acknowledge`, {
    method: 'POST',
  });
  return response.schedule;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  return request<FeedbackResponse>('/feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

export async function getGlobalProfile(): Promise<PromptProfile> {
  const response = await request<{ profile: PromptProfile }>('/profiles/global');
  return response.profile;
}

export async function updateGlobalProfile(content: string): Promise<PromptProfile> {
  const response = await request<{ profile: PromptProfile }>('/profiles/global', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });
  return response.profile;
}

export async function getKnowledgeBaseProfile(knowledgeBaseId: string): Promise<PromptProfile> {
  const response = await request<{ profile: PromptProfile }>(
    `/knowledge-bases/${encodeURIComponent(knowledgeBaseId)}/profile`
  );
  return response.profile;
}

export async function updateKnowledgeBaseProfile(
  knowledgeBaseId: string,
  content: string
): Promise<PromptProfile> {
  const response = await request<{ profile: PromptProfile }>(
    `/knowledge-bases/${encodeURIComponent(knowledgeBaseId)}/profile`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    }
  );
  return response.profile;
}

export const chat = sendChatMessage;

export { API_BASE_URL };
