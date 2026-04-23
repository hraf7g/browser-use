'use client';

import { motion, useReducedMotion } from 'framer-motion';
import {
  Activity,
  Bell,
  Clock,
  LayoutDashboard,
  Radar,
  SearchCheck,
  Target,
  Zap,
} from 'lucide-react';

import { useTranslation } from '@/context/language-context';

const ICON_MAP: Record<string, React.ElementType> = { Clock, Target, Zap };

const SURFACE_ICONS = [LayoutDashboard, SearchCheck, Bell, Radar, Activity] as const;

export default function ProductPreview() {
  const { t, lang } = useTranslation();
  const prefersReducedMotion = useReducedMotion();
  const isArabic = lang === 'ar';
  const whyItems = t.homepageWhyTeams.items as Array<{ icon: string; title: string; desc: string }>;

  return (
    <>
      {/* ── Section 1: Why teams use it ───────────────────── */}
      <section className="bg-white py-24 dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto mb-14 max-w-2xl text-center">
            <p className={`mb-3 text-sm font-bold text-blue-600 dark:text-blue-400 ${isArabic ? 'tracking-normal' : 'uppercase tracking-[0.26em]'}`}>
              {t.homepageWhyTeams.eyebrow}
            </p>
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white md:text-4xl">
              {t.homepageWhyTeams.title}
            </h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {whyItems.map((item, i) => {
              const Icon = ICON_MAP[item.icon] ?? Clock;
              const accents = [
                'border-blue-200 bg-blue-50 text-blue-600 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300',
                'border-violet-200 bg-violet-50 text-violet-600 dark:border-violet-900/40 dark:bg-violet-950/30 dark:text-violet-300',
                'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-900/40 dark:bg-emerald-950/30 dark:text-emerald-300',
              ];
              return (
                <div
                  key={item.title}
                  className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-7 transition-all hover:-translate-y-1 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/60"
                >
                  <div className={`mb-5 inline-flex h-12 w-12 items-center justify-center rounded-2xl border ${accents[i % 3]}`}>
                    <Icon size={22} />
                  </div>
                  <h3 className="text-lg font-bold tracking-tight text-slate-950 dark:text-white">{item.title}</h3>
                  <p className={`mt-3 text-sm text-slate-600 dark:text-slate-400 ${isArabic ? 'leading-8' : 'leading-7'}`}>{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Section 2: Product preview (dark) ─────────────── */}
      <section className="overflow-hidden bg-slate-950 py-24 text-white">
        <div className="mx-auto grid max-w-7xl items-start gap-14 px-6 lg:grid-cols-[1fr_1fr]">

          {/* Left: surface cards */}
          <div>
            <p className={`text-sm font-semibold text-slate-400 ${isArabic ? 'tracking-normal' : 'uppercase tracking-[0.26em]'}`}>
              {t.productPreview.workspaceLabel}
            </p>
            <h2 className="mt-4 text-3xl font-extrabold tracking-tight text-white md:text-4xl">
              {t.productPreview.workspaceTitle}
            </h2>
            <p className={`mt-4 max-w-lg text-lg text-slate-300 ${isArabic ? 'leading-9' : 'leading-8'}`}>
              {t.productPreview.workspaceSubtitle}
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {SURFACE_ICONS.map((Icon, i) => {
                const keys = ['dashboard', 'tenders', 'notifications', 'sources', 'activity'] as const;
                const key = keys[i];
                return (
                  <div
                    key={key}
                    className="rounded-3xl border border-white/10 bg-white/5 p-5 transition-all hover:border-white/20 hover:bg-white/8"
                  >
                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-white">
                      <Icon size={18} />
                    </div>
                    <h3 className="text-base font-semibold text-white">{t.app.nav[key]}</h3>
                    <p className={`mt-2 text-sm text-slate-400 ${isArabic ? 'leading-7' : 'leading-6'}`}>
                      {t.productPreview.cards[key as keyof typeof t.productPreview.cards]}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: tilted 3D dashboard card */}
          <motion.div
            initial={false}
            whileHover={prefersReducedMotion ? undefined : { rotateX: -3, rotateY: isArabic ? -4 : 4, y: -4 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            style={{
              transformStyle: 'preserve-3d',
              transform: prefersReducedMotion
                ? undefined
                : `perspective(1400px) rotateX(-5deg) rotateY(${isArabic ? '-7deg' : '7deg'})`,
            }}
            className="relative rounded-[30px] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-blue-500/10"
          >
            {/* Glow accents */}
            <div className="pointer-events-none absolute -left-4 top-10 hidden h-[88%] w-full rounded-[26px] border border-white/5 bg-white/3 lg:block" />
            <div className="pointer-events-none absolute -right-4 top-16 hidden h-[80%] w-full rounded-[26px] border border-emerald-500/10 bg-emerald-500/4 lg:block" />

            <div className="relative rounded-[24px] border border-white/10 bg-slate-950/70 p-5">
              <p className={`text-xs font-semibold text-slate-400 ${isArabic ? 'tracking-normal' : 'uppercase tracking-[0.22em]'}`}>
                {t.productPreview.panelLabel}
              </p>
              <h3 className="mt-3 text-xl font-bold text-white">{t.productPreview.panelTitle}</h3>
              <p className={`mt-3 text-sm text-slate-300 ${isArabic ? 'leading-7' : 'leading-6'}`}>
                {t.productPreview.panelDescription}
              </p>

              <div className="mt-5 grid gap-2 lg:grid-cols-2">
                {/* Dashboard preview */}
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-[0_16px_40px_-24px_rgba(59,130,246,0.5)]">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                    {t.productPreview.previewLabels.dashboard}
                  </p>
                  <div className="mt-3 space-y-2">
                    <div className="rounded-xl border border-white/10 bg-slate-900/90 px-3 py-2 text-xs text-slate-300">{t.productPreview.previewCards.sources}</div>
                    <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-200">{t.productPreview.previewCards.match}</div>
                  </div>
                </div>
                {/* Delivery preview */}
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-[0_16px_40px_-24px_rgba(16,185,129,0.4)]">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                    {t.productPreview.previewLabels.delivery}
                  </p>
                  <div className="mt-3 space-y-2">
                    <div className="rounded-xl border border-white/10 bg-slate-900/90 px-3 py-2 text-xs text-slate-300">{t.productPreview.previewCards.alert}</div>
                    <div className="rounded-xl border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs text-blue-200">{t.productPreview.previewCards.activity}</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-xs text-emerald-200">
                {t.productPreview.panelNote}
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </>
  );
}
