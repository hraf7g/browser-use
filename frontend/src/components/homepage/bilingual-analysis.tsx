const bilingualRows = [
  {
    label: 'Issuer',
    arabic: 'بلدية دبي',
    english: 'Dubai Municipality',
  },
  {
    label: 'Package',
    arabic: 'أعمال صيانة البنية التحتية',
    english: 'Infrastructure maintenance works',
  },
  {
    label: 'Submission deadline',
    arabic: 'آخر موعد للتقديم: 15 مايو 2026',
    english: 'Submission deadline: 15 May 2026',
  },
  {
    label: 'Qualification note',
    arabic: 'يشترط وجود خبرة في المشاريع الحكومية المماثلة',
    english: 'Requires prior experience on comparable public-sector projects',
  },
] as const;

const bilingualHighlights = [
  'Keep issuer language intact while producing an English operating brief',
  'Surface dates, scope, and mandatory criteria without manual copy-paste',
  'Reduce qualification errors caused by partial translation or missed clauses',
] as const;

export default function BilingualAnalysis() {
  return (
    <section className="section-shell" id="bilingual-analysis">
      <div className="section-inner bilingual-layout">
        <div className="bilingual-copy">
          <span className="section-label">Bilingual analysis</span>
          <h2 className="section-title">Arabic source material becomes a shared English operating brief.</h2>
          <p className="section-lead">
            In Gulf procurement, the problem is not only finding tenders — it is making sure the team
            interprets them correctly. Tender Watch preserves the source language while extracting the
            operational meaning your bid team actually needs.
          </p>

          <ul className="bilingual-highlights">
            {bilingualHighlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>

        <div className="bilingual-panel framed-panel">
          <div className="bilingual-panel__header">
            <span className="mono-text">Normalized tender brief</span>
            <strong>AR / EN side-by-side</strong>
          </div>

          <div className="bilingual-table">
            {bilingualRows.map((row) => (
              <div key={row.label} className="bilingual-row">
                <div className="bilingual-row__label mono-text">{row.label}</div>
                <div className="bilingual-row__value bilingual-row__value--arabic" lang="ar">
                  {row.arabic}
                </div>
                <div className="bilingual-row__value">{row.english}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
