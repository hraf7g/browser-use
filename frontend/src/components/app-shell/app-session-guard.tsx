'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/context/language-context';
import { useAuthSession } from '@/context/auth-session-context';

function SessionLoadingState() {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6 dark:bg-slate-950">
      <div className="max-w-sm rounded-3xl border border-slate-200 bg-white px-6 py-5 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
          Tender Watch
        </p>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {t.app.session.verifying}
        </p>
      </div>
    </div>
  );
}

export default function AppSessionGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { status } = useAuthSession();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.replace('/login');
    }
  }, [router, status]);

  if (status !== 'authenticated') {
    return <SessionLoadingState />;
  }

  return <>{children}</>;
}
