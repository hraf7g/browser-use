'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

export default function ActivityStatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const label =
    status === 'healthy'
      ? t.activity.monitoringStatus.healthy
      : status === 'delayed'
        ? t.activity.monitoringStatus.delayed
        : status === 'retrying'
          ? t.activity.monitoringStatus.checking
          : t.activity.monitoringStatus.failed;

  return (
    <span
      className={cn(
        'inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]',
        status === 'healthy'
          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
          : status === 'delayed'
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
            : status === 'retrying'
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      )}
    >
      {label}
    </span>
  );
}
