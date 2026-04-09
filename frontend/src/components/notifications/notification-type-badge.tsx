'use client';

import { cn } from '@/lib/utils';
import { useTranslation } from '@/context/language-context';

export default function NotificationTypeBadge({ type }: { type: string }) {
  const { t, lang } = useTranslation();
  const normalized = type.toLowerCase().replace(/[_\s]/g, '');
  const label = normalized.includes('daily')
    ? (lang === 'ar' ? t.notifications.preferences.daily : 'Daily Brief')
    : (lang === 'ar' ? t.notifications.preferences.instant : 'Instant Alert');

  return (
    <span
      className={cn(
        'inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]',
        normalized.includes('daily')
          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
      )}
    >
      {label}
    </span>
  );
}
