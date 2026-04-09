'use client';
import { useTranslation } from '@/context/language-context';
import { MessageSquare, Mail, Check } from 'lucide-react';

export default function TenderDetailsNotificationState({
  notificationState,
}: {
  notificationState: {
    match_created_at: string | null;
    matched_keywords: string[];
    instant_alert_sent: boolean;
    instant_alert_sent_at: string | null;
    daily_brief_sent: boolean;
    daily_brief_sent_at: string | null;
  };
}) {
  const { t, lang } = useTranslation();

  const formatDateTime = (value: string | null) =>
    value ? new Intl.DateTimeFormat(lang, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : null;

  const instantAlertTime = formatDateTime(notificationState.instant_alert_sent_at);
  const dailyBriefTime = formatDateTime(notificationState.daily_brief_sent_at);
  const matchedAtTime = formatDateTime(notificationState.match_created_at);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6">
      <h3 className="font-bold text-slate-900 dark:text-white mb-6">{t.details.notifications.title}</h3>
      <p className="mb-4 text-xs font-medium text-slate-500 dark:text-slate-400">
        {notificationState.match_created_at
          ? t.details.notifications.matchedAt.replace('{time}', matchedAtTime ?? '')
          : t.details.notifications.pending}
      </p>
      <div className="space-y-4">
        {[
          {
            label: t.details.notifications.whatsapp,
            icon: MessageSquare,
            time: instantAlertTime ?? t.details.notifications.pending,
            status: notificationState.instant_alert_sent ? 'sent' : 'scheduled',
          },
          {
            label: t.details.notifications.email,
            icon: Mail,
            time: dailyBriefTime ?? t.details.notifications.pending,
            status: notificationState.daily_brief_sent ? 'sent' : 'scheduled',
          },
        ].map((item, i) => (
          <div key={i} className="flex items-center justify-between p-4 rounded-xl border border-slate-50 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
            <div className="flex items-center gap-3">
              <item.icon size={18} className="text-slate-400" />
              <div>
                <p className="text-sm font-bold text-slate-900 dark:text-white">{item.label}</p>
                <p className="text-xs text-slate-500">{item.time}</p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${
              item.status === 'sent' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-blue-100 text-blue-700'
            }`}>
              {item.status === 'sent' && <Check size={10} />}
              {item.status === 'sent' ? t.details.notifications.sent : t.details.notifications.notSent}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
