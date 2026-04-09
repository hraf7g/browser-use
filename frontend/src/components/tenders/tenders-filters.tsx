'use client';
import { useTranslation } from '@/context/language-context';
import { Filter, X } from 'lucide-react';

export default function TendersFilters() {
  const { t } = useTranslation();

  const FilterGroup = ({ title, children }: { title: string, children: React.ReactNode }) => (
    <div className="space-y-3 pb-6 border-b border-slate-100 dark:border-slate-800 last:border-0 pt-6 first:pt-0">
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">{title}</h4>
      <div className="space-y-2">{children}</div>
    </div>
  );

  return (
    <aside className="w-full lg:w-64 shrink-0 hidden lg:block">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 sticky top-24">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-blue-600" />
            <h3 className="font-bold">{t.tenders.filters.title}</h3>
          </div>
          <button className="text-xs font-bold text-blue-600 hover:underline">{t.tenders.filters.reset}</button>
        </div>

        <FilterGroup title={t.tenders.filters.status}>
          {['New only', 'Matched only', 'Closing soon'].map(opt => (
            <label key={opt} className="flex items-center gap-3 cursor-pointer group">
              <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{opt}</span>
            </label>
          ))}
        </FilterGroup>

        <FilterGroup title={t.tenders.filters.source}>
          {['Etimad', 'Dubai Govt', 'NEOM', 'Aramco'].map(opt => (
            <label key={opt} className="flex items-center gap-3 cursor-pointer group">
              <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{opt}</span>
            </label>
          ))}
        </FilterGroup>
      </div>
    </aside>
  );
}
