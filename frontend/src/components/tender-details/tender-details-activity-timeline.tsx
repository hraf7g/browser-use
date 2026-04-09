'use client';
import { useTranslation } from '@/context/language-context';
import { CheckCircle2, Search, Zap, Bell, FileClock } from 'lucide-react';

export default function TenderDetailsActivityTimeline({
  items,
}: {
  items: Array<{
    id: string;
    kind:
      | 'source_checked'
      | 'tender_detected'
      | 'match_created'
      | 'instant_alert_sent'
      | 'daily_brief_sent';
    status: string;
    timestamp: string;
    title: string;
    summary?: string | null;
  }>;
}) {
  const { t, lang } = useTranslation();

  const formatTime = (value: string) =>
    new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));

  const events = items.map((item) => {
    if (item.kind === 'instant_alert_sent') {
      return { ...item, icon: Bell, color: 'text-blue-500', label: t.details.timeline.alerted };
    }
    if (item.kind === 'daily_brief_sent') {
      return { ...item, icon: FileClock, color: 'text-indigo-500', label: t.details.timeline.briefed };
    }
    if (item.kind === 'match_created') {
      return { ...item, icon: Zap, color: 'text-amber-500', label: t.details.timeline.matched };
    }
    if (item.kind === 'tender_detected') {
      return { ...item, icon: CheckCircle2, color: 'text-emerald-500', label: t.details.timeline.detected };
    }
    return { ...item, icon: Search, color: 'text-slate-400', label: t.details.timeline.sourceChecked };
  });

  if (events.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
        <h3 className="font-bold text-slate-900 dark:text-white mb-2">{t.details.timeline.title}</h3>
        <p className="text-sm text-slate-500 dark:text-slate-400">{t.details.timeline.noEvents}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
      <h3 className="font-bold text-slate-900 dark:text-white mb-6">{t.details.timeline.title}</h3>
      <div className="space-y-6">
        {events.map((event, idx) => (
          <div key={event.id} className="flex gap-4 relative">
            {idx !== events.length - 1 && (
              <div className="absolute start-[11px] top-6 bottom-[-24px] w-px bg-slate-100 dark:bg-slate-800" />
            )}
            <div className={`w-6 h-6 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center shrink-0 z-10 ${event.color}`}>
              <event.icon size={12} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                {event.label}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{formatTime(event.timestamp)}</p>
              {event.summary && (
                <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                  {event.summary}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
