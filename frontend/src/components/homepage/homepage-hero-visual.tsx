'use client';

import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { BellRing, CheckCircle2, Globe2, ScanLine, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';

import { useTranslation } from '@/context/language-context';
import { cn } from '@/lib/utils';

const STAGE_COUNT = 7;
const STAGE_MS = 2200;

type Stage = 0 | 1 | 2 | 3 | 4 | 5 | 6;

const PIPELINE = ['Browse sources', 'Detect tenders', 'Analyze content', 'Match profile', 'Send alert'] as const;

const DOT_COLORS: Record<string, string> = {
  success: 'bg-emerald-500',
  info: 'bg-blue-500',
  warning: 'bg-amber-400',
  neutral: 'bg-slate-400',
};

export default function HomepageHeroVisual() {
  const { t, lang } = useTranslation();
  const prefersReducedMotion = useReducedMotion();
  const [stage, setStage] = useState<Stage>(0);
  const isArabic = lang === 'ar';

  useEffect(() => {
    if (prefersReducedMotion) return;
    const id = window.setInterval(() => setStage((s) => ((s + 1) % STAGE_COUNT) as Stage), STAGE_MS);
    return () => window.clearInterval(id);
  }, [prefersReducedMotion]);

  const sources = t.hero.visual.sources as Array<{ label: string; region: string; url: string }>;
  const steps = t.hero.visual.steps as string[];
  const pipelineSteps = prefersReducedMotion ? PIPELINE : steps;

  const activeSourceIndex = stage <= 1 ? stage % sources.length : stage <= 3 ? 0 : 1;

  const scanFields = [
    t.hero.visual.deadlineField,
    t.hero.visual.buyerField,
    t.hero.visual.categoryField,
    t.hero.visual.valueField,
  ] as string[];

  return (
    <div
      className="relative overflow-hidden rounded-[2rem] border border-slate-200/80 bg-gradient-to-b from-white to-slate-50 shadow-[0_32px_80px_-24px_rgba(15,23,42,0.28)] dark:border-slate-800 dark:from-slate-950 dark:to-slate-900"
      aria-hidden="true"
    >
      {/* Subtle glow overlays */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(37,99,235,0.10),transparent_50%),radial-gradient(circle_at_bottom_left,rgba(16,185,129,0.08),transparent_48%)]" />

      <div className="relative grid gap-3 p-4 xl:grid-cols-[1.15fr_0.85fr]">
        {/* ── LEFT: Browser window ─────────────────────────────── */}
        <div className="flex flex-col gap-3">
          {/* Browser chrome */}
          <div className="overflow-hidden rounded-[1.5rem] border border-slate-200/80 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-950">
            {/* URL bar */}
            <div className="flex items-center gap-2 border-b border-slate-100 bg-slate-50 px-4 py-2.5 dark:border-slate-800 dark:bg-slate-900">
              <div className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
              </div>
              <div className="mx-auto flex h-6 max-w-[220px] flex-1 items-center rounded-md bg-white px-3 text-[11px] text-slate-400 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-500 dark:ring-slate-700">
                <Globe2 size={10} className="mr-1.5 shrink-0 text-slate-400" />
                {sources[activeSourceIndex]?.url ?? 'procurement.gov'}
              </div>
            </div>

            {/* Source cards */}
            <div className="p-4">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500">
                  {t.hero.visual.sourcesEyebrow}
                </p>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700 dark:border-emerald-900/40 dark:bg-emerald-950/30 dark:text-emerald-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {t.hero.visual.monitoring}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {sources.map((src, i) => {
                  const isActive = i === activeSourceIndex && stage >= 1;
                  return (
                    <div
                      key={src.label}
                      className={cn(
                        'rounded-xl border px-3 py-2.5 transition-all duration-500',
                        isActive
                          ? 'border-blue-300 bg-blue-50 shadow-[0_0_0_3px_rgba(59,130,246,0.12)] dark:border-blue-700 dark:bg-blue-950/30'
                          : 'border-slate-200 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-900/80'
                      )}
                    >
                      <p className="text-[11px] font-semibold text-slate-900 dark:text-white">{src.label}</p>
                      <p className="mt-0.5 text-[10px] text-slate-500 dark:text-slate-400">{src.region}</p>
                      <span
                        className={cn(
                          'mt-1.5 inline-block rounded-full px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.15em]',
                          isActive
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-400'
                        )}
                      >
                        {isActive ? (isArabic ? 'مسح' : 'Scanning') : isArabic ? 'في الانتظار' : 'Queued'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tender page scan area */}
            <div className="relative mx-4 mb-4 overflow-hidden rounded-[1.25rem] border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-900/60">
              {/* Animated scan line */}
              {!prefersReducedMotion && stage >= 2 && (
                <motion.div
                  className="pointer-events-none absolute inset-x-0 h-8 bg-gradient-to-b from-blue-400/20 to-transparent"
                  animate={{ y: [0, 70, 140, 0] }}
                  transition={{ duration: 2.2, repeat: Infinity, ease: 'linear' }}
                />
              )}

              <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
                <ScanLine size={12} />
                {t.hero.visual.tenderEyebrow}
              </div>

              <p className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">
                {isArabic ? t.hero.visual.tenderSampleTitleAr : t.hero.visual.tenderSampleTitle}
              </p>

              <div className="grid grid-cols-2 gap-2">
                {scanFields.map((field, i) => {
                  const highlighted = stage >= 2 && i <= Math.min(stage - 2, scanFields.length - 1);
                  return (
                    <div
                      key={field}
                      className={cn(
                        'rounded-lg border px-2.5 py-1.5 text-[11px] transition-all duration-500',
                        highlighted
                          ? 'border-blue-200 bg-white text-blue-700 shadow-sm dark:border-blue-800 dark:bg-blue-950/30 dark:text-blue-300'
                          : 'border-slate-200 bg-white/70 text-slate-500 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-500'
                      )}
                    >
                      <span className="font-semibold">{field}</span>
                      {highlighted && (
                        <span className="ml-1 text-blue-500 dark:text-blue-400">
                          {i === 0 ? t.hero.visual.tenderSampleDeadline : i === 1 ? t.hero.visual.tenderSampleBuyer : i === 2 ? t.hero.visual.tenderSampleCategory : t.hero.visual.valueUnavailable}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Extracted tender card */}
          <AnimatePresence>
            {(stage >= 4 || prefersReducedMotion) && (
              <motion.div
                initial={prefersReducedMotion ? false : { opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 shadow-[0_12px_32px_-16px_rgba(16,185,129,0.35)] dark:border-emerald-900/40 dark:bg-emerald-950/30"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">
                      {isArabic ? 'مناقصة مستخرجة' : 'Tender extracted'}
                    </p>
                    <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                      {isArabic ? t.hero.visual.tenderSampleTitleAr : t.hero.visual.tenderSampleTitle}
                    </p>
                    <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                      {t.hero.visual.tenderSampleBuyer}
                    </p>
                  </div>
                  {/* Match score badge */}
                  <motion.div
                    initial={prefersReducedMotion ? false : { scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2, duration: 0.35 }}
                    className="shrink-0 rounded-full bg-emerald-600 px-3 py-1.5 text-xs font-black text-white shadow-lg shadow-emerald-500/30"
                  >
                    {t.hero.visual.matchScore}
                  </motion.div>
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {(t.hero.visual.matchBadges as string[]).map((b) => (
                    <span
                      key={b}
                      className="rounded-full border border-emerald-300 bg-white px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700 dark:border-emerald-800 dark:bg-slate-900 dark:text-emerald-300"
                    >
                      {b}
                    </span>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* ── RIGHT: Pipeline + Alert ───────────────────────────── */}
        <div className="flex flex-col gap-3">
          {/* Pipeline steps */}
          <div className="rounded-[1.5rem] border border-slate-200/80 bg-white/80 p-4 backdrop-blur dark:border-slate-800/70 dark:bg-slate-950/80">
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400 dark:text-slate-500">
              {t.hero.visual.flowEyebrow}
            </p>
            <div className="space-y-2">
              {pipelineSteps.map((step, i) => {
                const done = i < stage;
                const active = i === stage;
                return (
                  <div
                    key={step}
                    className={cn(
                      'flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-all duration-500',
                      done
                        ? 'border-emerald-200 bg-emerald-50/80 dark:border-emerald-900/40 dark:bg-emerald-950/20'
                        : active
                          ? 'border-blue-200 bg-blue-50/80 dark:border-blue-900/40 dark:bg-blue-950/20'
                          : 'border-slate-100 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-900/40'
                    )}
                  >
                    <div
                      className={cn(
                        'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold',
                        done
                          ? 'bg-emerald-500 text-white'
                          : active
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
                      )}
                    >
                      {done ? <CheckCircle2 size={13} /> : i + 1}
                    </div>
                    <span className="text-xs font-medium text-slate-800 dark:text-slate-200">{step}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Alert panel */}
          <div className="relative flex-1 overflow-hidden rounded-[1.5rem] border border-slate-900 bg-[linear-gradient(150deg,#0f172a,#1e293b)] p-4 text-white">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.18),transparent)]" />
            <p className="relative text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">
              {t.hero.visual.deliveryEyebrow}
            </p>

            <AnimatePresence mode="wait">
              <motion.div
                key={stage >= 5 ? 'alert' : 'brief'}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
                className="relative mt-3 rounded-[1.25rem] border border-white/10 bg-white/5 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <BellRing size={15} className={stage >= 5 ? 'text-emerald-300' : 'text-blue-300'} />
                    <p className="text-sm font-semibold text-white">
                      {stage >= 5 ? t.hero.visual.alertTitle : t.hero.visual.briefTitle}
                    </p>
                  </div>
                  <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-200">
                    {t.hero.visual.ready}
                  </span>
                </div>
                <p className="mt-2 text-[11px] leading-5 text-slate-300">
                  {stage >= 5 ? t.hero.visual.alertDescription : t.hero.visual.briefDescription}
                </p>

                {/* Alert pulse ring */}
                {stage >= 5 && !prefersReducedMotion && (
                  <motion.div
                    className="absolute -right-1 -top-1 h-4 w-4"
                    animate={{ scale: [1, 1.6, 1], opacity: [1, 0, 1] }}
                    transition={{ duration: 1.4, repeat: Infinity }}
                  >
                    <span className="block h-full w-full rounded-full bg-emerald-500/40" />
                  </motion.div>
                )}
              </motion.div>
            </AnimatePresence>

            {/* Sparkling AI cursor indicator */}
            {!prefersReducedMotion && (
              <motion.div
                className="pointer-events-none absolute bottom-4 right-4 flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 shadow-[0_0_0_6px_rgba(59,130,246,0.15)]"
                animate={{ scale: [1, 1.08, 1] }}
                transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
              >
                <Sparkles size={12} className="text-white" />
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
