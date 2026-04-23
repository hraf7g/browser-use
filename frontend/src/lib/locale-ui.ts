import type { Language } from '@/lib/translations';
import { cn } from '@/lib/utils';

export function eyebrowClass(lang: Language, extra?: string) {
  return cn(
    'text-xs font-semibold text-slate-500 dark:text-slate-400',
    lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.22em]',
    extra
  );
}

export function compactBadgeClass(lang: Language, extra?: string) {
  return cn(
    'text-[11px] font-semibold',
    lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.18em]',
    extra
  );
}
