'use client';
import { useState } from 'react';
import AppSidebar from '@/components/app-shell/app-sidebar';
import AppTopbar from '@/components/app-shell/app-topbar';
import AppMobileNav from '@/components/app-shell/app-mobile-nav';
import AppSessionGuard from '@/components/app-shell/app-session-guard';
import { AuthSessionProvider } from '@/context/auth-session-context';
import { AnimatePresence } from 'framer-motion';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <AuthSessionProvider>
      <AppSessionGuard>
        <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
          {/* Desktop Sidebar */}
          <AppSidebar />

          {/* Mobile Sidebar (Drawer) */}
          <AnimatePresence>
            {isMobileOpen && (
              <AppMobileNav onClose={() => setIsMobileOpen(false)} />
            )}
          </AnimatePresence>

          {/* Main Container */}
          <div className="flex-1 flex flex-col min-w-0">
            <AppTopbar onMenuClick={() => setIsMobileOpen(true)} />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </div>
      </AppSessionGuard>
    </AuthSessionProvider>
  );
}
