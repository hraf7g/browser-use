'use client';

import { useTranslation } from '@/context/language-context';

const activeFilters = ['Matched only', 'Etimad', 'Closing soon'] as const;

export default function TendersActiveFilters() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-wrap items-center gap-2">
      {activeFilters.map((filter) => (
        <button
          key={filter}
          className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          {filter}
        </button>
      ))}
      <button className="text-sm font-semibold text-blue-600 hover:text-blue-700">
        {t.tenders.filters.reset}
      </button>
    </div>
  );
}
