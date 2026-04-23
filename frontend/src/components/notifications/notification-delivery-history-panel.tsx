'use client';
import { useEffect, useState } from 'react';
import { useTranslation } from '@/context/language-context';
import NotificationStatusBadge from './notification-status-badge';
import NotificationTypeBadge from './notification-type-badge';
import { notificationBackendApi, type NotificationDeliveryApiItem } from '@/lib/notification-api-adapter';
import { compactBadgeClass, eyebrowClass } from '@/lib/locale-ui';

export default function NotificationDeliveryHistoryPanel({
  monitoringActive,
  onOpenSetup,
}: {
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  const { t, lang } = useTranslation();
  const [history, setHistory] = useState<NotificationDeliveryApiItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    notificationBackendApi
      .getDeliveries({ page: 1, limit: 20 })
      .then((response) => {
        if (!cancelled) {
          setHistory(response.items);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
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
  }, []);

  if (loading) {
    return <div className="h-56 animate-pulse rounded-[24px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />;
  }

  if (error) {
    return (
      <div className="rounded-[24px] border border-red-200 bg-red-50 p-6 dark:border-red-900/30 dark:bg-red-950/20">
        <p className={eyebrowClass(lang, 'text-red-600 dark:text-red-300')}>{t.notifications.tabs.history}</p>
        <p className="mt-2 text-sm font-medium text-red-700 dark:text-red-300">{error}</p>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="rounded-[24px] border border-dashed border-slate-300 bg-gradient-to-br from-white to-slate-50 p-6 dark:border-slate-700 dark:from-slate-900 dark:to-slate-950/70">
        <p className={eyebrowClass(lang, 'text-blue-600 dark:text-blue-400')}>
          {t.notifications.tabs.history}
        </p>
        <h3 className="text-base font-semibold text-slate-950 dark:text-white">
          {monitoringActive ? t.notifications.empty.historyActiveTitle : t.notifications.empty.historyInactiveTitle}
        </h3>
        <p className="mt-2 text-sm leading-7 text-slate-500 dark:text-slate-400">
          {monitoringActive ? t.notifications.empty.historyActiveDescription : t.notifications.empty.historyInactiveDescription}
        </p>
        {!monitoringActive ? (
          <button
            type="button"
            onClick={onOpenSetup}
            className="mt-5 inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {t.notifications.empty.primaryAction}
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="overflow-x-auto">
        <table className="w-full text-left rtl:text-right">
          <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
            <tr>
              <th className={`px-6 py-4 text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.history.type}</th>
              <th className={`px-6 py-4 text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.history.status}</th>
              <th className={`px-6 py-4 text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.history.time}</th>
              <th className={`px-6 py-4 text-center text-slate-500 ${compactBadgeClass(lang)}`}>{t.notifications.history.matches}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {history.map((row) => (
              <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                <td className="px-6 py-4">
                  <NotificationTypeBadge type={row.delivery_type} />
                </td>
                <td className="px-6 py-4">
                  <NotificationStatusBadge status={row.status} reason={row.failure_reason ?? undefined} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 dark:text-slate-400 font-medium">
                  {new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(row.attempted_at))}
                </td>
                <td className="px-6 py-4 text-center">
                   <span className="text-sm font-bold text-slate-900 dark:text-white">{row.match_count ?? 0}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
