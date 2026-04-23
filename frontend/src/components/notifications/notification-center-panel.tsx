'use client';

import { useEffect, useState } from 'react';
import { useTranslation } from '@/context/language-context';
import NotificationTypeBadge from './notification-type-badge';
import NotificationStatusBadge from './notification-status-badge';
import { notificationBackendApi, type NotificationDeliveryApiItem } from '@/lib/notification-api-adapter';
import { eyebrowClass } from '@/lib/locale-ui';

export default function NotificationCenterPanel({
  monitoringActive,
  onOpenSetup,
}: {
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();
  const loadDeliveriesError = t.notifications.errors.loadDeliveries;
  const [alerts, setAlerts] = useState<NotificationDeliveryApiItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    notificationBackendApi
      .getDeliveries({ page: 1, limit: 5 })
      .then((response) => {
        if (!cancelled) {
          setAlerts(response.items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAlerts([]);
          setError(loadDeliveriesError);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [loadDeliveriesError]);

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, index) => (
          <div key={index} className="h-32 animate-pulse rounded-[24px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[24px] border border-red-200 bg-red-50 p-6 dark:border-red-900/30 dark:bg-red-950/20">
        <p className={eyebrowClass(lang, 'text-red-600 dark:text-red-300')}>
          {t.notifications.title}
        </p>
        <p className="mt-2 text-sm font-medium text-red-700 dark:text-red-300">
          {error}
        </p>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="rounded-[24px] border border-dashed border-slate-300 bg-gradient-to-br from-white to-slate-50 p-6 dark:border-slate-700 dark:from-slate-900 dark:to-slate-950/70">
        <p className={eyebrowClass(lang, 'text-blue-600 dark:text-blue-400')}>
          {t.notifications.tabs.center}
        </p>
        <h3 className="text-base font-semibold text-slate-950 dark:text-white">
          {monitoringActive ? t.notifications.empty.centerActiveTitle : t.notifications.empty.centerInactiveTitle}
        </h3>
        <p className="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-400">
          {monitoringActive ? t.notifications.empty.centerActiveDescription : t.notifications.empty.centerInactiveDescription}
        </p>
        <p className="mt-3 text-sm leading-7 text-slate-500 dark:text-slate-400">
          {t.notifications.empty.centerFootnote}
        </p>
        {!monitoringActive ? (
          <button
            type="button"
            onClick={onOpenSetup}
            className="mt-5 inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            {t.notifications.empty.primaryAction}
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <NotificationTypeBadge type={alert.delivery_type} />
                <NotificationStatusBadge status={alert.status} />
              </div>
              <p className="text-base font-semibold text-slate-950 dark:text-white">
                {alert.delivery_type === 'daily_brief'
                  ? t.notifications.center.dailyBriefDelivery
                  : t.notifications.center.instantAlertDelivery}
              </p>
              <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
                {alert.match_count && alert.match_count > 0
                  ? t.notifications.center.matchesIncluded.replace('{count}', String(alert.match_count))
                  : t.notifications.empty.centerFootnote}
              </p>
            </div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(alert.attempted_at))}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
