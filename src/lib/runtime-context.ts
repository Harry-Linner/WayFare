type RuntimeDetails = Record<string, unknown>;

type RuntimeState = {
  page: string;
  scope: string;
  recentAction: string;
  recentActionAt: string;
  details: RuntimeDetails;
};

type FeedbackContext = {
  page: string;
  scope: string;
  recentAction: string;
  recentActionAt: string;
  knowledgeBaseId?: string;
  knowledgeBaseName?: string;
  documentId?: string;
  documentName?: string;
  metadata: RuntimeDetails;
};

declare global {
  interface Window {
    __wayfareRuntimeContext?: RuntimeState;
    activeKnowledgeBaseId?: string;
    activeKnowledgeBaseProfile?: {
      id?: string;
      name?: string;
      [key: string]: unknown;
    };
    activeDocumentId?: string;
    activeDocumentName?: string;
  }
}

function inBrowser() {
  return typeof window !== 'undefined';
}

function normalizeDetails(details: RuntimeDetails = {}): RuntimeDetails {
  return Object.fromEntries(
    Object.entries(details).filter(([, value]) => value !== undefined && value !== null && value !== '')
  );
}

function ensureStore(): RuntimeState | null {
  if (!inBrowser()) return null;

  if (!window.__wayfareRuntimeContext) {
    window.__wayfareRuntimeContext = {
      page: 'unknown',
      scope: 'general',
      recentAction: 'page_opened',
      recentActionAt: new Date().toISOString(),
      details: {},
    };
  }

  return window.__wayfareRuntimeContext;
}

export function setPageContext(page: string, details: RuntimeDetails = {}, scope = page) {
  const store = ensureStore();
  if (!store) return;

  store.page = page || store.page;
  store.scope = scope || store.scope;
  store.details = {
    ...store.details,
    ...normalizeDetails(details),
  };
}

export function recordAction(action: string, details: RuntimeDetails = {}) {
  const store = ensureStore();
  if (!store) return;

  store.recentAction = action || store.recentAction;
  store.recentActionAt = new Date().toISOString();
  store.details = {
    ...store.details,
    ...normalizeDetails(details),
  };

  if (typeof details.knowledgeBaseId === 'string') {
    window.activeKnowledgeBaseId = details.knowledgeBaseId;
  }
  if (typeof details.documentId === 'string') {
    window.activeDocumentId = details.documentId;
  }
  if (typeof details.documentName === 'string') {
    window.activeDocumentName = details.documentName;
  }
}

export function getFeedbackContext(defaults: Partial<FeedbackContext> = {}): FeedbackContext {
  const store = ensureStore();
  const profile = inBrowser() ? window.activeKnowledgeBaseProfile || {} : {};

  const metadata: RuntimeDetails = {
    ...(store?.details || {}),
    ...(defaults.metadata || {}),
  };

  if (inBrowser()) {
    metadata.locationPath = window.location.pathname;
    metadata.locationHash = window.location.hash;
    metadata.userAgent = window.navigator.userAgent;
  }

  return {
    page: defaults.page || store?.page || 'unknown',
    scope: defaults.scope || store?.scope || 'general',
    recentAction: defaults.recentAction || store?.recentAction || 'page_opened',
    recentActionAt: defaults.recentActionAt || store?.recentActionAt || new Date().toISOString(),
    knowledgeBaseId:
      defaults.knowledgeBaseId ||
      (typeof metadata.knowledgeBaseId === 'string' ? metadata.knowledgeBaseId : undefined) ||
      (inBrowser() ? window.activeKnowledgeBaseId : undefined) ||
      (typeof profile.id === 'string' ? profile.id : undefined),
    knowledgeBaseName:
      defaults.knowledgeBaseName ||
      (typeof metadata.knowledgeBaseName === 'string' ? metadata.knowledgeBaseName : undefined) ||
      (typeof profile.name === 'string' ? profile.name : undefined),
    documentId:
      defaults.documentId ||
      (typeof metadata.documentId === 'string' ? metadata.documentId : undefined) ||
      (inBrowser() ? window.activeDocumentId : undefined),
    documentName:
      defaults.documentName ||
      (typeof metadata.documentName === 'string' ? metadata.documentName : undefined) ||
      (inBrowser() ? window.activeDocumentName : undefined),
    metadata,
  };
}
