'use client';

import { useEffect, useState } from 'react';
import NotificationTypeBadge from './notification-type-badge';
import NotificationStatusBadge from './notification-status-badge';
import { notificationBackendApi, type NotificationDeliveryApiItem } from '@/lib/notification-api-adapter';

export default function NotificationCenterPanel() {
  const [alerts, setAlerts] = useState<NotificationDeliveryApiItem[]>([]);

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
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-4">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <NotificationTypeBadge type={alert.delivery_type} />
                <NotificationStatusBadge status={alert.status} />
              </div>
              <p className="text-base font-semibold text-slate-950 dark:text-white">
                {alert.delivery_type === 'daily_brief' ? 'Daily brief delivery' : 'Instant alert delivery'}
              </p>
            </div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{new Date(alert.attempted_at).toLocaleString()}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
