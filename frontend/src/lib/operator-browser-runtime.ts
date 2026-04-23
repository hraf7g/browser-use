import { apiClient } from '@/lib/api-client';

export interface OperatorBrowserRuntimeStatus {
  queued_count: number;
  running_count: number;
  cancelling_count: number;
  completed_last_24h_count: number;
  failed_last_24h_count: number;
  cancelled_last_24h_count: number;
  stale_running_count: number;
  oldest_queued_at: string | null;
  latest_started_at: string | null;
  latest_finished_at: string | null;
  max_global_running_runs: number;
  worker_stale_heartbeat_seconds: number;
}

export const operatorBrowserRuntimeApi = {
  getStatus: () => apiClient<OperatorBrowserRuntimeStatus>('/api/operator/browser-runtime'),
};
