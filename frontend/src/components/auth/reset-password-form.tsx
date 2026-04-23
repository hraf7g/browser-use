'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/context/language-context';
import { authSession } from '@/lib/auth-session';

export default function ResetPasswordForm({ token }: { token?: string }) {
  const { t } = useTranslation();
  const router = useRouter();
  const normalizedToken = token?.trim() ?? '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!normalizedToken) {
      setError(t.auth.reset.missingToken);
      return;
    }

    if (password !== confirmPassword) {
      setError(t.auth.reset.passwordMismatch);
      return;
    }

    setLoading(true);

    try {
      const response = await authSession.resetPassword({
        token: normalizedToken,
        password,
      });
      setSuccessMessage(response.message);
      setPassword('');
      setConfirmPassword('');
      router.refresh();
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t.auth.reset.error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="mb-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {t.auth.reset.title}
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          {t.auth.reset.subtitle}
        </p>
      </div>

      {!normalizedToken ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
          {t.auth.reset.missingToken}
        </div>
      ) : (
        <form className="space-y-5" onSubmit={handleSubmit}>
          <input
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
            placeholder={t.auth.signup.password}
          />
          <input
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
            placeholder={t.auth.signup.confirmPassword}
          />
          {error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-300">
              {error}
            </div>
          ) : null}
          {successMessage ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-sm text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-200">
              {successMessage}
            </div>
          ) : null}
          <button
            disabled={loading}
            className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? t.auth.reset.loading : t.auth.reset.submit}
          </button>
        </form>
      )}

      <Link href="/login" className="inline-flex text-sm font-bold text-blue-600 hover:underline">
        {t.auth.forgot.back}
      </Link>
    </div>
  );
}
