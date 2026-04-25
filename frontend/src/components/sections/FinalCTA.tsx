'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';

const FinalCTA = () => {
  const { t, dir } = useTranslation();
  return (
    <section className="py-24 relative overflow-hidden" dir={dir}>
      {/* Background patterns */}
      <div className="absolute inset-0 bg-primary z-0" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.2),transparent)] z-1" />
      
      <div className="container mx-auto px-6 relative z-10 text-center text-white">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto"
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-8">{t.finalCTA.title}</h2>
          <p className="text-xl md:text-2xl text-white/80 mb-4 leading-relaxed">
            {t.finalCTA.subtitle}
          </p>
          <p className="text-sm font-bold text-white/40 uppercase tracking-[0.2em] mb-12">
            {t.finalCTA.subtext}
          </p>

          <div className="flex flex-wrap justify-center items-center gap-6">
            <button className="bg-white text-primary hover:bg-slate-50 px-10 py-5 rounded-full font-black text-xl transition-all shadow-2xl shadow-black/20 hover:scale-105 active:scale-95">
              {t.finalCTA.primaryBtn}
            </button>
            <a 
              href="mailto:contact@tenderwatch.ai"
              className="px-10 py-5 rounded-full font-bold text-xl border-2 border-white/30 hover:border-white hover:bg-white/10 transition-all"
            >
              {t.finalCTA.secondaryBtn}
            </a>
          </div>

          <div className="mt-20 flex flex-wrap justify-center gap-12 text-white/60">
            {t.finalCTA.stats.map((stat: any, i: number) => (
              <div key={i} className="flex flex-col items-center">
                <div className="text-2xl font-bold text-white">{stat.value}</div>
                <div className="text-[10px] font-bold uppercase tracking-widest">{stat.label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default FinalCTA;
