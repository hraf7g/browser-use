const previewColumns = [
  {
    label: 'Watchlist intelligence',
    items: [
      'Unified source watchlists across public and private issuers',
      'Deadline and addendum change tracking',
      'Sector, geography, and package filtering',
    ],
  },
  {
    label: 'Qualification workspace',
    items: [
      'Structured tender briefs with issuer and scope context',
      'Bilingual requirement extraction and normalization',
      'Fit scoring based on your commercial lens',
    ],
  },
  {
    label: 'Action layer',
    items: [
      'Owner routing with rationale and urgency cues',
      'Commercial handoff for high-confidence opportunities',
      'A shared operating view across bid, sales, and leadership',
    ],
  },
] as const;

const previewTimeline = [
  'Source update captured',
  'Tender brief normalized',
  'Fit confidence scored',
  'Owner alerted to act',
] as const;

export default function ProductPreview() {
  return (
    <section className="section-shell" id="product-preview">
      <div className="section-inner product-preview-layout">
        <div className="product-preview-copy">
          <span className="section-label">Product preview</span>
          <h2 className="section-title">Designed like an operating system for pursuit teams.</h2>
          <p className="section-lead">
            The product experience combines live monitoring, structured analysis, and routed action into
            a single surface. Instead of switching between portals, spreadsheets, translation steps, and
            internal chats, teams work from one continuously updated view.
          </p>
        </div>

        <div className="product-preview-panel framed-panel">
          <div className="product-preview-panel__header">
            <div>
              <span className="mono-text">Tender Watch workspace</span>
              <strong>Signal, qualification, and routing in one view</strong>
            </div>
            <span className="product-preview-panel__status mono-text">Operational</span>
          </div>

          <div className="product-preview-grid">
            {previewColumns.map((column) => (
              <article key={column.label} className="product-preview-column">
                <h3>{column.label}</h3>
                <ul>
                  {column.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          <div className="product-preview-timeline" aria-label="Signal processing timeline">
            {previewTimeline.map((item, index) => (
              <div key={item} className="product-preview-timeline__step">
                <span className="mono-text">0{index + 1}</span>
                <strong>{item}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
