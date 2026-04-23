'use client';

import { startTransition, useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, BellRing, FileSearch, Radar, RefreshCcw } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import MonitoringGuidancePanel from '@/components/monitoring/monitoring-guidance-panel';
import DashboardHero from '@/components/dashboard/dashboard-hero';
import DashboardStatsRow from '@/components/dashboard/dashboard-stats-row';
import DashboardPriorityTenders from '@/components/dashboard/dashboard-priority-tenders';
import DashboardLiveActivity from '@/components/dashboard/dashboard-live-activity';
import DashboardSourceHealth from '@/components/dashboard/dashboard-source-health';
import DashboardAlertSummary from '@/components/dashboard/dashboard-alert-summary';
import DashboardProfileSummary from '@/components/dashboard/dashboard-profile-summary';
import DashboardAIControlCard from '@/components/dashboard/dashboard-ai-control-card';
import DashboardBrowserAgentCard from '@/components/dashboard/dashboard-browser-agent-card';
import DashboardBrowserRuntimeCard from '@/components/dashboard/dashboard-browser-runtime-card';
import { useMonitoringSetup } from '@/context/monitoring-setup-context';
import { useAuthSession } from '@/context/auth-session-context';
import { keywordProfileApi, type KeywordProfileApiResponse } from '@/lib/keyword-profile-api-adapter';
import { activityApi, type ActivityOverviewApiResponse } from '@/lib/activity-api-adapter';
import {
  notificationBackendApi,
  type NotificationDeliveriesApiResponse,
  type NotificationPreferencesApiResponse,
} from '@/lib/notification-api-adapter';
import { tenderApi, type TenderListApiResponse } from '@/lib/tender-api-adapter';

type DashboardPanelState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

const EMPTY_NOTIFICATION_PREFERENCES: NotificationPreferencesApiResponse = {
  user_id: 'unavailable',
  email_enabled: false,
  whatsapp_enabled: false,
  whatsapp_phone_e164: null,
  instant_alert_enabled: false,
  daily_brief_enabled: false,
  preferred_language: 'auto',
};

const EMPTY_KEYWORD_PROFILE: KeywordProfileApiResponse = {
  keywords: [],
  alert_enabled: false,
  country_codes: [],
  industry_codes: [],
  industry_label: null,
};

function DashboardSkeleton() {
  return (
    <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8">
      <div className="h-40 animate-pulse rounded-[28px] border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-28 animate-pulse rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-8 xl:grid-cols-12">
        <div className="h-[420px] rounded-2xl border border-slate-200 bg-white animate-pulse xl:col-span-8 dark:border-slate-800 dark:bg-slate-900" />
        <div className="space-y-8 xl:col-span-4">
          <div className="h-[320px] rounded-2xl border border-slate-200 bg-white animate-pulse dark:border-slate-800 dark:bg-slate-900" />
          <div className="h-[220px] rounded-2xl border border-slate-200 bg-white animate-pulse dark:border-slate-800 dark:bg-slate-900" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { t, lang } = useTranslation();
  const { monitoringActive, openSetup } = useMonitoringSetup();
  const { user } = useAuthSession();
  const [activityOverview, setActivityOverview] = useState<DashboardPanelState<ActivityOverviewApiResponse>>({
    data: null,
    error: null,
    loading: true,
  });
  const [tenders, setTenders] = useState<DashboardPanelState<TenderListApiResponse>>({
    data: null,
    error: null,
    loading: true,
  });
  const [deliveries, setDeliveries] = useState<DashboardPanelState<NotificationDeliveriesApiResponse>>({
    data: null,
    error: null,
    loading: true,
  });
  const [preferences, setPreferences] = useState<DashboardPanelState<NotificationPreferencesApiResponse>>({
    data: null,
    error: null,
    loading: true,
  });
  const [profile, setProfile] = useState<DashboardPanelState<KeywordProfileApiResponse>>({
    data: null,
    error: null,
    loading: true,
  });
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setActivityOverview((current) => ({ ...current, loading: true, error: null }));
    setTenders((current) => ({ ...current, loading: true, error: null }));
    setDeliveries((current) => ({ ...current, loading: true, error: null }));
    setPreferences((current) => ({ ...current, loading: true, error: null }));
    setProfile((current) => ({ ...current, loading: true, error: null }));

    const [nextActivityOverview, nextTenders, nextDeliveries, nextPreferences, nextProfile] = await Promise.allSettled([
      activityApi.getOverview(),
      tenderApi.list({ page: 1, limit: 3 }),
      notificationBackendApi.getDeliveries({ page: 1, limit: 5 }),
      notificationBackendApi.getPreferences(),
      keywordProfileApi.getProfile(),
    ]);

    let succeededCount = 0;

    if (nextActivityOverview.status === 'fulfilled') {
      succeededCount += 1;
      setActivityOverview({ data: nextActivityOverview.value, error: null, loading: false });
    } else {
      setActivityOverview((current) => ({
        data: current.data,
        error: nextActivityOverview.reason instanceof Error ? nextActivityOverview.reason.message : t.dashboard.refresh.panelError,
        loading: false,
      }));
    }

    if (nextTenders.status === 'fulfilled') {
      succeededCount += 1;
      setTenders({ data: nextTenders.value, error: null, loading: false });
    } else {
      setTenders((current) => ({
        data: current.data,
        error: nextTenders.reason instanceof Error ? nextTenders.reason.message : t.dashboard.refresh.panelError,
        loading: false,
      }));
    }

    if (nextDeliveries.status === 'fulfilled') {
      succeededCount += 1;
      setDeliveries({ data: nextDeliveries.value, error: null, loading: false });
    } else {
      setDeliveries((current) => ({
        data: current.data,
        error: nextDeliveries.reason instanceof Error ? nextDeliveries.reason.message : t.dashboard.refresh.panelError,
        loading: false,
      }));
    }

    if (nextPreferences.status === 'fulfilled') {
      succeededCount += 1;
      setPreferences({ data: nextPreferences.value, error: null, loading: false });
    } else {
      setPreferences((current) => ({
        data: current.data,
        error: nextPreferences.reason instanceof Error ? nextPreferences.reason.message : t.dashboard.refresh.panelError,
        loading: false,
      }));
    }

    if (nextProfile.status === 'fulfilled') {
      succeededCount += 1;
      setProfile({ data: nextProfile.value, error: null, loading: false });
    } else {
      setProfile((current) => ({
        data: current.data,
        error: nextProfile.reason instanceof Error ? nextProfile.reason.message : t.dashboard.refresh.panelError,
        loading: false,
      }));
    }

    if (succeededCount > 0) {
      setLastUpdatedAt(new Date().toISOString());
    }
  }, [t.dashboard.refresh.panelError]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const isInitialLoading =
    activityOverview.loading &&
    tenders.loading &&
    deliveries.loading &&
    preferences.loading &&
    profile.loading &&
    activityOverview.data === null &&
    tenders.data === null &&
    deliveries.data === null &&
    preferences.data === null &&
    profile.data === null;

  if (isInitialLoading) {
    return <DashboardSkeleton />;
  }

  const monitoredSources = activityOverview.data?.summary.total_sources ?? 0;
  const healthySources = activityOverview.data?.summary.healthy_sources ?? 0;
  const openTenders = tenders.data?.total ?? 0;
  const recentDeliveries = deliveries.data?.total ?? 0;
  const isZeroState = monitoredSources === 0 && healthySources === 0 && openTenders === 0 && recentDeliveries === 0;
  const panelErrorCount = [
    activityOverview.error,
    tenders.error,
    deliveries.error,
    preferences.error,
    profile.error,
  ].filter(Boolean).length;
  const formattedLastUpdatedAt = lastUpdatedAt
    ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(lastUpdatedAt))
    : t.dashboard.refresh.notAvailable;

  return (
    <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-10">
      <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-semibold text-slate-900 dark:text-white">
            {t.dashboard.refresh.title}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {t.dashboard.refresh.lastUpdated.replace('{value}', formattedLastUpdatedAt)}
          </p>
          {panelErrorCount > 0 ? (
            <p className="inline-flex items-center gap-2 text-sm text-amber-700 dark:text-amber-300">
              <AlertTriangle size={15} />
              {t.dashboard.refresh.partialWarning.replace('{count}', String(panelErrorCount))}
            </p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => startTransition(() => void loadDashboard())}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
        >
          <RefreshCcw size={16} />
          {t.dashboard.refresh.action}
        </button>
      </section>

      <DashboardHero
        monitoredSources={monitoredSources}
        openTenders={openTenders}
        monitoringActive={monitoringActive}
        onOpenSetup={openSetup}
      />
      <DashboardStatsRow
        monitoredSources={monitoredSources}
        healthySources={healthySources}
        openTenders={openTenders}
        recentDeliveries={recentDeliveries}
        monitoringActive={monitoringActive}
      />

      {!monitoringActive || isZeroState ? (
        <MonitoringGuidancePanel
          badge={t.dashboard.guidance.badge}
          title={t.dashboard.guidance.title}
          description={t.dashboard.guidance.description}
          points={[
            {
              icon: FileSearch,
              title: t.dashboard.guidance.cards.profile.title,
              description: t.dashboard.guidance.cards.profile.description,
            },
            {
              icon: Radar,
              title: t.dashboard.guidance.cards.monitoring.title,
              description: t.dashboard.guidance.cards.monitoring.description,
            },
            {
              icon: BellRing,
              title: t.dashboard.guidance.cards.alerts.title,
              description: t.dashboard.guidance.cards.alerts.description,
            },
          ]}
          primaryLabel={t.dashboard.guidance.primaryAction}
          onPrimaryAction={openSetup}
          secondaryLabel={t.dashboard.guidance.secondaryAction}
          secondaryHref="/notifications"
        />
      ) : null}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        <div className="xl:col-span-8 space-y-8">
          <DashboardPanel
            loading={tenders.loading && tenders.data === null}
            error={tenders.error}
            onRetry={() => startTransition(() => void loadDashboard())}
          >
            <DashboardPriorityTenders
              tenders={tenders.data?.items ?? []}
              monitoringActive={monitoringActive}
              onOpenSetup={openSetup}
            />
          </DashboardPanel>
          <DashboardPanel
            loading={activityOverview.loading && activityOverview.data === null}
            error={activityOverview.error}
            onRetry={() => startTransition(() => void loadDashboard())}
          >
            <DashboardLiveActivity
              items={activityOverview.data?.activity_items ?? []}
              monitoringActive={monitoringActive}
              onOpenSetup={openSetup}
            />
          </DashboardPanel>
        </div>

        <div className="xl:col-span-4 space-y-8 h-full">
          <DashboardPanel
            loading={activityOverview.loading && activityOverview.data === null}
            error={activityOverview.error}
            onRetry={() => startTransition(() => void loadDashboard())}
          >
            <DashboardSourceHealth
              sources={activityOverview.data?.sources ?? []}
              monitoringActive={monitoringActive}
              onOpenSetup={openSetup}
            />
          </DashboardPanel>
          <DashboardPanel
            loading={deliveries.loading && deliveries.data === null}
            error={deliveries.error}
            onRetry={() => startTransition(() => void loadDashboard())}
          >
            <DashboardAlertSummary
              deliveries={deliveries.data?.items ?? []}
              monitoringActive={monitoringActive}
              onOpenSetup={openSetup}
            />
          </DashboardPanel>
          <DashboardPanel
            loading={(preferences.loading && preferences.data === null) || (profile.loading && profile.data === null)}
            error={profile.error ?? preferences.error}
            onRetry={() => startTransition(() => void loadDashboard())}
          >
            <DashboardProfileSummary
              profile={profile.data ?? EMPTY_KEYWORD_PROFILE}
              preferences={preferences.data ?? EMPTY_NOTIFICATION_PREFERENCES}
              monitoringActive={monitoringActive}
              onOpenSetup={openSetup}
            />
          </DashboardPanel>
        </div>
      </div>

      <section className="border-t border-slate-200 pt-8 dark:border-slate-800">
        <div className="max-w-3xl space-y-2">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">
            {t.dashboard.automation.eyebrow}
          </p>
          <h2 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
            {t.dashboard.automation.title}
          </h2>
          <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
            {t.dashboard.automation.description}
          </p>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-8 xl:grid-cols-12 items-start">
          <div className={user?.is_operator ? 'xl:col-span-7' : 'xl:col-span-12'}>
            <DashboardBrowserAgentCard />
          </div>

          {user?.is_operator ? (
            <div className="xl:col-span-5 space-y-8">
              <div className="space-y-2">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700 dark:text-amber-300">
                  {t.dashboard.operator.eyebrow}
                </p>
                <h3 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">
                  {t.dashboard.operator.title}
                </h3>
                <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
                  {t.dashboard.operator.description}
                </p>
              </div>
              <DashboardBrowserRuntimeCard />
              <DashboardAIControlCard />
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function DashboardPanel({
  loading,
  error,
  onRetry,
  children,
}: {
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  children: React.ReactNode;
}) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="h-32 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-6 shadow-sm dark:border-red-900/30 dark:bg-red-950/20">
        <div className="space-y-3">
          <p className="text-sm font-semibold text-red-700 dark:text-red-300">
            {t.dashboard.refresh.panelUnavailable}
          </p>
          <p className="text-sm text-red-600 dark:text-red-200">{error}</p>
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 bg-white px-4 py-2.5 text-sm font-semibold text-red-700 transition-colors hover:bg-red-50 dark:border-red-900/40 dark:bg-red-950/10 dark:text-red-200 dark:hover:bg-red-950/20"
          >
            <RefreshCcw size={16} />
            {t.dashboard.refresh.retry}
          </button>
        </div>
      </section>
    );
  }

  return <>{children}</>;
}
