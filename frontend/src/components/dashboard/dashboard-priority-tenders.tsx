'use client';

import Link from 'next/link';
import { useTranslation } from '@/context/language-context';
import { Calendar, Globe2, ArrowUpRight, Radar, SearchCheck, Sparkles } from 'lucide-react';
import type { TenderListApiItem } from '@/lib/tender-api-adapter';
import { getMatchReasonBadges } from '@/lib/match-reason';

function getSourceLabel(sourceUrl: string) {
  try {
    return new URL(sourceUrl).hostname.replace(/^www\./, '');
  } catch {
    return 'Official Source';
  }
}

export default function DashboardPriorityTenders({
  tenders,
  monitoringActive,
  onOpenSetup,
}: {
  tenders: TenderListApiItem[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.priority.title}</h3>
        <Link href="/tenders" className="text-sm font-bold text-blue-600 hover:text-blue-700 transition-colors">
          {t.dashboard.priority.viewAll}
        </Link>
      </div>

      {tenders.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-6 dark:border-slate-800 dark:bg-slate-950/30">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-2xl">
              <h4 className="text-lg font-semibold text-slate-950 dark:text-white">
                {monitoringActive ? t.dashboard.priority.emptyActiveTitle : t.dashboard.priority.emptyInactiveTitle}
              </h4>
              <p className="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-400">
                {monitoringActive ? t.dashboard.priority.emptyActiveDescription : t.dashboard.priority.emptyInactiveDescription}
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                    <Radar size={16} className="text-blue-600 dark:text-blue-400" />
                    <span>{t.dashboard.priority.preview.monitoringTitle}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                    {t.dashboard.priority.preview.monitoringDescription}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                    <SearchCheck size={16} className="text-blue-600 dark:text-blue-400" />
                    <span>{t.dashboard.priority.preview.matchingTitle}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                    {t.dashboard.priority.preview.matchingDescription}
                  </p>
                </div>
              </div>
            </div>

            {!monitoringActive ? (
              <button
                type="button"
                onClick={onOpenSetup}
                className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
              >
                {t.dashboard.priority.setupAction}
              </button>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {tenders.map((tender) => {
            const closingDate = tender.closing_date
              ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium' }).format(new Date(tender.closing_date))
              : 'Unknown';
            const matchReasonBadges = getMatchReasonBadges(
              {
                keywords: tender.matched_keywords,
                countryCodes: tender.matched_country_codes,
                industryCodes: tender.matched_industry_codes,
              },
              lang
            ).slice(0, 3);

            return (
              <article key={tender.id} className="group rounded-xl border border-slate-100 bg-slate-50/30 p-4 transition-all hover:border-blue-200 dark:border-slate-800 dark:bg-slate-950/30 dark:hover:border-blue-800">
                <div className="mb-2 flex justify-between items-start gap-4">
                  <div className="min-w-0">
                    <h4 className="font-bold text-slate-900 transition-colors group-hover:text-blue-600 line-clamp-1 dark:text-slate-100">
                      {tender.title}
                    </h4>
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 line-clamp-1">
                      {tender.issuing_entity}
                    </p>
                  </div>
                  <ArrowUpRight size={16} className={`shrink-0 text-slate-400 transition-transform group-hover:translate-x-0.5 ${lang === 'ar' ? 'rotate-[-90deg]' : ''}`} />
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Globe2 size={12} />
                    <span>{getSourceLabel(tender.source_url)}</span>
                  </div>
                  <div className="flex items-center gap-1.5 font-medium text-amber-600 dark:text-amber-500">
                    <Calendar size={12} />
                    <span>{t.dashboard.priority.closingOn.replace('{date}', closingDate)}</span>
                  </div>
                  {tender.category && (
                    <div className="rounded-full bg-white px-2 py-1 font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                      {tender.category}
                    </div>
                  )}
                </div>

                {tender.ai_summary ? (
                  <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {tender.ai_summary}
                  </p>
                ) : null}

                {tender.is_matched && matchReasonBadges.length > 0 ? (
                  <div className="mt-3">
                    <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-blue-700 dark:text-blue-300">
                      <Sparkles size={13} />
                      <span>{t.dashboard.priority.matchSignals}</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {matchReasonBadges.map((badge) => (
                        <span
                          key={badge.key}
                          className="rounded-full border border-blue-200 bg-white px-2.5 py-1 text-[11px] font-bold text-blue-700 dark:border-blue-900/40 dark:bg-slate-900 dark:text-blue-300"
                        >
                          {badge.label}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                  <Link
                    href={`/tenders/${tender.id}`}
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
                  >
                    <span>{t.dashboard.priority.reviewAction}</span>
                    <ArrowUpRight size={15} className={lang === 'ar' ? 'rotate-[-90deg]' : ''} />
                  </Link>
                  <Link
                    href={tender.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                  >
                    <span>{t.dashboard.priority.openSourceAction}</span>
                    <ArrowUpRight size={15} className={lang === 'ar' ? 'rotate-[-90deg]' : ''} />
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
