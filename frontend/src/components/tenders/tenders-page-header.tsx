'use client';

import { Radar } from 'lucide-react';
import { useTranslation } from '@/context/language-context';

export default function TendersPageHeader({
  total,
  newCount,
  closingSoonCount,
  monitoringActive,
  onOpenSetup,
}: {
  total: number;
  newCount: number;
  closingSoonCount: number;
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t } = useTranslation();

  return (
    <section className="flex flex-col gap-5 rounded-[28px] border border-slate-200 bg-white px-6 py-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:flex-row lg:items-end lg:justify-between lg:px-8">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
          Tender Watch
        </p>
        <h2 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.tenders.title}
        </h2>
        <p className="max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-400">
          {monitoringActive ? t.tenders.subtitle : t.tenders.subtitleInactive}
        </p>
        {!monitoringActive ? (
          <button
            type="button"
            onClick={onOpenSetup}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            <Radar size={16} />
            {t.tenders.primaryAction}
          </button>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{t.tenders.metrics.loaded}</p>
          <p className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">{total}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{t.tenders.metrics.captions.loaded}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{t.tenders.metrics.newInView}</p>
          <p className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">{newCount}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{t.tenders.metrics.captions.newInView}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{t.tenders.metrics.closingSoonInView}</p>
          <p className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">{closingSoonCount}</p>
          <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">{t.tenders.metrics.captions.closingSoonInView}</p>
        </div>
      </div>
    </section>
  );
}
