import type { APIRoute } from 'astro';

import {
  createBetaSessionToken,
  getBetaAuthConfig,
  sanitizeNextPath,
  validateBetaCredentials,
} from '../../../lib/server/beta-auth';

export const POST: APIRoute = async ({ request, cookies, redirect }) => {
  const config = getBetaAuthConfig();
  const formData = await request.formData();
  const username = String(formData.get('username') || '').trim();
  const password = String(formData.get('password') || '').trim();
  const nextPath = sanitizeNextPath(String(formData.get('next') || '/dashboard'));

  if (!config.enabled) {
    return redirect(nextPath);
  }

  if (!config.configured) {
    return redirect(`/login?error=${encodeURIComponent('beta-auth-not-configured')}`);
  }

  if (!validateBetaCredentials(username, password)) {
    return redirect(`/login?error=${encodeURIComponent('invalid')}&next=${encodeURIComponent(nextPath)}`);
  }

  const token = createBetaSessionToken(username);
  cookies.set(config.cookieName, token, {
    path: '/',
    httpOnly: true,
    sameSite: 'lax',
    secure: config.secureCookie,
    maxAge: config.sessionHours * 60 * 60,
  });

  return redirect(nextPath);
};
