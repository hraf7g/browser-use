'use client';

import Link from 'next/link';
import { useTranslation } from '@/context/language-context';

export default function NotificationsPageHeader({
  monitoringActive,
  onOpenSetup,
}: {
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t } = useTranslation();

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white px-6 py-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:px-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
            Tender Watch
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
            {t.notifications.title}
          </h1>
          <p className="text-base leading-7 text-slate-600 dark:text-slate-400">
            {t.notifications.subtitle}
          </p>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            {monitoringActive ? t.notifications.summary : t.notifications.summaryInactive}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          {!monitoringActive ? (
            <button
              type="button"
              onClick={onOpenSetup}
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              {t.notifications.primaryAction}
            </button>
          ) : null}
          <Link
            href="/activity"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {t.notifications.secondaryAction}
          </Link>
        </div>
      </div>
    </section>
  );
}
