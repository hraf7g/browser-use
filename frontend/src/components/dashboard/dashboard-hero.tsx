'use client';

import Link from 'next/link';
import { ArrowRight, Radar } from 'lucide-react';
import { useTranslation } from '@/context/language-context';

export default function DashboardHero({
  monitoredSources,
  openTenders,
  monitoringActive,
  onOpenSetup,
}: {
  monitoredSources: number;
  openTenders: number;
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white px-6 py-7 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:px-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl space-y-3">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
            Tender Watch
          </p>
          <h2 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white lg:text-4xl">
            {t.dashboard.hero.greeting}
          </h2>
          <p className="text-base leading-7 text-slate-600 dark:text-slate-400">
            {monitoringActive
              ? t.dashboard.hero.summary
                  .replace('{sources}', monitoredSources.toString())
                  .replace('{tenders}', openTenders.toString())
              : t.dashboard.hero.inactiveSummary}
          </p>
          <div className="inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:bg-slate-950/50 dark:text-slate-300">
            <Radar size={14} className="text-blue-600 dark:text-blue-400" />
            <span>{monitoringActive ? t.dashboard.hero.activePill : t.dashboard.hero.inactivePill}</span>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          {monitoringActive ? (
            <Link
              href="/tenders"
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              {t.dashboard.hero.actions.browse}
            </Link>
          ) : (
            <button
              type="button"
              onClick={onOpenSetup}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              {t.dashboard.hero.actions.setup}
              <ArrowRight size={16} className={lang === 'ar' ? 'rotate-180' : ''} />
            </button>
          )}
          <Link
            href={monitoringActive ? '/profile' : '/activity'}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {monitoringActive ? t.dashboard.hero.actions.profile : t.dashboard.hero.actions.activity}
          </Link>
        </div>
      </div>
    </section>
  );
}
