import {
  keywordProfileApi,
  type KeywordProfileApiResponse,
  type KeywordProfileUpdateRequest,
} from '@/lib/keyword-profile-api-adapter';
import {
  notificationBackendApi,
  type NotificationPreferencesApiResponse,
} from '@/lib/notification-api-adapter';

export interface BusinessProfileWorkspaceResponse {
  profile: KeywordProfileApiResponse;
  notificationPreferences: NotificationPreferencesApiResponse;
}

export const profileApi = {
  getWorkspace: async (): Promise<BusinessProfileWorkspaceResponse> => {
    const [profile, notificationPreferences] = await Promise.all([
      keywordProfileApi.getProfile(),
      notificationBackendApi.getPreferences(),
    ]);

    return {
      profile,
      notificationPreferences,
    };
  },
  updateProfile: (data: KeywordProfileUpdateRequest) => keywordProfileApi.updateProfile(data),
};
