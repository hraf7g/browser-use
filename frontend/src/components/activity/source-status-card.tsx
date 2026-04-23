'use client';

import { useTranslation } from '@/context/language-context';
import type { ActivitySourceCard } from '@/lib/activity-api-adapter';
import ActivityStatusBadge from './activity-status-badge';

export default function SourceStatusCard({ source }: { source: ActivitySourceCard }) {
  const { t, lang } = useTranslation();
  const lastSuccessfulCheck = source.last_successful_run_at ?? source.latest_run_started_at;
  const lastCheckLabel = lastSuccessfulCheck
    ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(
        new Date(lastSuccessfulCheck)
      )
    : t.activity.sourceMonitoring.noCheckYet;

  const latestResult =
    source.latest_run_status === 'success'
      ? t.activity.sourceMonitoring.success
      : source.latest_run_status === 'failed'
        ? t.activity.sourceMonitoring.failed
        : source.latest_run_status ?? t.activity.sourceMonitoring.unknown;

  const runMetrics = [
    {
      label: t.activity.sourceMonitoring.crawledRows,
      value: source.latest_run_crawled_row_count ?? 0,
    },
    {
      label: t.activity.sourceMonitoring.normalizedRows,
      value: source.latest_run_normalized_row_count ?? 0,
    },
    {
      label: t.activity.sourceMonitoring.acceptedRows,
      value: source.latest_run_accepted_row_count ?? 0,
    },
    {
      label: t.activity.sourceMonitoring.reviewRequiredRows,
      value: source.latest_run_review_required_row_count ?? 0,
    },
    {
      label: t.activity.sourceMonitoring.newTenders,
      value: source.latest_run_new_tenders_count ?? 0,
    },
    {
      label: t.activity.sourceMonitoring.updatedTenders,
      value: source.latest_run_updated_tender_count ?? 0,
    },
  ];

  const latestFailureDetail = [source.latest_run_failure_step, source.latest_run_failure_reason]
    .filter(Boolean)
    .join(': ');

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <h4 className="font-bold text-slate-950 dark:text-white">{source.source_name}</h4>
          <p className="text-sm text-slate-500 dark:text-slate-400">{latestResult}</p>
        </div>
        <ActivityStatusBadge status={source.source_status} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.activity.sourceMonitoring.lastCheck}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{lastCheckLabel}</p>
        </div>
        {runMetrics.map((metric) => (
          <div key={metric.label} className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{metric.label}</p>
            <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{metric.value}</p>
          </div>
        ))}
      </div>
      {latestFailureDetail ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
          <span className="font-semibold">{t.activity.sourceMonitoring.failureDetail}:</span>{' '}
          {latestFailureDetail}
        </div>
      ) : null}
    </div>
  );
}
