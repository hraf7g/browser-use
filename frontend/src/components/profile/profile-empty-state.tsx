'use client';

import Link from 'next/link';
import { ArrowRight, Plus } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import { eyebrowClass } from '@/lib/locale-ui';

export default function ProfileEmptyState({
  onPrimaryAction,
}: {
  onPrimaryAction: () => void;
}) {
  const { t, lang } = useTranslation();

  return (
    <section className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-100 bg-[linear-gradient(135deg,rgba(59,130,246,0.08),transparent_60%)] px-6 py-6 dark:border-slate-800 dark:bg-[linear-gradient(135deg,rgba(59,130,246,0.12),transparent_60%)] lg:px-8">
        <p className={eyebrowClass(lang, 'text-blue-600 dark:text-blue-400')}>
          {t.profilePage.empty.badge}
        </p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.profilePage.empty.title}
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-400">
          {t.profilePage.empty.description}
        </p>
      </div>

      <div className="grid gap-4 px-6 py-6 lg:grid-cols-3 lg:px-8">
        {[
          t.profilePage.empty.tips.services,
          t.profilePage.empty.tips.buyers,
          t.profilePage.empty.tips.focus,
        ].map((tip) => (
          <div
            key={tip}
            className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-sm leading-6 text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-400"
          >
            {tip}
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3 border-t border-slate-100 px-6 py-6 dark:border-slate-800 sm:flex-row lg:px-8">
        <button
          type="button"
          onClick={onPrimaryAction}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
        >
          <Plus size={16} />
          {t.profilePage.empty.primaryAction}
        </button>
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
        >
          {t.profilePage.empty.secondaryAction}
          <ArrowRight size={16} className={lang === 'ar' ? 'rotate-180' : ''} />
        </Link>
      </div>
    </section>
  );
}
