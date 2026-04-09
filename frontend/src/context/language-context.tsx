'use client';
import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from 'react';
import { Language, translations } from '@/lib/translations';

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  dir: 'ltr' | 'rtl';
  t: typeof translations.en;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);
const STORAGE_KEY = 'lang';
const LANGUAGE_EVENT = 'language-change';

function readLanguageSnapshot(): Language {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const saved = window.localStorage.getItem(STORAGE_KEY);
  return saved === 'ar' || saved === 'en' ? saved : 'en';
}

function subscribeLanguageStore(onStoreChange: () => void) {
  const handleStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY) {
      onStoreChange();
    }
  };
  const handleLanguageEvent = () => onStoreChange();

  window.addEventListener('storage', handleStorage);
  window.addEventListener(LANGUAGE_EVENT, handleLanguageEvent);

  return () => {
    window.removeEventListener('storage', handleStorage);
    window.removeEventListener(LANGUAGE_EVENT, handleLanguageEvent);
  };
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const lang = useSyncExternalStore(
    subscribeLanguageStore,
    readLanguageSnapshot,
    () => 'en'
  ) as Language;

  useEffect(() => {
    document.documentElement.dir = translations[lang].dir;
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<LanguageContextType>(
    () => ({
      lang,
      setLang: (nextLang) => {
        window.localStorage.setItem(STORAGE_KEY, nextLang);
        window.dispatchEvent(new Event(LANGUAGE_EVENT));
      },
      dir: translations[lang].dir as 'ltr' | 'rtl',
      t: translations[lang]
    }),
    [lang]
  );

  return (
    <LanguageContext.Provider value={value}>
      <div className={translations[lang].font}>{children}</div>
    </LanguageContext.Provider>
  );
}

export const useTranslation = () => {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useTranslation must be used within LanguageProvider');
  return context;
};
