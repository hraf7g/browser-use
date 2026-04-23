'use client';

import { ArrowRight, ShieldCheck } from 'lucide-react';
import Link from 'next/link';

import { useTranslation } from '@/context/language-context';
import HomepageHeroVisual from './homepage-hero-visual';

export default function Hero() {
  const { t, lang } = useTranslation();
  const isArabic = lang === 'ar';

  return (
    <section className="relative overflow-hidden bg-white pb-20 pt-32 dark:bg-slate-950 md:pb-28 md:pt-40">
      {/* Background radial glow */}
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[700px] w-full -translate-x-1/2 bg-[radial-gradient(ellipse_at_top,rgba(37,99,235,0.10),transparent_55%)]" />

      <div className="relative z-10 mx-auto max-w-7xl px-6">
        <div className="grid items-center gap-14 lg:grid-cols-[0.95fr_1.05fr]">

          {/* ── Copy block ─────────────────────────────────────── */}
          <div className={isArabic ? 'lg:order-2' : ''}>
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 dark:border-blue-900/40 dark:bg-blue-950/30">
              <ShieldCheck size={13} className="text-blue-600" />
              <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-blue-700 dark:text-blue-300">
                {t.hero.badge}
              </span>
            </div>

            {/* Headline */}
            <h1
              className={`text-4xl font-extrabold tracking-tight text-slate-950 dark:text-white md:text-5xl lg:text-6xl ${
                isArabic ? 'leading-[1.28] md:leading-[1.18]' : 'leading-[1.08] md:leading-[1.04]'
              }`}
            >
              <span className="bg-gradient-to-br from-slate-950 via-slate-800 to-slate-500 bg-clip-text text-transparent dark:from-white dark:via-slate-100 dark:to-slate-400">
                {t.hero.title}
              </span>
            </h1>

            {/* Subtitle */}
            <p
              className={`mt-6 max-w-xl text-lg text-slate-600 dark:text-slate-400 ${
                isArabic ? 'leading-9' : 'leading-8'
              }`}
            >
              {t.hero.subtitle}
            </p>

            {/* CTAs */}
            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/signup"
                id="hero-cta-primary"
                className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-7 py-3.5 text-sm font-bold text-white shadow-lg shadow-blue-500/25 transition-all hover:-translate-y-0.5 hover:bg-blue-700 hover:shadow-xl active:scale-95"
              >
                {t.hero.ctaPrimary}
              </Link>
              <Link
                href="#how"
                id="hero-cta-secondary"
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-7 py-3.5 text-sm font-bold text-slate-900 transition-all hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800"
              >
                {t.hero.ctaSecondary}
                <ArrowRight size={16} className={isArabic ? 'rotate-180' : ''} />
              </Link>
            </div>

            {/* Trust pills */}
            <div className="mt-8 flex flex-wrap gap-2">
              {(t.hero.highlights as string[]).map((item) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3.5 py-1.5 text-xs font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  {item}
                </span>
              ))}
            </div>
          </div>

          {/* ── Hero visual ────────────────────────────────────── */}
          <div className={isArabic ? 'lg:order-1' : ''}>
            <HomepageHeroVisual />
          </div>
        </div>
      </div>
    </section>
  );
}
