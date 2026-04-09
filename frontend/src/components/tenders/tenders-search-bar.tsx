'use client';
import { useTranslation } from '@/context/language-context';
import { Search } from 'lucide-react';

export default function TendersSearchBar({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="relative group max-w-2xl">
      <div className="absolute inset-y-0 start-0 ps-4 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-600 transition-colors">
        <Search size={20} />
      </div>
      <input 
        type="text" 
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={t.tenders.searchPlaceholder}
        className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl ps-12 pe-4 py-4 text-sm md:text-base font-medium focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all shadow-sm"
      />
    </div>
  );
}
