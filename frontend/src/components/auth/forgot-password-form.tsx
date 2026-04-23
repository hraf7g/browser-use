'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslation } from '@/context/language-context';
import { authSession } from '@/lib/auth-session';

export default function ForgotPasswordForm() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [deliveryChannel, setDeliveryChannel] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await authSession.requestPasswordReset(email.trim());
      setSuccessMessage(response.message);
      setDeliveryChannel(response.delivery_channel);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t.auth.forgot.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="mb-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {t.auth.forgot.title}
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          {t.auth.forgot.subtitle}
        </p>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <input
          autoComplete="email"
          required
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
          placeholder={t.auth.login.emailPlaceholder}
        />
        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
            {error}
          </div>
        ) : null}
        {successMessage ? (
          <div className="space-y-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-200">
            <p>{successMessage}</p>
            {deliveryChannel === 'dev_outbox' ? <p>{t.auth.forgot.devHint}</p> : null}
          </div>
        ) : null}
        <button
          disabled={loading}
          className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? t.auth.forgot.loading : t.auth.forgot.submit}
        </button>
      </form>

      <Link href="/login" className="inline-flex text-sm font-bold text-blue-600 hover:underline">
        {t.auth.forgot.back}
      </Link>
    </div>
  );
}
