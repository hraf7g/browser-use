'use client';

import Link from 'next/link';
import TendersListItem from './tenders-list-item';
import { useTranslation } from '@/context/language-context';

export interface UITenderItem {
  id: string;
  title: string;
  entity: string;
  source: string;
  sourceName: string;
  reference: string;
  daysLeft: number | null;
  isNew: boolean;
  isMatched: boolean;
  matchedKeywords: string[];
  matchedCountryCodes: string[];
  matchedIndustryCodes: string[];
}

export default function TendersList({
  items,
  loading,
  error,
  monitoringActive,
  onOpenSetup,
  searchTerm,
}: {
  items: UITenderItem[];
  loading: boolean;
  error: string | null;
  monitoringActive: boolean;
  onOpenSetup: () => void;
  searchTerm: string;
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
    const searching = searchTerm.trim().length > 0;

    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 dark:border-slate-700 dark:bg-slate-900">
        <div className="mx-auto max-w-2xl text-center">
          <h3 className="text-lg font-bold text-slate-950 dark:text-white">
            {!monitoringActive && !searching ? t.tenders.empty.inactiveTitle : t.tenders.empty.title}
          </h3>
          <p className="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-400">
            {!monitoringActive && !searching
              ? t.tenders.empty.inactiveDescription
              : searching
                ? t.tenders.empty.description
                : t.tenders.empty.activeDescription}
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            {!monitoringActive && !searching ? (
              <button
                type="button"
                onClick={onOpenSetup}
                className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
              >
                {t.tenders.empty.primaryAction}
              </button>
            ) : null}
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
            >
              {t.tenders.empty.secondaryAction}
            </Link>
          </div>
        </div>
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
