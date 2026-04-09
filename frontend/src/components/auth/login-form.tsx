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
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 tracking-tight">
          {t.auth.login.title}
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          {t.auth.login.subtitle}
        </p>
      </div>

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
            {t.auth.login.emailLabel}
          </label>
          <input 
            type="email" 
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="name@company.com"
            className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              {t.auth.login.passwordLabel}
            </label>
            <Link href="/forgot-password" size="sm" className="text-xs font-bold text-blue-600 hover:text-blue-700">
              {t.auth.login.forgotPassword}
            </Link>
          </div>
          <div className="relative">
            <input 
              type={showPassword ? "text" : "password"} 
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all"
            />
            <button 
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className={`absolute top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 ${lang === 'ar' ? 'left-4' : 'right-4'}`}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {error && <div className="text-sm font-medium text-red-600 dark:text-red-400">{error}</div>}

        <button disabled={loading} className="w-full py-4 bg-blue-600 disabled:opacity-60 hover:bg-blue-700 text-white rounded-xl font-bold text-lg shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98]">
          {t.auth.login.submit}
        </button>
      </form>

      <p className="text-center text-sm text-slate-600 dark:text-slate-400">
        {t.auth.login.noAccount}{' '}
        <Link href="/signup" className="text-blue-600 font-bold hover:underline">
          {t.auth.login.signUpLink}
        </Link>
      </p>
    </div>
  );
}
