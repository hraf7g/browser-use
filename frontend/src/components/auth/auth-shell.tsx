'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import AuthBrandPanel from './auth-brand-panel';
import AuthHeader from './auth-header';
import { authSession, readSafeRedirectPathFromLocation } from '@/lib/auth-session';

export default function AuthShell({ children }: { children: React.ReactNode }) {
  const { lang } = useTranslation();
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    void authSession
      .getCurrentUser()
      .then(() => {
        if (!cancelled) {
          router.replace(readSafeRedirectPathFromLocation());
        }
      })
      .catch((error) => {
        if (cancelled || !authSession.isUnauthorizedError(error)) {
          return;
        }
      });

    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="flex min-h-screen flex-col bg-white transition-colors duration-300 dark:bg-slate-950">
      <AuthHeader />
      <div className="flex flex-1 items-center justify-center bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.08),transparent_34%)] px-6 py-10 dark:bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.12),transparent_34%)] lg:px-10">
        <div className="grid w-full max-w-6xl items-center gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(320px,0.75fr)] xl:gap-14">
          <main className="flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0, x: lang === 'ar' ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="w-full max-w-xl"
            >
              {children}
            </motion.div>
          </main>

          <aside className="hidden lg:block">
            <AuthBrandPanel />
          </aside>
        </div>
      </div>
    </div>
  );
}
