'use client';

import { BellRing, FileSearch, Radar, SearchCheck } from 'lucide-react';
import { useTranslation } from '@/context/language-context';

const icons = [Radar, FileSearch, SearchCheck, BellRing] as const;

export default function ProfileMatchingExplainer() {
  const { t } = useTranslation();

  const items = [
    t.profilePage.matching.cards.sources,
    t.profilePage.matching.cards.compare,
    t.profilePage.matching.cards.matches,
    t.profilePage.matching.cards.alerts,
  ];

  return (
    <section className="overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-100 bg-[linear-gradient(135deg,rgba(59,130,246,0.08),transparent_60%)] px-6 py-6 dark:border-slate-800 dark:bg-[linear-gradient(135deg,rgba(59,130,246,0.12),transparent_60%)] lg:px-8">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-600 dark:text-blue-400">
          {t.profilePage.matching.badge}
        </p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
          {t.profilePage.matching.title}
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400">
          {t.profilePage.matching.description}
        </p>
      </div>

      <div className="grid gap-4 px-6 py-6 lg:px-8">
        {items.map((item, index) => {
          const Icon = icons[index];

          return (
            <div
              key={item.title}
              className="flex items-start gap-4 rounded-2xl border border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-950/50"
            >
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white text-blue-600 shadow-sm dark:bg-slate-900">
                <Icon size={20} />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{item.title}</h3>
                <p className="text-sm leading-6 text-slate-600 dark:text-slate-400">{item.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
