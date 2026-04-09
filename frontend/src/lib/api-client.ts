import { getPublicApiBaseUrl } from '@/lib/runtime-env';

type FetchOptions = RequestInit & {
  params?: Record<string, string | number | undefined>;
};

export class ApiError extends Error {
  status: number;

  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

async function parseResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204 || response.status === 205) {
    return null;
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json().catch(() => null);
  }

  return response.text().catch(() => null);
}

function getErrorMessage(errorBody: unknown): string {
  if (typeof errorBody === 'string') {
    return errorBody.trim() || 'An unexpected error occurred';
  }

  if (typeof errorBody === 'object' && errorBody !== null) {
    const body = errorBody as Record<string, unknown>;
    const detail = body.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }

    const message = body.message;
    if (typeof message === 'string' && message.trim()) {
      return message;
    }
  }

  return 'An unexpected error occurred';
}

export async function apiClient<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...init } = options;

  const url = new URL(endpoint, getPublicApiBaseUrl());
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) url.searchParams.append(key, String(value));
    });
  }

  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url.toString(), {
    ...init,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    const errorBody = await parseResponseBody(response);
    throw new ApiError(getErrorMessage(errorBody), response.status, errorBody);
  }

  const body = await parseResponseBody(response);
  return body as T;
}
