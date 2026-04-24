'use client';
import { useTranslation } from '@/context/language-context';
import { ThemeToggle } from '../ui/theme-toggle';
import { LanguageToggle } from '../ui/language-toggle';
import Link from 'next/link';

export default function Header() {
  const { t } = useTranslation();

  return (
    <header className="fixed top-0 w-full z-50 border-b border-slate-200/60 dark:border-slate-800/50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3 text-slate-900 dark:text-white">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-sm font-black text-white shadow-lg shadow-blue-500/20">TW</div>
            <span className="text-base font-black tracking-tight">
              Tender<span className="text-blue-600">Watch</span>
            </span>
          </Link>
          
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600 dark:text-slate-400">
            <Link href="#features" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">{t.nav.features}</Link>
            <Link href="#how" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">{t.nav.howItWorks}</Link>
            <Link href="#solutions" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">{t.nav.solutions}</Link>
            <Link href="#activity" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">{t.homepageActivity.badge}</Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <LanguageToggle />
          <ThemeToggle />
          <div className="h-4 w-[1px] bg-slate-200 dark:bg-slate-800 mx-1" />
          <Link href="/login" className="hidden sm:block text-sm font-semibold text-slate-700 dark:text-slate-300 hover:text-blue-600 transition-colors px-3">
            {t.nav.signIn}
          </Link>
          <Link href="/signup" className="px-5 py-2 bg-slate-900 dark:bg-white text-white dark:text-slate-950 text-sm font-bold rounded-full transition-all hover:shadow-xl hover:-translate-y-0.5 active:scale-95">
            {t.nav.getStarted}
          </Link>
        </div>
      </div>
    </header>
  );
}
