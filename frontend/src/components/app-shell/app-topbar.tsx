'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from '@/context/language-context';
import { Search, Bell, Menu } from 'lucide-react';
import { ThemeToggle } from '../ui/theme-toggle';
import { LanguageToggle } from '../ui/language-toggle';
import AppUserMenu from './app-user-menu';

export default function AppTopbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { t } = useTranslation();
  const pathname = usePathname();
  const pageTitle =
    pathname.startsWith('/tenders') ? t.app.nav.tenders
      : pathname.startsWith('/notifications') ? t.notifications.title
        : pathname.startsWith('/activity') ? t.app.nav.activity
          : t.app.nav.dashboard;

  return (
    <header className="sticky top-0 z-30 flex min-h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-3 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/80 sm:px-4 lg:px-8">
      {/* Mobile Toggle & Page Title */}
      <div className="flex min-w-0 items-center gap-2 sm:gap-4">
        <button 
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>
        <h1 className="truncate text-sm font-bold text-slate-900 dark:text-white lg:text-base">
          {pageTitle}
        </h1>
      </div>

      {/* Search entry point */}
      <div className="hidden flex-1 max-w-md mx-4 md:flex lg:mx-8">
        <Link href="/tenders" className="relative w-full group block">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={16} />
          <span className="flex w-full items-center rounded-full bg-slate-100 dark:bg-slate-900 border-none ps-10 pe-4 py-2 text-sm text-slate-500 dark:text-slate-400 transition-all group-hover:bg-slate-200/60 dark:group-hover:bg-slate-800">
            {t.app.topbar.search}
          </span>
        </Link>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-1 sm:gap-2 lg:gap-4">
        <Link
          href="/tenders"
          className="rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 md:hidden"
          aria-label={t.app.topbar.search}
        >
          <Search size={18} />
        </Link>
        <div className="hidden sm:flex items-center gap-2">
          <LanguageToggle />
          <ThemeToggle />
        </div>
        <Link href="/notifications" className="rounded-full p-2 text-slate-500 transition-colors hover:bg-slate-100 dark:hover:bg-slate-800 relative" aria-label={t.app.topbar.notifications}>
          <Bell size={18} className="sm:h-5 sm:w-5" />
        </Link>
        <div className="mx-1 hidden h-6 w-px bg-slate-200 dark:bg-slate-800 sm:block" />
        <AppUserMenu />
      </div>
    </header>
  );
}
