'use client';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { MapPin, Calendar, ArrowUpRight, Zap } from 'lucide-react';
import TendersStatusBadge from './tenders-status-badge';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import type { UITenderItem } from './tenders-list';

export default function TendersListItem({ tender }: { tender: UITenderItem }) {
  const { t, lang } = useTranslation();

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 md:p-6 hover:border-blue-300 dark:hover:border-blue-700 transition-all hover:shadow-xl hover:shadow-blue-500/5"
    >
      <div className="flex flex-col md:flex-row gap-6 justify-between">
        <div className="flex-1 min-w-0 space-y-4">
          {/* Top Row: Badges & Source */}
          <div className="flex flex-wrap items-center gap-2">
            <TendersStatusBadge type={tender.isNew ? 'new' : ''} />
            <TendersStatusBadge type={tender.isMatched ? 'matched' : ''} />
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[11px] font-bold">
              <MapPin size={12} />
              {tender.source}
            </div>
            <span className="text-slate-400 text-[11px] font-medium font-mono">{tender.reference}</span>
          </div>

          {/* Title & Entity */}
          <div>
            <h3 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white leading-tight group-hover:text-blue-600 transition-colors">
              {tender.title}
            </h3>
            <p className="text-slate-500 dark:text-slate-400 font-medium mt-1">{tender.entity}</p>
          </div>

          {/* Match Reason Section */}
          {tender.isMatched && (
            <div className="flex items-center gap-2 py-2 px-3 rounded-xl bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/40 w-fit">
              <Zap size={14} className="text-blue-600" />
              <span className="text-xs font-semibold text-blue-900 dark:text-blue-300">
                {t.tenders.card.matchReason} {tender.matchedKeywords.join(', ')}
              </span>
            </div>
          )}
        </div>

        {/* Action Column */}
        <div className="flex flex-col justify-between items-end gap-4 min-w-[140px]">
          <div className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold",
            tender.daysLeft <= 3 
              ? "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400" 
              : "bg-slate-50 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
          )}>
            <Calendar size={14} />
            {t.tenders.card.daysLeft.replace('{n}', tender.daysLeft.toString())}
          </div>

          <Link href={`/tenders/${tender.id}`} className="w-full md:w-auto px-6 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold text-sm transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2">
            {t.tenders.card.viewDetails}
            <ArrowUpRight size={16} className={lang === 'ar' ? 'rotate-[-90deg]' : ''} />
          </Link>
        </div>
      </div>
    </motion.div>
  );
}
