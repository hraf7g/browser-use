'use client';

import { useState } from 'react';
import { useTranslation } from '@/context/language-context';
import Link from 'next/link';
import { Eye, EyeOff } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { authSession, readSafeRedirectPathFromLocation } from '@/lib/auth-session';

export default function LoginForm() {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await authSession.login({ email, password });
      router.push(readSafeRedirectPathFromLocation());
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 rounded-[30px] border border-slate-200 bg-white/95 p-8 shadow-xl shadow-slate-200/50 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90 dark:shadow-none sm:p-10">
      <div className="space-y-3">
        <p className={`text-sm font-bold text-blue-600 ${lang === 'ar' ? 'tracking-normal' : 'uppercase tracking-[0.24em]'}`}>
          {t.auth.login.eyebrow}
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {t.auth.login.title}
        </h1>
        <p className={`text-slate-500 dark:text-slate-400 ${lang === 'ar' ? 'leading-8' : 'leading-7'}`}>
          {t.auth.login.subtitle}
        </p>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit} noValidate>
        <div className="space-y-2">
          <label htmlFor="login-email" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {t.auth.login.emailLabel}
          </label>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder={t.auth.login.emailPlaceholder}
            aria-invalid={error ? 'true' : 'false'}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-4">
            <label htmlFor="login-password" className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              {t.auth.login.passwordLabel}
            </label>
            <Link href="/forgot-password" className="text-sm font-semibold text-blue-600 transition-colors hover:text-blue-700">
              {t.auth.login.forgotPassword}
            </Link>
          </div>
          <div className="relative">
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              aria-invalid={error ? 'true' : 'false'}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className={`absolute top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 ${lang === 'ar' ? 'left-4' : 'right-4'}`}
              aria-label={showPassword ? t.auth.login.hidePassword : t.auth.login.showPassword}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-300">
            {error}
          </div>
        ) : null}

        <button
          disabled={loading}
          className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] hover:bg-blue-700 disabled:opacity-60"
        >
          {loading ? t.auth.login.loading : t.auth.login.submit}
        </button>
      </form>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
        {t.auth.login.help}
      </div>

      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        {t.auth.login.noAccount}{' '}
        <Link href="/signup" className="font-bold text-blue-600 hover:underline">
          {t.auth.login.signUpLink}
        </Link>
      </p>
    </div>
  );
}
