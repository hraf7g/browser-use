'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { usePathname } from 'next/navigation';
import { useTranslation } from '@/context/language-context';
import { navigationItems } from '@/lib/nav-config';
import AppSidebarItem from './app-sidebar-item';
import { LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthSession } from '@/context/auth-session-context';
import { LanguageToggle } from '../ui/language-toggle';
import { ThemeToggle } from '../ui/theme-toggle';

export default function AppSidebar({
  className,
  onNavigate,
  mobile = false,
}: {
  className?: string;
  onNavigate?: () => void;
  mobile?: boolean;
}) {
  const { t, lang } = useTranslation();
  const router = useRouter();
  const pathname = usePathname();
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
      mobile
        ? "flex h-full w-full flex-col bg-white dark:bg-slate-950"
        : "hidden w-64 flex-col border-e border-slate-200 bg-white transition-all duration-300 dark:border-slate-800 dark:bg-slate-950 lg:flex",
      className
    )}>
      {/* Brand Logo Area */}
      <div className="flex h-16 items-center border-b border-slate-200 px-5 dark:border-slate-800 sm:px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-blue-600 text-sm font-bold text-white">TW</div>
        <span className="ms-3 font-bold tracking-tight text-slate-900 dark:text-white">TenderWatch</span>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4 sm:px-4 sm:py-6">
        {navigationItems.map((item) => (
          <AppSidebarItem 
            key={item.id}
            icon={item.icon}
            label={t.app.nav[item.id as keyof typeof t.app.nav]}
            href={item.path}
            isActive={pathname === item.path || pathname.startsWith(`${item.path}/`)}
            onNavigate={onNavigate}
          />
        ))}
      </nav>

      {/* Bottom Actions */}
      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
        {mobile ? (
          <div className="mb-3 flex flex-col gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center gap-2">
              <LanguageToggle />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                Theme
              </span>
              <ThemeToggle />
            </div>
          </div>
        ) : null}
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
          className="flex w-full items-center rounded-lg px-4 py-3 text-sm font-medium text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/20 disabled:cursor-not-allowed disabled:opacity-60"
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
