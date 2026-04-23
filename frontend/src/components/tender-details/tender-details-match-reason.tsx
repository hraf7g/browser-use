'use client';
import { useTranslation } from '@/context/language-context';
import { Zap, Target, Info } from 'lucide-react';
import { getMatchReasonBadges } from '@/lib/match-reason';

export default function TenderDetailsMatchReason({
  keywords,
  countryCodes,
  industryCodes,
}: {
  keywords: string[];
  countryCodes: string[];
  industryCodes: string[];
}) {
  const { t, lang } = useTranslation();
  const reasonBadges = getMatchReasonBadges(
    {
      keywords,
      countryCodes,
      industryCodes,
    },
    lang
  );

  if (reasonBadges.length === 0) {
    return (
      <div className="rounded-2xl border border-blue-100 bg-blue-50/50 p-6 dark:border-blue-900/30 dark:bg-blue-900/10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
            <Info size={20} />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 dark:text-white">{t.details.match.title}</h3>
            <p className="text-xs font-semibold text-blue-600 dark:text-blue-400">{t.details.match.confidence}</p>
          </div>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
          {t.details.match.noReasons}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white">
          <Zap size={20} />
        </div>
        <div>
          <h3 className="font-bold text-slate-900 dark:text-white">{t.details.match.title}</h3>
          <p className="text-xs font-semibold text-blue-600 dark:text-blue-400">{t.details.match.confidence}</p>
        </div>
      </div>

      <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed mb-4">
        {t.details.match.reason}
      </p>

      <div className="flex flex-wrap gap-2">
        {reasonBadges.map((badge) => (
          <span key={badge.key} className="px-3 py-1 bg-white dark:bg-slate-800 border border-blue-200 dark:border-blue-800 rounded-full text-xs font-bold text-blue-700 dark:text-blue-300">
            {badge.label}
          </span>
        ))}
      </div>
    </div>
  );
}
