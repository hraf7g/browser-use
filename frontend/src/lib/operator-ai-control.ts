import { apiClient } from '@/lib/api-client';

export interface OperatorAIControlState {
  ai_enrichment_enabled: boolean;
  emergency_stop_enabled: boolean;
  emergency_stop_reason: string | null;
  max_enrichment_batch_size_override: number | null;
  max_daily_requests_override: number | null;
  max_daily_reserved_tokens_override: number | null;
  effective_ai_provider: string;
  effective_ai_enrichment_enabled: boolean;
  effective_enrichment_batch_size: number;
  effective_daily_request_budget: number | null;
  effective_daily_reserved_token_budget: number | null;
  today_usage_date: string;
  today_request_count: number;
  today_blocked_request_count: number;
  today_throttled_request_count: number;
  today_provider_error_count: number;
  today_estimated_input_tokens: number;
  today_reserved_total_tokens: number;
  today_actual_prompt_tokens: number;
  today_actual_completion_tokens: number;
  today_actual_total_tokens: number;
  budget_exhausted: boolean;
  budget_exhausted_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface OperatorAIControlUpdatePayload {
  ai_enrichment_enabled: boolean;
  emergency_stop_enabled: boolean;
  emergency_stop_reason: string | null;
  max_enrichment_batch_size_override: number | null;
  max_daily_requests_override?: number | null;
  max_daily_reserved_tokens_override?: number | null;
}

export const operatorAiControlApi = {
  getState: () => apiClient<OperatorAIControlState>('/api/operator/ai-control'),
  updateState: (payload: OperatorAIControlUpdatePayload) =>
    apiClient<OperatorAIControlState>('/api/operator/ai-control', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
};
