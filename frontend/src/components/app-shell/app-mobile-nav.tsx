'use client';

import { motion } from 'framer-motion';
import { X } from 'lucide-react';

import AppSidebar from './app-sidebar';

export default function AppMobileNav({ onClose }: { onClose: () => void }) {
  return (
    <>
      <button
        type="button"
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-950/50 backdrop-blur-[1px] lg:hidden"
        aria-label="Close navigation"
      />
      <motion.div
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="fixed inset-y-0 left-0 z-50 w-[min(86vw,22rem)] lg:hidden"
      >
        <div className="absolute right-3 top-3 z-10">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full bg-white p-2 text-slate-700 shadow dark:bg-slate-900 dark:text-slate-200"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>
        <div className="h-full overflow-hidden rounded-r-3xl border-e border-slate-200 shadow-2xl dark:border-slate-800">
          <AppSidebar className="h-full w-full" onNavigate={onClose} mobile />
        </div>
      </motion.div>
    </>
  );
}
