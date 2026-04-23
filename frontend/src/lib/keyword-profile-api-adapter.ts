import { apiClient } from './api-client';

export interface KeywordProfileApiResponse {
  keywords: string[];
  alert_enabled: boolean;
  country_codes: string[];
  industry_codes: string[];
  industry_label: string | null;
}

export interface KeywordProfileUpdateRequest {
  keywords: string[];
  alert_enabled: boolean;
  country_codes?: string[];
  industry_codes?: string[];
  industry_label?: string | null;
}

export const keywordProfileApi = {
  getProfile: () => apiClient<KeywordProfileApiResponse>('/me/keyword-profile'),
  updateProfile: (data: KeywordProfileUpdateRequest) =>
    apiClient<KeywordProfileApiResponse>('/me/keyword-profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};
