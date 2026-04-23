'use client';

import { BellRing, FileSearch, Radar } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import { eyebrowClass } from '@/lib/locale-ui';

export default function ActivityEmptyState({
  monitoringActive,
  onOpenSetup,
  variant,
}: {
  monitoringActive: boolean;
  onOpenSetup: () => void;
  variant: 'dashboard' | 'activity';
}) {
  const { t, lang } = useTranslation();
  const previews = [
    {
      icon: Radar,
      title: t.activity.empty.preview.sourceChecksTitle,
      description: t.activity.empty.preview.sourceChecksDescription,
    },
    {
      icon: FileSearch,
      title: t.activity.empty.preview.matchesTitle,
      description: t.activity.empty.preview.matchesDescription,
    },
    {
      icon: BellRing,
      title: t.activity.empty.preview.alertsTitle,
      description: t.activity.empty.preview.alertsDescription,
    },
  ];

  return (
    <div className="rounded-[24px] border border-dashed border-slate-300 bg-gradient-to-br from-slate-50 to-white p-6 dark:border-slate-700 dark:from-slate-950/60 dark:to-slate-900">
      <div className="max-w-3xl">
        <p className={eyebrowClass(lang, 'text-blue-600 dark:text-blue-400')}>
          Tender Watch
        </p>
        <h3 className="text-lg font-bold text-slate-950 dark:text-white">
          {monitoringActive ? t.activity.empty.activeTitle : t.activity.empty.inactiveTitle}
        </h3>
        <p className="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-400">
          {monitoringActive
            ? variant === 'activity'
              ? t.activity.empty.activeDescription
              : t.dashboard.activity.emptyDescription
            : variant === 'activity'
              ? t.activity.empty.inactiveDescription
              : t.dashboard.activity.emptyDescription}
        </p>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {previews.map((preview) => {
          const Icon = preview.icon;

          return (
            <div
              key={preview.title}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-950/30 dark:text-blue-300">
                <Icon size={18} />
              </div>
              <p className="mt-3 text-sm font-semibold text-slate-950 dark:text-white">
                {preview.title}
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                {preview.description}
              </p>
            </div>
          );
        })}
      </div>

      {!monitoringActive ? (
        <button
          type="button"
          onClick={onOpenSetup}
          className="mt-6 inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          {t.activity.empty.primaryAction}
        </button>
      ) : null}
    </div>
  );
}
