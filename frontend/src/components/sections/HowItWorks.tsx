'use client';

import { useEffect, useRef, useState } from 'react';

const steps = [
  {
    key: 'scan',
    title: 'يتصفح المصادر الرسمية',
    description: 'البوابات الحكومية في الإمارات، السعودية، وسائر دول المنطقة.',
  },
  {
    key: 'document',
    title: 'يكتشف العقود',
    description: 'مناقصات ومشاريع وعروض أسعار جديدة من المصادر المعتمدة ذات الصلة.',
  },
  {
    key: 'analysis',
    title: 'يحلل المحتوى',
    description: 'بالعربية والإنجليزية، ويستخرج البنود الرئيسية والجهة والميزانية والمواعيد.',
  },
  {
    key: 'alert',
    title: 'يُنبّه فريقك',
    description: 'تنبيهات فورية وملخصات يومية مرتبة بحسب الأولوية ونسبة المطابقة.',
  },
] as const;

export default function HowItWorks() {
  const sectionRef = useRef<HTMLElement | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.28 },
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  return (
    <section ref={sectionRef} className="content-section" id="how-it-works" aria-labelledby="how-it-works-title">
      <div className="section-heading">
        <span className="section-eyebrow">كيف يعمل</span>
        <h2 id="how-it-works-title">تسلسل عملي واضح من فحص البوابة حتى وصول التنبيه إلى فريقك.</h2>
        <p>
          كل خطوة مبنية لتشرح ما يفعله الوكيل بدقة: يبدأ بالمصدر الرسمي، يلتقط الفرصة
          الجديدة، يحلل محتواها، ثم يرسل النتيجة في اللحظة المناسبة.
        </p>
      </div>

      <div className={`how-it-works-grid${isVisible ? ' is-visible' : ''}`}>
        {steps.map((step, index) => (
          <article
            key={step.key}
            className={`step-card${isVisible ? ' is-visible' : ''}`}
            style={{ transitionDelay: `${index * 150}ms` }}
          >
            <div className={`step-card__icon step-card__icon--${step.key}`} aria-hidden="true">
              <span className="step-card__shape" />
              <span className="step-card__shape step-card__shape--secondary" />
              <span className="step-card__shape step-card__shape--tertiary" />
            </div>

            <div className="step-card__content">
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </div>

            {index < steps.length - 1 ? <span className="step-card__connector" aria-hidden="true" /> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
