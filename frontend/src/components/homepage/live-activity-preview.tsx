'use client';

import { motion, useReducedMotion } from 'framer-motion';
import { Activity, AlertTriangle, Bell, CheckCircle2, MinusCircle, RefreshCw, Search, XCircle } from 'lucide-react';
import { useState } from 'react';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

const TYPE_CONFIG = {
  success: { Icon: CheckCircle2, dot: 'bg-emerald-500', ring: 'border-emerald-200 dark:border-emerald-900/40', bg: 'bg-emerald-50 dark:bg-emerald-950/20' },
  info:    { Icon: Search,       dot: 'bg-blue-500',    ring: 'border-blue-200 dark:border-blue-900/40',    bg: 'bg-blue-50 dark:bg-blue-950/20'    },
  warning: { Icon: AlertTriangle, dot: 'bg-amber-400',  ring: 'border-amber-200 dark:border-amber-900/40',  bg: 'bg-amber-50 dark:bg-amber-950/20'  },
  neutral: { Icon: MinusCircle,  dot: 'bg-slate-400',   ring: 'border-slate-200 dark:border-slate-800',     bg: 'bg-slate-50 dark:bg-slate-900/60'  },
} as const;

type EventType = keyof typeof TYPE_CONFIG;

export default function LiveActivityPreview() {
  const { t, lang } = useTranslation();
  const prefersReducedMotion = useReducedMotion();
  const isArabic = lang === 'ar';
  const items = t.homepageActivity.items as Array<{ title: string; summary: string; type?: string }>;
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <section className="bg-slate-50 py-24 dark:bg-slate-900">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">

          {/* ── Copy ─────────────────────────────────────────── */}
          <div className="lg:sticky lg:top-28">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
              <Activity size={15} className="text-blue-600" />
              {t.homepageActivity.badge}
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white md:text-4xl">
              {t.homepageActivity.title}
            </h2>
            <p className={`mt-4 max-w-lg text-lg text-slate-600 dark:text-slate-400 ${isArabic ? 'leading-9' : 'leading-8'}`}>
              {t.homepageActivity.description}
            </p>

            {/* Legend */}
            <div className="mt-8 grid grid-cols-2 gap-3">
              {Object.entries(TYPE_CONFIG).map(([key, cfg]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
                  <span className="text-xs font-medium capitalize text-slate-600 dark:text-slate-400">{key}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Feed ─────────────────────────────────────────── */}
          <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">
                {t.homepageActivity.panelEyebrow}
              </p>
              <span className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/30 dark:text-emerald-300">
                <span className="relative flex h-2 w-2">
                  {!prefersReducedMotion && (
                    <motion.span
                      className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"
                      animate={{ scale: [1, 1.8, 1], opacity: [0.75, 0, 0.75] }}
                      transition={{ duration: 1.6, repeat: Infinity }}
                    />
                  )}
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                {t.homepageActivity.liveLabel}
              </span>
            </div>

            {/* Event list */}
            <div className="space-y-2">
              {items.map((item, index) => {
                const type = (item.type ?? 'neutral') as EventType;
                const cfg = TYPE_CONFIG[type] ?? TYPE_CONFIG.neutral;
                const isActive = activeIndex === index;

                return (
                  <button
                    key={item.title}
                    type="button"
                    onClick={() => setActiveIndex(index)}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      'w-full rounded-[1.25rem] border p-4 text-start transition-all',
                      isActive
                        ? `${cfg.ring} ${cfg.bg}`
                        : 'border-slate-100 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-900/60'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <span className={cn('mt-0.5 h-2 w-2 shrink-0 rounded-full', cfg.dot)} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-slate-950 dark:text-white">{item.title}</p>
                        {isActive && (
                          <motion.p
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
                            className={`mt-1 text-xs text-slate-600 dark:text-slate-400 ${isArabic ? 'leading-7' : 'leading-6'}`}
                          >
                            {item.summary}
                          </motion.p>
                        )}
                      </div>
                      <cfg.Icon size={14} className="mt-0.5 shrink-0 text-slate-400" />
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Footer badges */}
            <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
              {(t.homepageActivity.detailBadges as string[]).map((b) => (
                <span key={b} className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
                  {b}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
