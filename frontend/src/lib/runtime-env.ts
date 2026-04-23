const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const DEFAULT_AUTH_COOKIE_NAME = 'utw_access_token';
const COOKIE_NAME_PATTERN = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;

function normalizeAbsoluteUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return trimmed;
  }

  const url = new URL(trimmed);
  const normalized = url.toString().replace(/\/$/, '');

  if (process.env.NODE_ENV === 'production') {
    const isLoopbackHost = ['localhost', '127.0.0.1'].includes(url.hostname);
    if (!isLoopbackHost && url.protocol !== 'https:') {
      throw new Error('NEXT_PUBLIC_API_URL must use https:// outside local development');
    }
  }

  return normalized;
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

  const cookieName = (configured ?? DEFAULT_AUTH_COOKIE_NAME).trim() || DEFAULT_AUTH_COOKIE_NAME;
  if (!COOKIE_NAME_PATTERN.test(cookieName)) {
    throw new Error('NEXT_PUBLIC_AUTH_COOKIE_NAME must be a valid cookie token');
  }

  return cookieName;
}

export function getPublicApiBaseUrl(): string {
  return resolvePublicApiBaseUrl();
}

export function getPublicAuthCookieName(): string {
  return resolvePublicAuthCookieName();
}
