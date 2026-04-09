'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

export default function LiveActivityFilters({
  active,
  onChange,
}: {
  active: string;
  onChange: (value: string) => void;
}) {
  const { t } = useTranslation();
  const filters = [
    { id: 'all', label: t.activity.filters.all },
    { id: 'sources', label: t.activity.filters.sources },
    { id: 'matches', label: t.activity.filters.matches },
    { id: 'alerts', label: t.activity.filters.alerts },
    { id: 'failures', label: t.activity.filters.failures },
  ] as const;

  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((filter) => (
        <button
          key={filter.id}
          onClick={() => onChange(filter.id)}
          className={cn(
            'rounded-full px-3 py-1.5 text-sm font-semibold transition-colors',
            active === filter.id
              ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
          )}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}
