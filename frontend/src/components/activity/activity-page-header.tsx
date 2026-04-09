'use client';

import { useTranslation } from '@/context/language-context';

export default function ActivityPageHeader() {
  const { t } = useTranslation();

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white px-6 py-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:px-8">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
          Tender Watch
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.activity.pageTitle}
        </h1>
        <p className="text-base leading-7 text-slate-600 dark:text-slate-400">
          {t.activity.pageSubtitle}
        </p>
      </div>
    </section>
  );
}
