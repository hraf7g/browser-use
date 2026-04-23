'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { AlertTriangle, Bot, Clock3, ServerCog } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import {
  operatorBrowserRuntimeApi,
  type OperatorBrowserRuntimeStatus,
} from '@/lib/operator-browser-runtime';

export default function DashboardBrowserRuntimeCard() {
  const { t, lang } = useTranslation();
  const [status, setStatus] = useState<OperatorBrowserRuntimeStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const next = await operatorBrowserRuntimeApi.getStatus();
        if (!cancelled) {
          setStatus(next);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t.dashboard.browserRuntime.errorFallback);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    const intervalId = window.setInterval(() => {
      void load();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [t.dashboard.browserRuntime.errorFallback]);

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="h-28 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
      </section>
    );
  }

  if (error && status === null) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-5 shadow-sm dark:border-red-900/30 dark:bg-red-950/20">
        <p className="text-sm font-semibold text-red-700 dark:text-red-300">{error}</p>
      </section>
    );
  }

  if (status === null) {
    return null;
  }

  const dateFormatter = new Intl.DateTimeFormat(lang, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  const healthLabel =
    status.stale_running_count > 0
      ? t.dashboard.browserRuntime.health.degraded
      : status.running_count > 0 || status.queued_count > 0
        ? t.dashboard.browserRuntime.health.active
        : t.dashboard.browserRuntime.health.idle;

  return (
    <section className="rounded-2xl border border-cyan-200 bg-white p-5 shadow-sm dark:border-cyan-900/30 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-300">
            <ServerCog size={14} />
            <span>{t.dashboard.browserRuntime.badge}</span>
          </div>
          <h3 className="text-lg font-bold text-slate-950 dark:text-white">
            {t.dashboard.browserRuntime.title}
          </h3>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-400">
            {t.dashboard.browserRuntime.description}
          </p>
        </div>
        <div className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">
          {healthLabel}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <RuntimeMetric
          label={t.dashboard.browserRuntime.metrics.queued}
          value={status.queued_count}
        />
        <RuntimeMetric
          label={t.dashboard.browserRuntime.metrics.running}
          value={status.running_count}
        />
        <RuntimeMetric
          label={t.dashboard.browserRuntime.metrics.cancelling}
          value={status.cancelling_count}
        />
        <RuntimeMetric
          label={t.dashboard.browserRuntime.metrics.capacity}
          value={status.max_global_running_runs}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <RuntimeMeta
          icon={<Bot size={15} />}
          label={t.dashboard.browserRuntime.last24h}
          value={t.dashboard.browserRuntime.last24hValue
            .replace('{completed}', String(status.completed_last_24h_count))
            .replace('{failed}', String(status.failed_last_24h_count))
            .replace('{cancelled}', String(status.cancelled_last_24h_count))}
        />
        <RuntimeMeta
          icon={<Clock3 size={15} />}
          label={t.dashboard.browserRuntime.oldestQueued}
          value={
            status.oldest_queued_at
              ? dateFormatter.format(new Date(status.oldest_queued_at))
              : t.dashboard.browserRuntime.notAvailable
          }
        />
        <RuntimeMeta
          icon={<ServerCog size={15} />}
          label={t.dashboard.browserRuntime.staleThreshold}
          value={t.dashboard.browserRuntime.staleThresholdValue.replace(
            '{seconds}',
            String(status.worker_stale_heartbeat_seconds),
          )}
        />
      </div>

      {status.stale_running_count > 0 ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
          <span className="inline-flex items-center gap-2 font-semibold">
            <AlertTriangle size={16} />
            {t.dashboard.browserRuntime.staleWarning.replace(
              '{count}',
              String(status.stale_running_count),
            )}
          </span>
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
          {error}
        </div>
      ) : null}
    </section>
  );
}

function RuntimeMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
      <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{label}</p>
      <p className="mt-1 text-base font-semibold text-slate-900 dark:text-white">{value}</p>
    </div>
  );
}

function RuntimeMeta({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-3 dark:border-slate-800 dark:bg-slate-950/60">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{value}</p>
    </div>
  );
}
