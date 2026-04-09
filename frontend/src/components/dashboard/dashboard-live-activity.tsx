'use client';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { Search, Zap, Bell, CheckCircle2, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

type ActivityType = 'check' | 'detect' | 'match' | 'alert' | 'brief';

interface ActivityItem {
  id: string;
  type: ActivityType;
  name?: string;
  keyword?: string;
  time: string;
}

export default function DashboardLiveActivity() {
  const { t, lang } = useTranslation();
  const [filter, setFilter] = useState<'all' | 'sources' | 'matches'>('all');

  // Mock data representing operational transparency
  const activities: ActivityItem[] = [
    { id: '1', type: 'alert', time: '2m' },
    { id: '2', type: 'match', keyword: 'Cybersecurity', time: '5m' },
    { id: '3', type: 'detect', name: 'Etimad', time: '12m' },
    { id: '4', type: 'check', name: 'Dubai Govt', time: '15m' },
    { id: '5', type: 'brief', time: '1h' },
  ];

  const getIcon = (type: ActivityType) => {
    switch (type) {
      case 'check': return <Search size={14} />;
      case 'detect': return <CheckCircle2 size={14} className="text-emerald-500" />;
      case 'match': return <Zap size={14} className="text-amber-500" />;
      case 'alert': return <Bell size={14} className="text-blue-500" />;
      default: return <RefreshCw size={14} />;
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden flex flex-col h-full">
      <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <h3 className="font-bold text-slate-900 dark:text-white">{t.dashboard.activity.title}</h3>
        <div className="flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
          {(['all', 'sources', 'matches'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-3 py-1 text-xs font-semibold rounded-md transition-all",
                filter === f
                  ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              )}
            >
              {f === 'all' ? t.dashboard.activity.filterAll : f === 'sources' ? t.dashboard.activity.filterSources : t.dashboard.activity.filterMatches}
            </button>
          ))}
        </div>
      </div>

      <div className="p-5 space-y-6 flex-1 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {activities.map((item, idx) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: lang === 'ar' ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-4 relative"
            >
              {idx !== activities.length - 1 && (
                <div className="absolute start-3 top-8 bottom-[-24px] w-px bg-slate-100 dark:bg-slate-800" />
              )}
              <div className="w-6 h-6 rounded-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center shrink-0 z-10">
                {getIcon(item.type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-200 leading-snug">
                  {item.type === 'check' && t.dashboard.activity.status.check.replace('{name}', item.name || '')}
                  {item.type === 'detect' && t.dashboard.activity.status.detect.replace('{name}', item.name || '')}
                  {item.type === 'match' && t.dashboard.activity.status.match.replace('{keyword}', item.keyword || '')}
                  {item.type === 'alert' && t.dashboard.activity.status.alert}
                  {item.type === 'brief' && t.dashboard.activity.status.brief}
                </p>
                <p className="text-xs text-slate-500 mt-1">{item.time} {lang === 'ar' ? 'منذ' : 'ago'}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
