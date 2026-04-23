'use client';

import { useEffect, useState } from 'react';
import { Ban, Gauge, PauseCircle, PlayCircle, ShieldAlert } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import {
  operatorAiControlApi,
  type OperatorAIControlState,
} from '@/lib/operator-ai-control';

export default function DashboardAIControlCard() {
  const { t, lang } = useTranslation();
  const [control, setControl] = useState<OperatorAIControlState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reasonDraft, setReasonDraft] = useState('');
  const [requestBudgetDraft, setRequestBudgetDraft] = useState('');
  const [reservedTokenBudgetDraft, setReservedTokenBudgetDraft] = useState('');

  useEffect(() => {
    let cancelled = false;

    operatorAiControlApi
      .getState()
      .then((response) => {
        if (cancelled) {
          return;
        }
        setControl(response);
        setReasonDraft(response.emergency_stop_reason ?? '');
        setRequestBudgetDraft(String(response.max_daily_requests_override ?? ''));
        setReservedTokenBudgetDraft(String(response.max_daily_reserved_tokens_override ?? ''));
      })
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

    return () => {
      cancelled = true;
    };
  }, []);

  async function updateControl(next: OperatorAIControlState, overrides: Partial<OperatorAIControlState>) {
    setSaving(true);
    setError(null);
    try {
      const response = await operatorAiControlApi.updateState({
        ai_enrichment_enabled: overrides.ai_enrichment_enabled ?? next.ai_enrichment_enabled,
        emergency_stop_enabled: overrides.emergency_stop_enabled ?? next.emergency_stop_enabled,
        emergency_stop_reason:
          overrides.emergency_stop_reason ?? next.emergency_stop_reason ?? null,
        max_enrichment_batch_size_override:
          overrides.max_enrichment_batch_size_override ??
          next.max_enrichment_batch_size_override,
      });
      setControl(response);
      setReasonDraft(response.emergency_stop_reason ?? '');
      setRequestBudgetDraft(String(response.max_daily_requests_override ?? ''));
      setReservedTokenBudgetDraft(String(response.max_daily_reserved_tokens_override ?? ''));
    } catch (err) {
      setError(err instanceof Error ? err.message : t.dashboard.aiControl.errorFallback);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="h-32 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800" />
      </section>
    );
  }

  if (error && control === null) {
    return (
      <section className="rounded-2xl border border-red-200 bg-red-50 p-5 shadow-sm dark:border-red-900/30 dark:bg-red-950/20">
        <p className="text-sm font-semibold text-red-700 dark:text-red-300">
          {error}
        </p>
      </section>
    );
  }

  if (control === null) {
    return null;
  }

  const effectiveStatus = control.emergency_stop_enabled
    ? t.dashboard.aiControl.status.emergencyStopped
    : control.effective_ai_enrichment_enabled
      ? t.dashboard.aiControl.status.active
      : t.dashboard.aiControl.status.paused;

  const updatedAtLabel = new Intl.DateTimeFormat(lang, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(control.updated_at));
  const usageDateLabel = new Intl.DateTimeFormat(lang, {
    dateStyle: 'medium',
  }).format(new Date(`${control.today_usage_date}T00:00:00Z`));
  const requestBudgetLabel = control.effective_daily_request_budget ?? t.dashboard.aiControl.unlimited;
  const reservedBudgetLabel = control.effective_daily_reserved_token_budget ?? t.dashboard.aiControl.unlimited;

  function parseOptionalInteger(value: string): number | null {
    const trimmed = value.trim();
    if (!trimmed) {
      return null;
    }
    const parsed = Number.parseInt(trimmed, 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }

  return (
    <section className="rounded-2xl border border-amber-200 bg-white p-5 shadow-sm dark:border-amber-900/30 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-amber-700 dark:bg-amber-950/30 dark:text-amber-300">
            <ShieldAlert size={14} />
            <span>{t.dashboard.aiControl.badge}</span>
          </div>
          <h3 className="text-lg font-bold text-slate-950 dark:text-white">
            {t.dashboard.aiControl.title}
          </h3>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-400">
            {t.dashboard.aiControl.description}
          </p>
        </div>
        <div className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">
          {effectiveStatus}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.provider}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{control.effective_ai_provider}</p>
        </div>
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.batchSize}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{control.effective_enrichment_batch_size}</p>
        </div>
        <div className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-950/60">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.lastUpdated}</p>
          <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{updatedAtLabel}</p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-950/60">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
          <Gauge size={16} />
          <span>{t.dashboard.aiControl.budgetTitle}</span>
        </div>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {t.dashboard.aiControl.budgetDescription.replace('{date}', usageDateLabel)}
        </p>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-white px-3 py-2 dark:bg-slate-900">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.requestBudget}</p>
            <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{requestBudgetLabel}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {t.dashboard.aiControl.usedLabel.replace('{value}', String(control.today_request_count))}
            </p>
          </div>
          <div className="rounded-xl bg-white px-3 py-2 dark:bg-slate-900">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.tokenBudget}</p>
            <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{reservedBudgetLabel}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {t.dashboard.aiControl.usedLabel.replace('{value}', String(control.today_reserved_total_tokens))}
            </p>
          </div>
          <div className="rounded-xl bg-white px-3 py-2 dark:bg-slate-900">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.actualTokens}</p>
            <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{control.today_actual_total_tokens}</p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {t.dashboard.aiControl.promptCompletion
                .replace('{prompt}', String(control.today_actual_prompt_tokens))
                .replace('{completion}', String(control.today_actual_completion_tokens))}
            </p>
          </div>
          <div className="rounded-xl bg-white px-3 py-2 dark:bg-slate-900">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{t.dashboard.aiControl.failures}</p>
            <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
              {control.today_throttled_request_count + control.today_provider_error_count}
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              {t.dashboard.aiControl.failureBreakdown
                .replace('{throttled}', String(control.today_throttled_request_count))
                .replace('{provider}', String(control.today_provider_error_count))
                .replace('{blocked}', String(control.today_blocked_request_count))}
            </p>
          </div>
        </div>

        {control.budget_exhausted ? (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
            <span className="font-semibold">{t.dashboard.aiControl.budgetExhausted}:</span>{' '}
            {control.budget_exhausted_reason ?? t.dashboard.aiControl.budgetExhaustedFallback}
          </div>
        ) : null}

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {t.dashboard.aiControl.requestBudgetOverride}
            </span>
            <input
              type="number"
              min={1}
              inputMode="numeric"
              value={requestBudgetDraft}
              onChange={(event) => setRequestBudgetDraft(event.target.value)}
              disabled={saving}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-colors focus:border-amber-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
              placeholder={t.dashboard.aiControl.overridePlaceholder}
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
              {t.dashboard.aiControl.tokenBudgetOverride}
            </span>
            <input
              type="number"
              min={1}
              inputMode="numeric"
              value={reservedTokenBudgetDraft}
              onChange={(event) => setReservedTokenBudgetDraft(event.target.value)}
              disabled={saving}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-colors focus:border-amber-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
              placeholder={t.dashboard.aiControl.overridePlaceholder}
            />
          </label>
        </div>
      </div>

      <label className="mt-4 block">
        <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
          {t.dashboard.aiControl.reasonLabel}
        </span>
        <textarea
          value={reasonDraft}
          onChange={(event) => setReasonDraft(event.target.value)}
          rows={3}
          disabled={saving}
          className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-colors focus:border-amber-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          placeholder={t.dashboard.aiControl.reasonPlaceholder}
        />
      </label>

      {control.emergency_stop_reason ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
          <span className="font-semibold">{t.dashboard.aiControl.currentReason}:</span>{' '}
          {control.emergency_stop_reason}
        </div>
      ) : null}

      {error ? (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
          {error}
        </div>
      ) : null}

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          disabled={saving || control.emergency_stop_enabled}
          onClick={() =>
            updateControl(control, {
              emergency_stop_enabled: true,
              emergency_stop_reason: reasonDraft.trim() || t.dashboard.aiControl.defaultEmergencyReason,
              max_daily_requests_override: parseOptionalInteger(requestBudgetDraft),
              max_daily_reserved_tokens_override: parseOptionalInteger(reservedTokenBudgetDraft),
            })
          }
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Ban size={16} />
          {t.dashboard.aiControl.actions.emergencyStop}
        </button>
        <button
          type="button"
          disabled={saving || !control.emergency_stop_enabled}
          onClick={() =>
            updateControl(control, {
              emergency_stop_enabled: false,
              emergency_stop_reason: null,
              max_daily_requests_override: parseOptionalInteger(requestBudgetDraft),
              max_daily_reserved_tokens_override: parseOptionalInteger(reservedTokenBudgetDraft),
            })
          }
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
        >
          <PlayCircle size={16} />
          {t.dashboard.aiControl.actions.resume}
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={() =>
            updateControl(control, {
              ai_enrichment_enabled: !control.ai_enrichment_enabled,
              max_daily_requests_override: parseOptionalInteger(requestBudgetDraft),
              max_daily_reserved_tokens_override: parseOptionalInteger(reservedTokenBudgetDraft),
            })
          }
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800 transition-colors hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-amber-900/30 dark:bg-amber-950/20 dark:text-amber-200 dark:hover:bg-amber-950/30"
        >
          <PauseCircle size={16} />
          {control.ai_enrichment_enabled
            ? t.dashboard.aiControl.actions.pauseEnrichment
            : t.dashboard.aiControl.actions.enableEnrichment}
        </button>
      </div>
    </section>
  );
}
