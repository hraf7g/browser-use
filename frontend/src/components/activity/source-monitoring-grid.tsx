'use client';

import { useTranslation } from '@/context/language-context';
import type { ActivitySourceCard } from '@/lib/activity-api-adapter';
import SourceStatusCard from './source-status-card';
import { Globe } from 'lucide-react';

export default function SourceMonitoringGrid({
  sources,
  monitoringActive,
  onOpenSetup,
}: {
  sources: ActivitySourceCard[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t } = useTranslation();

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2 px-1">
        <Globe size={18} className="text-slate-400" />
        <h3 className="font-bold text-slate-900 dark:text-white">
          {t.activity.sourceMonitoring.title}
        </h3>
      </div>
      <div className="grid grid-cols-1 gap-4">
        {sources.map((source) => (
          <SourceStatusCard key={source.source_id} source={source} />
        ))}
        {sources.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-sm font-semibold text-slate-950 dark:text-white">
              {monitoringActive ? t.activity.sourceMonitoring.emptyActiveTitle : t.activity.sourceMonitoring.emptyInactiveTitle}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {monitoringActive ? t.activity.sourceMonitoring.emptyActiveDescription : t.activity.sourceMonitoring.emptyInactiveDescription}
            </p>
            {!monitoringActive ? (
              <button
                type="button"
                onClick={onOpenSetup}
                className="mt-4 inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
              >
                {t.activity.sourceMonitoring.setupAction}
              </button>
            ) : null}
          </div>
        )}
      </div>
    </section>
  );
}
