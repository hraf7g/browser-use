'use client';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';

export default function Trust() {
  const { t } = useTranslation();

  return (
    <section className="py-20 border-y border-slate-100 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-slate-400 dark:text-slate-600 uppercase tracking-widest">{t.trust.title}</h2>
        </div>
        
        <div className="flex flex-wrap justify-center gap-12 md:gap-24 opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
          {/* Logo Placeholders with text */}
          {['DUBAI GOV', 'SAUDI ARAMCO', 'ETIHAD', 'NEOM', 'ADNOC'].map((logo, i) => (
            <div key={i} className="text-2xl font-black italic tracking-tighter text-slate-900 dark:text-white">
              {logo}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
