'use client';
import { useTranslation } from '@/context/language-context';
import { Search, Bell, Menu } from 'lucide-react';
import { ThemeToggle } from '../ui/theme-toggle';
import { LanguageToggle } from '../ui/language-toggle';
import AppUserMenu from './app-user-menu';

export default function AppTopbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { t } = useTranslation();

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md px-4 lg:px-8 flex items-center justify-between">
      {/* Mobile Toggle & Page Title */}
      <div className="flex items-center gap-4">
        <button 
          onClick={onMenuClick}
          className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
        >
          <Menu size={20} />
        </button>
        <h1 className="text-sm lg:text-base font-bold text-slate-900 dark:text-white">
          {t.app.nav.dashboard}
        </h1>
      </div>

      {/* Search Bar Placeholder */}
      <div className="hidden md:flex flex-1 max-w-md mx-8">
        <div className="relative w-full group">
          <Search className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={16} />
          <input 
            type="text" 
            placeholder={t.app.topbar.search}
            className="w-full bg-slate-100 dark:bg-slate-900 border-none rounded-full ps-10 pe-4 py-2 text-sm focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 lg:gap-4">
        <div className="hidden sm:flex items-center gap-2">
          <LanguageToggle />
          <ThemeToggle />
        </div>
        <button className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full relative">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-slate-950" />
        </button>
        <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-1" />
        <AppUserMenu />
      </div>
    </header>
  );
}
