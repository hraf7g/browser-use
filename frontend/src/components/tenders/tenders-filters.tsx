'use client';
import { useTranslation } from '@/context/language-context';
import { Filter, X } from 'lucide-react';
import type { TenderSourceFilterOption } from '@/lib/tender-api-adapter';

type TenderFiltersState = {
  matchOnly: boolean;
  newOnly: boolean;
  closingSoon: boolean;
  sourceIds: string[];
};

export default function TendersFilters({
  filters,
  availableSources = [],
  onToggleMatchOnly,
  onToggleNewOnly,
  onToggleClosingSoon,
  onToggleSource,
  onReset,
}: {
  filters: TenderFiltersState;
  availableSources: TenderSourceFilterOption[];
  onToggleMatchOnly: () => void;
  onToggleNewOnly: () => void;
  onToggleClosingSoon: () => void;
  onToggleSource: (sourceId: string) => void;
  onReset: () => void;
}) {
  const { t } = useTranslation();

  const FilterGroup = ({ title, children }: { title: string, children: React.ReactNode }) => (
    <div className="space-y-3 pb-6 border-b border-slate-100 dark:border-slate-800 last:border-0 pt-6 first:pt-0">
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">{title}</h4>
      <div className="space-y-2">{children}</div>
    </div>
  );

  return (
    <aside className="w-full lg:w-64 shrink-0">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sticky top-24">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-blue-600" />
            <h3 className="font-bold">{t.tenders.filters.title}</h3>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 hover:text-blue-600"
          >
            <X size={12} />
            {t.tenders.filters.reset}
          </button>
        </div>

        <FilterGroup title={t.tenders.filters.status}>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input type="checkbox" checked={filters.newOnly} onChange={onToggleNewOnly} className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{t.tenders.filters.newOnly}</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input type="checkbox" checked={filters.matchOnly} onChange={onToggleMatchOnly} className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{t.tenders.filters.matchOnly}</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer group">
            <input type="checkbox" checked={filters.closingSoon} onChange={onToggleClosingSoon} className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
            <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{t.tenders.sort.closingSoon}</span>
          </label>
        </FilterGroup>

        <FilterGroup title={t.tenders.filters.source}>
          {availableSources.map((source) => (
            <label key={source.id} className="flex items-center gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={filters.sourceIds.includes(source.id)}
                onChange={() => onToggleSource(source.id)}
                className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{source.name}</span>
            </label>
          ))}
        </FilterGroup>
      </div>
    </aside>
  );
}
