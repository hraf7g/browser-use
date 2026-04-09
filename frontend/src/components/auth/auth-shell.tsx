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
    <div className="min-h-screen flex flex-col bg-white dark:bg-slate-950 transition-colors duration-300">
      <AuthHeader />
      <div className="flex-1 flex">
        {/* Form Side */}
        <main className="flex-1 flex items-center justify-center p-6 lg:p-12">
          <motion.div 
            initial={{ opacity: 0, x: lang === 'ar' ? 20 : -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-full max-w-md"
          >
            {children}
          </motion.div>
        </main>

        {/* Brand Side (Desktop Only) */}
        <aside className="hidden lg:flex lg:w-[45%] xl:w-[50%] bg-slate-50 dark:bg-slate-900 border-s border-slate-200 dark:border-slate-800 relative overflow-hidden">
          <AuthBrandPanel />
        </aside>
      </div>
    </div>
  );
}
