'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/context/language-context';
import { navigationItems } from '@/lib/nav-config';
import AppSidebarItem from './app-sidebar-item';
import { LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthSession } from '@/context/auth-session-context';

export default function AppSidebar({ className }: { className?: string }) {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const { user, signOut } = useAuthSession();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  async function handleLogout() {
    setIsSigningOut(true);
    setLogoutError(null);

    try {
      await signOut();
      router.replace('/login');
      router.refresh();
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : 'Logout failed');
    } finally {
      setIsSigningOut(false);
    }
  }

  return (
    <aside className={cn(
      "hidden lg:flex flex-col w-64 border-e border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 transition-all duration-300",
      className
    )}>
      {/* Brand Logo Area */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200 dark:border-slate-800">
        <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center text-white font-bold text-sm">TW</div>
        <span className="ms-3 font-bold tracking-tight text-slate-900 dark:text-white">TenderWatch</span>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-6 px-4 space-y-1">
        {navigationItems.map((item) => (
          <AppSidebarItem 
            key={item.id}
            icon={item.icon}
            label={t.app.nav[item.id as keyof typeof t.app.nav]}
            isActive={item.id === 'dashboard'} // Mock active state
          />
        ))}
      </nav>

      {/* Bottom Actions */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <div className="mb-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900/60">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            {t.app.session.signedInAs}
          </p>
          <p className="mt-1 truncate text-sm font-semibold text-slate-900 dark:text-white">
            {user?.email ?? t.app.nav.account}
          </p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          disabled={isSigningOut}
          className="flex items-center w-full px-4 py-2.5 text-sm font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-lg transition-colors group disabled:cursor-not-allowed disabled:opacity-60"
        >
          <LogOut size={18} className={cn("shrink-0", lang === 'ar' && "rotate-180")} />
          <span className="ms-3">{isSigningOut ? 'Signing out...' : t.app.nav.logout}</span>
        </button>
        {logoutError && (
          <p className="mt-2 text-xs font-medium text-red-600 dark:text-red-400">
            {logoutError}
          </p>
        )}
      </div>
    </aside>
  );
}
