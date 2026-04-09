'use client';

import { useTranslation } from '@/context/language-context';
import { Globe, ExternalLink } from 'lucide-react';

export default function TenderDetailsSourceCard({
  source,
  sourceUrl,
}: {
  source: string | null | undefined;
  sourceUrl: string;
}) {
  const { t } = useTranslation();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          <Globe size={18} />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
            {t.details.labels.source}
          </p>
          <p className="mt-1 text-sm font-semibold text-slate-950 dark:text-white">
            {source ?? t.details.labels.notAvailable}
          </p>
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            <ExternalLink size={12} />
            {t.details.sourceLink}
          </a>
        </div>
      </div>
    </div>
  );
}
