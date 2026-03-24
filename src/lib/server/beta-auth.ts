import crypto from 'node:crypto';

export type BetaAuthConfig = {
  enabled: boolean;
  configured: boolean;
  cookieName: string;
  sessionHours: number;
  secureCookie: boolean;
  allowedUsers: Map<string, string>;
  secret: string;
};

export type BetaSession = {
  username: string;
  expiresAt: number;
};

const serverEnv = import.meta.env as Record<string, string | boolean | undefined>;

function readServerEnv(key: string) {
  const viteValue = serverEnv[key];
  if (typeof viteValue === 'string' && viteValue.trim() !== '') {
    return viteValue;
  }

  const processValue = process.env[key];
  if (typeof processValue === 'string' && processValue.trim() !== '') {
    return processValue;
  }

  return '';
}

function parseAllowedUsers(raw: string): Map<string, string> {
  const users = new Map<string, string>();

  for (const entry of raw.split(',')) {
    const trimmed = entry.trim();
    if (!trimmed) continue;

    const separatorIndex = trimmed.indexOf(':');
    if (separatorIndex <= 0) continue;

    const username = trimmed.slice(0, separatorIndex).trim();
    const password = trimmed.slice(separatorIndex + 1).trim();
    if (!username || !password) continue;

    users.set(username, password);
  }

  return users;
}

export function getBetaAuthConfig(): BetaAuthConfig {
  const enabled = readServerEnv('BETA_AUTH_ENABLED') === '1';
  const cookieName = readServerEnv('BETA_AUTH_COOKIE_NAME') || 'wayfare_beta_auth';
  const sessionHours = Number(readServerEnv('BETA_AUTH_SESSION_HOURS') || 24) || 24;
  const secureCookie = readServerEnv('BETA_AUTH_SECURE_COOKIE') === '1' || import.meta.env.PROD;
  const allowedUsers = parseAllowedUsers(readServerEnv('BETA_ALLOWED_USERS'));
  const secret = readServerEnv('BETA_AUTH_SECRET');

  return {
    enabled,
    configured: !enabled || (!!secret && allowedUsers.size > 0),
    cookieName,
    sessionHours,
    secureCookie,
    allowedUsers,
    secret,
  };
}

function base64UrlEncode(input: Buffer | string) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');
}

function base64UrlDecode(input: string) {
  const normalized = input.replace(/-/g, '+').replace(/_/g, '/');
  const padding = normalized.length % 4 === 0 ? '' : '='.repeat(4 - (normalized.length % 4));
  return Buffer.from(normalized + padding, 'base64').toString('utf-8');
}

function signPayload(secret: string, payload: string) {
  return base64UrlEncode(crypto.createHmac('sha256', secret).update(payload).digest());
}

export function validateBetaCredentials(username: string, password: string) {
  const config = getBetaAuthConfig();
  if (!config.enabled || !config.configured) {
    return false;
  }

  return config.allowedUsers.get(username) === password;
}

export function createBetaSessionToken(username: string) {
  const config = getBetaAuthConfig();
  if (!config.configured) {
    throw new Error('Beta auth is not configured.');
  }

  const expiresAt = Math.floor(Date.now() / 1000) + config.sessionHours * 60 * 60;
  const userPart = base64UrlEncode(username);
  const payload = `${userPart}.${expiresAt}`;
  const signature = signPayload(config.secret, payload);
  return `${payload}.${signature}`;
}

export function verifyBetaSessionToken(token?: string | null): BetaSession | null {
  const config = getBetaAuthConfig();
  if (!config.enabled) {
    return { username: 'anonymous', expiresAt: Number.MAX_SAFE_INTEGER };
  }
  if (!config.configured || !token) return null;

  const [userPart, expiresAtRaw, signature] = token.split('.');
  if (!userPart || !expiresAtRaw || !signature) return null;

  const payload = `${userPart}.${expiresAtRaw}`;
  const expectedSignature = signPayload(config.secret, payload);
  const left = Buffer.from(signature);
  const right = Buffer.from(expectedSignature);
  if (left.length !== right.length || !crypto.timingSafeEqual(left, right)) {
    return null;
  }

  const expiresAt = Number(expiresAtRaw);
  if (!Number.isFinite(expiresAt) || expiresAt <= Math.floor(Date.now() / 1000)) {
    return null;
  }

  const username = base64UrlDecode(userPart);
  if (!config.allowedUsers.has(username)) {
    return null;
  }

  return { username, expiresAt };
}

export function sanitizeNextPath(nextPath: string | null | undefined) {
  if (!nextPath) return '/dashboard';
  if (!nextPath.startsWith('/')) return '/dashboard';
  if (nextPath.startsWith('//')) return '/dashboard';
  if (nextPath.startsWith('/api/auth/')) return '/dashboard';
  return nextPath;
}

export function isPublicBetaPath(pathname: string) {
  return (
    pathname === '/login' ||
    pathname === '/api/auth/login' ||
    pathname === '/api/auth/logout' ||
    pathname.startsWith('/_astro/') ||
    pathname.startsWith('/favicon') ||
    pathname.startsWith('/images/')
  );
}
