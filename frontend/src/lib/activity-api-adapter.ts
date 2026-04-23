import { apiClient } from './api-client';

export type SourceStatus = 'healthy' | 'degraded' | 'retrying';
export type ActivityType = 'check' | 'detect' | 'match' | 'alert' | 'brief' | 'delay' | 'retry' | 'failure';

export interface SourceMonitoring {
  id: string;
  name: string;
  status: SourceStatus;
  lastCheck: string;
  tendersFound24h: number;
  latestResult: string;
}

export interface ActivityEvent {
  id: string;
  type: ActivityType;
  title: string;
  description: string;
  timestamp: string;
  sourceName?: string;
  matchedKeywords: string[];
  matchedCountryCodes: string[];
  matchedIndustryCodes: string[];
  metadata?: Record<string, unknown>;
}

export interface ActivityOverviewSummary {
  total_sources: number;
  healthy_sources: number;
  degraded_sources: number;
  latest_successful_check_at: string | null;
}

export interface ActivitySourceCard {
  source_id: string;
  source_name: string;
  source_country_code: string;
  source_country_name: string;
  source_lifecycle: string;
  source_status: 'healthy' | 'degraded';
  failure_count: number;
  last_successful_run_at: string | null;
  last_failed_run_at: string | null;
  latest_run_status: string | null;
  latest_run_started_at: string | null;
  latest_run_finished_at: string | null;
  latest_run_new_tenders_count: number | null;
  latest_run_updated_tender_count: number | null;
  latest_run_crawled_row_count: number | null;
  latest_run_normalized_row_count: number | null;
  latest_run_accepted_row_count: number | null;
  latest_run_review_required_row_count: number | null;
  latest_run_failure_step: string | null;
  latest_run_failure_reason: string | null;
}

export interface ActivityRecentRunItem {
  id: string;
  source_id: string;
  source_name: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  new_tenders_count: number | null;
  failure_reason: string | null;
}

export interface ActivityFeedItem {
  id: string;
  kind: 'source_checked' | 'source_failed' | 'match_created' | 'instant_alert_sent' | 'daily_brief_sent';
  status: string;
  timestamp: string;
  title: string;
  summary?: string | null;
  source_id?: string | null;
  source_name?: string | null;
  tender_id?: string | null;
  tender_title?: string | null;
  matched_keywords: string[];
  matched_country_codes: string[];
  matched_industry_codes: string[];
  metadata: Record<string, unknown>;
}

export interface ActivityOverviewApiResponse {
  generated_at: string;
  summary: ActivityOverviewSummary;
  sources: ActivitySourceCard[];
  recent_runs: ActivityRecentRunItem[];
  activity_items: ActivityFeedItem[];
}

export const activityApi = {
  getOverview: () => apiClient<ActivityOverviewApiResponse>('/me/activity-overview'),
};

export function mapSourceStatus(status: string): SourceStatus {
  if (status === 'healthy' || status === 'degraded' || status === 'retrying') {
    return status;
  }

  return 'degraded';
}

export function mapRunStatusToSourceStatus(status: string): SourceStatus {
  if (status === 'success') {
    return 'healthy';
  }

  if (status === 'failed') {
    return 'degraded';
  }

  if (status === 'retrying') {
    return 'retrying';
  }

  return 'degraded';
}

export function mapActivityKindToType(kind: ActivityFeedItem['kind']): ActivityType {
  if (kind === 'source_checked') {
    return 'check';
  }

  if (kind === 'source_failed') {
    return 'failure';
  }

  if (kind === 'match_created') {
    return 'match';
  }

  if (kind === 'instant_alert_sent') {
    return 'alert';
  }

  return 'brief';
}
