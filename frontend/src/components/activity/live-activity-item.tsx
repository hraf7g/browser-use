'use client';

import { motion } from 'framer-motion';
import { ActivityEvent } from '@/lib/activity-api-adapter';
import {
  Search, CheckCircle2, Zap, Bell, FileText,
  Clock3, RefreshCcw, XCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslation } from '@/context/language-context';
import { compactBadgeClass } from '@/lib/locale-ui';
import { getMatchReasonBadges } from '@/lib/match-reason';

const iconMap = {
  check: { icon: Search, color: 'text-slate-400 bg-slate-50 dark:bg-slate-800' },
  detect: { icon: CheckCircle2, color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10' },
  match: { icon: Zap, color: 'text-amber-500 bg-amber-50 dark:bg-amber-500/10' },
  alert: { icon: Bell, color: 'text-blue-500 bg-blue-50 dark:bg-blue-500/10' },
  brief: { icon: FileText, color: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-500/10' },
  delay: { icon: Clock3, color: 'text-orange-500 bg-orange-50 dark:bg-orange-500/10' },
  retry: { icon: RefreshCcw, color: 'text-blue-400 bg-blue-50 dark:bg-blue-400/10' },
  failure: { icon: XCircle, color: 'text-red-500 bg-red-50 dark:bg-red-500/10' },
};

export default function LiveActivityItem({ event, isLast }: { event: ActivityEvent, isLast: boolean }) {
  const { t, lang } = useTranslation();
  const config = iconMap[event.type] || iconMap.check;
  const matchReasonBadges = getMatchReasonBadges(
    {
      keywords: event.matchedKeywords,
      countryCodes: event.matchedCountryCodes,
      industryCodes: event.matchedIndustryCodes,
    },
    lang
  );

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative flex gap-4"
    >
      <div className="flex flex-col items-center">
        <div className={cn('z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-transparent transition-colors dark:border-slate-800', config.color)}>
          <config.icon size={18} />
        </div>
        {!isLast && (
          <div className="my-2 w-[2px] grow rounded-full bg-slate-200 dark:bg-slate-800" />
        )}
      </div>

      <div className="flex-1 rounded-2xl border border-transparent pb-6 pt-1 transition-colors group-hover:border-slate-200 group-hover:bg-white/70 group-hover:px-4 group-hover:py-3 dark:group-hover:border-slate-800 dark:group-hover:bg-slate-900/70">
        <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <h4 className="font-bold tracking-tight text-slate-900 dark:text-slate-100">
              {event.title}
            </h4>
            {event.sourceName && (
              <div className="flex flex-wrap items-center gap-2">
                <span className={compactBadgeClass(lang, 'rounded-full bg-slate-100 px-2.5 py-1 text-slate-500 dark:bg-slate-800 dark:text-slate-300')}>
                  {t.details.labels.source}
                </span>
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                  {event.sourceName}
                </span>
              </div>
            )}
          </div>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-300">
            {event.timestamp}
          </span>
        </div>
        <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
          {event.description}
        </p>
        {matchReasonBadges.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {matchReasonBadges.map((badge) => (
              <span
                key={badge.key}
                className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-[11px] font-semibold text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300"
              >
                {badge.label}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}
