'use client';

import type { LucideIcon } from 'lucide-react';
import Link from 'next/link';

type GuidancePoint = {
  icon: LucideIcon;
  title: string;
  description: string;
};

export default function MonitoringGuidancePanel({
  badge,
  title,
  description,
  points,
  primaryLabel,
  onPrimaryAction,
  secondaryLabel,
  secondaryHref,
  className = '',
}: {
  badge?: string;
  title: string;
  description: string;
  points: GuidancePoint[];
  primaryLabel: string;
  onPrimaryAction: () => void;
  secondaryLabel?: string;
  secondaryHref?: string;
  className?: string;
}) {
  return (
    <section className={`overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 ${className}`}>
      <div className="border-b border-slate-100 bg-[linear-gradient(135deg,rgba(59,130,246,0.08),transparent_55%)] px-6 py-6 dark:border-slate-800 dark:bg-[linear-gradient(135deg,rgba(59,130,246,0.12),transparent_55%)] lg:px-8">
        {badge ? (
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
            {badge}
          </p>
        ) : null}
        <div className="mt-2 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-2">
            <h2 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
              {title}
            </h2>
            <p className="text-sm leading-7 text-slate-600 dark:text-slate-400">
              {description}
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={onPrimaryAction}
              className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              {primaryLabel}
            </button>
            {secondaryLabel && secondaryHref ? (
              <Link
                href={secondaryHref}
                className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
              >
                {secondaryLabel}
              </Link>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-4 px-6 py-6 lg:grid-cols-3 lg:px-8">
        {points.map((point) => {
          const Icon = point.icon;

          return (
            <div
              key={point.title}
              className="rounded-2xl border border-slate-100 bg-slate-50/70 p-5 dark:border-slate-800 dark:bg-slate-950/50"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-blue-600 shadow-sm dark:bg-slate-900">
                <Icon size={20} />
              </div>
              <h3 className="mt-4 text-sm font-semibold text-slate-950 dark:text-white">
                {point.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
                {point.description}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
