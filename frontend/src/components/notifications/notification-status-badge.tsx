'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

export default function NotificationStatusBadge({
  status,
  reason,
}: {
  status: string;
  reason?: string;
}) {
  const { t } = useTranslation();

  const label =
    status === 'sent'
      ? t.notifications.history.sent
      : status === 'failed'
        ? t.notifications.history.failed
        : t.notifications.history.pending;

  return (
    <span
      title={reason}
      className={cn(
        'inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]',
        status === 'sent'
          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
          : status === 'failed'
            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
            : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
      )}
    >
      {label}
    </span>
  );
}
