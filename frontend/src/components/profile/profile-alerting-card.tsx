'use client';

import Link from 'next/link';
import { BellRing, Mail, MessageSquare, Settings2, Zap } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import type { NotificationPreferencesApiResponse } from '@/lib/notification-api-adapter';

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (nextValue: boolean) => void;
}) {
  return (
    <label
      className={`relative inline-flex h-6 w-12 cursor-pointer items-center rounded-full transition-colors ${
        checked ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'
      }`}
    >
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span
        className={`absolute top-1 h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${checked ? 'translate-x-7' : 'translate-x-1'}`}
      />
    </label>
  );
}

function StatusRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Mail;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          <Icon size={18} />
        </div>
        <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{label}</span>
      </div>
      <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">{value}</span>
    </div>
  );
}

export default function ProfileAlertingCard({
  alertEnabled,
  notificationPreferences,
  onAlertEnabledChange,
}: {
  alertEnabled: boolean;
  notificationPreferences: NotificationPreferencesApiResponse;
  onAlertEnabledChange: (nextValue: boolean) => void;
}) {
  const { t } = useTranslation();

  return (
    <section className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:p-8">
      <div className="space-y-3">
        <h2 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.profilePage.alerting.title}
        </h2>
        <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
          {t.profilePage.alerting.description}
        </p>
      </div>

      <div className="mt-5 rounded-[24px] border border-slate-200 bg-slate-50/80 p-5 dark:border-slate-700 dark:bg-slate-950/40">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-slate-950 dark:text-white">
              {t.profilePage.alerting.profileToggleTitle}
            </p>
            <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
              {alertEnabled
                ? t.profilePage.alerting.profileToggleEnabled
                : t.profilePage.alerting.profileToggleDisabled}
            </p>
          </div>
          <Toggle checked={alertEnabled} onChange={onAlertEnabledChange} />
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <StatusRow
          icon={Zap}
          label={t.profilePage.alerting.instant}
          value={
            notificationPreferences.instant_alert_enabled
              ? t.profilePage.alerting.enabled
              : t.profilePage.alerting.disabled
          }
        />
        <StatusRow
          icon={BellRing}
          label={t.profilePage.alerting.daily}
          value={
            notificationPreferences.daily_brief_enabled
              ? t.profilePage.alerting.enabled
              : t.profilePage.alerting.disabled
          }
        />
        <StatusRow
          icon={Mail}
          label={t.profilePage.alerting.email}
          value={
            notificationPreferences.email_enabled
              ? t.profilePage.alerting.enabled
              : t.profilePage.alerting.disabled
          }
        />
        <StatusRow
          icon={MessageSquare}
          label={t.profilePage.alerting.whatsapp}
          value={
            notificationPreferences.whatsapp_enabled
              ? t.profilePage.alerting.enabled
              : t.profilePage.alerting.disabled
          }
        />
      </div>

      <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white/70 p-4 text-sm leading-6 text-slate-500 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-400">
        {t.profilePage.alerting.footnote}
      </div>

      <div className="mt-5">
        <Link
          href="/notifications"
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
        >
          <Settings2 size={16} />
          {t.profilePage.alerting.manageNotifications}
        </Link>
      </div>
    </section>
  );
}
