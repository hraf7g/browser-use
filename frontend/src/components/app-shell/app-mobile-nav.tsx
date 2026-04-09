'use client';

import { motion } from 'framer-motion';
import { X } from 'lucide-react';

import AppSidebar from './app-sidebar';

export default function AppMobileNav({ onClose }: { onClose: () => void }) {
  return (
    <>
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-950/40 lg:hidden"
        aria-label="Close navigation"
      />
      <motion.div
        initial={{ x: -320 }}
        animate={{ x: 0 }}
        exit={{ x: -320 }}
        transition={{ type: 'spring', stiffness: 320, damping: 30 }}
        className="fixed inset-y-0 left-0 z-50 w-72 lg:hidden"
      >
        <div className="absolute right-3 top-3 z-10">
          <button
            onClick={onClose}
            className="rounded-full bg-white p-2 text-slate-700 shadow dark:bg-slate-900 dark:text-slate-200"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>
        <AppSidebar className="flex h-full w-full" />
      </motion.div>
    </>
  );
}
