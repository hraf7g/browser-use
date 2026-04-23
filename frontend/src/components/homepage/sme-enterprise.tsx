'use client';

import { useTranslation } from '@/context/language-context';
import { Building2, Shield } from 'lucide-react';

export default function SmeEnterprise() {
  const { t, lang } = useTranslation();

  return (
    <section className="py-20">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mx-auto mb-12 max-w-3xl text-center">
          <p className={`text-sm font-bold text-blue-600 ${lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.24em]'}`}>
            {t.smeEnterprise.eyebrow}
          </p>
          <h2 className="mt-4 text-4xl font-bold tracking-tight text-slate-950 dark:text-white">
            {t.smeEnterprise.title}
          </h2>
          <p className={`mt-4 text-lg text-slate-600 dark:text-slate-400 ${lang === 'ar' ? 'leading-9' : 'leading-8'}`}>
            {t.smeEnterprise.subtitle}
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl bg-blue-600 p-10 text-white transition-transform hover:-translate-y-1">
            <Building2 size={40} className="mb-6 opacity-80" />
            <h3 className="mb-4 text-3xl font-bold">{t.smeEnterprise.sme.title}</h3>
            <p className="text-lg leading-relaxed text-blue-100">{t.smeEnterprise.sme.desc}</p>
          </div>

          <div className="rounded-3xl bg-slate-900 p-10 text-white transition-transform hover:-translate-y-1">
            <Shield size={40} className="mb-6 opacity-80" />
            <h3 className="mb-4 text-3xl font-bold">{t.smeEnterprise.enterprise.title}</h3>
            <p className="text-lg leading-relaxed text-slate-400">{t.smeEnterprise.enterprise.desc}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
