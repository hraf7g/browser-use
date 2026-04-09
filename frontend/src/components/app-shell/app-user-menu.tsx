'use client';

import { ChevronDown, UserCircle2 } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import { useAuthSession } from '@/context/auth-session-context';

export default function AppUserMenu() {
  const { t } = useTranslation();
  const { user } = useAuthSession();

  return (
    <button className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200 dark:hover:bg-slate-900">
      <UserCircle2 size={22} />
      <span className="hidden sm:inline max-w-40 truncate font-medium">
        {user?.email ?? t.app.nav.account}
      </span>
      <ChevronDown size={16} />
    </button>
  );
}
