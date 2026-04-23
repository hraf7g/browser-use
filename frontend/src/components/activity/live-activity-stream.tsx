'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { mapActivityKindToType } from '@/lib/activity-api-adapter';
import type {
  ActivityFeedItem,
  ActivityEvent,
} from '@/lib/activity-api-adapter';
import LiveActivityItem from './live-activity-item';
import LiveActivityFilters from './live-activity-filters';
import { Activity, Radar } from 'lucide-react';
import ActivityEmptyState from './activity-empty-state';
import { eyebrowClass } from '@/lib/locale-ui';

export default function LiveActivityStream({
  items,
  monitoringActive,
  onOpenSetup,
  variant,
}: {
  items: ActivityFeedItem[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
  variant: 'dashboard' | 'activity';
}) {
  const { t, lang } = useTranslation();
  const [filter, setFilter] = useState('all');

  const events: ActivityEvent[] = items.map((item) => ({
    id: item.id,
    type: mapActivityKindToType(item.kind),
    title:
      item.kind === 'source_checked'
        ? t.activity.events.sourceChecked
        : item.kind === 'source_failed'
          ? t.activity.events.sourceFailed
          : item.kind === 'match_created'
            ? t.activity.events.matchCreated
            : item.kind === 'instant_alert_sent'
              ? t.activity.events.instantAlertSent
              : t.activity.events.dailyBriefSent,
    description: item.summary ?? '',
    timestamp: new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(item.timestamp)
    ),
    sourceName: item.source_name ?? undefined,
    matchedKeywords: item.matched_keywords ?? [],
    matchedCountryCodes: item.matched_country_codes ?? [],
    matchedIndustryCodes: item.matched_industry_codes ?? [],
    metadata: item.metadata,
  }));

  const filteredActivity = events.filter((event) => {
    if (filter === 'all') return true;
    if (filter === 'sources') return ['check', 'detect', 'delay', 'retry', 'failure'].includes(event.type);
    if (filter === 'matches') return event.type === 'match';
    if (filter === 'alerts') return ['alert', 'brief'].includes(event.type);
    if (filter === 'failures') return ['failure', 'delay', 'retry'].includes(event.type);
    return true;
  });

  const filterCounts = {
    all: events.length,
    sources: events.filter((event) => ['check', 'detect', 'delay', 'retry', 'failure'].includes(event.type)).length,
    matches: events.filter((event) => event.type === 'match').length,
    alerts: events.filter((event) => ['alert', 'brief'].includes(event.type)).length,
    failures: events.filter((event) => ['failure', 'delay', 'retry'].includes(event.type)).length,
  };

  const statusCopy = monitoringActive
    ? t.activity.pageSubtitle
    : t.activity.pageSubtitleInactive;

  return (
    <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-100 bg-[linear-gradient(135deg,rgba(59,130,246,0.07),transparent_62%)] p-6 dark:border-slate-800 dark:bg-[linear-gradient(135deg,rgba(59,130,246,0.12),transparent_62%)]">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0 space-y-3">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-300">
                <Activity size={20} />
              </div>
              <div className="space-y-1">
                <p className={eyebrowClass(lang)}>
                  Tender Watch
                </p>
                <h3 className="font-bold text-slate-950 dark:text-white">
                  {t.activity.title}
                </h3>
              </div>
            </div>
            <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400">
              {variant === 'activity' ? t.activity.pageSubtitle : t.dashboard.activity.subtitle}
            </p>
            <div className="flex flex-wrap gap-3 text-sm text-slate-500 dark:text-slate-400">
              <div className="inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-1.5 dark:bg-slate-950/60">
                <Radar size={14} className="text-blue-600 dark:text-blue-300" />
                <span>{statusCopy}</span>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-1.5 dark:bg-slate-950/60">
                <span className="font-semibold text-slate-900 dark:text-white">
                  {filteredActivity.length}
                </span>
                <span>{t.dashboard.activity.filterAll}</span>
              </div>
            </div>
          </div>
          <div className="xl:max-w-[22rem] xl:pt-1">
            <LiveActivityFilters active={filter} counts={filterCounts} onChange={setFilter} />
          </div>
        </div>
      </div>

      <div className="p-6">
        <AnimatePresence mode="popLayout">
          {filteredActivity.length === 0 ? (
            <ActivityEmptyState
              monitoringActive={monitoringActive}
              onOpenSetup={onOpenSetup}
              variant={variant}
            />
          ) : (
            <div className="rounded-[24px] border border-slate-100 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-950/40 sm:p-5">
              {filteredActivity.map((event, index) => (
                <LiveActivityItem
                  key={event.id}
                  event={event}
                  isLast={index === filteredActivity.length - 1}
                />
              ))}
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
