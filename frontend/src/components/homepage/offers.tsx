'use client';

import { useTranslation } from '@/context/language-context';
import { Bell, Globe, Search, Zap } from 'lucide-react';

export default function Offers() {
  const { t, lang } = useTranslation();

  const features = [
    {
      icon: Bell,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-900/10',
      ...t.features.items[0],
      span: 'col-span-12 md:col-span-5',
    },
    {
      icon: Search,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50 dark:bg-indigo-900/10',
      ...t.features.items[1],
      span: 'col-span-12 md:col-span-7',
    },
    {
      icon: Globe,
      color: 'text-violet-600',
      bg: 'bg-violet-50 dark:bg-violet-900/10',
      ...t.features.items[2],
      span: 'col-span-12 md:col-span-7',
    },
    {
      icon: Zap,
      color: 'text-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-900/10',
      ...t.features.items[3],
      span: 'col-span-12 md:col-span-5',
    },
  ];

  return (
    <section id="features" className="bg-slate-50/70 py-20 dark:bg-slate-950/50">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-12 flex max-w-3xl flex-col gap-4">
          <p className={`text-sm font-bold text-blue-600 ${lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.24em]'}`}>
            {t.productPreview.badge}
          </p>
          <h2 className="text-4xl font-bold tracking-tight text-slate-950 dark:text-white">
            {t.productPreview.title}
          </h2>
          <p className={`text-lg text-slate-600 dark:text-slate-400 ${lang === 'ar' ? 'leading-9' : 'leading-8'}`}>
            {t.productPreview.subtitle}
          </p>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {features.map((feature, i) => (
            <div
              key={i}
              className={`${feature.span} rounded-3xl border border-slate-200 bg-white p-8 transition-all hover:shadow-2xl hover:shadow-blue-500/5 dark:border-slate-800 dark:bg-slate-900`}
            >
              <div className={`mb-6 flex h-12 w-12 items-center justify-center rounded-2xl ${feature.bg}`}>
                <feature.icon className={feature.color} size={24} />
              </div>
              <h3 className="mb-3 text-xl font-bold leading-tight text-slate-900 dark:text-white">
                {feature.title}
              </h3>
              <p className={`text-sm text-slate-600 dark:text-slate-400 md:text-base ${lang === 'ar' ? 'leading-8' : 'leading-7'}`}>
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
