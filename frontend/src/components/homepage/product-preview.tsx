'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { useState, useEffect } from 'react';

export default function ProductPreview() {
  const { t, lang } = useTranslation();
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setLogs(prev => {
        const next = [t.activity.status[Math.floor(Math.random() * t.activity.status.length)], ...prev];
        return next.slice(0, 5);
      });
    }, 4000);
    return () => clearInterval(interval);
  }, [t.activity.status]);

  return (
    <section className="py-24 bg-slate-950 text-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <h2 className="text-4xl font-bold mb-6 tracking-tight">{t.activity.title}</h2>
          <p className="text-slate-400 text-lg mb-8">{t.activity.subtitle}</p>
          
          <div className="space-y-3 font-mono text-sm">
            <AnimatePresence mode="popLayout">
              {logs.map((log, i) => (
                <motion.div
                  key={log + i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1 - (i * 0.2), x: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-center gap-3 p-3 rounded bg-white/5 border border-white/10"
                >
                  <span className="text-blue-500 font-bold">[{new Date().toLocaleTimeString()}]</span>
                  <span>{log}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        <div className="relative">
          {/* Dashboard Visual Placeholder */}
          <div className="aspect-square bg-gradient-to-br from-blue-600/20 to-transparent rounded-full blur-3xl absolute inset-0" />
          <div className="relative border border-white/10 rounded-2xl bg-slate-900 p-2 shadow-2xl">
             <div className="bg-slate-950 rounded-xl aspect-[4/3] flex items-center justify-center border border-white/5">
                <div className="text-center">
                  <div className="text-4xl font-bold text-blue-500 mb-2">99.9%</div>
                  <div className="text-xs uppercase tracking-widest text-slate-500">{t.activity.uptime}</div>
                </div>
             </div>
          </div>
        </div>
      </div>
    </section>
  );
}
