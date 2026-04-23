import { apiClient } from '@/lib/api-client';

export interface BrowserAgentRun {
  id: string;
  user_id: string;
  status: 'queued' | 'running' | 'cancelling' | 'cancelled' | 'completed' | 'failed';
  task_prompt: string;
  start_url: string | null;
  allowed_domains: string[] | null;
  max_steps: number;
  step_timeout_seconds: number;
  llm_timeout_seconds: number;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  cancel_requested_at: string | null;
  last_heartbeat_at: string | null;
  error_message: string | null;
  final_result_text: string | null;
  llm_provider: string;
  llm_model: string;
  created_at: string;
  updated_at: string;
}

export interface BrowserAgentRunListResponse {
  items: BrowserAgentRun[];
  max_concurrent_runs_per_user: number;
  max_queued_runs_per_user: number;
  max_global_running_runs: number;
  current_user_running_count: number;
  current_user_queued_count: number;
  global_running_count: number;
}

export interface BrowserAgentRunCreatePayload {
  task_prompt: string;
  start_url?: string | null;
  allowed_domains?: string[] | null;
  max_steps?: number | null;
}

export const browserAgentApi = {
  listRuns: () => apiClient<BrowserAgentRunListResponse>('/browser-agent-runs'),
  queueRun: (payload: BrowserAgentRunCreatePayload) =>
    apiClient<BrowserAgentRun>('/browser-agent-runs', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  cancelRun: (runId: string) =>
    apiClient<{ run: BrowserAgentRun; cancelled_immediately: boolean }>(
      `/browser-agent-runs/${runId}/cancel`,
      {
        method: 'POST',
      }
    ),
};
