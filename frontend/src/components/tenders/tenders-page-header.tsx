'use client';

import { useTranslation } from '@/context/language-context';

export default function TendersPageHeader({
  total,
  newCount,
  closingSoonCount,
}: {
  total: number;
  newCount: number;
  closingSoonCount: number;
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
          {t.tenders.subtitle}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Relevant</p>
          <p className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">{total}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">New</p>
          <p className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">{newCount}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 dark:bg-slate-950/60">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Closing Soon</p>
          <p className="mt-2 text-2xl font-bold text-slate-950 dark:text-white">{closingSoonCount}</p>
        </div>
      </div>
    </section>
  );
}
