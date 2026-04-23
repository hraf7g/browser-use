'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslation } from '@/context/language-context';
import { useRouter } from 'next/navigation';
import { authSession, readSafeRedirectPathFromLocation } from '@/lib/auth-session';

export default function SignupForm() {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(t.auth.reset.passwordMismatch);
      return;
    }

    setLoading(true);

    try {
      await authSession.signup({ email: email.trim(), password });
      router.push(readSafeRedirectPathFromLocation());
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 rounded-[30px] border border-slate-200 bg-white/95 p-8 shadow-xl shadow-slate-200/50 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90 dark:shadow-none sm:p-10">
      <div className="space-y-3">
        <p className={`text-sm font-bold text-blue-600 ${lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.24em]'}`}>
          {t.auth.signup.eyebrow}
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {t.auth.signup.title}
        </h1>
        <p className={`text-slate-500 dark:text-slate-400 ${lang === 'ar' ? 'leading-8' : 'leading-7'}`}>
          {t.auth.signup.subtitle}
        </p>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <div className="space-y-2">
          <label htmlFor="signup-email" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {t.auth.signup.emailLabel}
          </label>
          <input
            id="signup-email"
            autoComplete="email"
            required
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
            placeholder={t.auth.signup.workEmail}
            aria-invalid={error ? 'true' : 'false'}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-password" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {t.auth.signup.passwordLabel}
          </label>
          <input
            id="signup-password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
            placeholder={t.auth.signup.password}
            aria-invalid={error ? 'true' : 'false'}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="signup-confirm-password" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {t.auth.signup.confirmPasswordLabel}
          </label>
          <input
            id="signup-confirm-password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            type="password"
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
            placeholder={t.auth.signup.confirmPassword}
            aria-invalid={error ? 'true' : 'false'}
          />
        </div>

        <p className="text-sm text-slate-500 dark:text-slate-400">
          {t.auth.signup.passwordHint}
        </p>

        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
            {error}
          </div>
        ) : null}

        <button
          disabled={loading}
          className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? t.auth.signup.loading : t.auth.signup.submit}
        </button>
      </form>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
        {t.auth.signup.terms}
      </div>

      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        {t.auth.signup.hasAccount}{' '}
        <Link href="/login" className="font-bold text-blue-600 hover:underline">
          {t.auth.signup.loginLink}
        </Link>
      </p>
    </div>
  );
}
