'use client';

import { useTranslation } from '@/context/language-context';
import { Minus, Plus } from 'lucide-react';
import { useState } from 'react';

export default function FAQ() {
  const { t, lang } = useTranslation();
  const [open, setOpen] = useState<number | null>(0);

  const items = [
    { q: t.faq.q1, a: t.faq.a1 },
    { q: t.faq.q2, a: t.faq.a2 },
  ];

  return (
    <section id="faq" className="bg-slate-50 py-20 dark:bg-slate-950">
      <div className="mx-auto max-w-3xl px-6">
        <div className="mb-14 text-center">
          <h2 className="text-4xl font-bold tracking-tight text-slate-950 dark:text-white">{t.faq.title}</h2>
          <p className={`mt-4 text-lg text-slate-600 dark:text-slate-400 ${lang === 'ar' ? 'leading-9' : 'leading-8'}`}>
            {t.faq.subtitle}
          </p>
        </div>

        <div className="space-y-4">
          {items.map((item, i) => (
            <div key={i} className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
              <button
                type="button"
                onClick={() => setOpen(open === i ? null : i)}
                className="flex w-full items-center justify-between px-8 py-6 text-start text-lg font-bold"
              >
                <span>{item.q}</span>
                {open === i ? <Minus size={20} /> : <Plus size={20} />}
              </button>

              <div
                className={`overflow-hidden transition-[max-height,opacity] duration-300 ease-out ${open === i ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'}`}
              >
                <div className="px-8 pb-6 text-slate-600 dark:text-slate-400">
                  {item.a}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
