'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

export default function LiveActivityFilters({
  active,
  counts,
  onChange,
}: {
  active: string;
  counts: Record<string, number>;
  onChange: (value: string) => void;
}) {
  const { t, lang } = useTranslation();
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
            'inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm font-semibold transition-colors',
            active === filter.id
              ? 'border-slate-900 bg-slate-900 text-white shadow-sm dark:border-white dark:bg-white dark:text-slate-900'
              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:bg-slate-800'
          )}
        >
          <span>{filter.label}</span>
          <span
            className={cn(
              'rounded-full px-2 py-0.5 text-[11px] font-semibold',
              active === filter.id
                ? 'bg-white/15 text-white dark:bg-slate-900/20 dark:text-slate-900'
                : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
              lang === 'ar' ? 'tracking-normal' : 'tracking-[0.08em]'
            )}
          >
            {counts[filter.id] ?? 0}
          </span>
        </button>
      ))}
    </div>
  );
}
