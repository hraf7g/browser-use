'use client';

import { useTranslation } from '@/context/language-context';

export default function TenderDetailsMetaGrid({
  tender,
}: {
  tender: {
    source: string;
    closingDate: string;
    openingDate: string | null;
    publishedDate: string;
    reference: string;
    category: string;
    industries: string;
  };
}) {
  const { t } = useTranslation();

  const items = [
    { label: t.details.labels.source, value: tender.source },
    { label: t.details.labels.closingDate, value: tender.closingDate },
    { label: t.details.labels.openingDate, value: tender.openingDate ?? t.details.labels.notAvailable },
    { label: t.details.labels.publishedDate, value: tender.publishedDate },
    { label: t.details.labels.reference, value: tender.reference },
    { label: t.details.labels.category, value: tender.category },
    { label: t.details.labels.industries, value: tender.industries },
  ];

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
            {item.label}
          </p>
          <p className="mt-3 text-sm font-semibold text-slate-950 dark:text-white">{item.value}</p>
        </div>
      ))}
    </section>
  );
}
