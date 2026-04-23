'use client';

import Link from 'next/link';
import { ArrowUpRight, TriangleAlert } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';
import type { ActivitySourceCard } from '@/lib/activity-api-adapter';

export default function DashboardSourceHealth({
  sources,
  monitoringActive,
  onOpenSetup,
}: {
  sources: ActivitySourceCard[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.sourceHealth.title}</h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {t.dashboard.sourceHealth.summary}
          </p>
        </div>
        <Link
          href="/activity"
          className="inline-flex items-center gap-2 text-sm font-bold text-blue-600 transition-colors hover:text-blue-700"
        >
          <span>{t.dashboard.sourceHealth.openActivity}</span>
          <ArrowUpRight size={15} className={lang === 'ar' ? 'rotate-[-90deg]' : ''} />
        </Link>
      </div>

      {sources.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 px-4 py-4 dark:border-slate-800 dark:bg-slate-950/50">
          <p className="text-sm font-semibold text-slate-900 dark:text-white">
            {monitoringActive ? t.dashboard.sourceHealth.emptyActiveTitle : t.dashboard.sourceHealth.emptyInactiveTitle}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {monitoringActive ? t.dashboard.sourceHealth.emptyActiveDescription : t.dashboard.sourceHealth.emptyInactiveDescription}
          </p>
          {!monitoringActive ? (
            <button
              type="button"
              onClick={onOpenSetup}
              className="mt-4 inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              {t.dashboard.sourceHealth.setupAction}
            </button>
          ) : null}
        </div>
      ) : (
        <div className="space-y-4">
          {sources.map((source) => {
            const lastKnownCheck = source.last_successful_run_at ?? source.latest_run_started_at;
            const lastCheckLabel = lastKnownCheck
              ? t.dashboard.sourceHealth.lastCheck.replace(
                  '{time}',
                  new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(lastKnownCheck))
                )
              : t.activity.sourceMonitoring.noCheckYet;
            const latestRunStatus =
              source.latest_run_status === 'success'
                ? t.activity.sourceMonitoring.success
                : source.latest_run_status === 'failed'
                  ? t.activity.sourceMonitoring.failed
                  : source.latest_run_status ?? t.activity.sourceMonitoring.unknown;

            const status =
              source.source_status === 'healthy'
                ? t.dashboard.sourceHealth.healthy
                : t.dashboard.sourceHealth.degraded;

            const acceptedCount = source.latest_run_accepted_row_count ?? 0;
            const reviewRequiredCount = source.latest_run_review_required_row_count ?? 0;

            return (
              <div
                key={source.source_id}
                className="rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">{source.source_name}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{lastCheckLabel}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{latestRunStatus}</p>
                  </div>
                  <span
                    className={cn(
                      'inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.16em]',
                      source.source_status === 'healthy'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                        : 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'
                    )}
                  >
                    {status}
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
                  <span className="rounded-full bg-white px-2.5 py-1 dark:bg-slate-900">
                    {t.activity.sourceMonitoring.acceptedRows}: {acceptedCount}
                  </span>
                  <span className="rounded-full bg-white px-2.5 py-1 dark:bg-slate-900">
                    {t.activity.sourceMonitoring.reviewRequiredRows}: {reviewRequiredCount}
                  </span>
                  <span className="rounded-full bg-white px-2.5 py-1 dark:bg-slate-900">
                    {t.dashboard.sourceHealth.failures.replace('{count}', String(source.failure_count))}
                  </span>
                </div>

                {source.latest_run_failure_reason ? (
                  <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50/80 px-3 py-2 text-sm text-amber-800 dark:border-amber-900/30 dark:bg-amber-950/20 dark:text-amber-200">
                    <p className="inline-flex items-center gap-2 font-semibold">
                      <TriangleAlert size={15} />
                      {t.dashboard.sourceHealth.failureReason}
                    </p>
                    <p className="mt-1 line-clamp-2">{source.latest_run_failure_reason}</p>
                  </div>
                ) : null}

                <div className="mt-3">
                  <Link
                    href="/activity"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 transition-colors hover:text-blue-600 dark:text-slate-200 dark:hover:text-blue-300"
                  >
                    <span>{t.dashboard.sourceHealth.inspectAction}</span>
                    <ArrowUpRight size={15} className={lang === 'ar' ? 'rotate-[-90deg]' : ''} />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
