'use client';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { ArrowRight, ShieldCheck } from 'lucide-react';

export default function Hero() {
  const { t, lang } = useTranslation();

  return (
    <section className="relative pt-40 pb-20 overflow-hidden bg-white dark:bg-slate-950">
      {/* Dynamic Background Mesh */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent -z-10 opacity-70 dark:opacity-40" />
      
      <div className="max-w-7xl mx-auto px-6 text-center flex flex-col items-center relative z-10">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] md:text-xs font-bold uppercase tracking-widest mb-8 text-slate-600 dark:text-slate-400"
        >
          <ShieldCheck size={14} className="text-blue-600" />
          {t.hero.badge}
        </motion.div>

        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl md:text-7xl lg:text-8xl font-extrabold tracking-tight mb-8 leading-[1.15] md:leading-[1.1] text-slate-950 dark:text-white"
        >
          {/* Using text-slate-950 for light mode and a gradient for dark mode */}
          <span className="bg-gradient-to-b from-slate-900 via-slate-800 to-slate-600 dark:from-white dark:via-slate-200 dark:to-slate-500 bg-clip-text text-transparent">
            {t.hero.title}
          </span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="max-w-2xl text-lg md:text-xl text-slate-600 dark:text-slate-400 mb-12 leading-relaxed"
        >
          {t.hero.subtitle}
        </motion.p>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col sm:flex-row gap-4 mb-20"
        >
          <button className="px-8 py-4 bg-blue-600 text-white rounded-xl font-bold text-lg shadow-xl shadow-blue-500/25 hover:bg-blue-700 transition-all hover:-translate-y-1">
            {t.hero.ctaPrimary}
          </button>
          <button className="px-8 py-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white rounded-xl font-bold text-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-all flex items-center justify-center gap-2">
            {t.hero.ctaSecondary}
            <ArrowRight size={20} className={lang === 'ar' ? 'rotate-180' : ''} />
          </button>
        </motion.div>
      </div>
    </section>
  );
}
