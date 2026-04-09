'use client';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

export default function TendersStatusBadge({ type }: { type: string }) {
  const { t } = useTranslation();

  if (!type) {
    return null;
  }

  const label = type === 'new' ? t.dashboard.priority.newLabel : 'Matched';

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em]',
        type === 'new'
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
      )}
    >
      {label}
    </span>
  );
}
