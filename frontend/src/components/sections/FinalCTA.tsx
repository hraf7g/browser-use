export default function FinalCTA() {
  return (
    <section className="content-section" id="signup" aria-labelledby="final-cta-title">
      <div className="final-cta content-card">
        <div className="final-cta__copy">
          <span className="section-eyebrow">ابدأ رحلتك</span>
          <h2 id="final-cta-title">ابدأ مراقبة المناقصات اليوم</h2>
          <p>لا تفوتك فرصة عقد أخرى. يعمل النظام على مدار الساعة، ٧ أيام في الأسبوع.</p>
          <span className="final-cta__english">مراقبة آلية على مدار الساعة عبر مصادر المشتريات الرسمية في المنطقة</span>
        </div>

        <div className="final-cta__actions">
          <a className="primary-cta final-cta__primary" href="/signup">
            ابدأ الآن
          </a>

          <a className="secondary-cta final-cta__secondary" href="mailto:sales@tenderwatch.ai">
            تواصل معنا
          </a>
        </div>
      </div>
    </section>
  );
}
