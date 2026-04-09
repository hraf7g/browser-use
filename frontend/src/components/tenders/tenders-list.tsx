'use client';

import TendersListItem from './tenders-list-item';
import { useTranslation } from '@/context/language-context';

export interface UITenderItem {
  id: string;
  title: string;
  entity: string;
  source: string;
  reference: string;
  daysLeft: number;
  isNew: boolean;
  isMatched: boolean;
  matchedKeywords: string[];
}

export default function TendersList({
  items,
  loading,
  error,
}: {
  items: UITenderItem[];
  loading: boolean;
  error: string | null;
}) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="h-40 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
        {error}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center dark:border-slate-700 dark:bg-slate-900">
        <h3 className="text-lg font-bold text-slate-950 dark:text-white">{t.tenders.empty.title}</h3>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{t.tenders.empty.description}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((tender) => (
        <TendersListItem key={tender.id} tender={tender} />
      ))}
    </div>
  );
}
