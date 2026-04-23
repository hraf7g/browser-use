'use client';
import { useTranslation } from '@/context/language-context';

export const LanguageToggle = () => {
  const { lang, setLang } = useTranslation();
  const isEnglish = lang === 'en';

  return (
    <button
      type="button"
      onClick={() => setLang(lang === 'en' ? 'ar' : 'en')}
      aria-label={isEnglish ? 'Switch language to Arabic' : 'التبديل إلى الإنجليزية'}
      className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-100/90 p-1 text-sm font-bold text-slate-900 transition-colors hover:bg-slate-200 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
    >
      <span
        className={`rounded-full px-2.5 py-1 transition-colors ${
          isEnglish
            ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-800 dark:text-white'
            : 'text-slate-500 dark:text-slate-400'
        }`}
      >
        EN
      </span>
      <span
        className={`rounded-full px-2.5 py-1 transition-colors ${
          !isEnglish
            ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-800 dark:text-white'
            : 'text-slate-500 dark:text-slate-400'
        }`}
      >
        العربية
      </span>
    </button>
  );
};
