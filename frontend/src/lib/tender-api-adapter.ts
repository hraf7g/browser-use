import { apiClient } from './api-client';

export interface TenderListApiItem {
  id: string;
  source_id: string;
  source_url: string;
  title: string;
  issuing_entity: string;
  closing_date: string;
  category?: string | null;
  ai_summary?: string | null;
  tender_ref?: string | null;
}

export interface TenderListApiResponse {
  items: TenderListApiItem[];
  total: number;
  page: number;
  limit: number;
}

export const tenderApi = {
  list: (params: { page?: number; limit?: number; search?: string; source_id?: string }) =>
    apiClient<TenderListApiResponse>('/tenders', { params }),
  get: (id: string) => apiClient<TenderListApiItem>(`/tenders/${id}`),
};
