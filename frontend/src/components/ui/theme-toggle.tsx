'use client';
import { useTheme } from '@/context/theme-context';
import { Sun, Moon } from 'lucide-react';

export const ThemeToggle = () => {
  const { theme, setTheme } = useTheme();

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="relative inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-slate-100 text-slate-900 transition-colors dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
      aria-label="Toggle theme"
    >
      <Sun
        size={20}
        className={`absolute transition-all duration-200 ${theme === 'dark' ? 'scale-75 rotate-90 opacity-0' : 'scale-100 rotate-0 opacity-100'}`}
      />
      <Moon
        size={20}
        className={`absolute transition-all duration-200 ${theme === 'dark' ? 'scale-100 rotate-0 opacity-100' : 'scale-75 -rotate-90 opacity-0'}`}
      />
    </button>
  );
};
