import { activityApi, type ActivityOverviewApiResponse } from '@/lib/activity-api-adapter';
import {
  notificationBackendApi,
  type NotificationDeliveriesApiResponse,
  type NotificationPreferencesApiResponse,
} from '@/lib/notification-api-adapter';
import { tenderApi, type TenderListApiResponse } from '@/lib/tender-api-adapter';

export interface DashboardData {
  activityOverview: ActivityOverviewApiResponse;
  tenders: TenderListApiResponse;
  deliveries: NotificationDeliveriesApiResponse;
  preferences: NotificationPreferencesApiResponse;
}

export async function loadDashboardData(): Promise<DashboardData> {
  const [activityOverview, tenders, deliveries, preferences] = await Promise.all([
    activityApi.getOverview(),
    tenderApi.list({ page: 1, limit: 3 }),
    notificationBackendApi.getDeliveries({ page: 1, limit: 5 }),
    notificationBackendApi.getPreferences(),
  ]);

  return {
    activityOverview,
    tenders,
    deliveries,
    preferences,
  };
}
