import { apiClient } from './api-client';

export interface TenderListApiItem {
  id: string;
  source_id: string;
  source_name: string;
  source_url: string;
  title: string;
  issuing_entity: string;
  closing_date: string | null;
  created_at: string;
  category?: string | null;
  industry_codes: string[];
  primary_industry_code?: string | null;
  ai_summary?: string | null;
  tender_ref?: string | null;
  is_matched: boolean;
  matched_keywords: string[];
  matched_country_codes: string[];
  matched_industry_codes: string[];
}

export interface TenderSourceFilterOption {
  id: string;
  name: string;
}

export interface TenderListApiResponse {
  items: TenderListApiItem[];
  available_sources: TenderSourceFilterOption[];
  total: number;
  page: number;
  limit: number;
}

export const tenderApi = {
  list: (params: {
    page?: number;
    limit?: number;
    search?: string;
    source_id?: string;
    source_ids?: string;
    match_only?: boolean;
    new_only?: boolean;
    closing_soon?: boolean;
    sort?: 'relevance' | 'newest' | 'closingSoon';
  }) =>
    apiClient<TenderListApiResponse>('/tenders', { params }),
  get: (id: string) => apiClient<TenderListApiItem>(`/tenders/${id}`),
};
