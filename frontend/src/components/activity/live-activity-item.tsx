'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ActivityEvent } from '@/lib/activity-api-adapter';
import { 
  Search, CheckCircle2, Zap, Bell, FileText, 
  AlertCircle, RefreshCcw, XCircle 
} from 'lucide-react';
import { cn } from '@/lib/utils';

const iconMap = {
  check: { icon: Search, color: 'text-slate-400 bg-slate-50 dark:bg-slate-800' },
  detect: { icon: CheckCircle2, color: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10' },
  match: { icon: Zap, color: 'text-amber-500 bg-amber-50 dark:bg-amber-500/10' },
  alert: { icon: Bell, color: 'text-blue-500 bg-blue-50 dark:bg-blue-500/10' },
  brief: { icon: FileText, color: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-500/10' },
  delay: { icon: ClockIcon, color: 'text-orange-500 bg-orange-50 dark:bg-orange-500/10' },
  retry: { icon: RefreshCcw, color: 'text-blue-400 bg-blue-50 dark:bg-blue-400/10' },
  failure: { icon: XCircle, color: 'text-red-500 bg-red-50 dark:bg-red-500/10' },
};

function ClockIcon({ size, className }: { size: number, className?: string }) {
  return <AlertCircle size={size} className={className} />; // Placeholder
}

export default function LiveActivityItem({ event, isLast }: { event: ActivityEvent, isLast: boolean }) {
  const config = iconMap[event.type] || iconMap.check;

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-4 relative group"
    >
      <div className="flex flex-col items-center">
        <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0 z-10 transition-colors border border-transparent dark:border-slate-800", config.color)}>
          <config.icon size={18} />
        </div>
        {!isLast && (
          <div className="w-[2px] grow bg-slate-100 dark:bg-slate-800 my-1" />
        )}
      </div>

      <div className="pb-8 flex-1 pt-1">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
          <h4 className="font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            {event.title}
          </h4>
          <span className="text-xs font-medium text-slate-400 bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded-md">
            {event.timestamp}
          </span>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
          {event.description}
        </p>
        {event.sourceName && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Source:
            </span>
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
              {event.sourceName}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
