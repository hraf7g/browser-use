'use client';

import { useTranslation } from '@/context/language-context';
import type { ActivitySourceCard } from '@/lib/activity-api-adapter';
import SourceStatusCard from './source-status-card';
import { Globe } from 'lucide-react';

export default function SourceMonitoringGrid({
  sources,
}: {
  sources: ActivitySourceCard[];
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
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
            {t.activity.empty.subtitle}
          </div>
        )}
      </div>
    </section>
  );
}
