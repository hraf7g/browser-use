'use client';

import type { LucideIcon } from 'lucide-react';

type AppSidebarItemProps = {
  icon: LucideIcon;
  label: string;
  isActive?: boolean;
};

export default function AppSidebarItem({
  icon: Icon,
  label,
  isActive = false,
}: AppSidebarItemProps) {
  return (
    <button
      className={`flex w-full items-center rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
        isActive
          ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
          : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900'
      }`}
    >
      <Icon size={18} className="shrink-0" />
      <span className="ms-3">{label}</span>
    </button>
  );
}
