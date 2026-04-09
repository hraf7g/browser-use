'use client';

import { useTranslation } from '@/context/language-context';

export default function TenderDetailsMainCard({
  tender,
}: {
  tender: {
    issuing_entity: string;
    ai_summary?: string | null;
  };
}) {
  const { t } = useTranslation();

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:p-8">
      <div className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
            {t.details.labels.entity}
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950 dark:text-white">{tender.issuing_entity}</p>
        </div>
        <p className="text-base leading-7 text-slate-600 dark:text-slate-400">
          {tender.ai_summary ?? t.details.summaryUnavailable}
        </p>
      </div>
    </section>
  );
}
