'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';

const HowItWorks = () => {
  const { t, dir } = useTranslation();

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'Globe2':
        return (
          <div className="relative w-12 h-12 flex items-center justify-center">
            <div className="absolute inset-0 border-2 border-primary rounded-full animate-spin-slow" style={{ borderRightColor: 'transparent' }} />
            <div className="w-5 h-5 border-2 border-primary rounded-full" />
            <div className="absolute w-3 h-0.5 bg-primary bottom-2 right-2 rotate-45" />
          </div>
        );
      case 'FileSearch':
        return (
          <div className="relative w-12 h-12 flex items-center justify-center">
            <div className="w-8 h-10 border-2 border-primary rounded-sm relative">
              <div className="absolute top-2 left-2 right-2 h-0.5 bg-primary/30" />
              <div className="absolute top-4 left-2 right-2 h-0.5 bg-primary/30" />
              <div className="absolute top-6 left-2 right-4 h-0.5 bg-primary/30" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-primary rounded-full flex items-center justify-center text-[10px] text-white font-bold">+</div>
          </div>
        );
      case 'Fingerprint':
        return (
          <div className="relative w-12 h-12 flex items-center justify-center">
            <div className="flex gap-0.5 items-end h-6">
              <div className="w-1.5 h-3 bg-primary/40 rounded-t-sm" />
              <div className="w-1.5 h-6 bg-primary rounded-t-sm" />
              <div className="w-1.5 h-4 bg-primary/60 rounded-t-sm" />
            </div>
            <div className="absolute inset-0 border border-primary/20 rounded-xl rotate-45" />
          </div>
        );
      case 'BellRing':
        return (
          <div className="relative w-12 h-12 flex items-center justify-center">
            <div className="w-7 h-8 border-2 border-primary rounded-t-full rounded-b-sm relative">
              <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-2 h-2 border-2 border-primary rounded-full" />
            </div>
            <div className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full animate-ping" />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <section id="how-it-works" className="py-24 bg-slate-50/50 dark:bg-navy-800/30" dir={dir}>
      <div className="container mx-auto px-6">
        <div className="text-center mb-20">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl md:text-4xl font-bold mb-4"
          >
            {t.howItWorks.title}
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-muted max-w-2xl mx-auto"
          >
            {t.howItWorks.subtitle}
          </motion.p>
        </div>

        <div className="relative">
          {/* Connector Line (Desktop) */}
          <div className="hidden lg:block absolute top-12 left-0 right-0 h-0.5 bg-border z-0 overflow-hidden">
            <motion.div 
              initial={{ x: dir === 'rtl' ? '-100%' : '100%' }}
              whileInView={{ x: '0%' }}
              viewport={{ once: true }}
              transition={{ duration: 1.5, ease: "easeInOut" }}
              className="w-full h-full bg-primary"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
            {t.howItWorks.steps.map((step: any, idx: number) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.15, duration: 0.5 }}
                className="relative z-10 text-center flex flex-col items-center group"
              >
                <div className="w-20 h-20 bg-white dark:bg-navy-900 rounded-2xl border border-border flex items-center justify-center mb-6 group-hover:border-primary/50 group-hover:shadow-xl group-hover:shadow-primary/5 transition-all duration-300">
                  {getIcon(step.icon)}
                </div>
                <h3 className="text-lg font-bold mb-3">{step.t}</h3>
                <p className="text-sm text-muted leading-relaxed">{step.d}</p>
                
                {/* Step Number Badge */}
                <div className="absolute top-0 right-1/2 translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-primary text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {step.n}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
