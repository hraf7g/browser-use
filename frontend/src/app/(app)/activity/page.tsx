'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from '@/context/language-context';
import ActivityPageHeader from '@/components/activity/activity-page-header';
import SourceHealthSummary from '@/components/activity/source-health-summary';
import SourceMonitoringGrid from '@/components/activity/source-monitoring-grid';
import LiveActivityStream from '@/components/activity/live-activity-stream';
import RecentRunsPanel from '@/components/activity/recent-runs-panel';
import { activityApi } from '@/lib/activity-api-adapter';
import type { ActivityOverviewApiResponse } from '@/lib/activity-api-adapter';

export default function ActivityPage() {
  const { t } = useTranslation();
  const [overview, setOverview] = useState<ActivityOverviewApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    activityApi
      .getOverview()
      .then((response) => {
        if (!cancelled) {
          setOverview(response);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8 min-h-screen">
        <ActivityPageHeader />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-32 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
            />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-8 xl:grid-cols-12">
          <div className="h-[420px] rounded-2xl border border-slate-200 bg-white animate-pulse xl:col-span-8 dark:border-slate-800 dark:bg-slate-900" />
          <div className="space-y-8 xl:col-span-4">
            <div className="h-[320px] rounded-2xl border border-slate-200 bg-white animate-pulse dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-[220px] rounded-2xl border border-slate-200 bg-white animate-pulse dark:border-slate-800 dark:bg-slate-900" />
          </div>
        </div>
      </div>
    );
  }

  if (error || overview === null) {
    return (
      <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8 min-h-screen">
        <ActivityPageHeader />
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
          {error ?? t.activity.empty.subtitle}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8 min-h-screen">
      <ActivityPageHeader />
      
      {/* Top Section: Global Health Metrics */}
      <SourceHealthSummary summary={overview.summary} />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        {/* Main Column: Live Feed */}
        <div className="xl:col-span-8 space-y-8">
          <LiveActivityStream items={overview.activity_items} />
        </div>

        {/* Side Column: Source Cards & Runs */}
        <div className="xl:col-span-4 space-y-8">
          <SourceMonitoringGrid sources={overview.sources} />
          <RecentRunsPanel runs={overview.recent_runs} />
        </div>
      </div>
    </div>
  );
}
