'use client';

import { useTranslation } from '@/context/language-context';

export default function BilingualAnalysis() {
  const { t, lang } = useTranslation();
  const isArabic = lang === 'ar';
  const p = t.homepageBilingual.panels;

  return (
    <section id="features" className="bg-white py-24 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mx-auto mb-14 max-w-2xl text-center">
          <p className={`mb-3 text-sm font-bold text-blue-600 dark:text-blue-400 ${isArabic ? 'tracking-normal' : 'uppercase tracking-[0.26em]'}`}>
            {t.homepageBilingual.eyebrow}
          </p>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-950 dark:text-white md:text-4xl">
            {t.homepageBilingual.title}
          </h2>
          <p className={`mt-4 text-lg text-slate-600 dark:text-slate-400 ${isArabic ? 'leading-9' : 'leading-8'}`}>
            {t.homepageBilingual.description}
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {(t.homepageBilingual.badges as string[]).map((b) => (
              <span key={b} className="rounded-full border border-slate-200 bg-slate-50 px-3.5 py-1.5 text-xs font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                {b}
              </span>
            ))}
          </div>
        </div>

        {/* Three-panel layout: EN card | Match bridge | AR card */}
        <div className="grid gap-4 lg:grid-cols-3">

          {/* English tender card (LTR) */}
          <div className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/70" dir="ltr">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300">
              English
            </div>
            <h3 className="text-base font-bold text-slate-950 dark:text-white">{p.tenderView.title}</h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{p.tenderView.subtitle}</p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
              <p className="text-sm font-semibold leading-snug text-slate-900 dark:text-white">{p.tenderView.titleEn}</p>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{p.tenderView.subtitleEn}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {['Deadline', 'Buyer', 'Category'].map((f) => (
                  <span key={f} className="rounded-md border border-blue-100 bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300">{f}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Matched opportunity bridge */}
          <div className="flex flex-col items-center justify-center rounded-[2rem] border border-emerald-200 bg-emerald-50 p-6 dark:border-emerald-900/40 dark:bg-emerald-950/20">
            <div className="mb-3 rounded-full bg-emerald-600 px-4 py-2 text-sm font-black text-white shadow-lg shadow-emerald-500/30">
              {p.matched.score}
            </div>
            <p className="text-center text-sm font-bold text-slate-950 dark:text-white">{p.matched.title}</p>
            <p className="mt-2 text-center text-xs text-emerald-700 dark:text-emerald-300">{p.matched.reason}</p>
            <div className="mt-5 w-full space-y-2">
              <div className="rounded-xl border border-emerald-200 bg-white px-3 py-2 text-xs text-slate-700 dark:border-emerald-900/30 dark:bg-slate-900 dark:text-slate-300">
                {p.layout.title}
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white px-3 py-2 text-xs text-slate-700 dark:border-emerald-900/30 dark:bg-slate-900 dark:text-slate-300">
                {p.extraction.title}
              </div>
            </div>
          </div>

          {/* Arabic tender card (RTL) */}
          <div className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/70" dir="rtl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-violet-700 dark:border-violet-900/40 dark:bg-violet-950/30 dark:text-violet-300">
              عربي
            </div>
            <h3 className="text-base font-bold text-slate-950 dark:text-white">{p.tenderViewAr.title}</h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{p.tenderViewAr.subtitle}</p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
              <p className="text-sm font-semibold leading-relaxed text-slate-900 dark:text-white">{p.tenderViewAr.titleAr}</p>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{p.tenderViewAr.subtitleAr}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {['الموعد', 'الجهة', 'الفئة'].map((f) => (
                  <span key={f} className="rounded-md border border-violet-100 bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-700 dark:border-violet-900/40 dark:bg-violet-950/30 dark:text-violet-300">{f}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom feature row */}
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-6 dark:border-slate-800 dark:bg-slate-900/70">
            <h3 className="text-base font-bold text-slate-950 dark:text-white">{p.layout.title}</h3>
            <p className={`mt-3 text-sm text-slate-600 dark:text-slate-400 ${isArabic ? 'leading-8' : 'leading-7'}`}>{p.layout.description}</p>
          </div>
          <div className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-6 dark:border-slate-800 dark:bg-slate-900/70">
            <h3 className="text-base font-bold text-slate-950 dark:text-white">{p.extraction.title}</h3>
            <p className={`mt-3 text-sm text-slate-600 dark:text-slate-400 ${isArabic ? 'leading-8' : 'leading-7'}`}>{p.extraction.description}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
