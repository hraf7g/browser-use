'use client';

import { useTranslation } from '@/context/language-context';
import { CheckCircle2 } from 'lucide-react';

export default function AuthBrandPanel() {
  const { t, lang } = useTranslation();

  return (
    <div className="rounded-[32px] border border-slate-200 bg-slate-50/90 p-8 shadow-xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-none xl:p-10">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-sm font-black text-white shadow-lg shadow-blue-500/20">
          TW
        </div>
        <span className="text-base font-black tracking-tight text-slate-950 dark:text-white">
          Tender<span className="text-blue-600">Watch</span>
        </span>
      </div>

      <h2 className={`mt-8 text-3xl font-bold tracking-tight text-slate-950 dark:text-white ${lang === 'ar' ? 'leading-[1.4]' : 'leading-tight'}`}>
        {t.auth.brand.title}
      </h2>
      <p className={`mt-4 text-base text-slate-600 dark:text-slate-400 ${lang === 'ar' ? 'leading-8' : 'leading-7'}`}>
        {t.auth.brand.description}
      </p>

      <div className="mt-8 space-y-4">
        {[t.auth.brand.benefit1, t.auth.brand.benefit2].map((benefit) => (
          <div key={benefit} className="flex gap-3">
            <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-blue-600" />
            <p className="text-sm font-medium text-slate-600 dark:text-slate-300">{benefit}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
