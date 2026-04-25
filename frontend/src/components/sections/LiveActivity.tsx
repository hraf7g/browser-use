'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from '@/context/language-context';

const STATUS_COLORS: Record<string, string> = {
  emerald: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  blue: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  purple: 'bg-purple-500/10 text-purple-600 border-purple-500/20',
  amber: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  teal: 'bg-teal-500/10 text-teal-600 border-teal-500/20',
};

const LiveActivity = () => {
  const { t, dir } = useTranslation();
  
  const eventsList = t.liveActivityStream.events;
  const [items, setItems] = useState(eventsList.slice(0, 4));
  const [counter, setCounter] = useState(4);

  useEffect(() => {
    // Reset when language changes
    setItems(eventsList.slice(0, 4));
    setCounter(4);
  }, [t]);

  useEffect(() => {
    const interval = setInterval(() => {
      setItems(prev => {
        const nextItem = eventsList[counter % eventsList.length];
        setCounter(c => c + 1);
        return [nextItem, ...prev.slice(0, 4)];
      });
    }, 2500);
    return () => clearInterval(interval);
  }, [counter, eventsList]);

  return (
    <section className="py-24 bg-navy-900 text-white overflow-hidden" dir={dir}>
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold mb-6">{t.liveActivityStream.title}</h2>
            <p className="text-navy-300 text-lg leading-relaxed mb-8">
              {t.liveActivityStream.subtitle}
            </p>
            <div className="flex gap-12">
              <div>
                <div className="text-3xl font-bold text-primary mb-1">{t.liveActivityStream.scannedPagesCount}</div>
                <div className="text-xs text-navy-400 font-bold uppercase tracking-widest">{t.liveActivityStream.scannedPagesLabel}</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-success mb-1">{t.liveActivityStream.monitoredSourcesCount}</div>
                <div className="text-xs text-navy-400 font-bold uppercase tracking-widest">{t.liveActivityStream.monitoredSourcesLabel}</div>
              </div>
            </div>
          </div>

          <div className="relative">
            {/* Glossy Overlay */}
            <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-navy-900 to-transparent z-10 pointer-events-none" />
            <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-navy-900 to-transparent z-10 pointer-events-none" />

            <div className="h-[400px] flex flex-col gap-4">
              <AnimatePresence mode="popLayout">
                {items.map((event: any, idx: number) => (
                  <motion.div
                    key={`${event.time}-${counter}-${idx}`}
                    initial={{ opacity: 0, y: -20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.95 }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className="bg-navy-800/50 border border-white/5 p-4 rounded-2xl flex items-center gap-4"
                  >
                    <div className="text-xs font-mono text-navy-400 bg-navy-900/50 px-2 py-1 rounded">
                      {event.time}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-bold mb-0.5">{event.text}</div>
                      <div className="text-[10px] text-navy-400">{event.sub}</div>
                    </div>
                    <div className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${STATUS_COLORS[event.color]}`}>
                      {event.status}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default LiveActivity;
