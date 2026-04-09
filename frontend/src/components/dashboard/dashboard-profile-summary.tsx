'use client';

import { useTranslation } from '@/context/language-context';

const profilePoints = [
  'Construction',
  'Cybersecurity',
  'Facility Management',
] as const;

export default function DashboardProfileSummary() {
  const { t } = useTranslation();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-6">
        <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.hero.actions.profile}</h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Your current matching logic is prioritizing these sectors and signals.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {profilePoints.map((point) => (
          <span
            key={point}
            className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            {point}
          </span>
        ))}
      </div>
    </section>
  );
}
