'use client';
import { useEffect, useState } from 'react';
import { useTranslation } from '@/context/language-context';
import NotificationStatusBadge from './notification-status-badge';
import NotificationTypeBadge from './notification-type-badge';
import { notificationBackendApi, type NotificationDeliveryApiItem } from '@/lib/notification-api-adapter';

export default function NotificationDeliveryHistoryPanel() {
  const { t } = useTranslation();
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
    return <div className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />;
  }

  if (error) {
    return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">{error}</div>;
  }

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left rtl:text-right">
          <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
            <tr>
              <th className="px-6 py-4 text-xs font-bold uppercase text-slate-500 tracking-wider">{t.notifications.history.type}</th>
              <th className="px-6 py-4 text-xs font-bold uppercase text-slate-500 tracking-wider">{t.notifications.history.status}</th>
              <th className="px-6 py-4 text-xs font-bold uppercase text-slate-500 tracking-wider">{t.notifications.history.time}</th>
              <th className="px-6 py-4 text-xs font-bold uppercase text-slate-500 tracking-wider text-center">{t.notifications.history.matches}</th>
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
                  {new Date(row.attempted_at).toLocaleString()}
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
