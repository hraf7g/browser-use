'use client';

import { useTranslation } from '@/context/language-context';
import type { ActivityRecentRunItem } from '@/lib/activity-api-adapter';
import ActivityStatusBadge from './activity-status-badge';

export default function RecentRunsPanel({
  runs,
  monitoringActive,
  onOpenSetup,
}: {
  runs: ActivityRecentRunItem[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();

  const formatDateTime = (value: string) =>
    new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));

  const formatDuration = (startedAt: string, finishedAt: string | null) => {
    if (!finishedAt) {
      return t.activity.recentRuns.running;
    }

    const durationMs = new Date(finishedAt).getTime() - new Date(startedAt).getTime();
    if (durationMs <= 0) {
      return t.activity.recentRuns.running;
    }

    const seconds = Math.max(1, Math.round(durationMs / 1000));
    if (seconds < 60) {
      return `${seconds}s`;
    }

    const minutes = Math.round(seconds / 60);
    return `${minutes}m`;
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="font-bold text-slate-950 dark:text-white">{t.activity.recentRuns.title}</h3>
        <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{t.activity.recentRuns.latest}</span>
      </div>

      <div className="space-y-4">
        {runs.map((run) => (
          <div
            key={run.id}
            className="rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-950 dark:text-white">{run.source_name}</p>
              <ActivityStatusBadge status={run.status === 'success' ? 'healthy' : run.status} />
            </div>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span>{formatDateTime(run.started_at)}</span>
              <span>{formatDuration(run.started_at, run.finished_at)}</span>
              <span>
                {t.activity.recentRuns.newTenders}: {run.new_tenders_count ?? 0}
              </span>
            </div>
            {run.failure_reason && (
              <p className="mt-2 text-xs leading-relaxed text-red-600 dark:text-red-400">
                {run.failure_reason}
              </p>
            )}
          </div>
        ))}
        {runs.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/60 px-4 py-6 dark:border-slate-800 dark:bg-slate-950/50">
            <p className="text-sm font-semibold text-slate-950 dark:text-white">
              {monitoringActive ? t.activity.recentRuns.emptyActiveTitle : t.activity.recentRuns.emptyInactiveTitle}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {monitoringActive ? t.activity.recentRuns.emptyActiveDescription : t.activity.recentRuns.emptyInactiveDescription}
            </p>
            {!monitoringActive ? (
              <button
                type="button"
                onClick={onOpenSetup}
                className="mt-4 inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              >
                {t.activity.recentRuns.setupAction}
              </button>
            ) : null}
          </div>
        )}
      </div>
    </section>
  );
}
