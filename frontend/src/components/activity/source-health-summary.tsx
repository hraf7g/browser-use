'use client';

import { useTranslation } from '@/context/language-context';
import type { ActivityOverviewSummary } from '@/lib/activity-api-adapter';

export default function SourceHealthSummary({
  summary,
  monitoringActive,
}: {
  summary: ActivityOverviewSummary;
  monitoringActive: boolean;
}) {
  const { t, lang } = useTranslation();

  const items = [
    {
      label: t.activity.summaryCards.totalSources,
      value: summary.total_sources.toString(),
      caption: monitoringActive ? t.activity.summaryCards.captions.totalSourcesActive : t.activity.summaryCards.captions.totalSourcesInactive,
    },
    {
      label: t.activity.summaryCards.healthySources,
      value: summary.healthy_sources.toString(),
      caption: monitoringActive ? t.activity.summaryCards.captions.healthySourcesActive : t.activity.summaryCards.captions.healthySourcesInactive,
    },
    {
      label: t.activity.summaryCards.degradedSources,
      value: summary.degraded_sources.toString(),
      caption: monitoringActive ? t.activity.summaryCards.captions.degradedSourcesActive : t.activity.summaryCards.captions.degradedSourcesInactive,
    },
  ];

  const latestSuccessfulCheck = summary.latest_successful_check_at
    ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(
        new Date(summary.latest_successful_check_at)
      )
    : t.activity.summaryCards.noCheckYet;

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              {item.label}
            </p>
            <p className="mt-4 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
              {item.value}
            </p>
            <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {item.caption}
            </p>
          </div>
        ))}
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-600 shadow-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
        <span className="font-semibold text-slate-900 dark:text-white">
          {t.activity.summaryCards.latestSuccessfulCheck}:
        </span>{' '}
        {latestSuccessfulCheck}
      </div>
    </section>
  );
}
