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
import { Activity } from 'lucide-react';
import ActivityEmptyState from './activity-empty-state';

export default function LiveActivityStream({
  items,
}: {
  items: ActivityFeedItem[];
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

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex flex-col shadow-sm">
      <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-600 flex items-center justify-center">
            <Activity size={20} />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white">
              {t.activity.title}
            </h3>
            <p className="text-sm text-slate-500">
              {t.activity.pageSubtitle}
            </p>
          </div>
        </div>
        <LiveActivityFilters active={filter} onChange={setFilter} />
      </div>

      <div className="p-6 space-y-1">
        <AnimatePresence mode="popLayout">
          {filteredActivity.length === 0 ? (
            <ActivityEmptyState />
          ) : (
            filteredActivity.map((event, index) => (
              <LiveActivityItem
                key={event.id}
                event={event}
                isLast={index === filteredActivity.length - 1}
              />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
