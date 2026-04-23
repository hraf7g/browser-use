'use client';

import { useTranslation } from '@/context/language-context';
import { AlertCircle, Clock, Zap } from 'lucide-react';

export default function Problem() {
  const { t, lang } = useTranslation();
  const icons = [AlertCircle, Clock, Zap];

  return (
    <section className="bg-slate-50 py-20 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto mb-14 max-w-3xl text-center">
          <span className={`text-sm font-bold text-emerald-600 ${lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.24em]'}`}>
            {t.problem.tag}
          </span>
          <h2 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 dark:text-white">
            {t.problem.title}
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {t.problem.items.map((item: { title: string; desc: string }, i: number) => {
            const Icon = icons[i % icons.length];

            return (
              <div
                key={i}
                className="group rounded-3xl border border-slate-200 bg-white p-8 transition-all hover:border-emerald-500/50 hover:shadow-2xl hover:shadow-emerald-500/5 dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 transition-transform group-hover:scale-110 dark:bg-emerald-900/20">
                  <Icon className="text-emerald-600" size={28} />
                </div>
                <h3 className="mb-4 text-xl font-bold text-slate-900 dark:text-white">{item.title}</h3>
                <p className={`text-slate-600 dark:text-slate-400 ${lang === 'ar' ? 'leading-8' : 'leading-7'}`}>
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
