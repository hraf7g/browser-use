'use client';

import Link from 'next/link';
import { Mail, MessageSquare } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import type { NotificationDeliveryApiItem } from '@/lib/notification-api-adapter';
import NotificationStatusBadge from '../notifications/notification-status-badge';
import NotificationTypeBadge from '../notifications/notification-type-badge';

export default function DashboardAlertSummary({
  deliveries,
  monitoringActive,
  onOpenSetup,
}: {
  deliveries: NotificationDeliveryApiItem[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.alerts.title}</h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t.notifications.summary}</p>
        </div>
        <Link
          href="/notifications"
          className="text-sm font-bold text-blue-600 transition-colors hover:text-blue-700"
        >
          {t.dashboard.alerts.viewAll}
        </Link>
      </div>

      {deliveries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 px-4 py-4 dark:border-slate-800 dark:bg-slate-950/50">
          <p className="text-sm font-semibold text-slate-900 dark:text-white">
            {monitoringActive ? t.dashboard.alerts.emptyActiveTitle : t.dashboard.alerts.emptyInactiveTitle}
          </p>
          <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
            {monitoringActive ? t.dashboard.alerts.emptyActiveDescription : t.dashboard.alerts.emptyInactiveDescription}
          </p>
          {!monitoringActive ? (
            <button
              type="button"
              onClick={onOpenSetup}
              className="mt-4 inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              {t.dashboard.alerts.setupAction}
            </button>
          ) : null}
        </div>
      ) : (
        <div className="space-y-4">
          {deliveries.map((delivery) => (
            <div
              key={delivery.id}
              className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3 dark:border-slate-800 dark:bg-slate-950/50"
            >
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-slate-500 dark:bg-slate-900">
                  {delivery.delivery_type === 'daily_brief' ? <Mail size={18} /> : <MessageSquare size={18} />}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    {delivery.delivery_type === 'daily_brief' ? t.notifications.preferences.daily : t.notifications.preferences.instant}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(delivery.attempted_at))}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  {delivery.match_count ?? 0}
                </span>
                <NotificationStatusBadge status={delivery.status} reason={delivery.failure_reason ?? undefined} />
                <NotificationTypeBadge type={delivery.delivery_type} />
              </div>
            </div>
          ))}
          <Link
            href="/notifications"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {t.dashboard.alerts.openLog}
          </Link>
        </div>
      )}
    </section>
  );
}
