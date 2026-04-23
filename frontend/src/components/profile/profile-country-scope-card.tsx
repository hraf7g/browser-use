'use client';

import { useTranslation } from '@/context/language-context';
import { MONITORING_COUNTRY_OPTIONS } from '@/lib/monitoring-country-options';

export default function ProfileCountryScopeCard({
  countryCodes,
  onToggleCountry,
}: {
  countryCodes: string[];
  onToggleCountry: (countryCode: string) => void;
}) {
  const { t, lang } = useTranslation();
  const displayNames = new Intl.DisplayNames([lang], { type: 'region' });

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:p-8">
      <div className="space-y-3">
        <h2 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.profilePage.countries.title}
        </h2>
        <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400">
          {t.profilePage.countries.description}
        </p>
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        {MONITORING_COUNTRY_OPTIONS.map((country) => {
          const selected = countryCodes.includes(country.code);
          const label = displayNames.of(country.code) ?? country.code;

          return (
            <button
              key={country.code}
              type="button"
              onClick={() => onToggleCountry(country.code)}
              className={`rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                selected
                  ? 'border-blue-600 bg-blue-600 text-white'
                  : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-blue-300 hover:text-blue-600 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
        {t.profilePage.countries.helper}
      </p>
    </section>
  );
}
