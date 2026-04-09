'use client';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { ThemeToggle } from '../ui/theme-toggle';
import { LanguageToggle } from '../ui/language-toggle';
import Link from 'next/link';

export default function Header() {
  const { t } = useTranslation();

  return (
    <motion.header 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 w-full z-50 border-b border-slate-200/60 dark:border-slate-800/50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md"
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-xl font-bold tracking-tighter flex items-center gap-2 text-slate-900 dark:text-white">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-blue-500/20">TW</div>
            <span>Tender<span className="text-blue-600">Watch</span></span>
          </Link>
          
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600 dark:text-slate-400">
            <Link href="#features" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">{t.nav.features}</Link>
            <Link href="#how" className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors">{t.nav.howItWorks}</Link>
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
    </motion.header>
  );
}
