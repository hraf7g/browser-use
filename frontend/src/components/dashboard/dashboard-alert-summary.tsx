'use client';

import { useTranslation } from '@/context/language-context';

const deliveryRows = [
  { label: 'Instant alerts', sent: 18, success: '98%' },
  { label: 'Daily briefs', sent: 10, success: '100%' },
] as const;

export default function DashboardAlertSummary() {
  const { t } = useTranslation();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.stats.alertsSent}</h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Operational delivery summary</p>
        </div>
        <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700 dark:bg-blue-950/40 dark:text-blue-300">
          28 total
        </span>
      </div>

      <div className="space-y-4">
        {deliveryRows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50"
          >
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">{row.label}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">{row.sent} sent today</p>
            </div>
            <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{row.success}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
