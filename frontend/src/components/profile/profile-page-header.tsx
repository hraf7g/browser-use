'use client';

import Link from 'next/link';
import { ArrowLeft, ArrowRight, Save } from 'lucide-react';
import { useTranslation } from '@/context/language-context';

export default function ProfilePageHeader({
  dirty,
  saving,
  monitoringActive,
  saveError,
  saveSuccess,
  onSave,
  onReset,
}: {
  dirty: boolean;
  saving: boolean;
  monitoringActive: boolean;
  saveError: string | null;
  saveSuccess: string | null;
  onSave: () => void;
  onReset: () => void;
}) {
  const { t, lang } = useTranslation();
  const BackIcon = lang === 'ar' ? ArrowRight : ArrowLeft;

  const statusLabel = saveError
    ? saveError
    : saveSuccess
      ? saveSuccess
      : monitoringActive
        ? t.profilePage.status.active
        : t.profilePage.status.inactive;

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white px-6 py-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:px-8">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
            Tender Watch
          </p>
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
              {t.profilePage.title}
            </h1>
            <p className="max-w-3xl text-base leading-7 text-slate-600 dark:text-slate-400">
              {t.profilePage.subtitle}
            </p>
            <p className="max-w-3xl text-sm font-medium text-slate-500 dark:text-slate-400">
              {t.profilePage.summary}
            </p>
          </div>
          <div className="inline-flex items-center rounded-full bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:bg-slate-950/60 dark:text-slate-300">
            {statusLabel}
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            <BackIcon size={16} />
            {t.profilePage.actions.back}
          </Link>
          <button
            type="button"
            onClick={onReset}
            disabled={!dirty || saving}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
          >
            {t.profilePage.actions.reset}
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={!dirty || saving}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Save size={16} />
            {saving ? t.profilePage.actions.saving : t.profilePage.actions.save}
          </button>
        </div>
      </div>
    </section>
  );
}
