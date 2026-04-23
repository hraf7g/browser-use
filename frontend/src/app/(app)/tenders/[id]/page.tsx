'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import TenderDetailsHeader from '@/components/tender-details/tender-details-header';
import TenderDetailsMainCard from '@/components/tender-details/tender-details-main-card';
import TenderDetailsMetaGrid from '@/components/tender-details/tender-details-meta-grid';
import TenderDetailsMatchReason from '@/components/tender-details/tender-details-match-reason';
import TenderDetailsNotificationState from '@/components/tender-details/tender-details-notification-state';
import TenderDetailsActivityTimeline from '@/components/tender-details/tender-details-activity-timeline';
import TenderDetailsSourceCard from '@/components/tender-details/tender-details-source-card';
import { useTranslation } from '@/context/language-context';
import { tenderDetailsApi } from '@/lib/tender-details-api-adapter';
import type { TenderDetailsApiResponse } from '@/lib/tender-details-api-adapter';
import { getIndustryLabel } from '@/lib/match-reason';

export default function TenderDetailsPage() {
  const { t, lang } = useTranslation();
  const params = useParams<{ id: string }>();
  const tenderId = Array.isArray(params.id) ? params.id[0] : params.id;
  const missingTenderId = !tenderId;
  const [tender, setTender] = useState<TenderDetailsApiResponse | null>(null);
  const [loading, setLoading] = useState(!missingTenderId);
  const [error, setError] = useState<string | null>(null);
  const isStaleTender = tender !== null && tender.id !== tenderId;

  useEffect(() => {
    if (missingTenderId) {
      return;
    }

    let cancelled = false;

    tenderDetailsApi
      .get(tenderId)
      .then((response) => {
        if (!cancelled) {
          setError(null);
          setTender(response);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
          setTender(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [missingTenderId, tenderId]);

  if (missingTenderId) {
    return (
      <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-8">
        <div className="rounded-[28px] border border-red-200 bg-red-50 p-6 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
          Tender id is missing from the URL.
        </div>
      </div>
    );
  }

  if (loading || isStaleTender) {
    return (
      <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-8">
        <div className="h-40 animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-8">
            <div className="h-64 animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-56 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
          </div>
          <aside className="lg:col-span-4 space-y-8">
            <div className="h-40 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-72 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
            <div className="h-32 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
          </aside>
        </div>
      </div>
    );
  }

  if (error || tender === null) {
    return (
      <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-8">
        <div className="rounded-[28px] border border-red-200 bg-red-50 p-6 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
          {error ?? t.details.timeline.noEvents}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-8">
      <TenderDetailsHeader title={tender.title} officialUrl={tender.source_url} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Main Content: Left Column */}
        <div className="lg:col-span-8 space-y-8">
          <TenderDetailsMainCard tender={tender} />
          <TenderDetailsMetaGrid
            tender={{
              source: tender.source_name ?? tender.source_url,
              closingDate: tender.closing_date
                ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(
                    new Date(tender.closing_date)
                  )
                : t.details.labels.notAvailable,
              openingDate: tender.opening_date
                ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(
                    new Date(tender.opening_date)
                  )
                : null,
              publishedDate: tender.published_at
                ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(
                    new Date(tender.published_at)
                  )
                : t.details.labels.notAvailable,
              reference: tender.tender_ref ?? t.details.labels.notAvailable,
              category: tender.category ?? t.details.labels.notAvailable,
              industries:
                tender.industry_codes.length > 0
                  ? tender.industry_codes.map((industryCode) => getIndustryLabel(industryCode)).join(', ')
                  : t.details.labels.notAvailable,
            }}
          />
          <TenderDetailsMatchReason
            keywords={tender.matched_keywords}
            countryCodes={tender.matched_country_codes}
            industryCodes={tender.matched_industry_codes}
          />
        </div>

        {/* Sidebar: Right Column */}
        <aside className="lg:col-span-4 space-y-8">
          <TenderDetailsNotificationState notificationState={tender.notification_state} />
          <TenderDetailsActivityTimeline items={tender.activity_timeline} />
          <TenderDetailsSourceCard source={tender.source_name} sourceUrl={tender.source_url} />
        </aside>
      </div>
    </div>
  );
}
