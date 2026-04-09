'use client';
import { useTranslation } from '@/context/language-context';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Minus } from 'lucide-react';
import { useState } from 'react';

export default function FAQ() {
  const { t } = useTranslation();
  const [open, setOpen] = useState<number | null>(0);

  const items = [
    { q: t.faq.q1, a: t.faq.a1 },
    { q: t.faq.q2, a: t.faq.a2 },
  ];

  return (
    <section id="faq" className="py-24 bg-slate-50 dark:bg-slate-950">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-4xl font-bold text-center mb-16">{t.faq.title}</h2>
        
        <div className="space-y-4">
          {items.map((item, i) => (
            <div key={i} className="border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 overflow-hidden">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full px-8 py-6 flex items-center justify-between text-left font-bold text-lg"
              >
                <span>{item.q}</span>
                {open === i ? <Minus size={20} /> : <Plus size={20} />}
              </button>
              
              <AnimatePresence>
                {open === i && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    exit={{ height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="px-8 pb-6 text-slate-600 dark:text-slate-400">
                      {item.a}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
