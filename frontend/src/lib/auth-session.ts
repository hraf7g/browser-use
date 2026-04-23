import { apiClient, ApiError } from '@/lib/api-client';

export interface AuthUser {
  id: string;
  email: string;
  is_active: boolean;
  is_operator: boolean;
}

interface SessionStatusResponse {
  authenticated: boolean;
  user: AuthUser | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupCredentials extends LoginCredentials {}

export interface ForgotPasswordResponse {
  accepted: boolean;
  message: string;
  delivery_channel: string;
}

export interface ResetPasswordPayload {
  token: string;
  password: string;
}

export interface ResetPasswordResponse {
  message: string;
}

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
  const session = await apiClient<SessionStatusResponse>('/auth/session');
  if (session.authenticated && session.user) {
    return session.user;
  }

  throw new ApiError('authentication required', 401, session);
}

async function requestPasswordReset(email: string): Promise<ForgotPasswordResponse> {
  return apiClient<ForgotPasswordResponse>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

async function resetPassword(payload: ResetPasswordPayload): Promise<ResetPasswordResponse> {
  return apiClient<ResetPasswordResponse>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

export const authSession = {
  login,
  signup,
  logout,
  getCurrentUser,
  requestPasswordReset,
  resetPassword,
  isUnauthorizedError,
};
