'use client';

import { useEffect, useMemo, useState } from 'react';

type ActivityStatus = 'completed' | 'new' | 'matched' | 'sent' | 'delivered';

type ActivityItem = {
  id: string;
  time: string;
  body: string;
  statusLabel: string;
  status: ActivityStatus;
};

const activityItems: readonly ActivityItem[] = [
  {
    id: '1',
    time: '09:12',
    body: 'تم فحص بوابة دبي للمشتريات الإلكترونية — ٢٤٧ صفحة',
    statusLabel: 'مكتمل ✓',
    status: 'completed',
  },
  {
    id: '2',
    time: '09:13',
    body: 'تم اكتشاف مناقصة جديدة: مشاريع بنية تحتية - أبوظبي',
    statusLabel: 'جديد',
    status: 'new',
  },
  {
    id: '3',
    time: '09:13',
    body: 'تحليل المحتوى العربي — ٤ صفحات — ٣ بنود رئيسية',
    statusLabel: 'مكتمل ✓',
    status: 'completed',
  },
  {
    id: '4',
    time: '09:14',
    body: 'تم إنشاء مطابقة — نسبة ٩٢٪',
    statusLabel: 'مطابقة',
    status: 'matched',
  },
  {
    id: '5',
    time: '09:14',
    body: 'تم إرسال تنبيه فوري لأعضاء الفريق',
    statusLabel: 'مُرسَل',
    status: 'sent',
  },
  {
    id: '6',
    time: '09:30',
    body: 'الملخص اليومي جاهز — ٣ مناقصات جديدة — ١ عالية الأولوية',
    statusLabel: 'تم التسليم',
    status: 'delivered',
  },
] as const;

export default function LiveActivity() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % activityItems.length);
    }, 2500);

    return () => window.clearInterval(interval);
  }, []);

  const orderedItems = useMemo(
    () => activityItems.map((_, offset) => activityItems[(activeIndex + offset) % activityItems.length]),
    [activeIndex],
  );

  return (
    <section className="content-section" id="live-activity" aria-labelledby="live-activity-title">
      <div className="section-heading">
        <span className="section-eyebrow">نشاط مباشر</span>
        <h2 id="live-activity-title">تدفّق حي يوضح كيف يراقب النظام المصادر ويرسل الأحداث المهمة أولاً.</h2>
        <p>
          تظهر الأحداث بنفس التسلسل التشغيلي الحقيقي: فحص المصدر، اكتشاف الفرصة، تحليل المحتوى،
          إنشاء المطابقة، ثم إرسال التنبيه وتسليم الملخص اليومي.
        </p>
      </div>

      <div className="live-activity-shell content-card">
        <div className="live-activity-shell__header">
          <div>
            <strong>تغذية النشاط</strong>
            <span>المحرّك يراجع البوابات الحكومية ويحدّث الحالة لحظياً</span>
          </div>
          <div className="live-activity-shell__status">
            <span className="live-activity-shell__status-dot" />
            المراقبة نشطة الآن
          </div>
        </div>

        <div className="live-activity-feed" aria-live="polite">
          {orderedItems.map((item, index) => (
            <article
              key={`${item.id}-${activeIndex}`}
              className={`live-activity-item live-activity-item--${item.status}${index === 0 ? ' is-entering' : ''}`}
            >
              <span className="live-activity-item__time-chip">{item.time}</span>
              <div className="live-activity-item__body">
                <div className="live-activity-item__title-row">
                  <strong>{item.body}</strong>
                  <span className={`live-activity-item__status-pill live-activity-item__status-pill--${item.status}`}>
                    {item.statusLabel}
                  </span>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
