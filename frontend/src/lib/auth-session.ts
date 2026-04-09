import { apiClient, ApiError } from '@/lib/api-client';

export interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials extends LoginCredentials {}

export function resolveSafeRedirectPath(
  nextPath: string | null | undefined,
  fallback = '/dashboard'
): string {
  if (typeof nextPath !== 'string') {
    return fallback;
  }

  const trimmed = nextPath.trim();
  if (!trimmed.startsWith('/') || trimmed.startsWith('//')) {
    return fallback;
  }

  if (trimmed === '/login' || trimmed === '/signup') {
    return fallback;
  }

  return trimmed;
}

export function readSafeRedirectPathFromLocation(fallback = '/dashboard'): string {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const nextPath = new URLSearchParams(window.location.search).get('next');
  return resolveSafeRedirectPath(nextPath, fallback);
}

async function login(credentials: LoginCredentials): Promise<AuthUser> {
  return apiClient<AuthUser>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

async function signup(credentials: SignupCredentials): Promise<AuthUser> {
  return apiClient<AuthUser>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
}

async function logout(): Promise<void> {
  await apiClient<void>('/auth/logout', {
    method: 'POST',
  });
}

async function getCurrentUser(): Promise<AuthUser> {
  return apiClient<AuthUser>('/me');
}

function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

export const authSession = {
  login,
  signup,
  logout,
  getCurrentUser,
  isUnauthorizedError,
};
