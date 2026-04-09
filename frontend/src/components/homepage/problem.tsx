'use client';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';
import { AlertCircle, Clock, Zap } from 'lucide-react';

export default function Problem() {
  const { t } = useTranslation();
  
  const icons = [AlertCircle, Clock, Zap];

  return (
    <section className="py-24 bg-slate-50 dark:bg-slate-950">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-emerald-600 font-bold tracking-wider uppercase text-sm"
          >
            {t.problem.tag}
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-4 text-4xl font-bold text-slate-900 dark:text-white"
          >
            {t.problem.title}
          </motion.h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {t.problem.items.map((item: any, i: number) => {
            const Icon = icons[i % icons.length];
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="group p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 transition-all hover:shadow-2xl hover:shadow-emerald-500/5"
              >
                <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Icon className="text-emerald-600" size={28} />
                </div>
                <h3 className="text-xl font-bold mb-4 text-slate-900 dark:text-white">{item.title}</h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{item.desc}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
