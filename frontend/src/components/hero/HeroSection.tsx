import AgentBrowser from '@/components/hero/AgentBrowser';

export default function HeroSection() {
  return (
    <section className="hero-section" id="top" aria-labelledby="hero-title">
      <div className="hero-grid">
        <div className="hero-copy">
          <div className="hero-kicker section-eyebrow">
            <span className="hero-kicker__pulse" aria-hidden="true" />
            منصة عربية أولاً لمتابعة المناقصات الرسمية
          </div>

          <h1 id="hero-title">
            نظام ذكاء اصطناعي لمراقبة المناقصات في منطقة الشرق الأوسط وشمال أفريقيا
          </h1>

          <p className="hero-lead">
            يتصفح المنصات الحكومية الرسمية، ويكتشف العقود الجديدة، ويحلل المحتوى بالعربية
            والإنجليزية، ويرسل تنبيهات فورية لفريقك.
          </p>

          <p className="hero-sub-label">
            AI-powered tender monitoring across MENA procurement portals
          </p>

          <div className="hero-actions">
            <a className="primary-cta" href="/signup">
              <span>ابدأ الآن</span>
              <span aria-hidden="true">←</span>
            </a>

            <a className="secondary-cta" href="#how-it-works">
              شاهد كيف يعمل
            </a>
          </div>

          <ul className="hero-highlights" aria-label="أهم مزايا النظام">
            <li>مراقبة مستمرة لبوابات الشراء الرسمية في الإمارات والسعودية وسائر المنطقة.</li>
            <li>تحليل ثنائي اللغة لاستخراج الجهة والميزانية والمواعيد والبنود الرئيسية.</li>
            <li>مطابقة مباشرة مع ملف شركتك التجاري قبل إرسال التنبيه أو الملخص اليومي.</li>
          </ul>
        </div>

        <AgentBrowser />
      </div>
    </section>
  );
}
