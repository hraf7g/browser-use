'use client';

import { useMemo } from 'react';
import { useTranslation } from '@/context/language-context';
import { ActivitySquare, BellRing, Radar, SearchCheck } from 'lucide-react';
import { compactBadgeClass } from '@/lib/locale-ui';
import { cn } from '@/lib/utils';

export default function DashboardStatsRow({
  monitoredSources,
  healthySources,
  openTenders,
  recentDeliveries,
  monitoringActive,
}: {
  monitoredSources: number;
  healthySources: number;
  openTenders: number;
  recentDeliveries: number;
  monitoringActive: boolean;
}) {
  const { t, lang } = useTranslation();

  const stats = useMemo(() => [
    {
      key: 'monitoredSources',
      icon: Radar,
      label: t.dashboard.stats.monitoredSources,
      value: monitoredSources.toString(),
      caption: monitoringActive ? t.dashboard.stats.captions.monitoredSourcesActive : t.dashboard.stats.captions.monitoredSourcesInactive,
      tone: 'text-blue-600 bg-blue-50 dark:text-blue-300 dark:bg-blue-950/30',
    },
    {
      key: 'healthySources',
      icon: ActivitySquare,
      label: t.dashboard.stats.healthySources,
      value: healthySources.toString(),
      caption: monitoringActive ? t.dashboard.stats.captions.healthySourcesActive : t.dashboard.stats.captions.healthySourcesInactive,
      tone: 'text-emerald-600 bg-emerald-50 dark:text-emerald-300 dark:bg-emerald-950/30',
    },
    {
      key: 'openTenders',
      icon: SearchCheck,
      label: t.dashboard.stats.openTenders,
      value: openTenders.toString(),
      caption: monitoringActive ? t.dashboard.stats.captions.openTendersActive : t.dashboard.stats.captions.openTendersInactive,
      tone: 'text-amber-600 bg-amber-50 dark:text-amber-300 dark:bg-amber-950/30',
    },
    {
      key: 'recentDeliveries',
      icon: BellRing,
      label: t.dashboard.stats.recentDeliveries,
      value: recentDeliveries.toString(),
      caption: monitoringActive ? t.dashboard.stats.captions.recentDeliveriesActive : t.dashboard.stats.captions.recentDeliveriesInactive,
      tone: 'text-indigo-600 bg-indigo-50 dark:text-indigo-300 dark:bg-indigo-950/30',
    },
  ], [healthySources, monitoredSources, monitoringActive, openTenders, recentDeliveries, t]);

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.key}
          className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-3">
              <p className={compactBadgeClass(lang, 'text-slate-500 dark:text-slate-400')}>
                {stat.label}
              </p>
              <p className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
                {stat.value}
              </p>
            </div>
            <div className={cn('flex h-11 w-11 items-center justify-center rounded-2xl', stat.tone)}>
              <stat.icon size={20} />
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {stat.caption}
          </p>
        </div>
      ))}
    </section>
  );
}
