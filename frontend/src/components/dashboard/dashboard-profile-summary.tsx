'use client';

import Link from 'next/link';
import { useTranslation } from '@/context/language-context';
import type { KeywordProfileApiResponse } from '@/lib/keyword-profile-api-adapter';
import type { NotificationPreferencesApiResponse } from '@/lib/notification-api-adapter';

export default function DashboardProfileSummary({
  profile,
  preferences,
  monitoringActive,
  onOpenSetup,
}: {
  profile: KeywordProfileApiResponse;
  preferences: NotificationPreferencesApiResponse;
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();
  const languageLabel =
    preferences.preferred_language === 'auto'
      ? t.notifications.preferences.langAuto
      : preferences.preferred_language === 'en'
        ? 'English'
        : 'Arabic';
  const countryDisplayNames = new Intl.DisplayNames(lang, { type: 'region' });
  const scopedCountries = profile.country_codes
    .map((code) => countryDisplayNames.of(code) ?? code)
    .slice(0, 2)
    .join(', ');
  const remainingCountryCount = Math.max(profile.country_codes.length - 2, 0);
  const countrySummary =
    profile.country_codes.length === 0
      ? t.dashboard.profile.allCountries
      : remainingCountryCount > 0
        ? t.dashboard.profile.countrySummaryMore
            .replace('{countries}', scopedCountries)
            .replace('{count}', String(remainingCountryCount))
        : scopedCountries;
  const scopeSummary = profile.industry_label?.trim() || t.dashboard.profile.scopeNotSet;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-6">
        <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.profile.title}</h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t.dashboard.profile.summary}
        </p>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.matching}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {profile.alert_enabled ? t.dashboard.profile.enabled : t.dashboard.profile.disabled}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.keywords}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {t.dashboard.profile.keywordCount.replace('{count}', String(profile.keywords.length))}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.countryScope}</span>
          <span className="text-right text-sm font-semibold text-slate-950 dark:text-white">
            {countrySummary}
          </span>
        </div>
        <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.businessScope}</span>
          <span className="text-right text-sm font-semibold text-slate-950 dark:text-white">
            {scopeSummary}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.industries}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {t.dashboard.profile.industryCount.replace('{count}', String(profile.industry_codes.length))}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.email}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {preferences.email_enabled ? t.dashboard.profile.enabled : t.dashboard.profile.disabled}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.whatsapp}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {preferences.whatsapp_enabled ? t.dashboard.profile.enabled : t.dashboard.profile.disabled}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.instant}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {preferences.instant_alert_enabled ? t.dashboard.profile.enabled : t.dashboard.profile.disabled}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t.dashboard.profile.daily}</span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {preferences.daily_brief_enabled ? t.dashboard.profile.enabled : t.dashboard.profile.disabled}
          </span>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {t.notifications.preferences.language}
          </span>
          <span className="text-sm font-semibold text-slate-950 dark:text-white">
            {languageLabel}
          </span>
        </div>
      </div>

      <div className="mt-5 flex flex-col gap-3">
        <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
          {monitoringActive ? t.dashboard.profile.activeNote : t.dashboard.profile.inactiveNote}
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          {!monitoringActive ? (
            <button
              type="button"
              onClick={onOpenSetup}
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              {t.dashboard.profile.setupAction}
            </button>
          ) : null}
          <Link
            href="/profile"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {t.dashboard.profile.manageProfileAction}
          </Link>
          <Link
            href="/notifications"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {t.dashboard.profile.manageAction}
          </Link>
        </div>
      </div>
    </section>
  );
}
