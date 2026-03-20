import type { APIRoute } from 'astro';

import { getBetaAuthConfig, sanitizeNextPath } from '../../../lib/server/beta-auth';

export const POST: APIRoute = async ({ request, cookies, redirect }) => {
  const config = getBetaAuthConfig();
  const formData = await request.formData().catch(() => new FormData());
  const nextPath = sanitizeNextPath(String(formData.get('next') || '/login'));

  cookies.delete(config.cookieName, {
    path: '/',
  });

  return redirect(nextPath);
};
