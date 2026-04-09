'use client';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';

export default function HowItWorks() {
  const { t } = useTranslation();

  return (
    <section id="how" className="py-24 bg-slate-50 dark:bg-slate-950">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">{t.howItWorks.title}</h2>
        </div>
        
        <div className="grid md:grid-cols-4 gap-8">
          {t.howItWorks.steps.map((step: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="relative"
            >
              <div className="text-6xl font-black text-slate-200 dark:text-slate-800 mb-4">{step.n}</div>
              <h3 className="text-xl font-bold mb-2">{step.t}</h3>
              <p className="text-slate-600 dark:text-slate-400">{step.d}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
