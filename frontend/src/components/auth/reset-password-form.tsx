'use client';

import { useTranslation } from '@/context/language-context';

export default function ResetPasswordForm() {
  const { t } = useTranslation();

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

      <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
        <input type="password" placeholder={t.auth.reset.title} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900" />
        <input type="password" placeholder={t.auth.signup.confirmPassword} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900" />
        <button className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white shadow-lg shadow-blue-500/25 transition-all active:scale-[0.98] hover:bg-blue-700">
          {t.auth.reset.submit}
        </button>
      </form>

      <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-300">
        {t.auth.reset.success}
      </p>
    </div>
  );
}
