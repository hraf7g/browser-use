'use client';
import { useTranslation } from '@/context/language-context';
import { MapPin, Calendar, ExternalLink } from 'lucide-react';

export default function DashboardPriorityTenders() {
  const { t, lang } = useTranslation();

  const tenders = [
    { id: '1', title: 'IT Infrastructure Upgrade', source: 'Etimad', deadline: '3', score: 98, new: true },
    { id: '2', title: 'Consultancy for Smart Cities', source: 'Dubai Govt', deadline: '5', score: 85, new: false },
    { id: '3', title: 'Facility Management Services', source: 'NEOM', deadline: '2', score: 92, new: true },
  ];

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.priority.title}</h3>
        <button className="text-sm font-bold text-blue-600 hover:text-blue-700 transition-colors">
          {t.dashboard.priority.viewAll}
        </button>
      </div>

      <div className="space-y-4">
        {tenders.map((tender) => (
          <div key={tender.id} className="group p-4 rounded-xl border border-slate-100 dark:border-slate-800 hover:border-blue-200 dark:hover:border-blue-800 transition-all bg-slate-50/30 dark:bg-slate-950/30">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <h4 className="font-bold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 transition-colors cursor-pointer line-clamp-1">
                  {tender.title}
                </h4>
                {tender.new && (
                  <span className="px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-[10px] font-bold uppercase tracking-wider">
                    {t.dashboard.priority.newLabel}
                  </span>
                )}
              </div>
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30 px-2 py-1 rounded-md">
                {t.dashboard.priority.matchScore.replace('{n}', tender.score.toString())}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
              <div className="flex items-center gap-1.5">
                <MapPin size={12} />
                <span>{tender.source}</span>
              </div>
              <div className="flex items-center gap-1.5 font-medium text-amber-600 dark:text-amber-500">
                <Calendar size={12} />
                <span>{t.dashboard.priority.daysLeft.replace('{n}', tender.deadline)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
