'use client';

import { useTranslation } from '@/context/language-context';
import { INDUSTRY_MAX_LENGTH } from '@/lib/profile-validation';

export default function ProfileIndustryCard({
  value,
  error,
  onChange,
}: {
  value: string;
  error: string | null;
  onChange: (nextValue: string) => void;
}) {
  const { t } = useTranslation();

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:p-8">
      <div className="space-y-3">
        <h2 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.profilePage.industry.title}
        </h2>
        <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400">
          {t.profilePage.industry.description}
        </p>
      </div>

      <div className="mt-5 space-y-3">
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          maxLength={INDUSTRY_MAX_LENGTH}
          className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition-colors focus:border-blue-500 dark:border-slate-700 dark:bg-slate-950/50 dark:text-white"
          placeholder={t.profilePage.industry.placeholder}
        />
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t.profilePage.industry.helper}
          </p>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
            {t.profilePage.industry.count
              .replace('{count}', value.trim().length.toString())
              .replace('{limit}', INDUSTRY_MAX_LENGTH.toString())}
          </p>
        </div>
        {error ? (
          <p className="text-sm font-medium text-red-600 dark:text-red-400">{error}</p>
        ) : null}
      </div>
    </section>
  );
}
