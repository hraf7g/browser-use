'use client';

import { useEffect, useState } from 'react';
import { LoaderCircle, OctagonX, PlayCircle, SquareTerminal } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import { browserAgentApi, type BrowserAgentRunListResponse } from '@/lib/browser-agent-api';

function formatTimestamp(value: string | null, locale: string): string {
  if (!value) {
    return '—';
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export default function DashboardBrowserAgentCard() {
  const { t, lang } = useTranslation();
  const [data, setData] = useState<BrowserAgentRunListResponse | null>(null);
  const [taskPrompt, setTaskPrompt] = useState('');
  const [startUrl, setStartUrl] = useState('');
  const [allowedDomains, setAllowedDomains] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadRuns() {
    const response = await browserAgentApi.listRuns();
    setData(response);
  }

  useEffect(() => {
    let cancelled = false;

    loadRuns()
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    const timer = window.setInterval(() => {
      void loadRuns().catch(() => undefined);
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  async function handleQueueRun() {
    setSubmitting(true);
    setError(null);
    try {
      await browserAgentApi.queueRun({
        task_prompt: taskPrompt,
        start_url: startUrl.trim() || null,
        allowed_domains: allowedDomains
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setTaskPrompt('');
      setStartUrl('');
      setAllowedDomains('');
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.dashboard.browserAgent.errorFallback);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancelRun(runId: string) {
    setError(null);
    try {
      await browserAgentApi.cancelRun(runId);
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : t.dashboard.browserAgent.errorFallback);
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="h-32 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
      </section>
    );
  }

  if (data === null) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-cyan-200 bg-white p-5 shadow-sm dark:border-cyan-900/30 dark:bg-slate-900">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2 min-w-0">
          <div className="inline-flex items-center gap-2 rounded-full bg-cyan-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-300">
            <SquareTerminal size={14} />
            <span>{t.dashboard.browserAgent.badge}</span>
          </div>
          <h3 className="text-lg font-bold text-slate-950 dark:text-white">
            {t.dashboard.browserAgent.title}
          </h3>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-400">
            {t.dashboard.browserAgent.description}
          </p>
        </div>
        <div className="w-fit rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">
          {t.dashboard.browserAgent.runningCount
            .replace('{user}', String(data.current_user_running_count))
            .replace('{global}', String(data.global_running_count))}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.browserAgent.userLimit}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{data.max_concurrent_runs_per_user}</p>
        </div>
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.browserAgent.queueLimit}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{data.current_user_queued_count} / {data.max_queued_runs_per_user}</p>
        </div>
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.browserAgent.globalLimit}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{data.global_running_count} / {data.max_global_running_runs}</p>
        </div>
      </div>

      <div className="mt-4 space-y-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/60">
        <label className="block">
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t.dashboard.browserAgent.taskLabel}</span>
          <textarea
            value={taskPrompt}
            onChange={(event) => setTaskPrompt(event.target.value)}
            rows={4}
            placeholder={t.dashboard.browserAgent.taskPlaceholder}
            className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-cyan-400 dark:focus:ring-cyan-900/40"
          />
        </label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t.dashboard.browserAgent.startUrlLabel}</span>
            <input
              type="url"
              value={startUrl}
              onChange={(event) => setStartUrl(event.target.value)}
              placeholder={t.dashboard.browserAgent.startUrlPlaceholder}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-cyan-400 dark:focus:ring-cyan-900/40"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t.dashboard.browserAgent.allowedDomainsLabel}</span>
            <input
              type="text"
              value={allowedDomains}
              onChange={(event) => setAllowedDomains(event.target.value)}
              placeholder={t.dashboard.browserAgent.allowedDomainsPlaceholder}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-cyan-500 focus:ring-2 focus:ring-cyan-200 dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:focus:border-cyan-400 dark:focus:ring-cyan-900/40"
            />
          </label>
        </div>
        {error ? (
          <p className="text-sm font-medium text-red-700 dark:text-red-300">{error}</p>
        ) : null}
        <button
          type="button"
          onClick={() => void handleQueueRun()}
          disabled={submitting || taskPrompt.trim().length < 10}
          className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-cyan-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {submitting ? <LoaderCircle size={16} className="animate-spin" /> : <PlayCircle size={16} />}
          <span>{submitting ? t.dashboard.browserAgent.queueing : t.dashboard.browserAgent.queueAction}</span>
        </button>
      </div>

      <div className="mt-4 space-y-3">
        {data.items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 px-4 py-5 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
            {t.dashboard.browserAgent.empty}
          </div>
        ) : null}
        {data.items.map((item) => (
          <article key={item.id} className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/40">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="space-y-1 min-w-0">
                <p className="text-sm font-semibold text-slate-950 dark:text-white">{item.task_prompt}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {t.dashboard.browserAgent.queuedAt.replace('{value}', formatTimestamp(item.queued_at, lang))}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {t.dashboard.browserAgent.statusLabel.replace('{value}', item.status)}
                </p>
              </div>
              {item.status === 'queued' || item.status === 'running' || item.status === 'cancelling' ? (
                <button
                  type="button"
                  onClick={() => void handleCancelRun(item.id)}
                  className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-50 dark:border-red-900/40 dark:text-red-300 dark:hover:bg-red-950/30 sm:w-auto"
                >
                  <OctagonX size={14} />
                  <span>{item.status === 'cancelling' ? t.dashboard.browserAgent.stopping : t.dashboard.browserAgent.stopAction}</span>
                </button>
              ) : null}
            </div>
            {item.error_message ? (
              <p className="mt-2 text-sm text-red-700 dark:text-red-300">{item.error_message}</p>
            ) : null}
            {item.final_result_text ? (
              <p className="mt-2 line-clamp-3 text-sm text-slate-600 dark:text-slate-300">{item.final_result_text}</p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
