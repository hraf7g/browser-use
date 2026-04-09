'use client';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';

export const LanguageToggle = () => {
  const { lang, setLang } = useTranslation();

  return (
    <button
      onClick={() => setLang(lang === 'en' ? 'ar' : 'en')}
      className="px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-900 text-sm font-bold border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer"
    >
      <motion.span
        key={lang}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        {lang === 'en' ? 'AR' : 'EN'}
      </motion.span>
    </button>
  );
};
