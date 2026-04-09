'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

const sources = [
  { id: '1', name: 'Etimad', status: 'active', time: '4m' },
  { id: '2', name: 'Dubai Government', status: 'active', time: '7m' },
  { id: '3', name: 'Qatar Tenders', status: 'delayed', time: '18m' },
] as const;

export default function DashboardSourceHealth() {
  const { t } = useTranslation();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.sourceHealth.title}</h3>
        <span className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
          3 / 3
        </span>
      </div>

      <div className="space-y-4">
        {sources.map((source) => (
          <div
            key={source.id}
            className="flex items-start justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50"
          >
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">{source.name}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t.dashboard.sourceHealth.lastCheck.replace('{time}', source.time)}
              </p>
            </div>
            <span
              className={cn(
                'inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em]',
                source.status === 'active'
                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                  : 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'
              )}
            >
              {source.status === 'active' ? t.dashboard.sourceHealth.active : t.dashboard.sourceHealth.delayed}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
