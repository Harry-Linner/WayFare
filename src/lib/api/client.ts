import type {
  ApiChatHistoryMessage,
  ApiChatResponse,
  ApiDocument,
  ApiHealthResponse,
  ApiSystemStatus,
} from '../../types/sharedtypes';

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export type Document = ApiDocument;
export type ChatMessage = ApiChatHistoryMessage;
export type ChatResponse = ApiChatResponse;

const API_CONFIG = {
  baseURL:
    (typeof import.meta !== 'undefined' && (import.meta.env.PUBLIC_API_URL as string | undefined)) || '',
  timeout: 30000,
  retryAttempts: 2,
  retryDelay: 1000,
};

class HttpClient {
  private readonly baseURL: string;
  private readonly timeout: number;

  constructor(baseURL: string, timeout: number) {
    this.baseURL = baseURL.replace(/\/$/, '');
    this.timeout = timeout;
  }

  private buildURL(endpoint: string) {
    if (!this.baseURL) {
      return endpoint;
    }

    return `${this.baseURL}${endpoint}`;
  }

  private isFormData(body: BodyInit | null | undefined): body is FormData {
    return typeof FormData !== 'undefined' && body instanceof FormData;
  }

  private parseResponsePayload(text: string) {
    if (!text) {
      return undefined;
    }

    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  private extractErrorMessage(payload: unknown, fallback: string) {
    if (payload && typeof payload === 'object') {
      if ('error' in payload && typeof payload.error === 'string') {
        return payload.error;
      }

      if ('message' in payload && typeof payload.message === 'string') {
        return payload.message;
      }
    }

    if (typeof payload === 'string' && payload.trim()) {
      return payload;
    }

    return fallback;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const headers = new Headers(options.headers ?? {});
      if (options.body !== undefined && !this.isFormData(options.body) && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
      }

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const text = await response.text();
      const payload = this.parseResponsePayload(text);

      if (!response.ok) {
        return {
          success: false,
          error: this.extractErrorMessage(payload, `HTTP ${response.status}`),
        };
      }

      return {
        success: true,
        data: payload as T,
      };
    } catch (error) {
      clearTimeout(timeoutId);

      if (retryCount < API_CONFIG.retryAttempts && this.isRetryableError(error)) {
        await this.delay(API_CONFIG.retryDelay * (retryCount + 1));
        return this.request<T>(endpoint, options, retryCount + 1);
      }

      return {
        success: false,
        error: error instanceof Error ? error.message : '未知网络错误',
      };
    }
  }

  private isRetryableError(error: unknown) {
    if (!(error instanceof Error)) {
      return false;
    }

    return error.name === 'AbortError' || error.name === 'TypeError' || error.message.includes('NetworkError');
  }

  private delay(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data !== undefined ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async upload<T>(endpoint: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<T>> {
    const url = this.buildURL(endpoint);

    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      xhr.open('POST', url, true);
      xhr.timeout = this.timeout;

      xhr.upload.addEventListener('progress', (event) => {
        if (!event.lengthComputable || !onProgress) {
          return;
        }

        onProgress((event.loaded / event.total) * 100);
      });

      xhr.addEventListener('load', () => {
        const payload = this.parseResponsePayload(xhr.responseText ?? '');

        if (xhr.status >= 200 && xhr.status < 300) {
          onProgress?.(100);
          resolve({
            success: true,
            data: payload as T,
          });
          return;
        }

        resolve({
          success: false,
          error: this.extractErrorMessage(payload, `HTTP ${xhr.status}`),
        });
      });

      xhr.addEventListener('error', () => {
        resolve({
          success: false,
          error: '文件上传网络错误',
        });
      });

      xhr.addEventListener('timeout', () => {
        resolve({
          success: false,
          error: '文件上传超时',
        });
      });

      xhr.send(formData);
    });
  }
}

export class WayFareAPI {
  private readonly client: HttpClient;

  constructor() {
    this.client = new HttpClient(API_CONFIG.baseURL, API_CONFIG.timeout);
  }

  async uploadDocument(file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<Document>> {
    return this.client.upload<Document>('/api/upload', file, onProgress);
  }

  async sendChatMessage(
    message: string,
    docHash?: string,
    history: ChatMessage[] = []
  ): Promise<ApiResponse<ChatResponse>> {
    return this.client.post<ChatResponse>('/api/chat', {
      message,
      docHash,
      history: history.map((item) => ({
        role: item.role,
        content: item.content,
      })),
    });
  }

  async getDocuments(): Promise<ApiResponse<Document[]>> {
    return this.client.get<Document[]>('/api/documents');
  }

  async getDocument(docId: number): Promise<ApiResponse<Document>> {
    return this.client.get<Document>(`/api/documents/${docId}`);
  }

  async deleteDocument(docId: number): Promise<ApiResponse<{ message: string }>> {
    return this.client.delete<{ message: string }>(`/api/documents/${docId}`);
  }

  async getChatHistory(docHash?: string): Promise<ApiResponse<ChatMessage[]>> {
    const endpoint = docHash
      ? `/api/chat/history?docHash=${encodeURIComponent(docHash)}`
      : '/api/chat/history';

    return this.client.get<ChatMessage[]>(endpoint);
  }

  async healthCheck(): Promise<ApiResponse<ApiHealthResponse>> {
    return this.client.get<ApiHealthResponse>('/health');
  }

  async getSystemStatus(): Promise<ApiResponse<ApiSystemStatus>> {
    return this.client.get<ApiSystemStatus>('/api/status');
  }
}

export const api = new WayFareAPI();

export default api;
