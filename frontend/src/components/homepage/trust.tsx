'use client';

import { useTranslation } from '@/context/language-context';

const trustPoints = {
  en: ['Real backend auth', 'Arabic + English', 'RTL / LTR aware', 'Production-ready cookies'],
  ar: ['مصادقة حقيقية', 'عربي + إنجليزي', 'دعم RTL / LTR', 'كوكيز جاهزة للإنتاج'],
} as const;

export default function Trust() {
  const { t, lang } = useTranslation();
  const points = trustPoints[lang];

  return (
    <section className="py-20 border-y border-slate-100 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-700 dark:text-slate-300 uppercase tracking-widest">
            {t.trust.title}
          </h2>
          <p className="mt-4 text-slate-500 dark:text-slate-400">{t.trust.subtitle}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {points.map((point) => (
            <div
              key={point}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-4 text-center text-sm font-semibold text-slate-700 shadow-sm dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200"
            >
              {point}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
