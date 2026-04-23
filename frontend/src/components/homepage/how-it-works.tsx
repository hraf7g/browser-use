'use client';

import { BellRing, Fingerprint, FileSearch, Globe2 } from 'lucide-react';

import { useTranslation } from '@/context/language-context';

const ICON_MAP: Record<string, React.ElementType> = {
  Globe2,
  FileSearch,
  Fingerprint,
  BellRing,
};

const ACCENT_CLASSES = [
  'bg-blue-600 shadow-blue-500/25',
  'bg-indigo-600 shadow-indigo-500/25',
  'bg-violet-600 shadow-violet-500/25',
  'bg-emerald-600 shadow-emerald-500/25',
] as const;

export default function HowItWorks() {
  const { t, lang } = useTranslation();
  const isArabic = lang === 'ar';

  return (
    <section id="how" className="bg-slate-50 py-24 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <p
            className={`mb-3 text-sm font-bold text-blue-600 dark:text-blue-400 ${
              isArabic ? 'tracking-normal' : 'uppercase tracking-[0.26em]'
            }`}
          >
            {t.howItWorks.eyebrow}
          </p>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white md:text-4xl">
            {t.howItWorks.title}
          </h2>
          <p
            className={`mt-4 text-lg text-slate-600 dark:text-slate-400 ${
              isArabic ? 'leading-9' : 'leading-8'
            }`}
          >
            {t.howItWorks.subtitle}
          </p>
        </div>

        {/* 4-card grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {(t.howItWorks.steps as Array<{ n: string; icon?: string; t: string; d: string }>).map(
            (step, i) => {
              const iconKey = step.icon ?? ['Globe2', 'FileSearch', 'Fingerprint', 'BellRing'][i];
              const Icon = ICON_MAP[iconKey] ?? Globe2;
              const accentClass = ACCENT_CLASSES[i % ACCENT_CLASSES.length];

              return (
                <div
                  key={step.t}
                  className="group relative flex flex-col rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md dark:border-slate-800 dark:bg-slate-950"
                >
                  {/* Step number */}
                  <span className="mb-5 text-[10px] font-bold uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">
                    {t.howItWorks.stepLabel} {step.n}
                  </span>

                  {/* Icon */}
                  <div
                    className={`mb-5 flex h-12 w-12 items-center justify-center rounded-2xl text-white shadow-lg ${accentClass}`}
                  >
                    <Icon size={22} />
                  </div>

                  {/* Text */}
                  <h3 className="text-lg font-bold tracking-tight text-slate-950 dark:text-white">
                    {step.t}
                  </h3>
                  <p
                    className={`mt-3 flex-1 text-sm text-slate-600 dark:text-slate-400 ${
                      isArabic ? 'leading-8' : 'leading-7'
                    }`}
                  >
                    {step.d}
                  </p>

                  {/* Subtle number watermark */}
                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute bottom-4 right-5 text-5xl font-black text-slate-100 transition-colors group-hover:text-slate-200 dark:text-slate-800 dark:group-hover:text-slate-700"
                  >
                    {step.n}
                  </span>
                </div>
              );
            }
          )}
        </div>
      </div>
    </section>
  );
}
