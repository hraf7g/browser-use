'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { authSession, type AuthUser } from '@/lib/auth-session';

type AuthSessionStatus = 'loading' | 'authenticated' | 'unauthenticated';

type AuthSessionContextValue = {
  user: AuthUser | null;
  status: AuthSessionStatus;
  refreshSession: () => Promise<AuthUser | null>;
  signOut: () => Promise<void>;
};

const AuthSessionContext = createContext<AuthSessionContextValue | undefined>(undefined);

async function resolveSession() {
  try {
    const user = await authSession.getCurrentUser();
    return { user, status: 'authenticated' as const };
  } catch (error) {
    if (authSession.isUnauthorizedError(error)) {
      return { user: null, status: 'unauthenticated' as const };
    }
    throw error;
  }
}

export function AuthSessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthSessionStatus>('loading');

  useEffect(() => {
    let cancelled = false;

    void resolveSession()
      .then((nextSession) => {
        if (cancelled) {
          return;
        }
        setUser(nextSession.user);
        setStatus(nextSession.status);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setUser(null);
        setStatus('unauthenticated');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function refreshSession() {
    const nextSession = await resolveSession();
    setUser(nextSession.user);
    setStatus(nextSession.status);
    return nextSession.user;
  }

  async function signOut() {
    await authSession.logout();
    setUser(null);
    setStatus('unauthenticated');
  }

  const value: AuthSessionContextValue = {
    user,
    status,
    refreshSession,
    signOut,
  };

  return <AuthSessionContext.Provider value={value}>{children}</AuthSessionContext.Provider>;
}

export function useAuthSession() {
  const context = useContext(AuthSessionContext);
  if (context === undefined) {
    throw new Error('useAuthSession must be used within AuthSessionProvider');
  }

  return context;
}
