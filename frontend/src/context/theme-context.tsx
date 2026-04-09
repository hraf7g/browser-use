'use client';

import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'theme';
const THEME_EVENT = 'theme-change';

function readThemeSnapshot(): Theme {
  if (typeof window === 'undefined') {
    return 'system';
  }

  const saved = window.localStorage.getItem(STORAGE_KEY);
  return saved === 'light' || saved === 'dark' || saved === 'system'
    ? saved
    : 'system';
}

function readSystemDarkSnapshot(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function subscribeThemeStore(onStoreChange: () => void) {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handleStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) {
      onStoreChange();
    }
  };
  const handleThemeEvent = () => onStoreChange();

  window.addEventListener('storage', handleStorage);
  window.addEventListener(THEME_EVENT, handleThemeEvent);
  mediaQuery.addEventListener('change', onStoreChange);

  return () => {
    window.removeEventListener('storage', handleStorage);
    window.removeEventListener(THEME_EVENT, handleThemeEvent);
    mediaQuery.removeEventListener('change', onStoreChange);
  };
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSyncExternalStore(
    subscribeThemeStore,
    readThemeSnapshot,
    () => 'system'
  ) as Theme;
  const systemDark = useSyncExternalStore(
    subscribeThemeStore,
    readSystemDarkSnapshot,
    () => false
  );

  useEffect(() => {
    const root = document.documentElement;
    const resolvedDark = theme === 'dark' || (theme === 'system' && systemDark);

    root.classList.toggle('dark', resolvedDark);
  }, [systemDark, theme]);

  const value = useMemo<ThemeContextType>(
    () => ({
      theme,
      setTheme: (nextTheme) => {
        window.localStorage.setItem(STORAGE_KEY, nextTheme);
        window.dispatchEvent(new Event(THEME_EVENT));
      },
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }

  return context;
}
