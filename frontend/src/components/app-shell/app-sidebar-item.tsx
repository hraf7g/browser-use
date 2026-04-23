'use client';

import Link from 'next/link';
import type { LucideIcon } from 'lucide-react';

type AppSidebarItemProps = {
  icon: LucideIcon;
  label: string;
  href: string;
  isActive?: boolean;
  onNavigate?: () => void;
};

export default function AppSidebarItem({
  icon: Icon,
  label,
  href,
  isActive = false,
  onNavigate,
}: AppSidebarItemProps) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={`flex min-h-11 w-full items-center rounded-xl px-4 py-3 text-sm font-medium transition-colors ${
        isActive
          ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
          : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-900'
      }`}
    >
      <Icon size={18} className="shrink-0" />
      <span className="ms-3">{label}</span>
    </Link>
  );
}
