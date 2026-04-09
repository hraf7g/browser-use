'use client';

import { useTranslation } from '@/context/language-context';

export default function ActivityEmptyState() {
  const { t } = useTranslation();

  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-slate-700 dark:bg-slate-900">
      <h3 className="text-lg font-bold text-slate-950 dark:text-white">{t.activity.empty.title}</h3>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{t.activity.empty.subtitle}</p>
    </div>
  );
}
