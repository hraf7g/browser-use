const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const DEFAULT_AUTH_COOKIE_NAME = 'utw_access_token';

function normalizeAbsoluteUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return trimmed;
  }

  const url = new URL(trimmed);
  return url.toString().replace(/\/$/, '');
}

function resolvePublicApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL;
  if (process.env.NODE_ENV === 'production' && !configured) {
    throw new Error('NEXT_PUBLIC_API_URL must be set in production');
  }

  return normalizeAbsoluteUrl(configured ?? DEFAULT_API_BASE_URL);
}

function resolvePublicAuthCookieName(): string {
  const configured = process.env.NEXT_PUBLIC_AUTH_COOKIE_NAME;
  if (process.env.NODE_ENV === 'production' && !configured) {
    throw new Error('NEXT_PUBLIC_AUTH_COOKIE_NAME must be set in production');
  }

  return (configured ?? DEFAULT_AUTH_COOKIE_NAME).trim() || DEFAULT_AUTH_COOKIE_NAME;
}

export const PUBLIC_API_BASE_URL = resolvePublicApiBaseUrl();
export const PUBLIC_AUTH_COOKIE_NAME = resolvePublicAuthCookieName();

export function getPublicApiBaseUrl(): string {
  return PUBLIC_API_BASE_URL;
}

export function getPublicAuthCookieName(): string {
  return PUBLIC_AUTH_COOKIE_NAME;
}
