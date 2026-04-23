'use client';

import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

import { useTranslation } from '@/context/language-context';

export default function FinalCTA() {
  const { t, lang } = useTranslation();
  const isArabic = lang === 'ar';

  return (
    <section className="relative overflow-hidden bg-white py-24 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl px-6">
        <div className="relative overflow-hidden rounded-[3rem] bg-[linear-gradient(135deg,#0f172a_0%,#1e3a8a_60%,#1d4ed8_100%)] px-10 py-20 text-center shadow-2xl shadow-blue-900/30 md:px-20">
          {/* Decorative glows */}
          <div className="pointer-events-none absolute left-1/4 top-0 h-56 w-56 -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/20 blur-3xl" />
          <div className="pointer-events-none absolute bottom-0 right-1/4 h-56 w-56 translate-x-1/2 translate-y-1/2 rounded-full bg-indigo-500/20 blur-3xl" />

          {/* Content */}
          <div className="relative">
            <h2 className={`text-4xl font-black tracking-tight text-white md:text-5xl lg:text-6xl ${isArabic ? 'leading-[1.3]' : 'leading-[1.08]'}`}>
              {t.finalCta.title}
            </h2>
            <p className={`mx-auto mt-6 max-w-xl text-lg text-blue-100 ${isArabic ? 'leading-9' : 'leading-8'}`}>
              {t.finalCta.desc}
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/signup"
                id="final-cta-primary"
                className="inline-flex items-center gap-2 rounded-full bg-white px-9 py-4 text-base font-black text-blue-700 shadow-xl transition-all hover:-translate-y-0.5 hover:shadow-2xl active:scale-95"
              >
                {t.finalCta.button}
                <ArrowRight size={18} className={isArabic ? 'rotate-180' : ''} />
              </Link>
              <Link
                href="/login"
                id="final-cta-secondary"
                className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-9 py-4 text-base font-bold text-white transition-colors hover:bg-white/15 active:scale-95"
              >
                {t.finalCta.secondary}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
