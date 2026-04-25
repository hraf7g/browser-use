'use client';

import React from 'react';
import { motion } from 'framer-motion';
import AgentBrowser from './AgentBrowser';
import { useTranslation } from '@/context/language-context';



const HeroSection = () => {
  const { t, dir } = useTranslation();
  return (
    <section className="relative min-h-screen flex items-center pt-20 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/4 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/4 w-[600px] h-[600px] bg-success/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="container mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        {/* Copy Layer */}
        <motion.div 
          initial={{ opacity: 0, x: 50 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`z-10 ${dir === "rtl" ? "text-right" : "text-left"}`}
        >
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight mb-6 text-balance" dir={dir}>{t.hero.title}</h1>
          <p className="text-lg md:text-xl text-muted leading-relaxed mb-6" dir={dir}>{t.hero.subtitle}</p>
          

          <div className="flex flex-wrap items-center justify-start gap-4">
            <button className="bg-primary hover:bg-primary/90 text-white px-8 py-4 rounded-full font-bold text-lg transition-all shadow-xl shadow-primary/25 hover:scale-105 active:scale-95">
              {t.hero.ctaPrimary}
            </button>
            <a 
              href="#how-it-works"
              className="px-8 py-4 rounded-full font-bold text-lg border border-border hover:bg-slate-50 dark:hover:bg-navy-800 transition-all"
            >
              {t.hero.ctaSecondary}
            </a>
          </div>

                    <div className={`mt-12 flex items-center gap-6 opacity-60 overflow-hidden w-full max-w-xl ${dir === 'rtl' ? 'ml-auto' : 'mr-auto'}`}>
            <span className="text-[10px] font-bold uppercase tracking-widest whitespace-nowrap" dir={dir}>
              {t.hero.visual.sourcesEyebrow}:
            </span>
            <div 
              className="relative flex-1 overflow-hidden"
              dir="ltr"
              style={{
                maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)',
                WebkitMaskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)'
              }}
            >
              <motion.div 
                className="flex gap-8 whitespace-nowrap w-max"
                animate={{ x: ["0%", "-50%"] }}
                transition={{ duration: 30, ease: "linear", repeat: Infinity }}
              >
                {[...t.scrollingSources, ...t.scrollingSources].map((source: string, i: number) => (
                  <div key={i} className="text-xs font-bold flex items-center gap-2 grayscale transition-all hover:grayscale-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    {source}
                  </div>
                ))}
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Browser Layer */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          whileInView={{ opacity: 1, scale: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative lg:scale-[1.02] xl:scale-105"
        >
          <AgentBrowser />
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;
