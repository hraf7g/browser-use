'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import MonitoringSetupModal from '@/components/monitoring/monitoring-setup-modal';
import { useAuthSession } from '@/context/auth-session-context';
import {
  keywordProfileApi,
  type KeywordProfileApiResponse,
} from '@/lib/keyword-profile-api-adapter';
import {
  notificationBackendApi,
  type NotificationPreferencesApiResponse,
} from '@/lib/notification-api-adapter';

type MonitoringSetupContextValue = {
  isSetupOpen: boolean;
  openSetup: () => void;
  closeSetup: () => void;
  refreshMonitoringSetup: () => Promise<void>;
  loading: boolean;
  profile: KeywordProfileApiResponse | null;
  preferences: NotificationPreferencesApiResponse | null;
  monitoringActive: boolean;
  hasKeywordsConfigured: boolean;
};

const MonitoringSetupContext = createContext<MonitoringSetupContextValue | undefined>(undefined);

export function MonitoringSetupProvider({ children }: { children: React.ReactNode }) {
  const { status } = useAuthSession();
  const [isSetupOpen, setIsSetupOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<KeywordProfileApiResponse | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreferencesApiResponse | null>(null);

  const refreshMonitoringSetup = useCallback(async () => {
    if (status !== 'authenticated') {
      setProfile(null);
      setPreferences(null);
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      const [nextProfile, nextPreferences] = await Promise.all([
        keywordProfileApi.getProfile(),
        notificationBackendApi.getPreferences(),
      ]);

      setProfile(nextProfile);
      setPreferences(nextPreferences);
    } catch {
      setProfile(null);
      setPreferences(null);
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    void refreshMonitoringSetup();
  }, [refreshMonitoringSetup]);

  const value = useMemo<MonitoringSetupContextValue>(() => {
    const hasKeywordsConfigured = Boolean(profile && profile.keywords.length > 0);

    return {
      isSetupOpen,
      openSetup: () => setIsSetupOpen(true),
      closeSetup: () => setIsSetupOpen(false),
      refreshMonitoringSetup,
      loading,
      profile,
      preferences,
      monitoringActive: hasKeywordsConfigured && Boolean(profile?.alert_enabled),
      hasKeywordsConfigured,
    };
  }, [isSetupOpen, loading, preferences, profile, refreshMonitoringSetup]);

  return (
    <MonitoringSetupContext.Provider value={value}>
      {children}
      <MonitoringSetupModal
        open={isSetupOpen}
        onClose={() => setIsSetupOpen(false)}
        profile={profile}
        preferences={preferences}
        onSaved={(nextProfile, nextPreferences) => {
          setProfile(nextProfile);
          setPreferences(nextPreferences);
        }}
      />
    </MonitoringSetupContext.Provider>
  );
}

export function useMonitoringSetup() {
  const context = useContext(MonitoringSetupContext);

  if (!context) {
    throw new Error('useMonitoringSetup must be used within MonitoringSetupProvider');
  }

  return context;
}
