import { apiClient } from './api-client';

export interface NotificationPreferencesApiResponse {
  user_id: string;
  email_enabled: boolean;
  whatsapp_enabled: boolean;
  whatsapp_phone_e164: string | null;
  daily_brief_enabled: boolean;
  instant_alert_enabled: boolean;
  preferred_language: 'auto' | 'en' | 'ar';
}

export interface NotificationDeliveryApiItem {
  id: string;
  delivery_type: string;
  status: 'sent' | 'failed' | 'pending';
  attempted_at: string;
  sent_at?: string | null;
  match_count?: number | null;
  failure_reason?: string | null;
}

export interface NotificationDeliveriesApiResponse {
  page: number;
  limit: number;
  total: number;
  items: NotificationDeliveryApiItem[];
}

export const notificationBackendApi = {
  getPreferences: () =>
    apiClient<NotificationPreferencesApiResponse>('/me/notification-preferences'),
  updatePreferences: (data: Partial<NotificationPreferencesApiResponse>) =>
    apiClient<NotificationPreferencesApiResponse>('/me/notification-preferences', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  getDeliveries: (params?: { page?: number; limit?: number }) =>
    apiClient<NotificationDeliveriesApiResponse>('/me/notification-deliveries', {
      params,
    }),
};
