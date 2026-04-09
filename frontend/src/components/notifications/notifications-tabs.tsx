'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

export default function NotificationsTabs({
  activeTab,
  onChange,
}: {
  activeTab: 'center' | 'preferences' | 'history';
  onChange: (tab: 'center' | 'preferences' | 'history') => void;
}) {
  const { t } = useTranslation();

  const tabs = [
    { id: 'center', label: t.notifications.tabs.center },
    { id: 'preferences', label: t.notifications.tabs.preferences },
    { id: 'history', label: t.notifications.tabs.history },
  ] as const;

  return (
    <div className="inline-flex flex-wrap gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            'rounded-xl px-4 py-2 text-sm font-semibold transition-colors',
            activeTab === tab.id
              ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
              : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
