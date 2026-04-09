'use client';

import { useTranslation } from '@/context/language-context';

export default function TendersResultsToolbar({
  total,
  sort,
  onSortChange,
}: {
  total: number;
  sort: 'relevance' | 'newest' | 'closingSoon';
  onSortChange: (sort: 'relevance' | 'newest' | 'closingSoon') => void;
}) {
  const { t } = useTranslation();
  const options = [
    { id: 'relevance', label: t.tenders.sort.relevance },
    { id: 'newest', label: t.tenders.sort.newest },
    { id: 'closingSoon', label: t.tenders.sort.closingSoon },
  ] as const;

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
        {t.tenders.resultsCount.replace('{n}', total.toString())}
      </p>

      <div className="flex items-center gap-2">
        {options.map((option) => (
          <button
            key={option.id}
            onClick={() => onSortChange(option.id)}
            className={`rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${
              sort === option.id
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
                : 'bg-white text-slate-600 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
