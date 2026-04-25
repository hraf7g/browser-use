'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';

const BilingualPanel = () => {
  const { t, dir } = useTranslation();
  return (
    <section className="py-24 overflow-hidden" dir={dir}>
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">{t.bilingualPanel.title}</h2>
          <p className="text-muted">{t.bilingualPanel.subtitle}</p>
        </div>

        <div className="flex flex-col lg:flex-row items-center justify-center gap-12 lg:gap-0">
          {/* Arabic Scanned Card */}
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="w-full max-w-md bg-slate-50 dark:bg-navy-900 rounded-3xl p-8 border border-border relative overflow-hidden group"
          >
            <div className={`absolute top-0 ${dir === 'rtl' ? 'right-0 rounded-bl-xl' : 'left-0 rounded-br-xl'} bg-primary/10 text-primary text-[10px] font-bold px-4 py-1.5`}>{t.bilingualPanel.arCardTag}</div>
            <div className="space-y-6 opacity-80">
              <div className="flex items-center gap-3 border-b border-border pb-4">
                <div className="w-12 h-12 bg-white dark:bg-navy-800 rounded border border-border flex items-center justify-center font-bold text-xs">{t.bilingualPanel.arCardLogo}</div>
                <div>
                  <div className="h-3 w-32 bg-slate-200 dark:bg-navy-700 rounded mb-2" />
                  <div className="h-2 w-20 bg-slate-100 dark:bg-navy-800 rounded" />
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center bg-primary/5 p-3 rounded border-s-2 border-primary animate-pulse">
                  <div className="h-3 w-20 bg-primary/20 rounded" />
                  <span className="text-[11px] font-bold">{t.bilingualPanel.arCardBuyer}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded">
                  <div className="h-2 w-40 bg-slate-200 dark:bg-navy-700 rounded" />
                  <span className="text-[11px]">{t.bilingualPanel.arCardSubject}</span>
                </div>
                <div className="flex justify-between items-center bg-success/5 p-3 rounded border-s-2 border-success">
                  <div className="h-3 w-24 bg-success/20 rounded" />
                  <span className="text-[11px] font-bold">{t.bilingualPanel.arCardValue}</span>
                </div>
                <div className="flex justify-between items-center p-3 rounded border-s-2 border-amber-500 bg-amber-500/5">
                  <div className="h-3 w-16 bg-amber-500/20 rounded" />
                  <span className="text-[11px] font-bold">{t.bilingualPanel.arCardDate}</span>
                </div>
              </div>
              <div className="h-20 w-full border-t border-dashed border-border pt-4 text-[10px] text-start leading-relaxed text-muted">
                {t.bilingualPanel.arCardText}
              </div>
            </div>
          </motion.div>

          {/* Center Connector */}
          <div className="flex flex-col items-center z-10 -mx-6">
            <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center shadow-2xl shadow-primary/40 relative">
              <motion.div 
                animate={{ scale: [1, 1.4, 1], opacity: [0.3, 0, 0.3] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="absolute inset-0 bg-primary rounded-full"
              />
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
            </div>
            <div className="h-12 w-px bg-gradient-to-b from-primary to-transparent lg:hidden" />
            <div className="hidden lg:block w-32 h-px bg-gradient-to-l from-primary via-primary to-transparent" />
            <span className="mt-2 text-[10px] font-bold uppercase tracking-widest text-primary">{t.bilingualPanel.centerTag}</span>
          </div>

          {/* English Output Card */}
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="w-full max-w-md bg-white dark:bg-navy-800 rounded-3xl p-8 border border-primary/20 shadow-2xl relative overflow-hidden"
          >
            <div className={`absolute top-0 ${dir === 'rtl' ? 'left-0 rounded-br-xl' : 'right-0 rounded-bl-xl'} bg-success/10 text-success text-[10px] font-bold px-4 py-1.5`}>{t.bilingualPanel.enCardTag}</div>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="text-lg font-bold text-navy-900 dark:text-white">{t.bilingualPanel.enCardTitle}</div>
                <div className="bg-primary/10 text-primary text-[10px] font-bold px-2 py-0.5 rounded">ID: #DXB-882</div>
              </div>
              <div className="space-y-4">
                <div className="flex flex-col gap-1 border-b border-border pb-3">
                  <span className="text-[10px] text-muted uppercase font-bold tracking-tight">{t.bilingualPanel.buyerLabel}</span>
                  <span className="text-sm font-semibold">{t.bilingualPanel.buyerValue}</span>
                </div>
                <div className="flex flex-col gap-1 border-b border-border pb-3">
                  <span className="text-[10px] text-muted uppercase font-bold tracking-tight">{t.bilingualPanel.valueLabel}</span>
                  <span className="text-sm font-bold text-primary">{t.bilingualPanel.valueValue}</span>
                </div>
                <div className="flex flex-col gap-1 border-b border-border pb-3">
                  <span className="text-[10px] text-muted uppercase font-bold tracking-tight">{t.bilingualPanel.dateLabel}</span>
                  <span className="text-sm font-semibold">{t.bilingualPanel.dateValue}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] text-muted uppercase font-bold tracking-tight">{t.bilingualPanel.catLabel}</span>
                  <span className="text-sm font-semibold">{t.bilingualPanel.catValue}</span>
                </div>
              </div>
              
              <div className="mt-8 pt-6 border-t border-dashed border-border">
                <div className="flex items-center justify-between bg-emerald-500/5 p-4 rounded-xl border border-emerald-500/20">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                      <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-emerald-600">{t.bilingualPanel.matchStatus}</div>
                      <div className="text-[10px] text-emerald-600/70">{t.bilingualPanel.matchReason}</div>
                    </div>
                  </div>
                  <div className="text-2xl font-black text-emerald-600">{t.bilingualPanel.matchScore}</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default BilingualPanel;
