'use client';

import type { LucideIcon } from 'lucide-react';

export default function NotificationChannelCard({
  icon: Icon,
  title,
  description,
  enabled,
  isInput,
  placeholder,
  value,
  onChange,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  enabled: boolean;
  isInput?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          <Icon size={20} />
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-bold text-slate-950 dark:text-white">{title}</h3>
            <span
              className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${
                enabled
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                  : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
              }`}
            >
              {enabled ? 'On' : 'Off'}
            </span>
          </div>
          {isInput ? (
            <input
              type="text"
              placeholder={placeholder}
              value={value}
              onChange={(event) => onChange?.(event.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 outline-none transition-colors focus:border-blue-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
          ) : (
            <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>
          )}
        </div>
      </div>
    </div>
  );
}
