export default function BilingualPanel() {
  return (
    <section className="content-section" id="sources" aria-labelledby="bilingual-panel-title">
      <div className="section-heading">
        <span className="section-eyebrow">ثنائي اللغة</span>
        <h2 id="bilingual-panel-title">من نص عربي رسمي إلى مخرجات إنجليزية منظمة يمكن مشاركتها فوراً.</h2>
        <p>
          يربط النظام بين المستند العربي الأصلي والمخرجات الإنجليزية المنظمة دون فقدان السياق،
          بحيث يرى الفريق النص الخام والبيانات المستخلصة في نفس اللحظة.
        </p>
      </div>

      <div className="bilingual-panel">
        <article className="analysis-card analysis-card--arabic">
          <span className="analysis-card__label">تحليل نص عربي</span>
          <h3>مقتطف من وثيقة مناقصة حكومية</h3>
          <div className="analysis-card__document">
            <p>
              تعلن <mark>هيئة الطرق والمواصلات</mark> عن طرح مناقصة خاصة بتحديث طريق الخوانيج
              والبنية التحتية المحيطة به، وتشمل الأعمال الدراسات التنفيذية، أعمال السلامة
              المرورية، والتحسينات المدنية المرتبطة بالموقع. وتبلغ <mark>الميزانية التقديرية
              ١٢.٤ مليون درهم</mark>، فيما سيكون <mark>تاريخ الإغلاق ١٥ يونيو ٢٠٢٦</mark>
              ، مع إلزام جميع المتقدمين برفع المستندات الفنية والمالية عبر البوابة الرسمية قبل
              الموعد المحدد.
            </p>
          </div>
        </article>

        <div className="bilingual-panel__connector" aria-hidden="true">
          <span className="bilingual-panel__connector-line" />
          <span className="bilingual-panel__connector-text">→ تحليل → ←</span>
          <span className="bilingual-panel__connector-pulse" />
        </div>

        <article className="analysis-card analysis-card--english" dir="ltr">
          <span className="analysis-card__label">مخرجات إنجليزية منظمة</span>
          <h3>ملخص فرصة منظم</h3>
          <dl className="analysis-summary">
            <div>
              <dt>الجهة</dt>
              <dd>Roads and Transport Authority</dd>
            </div>
            <div>
              <dt>الفئة</dt>
              <dd>Infrastructure Projects</dd>
            </div>
            <div>
              <dt>تاريخ الإغلاق</dt>
              <dd>15 June 2026</dd>
            </div>
            <div>
              <dt>القيمة التقديرية</dt>
              <dd>AED 12.4M</dd>
            </div>
            <div>
              <dt>نسبة المطابقة</dt>
              <dd>87%</dd>
            </div>
          </dl>
        </article>
      </div>

      <div className="result-badge">
        <span className="result-badge__dot" />
        مطابقة للملف التجاري ٨٧٪
      </div>
    </section>
  );
}
