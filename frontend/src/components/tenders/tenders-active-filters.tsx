'use client';

import { useTranslation } from '@/context/language-context';

export interface ActiveTenderFilter {
  id: string;
  label: string;
}

export default function TendersActiveFilters({
  filters,
  onRemove,
  onReset,
}: {
  filters: ActiveTenderFilter[];
  onRemove: (id: string) => void;
  onReset: () => void;
}) {
  const { t } = useTranslation();

  if (filters.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {filters.map((filter) => (
        <button
          key={filter.id}
          type="button"
          onClick={() => onRemove(filter.id)}
          className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          {filter.label}
        </button>
      ))}
      <button type="button" onClick={onReset} className="text-sm font-semibold text-blue-600 hover:text-blue-700">
        {t.tenders.filters.reset}
      </button>
    </div>
  );
}
