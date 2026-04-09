'use client';

import { useTranslation } from '@/context/language-context';

const statValues = {
  newMatches: '12',
  closingSoon: '5',
  alertsSent: '28',
  sources: '54',
} as const;

export default function DashboardStatsRow() {
  const { t } = useTranslation();

  const stats = [
    { key: 'newMatches', label: t.dashboard.stats.newMatches, value: statValues.newMatches },
    { key: 'closingSoon', label: t.dashboard.stats.closingSoon, value: statValues.closingSoon },
    { key: 'alertsSent', label: t.dashboard.stats.alertsSent, value: statValues.alertsSent },
    { key: 'sources', label: t.dashboard.stats.sources, value: statValues.sources },
  ];

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.key}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
            {stat.label}
          </p>
          <p className="mt-4 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
            {stat.value}
          </p>
        </div>
      ))}
    </section>
  );
}
