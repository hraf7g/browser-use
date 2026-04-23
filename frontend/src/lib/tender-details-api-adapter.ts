import { apiClient } from './api-client';

export interface TenderDetailsNotificationState {
  match_created_at: string | null;
  matched_keywords: string[];
  matched_country_codes: string[];
  matched_industry_codes: string[];
  instant_alert_sent: boolean;
  instant_alert_sent_at: string | null;
  daily_brief_sent: boolean;
  daily_brief_sent_at: string | null;
}

export interface TenderDetailsTimelineItem {
  id: string;
  kind:
    | 'source_checked'
    | 'tender_detected'
    | 'match_created'
    | 'instant_alert_sent'
    | 'daily_brief_sent';
  status: string;
  timestamp: string;
  title: string;
  summary?: string | null;
}

export interface TenderDetailsApiResponse {
  id: string;
  title: string;
  issuing_entity: string;
  source_id: string;
  source_name?: string | null;
  source_url: string;
  closing_date: string | null;
  opening_date?: string | null;
  published_at?: string | null;
  tender_ref?: string | null;
  category?: string | null;
  industry_codes: string[];
  primary_industry_code?: string | null;
  ai_summary?: string | null;
  matched_keywords: string[];
  matched_country_codes: string[];
  matched_industry_codes: string[];
  notification_state: TenderDetailsNotificationState;
  activity_timeline: TenderDetailsTimelineItem[];
}

export const tenderDetailsApi = {
  get: (id: string) =>
    apiClient<TenderDetailsApiResponse>(`/tenders/${encodeURIComponent(id)}`),
};
