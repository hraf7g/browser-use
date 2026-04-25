'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { SourceLogo } from '@/components/ui/SourceLogo';
import { Globe, Bot, Zap, Globe2, ShieldCheck, Target } from 'lucide-react';





const FeaturesCoverage = () => {
  const { t, dir } = useTranslation();
  
  return (
    <section className="py-24 bg-slate-50 dark:bg-navy-800/50 overflow-hidden" dir={dir}>
      <div className="container mx-auto px-6">
        
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-20">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl md:text-5xl font-bold mb-6"
          >
            {t.coverage.title} <span className="text-primary">{t.coverage.titleAccent}</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-muted"
          >
            {t.coverage.description}
          </motion.p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          
          {/* Features Grid */}
          <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            {t.featuresGrid.map((feature: any, i: number) => {
              const icons = [
                <Bot key={0} className="w-6 h-6 text-primary" />,
                <Globe2 key={1} className="w-6 h-6 text-primary" />,
                <Target key={2} className="w-6 h-6 text-primary" />,
                <Zap key={3} className="w-6 h-6 text-primary" />,
                <Globe key={4} className="w-6 h-6 text-primary" />,
                <ShieldCheck key={5} className="w-6 h-6 text-primary" />
              ];
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="bg-white dark:bg-navy-900 p-6 rounded-2xl border border-border shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                    {icons[i]}
                  </div>
                  <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                  <p className="text-muted leading-relaxed text-sm">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* Coverage Panel */}
          <motion.div
            initial={{ opacity: 0, x: dir === 'rtl' ? 30 : -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-4 bg-gradient-to-br from-primary to-primary/90 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden"
          >
            <div className={`absolute top-0 ${dir === 'rtl' ? 'left-0 -translate-x-1/3' : 'right-0 translate-x-1/3'} -translate-y-1/2 w-64 h-64 bg-white/10 rounded-full blur-3xl pointer-events-none`} />
            
            <h3 className="text-2xl font-bold mb-2 relative z-10">{t.coverage.sourcesTitle}</h3>
            <p className="text-white/80 text-sm mb-6 relative z-10">
              {t.coverage.sourcesSubtitle}
            </p>

            {/* Streaming Marquee Container */}
            <div 
              className="relative h-80 overflow-hidden rounded-xl border border-white/20 bg-black/10 p-4 z-10 shadow-inner"
              style={{
                maskImage: 'linear-gradient(to bottom, transparent, black 10%, black 90%, transparent)',
                WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 10%, black 90%, transparent)'
              }}
            >
              <motion.div
                animate={{ y: ["0%", "-50%"] }}
                transition={{ duration: 25, ease: "linear", repeat: Infinity }}
                className="flex flex-col gap-6"
              >
                {[...t.coverageSources, ...t.coverageSources].map((country: any, i: number) => (
                  <div key={i} className="flex flex-col gap-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{country.flag}</span>
                      <span className="font-bold text-lg">{country.country}</span>
                      <span className={`relative flex h-2 w-2 ${dir === 'rtl' ? 'mr-auto' : 'ml-auto'}`}>
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                      </span>
                    </div>
                    <div className="flex flex-col gap-2 ps-9">
                      {country.portals.map((portal: string, j: number) => (
                        <div key={j} className="flex items-center gap-3 bg-white/10 p-2 rounded-lg backdrop-blur-sm border border-white/10 shadow-sm">
                          <SourceLogo portalKey={portal} size={16} className="bg-white/20 text-white" />
                          <span className="text-sm font-medium">{portal}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </motion.div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/20 relative z-10">
              <p className="text-sm font-bold flex items-center justify-between">
                <span>{t.coverage.newMarkets}</span>
                <span className="bg-white text-primary px-2 py-0.5 rounded text-[10px] animate-pulse">
                  {t.coverage.exploring}
                </span>
              </p>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
};

export default FeaturesCoverage;
