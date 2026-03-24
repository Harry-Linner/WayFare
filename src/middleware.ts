import { defineMiddleware } from 'astro:middleware';

import {
  getBetaAuthConfig,
  isPublicBetaPath,
  sanitizeNextPath,
  verifyBetaSessionToken,
} from './lib/server/beta-auth';

export const onRequest = defineMiddleware(async (context, next) => {
  const url = new URL(context.request.url);
  const requestHost = context.request.headers.get('host')?.trim().toLowerCase() || '';

  if (requestHost === 'localhost' || requestHost.startsWith('localhost:')) {
    const portSuffix = requestHost.slice('localhost'.length);
    return context.redirect(
      `${url.protocol}//127.0.0.1${portSuffix}${url.pathname}${url.search}${url.hash}`,
      302
    );
  }

  const config = getBetaAuthConfig();
  if (!config.enabled) {
    return next();
  }

  if (!config.configured) {
    return new Response('Beta auth is enabled but not configured correctly.', {
      status: 503,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    });
  }

  const pathname = url.pathname;
  const token = context.cookies.get(config.cookieName)?.value;
  const session = verifyBetaSessionToken(token);

  if (pathname === '/login') {
    if (session) {
      return context.redirect('/dashboard');
    }
    return next();
  }

  if (isPublicBetaPath(pathname)) {
    return next();
  }

  if (!session) {
    const nextPath = sanitizeNextPath(
      pathname + url.search + url.hash
    );
    return context.redirect(`/login?next=${encodeURIComponent(nextPath)}`);
  }

  if (pathname === '/login') {
    return context.redirect('/dashboard');
  }

  return next();
});
