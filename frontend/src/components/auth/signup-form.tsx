'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslation } from '@/context/language-context';
import { useRouter } from 'next/navigation';
import { authSession, readSafeRedirectPathFromLocation } from '@/lib/auth-session';

export default function SignupForm() {
  const { t } = useTranslation();
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [workEmail, setWorkEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      await authSession.signup({ email: workEmail, password });
      router.push(readSafeRedirectPathFromLocation());
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="mb-2 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          {t.auth.signup.title}
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          {t.auth.signup.subtitle}
        </p>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <input value={fullName} onChange={(event) => setFullName(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900" placeholder={t.auth.signup.fullName} />
        <input value={workEmail} onChange={(event) => setWorkEmail(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900" placeholder={t.auth.signup.workEmail} />
        <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900" placeholder={t.auth.signup.password} />
        <input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} type="password" className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900" placeholder={t.auth.signup.confirmPassword} />
        {error && <div className="text-sm font-medium text-red-600 dark:text-red-400">{error}</div>}
        <button disabled={loading} className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] hover:bg-blue-700 disabled:opacity-60">
          {t.auth.signup.submit}
        </button>
      </form>

      <p className="text-sm text-slate-500 dark:text-slate-400">{t.auth.signup.terms}</p>
      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        {t.auth.signup.hasAccount}{' '}
        <Link href="/login" className="font-bold text-blue-600 hover:underline">
          {t.auth.signup.loginLink}
        </Link>
      </p>
    </div>
  );
}
