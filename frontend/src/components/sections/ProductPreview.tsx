'use client';

import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { useMemo, useState } from 'react';

const navigationTabs = ['المصادر', 'المناقصات', 'التنبيهات', 'النشاط', 'الإعدادات'];

const tenders = [
  {
    id: '١٠٢٤',
    buyer: 'بلدية دبي',
    category: 'البنية التحتية',
    closingDate: '١٥ يونيو ٢٠٢٦',
    match: '٩٢٪',
  },
  {
    id: '١٠٢٥',
    buyer: 'هيئة الصحة أبوظبي',
    category: 'التجهيزات الطبية',
    closingDate: '١٨ يونيو ٢٠٢٦',
    match: '٨٧٪',
  },
  {
    id: '١٠٢٦',
    buyer: 'وزارة التعليم السعودية',
    category: 'الخدمات الرقمية',
    closingDate: '٢٢ يونيو ٢٠٢٦',
    match: '٨١٪',
  },
  {
    id: '١٠٢٧',
    buyer: 'دائرة المالية - الشارقة',
    category: 'أنظمة مؤسسية',
    closingDate: '٢٥ يونيو ٢٠٢٦',
    match: '٧٦٪',
  },
];

export default function ProductPreview() {
  const [isInteractive, setIsInteractive] = useState(false);

  const prefersStatic = useMemo(() => {
    if (typeof window === 'undefined') {
      return false;
    }

    return (
      window.matchMedia('(max-width: 768px)').matches ||
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }, []);

  const pointerX = useMotionValue(0.5);
  const pointerY = useMotionValue(0.5);

  const rotateXTarget = useTransform(pointerY, [0, 1], [1.5, -1.5]);
  const rotateYTarget = useTransform(pointerX, [0, 1], [-1.5, 1.5]);

  const rotateX = useSpring(rotateXTarget, {
    stiffness: 180,
    damping: 24,
    mass: 0.8,
  });
  const rotateY = useSpring(rotateYTarget, {
    stiffness: 180,
    damping: 24,
    mass: 0.8,
  });

  const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (prefersStatic) {
      return;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    const relativeX = (event.clientX - rect.left) / rect.width;
    const relativeY = (event.clientY - rect.top) / rect.height;

    pointerX.set(relativeX);
    pointerY.set(relativeY);
    setIsInteractive(true);
  };

  const resetTilt = () => {
    pointerX.set(0.5);
    pointerY.set(0.5);
    setIsInteractive(false);
  };

  return (
    <section className="content-section" id="pricing" aria-labelledby="product-preview-title">
      <div className="section-heading">
        <span className="section-eyebrow">معاينة النظام</span>
        <h2 id="product-preview-title">لوحة مراقبة تعرض المناقصات والتنبيهات وحالة النظام في واجهة واحدة.</h2>
        <p>
          معاينة مباشرة لشكل النظام أثناء متابعة المصادر الرسمية، وفرز الفرص النشطة، وإظهار
          التنبيهات ذات الأولوية لفريقك.
        </p>
      </div>

      <div className="product-preview-shell">
        <motion.div
          className={`product-preview-frame content-card${isInteractive ? ' is-interactive' : ''}${prefersStatic ? ' is-static' : ''}`}
          onPointerMove={handlePointerMove}
          onPointerLeave={resetTilt}
          onPointerCancel={resetTilt}
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.35 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
          style={
            prefersStatic
              ? { transform: 'perspective(1400px) rotateX(0deg) rotateY(0deg)' }
              : {
                  perspective: 1400,
                  rotateX,
                  rotateY,
                  transformStyle: 'preserve-3d',
                }
          }
        >
          <article className="product-preview-alert" aria-label="تنبيه جديد">
            <strong>تنبيه جديد</strong>
            <span>1 مناقصة عالية الأولوية</span>
          </article>

          <div className="product-preview-dashboard">
            <aside className="product-preview-sidebar" aria-label="أقسام النظام">
              <div className="product-preview-sidebar__brand">
                <strong>تيندر ووتش</strong>
                <span>لوحة متابعة المناقصات</span>
              </div>

              <nav className="product-preview-sidebar__nav" aria-label="التنقل الداخلي">
                {navigationTabs.map((tab, index) => (
                  <a
                    key={tab}
                    href="#pricing"
                    className={`product-preview-sidebar__link${index === 1 ? ' is-active' : ''}`}
                    aria-current={index === 1 ? 'page' : undefined}
                  >
                    {tab}
                  </a>
                ))}
              </nav>
            </aside>

            <div className="product-preview-main">
              <div className="product-preview-topbar">
                <span>آخر فحص: منذ ٣ دقائق</span>
                <span className="product-preview-system-status">
                  حالة النظام: نشط <span aria-hidden="true">●</span>
                </span>
              </div>

              <div className="product-preview-table-shell">
                <table className="product-preview-table">
                  <thead>
                    <tr>
                      <th scope="col">رقم</th>
                      <th scope="col">الجهة</th>
                      <th scope="col">الفئة</th>
                      <th scope="col">تاريخ الإغلاق</th>
                      <th scope="col">المطابقة</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tenders.map((tender) => (
                      <tr key={tender.id}>
                        <td>{tender.id}</td>
                        <td>{tender.buyer}</td>
                        <td>{tender.category}</td>
                        <td>{tender.closingDate}</td>
                        <td>
                          <span className="product-preview-match-pill">{tender.match}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
