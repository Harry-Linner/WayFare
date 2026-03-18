const API_BASE_URL =
  import.meta.env.PUBLIC_API_BASE_URL?.replace(/\/+$/, '') || 'http://localhost:8080';

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
  });

  const data = await parseResponse(response);
  if (!response.ok) {
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
  documentId: number;
  pageCount: number;
  status: string;
}

export interface ChatResponse {
  content: string;
  knowledgePoint?: string;
}

export interface DocumentItem {
  id: number;
  knowledgeBaseId: string;
  fileName: string;
  fileType: string;
  pageCount: number;
  status: string;
  docHash: string;
  createdAt: string;
  fileUrl: string;
}

export async function uploadFile(file: File, kbId = 'default', relativePath?: string): Promise<UploadResponse> {
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

export async function sendChatMessage(projectId: number, context: string, knowledgeBaseId?: string): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ projectId, context, knowledgeBaseId }),
  });
}

export async function listDocuments(kbId: string): Promise<DocumentItem[]> {
  const response = await request<{ documents: DocumentItem[] }>(
    `/documents?kbId=${encodeURIComponent(kbId)}`
  );
  return response.documents ?? [];
}

export async function deleteDocument(id: number): Promise<{ deleted: boolean; id: number }> {
  return request<{ deleted: boolean; id: number }>(`/documents/${id}`, {
    method: 'DELETE',
  });
}

export const chat = sendChatMessage;

export { API_BASE_URL };
