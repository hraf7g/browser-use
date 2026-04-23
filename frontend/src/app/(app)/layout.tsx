'use client';
import { useEffect, useState } from 'react';
import AppSidebar from '@/components/app-shell/app-sidebar';
import AppTopbar from '@/components/app-shell/app-topbar';
import AppMobileNav from '@/components/app-shell/app-mobile-nav';
import AppSessionGuard from '@/components/app-shell/app-session-guard';
import { AuthSessionProvider } from '@/context/auth-session-context';
import { MonitoringSetupProvider } from '@/context/monitoring-setup-context';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    if (!isMobileOpen) {
      document.body.style.removeProperty('overflow');
      return;
    }

    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.removeProperty('overflow');
    };
  }, [isMobileOpen]);

  return (
    <AuthSessionProvider>
      <MonitoringSetupProvider>
        <AppSessionGuard>
          <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
            {/* Desktop Sidebar */}
            <AppSidebar />

            {/* Mobile Sidebar (Drawer) */}
            {isMobileOpen && <AppMobileNav onClose={() => setIsMobileOpen(false)} />}

            {/* Main Container */}
            <div className="flex-1 flex flex-col min-w-0">
              <AppTopbar onMenuClick={() => setIsMobileOpen(true)} />
              <main className="flex-1 overflow-y-auto">
                {children}
              </main>
            </div>
          </div>
        </AppSessionGuard>
      </MonitoringSetupProvider>
    </AuthSessionProvider>
  );
}
