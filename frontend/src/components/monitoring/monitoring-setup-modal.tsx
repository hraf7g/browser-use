'use client';

import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Bell, CheckCircle2, Globe, Sparkles, X } from 'lucide-react';
import { INDUSTRY_OPTIONS } from '@/lib/industry-options';
import { useTranslation } from '@/context/language-context';
import { MONITORING_COUNTRY_OPTIONS } from '@/lib/monitoring-country-options';
import { keywordProfileApi, type KeywordProfileApiResponse } from '@/lib/keyword-profile-api-adapter';
import {
  notificationBackendApi,
  type NotificationPreferencesApiResponse,
} from '@/lib/notification-api-adapter';

const KEYWORD_LIMIT = 50;
const PHONE_PATTERN = /^\+[1-9]\d{7,14}$/;

function normalizeKeywords(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function SetupSwitch({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (nextChecked: boolean) => void;
}) {
  return (
    <label
      className={`relative inline-flex h-6 w-12 cursor-pointer items-center rounded-full transition-colors duration-200 ${
        checked ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'
      }`}
    >
      <input
        checked={checked}
        className="sr-only"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
      <motion.span
        animate={{ x: checked ? 24 : 0 }}
        className="absolute left-1 top-1 h-4 w-4 rounded-full bg-white shadow-sm"
      />
    </label>
  );
}

export default function MonitoringSetupModal({
  open,
  onClose,
  profile,
  preferences,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  profile: KeywordProfileApiResponse | null;
  preferences: NotificationPreferencesApiResponse | null;
  onSaved: (
    nextProfile: KeywordProfileApiResponse,
    nextPreferences: NotificationPreferencesApiResponse
  ) => void;
}) {
  const router = useRouter();
  const { t, lang } = useTranslation();
  const [step, setStep] = useState(0);
  const [keywordInput, setKeywordInput] = useState('');
  const [industryLabel, setIndustryLabel] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [countryCodes, setCountryCodes] = useState<string[]>([]);
  const [industryCodes, setIndustryCodes] = useState<string[]>([]);
  const [instantAlerts, setInstantAlerts] = useState(false);
  const [dailyBriefs, setDailyBriefs] = useState(true);
  const [preferredLanguage, setPreferredLanguage] = useState<'auto' | 'en' | 'ar'>('auto');
  const [whatsappEnabled, setWhatsappEnabled] = useState(false);
  const [whatsappPhone, setWhatsappPhone] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const stepTitles = [
    t.monitoringSetup.steps.interests,
    t.monitoringSetup.steps.alerts,
    t.monitoringSetup.steps.sources,
    t.monitoringSetup.steps.next,
  ];

  const languageOptions = useMemo(
    () => [
      { id: 'auto', label: t.notifications.preferences.langAuto },
      { id: 'en', label: lang === 'ar' ? 'الإنجليزية' : 'English' },
      { id: 'ar', label: lang === 'ar' ? 'العربية' : 'Arabic' },
    ] as const,
    [lang, t]
  );
  const countryDisplayNames = useMemo(
    () => new Intl.DisplayNames([lang], { type: 'region' }),
    [lang]
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    setStep(0);
    setKeywordInput('');
    setIndustryLabel(profile?.industry_label ?? '');
    setKeywords(profile?.keywords ?? []);
    setCountryCodes(profile?.country_codes ?? []);
    setIndustryCodes(profile?.industry_codes ?? []);
    setInstantAlerts(preferences?.instant_alert_enabled ?? false);
    setDailyBriefs(preferences?.daily_brief_enabled ?? true);
    setPreferredLanguage(preferences?.preferred_language ?? 'auto');
    setWhatsappEnabled(preferences?.whatsapp_enabled ?? false);
    setWhatsappPhone(preferences?.whatsapp_phone_e164 ?? '');
    setSaving(false);
    setError(null);
    setCompleted(false);
  }, [open, preferences, profile]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !saving) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose, open, saving]);

  function addKeyword(rawValue: string) {
    const nextItems = normalizeKeywords(rawValue);
    if (nextItems.length === 0) {
      return;
    }

    setKeywords((current) => {
      const next = [...current];
      for (const item of nextItems) {
        if (next.length >= KEYWORD_LIMIT) {
          break;
        }

        if (!next.some((existing) => existing.localeCompare(item, undefined, { sensitivity: 'accent' }) === 0)) {
          next.push(item);
        }
      }
      return next;
    });
    setKeywordInput('');
    setError(null);
  }

  function removeKeyword(keyword: string) {
    setKeywords((current) => current.filter((item) => item !== keyword));
  }

  function toggleCountry(countryCode: string) {
    setCountryCodes((current) =>
      current.includes(countryCode)
        ? current.filter((item) => item !== countryCode)
        : [...current, countryCode]
    );
  }

  function toggleIndustry(industryCode: string) {
    setIndustryCodes((current) =>
      current.includes(industryCode)
        ? current.filter((item) => item !== industryCode)
        : [...current, industryCode]
    );
  }

  function handleKeywordKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      addKeyword(keywordInput);
    }
  }

  function validateStep() {
    if (step === 0 && keywords.length === 0) {
      setError(t.monitoringSetup.validation.keywords);
      return false;
    }

    if (step === 1) {
      if (!instantAlerts && !dailyBriefs) {
        setError(t.monitoringSetup.validation.alerts);
        return false;
      }

      if (whatsappEnabled && whatsappPhone && !PHONE_PATTERN.test(whatsappPhone)) {
        setError(t.monitoringSetup.validation.phone);
        return false;
      }
    }

    setError(null);
    return true;
  }

  function handleNext() {
    if (!validateStep()) {
      return;
    }

    setStep((current) => Math.min(current + 1, stepTitles.length - 1));
  }

  function handleBack() {
    setError(null);
    setStep((current) => Math.max(current - 1, 0));
  }

  async function handleActivate() {
    if (!validateStep()) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const [nextProfile, nextPreferences] = await Promise.all([
        keywordProfileApi.updateProfile({
          keywords,
          alert_enabled: instantAlerts || dailyBriefs,
          country_codes: countryCodes,
          industry_codes: industryCodes,
          industry_label: industryLabel.trim() || null,
        }),
        notificationBackendApi.updatePreferences({
          email_enabled: true,
          whatsapp_enabled: whatsappEnabled,
          whatsapp_phone_e164: whatsappPhone.trim() || null,
          instant_alert_enabled: instantAlerts,
          daily_brief_enabled: dailyBriefs,
          preferred_language: preferredLanguage,
        }),
      ]);

      onSaved(nextProfile, nextPreferences);
      setCompleted(true);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t.monitoringSetup.validation.save);
    } finally {
      setSaving(false);
    }
  }

  function renderStepContent() {
    if (completed) {
      return (
        <div className="space-y-6">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-300">
            <CheckCircle2 size={28} />
          </div>
          <div className="space-y-2">
            <h3 className="text-2xl font-bold text-slate-950 dark:text-white">
              {t.monitoringSetup.success.title}
            </h3>
            <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
              {t.monitoringSetup.success.description}
            </p>
          </div>
          <div className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-5 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-300">
            <p>{t.monitoringSetup.success.savedKeywords.replace('{count}', keywords.length.toString())}</p>
            <p>{t.monitoringSetup.success.savedAlerts.replace('{alerts}', [
              instantAlerts ? t.notifications.preferences.instant : null,
              dailyBriefs ? t.notifications.preferences.daily : null,
            ].filter(Boolean).join(' + '))}</p>
            <p>{t.monitoringSetup.success.next}</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => {
                onClose();
                router.push('/activity');
              }}
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              {t.monitoringSetup.success.primary}
            </button>
            <button
              type="button"
              onClick={() => {
                onClose();
                router.push('/notifications');
              }}
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
            >
              {t.monitoringSetup.success.secondary}
            </button>
          </div>
        </div>
      );
    }

    if (step === 0) {
      return (
        <div className="space-y-5">
          <div>
            <label className="text-sm font-semibold text-slate-900 dark:text-white">
              {t.monitoringSetup.form.countries}
            </label>
            <div className="mt-3 flex flex-wrap gap-3">
              {MONITORING_COUNTRY_OPTIONS.map((country) => {
                const selected = countryCodes.includes(country.code);
                const label = countryDisplayNames.of(country.code) ?? country.code;

                return (
                  <button
                    key={country.code}
                    type="button"
                    onClick={() => toggleCountry(country.code)}
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
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {t.monitoringSetup.form.countriesHint}
            </p>
          </div>

          <div>
            <label className="text-sm font-semibold text-slate-900 dark:text-white">
              {t.monitoringSetup.form.industryLabel}
            </label>
            <input
              value={industryLabel}
              onChange={(event) => setIndustryLabel(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition-colors focus:border-blue-500 dark:border-slate-700 dark:bg-slate-950/50"
              placeholder={t.monitoringSetup.form.industryPlaceholder}
            />
          </div>

          <div>
            <label className="text-sm font-semibold text-slate-900 dark:text-white">
              {t.monitoringSetup.form.industryCodes}
            </label>
            <div className="mt-3 flex flex-wrap gap-3">
              {INDUSTRY_OPTIONS.map((industry) => {
                const selected = industryCodes.includes(industry.code);

                return (
                  <button
                    key={industry.code}
                    type="button"
                    onClick={() => toggleIndustry(industry.code)}
                    className={`rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                      selected
                        ? 'border-blue-600 bg-blue-600 text-white'
                        : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-blue-300 hover:text-blue-600 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200'
                    }`}
                  >
                    {industry.label}
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {t.monitoringSetup.form.industryCodesHint}
            </p>
          </div>

          <div>
            <label className="text-sm font-semibold text-slate-900 dark:text-white">
              {t.monitoringSetup.form.keywords}
            </label>
            <div className="mt-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/50">
              <div className="flex flex-wrap gap-2">
                {keywords.map((keyword) => (
                  <button
                    key={keyword}
                    type="button"
                    onClick={() => removeKeyword(keyword)}
                    className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    <span>{keyword}</span>
                    <X size={14} />
                  </button>
                ))}
                <input
                  value={keywordInput}
                  onChange={(event) => setKeywordInput(event.target.value)}
                  onKeyDown={handleKeywordKeyDown}
                  onBlur={() => addKeyword(keywordInput)}
                  className="min-w-[220px] flex-1 bg-transparent px-2 py-1 text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-200"
                  placeholder={t.monitoringSetup.form.keywordPlaceholder}
                />
              </div>
            </div>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              {t.monitoringSetup.form.keywordHint}
            </p>
          </div>
        </div>
      );
    }

    if (step === 1) {
      return (
        <div className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-950 dark:text-white">
                  {t.notifications.preferences.instant}
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {t.monitoringSetup.form.instantHint}
                </p>
              </div>
              <SetupSwitch checked={instantAlerts} onChange={setInstantAlerts} />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-950 dark:text-white">
                  {t.notifications.preferences.daily}
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {t.monitoringSetup.form.dailyHint}
                </p>
              </div>
              <SetupSwitch checked={dailyBriefs} onChange={setDailyBriefs} />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-950 dark:text-white">
                  {t.notifications.preferences.whatsapp}
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {t.monitoringSetup.form.whatsappHint}
                </p>
              </div>
              <SetupSwitch checked={whatsappEnabled} onChange={setWhatsappEnabled} />
            </div>

            {whatsappEnabled ? (
              <input
                value={whatsappPhone}
                onChange={(event) => setWhatsappPhone(event.target.value)}
                className="mt-4 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition-colors focus:border-blue-500 dark:border-slate-700 dark:bg-slate-900"
                placeholder="+971501234567"
              />
            ) : null}
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
            <p className="text-sm font-semibold text-slate-950 dark:text-white">
              {t.notifications.preferences.language}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              {languageOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => setPreferredLanguage(option.id)}
                  className={`rounded-full border px-4 py-2 text-sm font-semibold transition-colors ${
                    preferredLanguage === option.id
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:text-blue-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {t.monitoringSetup.form.emailDeliveryNote}
            </p>
          </div>
        </div>
      );
    }

    if (step === 2) {
      return (
        <div className="grid gap-4 md:grid-cols-3">
          {[
            {
              icon: Globe,
              title: t.monitoringSetup.sources.cards.sources.title,
              description: t.monitoringSetup.sources.cards.sources.description,
            },
            {
              icon: Sparkles,
              title: t.monitoringSetup.sources.cards.matching.title,
              description: t.monitoringSetup.sources.cards.matching.description,
            },
            {
              icon: Bell,
              title: t.monitoringSetup.sources.cards.alerts.title,
              description: t.monitoringSetup.sources.cards.alerts.description,
            },
          ].map((card) => {
            const Icon = card.icon;

            return (
              <div
                key={card.title}
                className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-blue-600 shadow-sm dark:bg-slate-900">
                  <Icon size={20} />
                </div>
                <h3 className="mt-4 text-sm font-semibold text-slate-950 dark:text-white">
                  {card.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                  {card.description}
                </p>
              </div>
            );
          })}
        </div>
      );
    }

    return (
      <div className="space-y-5">
        <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-800 dark:bg-slate-950/50">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
            {t.monitoringSetup.next.summaryLabel}
          </p>
          <div className="mt-4 grid gap-3 text-sm text-slate-600 dark:text-slate-300">
            <p>
              {t.monitoringSetup.next.countries.replace(
                '{value}',
                countryCodes.length === 0
                  ? t.monitoringSetup.next.allCountries
                  : countryCodes
                      .map((countryCode) => countryDisplayNames.of(countryCode) ?? countryCode)
                      .join(', ')
              )}
            </p>
            <p>
              {t.monitoringSetup.next.industries.replace(
                '{value}',
                industryCodes.length === 0
                  ? t.monitoringSetup.next.allIndustries
                  : INDUSTRY_OPTIONS.filter((industry) => industryCodes.includes(industry.code))
                      .map((industry) => industry.label)
                      .join(', ')
              )}
            </p>
            <p>{t.monitoringSetup.next.industry.replace('{value}', industryLabel.trim() || t.monitoringSetup.next.notProvided)}</p>
            <p>{t.monitoringSetup.next.keywords.replace('{count}', keywords.length.toString())}</p>
            <p>{t.monitoringSetup.next.alerts.replace('{value}', [
              instantAlerts ? t.notifications.preferences.instant : null,
              dailyBriefs ? t.notifications.preferences.daily : null,
            ].filter(Boolean).join(' + '))}</p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950/30">
            <h3 className="text-sm font-semibold text-slate-950 dark:text-white">
              {t.monitoringSetup.next.cards.watchers.title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {t.monitoringSetup.next.cards.watchers.description}
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950/30">
            <h3 className="text-sm font-semibold text-slate-950 dark:text-white">
              {t.monitoringSetup.next.cards.outputs.title}
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
              {t.monitoringSetup.next.cards.outputs.description}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-6 py-6 dark:border-slate-800 lg:px-8">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
                  {t.monitoringSetup.badge}
                </p>
                <h2 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
                  {t.monitoringSetup.title}
                </h2>
                <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400">
                  {t.monitoringSetup.subtitle}
                </p>
              </div>

              <button
                type="button"
                onClick={onClose}
                disabled={saving}
                className="rounded-full border border-slate-200 p-2 text-slate-500 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                aria-label={t.monitoringSetup.close}
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-6 lg:px-8">
              <div className="mb-8 grid gap-3 md:grid-cols-4">
                {stepTitles.map((title, index) => (
                  <div
                    key={title}
                    className={`rounded-2xl border px-4 py-3 ${
                      completed || index <= step
                        ? 'border-blue-200 bg-blue-50/80 dark:border-blue-900/40 dark:bg-blue-950/20'
                        : 'border-slate-200 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-950/30'
                    }`}
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">
                      {t.monitoringSetup.stepLabel.replace('{n}', String(index + 1))}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-slate-950 dark:text-white">
                      {title}
                    </p>
                  </div>
                ))}
              </div>

              {renderStepContent()}

              {error ? (
                <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
                  {error}
                </div>
              ) : null}
            </div>

            {!completed ? (
              <div className="flex flex-col-reverse gap-3 border-t border-slate-100 px-6 py-5 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between lg:px-8">
                <div className="text-sm text-slate-500 dark:text-slate-400">
                  {t.monitoringSetup.stepCounter
                    .replace('{current}', String(step + 1))
                    .replace('{total}', String(stepTitles.length))}
                </div>
                <div className="flex flex-col gap-3 sm:flex-row">
                  {step > 0 ? (
                    <button
                      type="button"
                      onClick={handleBack}
                      className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
                    >
                      {t.monitoringSetup.back}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    onClick={step === stepTitles.length - 1 ? handleActivate : handleNext}
                    disabled={saving}
                    className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
                  >
                    {saving
                      ? t.monitoringSetup.saving
                      : step === stepTitles.length - 1
                        ? t.monitoringSetup.activate
                        : t.monitoringSetup.nextButton}
                  </button>
                </div>
              </div>
            ) : null}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
